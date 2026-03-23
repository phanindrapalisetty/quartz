from pydantic import BaseModel
from typing import Optional, List


class LoadSheetRequest(BaseModel):
    tab_name: str
    table_alias: Optional[str] = None


class QueryRequest(BaseModel):
    sql: str


class ColumnSchema(BaseModel):
    column: str
    type: str


class LoadedTable(BaseModel):
    name: str
    schema: List[ColumnSchema]
