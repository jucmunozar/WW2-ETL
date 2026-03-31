"""RAG and semantic search endpoints."""

from fastapi import APIRouter

from src.api.schemas import (
    SemanticSearchRequest, SemanticSearchResponse,
    SemanticSearchResult, ChatRequest, ChatResponse,
  )
from src.rag.vector_store import semantic_search
from src.rag.chain import ask

router = APIRouter(tags=["RAG"])

@router.post("/search/semantic", response_model=SemanticSearchResponse)
def search_semantic(request: SemanticSearchRequest):
    results = semantic_search(request.query,
    limit=request.limit)
    return SemanticSearchResponse(
        query=request.query,
        results=[SemanticSearchResult(**r) for r in results],
      )

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    result = ask(request.question, limit=request.limit)
    return ChatResponse(
        answer=result["answer"],
        sources=[SemanticSearchResult(**s) for s in
        result["sources"]],
      )