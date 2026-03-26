import os

import polars as pl
import requests
import streamlit as st

from utils.session import clear_session, get_session_id, handle_session_init

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Query — Quartz", layout="wide")

handle_session_init()


def api(method: str, path: str, **kwargs):
    sid = get_session_id()
    if not sid:
        return None
    params = kwargs.pop("params", {})
    params["session_id"] = sid
    try:
        resp = getattr(requests, method)(f"{API_URL}{path}", params=params, **kwargs)
    except requests.exceptions.RequestException as exc:
        st.error(f"Backend unreachable: {exc}")
        return None
    if resp.status_code == 401:
        clear_session()
        st.rerun()
    return resp


if not get_session_id():
    st.warning("Please login first.")
    st.stop()


# ── schema sidebar ────────────────────────────────────────────────────────────

with st.sidebar:
    st.subheader("Tables")
    r = api("get", "/sheets/loaded")
    if r and r.ok:
        tables = r.json()
        if tables:
            for t in tables:
                with st.expander(f"`{t['name']}`"):
                    for c in t["schema"]:
                        st.caption(f"{c['column']}  ·  {c['type']}")
        else:
            st.caption("No tables loaded.")
            st.page_link("pages/1_Load.py", label="Load Data →")


# ── query editor ──────────────────────────────────────────────────────────────

st.title("Query")

default = st.session_state.get("last_sql", "SELECT *\nFROM your_table\nLIMIT 20")
sql = st.text_area("SQL", value=default, height=160, label_visibility="collapsed")

col_run, col_clear, _ = st.columns([1, 1, 8])
run = col_run.button("Run", type="primary", use_container_width=True)
if col_clear.button("Clear", use_container_width=True):
    st.session_state.pop("last_sql", None)
    st.rerun()

if run and sql.strip():
    st.session_state["last_sql"] = sql
    with st.spinner("Running query..."):
        r = api("post", "/query/", json={"sql": sql})

    if r and r.ok:
        res = r.json()
        st.caption(f"{res['rows']} rows · {res['execution_time_ms']} ms")
        df = pl.from_dicts(res["data"]) if res["data"] else pl.DataFrame()
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.write_csv().encode()
        st.download_button("Download CSV", csv, "results.csv", "text/csv")
    elif r:
        st.error(r.json().get("detail", "Query failed"))
