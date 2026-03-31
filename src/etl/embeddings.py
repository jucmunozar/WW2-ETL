"""Generate embeddings for WW2 Events using Ollama"""
import requests
from sqlalchemy import select

from src.models.base import get_session
from src.models.event import Event
from src.models.embedding import EventEmbedding

OLLAMA_URL = "http://localhost:11434/api/embeddings"
MODEL = "nomic-embed-text"

def get_embedding(text: str) -> list[float]:
    """send text to Ollama and return embedding vector"""
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": text,
    })
    response.raise_for_status()
    return response.json()["embedding"]

def build_content(event: Event) -> str:
    """concatenate event title and description into single string"""
    parts = [event.title]
    if event.description: 
        parts.append(event.description)
    return ". ".join(parts)

def generate_embeddings() -> None:
    """Generate embeddings for all events that don't have one yet."""
    session=get_session()

    #find events without embedding
    existing_ids = select(EventEmbedding.event_id)
    events = session.scalars(
        select(Event).where(Event.id.not_in(existing_ids))
    ).all()

    print(f"Events without embeddings: {len(events)}")

    for i, event in enumerate (events, 1):
        content = build_content(event)
        embedding = get_embedding(content)
        event_embedding = EventEmbedding(
              event_id=event.id,
              content=content,
              embedding=embedding,
          )
        session.add(event_embedding)
        session.commit()
        print(f"  [{i}/{len(events)}] {event.title[:60]}")

    session.close()
    print("Done.")

if __name__ == "__main__":
    generate_embeddings()