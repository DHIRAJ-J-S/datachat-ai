"""
LLM Client — Unified multi-provider client for OpenAI, Anthropic, and Groq.

Supports streaming tool/function calling across all three providers.
Auto-detects provider based on available API keys (priority: OpenAI → Anthropic → Groq).
"""
import os
import json
from typing import Any, AsyncGenerator, Dict, List, Optional
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic


class LLMClient:
    """Unified LLM client supporting OpenAI, Anthropic, and Groq with tool calling."""

    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        
        # Ignore placeholder keys from .env.example
        if self.openai_key and "your-openai-key-here" in self.openai_key:
            self.openai_key = None
        if self.anthropic_key and "your-anthropic-key-here" in self.anthropic_key:
            self.anthropic_key = None
            
        provider_override = os.getenv("LLM_PROVIDER")

        # Priority: Override → OpenAI → Anthropic → Groq
        if provider_override == "openai" and self.openai_key:
            self._setup_openai()
        elif provider_override == "anthropic" and self.anthropic_key:
            self._setup_anthropic()
        elif provider_override == "groq" and self.groq_key:
            self._setup_groq()
        elif self.openai_key:
            self._setup_openai()
        elif self.anthropic_key:
            self._setup_anthropic()
        elif self.groq_key:
            self._setup_groq()
        else:
            raise ValueError(
                "No valid API keys found. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GROQ_API_KEY in your .env file."
            )

    def _setup_openai(self):
        self.provider = "openai"
        self.client = AsyncOpenAI(api_key=self.openai_key)
        self.model = "gpt-4o-mini"
        
    def _setup_anthropic(self):
        self.provider = "anthropic"
        self.client = AsyncAnthropic(api_key=self.anthropic_key)
        self.model = "claude-3-5-sonnet-20241022"
        
    def _setup_groq(self):
        self.provider = "groq"
        self.client = AsyncOpenAI(
            api_key=self.groq_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = "llama-3.3-70b-versatile"

    def format_tools_for_provider(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert tool definitions to provider-specific format."""
        if self.provider in ["openai", "groq"]:
            return [{"type": "function", "function": tool} for tool in tools]
        elif self.provider == "anthropic":
            return [
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["parameters"]
                }
                for tool in tools
            ]
        return []

    def _convert_messages_for_anthropic(self, messages: List[Dict[str, Any]]) -> tuple:
        """
        Convert OpenAI-format messages to Anthropic format.
        
        Anthropic differences:
        - System message is a separate parameter, not in messages list
        - Tool calls are content blocks of type 'tool_use' inside assistant messages
        - Tool results are content blocks of type 'tool_result' inside user messages
        """
        system_msg = ""
        anthropic_messages = []

        for m in messages:
            role = m.get("role", "")

            if role == "system":
                system_msg += m.get("content", "") + "\n"

            elif role == "assistant":
                # Check if this is a tool-calling assistant message
                if m.get("tool_calls"):
                    content_blocks = []
                    # Add any text content first
                    if m.get("content"):
                        content_blocks.append({
                            "type": "text",
                            "text": m["content"]
                        })
                    # Convert tool_calls to tool_use blocks
                    for tc in m["tool_calls"]:
                        func = tc.get("function", tc)
                        content_blocks.append({
                            "type": "tool_use",
                            "id": tc.get("id", ""),
                            "name": func.get("name", ""),
                            "input": json.loads(func.get("arguments", "{}"))
                        })
                    anthropic_messages.append({
                        "role": "assistant",
                        "content": content_blocks
                    })
                else:
                    anthropic_messages.append({
                        "role": "assistant",
                        "content": m.get("content", "") or ""
                    })

            elif role == "tool":
                # Convert tool result to Anthropic's user message with tool_result block
                tool_result_block = {
                    "type": "tool_result",
                    "tool_use_id": m.get("tool_call_id", ""),
                    "content": m.get("content", "")
                }
                # Anthropic expects tool_result blocks inside a user message
                # If the last message is already a user message with tool_result blocks, merge
                if (anthropic_messages and
                    anthropic_messages[-1]["role"] == "user" and
                    isinstance(anthropic_messages[-1]["content"], list)):
                    anthropic_messages[-1]["content"].append(tool_result_block)
                else:
                    anthropic_messages.append({
                        "role": "user",
                        "content": [tool_result_block]
                    })

            elif role == "user":
                anthropic_messages.append({
                    "role": "user",
                    "content": m.get("content", "")
                })

        return system_msg.strip(), anthropic_messages

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a chat completion with tool calling support.
        
        Yields events:
        - {"type": "text", "content": "..."} for text tokens
        - {"type": "tool_calls", "tool_calls": [...]} when tools are called
        """
        formatted_tools = self.format_tools_for_provider(tools)

        if self.provider in ["openai", "groq"]:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=formatted_tools if formatted_tools else None,
                stream=True
            )

            tool_calls_buffer: Dict[int, Dict] = {}
            async for chunk in stream:
                delta = chunk.choices[0].delta

                # Stream text content
                if delta.content:
                    yield {"type": "text", "content": delta.content}

                # Accumulate tool call arguments (they arrive in fragments)
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_buffer:
                            tool_calls_buffer[idx] = {
                                "id": tc.id or "",
                                "name": tc.function.name or "",
                                "arguments": ""
                            }
                        if tc.id:
                            tool_calls_buffer[idx]["id"] = tc.id
                        if tc.function.name:
                            tool_calls_buffer[idx]["name"] = tc.function.name
                        if tc.function.arguments:
                            tool_calls_buffer[idx]["arguments"] += tc.function.arguments

                # When the model finishes with tool_calls, emit them
                if chunk.choices[0].finish_reason == "tool_calls":
                    yield {
                        "type": "tool_calls",
                        "tool_calls": list(tool_calls_buffer.values())
                    }

        elif self.provider == "anthropic":
            system_msg, anthropic_messages = self._convert_messages_for_anthropic(messages)

            async with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=system_msg,
                messages=anthropic_messages,
                tools=formatted_tools if formatted_tools else None
            ) as stream:
                async for event in stream:
                    if event.type == "text":
                        yield {"type": "text", "content": event.text}

                # After streaming, check for tool calls in the final message
                final_msg = await stream.get_final_message()
                tool_calls = []
                for block in final_msg.content:
                    if block.type == "tool_use":
                        tool_calls.append({
                            "id": block.id,
                            "name": block.name,
                            "arguments": json.dumps(block.input)
                        })

                if tool_calls:
                    yield {"type": "tool_calls", "tool_calls": tool_calls}
