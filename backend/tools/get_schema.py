from typing import Any, Dict, Optional
from database import execute_query

def get_schema(db_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Introspects any SQLite database dynamically and returns the complete schema
    including tables, column names, data types, primary keys, and foreign keys.
    """
    schema = {}
    
    # Get all user tables
    tables = execute_query(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
        db_name=db_name
    )
    
    for table_row in tables:
        table_name = table_row['name']
        table_info = {'columns': [], 'foreign_keys': []}
        
        # Get columns with PRAGMA table_info
        columns = execute_query(f"PRAGMA table_info({table_name})", db_name=db_name)
        for col in columns:
            table_info['columns'].append({
                'name': col['name'],
                'type': col['type'],
                'notnull': bool(col['notnull']),
                'pk': bool(col['pk'])
            })
            
        # Get foreign keys with PRAGMA foreign_key_list
        fks = execute_query(f"PRAGMA foreign_key_list({table_name})", db_name=db_name)
        for fk in fks:
            table_info['foreign_keys'].append({
                'table': fk['table'],
                'from': fk['from'],
                'to': fk['to']
            })
            
        schema[table_name] = table_info
        
    return schema
