import os
from .schema import ToolSchema

class WebSearchTool(ToolSchema):
    """
    Web search tool using Tavily API for documentation lookups and general web searches.
    Useful for finding "how to" information, documentation, and current technical knowledge.
    """
    
    def __init__(self):
        self.name = "web_search"
        self.api_key = os.environ.get("TAVILY_API_KEY")
        
    def description(self):
        return (
            "Search the web for technical documentation, tutorials, and current information. "
            "Useful for 'how to' questions, finding documentation for tools/commands, "
            "troubleshooting errors, and getting up-to-date information about software/tools. "
            "Returns relevant snippets and URLs from the web."
        )

    def json_schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query. Be specific and include relevant technical terms, tool names, or error messages."
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of search results to return (default: 3)",
                            "default": 3
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    
    def run(self, query: str, max_results: int = 3) -> str:
        """
        Execute a web search using Tavily API.
        
        Args:
            query: The search query
            max_results: Maximum number of results to return (default: 3)
            
        Returns:
            Formatted search results with titles, URLs, and content snippets
        """
        try:
            if not self.api_key:
                return self._format_error(
                    "TAVILY_API_KEY not found in environment variables. "
                    "Please set it to enable web search functionality. "
                    "Get your API key at: https://tavily.com"
                )
            
            # Import here to avoid errors if tavily-python is not installed
            try:
                from tavily import TavilyClient
            except ImportError:
                return self._format_error(
                    "tavily-python package not installed. "
                    "Install it with: pip install tavily-python"
                )
            
            # Initialize client and perform search
            client = TavilyClient(api_key=self.api_key)
            
            # Perform search with relevant parameters
            response = client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",  # More thorough search
                include_answer=True,      # Get AI-generated answer if available
                include_raw_content=False # Don't need full page content
            )
            
            return self._format_results(response)
            
        except Exception as e:
            return self._format_error(f"Search failed: {str(e)}")
    
    def _format_results(self, response: dict) -> str:
        """Format Tavily API response into readable text."""
        output = []
        
        # Add AI-generated answer if available
        if response.get("answer"):
            output.append("=== Quick Answer ===")
            output.append(response["answer"])
            output.append("")
        
        # Add search results
        results = response.get("results", [])
        if results:
            output.append("=== Search Results ===")
            for i, result in enumerate(results, 1):
                output.append(f"\n{i}. {result.get('title', 'Untitled')}")
                output.append(f"   URL: {result.get('url', 'N/A')}")
                
                content = result.get('content', '')
                if content:
                    # Truncate long content
                    if len(content) > 300:
                        content = content[:297] + "..."
                    output.append(f"   {content}")
        else:
            output.append("No results found.")
        
        return "\n".join(output)
    
    def _format_error(self, error_msg: str) -> str:
        """Format error messages consistently."""
        return f"[Web Search Error] {error_msg}"
