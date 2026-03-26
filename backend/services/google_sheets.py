import re
from typing import List, Dict
import polars as pl
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def to_snake_case(name: str) -> str:
    name = re.sub(r"[%]", "_pct", name)
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    name = name.strip("_").lower()
    return name or "col"


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


def _creds(session: dict) -> Credentials:
    return Credentials(
        token=session["access_token"],
        refresh_token=session.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=session["client_id"],
        client_secret=session["client_secret"],
        scopes=SCOPES,
    )


def list_spreadsheets(session: dict) -> List[Dict]:
    service = build("drive", "v3", credentials=_creds(session), cache_discovery=False)
    result = (
        service.files()
        .list(
            q="mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
            fields="files(id, name, modifiedTime, webViewLink)",
            orderBy="modifiedTime desc",
            pageSize=50,
        )
        .execute()
    )
    return result.get("files", [])


def list_tabs(session: dict, spreadsheet_id: str) -> List[Dict]:
    service = build("sheets", "v4", credentials=_creds(session), cache_discovery=False)
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    return [
        {"id": s["properties"]["sheetId"], "name": s["properties"]["title"]}
        for s in meta.get("sheets", [])
    ]


def fetch_tab(session: dict, spreadsheet_id: str, tab_name: str) -> pl.DataFrame:
    service = build("sheets", "v4", credentials=_creds(session), cache_discovery=False)
    result = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=f"'{tab_name}'",
            valueRenderOption="UNFORMATTED_VALUE",
            dateTimeRenderOption="FORMATTED_STRING",
        )
        .execute()
    )

    values = result.get("values", [])
    if not values:
        return pl.DataFrame()

    headers = [to_snake_case(h) for h in values[0]]
    rows = values[1:]
    # Pad short rows and replace all "" with None so Polars infers types cleanly
    def clean(cell):
        return None if cell == "" else cell

    padded = [
        [clean(cell) for cell in (r + [None] * (len(headers) - len(r)))]
        for r in rows
    ]
    cols = {headers[i]: [row[i] for row in padded] for i in range(len(headers))}
    return pl.DataFrame(cols, infer_schema_length=None, strict=False)
