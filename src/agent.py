from llm import LlmService
from prompt import SYSTEM_PROMPT, EXPLAIN_PROMPT
from tools.tool_registry import ToolRegistry
from tools.env_detector import EnvironmentDetector
from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.spinner import Spinner
from rich.prompt import Confirm
import json

# We'll keep a local console for the spinner, but ideally this would be passed in
console = Console()

def get_spinner(message):
    return Spinner("dots", text=Text(message, style="bold green"))

class ShellMind:
    def __init__(self, console=None):
        self.llm = LlmService()
        self.messages = []
        self.tool_registry = ToolRegistry()
        self.console = console or Console()
    
    def add_system_prompt(self, prompt=SYSTEM_PROMPT):
        self.messages.append({"role": "system", "content": prompt})
        
        try:
            detector = EnvironmentDetector()
            env_info = detector.run()
            self.messages.append({
                "role": "system", 
                "content": f"Current Environment Information:\n{env_info}"
            })
        except Exception as e:
            self.console.print(f"[dim red]Warning: Could not detect environment: {e}[/dim red]")
    
    def add_user_message(self, user_input):
        self.messages.append({"role": "user", "content": user_input})

    def add_tool_message(self, tool_call, tool_output):
        message = {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": tool_call.function.name,
            "content": tool_output
        }
        self.messages.append(message)

    def run(self, user_input, use_tools=True):
        if not self.messages:
            self.add_system_prompt()
        
        self.add_user_message(user_input)
        
        if use_tools and self.tool_registry.tool_schemas:
            return self._run_with_tools()
        else:
            return self._run_without_tools()
    
    def _run_without_tools(self):
        """Run without tool support (original behavior)."""
        with Live(get_spinner("Thinking..."), console=self.console, refresh_per_second=10, transient=True):
            response = self.llm.generate(self.messages)

        if response.output.content or response.output.command:
            content = response.output.content or ""
            if response.output.command:
                content += f"\nCommand: {response.output.command}"
            self.messages.append({"role": "assistant", "content": content})
        
        return response
    
    def _run_with_tools(self):
        tool_call_count = [0] 
        
        def execute_tool(tool_name: str, arguments: dict) -> str:
            tool_call_count[0] += 1
            
            # Still doing some printing here for progress, but using self.console
            self.console.print(Text.assemble(
                ("🔧 ", "cyan"),
                ("Using tool: ", "dim white"),
                (tool_name, "bold bright_cyan")
            ))
            
            result = self.tool_registry.run_tool(tool_name, arguments)
            
            result_preview = result[:200] + "..." if len(result) > 200 else result
            self.console.print(Text(f"   ↳ {result_preview}", style="dim white"))
            
            return result
        
        with Live(get_spinner("Thinking..."), console=self.console, refresh_per_second=10, transient=True):
            response, updated_messages = self.llm.generate_with_tools(
                messages=self.messages,
                tools=self.tool_registry.tool_schemas,
                tool_executor=execute_tool
            )
        
        # Sync messages back to self.messages
        self.messages = updated_messages
        
        if response.output.content or response.output.command:
            content = response.output.content or ""
            if response.output.command:
                content += f"\nCommand: {response.output.command}"
            if self.messages and self.messages[-1].get("role") == "assistant":
                self.messages[-1]["content"] = content
            else:
                self.messages.append({"role": "assistant", "content": content})
        
        return response

    def explain(self, user_input):
        explain_content = user_input.replace('/explain', '').strip()
        
        if not explain_content:
            last_msg = next((m["content"] for m in reversed(self.messages) if m["role"] == "assistant"), None)
            if last_msg:
                if "Command: " in last_msg:
                    explain_content = last_msg.split("Command: ")[-1].strip()
                else:
                    explain_content = last_msg
            
        if not explain_content:
            return None

        temp_messages = [{"role": "system", "content": EXPLAIN_PROMPT}]
        temp_messages.append({"role": "user", "content": f"Explain this: {explain_content}"})
        
        with Live(get_spinner("Analyzing..."), console=self.console, refresh_per_second=10, transient=True):
            response = self.llm.generate(temp_messages)
        return response

