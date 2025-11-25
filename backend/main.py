import os
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# ------------------------------
# 🔥 FORCE LOAD backend/.env
# ------------------------------
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=ENV_PATH)

from .models import GenerateRequest, PositionUpdate
from .neo4j_service import Neo4jService
from .llm_service import generate_notes_and_relationships

app = FastAPI(title="AI Sticky Notes Backend")

# ------------------------------
# 🔵 Enable CORS (React → FastAPI)
# ------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------
# 🔵 Initialize Neo4j service
# ------------------------------
try:
    neo4j_service = Neo4jService()
except Exception as e:
    neo4j_service = None
    init_err = e
else:
    init_err = None


# ------------------------------
# 🔵 Endpoints
# ------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/generate")
async def generate(request: GenerateRequest):
    """Generate notes + relationships using LLM and store in Neo4j."""
    if init_err:
        raise HTTPException(status_code=500, detail=f"Neo4j init error: {init_err}")

    try:
        parsed = generate_notes_and_relationships(request.description)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    notes = parsed.get("notes", [])
    relationships = parsed.get("relationships", [])

    try:
        for note in notes:
            neo4j_service.create_note(note)
        for rel in relationships:
            neo4j_service.create_relationship(rel)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"DB write error: {str(e)}")

    return neo4j_service.get_all_notes_and_relationships()


@app.get("/notes")
async def get_notes():
    """Return all notes + relationships from Neo4j."""
    if init_err:
        raise HTTPException(status_code=500, detail=f"Neo4j init error: {init_err}")

    try:
        return neo4j_service.get_all_notes_and_relationships()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-position")
async def update_position(pos: PositionUpdate):
    """Update the x,y position of a note after drag."""
    if init_err:
        raise HTTPException(status_code=500, detail=f"Neo4j init error: {init_err}")

    try:
        neo4j_service.update_note_position(pos.id, pos.x, pos.y)
        return {"ok": True}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear")
async def clear():
    """Clear the entire Neo4j database (development only)."""
    if init_err:
        raise HTTPException(status_code=500, detail=f"Neo4j init error: {init_err}")

    try:
        neo4j_service.clear_database()
        return {"ok": True}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
