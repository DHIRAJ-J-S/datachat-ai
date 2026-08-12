from typing import Any, Dict, Optional
from database import get_db_connection
import sqlparse

def is_safe_query(query: str) -> bool:
    """Checks if a query is a safe SELECT statement."""
    parsed = sqlparse.parse(query)
    if not parsed:
        return False
    
    stmt = parsed[0]
    if stmt.get_type() != 'SELECT':
        return False
    
    # Check for forbidden keywords that mutate state
    forbidden = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'REPLACE', 'TRUNCATE']
    tokens = [t.value.upper() for t in stmt.flatten() if t.ttype not in (sqlparse.tokens.Whitespace, sqlparse.tokens.Newline)]
    
    for token in tokens:
        if token in forbidden:
            return False
            
    return True

def execute_safe_query(query: str, db_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes a SELECT-only SQL query safely against the specified database.
    Limits to 500 rows.
    """
    if not is_safe_query(query):
        return {"error": "Security Error: Only SELECT queries are allowed."}
        
    # Append LIMIT if not present to prevent massive memory usage
    if 'LIMIT' not in query.upper():
        query += " LIMIT 500"
        
    conn = get_db_connection(db_name)
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            return {"columns": [], "rows": [], "row_count": 0}
            
        columns = [description[0] for description in cursor.description]
        result_rows = [dict(row) for row in rows]
        
        return {
            "columns": columns,
            "rows": result_rows,
            "row_count": len(result_rows)
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()
