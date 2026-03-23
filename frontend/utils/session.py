"""
Session management.

- Across page navigation: st.session_state persists automatically.
- Across hard reloads: browser cookie via streamlit-cookies-controller.

Call handle_session_init() at the top of every page before any auth check.
"""
import streamlit as st
from streamlit_cookies_controller import CookieController

_COOKIE_KEY = "quartz_session_id"
_MAX_AGE = 7 * 24 * 3600  # 7 days


def _controller() -> CookieController:
    """One CookieController per Streamlit session."""
    if "_cc" not in st.session_state:
        st.session_state["_cc"] = CookieController()
    return st.session_state["_cc"]


def handle_session_init() -> None:
    """
    Resolves the session_id from three possible sources (in priority order):
      1. session_id param  → set by OAuth callback redirect
      2. st.session_state  → already set (normal page navigation)
      3. browser cookie    → persists across hard reloads
    """
    qp = st.query_params
    ctrl = _controller()

    if "session_id" in qp:
        sid = qp["session_id"]
        st.session_state["session_id"] = sid
        ctrl.set(_COOKIE_KEY, sid, max_age=_MAX_AGE)
        st.query_params.clear()
        st.rerun()

    if "session_id" in st.session_state:
        return

    # Try to restore from cookie.
    # On the very first render the component may return None while its JS
    # initialises; the library triggers a re-render automatically so the
    # script will run again with the real value shortly after.
    sid = ctrl.get(_COOKIE_KEY)
    if sid:
        st.session_state["session_id"] = sid


def get_session_id() -> str | None:
    return st.session_state.get("session_id")


def clear_session() -> None:
    st.session_state.pop("session_id", None)
    st.session_state.pop("user_info", None)
    _controller().remove(_COOKIE_KEY)
