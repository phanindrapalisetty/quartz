from fastapi import APIRouter, HTTPException

from models.schemas import LoadSheetRequest
from services.duckdb_engine import duckdb_engine
from services.google_sheets import list_spreadsheets, list_tabs, fetch_tab
from services.session_store import session_store

router = APIRouter(prefix="/sheets", tags=["sheets"])


def _require_session(session_id: str) -> dict:
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or not found")
    return session


@router.get("/list")
def get_sheets(session_id: str):
    session = _require_session(session_id)
    try:
        return list_spreadsheets(session)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{spreadsheet_id}/tabs")
def get_tabs(spreadsheet_id: str, session_id: str):
    session = _require_session(session_id)
    try:
        return list_tabs(session, spreadsheet_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{spreadsheet_id}/load")
def load_sheet(spreadsheet_id: str, body: LoadSheetRequest, session_id: str):
    session = _require_session(session_id)
    try:
        df = fetch_tab(session, spreadsheet_id, body.tab_name)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    if df.is_empty():
        raise HTTPException(status_code=400, detail="Sheet tab is empty or unreadable")

    table_name = duckdb_engine.load_dataframe(
        session_id, df, body.table_alias or body.tab_name
    )

    return {
        "table_name": table_name,
        "rows": len(df),
        "columns": df.columns,
        "preview": df.head(5).to_dicts(),
    }


@router.get("/loaded")
def loaded_tables(session_id: str):
    _require_session(session_id)
    tables = duckdb_engine.list_tables(session_id)
    return [
        {"name": t, "schema": duckdb_engine.describe(session_id, t)}
        for t in tables
    ]


@router.delete("/loaded/{table_name}")
def drop_table(table_name: str, session_id: str):
    _require_session(session_id)
    try:
        duckdb_engine.drop_table(session_id, table_name)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"ok": True}
