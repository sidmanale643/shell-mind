from llm import LlmService
from prompt import SYSTEM_PROMPT, EXPLAIN_PROMPT
from tools.tool_registry import ToolRegistry
from tools.env_detector import EnvironmentDetector
from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.spinner import Spinner
import json
from abc import ABC, abstractmethod
from rich.table import Table
from rich import box

class AgentUI(ABC):
    @abstractmethod
    def on_thinking_start(self, message: str): pass
    
    @abstractmethod
    def on_thinking_end(self): pass
    
    @abstractmethod
    def on_tool_start(self, tool_name: str, args: dict): pass
    
    @abstractmethod
    def on_tool_end(self, result: str): pass
    
    @abstractmethod
    def on_todo_update(self, todo_list: list): pass

    @abstractmethod
    def on_warning(self, message: str): pass

class RichConsoleUI(AgentUI):
    def __init__(self, console: Console = None):
        self.console = console or Console()
        self.live = None
        self.progress = None
        
    def _get_spinner(self, message):
        return Spinner("dots", text=Text(message, style="bold green"))

    def on_thinking_start(self, message: str):
        if self.live:
            self.live.stop()
        self.live = Live(self._get_spinner(message), console=self.console, refresh_per_second=10, transient=True)
        self.live.start()

    def on_thinking_end(self):
        if self.live:
            self.live.stop()
            self.live = None

    def on_tool_start(self, tool_name: str, args: dict):
        # We stop the live spinner for tool execution to allow for user interaction
        # (e.g. confirmation prompts) and clean output logging.
        if self.live and self.live.is_started:
            self.live.stop()
        
        # Show more informative tool usage message
        args_preview = ""
        if args:
            # Show first argument as preview
            first_key = list(args.keys())[0] if args else None
            if first_key and args[first_key]:
                arg_value = str(args[first_key])
                if len(arg_value) > 50:
                    arg_value = arg_value[:47] + "..."
                args_preview = f" ({arg_value})"
            
        self.console.print(Text.assemble(
            ("🔧 ", "cyan"),
            ("Using tool: ", "dim white"),
            (tool_name, "bold bright_cyan"),
            (args_preview, "dim italic")
        ))
        
        # We do NOT restart the spinner here. It stays stopped while the tool runs.
        # This is critical for interactive tools (like run_command asking for confirmation).
        # It will be restarted in on_tool_end.

    def on_tool_end(self, result: str):
        # Print a short preview of the result 
        result_preview = result[:200] + "..." if len(result) > 200 else result
        self.console.print(Text(f"   ↳ {result_preview}", style="dim white"))
        
        # Restart the thinking spinner if it was active before the tool started
        if self.live and not self.live.is_started:
            self.live.start()

    def on_todo_update(self, todo_list: list):
        if not todo_list:
            return
            
        table = Table(title="📝 Task List", show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("Status", width=12)
        table.add_column("Task")
        
        for item in todo_list:
            task = item.get("task", "Unknown")
            status = item.get("status", "pending")
            
            status_text = status.lower()
            if status_text == "completed":
                status_display = Text("✓ Done", style="bold green")
                task_display = Text(task, style="dim strikethrough")
            elif status_text == "in_progress":
                status_display = Text("▶ Active", style="bold yellow")
                task_display = Text(task, style="bold white")
            else:
                status_display = Text("○ Pending", style="dim white")
                task_display = Text(task)
                
            table.add_row(status_display, task_display)
            
        self.console.print()
        self.console.print(table)
        self.console.print()

    def on_warning(self, message: str):
        self.console.print(f"[dim red]Warning: {message}[/dim red]")

class ShellMind:
    def __init__(self, ui: AgentUI = None, console: Console = None):
        self.llm = LlmService()
        self.messages = []
        self.console = console or Console()
        self.tool_registry = ToolRegistry(console=self.console)
        # Backwards compatibility: if console is provided but no ui, use RichConsoleUI
        if ui is None:
            self.ui = RichConsoleUI(console)
        else:
            self.ui = ui
        # Maintain a single TODO list that gets updated
        self.current_todo_list = []
    
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
            self.ui.on_warning(f"Could not detect environment: {e}")
    
    def add_user_message(self, user_input):
        self.messages.append({"role": "user", "content": user_input})

    def run(self, user_input, use_tools=True, max_iterations=30):
        if not self.messages:
            self.add_system_prompt()
        
        self.add_user_message(user_input)
        
        if not use_tools or not self.tool_registry.tool_schemas:
            return self._run_without_tools()

        # Main agent loop for tool use and multi-step reasoning
        for i in range(max_iterations):
            response, should_stop = self._run_with_tools_step()
            if should_stop:
                return response
        
        # If we reached here, it means max_iterations was exceeded
        from llm import Response, Output
        return Response(
            thinking="Max iterations reached",
            output=Output(content="I reached the maximum number of iterations for this task. Please try a more specific request.")
        )
    
    def _run_without_tools(self):
        self.ui.on_thinking_start("Thinking...")
        try:
            response = self.llm.generate(self.messages)
        finally:
            self.ui.on_thinking_end()

        if response.output.content or response.output.command:
            content = response.output.content or ""
            if response.output.command:
                content += f"\\nCommand: {response.output.command}"
            self.messages.append({"role": "assistant", "content": content})
        
        return response
    
    def _run_with_tools_step(self):
        """Perform a single iteration of the tool loop."""
        self.ui.on_thinking_start("Thinking...")
        try:
            # 1. Ask LLM what to do
            chat_completion = self.llm.get_raw_completion(
                self.messages, 
                self.tool_registry.tool_schemas
            )
        finally:
            self.ui.on_thinking_end()

        response_message = chat_completion.choices[0].message
        tool_calls = getattr(response_message, 'tool_calls', None)
        
        # If no tool calls, get the final structured response and stop
        if not tool_calls:
            self.ui.on_thinking_start("Thinking...")
            try:
                response = self.llm.generate(self.messages)
            finally:
                self.ui.on_thinking_end()

            # Add to history (structured representation)
            self.messages.append({
                "role": "assistant",
                "content": str(response)
            })
            return response, True

        # If tool calls, execute them
        self.messages.append({
            "role": "assistant",
            "content": response_message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in tool_calls
            ]
        })
        
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                args = {}
                
            self.ui.on_tool_start(tool_name, args)
            result = self.tool_registry.run_tool(tool_name, args)
            
            # Update and display the single TODO list
            if tool_name == "todo_manager" and isinstance(result, list):
                # Update the current todo list with the new result
                self.current_todo_list = result
                self.ui.on_todo_update(self.current_todo_list)
                
            self.ui.on_tool_end(str(result))
            
            self.messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_name,
                "content": str(result)
            })
            
        return None, False

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
        
        self.ui.on_thinking_start("Analyzing...")
        try:
            response = self.llm.generate(temp_messages)
        finally:
            self.ui.on_thinking_end()
        return response


