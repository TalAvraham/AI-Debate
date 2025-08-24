"""
Supervisor agent implementation using LangChain.
"""
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from ..agents.prompts import SUPERVISOR_PROMPT_TEMPLATE
from ..utils.response_parser import parse_agent_response, format_conversation_entry
from ..config import SUPERVISOR_MODEL, OPENAI_API_KEY, DEFAULT_CONSENSUS_PROMPT
from ..state import AgentState


class SupervisorAgent:
    """Supervisor agent that manages the debate and consensus process."""
    
    def __init__(self):
        self.llm = ChatOpenAI(model=SUPERVISOR_MODEL, api_key=OPENAI_API_KEY, temperature=0.5)
    
    def introduce_mission(self, state: AgentState) -> AgentState:
        """Introduce the mission and topic."""
        introduction = f"Welcome! We are three participants who must debate and reach consensus on: {state['current_topic']}. Let's begin with introductions."
        
        # Add to conversation history
        conversation_entry = format_conversation_entry("SUPERVISOR", introduction)
        state["conversation_history"].append(conversation_entry)
        
        print(f"\nSUPERVISOR:")
        print(f"Introduction: {introduction}")
        
        return state
    
    def switch_to_consensus_mode(self, state: AgentState) -> AgentState:
        """Switch system to consensus mode."""
        state["mode"] = "consensus"
        state["consensus_prompt"] = DEFAULT_CONSENSUS_PROMPT
        state["consensus_round"] += 1
        
        instruction = f"Now entering consensus mode. Round {state['consensus_round']}"
        
        # Add to conversation history
        conversation_entry = format_conversation_entry("SUPERVISOR", instruction)
        state["conversation_history"].append(conversation_entry)
        
        print(f"\nSUPERVISOR:")
        print(f"Mode Switch: {instruction}")
        
        return state
    
    def evaluate_consensus(self, state: AgentState) -> AgentState:
        """Evaluate if consensus has been reached."""
        prompt = SUPERVISOR_PROMPT_TEMPLATE.format(
            current_topic=state["current_topic"],
            conversation_history="\n".join(state["conversation_history"]),
            mode=state["mode"]
        )
        
        # Get evaluation from LLM
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages).content
        
        # Parse response (supervisor uses same format for consistency)
        parsed = parse_agent_response(response)
        
        # Update state - check for consensus_reached_yes
        state["consensus_reached"] = "consensus_reached_yes" in parsed["response"].lower()
        state["consensus_counter"] += 1
        
        # Add to conversation history
        conversation_entry = format_conversation_entry("SUPERVISOR", f"Consensus evaluation: {parsed['explanation']}")
        state["conversation_history"].append(conversation_entry)
        
        print(f"\nSUPERVISOR:")
        print(f"Consensus Evaluation: {parsed['explanation']}")
        print(f"Consensus Reached: {state['consensus_reached']}")
        
        return state
