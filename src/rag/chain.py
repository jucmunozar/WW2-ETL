"""RAG chain: answer questions about WW2 using event context.""" 
import requests
from src.rag.vector_store import semantic_search

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1" 

PROMPT_TEMPLATE = """
You are a WW2 history expert.
Answer the user's question using ONLY the events provided below. If
the events don't contain enough information, say so.

EVENTS: {context}
QUESTION: {question}
ANSWER:
"""

def format_context(events: list[dict]) ->str:
    """format retrieved events into a readable string for the LLM"""
    lines = []
    for e in events:
        lines.append(f"- [{e['date']}] {e['title']}: {e['description']}") 
    return "\n".join(lines)

def ask(question: str, limit: int=5) -> dict:
    """
    Full RAG pipeline:
    1. Retrieve relevant events(semantic search)
    2. Build a prompt with those events as context
    3. Send to LLM and return answer
    """
    events = semantic_search(question, limit = limit)
    context = format_context(events)
    prompt = PROMPT_TEMPLATE.format(context=context, question = question)
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL, 
        "prompt": prompt, 
        "stream": False, 
    })
    response.raise_for_status()

    return{
        "answer": response.json()["response"],
        "sources": events, 
    }

if __name__ == "__main__":
    result = ask("What happened when Germany invaded Poland?")                           
    print("ANSWER:", result["answer"])            
    print("\nSOURCES:")                           
    for s in result["sources"]:                   
        print(f"  [{s['date']}] {s['title']}") 