import io

import polars as pl
from fastapi import APIRouter, File, HTTPException, UploadFile

from services.duckdb_engine import duckdb_engine
from services.google_sheets import to_snake_case
from services.session_store import session_store

router = APIRouter(prefix="/connectors", tags=["connectors"])


def _require_session(session_id: str) -> dict:
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired or not found")
    return session


@router.post("/upload")
async def upload_file(
    session_id: str,
    file: UploadFile = File(...),
    table_alias: str = None,
):
    _require_session(session_id)

    contents = await file.read()
    filename = file.filename or "upload"

    try:
        if filename.endswith(".csv"):
            df = pl.read_csv(io.BytesIO(contents))
        elif filename.endswith((".xlsx", ".xls")):
            df = pl.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use CSV or Excel.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {exc}")

    # Sanitize column names to snake_case
    df = df.rename({col: to_snake_case(col) for col in df.columns})

    name = table_alias or filename.rsplit(".", 1)[0]
    table_name = duckdb_engine.load_dataframe(session_id, df, name)

    return {
        "table_name": table_name,
        "rows": len(df),
        "columns": df.columns,
        "preview": df.head(5).to_dicts(),
    }
