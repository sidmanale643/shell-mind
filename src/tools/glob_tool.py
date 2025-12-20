import glob
from .schema import ToolSchema
from textwrap import dedent

class Glob(ToolSchema):
    def __init__(self):
        self.name = "glob"
    
    def description(self):
        return dedent("""
        Finds files matching a glob pattern. The pattern can include wildcards like '*' and '**'.
        The pattern should generally be an absolute path.
        The search is recursive if '**' is used.
        """)
    
    def json_schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "The glob pattern to match files against, e.g., '/path/to/**/*.py'"
                        }
                    },
                    "required": ["pattern"]
                }
            }
        }
    
    def run(self, pattern: str):
        try:
            # Use recursive=True for ** patterns
            files = glob.glob(pattern, recursive=True)
            if not files:
                return f"No files found matching pattern: {pattern}"
            
            return f"Found {len(files)} matches for pattern '{pattern}':\n" + "\n".join(files)
        except Exception as e:
            return f"Error executing glob: {str(e)}"

