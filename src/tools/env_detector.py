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
        Gathers comprehensive details about the current execution environment.
        Includes OS version, active shell, current working directory, and availability of key DevOps tools (git, docker, kubectl, etc.).
        
        Use this at the start of a task to:
        - Determine which commands are compatible with the OS.
        - Check if necessary CLI tools are installed.
        - Understand the current project context (e.g., active git branch).
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
