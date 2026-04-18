# Real-time Cryptocurrency Analyzer
An AI analyzer for the cryptocurrency market. Ask it anything from price, trends, and trading advice.
<p align="center">
  <img src="https://github.com/user-attachments/assets/d5b2943c-04bd-4abe-afdc-2eede3a15494"
       style="width:30%; height:200px; object-fit:cover;" />
  <img src="https://github.com/user-attachments/assets/79f98a6a-063b-4003-89f7-1dcea4024271"
       style="width:30%; height:200px; object-fit:cover;" />
  <img src="https://github.com/user-attachments/assets/a8f1fc61-0aff-40b9-9fd8-abfe9ffe2a58"
       style="width:30%; height:200px; object-fit:cover;" />
</p>

This project is a real-time, event-driven Retrieval-Augmented Generation (RAG) pipeline that transforms high-frequency market data into time-aware insights by tightly integrating streaming, vector storage, and LLM reasoning. 

Live trade ticks are captured via a WebSocket and structured into JSON events by a producer, then buffered through a distributed queue to ensure reliability under high throughput. These events are consumed, converted into semantic embeddings, and stored in a vector database alongside precise timestamp metadata, creating a temporal vector store that encodes both meaning and recency. 

When a user issues a query, the system performs hybrid retrieval—combining semantic similarity search with timestamp processing—while a preprocessing layer sanitizes event times and aligns them with the current system clock. This enables the LLM to reason not just about relevant information, but also about how recent it is, producing responses that reflect live conditions rather than static knowledge. 

The structure of the project can be viewed below:

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
