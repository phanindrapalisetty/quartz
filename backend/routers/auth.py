from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from core.config import settings
from services.session_store import session_store

router = APIRouter(prefix="/auth", tags=["auth"])

_GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO = "https://www.googleapis.com/oauth2/v3/userinfo"

_SCOPES = " ".join([
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "openid",
    "email",
    "profile",
])


@router.get("/login")
def login():
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": _SCOPES,
        "access_type": "offline",
        "prompt": "consent",
    }
    return RedirectResponse(f"{_GOOGLE_AUTH}?{urlencode(params)}")


@router.get("/callback")
async def callback(code: str = None, error: str = None):
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(_GOOGLE_TOKEN, data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        })
        token = token_resp.json()

    if "error" in token:
        raise HTTPException(status_code=400, detail=token.get("error_description", token["error"]))

    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            _GOOGLE_USERINFO,
            headers={"Authorization": f"Bearer {token['access_token']}"},
        )
        user = user_resp.json()

    session_id = session_store.create({
        "access_token": token["access_token"],
        "refresh_token": token.get("refresh_token"),
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "user_email": user.get("email"),
        "user_name": user.get("name"),
        "user_picture": user.get("picture"),
    })

    return RedirectResponse(f"{settings.streamlit_url}?session_id={session_id}")


@router.get("/me")
def me(session_id: str):
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session not found or expired")
    return {
        "email": session["user_email"],
        "name": session["user_name"],
        "picture": session["user_picture"],
    }


@router.delete("/logout")
def logout(session_id: str):
    session_store.delete(session_id)
    return {"ok": True}
