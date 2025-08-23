"""
Debater agents implementation using LangChain.
"""
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage
from langchain.tools import tool
from ..tools.web_search import web_search_tool
from ..agents.prompts import AGENT_PROMPT_TEMPLATE, AGENT_CONFIGS, MISSION_INSTRUCTIONS
from ..utils.response_parser import parse_agent_response, format_conversation_entry
from ..config import AGENT_X_MODEL, AGENT_Y_MODEL, AGENT_Z_MODEL, OPENAI_API_KEY, ANTHROPIC_API_KEY
from ..state import AgentState


@tool
def web_search(query: str) -> str:
    """Search the web for information."""
    try:
        return web_search_tool.run(query)
    except:
        return "Web search unavailable. Using existing knowledge."


class DebaterAgent:
    """Base class for debater agents."""
    
    def __init__(self, agent_type: str, model_name: str, api_key: str):
        self.agent_type = agent_type
        self.config = AGENT_CONFIGS[agent_type]
        
        if "gpt" in model_name:
            self.llm = ChatOpenAI(model=model_name, api_key=api_key, temperature=0.7)
        else:
            self.llm = ChatAnthropic(model=model_name, api_key=api_key, temperature=0.7)
    
    def get_prompt(self, state: AgentState) -> str:
        """Generate prompt for the agent."""
        return AGENT_PROMPT_TEMPLATE.format(
            agent_name=self.config["name"],
            personality_description=self.config["personality"],
            mission_instructions=MISSION_INSTRUCTIONS,
            current_topic=state["current_topic"],
            conversation_history="\n".join(state["conversation_history"]),
            iteration_count=state["iteration_count"],
            consensus_prompt=state["consensus_prompt"],
            agent_behavior_instructions=self.config["behavior"]
        )
    
    def process(self, state: AgentState) -> AgentState:
        """Process agent turn and update state."""
        prompt = self.get_prompt(state)
        
        # Get response from LLM
        messages = [HumanMessage(content=prompt)]
        response = self.llm.invoke(messages).content
        
        # Parse response
        parsed = parse_agent_response(response)
        
        # Update state
        agent_messages_key = f"{self.agent_type}_messages"
        state[agent_messages_key].append(parsed["response"])
        
        # Add to conversation history
        conversation_entry = format_conversation_entry(self.config["name"], parsed["response"])
        state["conversation_history"].append(conversation_entry)
        
        # Increment iteration count if this is Agent Z in presentation mode
        if self.agent_type == "agent_z" and state["mode"] == "presentation":
            state["iteration_count"] += 1
        
        # Print output
        print(f"\n{self.config['name']}:")
        print(f"Response: {parsed['response']}")
        print(f"Explanation: {parsed['explanation']}")
        
        return state


def create_agent_x() -> DebaterAgent:
    """Create Agent X."""
    return DebaterAgent("agent_x", AGENT_X_MODEL, OPENAI_API_KEY)


def create_agent_y() -> DebaterAgent:
    """Create Agent Y."""
    return DebaterAgent("agent_y", AGENT_Y_MODEL, OPENAI_API_KEY)


def create_agent_z() -> DebaterAgent:
    """Create Agent Z."""
    return DebaterAgent("agent_z", AGENT_Z_MODEL, ANTHROPIC_API_KEY)
