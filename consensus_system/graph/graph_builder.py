"""
LangGraph graph builder for the consensus system.
"""
from langgraph.graph import StateGraph, END
from ..state import AgentState
from ..agents.supervisor import SupervisorAgent
from ..agents.debater_agents import create_agent_x, create_agent_y, create_agent_z


def build_consensus_graph():
    """Build the consensus system graph."""
    
    # Create agents
    supervisor = SupervisorAgent()
    agent_x = create_agent_x()
    agent_y = create_agent_y()
    agent_z = create_agent_z()
    
    # Create graph
    graph = StateGraph(AgentState)
    
    # Set entry point
    graph.set_entry_point("supervisor")
    
    # Add nodes
    graph.add_node("supervisor", supervisor.introduce_mission)
    graph.add_node("agent_x", agent_x.process)
    graph.add_node("agent_y", agent_y.process)
    graph.add_node("agent_z", agent_z.process)
    graph.add_node("consensus_supervisor", supervisor.switch_to_consensus_mode)
    graph.add_node("consensus_agent_x", agent_x.process)
    graph.add_node("consensus_agent_y", agent_y.process)
    graph.add_node("consensus_agent_z", agent_z.process)
    graph.add_node("consensus_evaluator", supervisor.evaluate_consensus)
    
    # Add edges for presentation mode
    graph.add_edge("supervisor", "agent_x")
    graph.add_edge("agent_x", "agent_y")
    graph.add_edge("agent_y", "agent_z")
    
    # Conditional edge: continue presentation or switch to consensus
    graph.add_conditional_edges(
        "agent_z",
        lambda x: "agent_x" if x["iteration_count"] < x["max_iterations"] else "consensus_supervisor"
    )
    
    # Consensus mode edges
    graph.add_edge("consensus_supervisor", "consensus_agent_x")
    graph.add_edge("consensus_agent_x", "consensus_agent_y")
    graph.add_edge("consensus_agent_y", "consensus_agent_z")
    graph.add_edge("consensus_agent_z", "consensus_evaluator")
    
    # After evaluation: either consensus reached (END) or continue loop
    graph.add_conditional_edges(
        "consensus_evaluator",
        lambda x: END if (x["consensus_reached"] or x["consensus_round"] >= x["max_consensus_rounds"]) else "consensus_supervisor"
    )
    
    return graph.compile()
