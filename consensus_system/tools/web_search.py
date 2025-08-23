"""
Web search tool for agents using DuckDuckGo.
"""
from langchain_community.tools import DuckDuckGoSearchRun


def create_web_search_tool():
    """Create web search tool for agents."""
    return DuckDuckGoSearchRun()


# Global web search tool instance
web_search_tool = create_web_search_tool()
