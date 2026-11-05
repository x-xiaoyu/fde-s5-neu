import os
import re
import sys

import requests
import chromadb

# ── Configuration ──────────────────────────────────────────────
DOCS_FOLDER = "meridian_docs"
CHUNK_SIZE = 400        # words per chunk
CHUNK_OVERLAP = 50      # words of overlap between adjacent chunks
OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "company_docs"

# ── Step 1: Load documents ──────────────────────────────────────
def load_documents(folder):
    documents = []
    for filename in os.listdir(folder):
        if filename.endswith(".txt"):
            filepath = os.path.join(folder, filename)
            with open(filepath, "r") as f:
                content = f.read()
            documents.append({
                "filename": filename,
                "content": content
            })
            print(f"  Loaded: {filename} ({len(content)} chars)")
    return documents

# ── Step 2: Split into overlapping chunks ──────────────────────
def chunk_document(text, source, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    start = 0
    chunk_id = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_text = " ".join(words[start:end])
        chunks.append({
            "id": f"{source}_chunk_{chunk_id}",
            "text": chunk_text,
            "source": source,
            "chunk_index": chunk_id
        })
        chunk_id += 1
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks

# ── Or (--by-section): one chunk per numbered section, e.g. "4.2" ──
SECTION = re.compile(r"^(\d+\.\d+) ", re.MULTILINE)

def chunk_by_section(text, source):
    starts = [m.start() for m in SECTION.finditer(text)] + [len(text)]
    chunks = []
    for i, (start, end) in enumerate(zip(starts, starts[1:])):
        section = SECTION.match(text, start).group(1)
        chunks.append({
            "id": f"{source}_{section}",
            "text": text[start:end].strip(),
            "source": source,
            "chunk_index": i,
            "section": section
        })
    return chunks

# ── Step 3: Generate embedding via Ollama ──────────────────────
def get_embedding(text):
    response = requests.post(OLLAMA_URL, json={
        "model": EMBED_MODEL,
        "prompt": text
    })
    response.raise_for_status()
    return response.json()["embedding"]

# ── Main indexing pipeline ─────────────────────────────────────
def build_index(by_section=False):
    print("\n=== Building RAG Index ===\n")

    print("Step 1: Loading documents...")
    documents = load_documents(DOCS_FOLDER)
    print(f"  → {len(documents)} documents loaded\n")

    print("Step 2: Chunking documents...")
    all_chunks = []
    for doc in documents:
        split = chunk_by_section if by_section else chunk_document
        chunks = split(doc["content"], doc["filename"])
        all_chunks.extend(chunks)
        print(f"  {doc['filename']} → {len(chunks)} chunks")
    print(f"  → {len(all_chunks)} total chunks\n")

    print("Step 3: Initializing ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        client.delete_collection(COLLECTION_NAME)
        print("  → Existing collection cleared")
    except:
        pass
    # cosine distance: 0 = same direction, 1 = unrelated, 2 = opposite
    collection = client.create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    print(f"  → Collection '{COLLECTION_NAME}' created\n")

    print("Step 4: Generating embeddings and storing in ChromaDB...")
    for i, chunk in enumerate(all_chunks):
        print(f"  Embedding chunk {i+1}/{len(all_chunks)}: {chunk['id']}")
        embedding = get_embedding(chunk["text"])
        collection.add(
            ids=[chunk["id"]],
            embeddings=[embedding],
            documents=[chunk["text"]],
            metadatas=[{k: chunk[k] for k in ("source", "chunk_index", "section") if k in chunk}]
        )

    print(f"\n✅ Index built successfully.")
    print(f"   {len(all_chunks)} chunks stored in {CHROMA_PATH}/")
    print(f"   Collection: '{COLLECTION_NAME}'")

if __name__ == "__main__":
    build_index(by_section="--by-section" in sys.argv)
