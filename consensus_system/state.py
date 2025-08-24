"""
Agent state definitions for the consensus system.
"""
from typing import Dict, List, Literal, TypedDict


class AgentState(TypedDict):
    """State structure for the consensus system."""
    conversation_history: List[str]      # All messages in format "AGENT: message"
    iteration_count: int                 # Current iteration (0-5 for presentation mode)
    max_iterations: int                  # 5 iterations for presentation mode
    mode: Literal["presentation", "consensus"]  # Current system mode
    consensus_reached: bool              # Has consensus been achieved?
    consensus_prompt: str                # Consensus instruction for agents
    consensus_counter: int               # How many consensus rounds completed
    agent_x_messages: List[str]          # Agent X's stored messages
    agent_y_messages: List[str]          # Agent Y's stored messages
    agent_z_messages: List[str]          # Agent Z's stored messages
    current_topic: str                   # Debate topic
    consensus_round: int                 # Current consensus round number
    max_consensus_rounds: int           # Maximum consensus rounds to prevent infinite loops
    agent_x_full_responses: List[Dict]   # Agent X's full responses including explanation
    agent_y_full_responses: List[Dict]   # Agent Y's full responses including explanation
    agent_z_full_responses: List[Dict]   # Agent Z's full responses including explanation


def create_initial_state(topic: str) -> AgentState:
    """Create initial state for the consensus system."""
    return AgentState(
        conversation_history=[],
        iteration_count=0,
        max_iterations=2,
        mode="presentation",
        consensus_reached=False,
        consensus_prompt="",
        consensus_counter=0,
        agent_x_messages=[],
        agent_y_messages=[],
        agent_z_messages=[],
        current_topic=topic,
        consensus_round=0,
        max_consensus_rounds=5,  # Prevent infinite loops
        agent_x_full_responses=[],
        agent_y_full_responses=[],
        agent_z_full_responses=[]
    )
