# Real-time Cryptocurrency Analyzer
A real-time AI analyzer for the cryptocurrency market. Ask it anything from price, trends, and trading advice.
Demo:
<img width="643" height="547" alt="Screenshot 2026-04-19 at 01 19 36" src="https://github.com/user-attachments/assets/d5b2943c-04bd-4abe-afdc-2eede3a15494" />
<img width="641" height="585" alt="Screenshot 2026-04-19 at 01 19 22" src="https://github.com/user-attachments/assets/79f98a6a-063b-4003-89f7-1dcea4024271" />
<img width="786" height="467" alt="Screenshot 2026-04-19 at 01 19 47" src="https://github.com/user-attachments/assets/a8f1fc61-0aff-40b9-9fd8-abfe9ffe2a58" />

This system is a real-time, event-driven Retrieval-Augmented Generation (RAG) pipeline that transforms high-frequency market data into time-aware insights by tightly integrating streaming, vector storage, and LLM reasoning. Live trade ticks are captured via a WebSocket and structured into JSON events by a producer, then buffered through a distributed queue to ensure reliability under high throughput. These events are consumed, converted into semantic embeddings, and stored in a vector database alongside precise timestamp metadata, creating a temporal vector store that encodes both meaning and recency. When a user issues a query, the system performs hybrid retrieval—combining semantic similarity search with timestamp processing—while a preprocessing layer sanitizes event times and aligns them with the current system clock. This enables the LLM to reason not just about relevant information, but also about how recent it is, producing responses that reflect live conditions rather than static knowledge. By bridging real-time data streams with contextual retrieval and temporal awareness, the pipeline effectively solves the stale-data limitation of traditional RAG systems and enables continuous, up-to-date narrative generation.

        ┌────────────────────┐
        │  Market (WebSocket)│
        └─────────┬──────────┘
                  │ Raw ticks
                  ▼
        ┌────────────────────┐
        │  Producer (Kafka)  │
        │  JSON Formatter    │
        └─────────┬──────────┘
                  │ Structured events
                  ▼
        ┌────────────────────┐
        │      Kafka         │
        │  (Buffer/Queue)    │
        └─────────┬──────────┘
                  │ Stream
                  ▼
        ┌────────────────────┐
        │  Ingestor          │
        │  + Embeddings      │
        └─────────┬──────────┘
                  │ Vectors + metadata
                  ▼
        ┌────────────────────┐
        │     Qdrant         │
        │ (Temporal Vectors) │
        └─────────┬──────────┘
                  │ Retrieval
                  ▼
        ┌────────────────────┐
        │   RAG Narrator     │
        │ (Time Processing)  │
        └─────────┬──────────┘
                  │ Prompt
                  ▼
        ┌────────────────────┐
        │       LLM          │
        │ (DeepSeek)         │
        └─────────┬──────────┘
                  │ Streamed response
                  ▼
               User
