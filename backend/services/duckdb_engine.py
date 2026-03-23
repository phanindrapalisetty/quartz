import re
import duckdb
import polars as pl
from typing import Dict, List


class DuckDBEngine:
    """
    One DuckDB in-memory connection per session.
    Tables are registered from DataFrames and persist for the session lifetime.
    """

    def __init__(self):
        self._connections: Dict[str, duckdb.DuckDBPyConnection] = {}

    def _conn(self, session_id: str) -> duckdb.DuckDBPyConnection:
        if session_id not in self._connections:
            self._connections[session_id] = duckdb.connect(":memory:")
        return self._connections[session_id]

    def load_dataframe(self, session_id: str, df: pl.DataFrame, name: str) -> str:
        conn = self._conn(session_id)
        safe = self._sanitize(name)
        # Re-register replaces existing table with same name
        conn.execute(f"DROP VIEW IF EXISTS {safe}")
        conn.register(safe, df)
        return safe

    def query(self, session_id: str, sql: str) -> pl.DataFrame:
        return self._conn(session_id).execute(sql).pl()

    def list_tables(self, session_id: str) -> List[str]:
        rows = self._conn(session_id).execute("SHOW TABLES").fetchall()
        return [r[0] for r in rows]

    def describe(self, session_id: str, table: str) -> List[dict]:
        rows = self._conn(session_id).execute(f"DESCRIBE {table}").fetchall()
        return [{"column": r[0], "type": r[1]} for r in rows]

    def drop_table(self, session_id: str, table: str) -> None:
        conn = self._conn(session_id)
        conn.execute(f"DROP VIEW IF EXISTS {table}")
        conn.execute(f"DROP TABLE IF EXISTS {table}")

    def close(self, session_id: str) -> None:
        conn = self._connections.pop(session_id, None)
        if conn:
            conn.close()

    @staticmethod
    def _sanitize(name: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_]", "_", name).lower()
        return f"t_{safe}" if safe[0].isdigit() else safe


duckdb_engine = DuckDBEngine()
