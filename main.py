"""
Debate Orchestrator (Debaters-Only) with LangGraph + OpenAI + Claude
--------------------------------------------------------------------

Run:
  export OPENAI_API_KEY=...   # for OpenAI debaters
  export ANTHROPIC_API_KEY=... # for Claude debaters
  pip install langgraph langchain langchain-openai langchain-anthropic pydantic
  python debate_langgraph.py

What it does now:
- ONLY Debaters participate in the conversation (no Moderator turns).
- Runs a fixed number of rounds you specify.
- After the rounds, an additional AI "Arbiter" inspects the entire debate history
  and decides whether there is a CONSENSUS. If not, it triggers a VOTE among the debaters
  and reports the final decision by majority (or ties explicitly).

Customize DEFAULT_CONFIG at the bottom.
"""
from __future__ import annotations
import os
import json
from typing import TypedDict, List, Dict, Any, Optional, Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# LangChain chat model wrappers for OpenAI and Anthropic
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# =============================
# State Schema
# =============================
class DebateState(TypedDict):
    topic: str
    options: Dict[str, str]             # {"A": label_a, "B": label_b}
    context: str
    evidence_policy: str
    success_criteria: str
    round_limit: int                    # number of debate rounds to execute

    debaters: List[Dict[str, Any]]      # e.g., [{"id":"D1","model":"openai:gpt-4o"}, ...]

    # Logs and outputs
    round_idx: int
    openings: List[Dict[str, Any]]      # opening statements per debater
    rounds: List[Dict[str, Any]]        # list of rounds with debater turns

    arbiter_result: Dict[str, Any]      # output from arbiter
    votes: List[Dict[str, Any]]         # votes if voting happens
    tally: Dict[str, int]
    final_decision: Dict[str, Any]

# =============================
# Prompt Templates (Debaters)
# =============================
DEBATER_OPENING_PROMPT = """
ROLE: Debater

OBJECTIVE
Choose exactly one of two options and defend it concisely. You may switch later if persuaded.

TOPIC
{topic}
Options:
  - A: {A}
  - B: {B}

CONTEXT
{context}

EVIDENCE POLICY
{evidence_policy}

SUCCESS CRITERIA
Optimize for: {success}

OUTPUT JSON ONLY (no commentary):
{{
  "debater_id": "{debater_id}",
  "pick": "A|B",
  "reasons": ["point 1", "point 2", "point 3"]
}}
Constraints:
- "pick" must be exactly "A" or "B" (uppercase).
- Max 90 words across all reasons.
""".strip()

DEBATER_TURN_PROMPT = """
ROLE: Debater

OBJECTIVE
Debate concisely for this round. You may defend or revise your position.

TOPIC
{topic}
Options:
  - A: {A}
  - B: {B}

CONTEXT
{context}

SUCCESS CRITERIA
{success}

PREVIOUS ROUND SNAPSHOT (peers' strongest points)
{peer_points}

OUTPUT JSON ONLY:
{{
  "debater_id": "{debater_id}",
  "challenge": ["critique 1", "critique 2"],
  "defend_or_revise": {{"text":"concise defense or concession", "new_pick":"A|B|UNCHANGED"}},
  "proposal": "one concrete, falsifiable check aligned with SUCCESS_CRITERIA"
}}
Constraints:
- If switching, set new_pick to "A" or "B". Else set "UNCHANGED".
- Entire output <= 120 words.
""".strip()

DEBATER_VOTE_PROMPT = """
ROLE: Debater

TASK
Cast your final vote. Pick exactly one option.

TOPIC
{topic}
Options: A={A} | B={B}

SUCCESS CRITERIA
{success}

OUTPUT JSON ONLY:
{{
  "debater_id": "{debater_id}",
  "vote": "A|B"
}}
Constraints:
- "vote" must be exactly "A" or "B".
""".strip()

# =============================
# Arbiter Prompt (decides consensus vs vote)
# =============================
ARBITER_DECIDE_PROMPT = """
ROLE: Arbiter

You are given a full JSON log of a multi-agent debate with only debaters (no moderator messages).
Your job is to decide whether the debaters have already reached a CONSENSUS on one side (A or B), or whether a VOTE is needed.

CRITERIA FOR CONSENSUS (all should be true or overwhelmingly supported):
- A clear majority of debaters, by the final round, explicitly advocate the same side (A or B),
  or multiple debaters switched to that side while dissent is weak and unsubstantiated per SUCCESS CRITERIA.
- Arguments for the winning side best satisfy the SUCCESS CRITERIA and directly address top critiques.

If CONSENSUS is found, return a JSON object with decision_mode="consensus" and include side and rationale.
If not, return decision_mode="vote" with a brief reason.

INPUT
Topic: {topic}
Options: A={A} | B={B}
Success Criteria: {success}
Debate Log JSON:
{debate_log}

OUTPUT JSON ONLY:
{{
  "decision_mode": "consensus|vote",
  "consensus": {{"side": "A|B", "confidence": 0.0, "rationale": "..."}} | null,
  "reason": "why vote is needed if no consensus"
}}
Constraints:
- If decision_mode is "consensus", fill consensus; set reason to "".
- If decision_mode is "vote", set consensus to null; provide a short reason.
""".strip()

# =============================
# Model loader
# =============================

def get_model(model_id: str):
    """Return a LangChain chat model instance from a provider spec like:
       - "openai:gpt-4o-mini"
       - "openai:gpt-4.1"
       - "anthropic:claude-3-7-sonnet"
    """
    provider, name = model_id.split(":", 1)
    if provider == "openai":
        return ChatOpenAI(model=name, temperature=0.3)
    elif provider == "anthropic":
        return ChatAnthropic(model=name, temperature=0.3)
    else:
        raise ValueError(f"Unknown provider in model id: {model_id}")

# =============================
# Helpers
# =============================

def safe_json_parse(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except Exception:
                pass
        raise


def clamp_side(value: str) -> str:
    v = (value or "").strip().upper()
    return v if v in ("A", "B") else "A"

# =============================
# Nodes
# =============================

def openings(state: DebateState) -> DebateState:
    """Collect opening picks from each debater."""
    outs: List[Dict[str, Any]] = []
    for d in state["debaters"]:
        model = get_model(d["model"]) 
        prompt = DEBATER_OPENING_PROMPT.format(
            topic=state["topic"], A=state["options"]["A"], B=state["options"]["B"],
            context=state["context"], evidence_policy=state["evidence_policy"],
            success=state["success_criteria"], debater_id=d["id"],
        )
        resp = model.invoke(prompt)
        data = safe_json_parse(resp.content)
        data["pick"] = clamp_side(data.get("pick", ""))
        outs.append(data)
    state["openings"] = outs
    state["rounds"].append({"round": 0, "openings": outs})
    state["round_idx"] = 1
    return state


def debate_round(state: DebateState) -> DebateState:
    """Run one debate round where every debater responds once."""
    r = state["round_idx"]

    # Build snapshot of strongest peer points from previous step
    last_points: Dict[str, List[str]] = {}
    if r == 1:
        for op in state["openings"]:
            last_points[op["debater_id"]] = op.get("reasons", [])[:3]
    else:
        prev = state["rounds"][-1]
        for turn in prev.get("turns", []):
            pts = []
            pts.extend(turn.get("challenge", [])[:1])
            dor = turn.get("defend_or_revise", {})
            if isinstance(dor, dict) and dor.get("text"):
                pts.append(dor.get("text"))
            last_points[turn["debater_id"]] = pts[:3]
    peer_summary = json.dumps(last_points)

    turns: List[Dict[str, Any]] = []
    for d in state["debaters"]:
        model = get_model(d["model"]) 
        prompt = DEBATER_TURN_PROMPT.format(
            topic=state["topic"], A=state["options"]["A"], B=state["options"]["B"],
            context=state["context"], success=state["success_criteria"],
            peer_points=peer_summary, debater_id=d["id"],
        )
        resp = model.invoke(prompt)
        data = safe_json_parse(resp.content)
        npick = data.get("defend_or_revise", {}).get("new_pick", "UNCHANGED")
        if npick not in ("A", "B", "UNCHANGED"):
            data["defend_or_revise"]["new_pick"] = "UNCHANGED"
        turns.append(data)

    state["rounds"].append({"round": r, "turns": turns})
    state["round_idx"] = r + 1
    return state


def arbiter_decide(state: DebateState) -> DebateState:
    """Arbiter inspects full history and decides consensus vs vote-needed."""
    # Use the first debater's model as the arbiter provider for simplicity; change if you like.
    arb_model = get_model(state["debaters"][0]["model"]) 
    debate_log = json.dumps({"openings": state["openings"], "rounds": state["rounds"]}, ensure_ascii=False)
    prompt = ARBITER_DECIDE_PROMPT.format(
        topic=state["topic"], A=state["options"]["A"], B=state["options"]["B"],
        success=state["success_criteria"], debate_log=debate_log,
    )
    resp = arb_model.invoke(prompt)
    data = safe_json_parse(resp.content)
    # sanitize
    mode = data.get("decision_mode", "vote").strip().lower()
    if mode not in ("consensus", "vote"):
        mode = "vote"
    if mode == "consensus":
        side = clamp_side((data.get("consensus") or {}).get("side", ""))
        conf = float((data.get("consensus") or {}).get("confidence", 0))
        rationale = (data.get("consensus") or {}).get("rationale", "")
        state["arbiter_result"] = {"decision_mode": "consensus", "consensus": {"side": side, "confidence": conf, "rationale": rationale}, "reason": ""}
        state["final_decision"] = {"winner": side, "label": state["options"][side], "decision_basis": "consensus"}
    else:
        reason = data.get("reason", "Insufficient convergence.")
        state["arbiter_result"] = {"decision_mode": "vote", "consensus": None, "reason": reason}
    return state


def voting(state: DebateState) -> DebateState:
    """If Arbiter asked for a vote, collect votes and tally."""
    if state.get("arbiter_result", {}).get("decision_mode") != "vote":
        return state

    votes: List[Dict[str, Any]] = []
    tally = {"A": 0, "B": 0}

    for d in state["debaters"]:
        model = get_model(d["model"]) 
        prompt = DEBATER_VOTE_PROMPT.format(
            topic=state["topic"], A=state["options"]["A"], B=state["options"]["B"],
            success=state["success_criteria"], debater_id=d["id"],
        )
        resp = model.invoke(prompt)
        data = safe_json_parse(resp.content)
        vote = clamp_side(data.get("vote", ""))
        votes.append({"debater_id": d["id"], "vote": vote})
        tally[vote] += 1

    state["votes"] = votes
    state["tally"] = tally

    # Majority rule (explicit tie handling)
    a, b = tally["A"], tally["B"]
    if a > b:
        winner = "A"
    elif b > a:
        winner = "B"
    else:
        winner = None

    if winner:
        state["final_decision"] = {"winner": winner, "label": state["options"][winner], "decision_basis": "majority_vote"}
    else:
        state["final_decision"] = {"winner": None, "label": None, "decision_basis": "tie_after_vote"}

    return state

# =============================
# Edges / Conditions
# =============================

def need_another_round(state: DebateState) -> Literal["continue", "stop"]:
    return "continue" if state["round_idx"] <= state["round_limit"] else "stop"


def arbiter_path(state: DebateState) -> Literal["consensus", "vote", "done"]:
    mode = state.get("arbiter_result", {}).get("decision_mode")
    if mode == "consensus":
        return "consensus"
    elif mode == "vote":
        return "vote"
    return "done"

# =============================
# Build Graph
# =============================

def build_graph():
    workflow = StateGraph(DebateState)

    workflow.add_node("openings", openings)
    workflow.add_node("debate_round", debate_round)
    workflow.add_node("arbiter_decide", arbiter_decide)
    workflow.add_node("voting", voting)

    workflow.set_entry_point("openings")

    workflow.add_edge("openings", "debate_round")
    workflow.add_conditional_edges("debate_round", need_another_round, {"continue": "debate_round", "stop": "arbiter_decide"})

    workflow.add_conditional_edges("arbiter_decide", arbiter_path, {"consensus": END, "vote": "voting", "done": END})

    workflow.add_edge("voting", END)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

# =============================
# Default Config
# =============================
DEFAULT_CONFIG = {
    "topic": "Which is a better place to visit this September?",
    "options": {"A": "Japan", "B": "Thailand"},
    "context": """Travel window: September 1–30, 2025; travelers: a couple preferring private stays over shared hostels. Goals: balanced mix of food, culture, light hikes, city days, and 2–4 beach/relax days. Constraints: minimize severe-weather disruption; tolerate some rain but avoid extended downpours; avoid extreme heat/humidity when possible; mid-range budget.
Japan notes: Early September can be hot/humid; conditions improve mid–late September. Elevated typhoon risk especially for Okinawa/Kyushu/Shikoku and coastal areas; rail transit is excellent; crowds generally moderate after mid-September except during “Silver Week”.
Thailand notes: September is peak monsoon for much of the country (Bangkok/Chiang Mai rainy; Andaman coast—Phuket/Krabi—very wet with rough seas). Gulf islands (Koh Samui/Phangan/Tao) can be relatively drier but still see frequent showers; prices are generally lower; beach/swim conditions variable.""",

    "evidence_policy": "Use general knowledge and the provided context; no browsing or tools.",
    "success_criteria": """Score each destination (0–5) on: (1) Weather & season fit (×3): probability of mostly dry, safe days (no typhoon/rough-sea shutdowns). (2) Activity fit (×2): availability of our desired mix—food, culture, light hikes, and beach days in September. (3) Travel friction (×1): reliability of internal transport and likelihood of disruptions. (4) Cost (×1): expected mid-range daily cost (private lodging, meals, intercity transit). (5) Crowds & comfort (×1): heat/humidity and crowd levels. Choose the option with the higher weighted total; if within 1 point, break ties toward the option with lower disruption risk.""",

    "round_limit": 2,  # number of debate rounds (after openings)
    "debaters": [
        {"id": "D1", "model": "openai:gpt-4o-mini"},
        {"id": "D2", "model": "anthropic:claude-3-7-sonnet"},
        {"id": "D3", "model": "openai:gpt-4.1-mini"},
    ],
    "context": "Feature complete; unit tests pass; unknown peak traffic; rollback is possible.",
    "evidence_policy": "Use general knowledge and the provided context; no browsing or tools.",
    "success_criteria": "Minimize Sev-1 probability while not missing a revenue window; prefer reversible decisions.",
    "round_limit": 2,  # number of debate rounds (after openings)
    "debaters": [
        {"id": "D1", "model": "openai:gpt-4o-mini"},
        {"id": "D2", "model": "anthropic:claude-3-7-sonnet"},
        {"id": "D3", "model": "openai:gpt-4.1-mini"},
    ],
}

# =============================
# Main
# =============================

def run_debate(config: Dict[str, Any]) -> Dict[str, Any]:
    graph = build_graph()
    init_state: DebateState = {
        "topic": config["topic"],
        "options": config["options"],
        "context": config.get("context", ""),
        "evidence_policy": config.get("evidence_policy", "Use only the supplied context."),
        "success_criteria": config.get("success_criteria", ""),
        "round_limit": int(config.get("round_limit", 2)),
        "debaters": config["debaters"],
        "round_idx": 0,
        "openings": [],
        "rounds": [],
        "arbiter_result": {},
        "votes": [],
        "tally": {"A": 0, "B": 0},
        "final_decision": {},
    }

    final_state = graph.invoke(init_state)

    result = {
        "topic": final_state["topic"],
        "options": final_state["options"],
        "openings": final_state["openings"],
        "rounds": final_state["rounds"],
        "arbiter_result": final_state.get("arbiter_result", {}),
        "votes": final_state.get("votes", []),
        "tally": final_state.get("tally", {}),
        "final_decision": final_state.get("final_decision", {}),
    }
    return result

if __name__ == "__main__":
    cfg = DEFAULT_CONFIG
    print("Running debaters-only debate with config:", json.dumps({k:v for k,v in cfg.items() if k!="debaters"}, indent=2, ensure_ascii=False))
    print("Debaters:", ", ".join([f"{d['id']}@{d['model']}" for d in cfg["debaters"]]))
    out = run_debate(cfg)
    print("=== ARBITER RESULT ===")
    print(json.dumps(out.get("arbiter_result", {}), indent=2, ensure_ascii=False))
    print("=== FINAL DECISION ===")
    print(json.dumps(out.get("final_decision", {}), indent=2, ensure_ascii=False))
    print("=== FULL LOG ===")
    print(json.dumps(out, indent=2, ensure_ascii=False))
