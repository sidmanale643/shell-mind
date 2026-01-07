import os
import json
import instructor
from groq import Groq
from pydantic import BaseModel, Field
from typing import Optional, Callable, Any, Union
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


class Question(BaseModel):
    question: str
    options: list[str]


class Output(BaseModel):
    content: Optional[str] = Field(default=None, description="Response content")
    command: Optional[str] = Field(default=None, description="Command to execute")
    warning: Optional[str] = Field(default=None, description="Warning")

  
class Response(BaseModel):
    thinking: Optional[str] = Field(default=None, description="Internal thought process")
    output: Output
    follow_ups: Optional[list[Question]] = Field(default=None, description="Follow-up questions")
    
    def __str__(self) -> str:
        """Return a clean string representation instead of JSON."""
        parts = []
        if self.thinking:
            parts.append(f"Thinking: {self.thinking}")
        if self.output.content:
            parts.append(self.output.content)
        if self.output.command:
            parts.append(f"Command: {self.output.command}")
        return "\n".join(parts) if parts else "Response(no content)"
    
    def __repr__(self) -> str:
        """Return the same clean representation for repr."""
        return self.__str__()


@dataclass
class ToolCall:
    """Represents a tool call request from the LLM."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass 
class ToolCallResult:
    """Result of executing a tool call."""
    tool_call_id: str
    name: str
    content: str


class LlmService:
    def __init__(self):
        self.provider = os.environ.get("LLM_PROVIDER", "groq").lower()
        
        # Default model for Groq if not specified
        default_model = "moonshotai/kimi-k2-instruct-0905"

        if self.provider == "openrouter":
            default_model = "minimax/minimax-m2.1"
            
        self.model_name = os.environ.get("LLM_MODEL", default_model)
        
        if self.provider == "openrouter":
            from openai import OpenAI
            api_key = os.environ.get("OPENROUTER_API_KEY")
            self.client = instructor.from_openai(
                OpenAI(
                    api_key=api_key,
                    base_url="https://openrouter.ai/api/v1",
                ),
                mode=instructor.Mode.JSON
            )
        else:
            from groq import Groq
            self.client = instructor.from_groq(
                Groq(api_key=os.environ.get("GROQ_API_KEY")),
                mode=instructor.Mode.JSON
            )
    
    def generate(self, messages, retry_count=0, max_retries=2) -> Response:
        try:
            # filters out tool calls from messages if any exist, as simple generate shouldn't see them usually 
            # or handle them if they are part of history
            
            return self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_model=Response,
                temperature=0.3
            )
        except Exception as e:
            # Fallback for severe failures
            return Response(
                thinking="Error occurred", 
                output=Output(content=f"Failed to generate message due to error: {str(e)}")
            )

    def get_raw_completion(self, messages: list[dict], tools: list[dict] = None) -> Any:
        """Get raw completion from LLM, potentially with tool calls."""
        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "response_model": None,
            "temperature": 0.3
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
            
        return self.client.chat.completions.create(**kwargs)

    def generate_with_tools(
        self, 
        messages: list[dict], 
        tools: list[dict],
        tool_executor: Callable[[str, dict], str],
        max_iterations: int = 30
    ) -> tuple[Response, list[dict]]:
        """
        Generate a response with tool calling support.
        This is now a wrapper around the iteration logic.
        """
        working_messages = list(messages)
        
        for iteration in range(max_iterations):
            try:
                chat_completion = self.get_raw_completion(working_messages, tools)
                response_message = chat_completion.choices[0].message
                tool_calls = getattr(response_message, 'tool_calls', None)
                
                # If no tool calls, generate the final structured response.
                if not tool_calls:
                    final_response = self.generate(working_messages)
                    
                    # Add to history
                    working_messages.append({
                         "role": "assistant",
                         "content": str(final_response)
                    })
                    
                    messages.clear()
                    messages.extend(working_messages)
                    return (final_response, messages)
                
                # Add assistant message with tool calls to history
                working_messages.append({
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
                
                # Execute tool calls
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        function_args = {}
                    
                    tool_result = tool_executor(function_name, function_args)
                    
                    working_messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(tool_result)
                    })
                    
            except Exception as e:
                messages.clear()
                messages.extend(working_messages)
                return (Response(
                    thinking="Error occurred during tool calling",
                    output=Output(content=f"Failed to process tool calls: {str(e)}")
                ), messages)
        
        messages.clear()
        messages.extend(working_messages)
        return (Response(
            thinking="Max tool iterations reached",
            output=Output(content="I encountered too many tool calls. Please try a simpler request.")
        ), messages)

