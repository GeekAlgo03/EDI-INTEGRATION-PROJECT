import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).with_name("runs.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        run_id TEXT PRIMARY KEY,
        created_at TEXT,
        partner TEXT,
        doc_type TEXT,
        status TEXT,
        po_number TEXT,
        raw_xml TEXT,
        canonical_json TEXT,
        netsuite_payload_json TEXT,
        error TEXT
    )
    """)
    conn.commit()
    conn.close()
import json
from uuid import uuid4

def insert_run(
    partner: str,
    doc_type: str,
    status: str,
    po_number: str | None,
    raw_xml: str,
    canonical: dict | None,
    netsuite_payload: dict | None,
    error: str | None
) -> str:
    """
    Inserts one run record and returns run_id.
    """
    run_id = str(uuid4())
    created_at = datetime.utcnow().isoformat()

    canonical_json = json.dumps(canonical, ensure_ascii=False) if canonical is not None else None
    netsuite_payload_json = json.dumps(netsuite_payload, ensure_ascii=False) if netsuite_payload is not None else None

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO runs (
            run_id, created_at, partner, doc_type, status,
            po_number, raw_xml, canonical_json, netsuite_payload_json, error
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id, created_at, partner, doc_type, status,
            po_number, raw_xml, canonical_json, netsuite_payload_json, error
        )
    )

    conn.commit()
    conn.close()
    return run_id

def get_run(run_id: str) -> dict | None:
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
    row = cur.fetchone()
    conn.close()

    return dict(row) if row else None


def list_runs(limit: int = 20) -> list[dict]:
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM runs ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    rows = cur.fetchall()
    conn.close()

    return [dict(r) for r in rows]
