from llm import LlmService
from prompt import SYSTEM_PROMPT, EXPLAIN_PROMPT
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.align import Align
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich import box
import subprocess
import json
import questionary
from tools.tool_registry import ToolRegistry
console = Console()

# --- Style Constants ---
THEME_PRIMARY = "bright_magenta"
THEME_SECONDARY = "cyan"
THEME_SUCCESS = "green"
THEME_WARNING = "yellow"
THEME_ERROR = "red"
THEME_DIM = "dim white"
THEME_COMMAND = "bright_cyan"

def get_spinner(message):
    return Spinner("dots", text=Text(message, style="bold green"))

class ShellMind:
    def __init__(self):
        self.llm = LlmService()
        self.messages = []
        self.tool_registry = ToolRegistry()
    
    def add_system_prompt(self, prompt=SYSTEM_PROMPT):
        self.messages.append({"role": "system", "content": prompt})
    
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
        with Live(get_spinner("Thinking..."), console=console, refresh_per_second=10, transient=True):
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
            console.print(Text.assemble(
                ("🔧 ", THEME_SECONDARY),
                ("Using tool: ", THEME_DIM),
                (tool_name, f"bold {THEME_COMMAND}")
            ))
            
            result = self.tool_registry.run_tool(tool_name, arguments)
            
            result_preview = result[:200] + "..." if len(result) > 200 else result
            console.print(Text(f"   ↳ {result_preview}", style=THEME_DIM))
            
            return result
        
        with Live(get_spinner("Thinking..."), console=console, refresh_per_second=10, transient=True):
            response, updated_messages = self.llm.generate_with_tools(
                messages=self.messages,
                tools=self.tool_registry.tool_schemas,
                tool_executor=execute_tool
            )
        
        # Sync messages back to self.messages (generate_with_tools updates them in place)
        self.messages = updated_messages
        
        # Format the final response content for display/storage (if it contains a command)
        # Note: We keep the original JSON in messages for LLM context, but format for display
        if response.output.content or response.output.command:
            content = response.output.content or ""
            if response.output.command:
                content += f"\nCommand: {response.output.command}"
            # Update the last assistant message with formatted content for consistency
            if self.messages and self.messages[-1].get("role") == "assistant":
                self.messages[-1]["content"] = content
            else:
                # If no assistant message exists (error case), add it
                self.messages.append({"role": "assistant", "content": content})
        
        return response

    
    def explain(self, user_input):
        # When explaining, we typically want a fresh context or to explain the specific input
        # If user_input is just "/explain", explain the last assistant message if it exists
        explain_content = user_input.replace('/explain', '').strip()
        
        if not explain_content:
            # Try to find the last assistant message
            last_msg = next((m["content"] for m in reversed(self.messages) if m["role"] == "assistant"), None)
            if last_msg:
                # If it's the custom format we just added
                if "Command: " in last_msg:
                    explain_content = last_msg.split("Command: ")[-1].strip()
                else:
                    explain_content = last_msg
            
        if not explain_content:
            return None

        # Start a fresh context for explanation to avoid interference
        temp_messages = [{"role": "system", "content": EXPLAIN_PROMPT}]
        temp_messages.append({"role": "user", "content": f"Explain this: {explain_content}"})
        
        with Live(get_spinner("Analyzing..."), console=console, refresh_per_second=10, transient=True):
            response = self.llm.generate(temp_messages)
        return response

    def display_response(self, response):
        console.print()  # Breathing room before response
        
        parts = []
        
        if response.thinking:
             parts.append(Text.assemble(
                 ("> ", THEME_SECONDARY),
                 ("Thought: ", f"bold {THEME_SECONDARY}"),
                 (response.thinking, THEME_DIM + " italic")
             ))
             parts.append("") # Spacer
        
        if response.output.content:
            # Check if content is raw JSON that should have been parsed
            content = response.output.content
            if content.strip().startswith('{') and ('"thinking"' in content or '"output"' in content):
                # This looks like raw JSON response - try to parse and extract meaningful content
                try:
                    parsed = json.loads(content)
                    # Extract the actual content from the parsed JSON
                    if isinstance(parsed, dict):
                        if "output" in parsed and isinstance(parsed["output"], dict):
                            if "content" in parsed["output"] and parsed["output"]["content"]:
                                content = parsed["output"]["content"]
                            elif "command" in parsed["output"]:
                                # If there's a command but no content, skip displaying raw JSON
                                content = None
                        elif "content" in parsed:
                            content = parsed["content"]
                except (json.JSONDecodeError, ValueError, KeyError):
                    # If parsing fails, don't display raw JSON - it's likely an error
                    content = "I received a response, but there was an issue formatting it. Please try again."
            
            if content:
                parts.append(Markdown(content))
                parts.append("")

        if response.output.command:
            parts.append(Panel(
                Text(response.output.command, style="bold " + THEME_COMMAND), 
                title=Text("Command", style="bold " + THEME_COMMAND), 
                title_align="left",
                border_style=THEME_COMMAND, 
                box=box.DOUBLE,
                padding=(1, 4)
            ))
            parts.append("")
        
        if response.output.warning:
             parts.append(Panel(
                 Text(response.output.warning, style="bold " + THEME_ERROR), 
                 title=Text("⚠️ Security Warning", style="bold " + THEME_ERROR), 
                 title_align="left",
                 border_style=THEME_ERROR,
                 box=box.HEAVY,
                 padding=(1, 4)
             ))
             parts.append("")

        console.print(Group(*parts))

    def handle_follow_ups(self, follow_ups):
        if not follow_ups:
            return None

        console.print()
        console.print(Align.center(Panel(
            Text("FOLLOW-UP REQUIRED", style="bold " + THEME_PRIMARY),
            border_style=THEME_PRIMARY,
            box=box.ROUNDED,
            padding=(0, 4)
        )))
        
        answers = []
        for idx, q in enumerate(follow_ups, 1):
            console.print()
            
            if q.options:
                question_text = Text.assemble(
                    (f"Question {idx}: ", "bold white"),
                    (q.question, "white")
                )
                console.print(Align.center(Panel(
                    question_text,
                    border_style=THEME_SECONDARY,
                    box=box.SQUARE,
                    padding=(1, 4)
                )))
                console.print()
                
                selected_option = questionary.select(
                    "",  
                    choices=q.options,
                    instruction=f"[{THEME_DIM}][Use ↑↓ arrows to navigate, Enter to select][/{THEME_DIM}]",
                    qmark="❯",
                    pointer="▶"
                ).ask()
                
                if not selected_option:
                    raise KeyboardInterrupt
                
                answers.append(f"Question: {q.question}\nAnswer: {selected_option}")
                console.print(Text.assemble(
                    ("✓ ", THEME_SUCCESS),
                    (f"Selected: {selected_option}", THEME_DIM)
                ))
            else:
                question_text = Text.assemble(
                    (f"Question {idx}: ", "bold white"),
                    (q.question, "white")
                )
                console.print(Align.center(Panel(
                    question_text,
                    title=Text("Clarification", style="bold " + THEME_WARNING),
                    border_style=THEME_WARNING,
                    box=box.ROUNDED,
                    padding=(1, 4)
                )))
                
                prompt_text = Text.assemble(
                    ("\n👤 ", THEME_SECONDARY),
                    ("Your answer", f"bold {THEME_SECONDARY}")
                )
                answer = Prompt.ask(prompt_text)
                answers.append(f"Question: {q.question}\nAnswer: {answer}")
                console.print(Text.assemble(
                    ("✓ ", THEME_SUCCESS),
                    (f"Recorded: {answer}", THEME_DIM)
                ))
        
        console.print()
        console.print(Text("Processing your answers...", style=THEME_DIM))
        return "\n".join(answers)
        
        console.print()
        console.print("[dim]Processing your answers...[/dim]")
        return "\n".join(answers)


def run_query(query_text, explain_mode=False, auto_execute=None):

    app = ShellMind()
    
    try:
        if explain_mode:
            response = app.explain(f"/explain {query_text}")
            if response:
                app.display_response(response)
                return 0
            else:
                console.print(Text("Could not explain the command.", style=THEME_WARNING))
                return 1
        
        # Regular query mode
        response = app.run(query_text)
        
        # Handle follow-ups loop
        while True:
            app.display_response(response)
            
            if response.follow_ups:
                answers = app.handle_follow_ups(response.follow_ups)
                response = app.run(f"Answers to follow-up questions:\n{answers}")
                continue
            
            if response.output.command:
                should_execute = auto_execute
                if should_execute is None:
                    confirm_text = Text("Execute this command?", style="bold " + THEME_WARNING)
                    should_execute = Confirm.ask(confirm_text)
                
                if should_execute:
                    console.print(Text(f"Executing: {response.output.command}", style=THEME_DIM))
                    try:
                        result = subprocess.run(response.output.command, shell=True, text=True, capture_output=True)
                        console.print()
                        if result.stdout:
                            console.print(Panel(
                                result.stdout.strip(), 
                                title=Text("✓ Execution Output", style="bold " + THEME_SUCCESS), 
                                border_style=THEME_SUCCESS,
                                box=box.ROUNDED,
                                padding=(1, 4)
                            ))
                        if result.stderr:
                            console.print(Panel(
                                result.stderr.strip(), 
                                title=Text("✖ Execution Error", style="bold " + THEME_ERROR), 
                                border_style=THEME_ERROR,
                                box=box.HEAVY,
                                padding=(1, 4)
                            ))
                        console.print()
                        return result.returncode
                    except Exception as exec_err:
                        console.print(Text(f"Execution Failed: {exec_err}", style="bold " + THEME_ERROR))
                        return 1
            break
        
        return 0
    
    except KeyboardInterrupt:
        console.print(Text("\nCancelled", style=THEME_WARNING))
        return 130
    except Exception as e:
        console.print(Text(f"Error: {e}", style="bold " + THEME_ERROR))
        return 1


def run_interactive():
    """Run ShellMind in interactive mode."""
    app = ShellMind()
    
    console.clear()
    
    # Title section with larger ASCII art and gradient effect
    console.print()
    title_lines = [
        " _____ _          _ _ __  __ _           _ ",
        " / ____| |        | | |  \/  (_)         | |",
        "| (___ | |__   ___| | | \  / |_ _ __   __| |",
        " \___ \| '_ \ / _ \ | | |\/| | | '_ \ / _` |",
        " ____) | | | |  __/ | | |  | | | | | | (_| |",
        "|_____/|_| |_|\___|_|_|_|  |_|_|_| |_|\__,_|"
    ]
    
    gradient_colors = [
        "bright_magenta",
        "magenta",
        "violet",
        "deep_sky_blue1",
        "cyan",
        "bright_cyan"
    ]
    
    for line, color in zip(title_lines, gradient_colors):
        console.print(Align.center(Text(line, style="bold " + color)))
    console.print()

    quick_start = Table.grid(padding=(0, 2))
    quick_start.add_row(
        Text("→", style=THEME_SECONDARY),
        Text.assemble(("Describe what you need: ", "white"), ("deploy a service, check logs, troubleshoot errors", "bold sky_blue1"))
    )
    quick_start.add_row(
        Text("→", style="magenta"),
        Text.assemble(("Break down commands with ", "white"), ("/explain", "bold cyan"), (" - shows what each part does", "dim"))
    )
    quick_start.add_row(
        Text("→", style=THEME_SUCCESS),
        Text.assemble(("Exit anytime with ", "white"), ("exit", "bold yellow"), (" or ", "white"), ("quit", f"bold {THEME_SUCCESS}"))
    )

    banner_content = Group(
        Text("Your intelligent shell assistant", style="bold white", justify="center"),
        Text("AI-driven command synthesis for a seamless terminal experience", style="dim italic", justify="center"),
        Text(""),
        Text("Quick Start:", style="bold bright_yellow"),
        Text(""),
        Align.left(quick_start)
    )

    panel = Panel(
        banner_content,
        border_style=THEME_PRIMARY,
        box=box.DOUBLE_EDGE,
        padding=(2, 8),
        expand=False
    )
    
    console.print()
    console.print(Align.center(panel))
    console.print()

    while True:
        try:
            prompt_text = Text.assemble(
                ("\n👤 ", THEME_SECONDARY),
                ("You", f"bold {THEME_SECONDARY}")
            )
            user_input = Prompt.ask(prompt_text)
            
            if user_input.lower().startswith('/explain'):
                response = app.explain(user_input)
                if response:
                    app.display_response(response)
                else:
                    console.print(Text("⚠️ Nothing to explain. Try '/explain <command>' or generate a command first.", style=THEME_WARNING))
                continue
            
            if user_input.lower() in ['exit', 'quit']:
                console.print(Text("👋 Goodbye!", style=THEME_WARNING))
                break
            
            response = app.run(user_input)
            
            while True:
                app.display_response(response)
                
                if response.follow_ups:
                    answers = app.handle_follow_ups(response.follow_ups)
                    response = app.run(f"Answers to follow-up questions:\n{answers}")
                    continue

                if response.output.command:
                    confirm_text = Text("Execute this command?", style="bold " + THEME_WARNING)
                    if Confirm.ask(confirm_text):
                        console.print(Text(f"Executing: {response.output.command}", style=THEME_DIM))
                        try:
                            result = subprocess.run(response.output.command, shell=True, text=True, capture_output=True)
                            console.print()
                            if result.stdout:
                                console.print(Panel(
                                    result.stdout.strip(), 
                                    title=Text("✓ Execution Output", style="bold " + THEME_SUCCESS), 
                                    border_style=THEME_SUCCESS,
                                    box=box.ROUNDED,
                                    padding=(1, 4)
                                ))
                            if result.stderr:
                                console.print(Panel(
                                    result.stderr.strip(), 
                                    title=Text("✖ Execution Error", style="bold " + THEME_ERROR), 
                                    border_style=THEME_ERROR,
                                    box=box.HEAVY,
                                    padding=(1, 4)
                                ))
                            console.print()
                        except Exception as exec_err:
                            console.print(Text(f"Execution Failed: {exec_err}", style="bold " + THEME_ERROR))
                break
                
        except KeyboardInterrupt:
            console.print(Text("\n👋 Goodbye!", style=THEME_WARNING))
            break
        except Exception as e:
            console.print(Text(f"An unexpected error occurred: {e}", style="bold " + THEME_ERROR))

if __name__ == "__main__":
    run_interactive()
