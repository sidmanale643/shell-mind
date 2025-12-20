from .run_cmd import run_command

class CheckProcess:
    def __init__(self):
        self.name = "check_process"
    
    def description(self):
        return """
        Checks if a process is running.
        """
    
    def json_schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "process_name": {
                            "type": "string",
                            "description": "The name of the process to check"
                        }
                    },
                    "required": ["process_name"]
                }
            }
        }
    
    def run(self, process_name):
        # Use a bracket trick to avoid grep finding itself
        if process_name:
            pattern = f"[{process_name[0]}]{process_name[1:]}"
            return run_command(f"ps aux | grep {pattern}")
        return "No process name provided"
