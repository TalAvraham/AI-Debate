"""
Response parsing utilities for agent outputs.
"""
import json
from typing import Dict, Optional


def parse_agent_response(response: str) -> Optional[Dict]:
    """Parse agent JSON response with error handling."""
    try:
        # Try to extract JSON from response if it's embedded in text
        if '{' in response and '}' in response:
            start = response.find('{')
            end = response.rfind('}') + 1
            json_str = response[start:end]
            parsed = json.loads(json_str)
        else:
            parsed = json.loads(response)
            
        required_fields = ["response", "reasoning", "explanation"]
        
        if all(field in parsed for field in required_fields):
            return parsed
        else:
            # Create default response if fields missing
            return {
                "response": parsed.get("response", "No response"),
                "reasoning": parsed.get("reasoning", "No reasoning"),
                "explanation": parsed.get("explanation", "No explanation")
            }
    except (json.JSONDecodeError, ValueError, AttributeError):
        # If all else fails, try to extract key information from text
        response_text = response.strip()
        
        # Look for response and explanation patterns
        if "Response:" in response_text and "Explanation:" in response_text:
            parts = response_text.split("Explanation:")
            resp_part = parts[0].replace("Response:", "").strip()
            expl_part = parts[1].strip() if len(parts) > 1 else "No explanation"
            
            return {
                "response": resp_part,
                "reasoning": "Extracted from text",
                "explanation": expl_part
            }
        else:
            return {
                "response": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                "reasoning": "Text parsing fallback",
                "explanation": "Could not parse structured response"
            }


def format_conversation_entry(agent_name: str, response: str) -> str:
    """Format agent response for conversation history."""
    return f"{agent_name}: {response}"
