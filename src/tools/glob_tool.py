import glob
from .schema import ToolSchema
from textwrap import dedent

class Glob(ToolSchema):
    def __init__(self):
        self.name = "glob"
    
    def description(self):
        return dedent("""
        Finds files matching a glob pattern, supporting wildcards like '*' and '**' (recursive).
        Ideal for locating specific file types or files with known naming patterns across directories.
        
        Usage:
        - Use `**` for recursive searching (e.g., '/path/to/project/**/*.py').
        - The `pattern` should ideally be an absolute path.
        - Returns a list of matching file paths.
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

