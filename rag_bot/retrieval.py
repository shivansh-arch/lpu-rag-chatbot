import chromadb
from sentence_transformers import SentenceTransformer


VECTOR_STORE_DIR = "vector_store"

model = SentenceTransformer("all-MiniLM-L6-v2")

chroma_client = chromadb.PersistentClient(
    path=VECTOR_STORE_DIR
)

collection = chroma_client.get_collection(
    name="announcements"
)


def retrieve_relevant_docs(query, n_results=3):

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    retrieved_docs = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):
        retrieved_docs.append({
            "text": document,
            "filename": metadata["filename"],
            "distance": distance
        })

    return retrieved_docs


if __name__ == "__main__":
    results = retrieve_relevant_docs(
        "am I eligible for the Amazon drive"
    )

    print("\nRetrieved documents:")

    for result in results:
        print("\n---")
        print("File:", result["filename"])
        print("Distance:", result["distance"])
        print("Text:", result["text"])