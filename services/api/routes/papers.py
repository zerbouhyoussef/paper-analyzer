from fastapi import APIRouter, HTTPException, Query

from services.api.paper_store import PaperStore

router = APIRouter(prefix="/papers", tags=["papers"])
store = PaperStore()


@router.get("/")
def list_papers() -> list[dict]:
    """List all papers with basic metadata."""
    return [
        {
            "paper_id": p.paper_id,
            "title": p.title,
            "authors": p.authors,
            "topics": p.topics,
            "status": p.status,
        }
        for p in store.list_papers()
    ]


@router.get("/search")
def search_papers(q: str = Query(..., min_length=1), top_k: int = Query(5, ge=1, le=50)) -> dict:
    """Semantic search over papers by natural-language query."""
    results = store.search(q, top_k=top_k)
    if not results:
        return {"query": q, "results": [], "message": "No papers indexed yet"}
    return {"query": q, "results": [r.model_dump() for r in results]}


@router.get("/{paper_id}")
def get_paper(paper_id: str) -> dict:
    """Get full paper details (excluding raw embedding vector)."""
    paper = store.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper.model_dump(exclude={"embedding"})


@router.get("/{paper_id}/summary")
def get_paper_summary(paper_id: str) -> dict:
    """Get just the AI-generated summary for a paper."""
    paper = store.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
    return {
        "paper_id": paper.paper_id,
        "title": paper.title,
        "summary": paper.summary.model_dump(),
    }
