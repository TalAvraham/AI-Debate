"""
Main entry point for the consensus system.
"""
import json
import os
from datetime import datetime
from .state import create_initial_state
from .graph.graph_builder import build_consensus_graph
from .config import AGENT_X_MODEL, AGENT_Y_MODEL, AGENT_Z_MODEL


def export_results_to_json(final_state, topic: str):
    """Export all results to JSON files in a unique output folder."""
    # Create unique output folder with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = f"output_consensus_{timestamp}"
    os.makedirs(output_folder, exist_ok=True)
    
    # 1. Export complete conversation history
    conversation_data = {
        "topic": topic,
        "mode": final_state["mode"],
        "consensus_reached": final_state["consensus_reached"],
        "total_iterations": final_state["iteration_count"],
        "consensus_rounds": final_state["consensus_round"],
        "conversation_history": final_state["conversation_history"],
        "export_timestamp": datetime.now().isoformat()
    }
    
    with open(f"{output_folder}/complete_conversation.json", "w", encoding="utf-8") as f:
        json.dump(conversation_data, f, indent=2, ensure_ascii=False)
    
    # Import agent configurations
    from .agents.prompts import AGENT_CONFIGS
    
    # 2. Export Agent X responses
    agent_x_data = {
        "agent_name": "AGENT_X",
        "personality": AGENT_CONFIGS["agent_x"]["personality"],
        "behavior": AGENT_CONFIGS["agent_x"]["behavior"],
        "model": AGENT_X_MODEL,
        "topic": topic,
        "responses": final_state["agent_x_messages"],
        "total_responses": len(final_state["agent_x_messages"]),
        "export_timestamp": datetime.now().isoformat()
    }
    
    with open(f"{output_folder}/agent_x_responses.json", "w", encoding="utf-8") as f:
        json.dump(agent_x_data, f, indent=2, ensure_ascii=False)
    
    # 3. Export Agent Y responses
    agent_y_data = {
        "agent_name": "AGENT_Y",
        "personality": AGENT_CONFIGS["agent_y"]["personality"],
        "behavior": AGENT_CONFIGS["agent_y"]["behavior"],
        "model": AGENT_Y_MODEL,
        "topic": topic,
        "responses": final_state["agent_y_messages"],
        "total_responses": len(final_state["agent_y_messages"]),
        "export_timestamp": datetime.now().isoformat()
    }
    
    with open(f"{output_folder}/agent_y_responses.json", "w", encoding="utf-8") as f:
        json.dump(agent_y_data, f, indent=2, ensure_ascii=False)
    
    # 4. Export Agent Z responses
    agent_z_data = {
        "agent_name": "AGENT_Z",
        "personality": AGENT_CONFIGS["agent_z"]["personality"],
        "behavior": AGENT_CONFIGS["agent_z"]["behavior"],
        "model": AGENT_Z_MODEL,
        "topic": topic,
        "responses": final_state["agent_z_messages"],
        "total_responses": len(final_state["agent_z_messages"]),
        "export_timestamp": datetime.now().isoformat()
    }
    
    with open(f"{output_folder}/agent_z_responses.json", "w", encoding="utf-8") as f:
        json.dump(agent_z_data, f, indent=2, ensure_ascii=False)
    
    # 5. Export summary statistics
    summary_data = {
        "topic": topic,
        "consensus_reached": final_state["consensus_reached"],
        "total_iterations": final_state["iteration_count"],
        "consensus_rounds": final_state["consensus_round"],
        "max_consensus_rounds": final_state["max_consensus_rounds"],
        "agent_response_counts": {
            "agent_x": len(final_state["agent_x_messages"]),
            "agent_y": len(final_state["agent_y_messages"]),
            "agent_z": len(final_state["agent_z_messages"])
        },
        "total_conversation_entries": len(final_state["conversation_history"]),
        "export_timestamp": datetime.now().isoformat(),
        "output_folder": output_folder
    }
    
    with open(f"{output_folder}/summary_statistics.json", "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Results exported to folder: {output_folder}")
    print(f"📊 Files created:")
    print(f"   • complete_conversation.json")
    print(f"   • agent_x_responses.json") 
    print(f"   • agent_y_responses.json")
    print(f"   • agent_z_responses.json")
    print(f"   • summary_statistics.json")
    
    return output_folder


def run_consensus_system(topic: str):
    """Run the consensus system with the given topic."""
    print(f"Starting Consensus System")
    print(f"Topic: {topic}")
    print("=" * 50)
    
    # Create initial state
    initial_state = create_initial_state(topic)
    
    # Build and run graph
    graph = build_consensus_graph()
    
    try:
        # Execute the graph
        final_state = graph.invoke(initial_state, config={"recursion_limit": 300})
        
        print("\n" + "=" * 50)
        print("Consensus System Completed!")
        print(f"Final Consensus: {final_state['consensus_reached']}")
        print(f"Total Consensus Rounds: {final_state['consensus_counter']}")
        print(f"Total Iterations: {final_state['iteration_count']}")
        
        # Export results to JSON files
        output_folder = export_results_to_json(final_state, topic)
        
        return final_state, output_folder
        
    except Exception as e:
        print(f"Error running consensus system: {e}")
        return None


if __name__ == "__main__":
    # Example usage
    topic = "what is the best SUV for 5 person family?"
    result = run_consensus_system(topic)
