#!/usr/bin/env python3
"""ShellMind CLI - Command-line interface for ShellMind"""

import sys
import json
import subprocess
from pathlib import Path
import click
import questionary
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.align import Align
from rich.text import Text
from rich.table import Table
from rich import box
from rich.rule import Rule
from rich.padding import Padding

# Add src to path so we can import from it
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from agent import ShellMind  # noqa: E402
from config import ConfigManager  # noqa: E402
from ui_utils import syntax_highlight_output, format_command_with_explanation  # noqa: E402

# --- UI Constants ---
THEME_PRIMARY = "bright_magenta"
THEME_SECONDARY = "bright_cyan"
THEME_SUCCESS = "bright_green"
THEME_WARNING = "bright_yellow"
THEME_ERROR = "bright_red"
THEME_DIM = "grey70"
THEME_COMMAND = "dodger_blue2"
THEME_ACCENT = "deep_pink2"
THEME_SUBTLE = "grey50"

console = Console(highlight=True)
config_manager = ConfigManager()

def display_response(response):
    console.print()  # Breathing room before response
    
    parts = []
    
    if response.thinking:
        # More elegant thinking display with subtle styling
        thinking_content = Padding(
            Text.assemble(
                ("💭 ", THEME_ACCENT),
                ("Thinking: ", "bold " + THEME_ACCENT),
                (response.thinking, THEME_SUBTLE + " italic")
            ),
            (0, 2)
        )
        parts.append(Panel(
            thinking_content,
            border_style=THEME_SUBTLE,
            box=box.ROUNDED,
            padding=(0, 2)
        ))
        parts.append("") # Spacer
    
    if response.output.content:
        content = response.output.content
        
        # Check if content looks like raw JSON (should have been parsed already, but handle it just in case)
        if content.strip().startswith('{'):
            try:
                # Try to parse as JSON
                parsed = json.loads(content)
                if isinstance(parsed, dict):
                    # If we have a nested structure, extract the actual content
                    if "output" in parsed and isinstance(parsed["output"], dict):
                        if "content" in parsed["output"] and parsed["output"]["content"]:
                            content = parsed["output"]["content"]
                        elif "command" in parsed["output"]:
                            # Only command, no content to display
                            content = None
                        else:
                            # Output dict but no meaningful content
                            content = None
                    elif "content" in parsed:
                        content = parsed["content"]
                    else:
                        # JSON but not the expected structure - don't display raw JSON
                        content = None
            except (json.JSONDecodeError, ValueError, KeyError):
                # Not valid JSON, display as-is (or hide if it looks malformed)
                if '"thinking"' in content or '"output"' in content or '"command"' in content:
                    # Looks like malformed JSON response, don't display
                    content = None
        
        if content and content.strip():
            # Elegant content panel with subtle border
            content_panel = Panel(
                Markdown(content),
                border_style=THEME_SECONDARY,
                box=box.ROUNDED,
                padding=(1, 2),
                title=Text("▸ Response", style="bold " + THEME_SECONDARY),
                title_align="left"
            )
            parts.append(content_panel)
            parts.append("")

    if response.output.command:
        # Format command with inline explanations
        formatted_command = format_command_with_explanation(response.output.command)
        
        # Beautiful command panel with enhanced styling
        parts.append(Panel(
            Padding(formatted_command, (1, 2)), 
            title=Text("⚡ Command", style="bold " + THEME_COMMAND), 
            title_align="left",
            border_style=THEME_COMMAND, 
            box=box.HEAVY,
            padding=(0, 2)
        ))
        parts.append("")
    
    if response.output.warning:
        # Enhanced warning panel with better visibility
        parts.append(Panel(
            Text(response.output.warning, style=f"bold {THEME_WARNING}"), 
            title=Text("⚠️  Security Warning", style=f"bold {THEME_ERROR}"), 
            title_align="left",
            border_style=THEME_ERROR,
            box=box.DOUBLE,
            padding=(1, 3)
        ))
        parts.append("")

    console.print(Group(*parts))

def handle_follow_ups(app, follow_ups):
    if not follow_ups:
        return None

    console.print()
    
    # Elegant follow-up header with rule
    console.print(Rule(
        Text("✦ Follow-up Required ✦", style=f"bold {THEME_PRIMARY}"),
        style=THEME_PRIMARY
    ))
    console.print()
    
    answers = []
    for idx, q in enumerate(follow_ups, 1):
        console.print()
        
        if q.options:
            question_text = Text.assemble(
                (f"❓ Question {idx}: ", f"bold {THEME_ACCENT}"),
                (q.question, "white")
            )
            console.print(Panel(
                question_text,
                border_style=THEME_SECONDARY,
                box=box.ROUNDED,
                padding=(1, 3)
            ))
            console.print()
            
            selected_option = questionary.select(
                "",  
                choices=q.options,
                instruction="[Use ↑↓ arrows to navigate, Enter to select]",
                qmark="▸",
                pointer="❯"
            ).ask()
            
            if not selected_option:
                raise KeyboardInterrupt
            
            answers.append(f"Question: {q.question}\nAnswer: {selected_option}")
            console.print(Text.assemble(
                ("  ✓ ", THEME_SUCCESS),
                ("Selected: ", "bold " + THEME_SUCCESS),
                (selected_option, THEME_DIM)
            ))
        else:
            question_text = Text.assemble(
                (f"❓ Question {idx}: ", f"bold {THEME_ACCENT}"),
                (q.question, "white")
            )
            console.print(Panel(
                question_text,
                title=Text("Clarification Needed", style=f"bold {THEME_WARNING}"),
                border_style=THEME_WARNING,
                box=box.ROUNDED,
                padding=(1, 3)
            ))
            
            prompt_text = Text.assemble(
                ("\n  ✎ ", THEME_SECONDARY),
                ("Your answer", f"bold {THEME_SECONDARY}")
            )
            answer = Prompt.ask(prompt_text)
            answers.append(f"Question: {q.question}\nAnswer: {answer}")
            console.print(Text.assemble(
                ("  ✓ ", THEME_SUCCESS),
                ("Recorded: ", "bold " + THEME_SUCCESS),
                (answer, THEME_DIM)
            ))
    
    console.print()
    console.print(Text("⏳ Processing your answers...", style=f"italic {THEME_SUBTLE}"))
    return "\n".join(answers)

def run_query(query_text, explain_mode=False, auto_execute=None, use_tools=False):
    app = ShellMind(console=console)
    
    try:
        if explain_mode:
            response = app.explain(f"/explain {query_text}")
            if response:
                display_response(response)
                return 0
            else:
                console.print(Text("Could not explain the command.", style=THEME_WARNING))
                return 1
        
        # Regular query mode
        response = app.run(query_text, use_tools=use_tools)
        
        # Handle follow-ups and commands loop
        while True:
            display_response(response)
            
            # Step 1: Handle command execution if present
            if response.output.command:
                should_execute = auto_execute
                if should_execute is None:
                    confirm_text = Text("Execute this command?", style="bold " + THEME_WARNING)
                    should_execute = Confirm.ask(confirm_text)
                
                if should_execute:
                    console.print(Text(f"⚙️  Executing: {response.output.command}", style=f"italic {THEME_SUBTLE}"))
                    console.print()
                    try:
                        result = subprocess.run(response.output.command, shell=True, text=True, capture_output=True)
                        console.print()
                        if result.stdout:
                            # Apply syntax highlighting to output
                            highlighted_output = syntax_highlight_output(result.stdout.strip())
                            console.print(Panel(
                                highlighted_output, 
                                title=Text("✓ Execution Output", style=f"bold {THEME_SUCCESS}"), 
                                border_style=THEME_SUCCESS,
                                box=box.ROUNDED,
                                padding=(1, 2),
                                title_align="left"
                            ))
                        if result.stderr:
                            console.print(Panel(
                                result.stderr.strip(), 
                                title=Text("✖ Error Output", style=f"bold {THEME_ERROR}"), 
                                border_style=THEME_ERROR,
                                box=box.ROUNDED,
                                padding=(1, 2),
                                title_align="left"
                            ))
                        console.print()
                        # If this was the last step (no follow-ups), we can return the exit code
                        if not response.follow_ups:
                            return result.returncode
                    except Exception as exec_err:
                        console.print(Text(f"✖ Execution Failed: {exec_err}", style=f"bold {THEME_ERROR}"))
                        if not response.follow_ups:
                            return 1

            # Step 2: Handle follow-ups if present
            if response.follow_ups:
                answers = handle_follow_ups(app, response.follow_ups)
                response = app.run(f"Answers to follow-up questions:\n{answers}", use_tools=use_tools)
                continue
            
            # If no follow-ups, we've finished this turn
            break
        
        return 0
    
    except KeyboardInterrupt:
        console.print(Text("\nCancelled", style=THEME_WARNING))
        return 130
    except Exception as e:
        console.print(Text(f"Error: {e}", style="bold " + THEME_ERROR))
        return 1

def run_interactive(use_tools=False):
    """Run ShellMind in interactive mode."""
    app = ShellMind(console=console)
    
    console.clear()
    
    # Title section with improved ASCII art and gradient
    console.print()
    title_lines = [
        "  ███████╗██╗  ██╗███████╗██╗     ██╗     ███╗   ███╗██╗███╗   ██╗██████╗ ",
        "  ██╔════╝██║  ██║██╔════╝██║     ██║     ████╗ ████║██║████╗  ██║██╔══██╗",
        "  ███████╗███████║█████╗  ██║     ██║     ██╔████╔██║██║██╔██╗ ██║██║  ██║",
        "  ╚════██║██╔══██║██╔══╝  ██║     ██║     ██║╚██╔╝██║██║██║╚██╗██║██║  ██║",
        "  ███████║██║  ██║███████╗███████╗███████╗██║ ╚═╝ ██║██║██║ ╚████║██████╔╝",
        "  ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝ "
    ]
    
    gradient_colors = [
        "bright_magenta", "magenta", "medium_purple", "medium_purple1", "deep_sky_blue2", "bright_cyan"
    ]
    
    for line, color in zip(title_lines, gradient_colors):
        console.print(Align.center(Text(line, style=f"bold {color}")))
    console.print()

    # Tagline with better styling
    console.print(Align.center(Text("Your intelligent shell assistant", style="bold white")))
    console.print(Align.center(Text("AI-driven command synthesis for a seamless terminal experience", style="italic " + THEME_SUBTLE)))
    console.print()
    console.print(Align.center(Rule(style=THEME_PRIMARY)))
    console.print()

    # Quick start guide with improved layout
    quick_start = Table.grid(padding=(0, 3))
    quick_start.add_column(style=f"bold {THEME_ACCENT}", width=12)
    quick_start.add_column(style="bold white", width=20)
    quick_start.add_column(style=THEME_SUBTLE)
    
    # 1. Generate Commands
    quick_start.add_row(
        "⚡ COMMANDS",
        "Generate Commands",
        "Describe your task in plain English"
    )
    quick_start.add_row(
        "", 
        "",
        Text("e.g., \"Find all large files in /var and sort them\"", style="dim italic")
    )
    quick_start.add_row("", "", "")  # Spacer

    # 2. Explain Commands
    quick_start.add_row(
        "◈ EXPLAIN",
        "Explain Commands",
        "Type /explain <command> to understand it"
    )
    quick_start.add_row(
        "",
        "", 
        Text("e.g., \"/explain tar -xzf archive.tar.gz\"", style="dim italic")
    )
    quick_start.add_row("", "", "")  # Spacer

    # 3. Agent Mode
    quick_start.add_row(
        "◆ AGENT",
        "Agent Mode", 
        "Enable tools with --agent (or toggle in config)"
    )
    quick_start.add_row("", "", "")  # Spacer

    # 4. Exit
    quick_start.add_row(
        "◇ EXIT",
        "Exit",
        "Type exit or quit"
    )

    banner_content = Group(
        Text("Quick Start Guide", style=f"bold {THEME_PRIMARY}", justify="center"),
        Text(""),
        Align.center(quick_start)
    )

    panel = Panel(
        banner_content,
        border_style=THEME_PRIMARY,
        box=box.HEAVY,
        padding=(2, 6),
        expand=False
    )
    
    console.print(Align.center(panel))
    console.print()

    while True:
        try:
            # Show mode status with better styling
            status_text = Text()
            status_text.append("  Agent Mode: ", style=THEME_SUBTLE)
            if use_tools:
                status_text.append("●", style=f"bold {THEME_SUCCESS}")
                status_text.append(" ON", style=f"bold {THEME_SUCCESS}")
            else:
                status_text.append("○", style=THEME_SUBTLE)
                status_text.append(" OFF", style=THEME_SUBTLE)
            console.print(status_text, justify="right")

            prompt_text = Text.assemble(
                ("  ▸ ", THEME_SECONDARY),
                ("You", f"bold {THEME_SECONDARY}"),
                (" › ", THEME_SUBTLE)
            )
            user_input = Prompt.ask(prompt_text)
            
            if user_input.lower().startswith('/explain'):
                response = app.explain(user_input)
                if response:
                    display_response(response)
                else:
                    console.print(Panel(
                        Text("Nothing to explain. Try '/explain <command>' or generate a command first.", 
                             style=THEME_WARNING),
                        title=Text("⚠️  Warning", style=f"bold {THEME_WARNING}"),
                        border_style=THEME_WARNING,
                        box=box.ROUNDED,
                        padding=(1, 2)
                    ))
                continue
            
            if user_input.lower() in ['exit', 'quit']:
                console.print()
                console.print(Align.center(Text("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", style=THEME_PRIMARY)))
                console.print(Align.center(Text("Thank you for using ShellMind!", style="bold " + THEME_PRIMARY)))
                console.print(Align.center(Text("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", style=THEME_PRIMARY)))
                console.print()
                break
            
            response = app.run(user_input, use_tools=use_tools)
            
            while True:
                display_response(response)
                
                # Step 1: Handle command execution if present
                if response.output.command:
                    # In Agent mode, we still allow execution of suggested commands
                    # but give a helpful tip that tools are the primary way.
                    if use_tools:
                        console.print(Panel(
                            Text("Agent suggested this command. You can execute it now or let the agent handle tasks.", 
                                 style="italic"),
                            border_style=THEME_SUBTLE,
                            box=box.ROUNDED,
                            padding=(0, 2)
                        ))
                    
                    confirm_text = Text("Execute this command?", style=f"bold {THEME_WARNING}")
                    if Confirm.ask(confirm_text):
                        console.print(Text(f"⚙️  Executing: {response.output.command}", style=f"italic {THEME_SUBTLE}"))
                        console.print()
                        try:
                            result = subprocess.run(response.output.command, shell=True, text=True, capture_output=True)
                            console.print()
                            if result.stdout:
                                # Apply syntax highlighting to output
                                highlighted_output = syntax_highlight_output(result.stdout.strip())
                                console.print(Panel(
                                    highlighted_output, 
                                    title=Text("✓ Execution Output", style=f"bold {THEME_SUCCESS}"), 
                                    border_style=THEME_SUCCESS,
                                    box=box.ROUNDED,
                                    padding=(1, 2),
                                    title_align="left"
                                ))
                            if result.stderr:
                                console.print(Panel(
                                    result.stderr.strip(), 
                                    title=Text("✖ Error Output", style=f"bold {THEME_ERROR}"), 
                                    border_style=THEME_ERROR,
                                    box=box.ROUNDED,
                                    padding=(1, 2),
                                    title_align="left"
                                ))
                            console.print()
                        except Exception as exec_err:
                            console.print(Text(f"✖ Execution Failed: {exec_err}", style=f"bold {THEME_ERROR}"))

                # Step 2: Handle follow-ups if present
                if response.follow_ups:
                    answers = handle_follow_ups(app, response.follow_ups)
                    response = app.run(f"Answers to follow-up questions:\n{answers}", use_tools=use_tools)
                    continue

                # Turn is complete
                break
                
        except KeyboardInterrupt:
            console.print()
            console.print(Align.center(Text("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", style=THEME_PRIMARY)))
            console.print(Align.center(Text("Thank you for using ShellMind!", style="bold " + THEME_PRIMARY)))
            console.print(Align.center(Text("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", style=THEME_PRIMARY)))
            console.print()
            break
        except Exception as e:
            console.print(Panel(
                Text(str(e), style=f"bold {THEME_ERROR}"),
                title=Text("✖ Error", style=f"bold {THEME_ERROR}"),
                border_style=THEME_ERROR,
                box=box.ROUNDED,
                padding=(1, 2)
            ))

@click.command()
@click.argument('query', required=False)
@click.option('--explain', is_flag=True, help='Explain a command instead of generating one')
@click.option('--execute/--no-execute', default=None, help='Auto-execute commands without confirmation')
@click.option('--version', is_flag=True, help='Show version and exit')
@click.option('--agent', is_flag=True, help='Run in agent mode (with tools) for this session')
@click.option('--set-mode', type=click.Choice(['default', 'agent']), help='Set persistent mode preference')
def main(query, explain, execute, version, agent, set_mode):
    """ShellMind - Your intelligent shell assistant"""
    if version:
        click.echo("ShellMind v0.1.0")
        return
    
    if set_mode:
        agent_mode_val = (set_mode == 'agent')
        config_manager.agent_mode = agent_mode_val
        mode_str = "Agent Mode" if agent_mode_val else "Default Mode"
        click.echo(f"Configuration updated: Set to {mode_str}")
        return

    # Determine mode:
    # 1. CLI flag --agent overrides everything (forces True)
    # 2. Config file setting is used if --agent is not present
    use_tools = agent or config_manager.agent_mode

    try:


        if query:
            exit_code = run_query(query, explain_mode=explain, auto_execute=execute, use_tools=use_tools)
            sys.exit(exit_code)
        else:
            run_interactive(use_tools=use_tools)
    except KeyboardInterrupt:
        click.echo("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
