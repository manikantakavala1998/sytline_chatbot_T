"""
FastAPI app entry point. The Q&A search index is built once at startup
(not on the first request) so the first real user isn't the one waiting
for the embedding model to load.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.routes import router
from backend.app.qa.retriever import get_qa_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_qa_index()
    yield


app = FastAPI(
    title="SyteLine Prospect-to-Cash AI Chatbot",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)
