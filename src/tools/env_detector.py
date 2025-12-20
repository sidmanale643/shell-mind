import os
import platform
import subprocess
import shutil
from .schema import ToolSchema
from textwrap import dedent

class EnvironmentDetector(ToolSchema):
    def __init__(self):
        self.name = "env_detector"
    
    def description(self):
        return dedent("""
        Gathers information about the user's environment, including OS, shell, CWD, and available tools.
        Use this tool to understand the context in which commands will be executed.
        Returns a JSON-formatted string with environment details.
        """)
    
    def json_schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    
    def _check_tool(self, tool_name):
        return shutil.which(tool_name) is not None

    def run(self):
        env_info = {
            "os": platform.system(),
            "os_release": platform.release(),
            "shell": os.environ.get("SHELL", "unknown"),
            "cwd": os.getcwd(),
            "installed_tools": {},
        }

        tools_to_check = [
            "git", "docker", "kubectl", "terraform", "aws", 
            "gcloud", "helm", "brew", "apt", "python", "node"
        ]
        for tool in tools_to_check:
            env_info["installed_tools"][tool] = self._check_tool(tool)

        if env_info["installed_tools"]["git"]:
            try:
                branch = subprocess.check_output(
                    ["git", "branch", "--show-current"], 
                    stderr=subprocess.DEVNULL, 
                    text=True
                ).strip()
                if branch:
                    env_info["git_branch"] = branch
                    
                status = subprocess.check_output(
                    ["git", "status", "--short"], 
                    stderr=subprocess.DEVNULL, 
                    text=True
                ).strip()
                if status:
                    env_info["git_status"] = "dirty" if status else "clean"
            except Exception:
                pass

        import json
        return json.dumps(env_info, indent=2)
