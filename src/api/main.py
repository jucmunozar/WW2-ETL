"""FastAPI application for WW2 Timeline API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import events, stats, rag

app = FastAPI(
    title="WW2 Timeline API",
    description="REST API for World War II timeline events",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(stats.router)
app.include_router(rag.router)


@app.get("/")
def root():
    return {
        "name": "WW2 Timeline API",
        "version": "1.0.0",
        "docs": "/docs",
    }
