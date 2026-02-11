from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from transform import xml_to_canonical, canonical_to_netsuite_payload
from db import init_db, insert_run

import sqlite3
import json
from pathlib import Path


# ---- App metadata ----
app = FastAPI(
    title="Business Adaptive EDI & API Platform Prototype",
    version="0.1.0",
    description="Company-centric, EDI-aware FastAPI prototype with audit + replay capability (thesis MVP).",
)

# ---- DB init on startup (creates runs.db + table if not exists) ----
init_db()

# Keep DB path consistent with db.py logic: runs.db in same folder as code
DB_PATH = Path(__file__).with_name("runs.db")


# ---- Models ----
class IngestRequest(BaseModel):
    raw_xml: str


# ---- Health Check ----
@app.get("/")
def health_check():
    return {"status": "Platform is running"}


# ---- Ingest 850 (Parse + Transform + Save run) ----
@app.post("/ingest/850")
def ingest_850(req: IngestRequest):
    try:
        # 1) Transform
        canonical = xml_to_canonical(req.raw_xml)
        netsuite_payload = canonical_to_netsuite_payload(canonical)

        # 2) Persist run (insert_run generates run_id inside db.py)
        run_id = insert_run(
            partner="COSTCO",
            doc_type="850",
            status="SUCCESS",
            po_number=canonical.get("poNumber"),
            raw_xml=req.raw_xml,
            canonical=canonical,
            netsuite_payload=netsuite_payload,
            error=None,
        )

        # 3) Return response (API-first proof)
        return {
            "run_id": run_id,
            "message": "850 received and transformed",
            "canonical": canonical,
            "netsuite_payload": netsuite_payload,
        }

    except Exception as e:
        # Persist failure run too (audit-friendly)
        run_id = insert_run(
            partner="COSTCO",
            doc_type="850",
            status="FAILED",
            po_number=None,
            raw_xml=req.raw_xml,
            canonical=None,
            netsuite_payload=None,
            error=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail={"message": "Ingest failed", "run_id": run_id, "error": str(e)},
        )


# ---- Internal helper: fetch run row from SQLite ----
def _fetch_run(run_id: str) -> dict | None:
    if not DB_PATH.exists():
        return None

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT run_id, created_at, partner, doc_type, status, po_number,
               raw_xml, canonical_json, netsuite_payload_json, error
        FROM runs
        WHERE run_id = ?
        """,
        (run_id,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "run_id": row[0],
        "created_at": row[1],
        "partner": row[2],
        "doc_type": row[3],
        "status": row[4],
        "po_number": row[5],
        "raw_xml": row[6],
        "canonical_stored": json.loads(row[7]) if row[7] else None,
        "netsuite_payload_stored": json.loads(row[8]) if row[8] else None,
        "error": row[9],
    }


# ---- Replay API (DB raw_xml -> re-transform -> compare) ----
@app.get("/replay/{run_id}")
def replay_run(run_id: str):
    run = _fetch_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail={"message": "run_id not found", "run_id": run_id})

    raw_xml = run.get("raw_xml")
    if not raw_xml:
        raise HTTPException(status_code=400, detail={"message": "No raw_xml stored for this run", "run_id": run_id})

    try:
        canonical_replay = xml_to_canonical(raw_xml)
        netsuite_payload_replay = canonical_to_netsuite_payload(canonical_replay)

        return {
            "message": "Replay executed",
            "run_id": run_id,
            "stored": {
                "created_at": run.get("created_at"),
                "status": run.get("status"),
                "po_number": run.get("po_number"),
                "canonical": run.get("canonical_stored"),
                "netsuite_payload": run.get("netsuite_payload_stored"),
                "error": run.get("error"),
            },
            "replay": {
                "canonical": canonical_replay,
                "netsuite_payload": netsuite_payload_replay,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "Replay failed", "run_id": run_id, "error": str(e)})

