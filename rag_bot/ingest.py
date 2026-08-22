from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# Paths
DATA_DIR = Path("data/mock_announcements")
VECTOR_STORE_DIR = "vector_store"


# Load the embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")


# Create persistent ChromaDB client
chroma_client = chromadb.PersistentClient(
    path=VECTOR_STORE_DIR
)


# Create or get the collection
collection = chroma_client.get_or_create_collection(
    name="announcements"
)


def ingest_documents():
    files = list(DATA_DIR.glob("*.txt"))

    if not files:
        print("No .txt files found.")
        return

    for file_path in files:

        # Read the document
        text = file_path.read_text(
            encoding="utf-8"
        ).strip()

        # Skip empty files
        if not text:
            continue

        # Generate embedding
        embedding = model.encode(text).tolist()

        # Use filename (without extension) as the ID
        document_id = file_path.stem

        # Insert or update the document
        collection.upsert(
            ids=[document_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[
                {
                    "filename": file_path.name
                }
            ]
        )

        print(f"Added: {file_path.name}")


if __name__ == "__main__":
    ingest_documents()