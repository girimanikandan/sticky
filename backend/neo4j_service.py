import os
from neo4j import GraphDatabase
from typing import List, Dict, Any
from datetime import datetime
import uuid

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

class Neo4jService:
    def __init__(self, uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD):
        if not uri or not user or not password:
            raise ValueError("NEO4J_URI, NEO4J_USER and NEO4J_PASSWORD must be set in environment.")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_note(self, note: Dict[str, Any]) -> Dict[str, Any]:
        """
        note: dict with id,title,content,color,x,y,timestamp (timestamp optional)
        """
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
        with self.driver.session() as session:
            rec = session.run(query, {
                "id": note_id,
                "title": note.get("title"),
                "content": note.get("content"),
                "color": note.get("color", "#ffeb3b"),
                "x": note.get("x", 100),
                "y": note.get("y", 100),
                "timestamp": timestamp
            }).single()
            node = rec["n"]
            return dict(node)

    def create_relationship(self, rel: Dict[str, Any]) -> Dict[str, Any]:
        """
        rel: dict with fromId, toId, type, label
        """
        rel_type = rel.get("type") or "RELATES"
        # Sanitize rel_type to be a valid relationship name (uppercase, alnum)
        rel_type_clean = "".join([c for c in rel_type.upper() if c.isalnum()]) or "RELATES"
        query = f"""
        MATCH (a:Note {{id: $fromId}}), (b:Note {{id: $toId}})
        MERGE (a)-[r:{rel_type_clean}]->(b)
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
            # Neo4j relationship doesn't map to dict directly; build minimal dict
            return {"type": type(r).__name__, "properties": dict(r)}

    def get_all_notes_and_relationships(self) -> Dict[str, Any]:
        query_notes = "MATCH (n:Note) RETURN n"
        query_rels = "MATCH (a:Note)-[r]->(b:Note) RETURN a.id AS fromId, b.id AS toId, type(r) AS type, r.label AS label"
        notes = []
        rels = []
        with self.driver.session() as session:
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
            for rec in session.run(query_rels):
                rels.append({
                    "fromId": rec["fromId"],
                    "toId": rec["toId"],
                    "type": rec["type"],
                    "label": rec["label"] or ""
                })
        return {"notes": notes, "relationships": rels}

    def update_note_position(self, note_id: str, x: float, y: float) -> None:
        query = "MATCH (n:Note {id: $id}) SET n.x = $x, n.y = $y RETURN n"
        with self.driver.session() as session:
            session.run(query, {"id": note_id, "x": x, "y": y})

    def clear_database(self) -> None:
        query = "MATCH (n) DETACH DELETE n"
        with self.driver.session() as session:
            session.run(query)
