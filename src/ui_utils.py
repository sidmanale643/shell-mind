"""UI utilities for enhanced display formatting"""
import json
import re
from rich.syntax import Syntax
from rich.text import Text

# Enhanced color scheme
THEME_COMMAND = "dodger_blue2"
THEME_FLAG = "bright_yellow"
THEME_ARG = "white"
THEME_EXPLANATION = "grey70"

# Common shell command flags and their explanations
COMMON_FLAGS = {
    # ls flags
    '-l': 'long format with details',
    '-a': 'show hidden files (including . and ..)',
    '-h': 'human-readable sizes',
    '-t': 'sort by modification time',
    '-R': 'recursive listing',
    
    # docker flags
    '-d': 'detached mode (background)',
    '-it': 'interactive terminal',
    '-p': 'publish port mapping',
    '-v': 'mount volume',
    '--rm': 'remove container on exit',
    '-e': 'set environment variable',
    
    # kubectl flags
    '-o': 'output format',
    '--watch': 'watch for changes',
    '--all-namespaces': 'across all namespaces',
    '-f': 'file or force',
    
    # git flags
    '--oneline': 'condensed one-line format',
    '--graph': 'show branch graph',
    '--all': 'all branches',
    '--stat': 'show file statistics',
    '--pretty': 'pretty print format',
    
    # grep flags
    '-i': 'case insensitive',
    '-r': 'recursive search',
    '-n': 'show line numbers',
    '-E': 'extended regex',
    '-A': 'lines after match',
    '-B': 'lines before match',
    
    # Common across tools
    '--help': 'show help message',
    '--version': 'show version',
    '--verbose': 'verbose output',
    '-q': 'quiet mode',
}

def detect_content_type(content: str) -> str:
    """Detect the content type for syntax highlighting"""
    content = content.strip()
    
    # Check for JSON
    if content.startswith('{') or content.startswith('['):
        try:
            json.loads(content)
            return 'json'
        except (json.JSONDecodeError, ValueError):
            pass
    
    # Check for YAML (common in k8s configs)
    if re.search(r'^\s*[\w-]+:\s*[\w\s-]*$', content, re.MULTILINE):
        if 'apiVersion:' in content or 'kind:' in content:
            return 'yaml'
    
    # Check for common log patterns
    if re.search(r'\d{4}-\d{2}-\d{2}|\d{2}:\d{2}:\d{2}|ERROR|WARN|INFO|DEBUG', content):
        return 'log'
    
    # Check for shell scripts
    if content.startswith('#!') or re.search(r'\$\{|\$\(|export |function ', content):
        return 'bash'
    
    # Check for Python
    if re.search(r'^(def|class|import|from)\s+', content, re.MULTILINE):
        return 'python'
    
    # Check for Dockerfile
    if re.search(r'^(FROM|RUN|COPY|CMD|ENTRYPOINT)', content, re.MULTILINE):
        return 'dockerfile'
    
    return None

def syntax_highlight_output(content: str, detected_type: str = None) -> Syntax | str:
    """Apply syntax highlighting to output content"""
    if not content or len(content.strip()) == 0:
        return content
    
    # Auto-detect if not provided
    if not detected_type:
        detected_type = detect_content_type(content)
    
    # If we can't detect or it's too short, return as-is
    if not detected_type or len(content) < 20:
        return content
    
    try:
        # Special handling for logs - use dracula theme for better visibility
        if detected_type == 'log':
            return Syntax(content, "log", theme="dracula", line_numbers=False, word_wrap=True)
        
        # Use dracula theme for better aesthetics
        return Syntax(content, detected_type, theme="dracula", line_numbers=False, word_wrap=True)
    except Exception:
        # If highlighting fails, return original
        return content

def add_inline_explanations(command: str) -> Text:
    """Add inline flag explanations to a command with enhanced styling"""
    # Split command into parts
    parts = command.split()
    if not parts:
        return Text(command)
    
    cmd_name = parts[0]
    result = Text()
    result.append(parts[0], style="bold " + THEME_COMMAND)  # Command name
    
    i = 1
    while i < len(parts):
        part = parts[i]
        result.append(" ")
        
        # Check if it's a flag we recognize
        flag_explanation = None
        if part.startswith('-') and part in COMMON_FLAGS:
            flag_explanation = COMMON_FLAGS[part]
        elif part.startswith('--') and part in COMMON_FLAGS:
            flag_explanation = COMMON_FLAGS[part]
        
        # Add context-aware overrides for ambiguous flags
        if flag_explanation:
            # Context-specific overrides
            if part == '-a' and 'docker' in cmd_name:
                flag_explanation = 'all containers'
            elif part == '-f' and 'kubectl' in cmd_name:
                flag_explanation = 'file'
            elif part == '-f' and 'rm' in cmd_name:
                flag_explanation = 'force'
            elif part == '-r' and 'grep' in cmd_name:
                flag_explanation = 'recursive search'
            
            result.append(part, style=THEME_FLAG)
            result.append(" ", style="dim")
            result.append("({})".format(flag_explanation), style="dim italic " + THEME_EXPLANATION)
        else:
            # Regular argument - enhanced styling
            if part.startswith('-'):
                result.append(part, style=THEME_FLAG)
            else:
                result.append(part, style=THEME_ARG)
        
        i += 1
    
    return result

def should_add_explanations(command: str) -> bool:
    """Determine if a command is complex enough to warrant inline explanations"""
    if not command:
        return False
    
    # Count flags
    flag_count = len(re.findall(r'\s-+\w+', command))
    
    # Add explanations if there are 2+ flags or the command is long
    return flag_count >= 2 or len(command) > 40

def format_command_with_explanation(command: str) -> Text:
    """Format a command, optionally adding inline explanations for complex commands"""
    if should_add_explanations(command):
        return add_inline_explanations(command)
    else:
        # Simple highlighting without explanations - enhanced styling
        result = Text()
        parts = command.split()
        if parts:
            result.append(parts[0], style="bold " + THEME_COMMAND)
            if len(parts) > 1:
                # Apply smarter coloring to arguments
                for part in parts[1:]:
                    result.append(" ")
                    if part.startswith('-'):
                        result.append(part, style=THEME_FLAG)
                    else:
                        result.append(part, style=THEME_ARG)
        return result

