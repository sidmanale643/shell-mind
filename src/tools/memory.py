from typing import Literal
from textwrap import dedent

class MemoryTool():
    def __init__(self):
        self.name = "memory_tool"
        self.location = "src/memory/mem.md"
    
    def json_schema(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["read", "write"],
                            "description": "The operation to perform. 'read' retrieves all stored knowledge; 'write' saves new information."
                        },
                        "memory": {
                            "type": "string",
                            "description": "The information to store. **MANDATORY** if operation is 'write'. Use a concise, factual statement (e.g., 'User is a DevOps Engineer')."
                        }
                    },
                    "required": ["operation"]
                }
            }
        }
    
    def description(self):
        return dedent("""
        Access and manage a persistent knowledge base (Core Memory) to store critical user information across sessions.

        ### Guidelines for Use:
        - **Read at start**: Always perform a 'read' operation at the beginning of a conversation to understand the user's context, preferences, and background.
        - **Write immediately**: When the user shares new personal details, technical preferences, or project context, use 'write' to store it instantly.
        - **Be factual**: Store information as clear, third-person facts (e.g., "User prefers Python for scripting").
        - **Focus on longevity**: Only store information that remains relevant across different conversations. Avoid temporary or conversational filler.

        ### When to Store:
        - Personal details: Name, location, profession, interests.
        - Technical preferences: Tools (e.g., "User prefers Podman over Docker"), languages, coding styles.
        - Project context: Repositories they work on, current tech stack, recurring issues.
        - Explicit requests: "Remember that I always use the production namespace for these commands."
        """)
    
    def run(self, memory: str = "", operation: Literal["read", "write"] = "read"):
        import os
        os.makedirs(os.path.dirname(self.location), exist_ok=True)
        
        if operation == "read":
            try:
                with open(self.location, "r") as f:
                    memory_content = f.read()
                return memory_content if memory_content else "No memories stored yet."
            except FileNotFoundError:
                return "No memories stored yet."
        
        elif operation == "write":
            if not memory:
                return "Error: Memory content cannot be empty for write operation"
            
            with open(self.location, "a") as f:  # Changed to "a" (append mode)
                f.write(f"{memory}\n")
            return "Memory updated successfully"