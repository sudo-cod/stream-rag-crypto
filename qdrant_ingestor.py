import os
import json
import uuid
import ssl
import requests
from dotenv import load_dotenv
from confluent_kafka import Consumer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_nomic import NomicEmbeddings
from requests.adapters import HTTPAdapter
from urllib3.util import ssl_

load_dotenv()


# --- SSL PATCH FOR MAC/PYTHON 3.14 ---
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl_.create_urllib3_context(ssl_version=ssl.PROTOCOL_TLSv1_2)
        kwargs['ssl_context'] = ctx
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)


# Force Nomic/Requests to be less sensitive
session = requests.Session()
session.mount("https://", TLSAdapter())
# -------------------------------------

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "market_context"
VECTOR_SIZE = 768

qdrant = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)

embedder = NomicEmbeddings(
    model="nomic-embed-text-v1.5",
    nomic_api_key=os.getenv("NOMIC_API_KEY")
)


def ensure_collection_exists():
    collections = qdrant.get_collections().collections
    if not any(c.name == COLLECTION_NAME for c in collections):
        print(f"🏗️ Creating collection {COLLECTION_NAME}...")
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE)
        )


def run_ingestor():
    ensure_collection_exists()

    consumer = Consumer({
        "bootstrap.servers": os.getenv("KAFKA_BROKER"),
        "group.id": "qdrant-ingestor",
        "auto.offset.reset": "latest"
    })
    consumer.subscribe([os.getenv("KAFKA_TOPIC", "market-ticks")])

    print("🧠 Qdrant Ingestor Running (with SSL Patch)...")

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None or msg.error():
                continue

            try:
                data = json.loads(msg.value().decode("utf-8"))
                symbol = data["symbol"]
                price = data["price"]
                trade_time = data.get("time", "Unknown")

                text = f"{symbol} traded at {price} at {trade_time}"

                # The point of failure is usually right here
                vector = embedder.embed_query(text)

                qdrant.upsert(
                    collection_name=COLLECTION_NAME,
                    points=[
                        models.PointStruct(
                            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{symbol}_{trade_time}")),
                            vector=vector,
                            payload={"text": text, "symbol": symbol, "price": price, "time": trade_time}
                        )
                    ]
                )
                print(f"📥 Stored: {text}")

            except Exception as e:
                # If Nomic fails, we log it and keep the consumer alive
                print(f"⚠️ Ingestion skipped due to network error: {e}")
                continue

    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        consumer.close()


if __name__ == "__main__":
    run_ingestor()