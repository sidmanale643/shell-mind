import os
from .schema import ToolSchema
from textwrap import dedent

class WriteFileTool(ToolSchema):
    def __init__(self):
        self.name = "write_file"

    def description(self):
        return dedent("""
        Write content to a file, creating directories if needed.

        ### When to Use
        - Creating new files (config files, scripts, documentation)
        - Modifying existing file contents
        - Saving generated code, configurations, or outputs
        - Writing logs or reports to disk

        ### When NOT to Use
        - Use `read_file` to only view file contents
        - Use `run_command "cat file > newfile"` for simple copies (use write_file instead)
        - Be cautious when modifying system files or critical configs

        ### Parameters
        - `file_path`: Absolute path where the file should be written (required). Example: "/Users/project/config.yml"
        - `content`: The text content to write to the file (required). Can be multi-line.

        ### Output Format
        - Success: "File written successfully"
        - Error: "Error writing file: {reason}"

        ### Examples

        **Create a Python script:**
        Input: {
            "file_path": "/Users/project/scripts/setup.py",
            "content": "#!/usr/bin/env python3\\nimport os\\n\\ndef setup():\\n    print('Setting up...')\\n"
        }
        Output: "File written successfully"

        **Write a configuration file:**
        Input: {
            "file_path": "/Users/project/config/app.yml",
            "content": "version: '3'\\nservices:\\n  web:\\n    image: nginx:latest\\n    ports:\\n      - '80:80'\\n"
        }
        Output: "File written successfully"

        **Create a README:**
        Input: {
            "file_path": "/Users/project/README.md",
            "content": "# My Project\\n\\nThis is a sample project.\\n\\n## Installation\\n\\nRun `npm install` to get started.\\n"
        }
        Output: "File written successfully"

        **Overwrite an existing file:**
        Input: {
            "file_path": "/Users/project/existing.txt",
            "content": "This replaces the previous content completely."
        }
        Output: "File written successfully"

        ### Features
        - Creates parent directories automatically if they don't exist
        - Overwrites existing files completely (no append mode)
        - Must use absolute paths (starting with / on Unix/macOS)

        ### Important Notes
        - This tool OVERWRITES existing files completely
        - No backup is created before overwriting
        - Use `read_file` first if you need to check existing contents
        - Consider using `todo_manager` when making multiple file changes
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
                            "description": "The path to the file to write to"
                        },
                        "content": {
                            "type": "string",
                            "description": "The content to write to the file"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            }
        }
    
    def run(self, file_path: str, content: str):
        
        try:
            # Create directories if they don't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            with open(file_path, "w") as f:
                f.write(content)
            return "File written successfully"
        except Exception as e:
            return f"Error writing file: {e}"