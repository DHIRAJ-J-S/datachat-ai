import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
from llm_client import LLMClient
from tools.get_schema import get_schema
from tools.execute_query import execute_safe_query
from tools.generate_chart import generate_chart
from tools.generate_flowchart import generate_flowchart
from tools.explain_data import explain_data

logger = logging.getLogger(__name__)

# System prompt that makes the agent behave intelligently
SYSTEM_PROMPT = """You are DataChat AI, an expert data analysis assistant that helps users explore and understand databases through natural language.

## Your Capabilities
You have access to an e-commerce SQLite database with tables for categories, suppliers, products, inventory, customers, orders, and order_items.

## Your Tools
1. **get_schema** - Use this FIRST when you need to understand the database structure, table relationships, or column names. Always call this before writing complex queries.
2. **execute_query** - Run SELECT SQL queries against the database. Only SELECT is allowed. Always write clean, efficient SQL.
3. **generate_chart** - Create visualizations from data. Choose the right chart type:
   - **bar**: For comparing categories (e.g., top products, revenue by category)
   - **line**: For trends over time (e.g., monthly sales, growth)
   - **pie**: For proportional distributions (e.g., market share, category split)
   - **scatter**: For correlations between two variables
4. **generate_flowchart** - Create Mermaid diagrams:
   - **er**: Entity-relationship diagrams showing table relationships
   - **flowchart**: Process flow diagrams (e.g., order processing pipeline)
   - **decision_tree**: Decision trees for conditional logic
5. **explain_data** - Generate insights and explanations from query results

## Workflow
When a user asks a data question:
1. If needed, call get_schema to understand the database
2. Write and execute the appropriate SQL query
3. If the user wants a visualization, call generate_chart with the query results
4. For diagrams, call generate_flowchart with proper Mermaid syntax
5. Always explain your findings clearly

## Important Rules
- Always show the SQL you're executing for transparency
- When generating charts, pass ACTUAL data from query results, not placeholder data
- For Mermaid ER diagrams, use the erDiagram syntax with proper relationships
- For flowcharts, use `flowchart TD` or `flowchart LR` syntax
- Keep explanations concise but insightful — highlight key trends, outliers, and actionable insights
- If a query fails, explain the error and suggest corrections
- Use proper formatting: bold for emphasis, bullet points for lists
- **CRITICAL**: When calling a tool, use ONLY the exact tool name (e.g. `execute_query`). NEVER append JSON or arguments to the tool name string itself.
- **CRITICAL**: If you execute a query and do NOT generate a chart or diagram, you MUST present the data to the user as a Markdown table. Do not just summarize without showing the raw data in a table.

## Chart Data Format
When calling generate_chart, structure data as arrays of objects:
- Bar/Line/Scatter: [{name: "Category A", value: 100}, ...]  with x_axis_key and y_axis_key or series
- Pie: [{name: "Slice A", value: 400}, ...] with data_key="value" and name_key="name"

## Mermaid Syntax
For ER diagrams:
```
erDiagram
    CUSTOMERS ||--o{ ORDERS : places
    ORDERS ||--|{ ORDER_ITEMS : contains
    PRODUCTS ||--o{ ORDER_ITEMS : "ordered in"
```

For flowcharts:
```
flowchart TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
```
"""

# Tool definitions for the LLM
TOOLS_DEFS = [
    {
        "name": "get_schema",
        "description": "Retrieve the database schema including all tables, their columns (with data types), primary keys, and foreign key relationships. Use this to understand the database structure before writing queries.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "execute_query",
        "description": "Execute a SELECT SQL query against the SQLite database. Only SELECT statements are allowed. Returns columns, rows, and row count. Use this to fetch data for analysis, charts, or explanations.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A valid SQLite SELECT query. Examples: 'SELECT name, SUM(quantity * unit_price) as revenue FROM order_items JOIN products ON ...' . Only SELECT is allowed."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "generate_chart",
        "description": "Generate a chart visualization from data. Returns a renderable chart specification. Use this after execute_query to visualize results. Choose chart_type based on the data: 'bar' for comparisons, 'line' for trends over time, 'pie' for distributions, 'scatter' for correlations.",
        "parameters": {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "line", "pie", "scatter"],
                    "description": "Type of chart: 'bar' for categorical comparisons, 'line' for time trends, 'pie' for proportions, 'scatter' for correlations"
                },
                "title": {
                    "type": "string",
                    "description": "Descriptive title for the chart"
                },
                "data": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Array of data objects. Each object should have keys matching xAxisKey and series dataKeys. Example: [{\"month\": \"Jan\", \"revenue\": 5000}]"
                },
                "x_axis_key": {
                    "type": "string",
                    "description": "Key in data objects for X-axis values (required for bar/line/scatter)"
                },
                "y_axis_key": {
                    "type": "string",
                    "description": "Key in data objects for Y-axis values (use when there's only one series)"
                },
                "series": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "dataKey": {"type": "string"},
                            "name": {"type": "string"},
                            "color": {"type": "string"}
                        }
                    },
                    "description": "Array of series configs for multi-series charts. Each has dataKey, name, and color."
                },
                "name_key": {
                    "type": "string",
                    "description": "Key for slice names (required for pie charts)"
                },
                "data_key": {
                    "type": "string",
                    "description": "Key for slice values (required for pie charts)"
                }
            },
            "required": ["chart_type", "title", "data"]
        }
    },
    {
        "name": "generate_flowchart",
        "description": "Generate a Mermaid diagram. Supports ER diagrams (entity-relationship), flowcharts (process flows), and decision trees. Returns rendered Mermaid code.",
        "parameters": {
            "type": "object",
            "properties": {
                "diagram_type": {
                    "type": "string",
                    "enum": ["er", "flowchart", "decision_tree"],
                    "description": "Type of diagram: 'er' for entity-relationship, 'flowchart' for process flows, 'decision_tree' for conditional logic"
                },
                "description": {
                    "type": "string",
                    "description": "Human-readable description of what the diagram shows"
                },
                "mermaid_code": {
                    "type": "string",
                    "description": "Valid Mermaid syntax code for the diagram. Use 'erDiagram' for ER, 'flowchart TD' for flowcharts, 'graph TD' for decision trees."
                }
            },
            "required": ["diagram_type", "description", "mermaid_code"]
        }
    },
    {
        "name": "explain_data",
        "description": "Generate a natural language explanation of data results. Use this to provide insights, identify trends, and highlight key findings from query results.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The original user question being answered"
                },
                "data": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "The query result data to analyze and explain"
                },
                "context": {
                    "type": "string",
                    "description": "Additional context about the data or analysis"
                }
            },
            "required": ["question", "data"]
        }
    }
]


def execute_tool(name: str, arguments: str, db_name: Optional[str] = None) -> Any:
    """Execute a tool by name with JSON-encoded arguments."""
    try:
        args = json.loads(arguments) if arguments else {}
    except json.JSONDecodeError:
        return {"error": f"Invalid JSON arguments for tool '{name}'"}

    if name == "get_schema":
        return get_schema(db_name=db_name)
    elif name == "execute_query":
        return execute_safe_query(args.get("query", ""), db_name=db_name)
    elif name == "generate_chart":
        return generate_chart(**args)
    elif name == "generate_flowchart":
        return generate_flowchart(**args)
    elif name == "explain_data":
        return explain_data(**args)
    else:
        return {"error": f"Unknown tool: {name}"}


async def run_agent_loop(
    message: str,
    history: List[Dict[str, str]],
    llm_client: LLMClient,
    db_name: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Main agent loop that:
    1. Sends user message to LLM with tool definitions
    2. If LLM calls tools, executes them and feeds results back
    3. Streams text responses via SSE events
    4. Loops until LLM produces final text (no more tool calls)
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add conversation history
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current user message
    messages.append({"role": "user", "content": message})

    max_loops = 8  # Safety limit to prevent infinite tool-calling loops
    loop_count = 0

    while loop_count < max_loops:
        loop_count += 1
        tool_calls = []

        try:
            async for chunk in llm_client.stream_chat(messages, TOOLS_DEFS):
                if chunk["type"] == "text":
                    yield f"data: {json.dumps({'type': 'text_delta', 'content': chunk['content']})}\n\n"
                elif chunk["type"] == "tool_calls":
                    tool_calls = chunk["tool_calls"]
        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            break

        # If no tool calls, the agent is done
        if not tool_calls:
            break

        # Build the assistant message with tool calls for conversation history
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": tc["arguments"]
                    }
                }
                for tc in tool_calls
            ]
        })

        # Execute each tool call
        for tc in tool_calls:
            tool_name = tc["name"]
            tool_args = tc["arguments"]

            # Send SQL preview event before execution (for SQL transparency)
            if tool_name == "execute_query":
                try:
                    args_parsed = json.loads(tool_args)
                    sql = args_parsed.get("query", "")
                    yield f"data: {json.dumps({'type': 'sql_preview', 'sql': sql})}\n\n"
                except json.JSONDecodeError:
                    pass

            # Notify frontend that tool execution is starting
            try:
                args_display = json.loads(tool_args) if tool_args else {}
            except json.JSONDecodeError:
                args_display = {"raw": tool_args}

            yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_name, 'args': args_display})}\n\n"

            # Execute the tool
            try:
                result = execute_tool(tool_name, tool_args, db_name=db_name)
                yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name, 'result': result})}\n\n"

                # Add tool result to conversation history
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result) if isinstance(result, (dict, list)) else str(result)
                })
            except Exception as e:
                error_msg = {"error": str(e)}
                yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name, 'result': error_msg})}\n\n"
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(error_msg)
                })

    # Signal completion
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
