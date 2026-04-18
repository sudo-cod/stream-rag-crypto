import os
import json
import asyncio
import websockets
import time
from dotenv import load_dotenv
from confluent_kafka import Producer

load_dotenv()

ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
KAFKA_BROKER = os.getenv("KAFKA_BROKER")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")

producer = Producer({
    "bootstrap.servers": KAFKA_BROKER,
    "client.id": "alpaca-producer"
})

# ---------------- Kafka callback ----------------
def delivery_report(err, msg):
    if err:
        print(f"❌ Kafka Delivery Failed: {err}")
    else:
        print(f"✅ Kafka Sent → {msg.key()} | {msg.topic()} [{msg.partition()}]")


# ---------------- Stream ----------------
async def stream_alpaca():
    url = "wss://stream.data.alpaca.markets/v1beta3/crypto/us"

    print("🔌 Connecting to Alpaca Crypto Stream...")

    async with websockets.connect(url) as ws:
        print("✅ Connected to Alpaca Crypto WebSocket")

        # AUTH
        await ws.send(json.dumps({
            "action": "auth",
            "key": ALPACA_API_KEY,
            "secret": ALPACA_SECRET_KEY
        }))
        print("🔐 Authentication sent")

        # SUBSCRIBE
        symbols = ["BTC/USD", "ETH/USD", "SOL/USD"]

        await ws.send(json.dumps({
            "action": "subscribe",
            "trades": symbols
        }))

        print(f"📡 Subscribed to: {', '.join(symbols)}")
        print("🚀 Streaming crypto trades → Kafka...\n")

        # metrics
        trade_count = 0
        last_heartbeat = time.time()
        last_price = {}

        while True:
            try:
                msg = await ws.recv()

                data = json.loads(msg)

                if isinstance(data, dict):
                    data = [data]

                # heartbeat log
                if time.time() - last_heartbeat > 10:
                    print("💓 Alive — waiting for trades...")
                    last_heartbeat = time.time()

                for event in data:

                    if event.get("T") != "t":
                        continue

                    trade_count += 1
                    symbol = event.get("S")
                    price = event.get("p")

                    payload = {
                        "symbol": symbol,
                        "price": price,
                        "volume": event.get("s"),
                        "time": event.get("t"),
                    }

                    # -------- LOG OUTPUT --------
                    prev_price = last_price.get(symbol)
                    price_change = ""

                    if prev_price:
                        delta = price - prev_price
                        pct = (delta / prev_price) * 100
                        price_change = f"({pct:+.4f}%)"

                    last_price[symbol] = price

                    print("\n📊 [TRADE EVENT]")
                    print(f"Symbol:   {symbol}")
                    print(f"Price:    {price} {price_change}")
                    print(f"Volume:   {payload['volume']}")
                    print(f"Count:    {trade_count}")
                    print("-" * 50)
                    # ----------------------------

                    producer.produce(
                        topic=KAFKA_TOPIC,
                        key=symbol,
                        value=json.dumps(payload),
                        callback=delivery_report
                    )

                    producer.poll(0)

            except Exception as e:
                print(f"⚠️ Stream error: {e}")
                await asyncio.sleep(1)


# ---------------- MAIN ----------------
if __name__ == "__main__":
    asyncio.run(stream_alpaca())