import os

import requests
import streamlit as st

from utils.session import clear_session, get_session_id, handle_session_init

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Load Data — Quartz", layout="wide")

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


st.title("Load Data")

if not get_session_id():
    st.warning("Please login first.")
    st.stop()

tab_sheets, tab_upload = st.tabs(["Google Sheets", "Upload Excel / CSV"])


# ── Google Sheets tab ─────────────────────────────────────────────────────────

with tab_sheets:
    with st.spinner("Fetching your spreadsheets..."):
        r = api("get", "/sheets/list")

    if r is None:
        st.stop()  # error already shown by api()
    elif not r.ok:
        st.error(r.json().get("detail", "Could not fetch spreadsheets"))
    else:
        sheets = r.json()
        if not sheets:
            st.info("No spreadsheets found in your Google Drive.")
        else:
            sheet_map = {s["name"]: s for s in sheets}
            chosen_name = st.selectbox("Spreadsheet", list(sheet_map.keys()))
            chosen = sheet_map[chosen_name]

            r2 = api("get", f"/sheets/{chosen['id']}/tabs")
            if r2 and r2.ok:
                tabs = r2.json()
                tab_name = st.selectbox("Tab", [t["name"] for t in tabs])
                alias = st.text_input("Table alias (optional)", placeholder=tab_name)

                if st.button("Load tab", type="primary"):
                    with st.spinner("Loading..."):
                        r3 = api(
                            "post",
                            f"/sheets/{chosen['id']}/load",
                            json={"tab_name": tab_name, "table_alias": alias or None},
                        )
                    if r3 and r3.ok:
                        res = r3.json()
                        st.success(
                            f"Loaded as `{res['table_name']}` — "
                            f"{res['rows']} rows · {len(res['columns'])} columns"
                        )
                        st.dataframe(res["preview"], use_container_width=True)
                    elif r3:
                        st.error(r3.json().get("detail", "Failed to load sheet"))


# ── Upload tab ────────────────────────────────────────────────────────────────

with tab_upload:
    uploaded = st.file_uploader("Upload a file", type=["xlsx", "csv"])
    alias = st.text_input("Table alias (optional)", placeholder="my_table", key="upload_alias")

    if uploaded and st.button("Load file", type="primary"):
        with st.spinner("Loading..."):
            r = api(
                "post",
                "/connectors/upload",
                files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
                params={"table_alias": alias} if alias else {},
            )
        if r and r.ok:
            res = r.json()
            st.success(
                f"Loaded as `{res['table_name']}` — "
                f"{res['rows']} rows · {len(res['columns'])} columns"
            )
            st.dataframe(res["preview"], use_container_width=True)
        elif r:
            st.error(r.json().get("detail", "Upload failed"))


# ── Loaded tables summary ─────────────────────────────────────────────────────

st.divider()
st.subheader("Loaded Tables")

r = api("get", "/sheets/loaded")
if r and r.ok:
    tables = r.json()
    if tables:
        for t in tables:
            with st.expander(f"`{t['name']}`"):
                lines = [f"{c['column']}  ·  {c['type']}" for c in t["schema"]]
                st.code("\n".join(lines), language=None)
                if st.button("Drop table", key=f"drop_{t['name']}", type="secondary"):
                    rd = api("delete", f"/sheets/loaded/{t['name']}")
                    if rd and rd.ok:
                        st.rerun()
                    elif rd:
                        st.error(rd.json().get("detail", "Failed to drop table"))
    else:
        st.caption("Nothing loaded yet.")
