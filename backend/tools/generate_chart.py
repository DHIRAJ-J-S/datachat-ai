import json
from typing import Any, Dict, List, Optional

def generate_chart(
    chart_type: str, 
    title: str, 
    data: List[Dict[str, Any]], 
    x_axis_key: str = None, 
    y_axis_key: str = None,
    series: List[Dict[str, Any]] = None,
    name_key: str = None,
    data_key: str = None
) -> str:
    """
    Generates a markdown code block containing a JSON specification for a chart.
    """
    if chart_type not in ["bar", "line", "pie", "scatter"]:
        return "Error: Unsupported chart type."
        
    spec = {
        "type": chart_type,
        "title": title,
        "data": data
    }
    
    if chart_type == "pie":
        if not data_key or not name_key:
            return "Error: Pie charts require dataKey and nameKey."
        spec["dataKey"] = data_key
        spec["nameKey"] = name_key
    else:
        if not x_axis_key:
            return "Error: Bar/Line/Scatter charts require xAxisKey."
        spec["xAxisKey"] = x_axis_key
        
        if series:
            spec["series"] = series
        elif y_axis_key:
            spec["series"] = [{"dataKey": y_axis_key, "name": y_axis_key.capitalize(), "color": "#8884d8"}]
        else:
            return "Error: Provide either series or y_axis_key."
            
    json_str = json.dumps(spec, indent=2)
    return f"```chart\n{json_str}\n```"
