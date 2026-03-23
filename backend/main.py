from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from routers import auth, connectors, query, sheets

app = FastAPI(title="Quartz", version="0.1.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.streamlit_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sheets.router)
app.include_router(connectors.router)
app.include_router(query.router)


@app.get("/health")
def health():
    return {"status": "ok"}
