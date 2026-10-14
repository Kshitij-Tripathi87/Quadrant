import json
import uuid
import sqlite3
from typing import List, Dict, Any, Optional
from src.config import settings

class StorageRepository:
    """
    Data Access Object for SQLite persistence.
    """
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.SQLITE_DB_PATH

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_query(
        self,
        question: str,
        answer: str,
        session_id: Optional[str] = None,
        query_type: Optional[str] = None,
        retries: int = 0,
        sources: Optional[List[Dict[str, Any]]] = None,
        grounded: Optional[str] = None,
    ) -> str:
        """Stores a completed query execution and returns unique query_id."""
        query_id = str(uuid.uuid4())
        sources_json = json.dumps(sources or [])

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO queries (id, session_id, question, answer, query_type, retries, sources_json, grounded)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    query_id,
                    session_id or str(uuid.uuid4()),
                    question,
                    answer,
                    query_type,
                    retries,
                    sources_json,
                    grounded,
                ),
            )
            conn.commit()

        return query_id

    def save_feedback(
        self,
        query_id: str,
        rating: str,
        comment: Optional[str] = None,
    ) -> str:
        """Saves user feedback for a query."""
        feedback_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO feedback (id, query_id, rating, comment)
                VALUES (?, ?, ?, ?)
                """,
                (feedback_id, query_id, rating, comment),
            )
            conn.commit()

        return feedback_id

    def record_document(
        self,
        source: str,
        title: str,
        chunk_count: int,
        source_type: str = "file",
    ):
        """Records or updates an indexed document in the registry."""
        doc_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO documents (id, source, title, chunk_count, source_type)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(source) DO UPDATE SET
                    title=excluded.title,
                    chunk_count=excluded.chunk_count,
                    ingested_at=CURRENT_TIMESTAMP
                """,
                (doc_id, source, title, chunk_count, source_type),
            )
            conn.commit()

    def get_indexed_documents(self) -> List[Dict[str, Any]]:
        """Retrieves all indexed documents from the registry."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, source, title, chunk_count, source_type, ingested_at FROM documents ORDER BY ingested_at DESC"
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_recent_feedback(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent feedback items."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, query_id, rating, comment, created_at FROM feedback ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

# Singleton instance
storage_repo = StorageRepository()
