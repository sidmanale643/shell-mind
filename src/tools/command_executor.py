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
        Executes shell commands and returns their output. Highly versatile for system administration and DevOps tasks.
        
        Use this tool to:
        - Inspect system status (processes, disk usage, memory, etc.).
        - Manage and query Docker containers, images, and Kubernetes resources.
        - Verify service status, read logs, and perform project-wide diagnostics.
        - Run arbitrary safe shell commands to automate tasks.
        
        Safety & Compliance:
        - Only safe and moderate commands are allowed; dangerous commands (e.g., recursive deletion, system shutdown) are blocked.
        - ALL commands require explicit user confirmation before execution.
        - Built-in protection against common destructive patterns.
        - Standard execution limits: 30s timeout and 10KB output truncation.
        
        Examples:
        - `docker ps -a`
        - `kubectl get pods -n production`
        - `systemctl status nginx`
        - `df -h`
        - `ps aux | grep nginx`
        
        Note: Commands are executed in the user's active shell environment.
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