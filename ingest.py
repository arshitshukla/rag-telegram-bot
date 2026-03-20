import os
import glob
import sqlite3
import sqlite_vec
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# 1. Load configuration
load_dotenv()
DATA_DIR = "data"
DB_PATH = "db/vector_store.db"
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")

print(f"Loading embedding model: {EMBED_MODEL_NAME}...")
embed_model = SentenceTransformer(EMBED_MODEL_NAME)

# 2. Database Setup
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
db = sqlite3.connect(DB_PATH)
db.enable_load_extension(True)
sqlite_vec.load(db)
db.enable_load_extension(False)

with db:
    db.execute("DROP TABLE IF EXISTS vec_chunks")
    db.execute("DROP TABLE IF EXISTS chunk_metadata")
    
    # Virtual table for extremely fast vector search
    db.execute('''
        CREATE VIRTUAL TABLE vec_chunks USING vec0(
            embedding float[384]
        );
    ''')
    
    # Standard table for storing the actual text and source
    db.execute('''
        CREATE TABLE chunk_metadata (
            rowid INTEGER PRIMARY KEY,
            source TEXT,
            text TEXT
        );
    ''')

def chunk_text(text, max_words=100):
    """A simple chunker that splits by paragraphs to keep context intact."""
    paragraphs = text.split("\n\n")
    chunks = []
    for p in paragraphs:
        p = p.strip()
        if p:
            chunks.append(p)
    return chunks

def ingest_documents():
    md_files = glob.glob(os.path.join(DATA_DIR, "*.md"))
    if not md_files:
        print(f"No Markdown files found in {DATA_DIR}/")
        return

    total_chunks = 0
    
    with db:
        for file_path in md_files:
            filename = os.path.basename(file_path)
            print(f"Processing: {filename}...")
            
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                
            chunks = chunk_text(text)
            
            for chunk in chunks:
                # A. Generate Embedding
                embedding = embed_model.encode(chunk)
                
                # B. Insert Metadata (Text & Source)
                cursor = db.execute(
                    "INSERT INTO chunk_metadata (source, text) VALUES (?, ?)", 
                    (filename, chunk)
                )
                row_id = cursor.lastrowid # Get the ID of the inserted text
                
                # C. Insert Vector (Linked via rowid)
                db.execute(
                    "INSERT INTO vec_chunks (rowid, embedding) VALUES (?, ?)",
                    (row_id, sqlite_vec.serialize_float32(embedding))
                )
                total_chunks += 1

    print(f"Ingestion complete! {total_chunks} chunks saved to {DB_PATH}.")

if __name__ == "__main__":
    ingest_documents()