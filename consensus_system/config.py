"""
Configuration and environment variables for the consensus system.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Model configurations - using valid, available models
SUPERVISOR_MODEL = "gpt-4o"  # GPT-4o for Supervisor
AGENT_X_MODEL = "gpt-4.1"  # GPT-3.5 Turbo for Agent X (less capable)
AGENT_Y_MODEL = "gpt-4o"  # GPT-4o for Agent Y (more capable)
AGENT_Z_MODEL = "claude-3-5-sonnet-20241022"  # Claude 3.5 Sonnet for Agent Z

# Consensus prompt template
DEFAULT_CONSENSUS_PROMPT = "The debate phase is over. Now you must find areas of agreement and compromise to reach a consensus position that addresses key concerns from all perspectives. Please pick ONE opotion and give it as an answer, the rest will be at the explanation."
