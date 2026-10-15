import sqlite3
from pathlib import Path
from src.config import settings

def init_db():
    """Initializes the SQLite database tables if they do not exist."""
    db_path = Path(settings.SQLITE_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(db_path), timeout=30.0) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=30000;")
        cursor = conn.cursor()
        
        # Queries audit table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                query_type TEXT,
                retries INTEGER DEFAULT 0,
                sources_json TEXT,
                grounded TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Feedback table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                query_id TEXT,
                rating TEXT NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Documents registry table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                source TEXT UNIQUE NOT NULL,
                title TEXT,
                chunk_count INTEGER DEFAULT 0,
                source_type TEXT,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()

init_db()
