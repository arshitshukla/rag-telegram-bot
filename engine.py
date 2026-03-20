import os
import sqlite3
import sqlite_vec
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from groq import Groq  

load_dotenv()

# Configuration
DB_PATH = "db/vector_store.db"
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")
# Groq's string for the Llama 3 8B model
LLM_MODEL = os.getenv("LLM_MODEL_NAME", "llama-3.1-8b-instant")

# Initialize Embedding Model
print(f"Initializing Engine with {LLM_MODEL} on Groq...")
embed_model = SentenceTransformer(EMBED_MODEL_NAME)

# Initialize Groq Client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_db_connection():
    db = sqlite3.connect(DB_PATH)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    return db

def retrieve_context(query, top_k=4):
    """Finds the most relevant snippets from the vector database."""
    query_embedding = embed_model.encode(query)
    db = get_db_connection()
    
    results = db.execute(
        """
        SELECT 
            m.text, 
            m.source,
            v.distance
        FROM vec_chunks v
        JOIN chunk_metadata m ON v.rowid = m.rowid
        WHERE embedding MATCH ? AND k = ?
        ORDER BY distance
        """,
        (sqlite_vec.serialize_float32(query_embedding), top_k),
    ).fetchall()
    
    db.close()
    return results

def generate_answer(query):
    """Orchestrates the RAG flow."""
    # 1. Get relevant snippets (Using top_k=4)
    context_chunks = retrieve_context(query, top_k=4)
    
    if not context_chunks:
        return "I couldn't find any relevant information in my documents.", None

    # 2. Build the augmented prompt
    context_text = "\n\n".join([f"--- Source: {c[1]} ---\n{c[0]}" for c in context_chunks])
    sources = list(set([c[1] for c in context_chunks]))
    
    system_prompt = f"""
    You are a professional corporate assistant. Use the provided context to answer the user's question.
    If the answer is not in the context, politely state that you do not have that information.
    Keep the answer concise and factual.

    CONTEXT:
    {context_text}
    """

    # 3. Call Groq API for Ollama model
    try:
        response = groq_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            temperature=0.0 # Set to 0 to keep the bot strictly factual
        )
        # Extract the text from the Groq API response structure
        answer = response.choices[0].message.content
        return answer, sources
        
    except Exception as e:
        return f"Error connecting to Groq: {str(e)}", None

# Quick test if run directly
if __name__ == "__main__":
    test_query = "What is the battery life of the OmniBot 3000?"
    answer, docs = generate_answer(test_query)
    print(f"\nQuestion: {test_query}")
    print(f"Answer: {answer}")
    print(f"Sources used: {docs}")