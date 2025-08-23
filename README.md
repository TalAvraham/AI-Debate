# Hierarchical Multi-Agent Consensus System

A LangGraph-based system that enables three AI agents to debate topics and reach consensus through structured conversation.

## Features

- **Two-Phase System**: Presentation mode (5 iterations) + Consensus mode (until agreement)
- **Multiple AI Models**: Support for various OpenAI models (GPT-4o, GPT-3.5-turbo, etc.) and Anthropic Claude models
- **Web Search Integration**: Agents can search the web for information
- **JSON Export**: Automatic export of all conversation data and statistics
- **Modular Design**: Easy to modify agent order and personalities
- **Structured Output**: JSON responses with reasoning and explanations

## System Architecture

```
SUPERVISOR → AGENT_X → AGENT_Y → AGENT_Z → Decision Point
    ↓           ↓         ↓         ↓         ↓
  Start    Continue Debate OR Switch to Consensus Mode
    ↓
  Consensus Loop (until supervisor decides consensus reached)
```

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys**:
   - Copy `env.template` to `.env`
   - Add your OpenAI and Anthropic API keys

3. **Run the System**:
   ```bash
   python -m consensus_system.main
   ```

## File Structure

```
consensus_system/
├── main.py                 # Main entry point
├── config.py              # Configuration and API keys
├── state.py               # Agent state definitions
├── agents/
│   ├── supervisor.py      # Supervisor agent
│   ├── debater_agents.py # Agent X, Y, Z implementations
│   └── prompts.py         # Prompt templates
├── graph/
│   └── graph_builder.py   # LangGraph structure
├── tools/
│   └── web_search.py      # Web search integration
└── utils/
    └── response_parser.py # Response parsing utilities
```

## Usage

### Basic Usage
```python
from consensus_system.main import run_consensus_system

topic = "Should artificial intelligence be regulated by governments?"
result = run_consensus_system(topic)
```

### Customizing Agents
- Modify personalities in `agents/prompts.py`
- Change agent order in `graph/graph_builder.py`
- Adjust prompts and behaviors as needed
- Configure different AI models in `config.py`

### Customizing Topics
```python
# In main.py
if __name__ == "__main__":
    topic = "Your custom topic here?"
    result = run_consensus_system(topic)
```

## Configuration

- **Max Iterations**: Set in `state.py` (default: 5)
- **Models**: Configure in `config.py`
- **Consensus Prompt**: Modify in `config.py`

## Output

The system provides:
- Real-time console output of agent responses
- Structured state storage for analysis
- Conversation history tracking
- Consensus evaluation results
- JSON export of all data for analysis

### JSON Export

After each run, the system exports the following JSON files to a timestamped output folder:
- `complete_conversation.json` - Full conversation history with metadata
- `agent_x_responses.json` - All Agent X responses with metadata
- `agent_y_responses.json` - All Agent Y responses with metadata
- `agent_z_responses.json` - All Agent Z responses with metadata
- `summary_statistics.json` - System statistics and counts

## Research Applications

This system is designed to study:
- Agent order effects on consensus
- Impact of different AI models
- Prompt engineering effects
- Consensus building dynamics
- Personality effects on debate outcomes
- Topic complexity and consensus difficulty

## Requirements

- Python 3.8+
- OpenAI API key
- Anthropic API key
- Internet connection (for web search)
