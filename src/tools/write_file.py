import os
from .schema import ToolSchema
from textwrap import dedent

class WriteFileTool(ToolSchema):
    def __init__(self):
        self.name = "write_file"

    def description(self):
        return dedent("""
        Use this tool to write a file to the local filesystem.
        The file_path parameter must be an absolute path, not a relative path.
        If the directory does not exist, it will be created.
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