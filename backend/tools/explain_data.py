from typing import Any, Dict, List

def explain_data(question: str, data: List[Dict[str, Any]], context: str = "") -> str:
    """
    Instructs the LLM to explain the data. This tool is a dummy wrapper.
    The agent should use the data and summarize it in its response.
    We just return a system instruction string.
    """
    return f"Data has been provided. Please provide a natural language explanation with key insights answering the question: '{question}'. Context: {context}"
