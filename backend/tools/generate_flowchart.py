def generate_flowchart(diagram_type: str, description: str, mermaid_code: str) -> str:
    """
    Returns a markdown code block with Mermaid code.
    """
    if diagram_type not in ["er", "flowchart", "decision_tree"]:
        return "Error: Unsupported diagram type."
        
    return f"```mermaid\n{mermaid_code}\n```"
