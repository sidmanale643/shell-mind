import glob
from .schema import ToolSchema
from textwrap import dedent

class Glob(ToolSchema):
    def __init__(self):
        self.name = "glob"
    
    def description(self):
        return dedent("""
        Finds files matching a glob pattern with support for wildcards.

        ### When to Use
        - Finding all files of a certain type (e.g., all Python files)
        - Locating files by naming pattern across directories
        - Discovering configuration files in a project
        - Finding test files, logs, or assets

        ### When NOT to Use
        - Use `grep` to search within file contents
        - Use `read_file` to inspect specific files
        - Use `run_command "find ..."` only if glob can't handle your pattern

        ### Parameters
        - `pattern`: Glob pattern with wildcards (required). Supports:
          - `*` matches any files in one directory
          - `**` matches recursively across directories
          - `?` matches single characters
          - `[abc]` matches character sets
          Use absolute paths for best results.

        ### Output Format
        - Success: "Found {count} matches for pattern '{pattern}':\\n{file_list}"
        - No results: "No files found matching pattern: {pattern}"

        ### Examples

        **Find all Python files recursively:**
        Input: {"pattern": "/Users/project/**/*.py"}
        Output: "Found 5 matches for pattern '/Users/project/**/*.py':
        /Users/project/src/main.py
        /Users/project/src/utils.py
        /Users/project/tests/test_main.py
        /Users/project/tests/test_utils.py
        /Users/project/setup.py"

        **Find all YAML files in current directory:**
        Input: {"pattern": "/Users/project/*.yml"}
        Output: "Found 2 matches for pattern '/Users/project/*.yml':
        /Users/project/docker-compose.yml
        /Users/project/config.yml"

        **Find all test files:**
        Input: {"pattern": "/Users/project/**/*test*.py"}
        Output: "Found 3 matches for pattern '/Users/project/**/*test*.py':
        /Users/project/tests/test_api.py
        /Users/project/tests/test_db.py
        /Users/project/src/integrationtest.py"

        **No matches found:**
        Input: {"pattern": "/Users/project/**/*.go"}
        Output: "No files found matching pattern: /Users/project/**/*.go"

        ### Tips
        - Always use absolute paths (starting with /) for reliability
        - Use `**` for recursive searches (most common case)
        - Chain with `read_file` to inspect found files
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

