import os

import requests
import streamlit as st

from utils.session import clear_session, get_session_id, handle_session_init

API_URL = os.getenv("API_URL", "http://localhost:8000")
PUBLIC_API_URL = os.getenv("PUBLIC_API_URL", "http://localhost:8000")

st.set_page_config(page_title="Quartz", page_icon="📊", layout="wide")

handle_session_init()


# ── helpers ───────────────────────────────────────────────────────────────────

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


# ── unauthenticated landing ───────────────────────────────────────────────────

if not get_session_id():
    st.title("Quartz")
    st.markdown(
        "Query your Google Sheets and databases with SQL.  \n"
        "No service accounts. No sharing with bots. Just login and query."
    )
    st.divider()
    st.link_button("Login with Google", f"{PUBLIC_API_URL}/auth/login", type="primary")
    st.stop()


# ── fetch user once ───────────────────────────────────────────────────────────

if "user_info" not in st.session_state:
    r = api("get", "/auth/me")
    if r and r.ok:
        st.session_state["user_info"] = r.json()

user = st.session_state.get("user_info", {})


# ── sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(f"**{user.get('name', 'User')}**")
    st.caption(user.get("email", ""))
    st.divider()
    if st.button("Logout", use_container_width=True):
        api("delete", "/auth/logout")
        clear_session()
        st.rerun()
    st.divider()
    st.page_link("app.py", label="Home", icon="🏠")
    st.page_link("pages/1_Load.py", label="Load Data", icon="📂")
    st.page_link("pages/2_Query.py", label="Query", icon="🔍")


# ── home ──────────────────────────────────────────────────────────────────────

st.title("Quartz")

r = api("get", "/sheets/loaded")
tables = r.json() if r and r.ok else []

if not tables:
    st.info("No tables loaded yet. Go to **Load Data** to connect a source.")
else:
    st.subheader(f"{len(tables)} table(s) in session")
    for t in tables:
        with st.expander(f"`{t['name']}` — {len(t['schema'])} columns"):
            for col in t["schema"]:
                st.caption(f"{col['column']}  ·  {col['type']}")
