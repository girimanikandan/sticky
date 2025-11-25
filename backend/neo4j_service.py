import os
from neo4j import GraphDatabase
from typing import Dict, Any
from datetime import datetime
import uuid
from dotenv import load_dotenv

# -------------------------------------------------------
# 🔥 Force load .env from backend folder
# -------------------------------------------------------
ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(ENV_PATH)

class Neo4jService:
    def __init__(self):
        # -------------------------------------------------------
        # 🔥 Read environment variables
        # -------------------------------------------------------
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")

        print("Neo4j connecting with:")
        print("URI:", uri)
        print("USER:", user)
        print("PASSWORD:", "******")

        if not uri or not user or not password:
            raise ValueError("NEO4J_URI, NEO4J_USER and NEO4J_PASSWORD must be set in environment.")

        # -------------------------------------------------------
        # 🔵 Connect Neo4j Driver
        # -------------------------------------------------------
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # -------------------------------------------------------
    # 🟡 Create Note
    # -------------------------------------------------------
    def create_note(self, note: Dict[str, Any]) -> Dict[str, Any]:
        note_id = note.get("id") or str(uuid.uuid4())
        timestamp = note.get("timestamp") or datetime.utcnow().isoformat()

        query = """
        MERGE (n:Note {id: $id})
        SET n.title = $title,
            n.content = $content,
            n.color = $color,
            n.x = $x,
            n.y = $y,
            n.timestamp = $timestamp
        RETURN n
        """

        params = {
            "id": note_id,
            "title": note.get("title"),
            "content": note.get("content"),
            "color": note.get("color", "#ffeb3b"),
            "x": note.get("x", 100),
            "y": note.get("y", 100),
            "timestamp": timestamp
        }

        with self.driver.session() as session:
            rec = session.run(query, params).single()
            return dict(rec["n"])

    # -------------------------------------------------------
    # 🟡 Create Relationship
    # -------------------------------------------------------
    def create_relationship(self, rel: Dict[str, Any]) -> Dict[str, Any]:
        rel_type = rel.get("type", "RELATES").upper()
        rel_type = "".join([c for c in rel_type if c.isalnum()])  # sanitize

        query = f"""
        MATCH (a:Note {{id: $fromId}}), (b:Note {{id: $toId}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r.label = $label
        RETURN r
        """

        with self.driver.session() as session:
            rec = session.run(query, {
                "fromId": rel["fromId"],
                "toId": rel["toId"],
                "label": rel.get("label", "")
            }).single()

            r = rec["r"]
            return {"type": rel_type, "properties": dict(r)}

    # -------------------------------------------------------
    # 🟢 Get All Notes + Relationships
    # -------------------------------------------------------
    def get_all_notes_and_relationships(self) -> Dict[str, Any]:
        query_notes = "MATCH (n:Note) RETURN n"
        query_rels = """
        MATCH (a:Note)-[r]->(b:Note)
        RETURN a.id AS fromId, b.id AS toId, type(r) AS type, r.label AS label
        """

        notes = []
        rels = []

        with self.driver.session() as session:
            # Notes
            for rec in session.run(query_notes):
                n = rec["n"]
                notes.append({
                    "id": n.get("id"),
                    "title": n.get("title"),
                    "content": n.get("content"),
                    "color": n.get("color"),
                    "x": n.get("x"),
                    "y": n.get("y"),
                    "timestamp": n.get("timestamp"),
                })

            # Relationships
            for rec in session.run(query_rels):
                rels.append({
                    "fromId": rec["fromId"],
                    "toId": rec["toId"],
                    "type": rec["type"],
                    "label": rec["label"] or ""
                })

        return {"notes": notes, "relationships": rels}

    # -------------------------------------------------------
    # 🟡 Update Note Position
    # -------------------------------------------------------
    def update_note_position(self, note_id: str, x: float, y: float) -> None:
        query = """
        MATCH (n:Note {id: $id})
        SET n.x = $x, n.y = $y
        RETURN n
        """
        with self.driver.session() as session:
            session.run(query, {"id": note_id, "x": x, "y": y})

    # -------------------------------------------------------
    # 🔴 Clear All Data (DEV ONLY)
    # -------------------------------------------------------
    def clear_database(self) -> None:
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
