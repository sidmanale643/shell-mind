import subprocess
import os
from .schema import ToolSchema
from textwrap import dedent

class Grep(ToolSchema):
    def __init__(self):
        self.name = "grep"
    
    def description(self):
        return dedent("""
        Perform recursive text search for a pattern across files in a directory.

        ### When to Use
        - Finding where a function, variable, or class is defined
        - Searching for specific code usage or patterns across a project
        - Locating configuration values or settings
        - Finding all occurrences of a string/text in multiple files

        ### When NOT to Use
        - Use `glob` to find files by name/pattern (not content)
        - Use `read_file` to inspect a specific file's full contents
        - Use `run_command "grep ..."` only if you need special grep flags

        ### Parameters
        - `pattern`: The text or regex pattern to search for (required). Can be:
          - Literal string: "function_name"
          - Regex: "def \\w+\\(", "import .*os", "TODO|FIXME"
        - `directory_path`: Absolute path to search directory (required). Example: "/Users/project/src"

        ### Output Format
        - Success: "Grep results for '{pattern}' in '{dir}':\\n{file}:{line}:{content}"
        - No matches: "No matches found for pattern '{pattern}' in '{dir}'."
        - Error: "Error executing grep: {error_details}"

        ### Examples

        **Find function definition:**
        Input: {"pattern": "def main", "directory_path": "/Users/project/src"}
        Output: "Grep results for 'def main' in '/Users/project/src':
        /Users/project/src/main.py:15:def main():
        /Users/project/src/app.py:8:    def main(self):"

        **Find import statements:**
        Input: {"pattern": "import os", "directory_path": "/Users/project"}
        Output: "Grep results for 'import os' in '/Users/project':
        /Users/project/src/utils.py:1:import os
        /Users/project/src/helpers.py:3:import os
        /Users/project/tests/test_utils.py:2:import os"

        **Search for TODO comments:**
        Input: {"pattern": "TODO|FIXME", "directory_path": "/Users/project"}
        Output: "Grep results for 'TODO|FIXME' in '/Users/project':
        /Users/project/src/api.py:45:# TODO: Add error handling
        /Users/project/src/db.py:120:# FIXME: This query is slow"

        **Search for configuration value:**
        Input: {"pattern": "DATABASE_URL", "directory_path": "/Users/project/config"}
        Output: "Grep results for 'DATABASE_URL' in '/Users/project/config':
        /Users/project/config/settings.py:12:DATABASE_URL = os.getenv('DB_URL')
        /Users/project/config/test.py:8:DATABASE_URL = 'localhost:5432'"

        **No matches found:**
        Input: {"pattern": "unicorn", "directory_path": "/Users/project/src"}
        Output: "No matches found for pattern 'unicorn' in '/Users/project/src'."

        ### Features
        - Recursive search (includes subdirectories)
        - Line numbers included in output
        - Extended regex supported (use | for OR, \\w+ for word patterns, etc.)
        - Ignores binary files automatically
        - Output truncated at 10KB if too large

        ### Tips
        - Use specific patterns to avoid overwhelming results
        - Chain with `read_file` to see context around matches
        - For case-insensitive search, use regex flag: "(?i)pattern"
        - """)
    
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

