#   python src/explore_index.py "How much PTO can I carry over?"

import sys

import chromadb
import requests

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "company_docs"
OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"

if len(sys.argv) < 2:
    sys.exit('usage: python src/explore_index.py "your question"')
query = " ".join(sys.argv[1:])

embedding = requests.post(OLLAMA_URL, json={"model": EMBED_MODEL, "prompt": query}).json()["embedding"]
collection = chromadb.PersistentClient(path=CHROMA_PATH).get_collection(COLLECTION_NAME)
results = collection.query(query_embeddings=[embedding], n_results=3,
                           include=["documents", "metadatas", "distances"])

print(f"QUERY: {query}")
for i, (doc, meta, dist) in enumerate(zip(
    results["documents"][0], results["metadatas"][0], results["distances"][0]
), 1):
    section = f" §{meta['section']}" if "section" in meta else ""
    print(f"\n  Result {i} | Source: {meta['source']}{section} | Distance: {dist:.4f}")
    print(f"  {doc[:300]}...")
