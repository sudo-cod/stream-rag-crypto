import os, json, asyncio, websockets, time
from dotenv import load_dotenv
from confluent_kafka import Producer

load_dotenv()

class AlpacaNewsProducer:
    def __init__(self):
        self.producer = Producer({
            "bootstrap.servers": os.getenv("KAFKA_BROKER"),
            "client.id": "alpaca-news-producer"
        })

        self.url = "wss://stream.data.alpaca.markets/v1beta1/news"

        self.msg_count = 0
        self.last_heartbeat = time.time()

    # ---------------- Kafka callback ----------------
    def delivery_report(self, err, msg):
        if err:
            print(f"[KAFKA ERROR] {err}")
        else:
            print(f"[KAFKA OK] {msg.topic()} → {msg.key()}")

    # ---------------- Main loop ----------------
    async def start(self):
        print("🔌 Connecting to Alpaca News Stream...")

        async with websockets.connect(self.url) as ws:
            print("✅ Connected to Alpaca News WebSocket")

            # AUTH
            auth_msg = {
                "action": "auth",
                "key": os.getenv("ALPACA_API_KEY"),
                "secret": os.getenv("ALPACA_SECRET_KEY")
            }
            await ws.send(json.dumps(auth_msg))
            print("🔐 Auth sent")

            # SUBSCRIBE
            sub_msg = {
                "action": "subscribe",
                "news": ["BTC", "ETH", "SOL"]
            }
            await ws.send(json.dumps(sub_msg))
            print("📡 Subscribed to crypto news stream")

            print("🚀 Streaming news → Kafka...\n")

            while True:
                try:
                    raw_msg = await ws.recv()
                    data = json.loads(raw_msg)

                    # Normalize (sometimes list, sometimes dict)
                    if isinstance(data, dict):
                        data = [data]

                    # Heartbeat
                    if time.time() - self.last_heartbeat > 10:
                        print("💓 Alive - waiting for news...")
                        self.last_heartbeat = time.time()

                    for item in data:

                        if item.get("T") != "n":
                            continue

                        self.msg_count += 1

                        payload = {
                            "id": item.get("id"),
                            "headline": item.get("headline"),
                            "summary": item.get("summary"),
                            "symbols": item.get("symbols"),
                            "timestamp": item.get("updated_at"),
                            "url": item.get("url")
                        }

                        # -------- TERMINAL LOGGING --------
                        symbols_str = ", ".join(payload.get("symbols") or [])

                        print("\n📰 [NEWS EVENT]")
                        print(f"ID:       {payload['id']}")
                        print(f"Targets:  {symbols_str}")
                        print(f"Headline: {payload['headline']}")
                        print(f"Time:     {payload['timestamp']}")
                        print(f"Count:    {self.msg_count}")
                        print("-" * 60)
                        # -----------------------------------

                        key = payload["symbols"][0] if payload.get("symbols") else "GENERAL"

                        self.producer.produce(
                            topic="market-news",
                            key=key,
                            value=json.dumps(payload),
                            callback=self.delivery_report
                        )

                    # Flush every loop (safe for news, low volume)
                    self.producer.poll(0)

                except Exception as e:
                    print(f"⚠️ Stream error: {e}")
                    await asyncio.sleep(1)


# ---------------- ENTRY ----------------
if __name__ == "__main__":
    news_stream = AlpacaNewsProducer()
    asyncio.run(news_stream.start())