import time

from fastapi import APIRouter, HTTPException

from models.schemas import QueryRequest
from services.duckdb_engine import duckdb_engine
from services.session_store import session_store

router = APIRouter(prefix="/query", tags=["query"])


@router.post("/")
def run_query(body: QueryRequest, session_id: str):
    if not session_store.get(session_id):
        raise HTTPException(status_code=401, detail="Session expired")

    t0 = time.perf_counter()
    try:
        df = duckdb_engine.query(session_id, body.sql)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

    return {
        "rows": len(df),
        "columns": df.columns,
        "data": df.to_dicts(),
        "execution_time_ms": elapsed_ms,
    }
