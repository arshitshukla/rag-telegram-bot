# Mini-RAG Telegram Corporate Assistant

A production-ready Retrieval-Augmented Generation (RAG) system that allows users to query internal Markdown documents via a Telegram Bot. It features high-speed vector retrieval and sub-second LLM inference.

## Key Features
- **Semantic Search:** Uses `sqlite-vec` for local, high-performance vector similarity.
- **Lightning-Fast Inference:** Powered by Llama 3.1 via the Groq LPU API.
- **Source Attribution:** Every answer cites the specific document(s) used as context.
- **Production-Ready:** Fully containerized with Docker and Docker Compose.

## Tech Stack & Models
- **Language:** Python 3.11
- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (Converts text to 384-dimension vectors)
- **LLM:** `llama-3.1-8b-instant` via **Groq Cloud API**
- **Vector Database:** SQLite with the `sqlite-vec` extension
- **Bot Framework:** `python-telegram-bot` (Asynchronous)

## System Design
The system follows a standard RAG pipeline:
1. **Ingestion:** Documents are chunked, embedded, and stored in a SQLite vector table.
2. **Retrieval:** User queries are embedded; the most relevant chunks are fetched via KNN search.
3. **Generation:** Context + Query are sent to Llama 3.1 to generate a factual response.



## How to Run

### Option A: Using Docker Compose (Recommended)
1. **Set Environment Variables:**
   Create a `.env` file in the root directory:
   ```text
   TELEGRAM_BOT_TOKEN=your_telegram_token
   GROQ_API_KEY=your_groq_api_key
   LLM_MODEL_NAME=llama-3.1-8b-instant
   
Launch the Container:

    docker-compose up --build -d


### Option B: Running Locally
Install Dependencies:

    pip install -r requirements.txt

Ingest Data:
Place .md files in /data and run:

    python ingest.py
Start the Bot:

    python main.py


## Demo Interaction
Start the bot on Telegram.

Use the /ask command to query the knowledge base.

Example: /ask What is the Friday dress code?

Response: "The dress code on Fridays is Casual Fridays... Sources: hr_policy.md"