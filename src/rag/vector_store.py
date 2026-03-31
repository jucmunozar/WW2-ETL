"""Vector store: semantic search over WW2 event embeddings."""  
from sqlalchemy import select, text

from src.models.base import get_session
from src.models.event import Event
from src.models.embedding import EventEmbedding
from src.etl.embeddings import get_embedding

def semantic_search(query: str, limit: int=5) -> list[dict]:
    """
      Find the most similar events to a user query.
      1. Convert the query text into a vector (via Ollama)
      2. Compare that vector against all event embeddings using cosine distance
      3. Return the top N most similar events
    """
    query_embedding = get_embedding(query)
    session = get_session()

    results = session.execute(
        select(
            EventEmbedding.content,
            EventEmbedding.event_id, 
            Event.event_date,
            Event.title, 
            Event.description,
        )
        .join(Event, EventEmbedding.event_id == Event.id)
        .order_by(EventEmbedding.embedding.cosine_distance(query_embedding))
        .limit(limit)
    ).all()
    session.close()

    return [
        {
            "event_id": row.event_id,
            "date": str(row.event_date),
            "title": row.title,
            "description": row.description, 
            "content": row.content,
        }
        for row in results
    ]

if __name__ == "__main__":
    import json
    results = semantic_search("What happened when Germany invaded Poland?")
    print(json.dumps(results, indent=2))