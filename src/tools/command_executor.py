import subprocess
import json
import time
from .schema import ToolSchema
from textwrap import dedent
from rich.console import Console
from rich.text import Text
from rich.prompt import Confirm


class CommandExecutor(ToolSchema):
    """
    Executes shell commands with safety constraints.
    Classifies commands by risk level and enforces execution policies.
    """
    
    def __init__(self, console=None):
        self.name = "run_command"
        self.console = console or Console()
        
        # Safe read-only commands that can be executed without restrictions
        self.safe_prefixes = [
            "ls", "cat", "head", "tail", "grep", "find", "wc", "echo",
            "ps", "top", "htop", "df", "du", "free", "uptime", "whoami",
            "pwd", "which", "whereis", "file", "stat", "date",
            "docker ps", "docker images", "docker inspect", "docker logs", "docker stats",
            "kubectl get", "kubectl describe", "kubectl logs", "kubectl top",
            "git status", "git log", "git diff", "git branch", "git show",
            "systemctl status", "systemctl list-units", "journalctl",
            "aws s3 ls", "aws ec2 describe-instances", "gcloud compute instances list",
            "terraform show", "terraform plan", "helm list", "helm status",
            "curl -s", "curl -L", "curl -I", "curl --head", "curl http",
            "wget --spider", "ping", "dig", "nslookup", "netstat", "ss",
            "env", "printenv", "uname", "hostname"
        ]
        
        # Dangerous commands that should never be executed
        self.dangerous_patterns = [
            "rm -rf", "rm -fr", "rm -r", "rm -f",
            "dd if=", "mkfs", "fdisk", "parted",
            "> /dev/", "shutdown", "reboot", "halt", "poweroff",
            "kill -9", "killall", "pkill -9",
            "chmod 777", "chown -R", "chmod -R 777",
            ":(){ :|:& };:",  # Fork bomb
            "mv /", "cp -r /", "rsync -a /",
            "curl -X POST", "curl -X PUT", "curl -X DELETE", "curl -X PATCH",
            "wget -O", "wget --post", "wget --delete",
            "docker rm", "docker rmi", "docker system prune",
            "kubectl delete", "kubectl apply", "kubectl create",
            "git push --force", "git push -f", "git reset --hard", "git clean -fd",
            "npm install -g", "pip install", "apt install", "yum install", "brew install",
            "systemctl stop", "systemctl restart", "systemctl disable",
            "iptables", "ufw", "firewall-cmd",
            "crontab -r", "at ", "batch",
            "sudo su", "su -", "sudo -i"
        ]
        
        # Moderate commands that need confirmation but aren't dangerous
        self.moderate_patterns = [
            "git push",  # Safe git push (not force)
            "curl -X",   # Other HTTP methods
            "wget "      # Basic wget downloads
        ]
    
    def description(self):
        return dedent("""
        Execute shell commands with safety checks and user confirmation.

        ### When to Use
        - Running system administration commands (ps, df, systemctl, etc.)
        - Managing Docker containers and images
        - Managing Kubernetes resources (kubectl)
        - Git operations (status, log, diff, branch)
        - Cloud CLI operations (aws, gcloud, az)
        - Running custom scripts or commands not available as dedicated tools
        - Checking service status, logs, and diagnostics

        ### When NOT to Use
        - Use `read_file` instead of `cat file.txt`
        - Use `glob` instead of `find` commands for simple file searches
        - Use `grep` tool instead of `grep` command for text searches
        - Use `list_file` instead of `ls` for directory listings
        - Dangerous commands will be automatically blocked

        ### Parameters
        - `command`: Shell command to execute (required). Examples: "docker ps", "kubectl get pods"
        - `timeout`: Maximum execution time in seconds (optional, default: 30)

        ### Output Format
        Returns JSON with structure:
        ```json
        {
            "success": true/false,
            "command": "the executed command",
            "return_code": 0,
            "stdout": "standard output content",
            "stderr": "error output content",
            "execution_time": 1.23,
            "risk_level": "safe|moderate|dangerous",
            "stdout_truncated": false,
            "stderr_truncated": false
        }
        ```
        Or on user rejection:
        ```json
        {
            "success": false,
            "error": "User rejected the command",
            "command": "..."
        }
        ```

        ### Examples

        **List Docker containers (safe - auto-executed):**
        Input: {"command": "docker ps -a"}
        Output: {
            "success": true,
            "command": "docker ps -a",
            "return_code": 0,
            "stdout": "CONTAINER ID   IMAGE     STATUS   NAMES\\nabc123   nginx     Up       web",
            "stderr": "",
            "execution_time": 0.45,
            "risk_level": "safe"
        }

        **Check service status (safe - auto-executed):**
        Input: {"command": "systemctl status nginx"}
        Output: {
            "success": true,
            "command": "systemctl status nginx",
            "return_code": 0,
            "stdout": "● nginx.service - A high performance web server\\n   Loaded: loaded...",
            "risk_level": "safe"
        }

        **Get Kubernetes pods (safe - auto-executed):**
        Input: {"command": "kubectl get pods -n production"}
        Output: {
            "success": true,
            "command": "kubectl get pods -n production",
            "return_code": 0,
            "stdout": "NAME              READY   STATUS    RESTARTS   AGE\\napp-pod-7d8f   1/1     Running   0          2d",
            "risk_level": "safe"
        }

        **User rejects command:**
        Input: {"command": "git push origin main"}
        Output: {
            "success": false,
            "error": "User rejected the command",
            "command": "git push origin main"
        }

        **Dangerous command blocked:**
        Input: {"command": "rm -rf /important/data"}
        Output: {
            "success": false,
            "error": "Command rejected: This command is classified as dangerous and cannot be executed.",
            "risk_level": "dangerous",
            "command": "rm -rf /important/data",
            "suggestion": "Please run this command manually if you're certain it's safe."
        }

        ### Safety Classification

        **Safe Commands** (executed after confirmation):
        - Read-only commands: ls, cat, ps, df, docker ps, kubectl get, git status/log/diff
        - Status checks: systemctl status, service status, top, htop
        - Network diagnostics: ping, curl, wget, dig, nslookup

        **Moderate Commands** (require confirmation):
        - git push, curl with -X, wget downloads
        - Any command not in safe list

        **Dangerous Commands** (blocked):
        - Destructive: rm -rf, dd, mkfs, shutdown, reboot
        - System modifications: chmod 777, chown -R, iptables
        - Force operations: git push --force, kubectl delete, docker rmi

        ### Important Notes
        - ALL commands require user confirmation before execution
        - Commands timeout after 30 seconds by default
        - Output is truncated at 10KB for stdout and stderr
        - Commands run in the user's active shell environment
        - If user rejects a command, DO NOT retry immediately
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
                        "command": {
                            "type": "string",
                            "description": "The shell command to execute (e.g., 'docker ps', 'ls -la /tmp')"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds (default: 30)",
                            "default": 30
                        }
                    },
                    "required": ["command"]
                }
            }
        }
    
    def _classify_risk(self, command: str) -> str:
        """
        Classify command risk level with context-aware detection.
        Returns: 'safe', 'moderate', or 'dangerous'
        """
        command_lower = command.lower().strip()
        
        # Check for dangerous patterns first
        for pattern in self.dangerous_patterns:
            if pattern.lower() in command_lower:
                return "dangerous"
        
        # Check for moderate patterns (commands that need confirmation but aren't dangerous)
        for pattern in self.moderate_patterns:
            if pattern.lower() in command_lower:
                return "moderate"
        
        # Check for safe prefixes
        for prefix in self.safe_prefixes:
            if command_lower.startswith(prefix.lower()):
                return "safe"
        
        # Default to moderate for unknown commands
        return "moderate"
    
    def _is_safe_command(self, command: str) -> bool:
        """Check if command is safe to execute."""
        risk = self._classify_risk(command)
        return risk == "safe"
    
    def run(self, command: str, timeout: int = 30):
        """
        Execute a shell command with safety checks.
        
        Args:
            command: Shell command to execute
            timeout: Maximum execution time in seconds
            
        Returns:
            JSON string with execution results
        """
        # Validate command safety
        risk_level = self._classify_risk(command)
        
        if risk_level == "dangerous":
            return json.dumps({
                "success": False,
                "error": "Command rejected: This command is classified as dangerous and cannot be executed.",
                "risk_level": "dangerous",
                "command": command,
                "suggestion": "Please run this command manually if you're certain it's safe."
            }, indent=2)

        THEME_WARNING = "yellow"
        self.console.print(Text.assemble(
            ("Command to execute: ", "bold white"),
            (command, "bold bright_cyan")
        ))
        confirm_text = Text("Execute this command?", style="bold " + THEME_WARNING)
        
        should_execute = Confirm.ask(confirm_text)

        if should_execute:
            try:
                start_time = time.time()
                
                with self.console.status(f"[bold green]Running: {command}"):
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=timeout
                    )
                
                execution_time = time.time() - start_time
                
                # Limit output size to 10KB
                max_output_size = 10 * 1024  # 10KB
                stdout = result.stdout[:max_output_size]
                stderr = result.stderr[:max_output_size]
                
                stdout_truncated = len(result.stdout) > max_output_size
                stderr_truncated = len(result.stderr) > max_output_size
                
                return json.dumps({
                    "success": result.returncode == 0,
                    "command": command,
                    "return_code": result.returncode,
                    "stdout": stdout.strip() if stdout else "",
                    "stderr": stderr.strip() if stderr else "",
                    "execution_time": round(execution_time, 2),
                    "stdout_truncated": stdout_truncated,
                    "stderr_truncated": stderr_truncated,
                    "risk_level": risk_level
                }, indent=2)
                
            except subprocess.TimeoutExpired:
                return json.dumps({
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds",
                    "command": command,
                    "timeout": timeout
                }, indent=2)
                
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": f"Execution failed: {str(e)}",
                    "command": command
                }, indent=2)

        else:
            return json.dumps({
                "success": False,
                "error": "User rejected the command",
                "command": command
            }, indent=2)