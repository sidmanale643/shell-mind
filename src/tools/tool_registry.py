from .read_file import FileReader 
from .list_file import Ls 
from .glob_tool import Glob 
from .grep_tool import Grep 
from .env_detector import EnvironmentDetector 
from .command_executor import CommandExecutor 
from .check_git import GitInfo 
from .check_process import CheckProcess

class ToolRegistry:
    def __init__(self):
        self.tool_box = {}
        self.register_all_tools()

    def register_tool(self, name, tool_obj):
        if name in self.tool_box:
            raise ValueError(f"Duplicate tool name detected: {name}")
        self.tool_box[name] = tool_obj

    def register_all_tools(self):
        tools = [
            FileReader(),
            Ls(),
            Glob(),
            Grep(),
            EnvironmentDetector(),
            CommandExecutor(),
            GitInfo(),
            CheckProcess(),
        ]

        for tool in tools:
            self.register_tool(tool.name, tool)

    @property
    def tool_schemas(self):
        return [tool.json_schema() for tool in self.tool_box.values()]

    def run_tool(self, tool_name: str, arguments: dict) -> str:
        if tool_name not in self.tool_box:
            return f"Error: Tool '{tool_name}' not found."

        try:
            return self.tool_box[tool_name].run(**arguments)
        except TypeError as e:
            return f"Invalid arguments for '{tool_name}': {e}"
        except Exception as e:
            return f"Error executing tool '{tool_name}': {e}"
