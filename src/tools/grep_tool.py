import subprocess
import os
from .schema import ToolSchema
from textwrap import dedent

class Grep(ToolSchema):
    def __init__(self):
        self.name = "grep"
    
    def description(self):
        return dedent("""
        Performs a recursive text search (grep) for a pattern within a directory.
        Uses `grep -rnEI` to provide line numbers and ignore binary files.
        
        Usage:
        - `pattern` can be a literal string or an extended regular expression.
        - `directory_path` must be an absolute path.
        - Use this to find specific code usage, variable definitions, or configuration values across a project.
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
                            "description": "The pattern to search for (regex supported)"
                        },
                        "directory_path": {
                            "type": "string",
                            "description": "The directory to search in. Must be an absolute path."
                        }
                    },
                    "required": ["pattern", "directory_path"]
                }
            }
        }
    
    def run(self, pattern: str, directory_path: str):
        # Validate the path exists
        if not os.path.exists(directory_path):
            return f"Error: Path '{directory_path}' does not exist."
        
        if not os.path.isdir(directory_path):
            return f"Error: Path '{directory_path}' is not a directory."

        try:
            # -r: recursive
            # -n: line numbers
            # -E: extended regex
            # -I: ignore binary files
            result = subprocess.run(
                ["grep", "-rnEI", pattern, directory_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 1:
                return f"No matches found for pattern '{pattern}' in '{directory_path}'."
            
            if result.returncode != 0:
                return f"Error executing grep: {result.stderr.strip() or 'Unknown error.'}"

            output = result.stdout.strip()
            # Truncate if too long? For now let's just return it.
            if len(output) > 10000:
                output = output[:10000] + "\n... (output truncated)"
                
            return f"Grep results for '{pattern}' in '{directory_path}':\n{output}"
            
        except Exception as e:
            return f"Error executing grep command: {str(e)}"

