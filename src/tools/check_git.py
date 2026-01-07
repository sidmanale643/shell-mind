from textwrap import dedent
from .run_cmd import run_command

class GitInfo:
    def __init__(self):
        self.name = "git_info"
    
    def description(self):
        return dedent("""
        Retrieves essential Git metadata for the current repository.
        Provides a summary of `git status`, the latest commit log, current branch name, and configured remotes.
        
        Use this to:
        - Quickly assess the state of a repository.
        - Identify the current working branch and recent changes.
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
    
    def run(self):
        git_status = run_command("git status")
        git_log = run_command("git log -n 1")
        git_branch = run_command("git branch --show-current")
        git_remote = run_command("git remote -v")

        return dedent(f"""
        Git Status: {git_status}
        Git Log: {git_log}
        Git Remote: {git_remote}
        Git Branch: {git_branch}
        """)