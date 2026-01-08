import subprocess
from .schema import ToolSchema
from textwrap import dedent

class FileReader(ToolSchema):
    def __init__(self):
        self.name = "read_file"
    
    def description(self):
        return dedent("""
    Read file contents with line numbers. Works for any accessible file on the system.

    ### When to Use
    - Reading source code, config files, documentation
    - Inspecting docker-compose.yml, Kubernetes manifests, README files
    - Viewing logs or any text-based file
    - Checking file contents before making changes

    ### When NOT to Use
    - Use `list_file` to just check directory contents
    - Use `grep` to search across multiple files
    - Use `glob` to find files by pattern
    - Use `write_file` to create or modify files

    ### Parameters
    - `file_path`: Absolute path to the file (required). Example: "/Users/project/app.py"

    ### Output Format
    - Success: "File Content:\\n{line_number}\\t{content}"
    - Empty file: "File is empty"
    - Not found: "File does not exist"
    - Restricted: "Restricted access to .env (environment) files"

    ### Examples

    **Read a Python file:**
    Input: {"file_path": "/Users/project/src/main.py"}
    Output: "File Content:\\n1\\timport os\\n2\\t\\n3\\tdef main():\\n..."

    **Read a Docker Compose file:**
    Input: {"file_path": "/Users/project/docker-compose.yml"}
    Output: "File Content:\\n1\\tversion: '3'\\n2\\tservices:\\n3\\t  web:..."

    **File doesn't exist:**
    Input: {"file_path": "/Users/project/missing.txt"}
    Output: "File does not exist"

    ### Important Constraints
    - .env files are blocked for security
    - Maximum file size: 1MB (larger files will be truncated)
    - Must use absolute paths (starting with / on Unix/macOS)
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
                    "file_path": {
                        "type": "string",
                        "description": "the path of the file to read"
                    }
                },
                "required": ["file_path"]
            }
        }
    }
    
    def run(self, file_path: str):

        if ".env" in file_path:
            return "Restricted access to .env (environment) files"

        file_content = subprocess.run(
            f"cat -n {file_path}",
            shell=True,
            capture_output=True,
            text=True
        )

        if file_content.returncode != 0:
            error_msg = file_content.stderr.strip()
            if "No such file or directory" in error_msg:
                return "File does not exist"
            return f"Error reading file: {error_msg or 'Unknown error.'}"

        if not file_content.stdout.strip():
            return "File is empty"

        return f"File Content:\n{file_content.stdout.strip()}"
        
