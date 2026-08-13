"""
DataChat AI Backend — FastAPI Server

Provides SSE-streaming endpoints for the LLM-powered database agent,
schema introspection, and health checks.
"""
import os
import sqlite3
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv, set_key
import uvicorn
from pydantic import BaseModel
from typing import List, Optional

from database import init_db
from agent import run_agent_loop
from tools.get_schema import get_schema
from llm_client import LLMClient

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database on startup."""
    init_db()
    logger.info("DataChat AI backend started successfully")
    yield


app = FastAPI(
    title="DataChat AI",
    description="Conversational AI for Natural Language Database Intelligence",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/Response Models ─────────────────────────────────────────

class HistoryMessage(BaseModel):
    role: str
    content: str


class SettingsData(BaseModel):
    provider: str
    api_key: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[HistoryMessage]] = []
    database: Optional[str] = None


# ── API Endpoints ───────────────────────────────────────────────────

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint — streams LLM agent responses via Server-Sent Events.

    The agent loop:
    1. Receives user message + conversation history
    2. Sends to LLM with tool definitions
    3. Executes tools as needed (schema, SQL, charts, diagrams)
    4. Streams text responses and tool results back
    """
    try:
        llm = LLMClient()
    except ValueError as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

    history = [{"role": m.role, "content": m.content} for m in (request.history or [])]

    return StreamingResponse(
        run_agent_loop(request.message, history, llm, db_name=request.database),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/api/schema")
async def get_schema_endpoint(db: Optional[str] = None):
    """Returns the database schema as JSON."""
    try:
        # Pass the database parameter if get_schema supports it, else use it implicitly if it uses a global or default
        schema = get_schema(db) if db else get_schema()
        return JSONResponse(content=schema)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/databases")
async def get_databases_endpoint():
    """Lists available databases."""
    databases = ["ecommerce.db"] if os.path.exists("ecommerce.db") else []
    # Check for additional .db files in the current directory
    for f in os.listdir("."):
        if f.endswith((".db", ".sqlite", ".sqlite3")) and f not in databases:
            databases.append(f)
    return JSONResponse(content={"databases": databases})

@app.post("/api/upload-database")
async def upload_database(file: UploadFile = File(...)):
    """Uploads a SQLite database file."""
    if not file.filename.endswith((".db", ".sqlite", ".sqlite3")):
        raise HTTPException(status_code=400, detail="Invalid file extension. Only .db, .sqlite, and .sqlite3 are allowed.")
    
    file_path = os.path.join(".", file.filename)
    
    # Read file and check size limit (50MB)
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 50MB.")
        
    with open(file_path, "wb") as f:
        f.write(content)
        
    # Verify it's a valid SQLite database
    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        # If it fails to open, remove the uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Invalid SQLite database: {str(e)}")
        
    return JSONResponse(content={
        "filename": file.filename,
        "tables": tables,
        "message": "Database uploaded successfully"
    })


class ExportRequest(BaseModel):
    query: str
    database: Optional[str] = None


@app.post("/api/export-csv")
async def export_csv(request: ExportRequest):
    """Export query results as a downloadable CSV file."""
    import csv
    import io
    from tools.execute_query import execute_safe_query

    result = execute_safe_query(request.query, db_name=request.database)
    if "error" in result:
        return JSONResponse(status_code=400, content=result)

    if not result.get("rows"):
        return JSONResponse(status_code=400, content={"error": "No data to export"})

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=result["columns"])
    writer.writeheader()
    writer.writerows(result["rows"])

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=datachat_export.csv"}
    )


@app.get("/api/settings")
async def get_settings():
    provider = os.getenv("LLM_PROVIDER", "openai")
    has_key = False
    
    if provider == "openai" and os.getenv("OPENAI_API_KEY") and "your-" not in os.getenv("OPENAI_API_KEY"):
        has_key = True
    elif provider == "anthropic" and os.getenv("ANTHROPIC_API_KEY") and "your-" not in os.getenv("ANTHROPIC_API_KEY"):
        has_key = True
    elif provider == "groq" and os.getenv("GROQ_API_KEY") and "your-" not in os.getenv("GROQ_API_KEY"):
        has_key = True

    return {"provider": provider, "has_key": has_key}

@app.post("/api/settings")
async def update_settings(data: SettingsData):
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write("")
            
    set_key(env_path, "LLM_PROVIDER", data.provider)
    os.environ["LLM_PROVIDER"] = data.provider
    
    if data.api_key:
        if data.provider == "openai":
            set_key(env_path, "OPENAI_API_KEY", data.api_key)
            os.environ["OPENAI_API_KEY"] = data.api_key
        elif data.provider == "anthropic":
            set_key(env_path, "ANTHROPIC_API_KEY", data.api_key)
            os.environ["ANTHROPIC_API_KEY"] = data.api_key
        elif data.provider == "groq":
            set_key(env_path, "GROQ_API_KEY", data.api_key)
            os.environ["GROQ_API_KEY"] = data.api_key
            
    return {"status": "success"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(content={
        "status": "ok",
        "version": "1.0.0",
        "name": "DataChat AI"
    })


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
