import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from langchain_nomic import NomicEmbeddings
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown

load_dotenv()
console = Console()

# ---------------- CONFIG ----------------
qdrant = QdrantClient("localhost", port=6333)
COLLECTION_NAME = "market_context"

embedder = NomicEmbeddings(
    model="nomic-embed-text-v1.5",
    nomic_api_key=os.getenv("NOMIC_API_KEY")
)

ai_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL")
)


def get_market_context(query: str, limit: int = 5):
    query_text = f"search_query: {query}"
    vector = embedder.embed_query(query_text)

    # Using the new query_points API
    search_result = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=limit
    )

    # We return the full payload so the LLM can see the 'time' field
    return [hit.payload for hit in search_result.points]


def narrate_crypto_query(user_query: str):
    # 1. Fix Deprecation: Use timezone-aware UTC
    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 2. Get data + timestamps
    payloads = get_market_context(user_query)

    # Format context so LLM explicitly sees the time for each trade
    context_list = []
    for p in payloads:
        # Check if 'time' exists in payload (it should if ingestor is updated)
        t = p.get('time', 'Unknown Time')
        context_list.append(f"- {p['text']} (Timestamp: {t})")

    context_str = "\n".join(context_list)

    if not payloads:
        return "I don't have any recent data in my database to answer that."

    system_prompt = (
        f"You are a real-time crypto analyst. The current system time is {current_time}. "
        "Use the provided trades to answer. "
        "IMPORTANT: When mentioning times, convert them from ISO format to a "
        "clean, human-readable format like '16:15:05' or 'just now'."
    )

    user_prompt = f"""
    LATEST TRADES:
    {context_str}

    USER QUESTION: {user_query}

    ANALYSIS:"""

    response = ai_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    console.print("[bold cyan]🛰️ DeepSeek Crypto Narrator Online.[/bold cyan]")
    try:
        while True:
            query = input("\n💬 Query: ")
            if query.lower() in ["exit", "quit"]:
                break

            answer = narrate_crypto_query(query)
            console.print("\n📊 [bold]ANALYSIS:[/bold]")
            console.print(Markdown(answer))

    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting...[/yellow]")