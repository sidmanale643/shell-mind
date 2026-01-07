from textwrap import dedent

class TodoManager():
    def __init__(self):
        self.name = "todo_manager"
        self.todo_list = []
    
    def json_schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "todo_list": {
                            "type": "array",
                            "description": "A list of dictionaries with 'task' and 'status' keys",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "task": {"type": "string"},
                                    "status": {"type": "string"}
                                }
                            }
                        }
                    },
                    "required": ["todo_list"]
                }
            }
        }
    
    def description(self):
        return dedent("""
        Use this tool to create and manage a structured task list for your current coding session. 
        This helps you track progress, organize complex tasks, and demonstrate thoroughness to the user. 
        It also helps the user understand the progress of the task and overall progress of their requests.
        
        IMPORTANT: There is only ONE TODO list per session. Each time you call this tool, you are 
        UPDATING the existing list. Always include ALL tasks (both old and new) when calling this tool,
        updating the status of tasks as they progress (pending -> in_progress -> completed).

        ### When to Use This Tool

        Use this tool proactively in these scenarios:

        Complex multi-step tasks - When a task requires 3 or more distinct steps or actions
        Non-trivial and complex tasks - Tasks that require careful planning or multiple operations
        User explicitly requests todo list - When the user directly asks you to use the todo list
        User provides multiple tasks - When users provide a list of things to be done (numbered or comma-separated)
        After receiving new instructions - Immediately capture user requirements as todos
        When you start working on a task - Mark it as in_progress BEFORE beginning work. Ideally you should only have one todo as in_progress at a time
        After completing a task - Mark it as completed and add any new follow-up tasks discovered during implementation

        ### When NOT to Use This Tool

        Skip using this tool when:

        There is only a single, straightforward task
        The task is trivial and tracking it provides no organizational benefit
        The task can be completed in less than 3 trivial steps
        The task is purely conversational or informational
        NOTE that you should not use this tool if there is only one trivial task to do. In this case you are better off just doing the task directly.
        """)
    
    def run(self, todo_list):
  
        self.todo_list = todo_list
        return self.todo_list