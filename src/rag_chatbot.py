# Meridian HR assistant.
#   python src/rag_chatbot.py "How much PTO can I carry over?"
#   python src/rag_chatbot.py --plain "..."   # no retrieval
#   python src/rag_chatbot.py --show "..."    # also print the retrieved chunks
#   python src/rag_chatbot.py --threshold 0.5 "..."   # drop chunks farther than 0.5

import argparse
import time

import chromadb
import requests

# ── Configuration ──────────────────────────────────────────────
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "company_docs"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "llama3.2:3b"
N_RESULTS = 3
RELEVANCE_THRESHOLD = None  # no cutoff yet: every retrieved chunk is used

PLAIN_SYSTEM_PROMPT = "You are a helpful assistant. Answer questions clearly and concisely."

# When no chunk is relevant, the code declines, not the model: same words every time, and a test
# can check them.
DECLINE = ("I don't have information about that in the company documents. "
           "I can only answer questions about Meridian's HR, IT, expense and data-governance "
           "policies; for anything else, please contact HR.")


# ── Vector database ────────────────────────────────────────────
_collection = None


def get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection


def get_embedding(text):
    response = requests.post(OLLAMA_EMBED_URL, json={"model": EMBED_MODEL, "prompt": text})
    response.raise_for_status()
    return response.json()["embedding"]


def retrieve_context(query, n_results=N_RESULTS):
    results = get_collection().query(
        query_embeddings=[get_embedding(query)],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    return [
        {"text": doc, "source": meta["source"], "distance": dist}
        for doc, meta, dist in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        )
    ]


# ── Relevance filter ───────────────────────────────────────────
def is_relevant(chunk, threshold=RELEVANCE_THRESHOLD):
    return threshold is None or chunk["distance"] < threshold


def filter_relevant(chunks, threshold=RELEVANCE_THRESHOLD):
    return [c for c in chunks if is_relevant(c, threshold)]


def build_system_prompt(chunks):
    context_text = "\n\n---\n\n".join(f"Source: {c['source']}\n{c['text']}" for c in chunks)
    return f"""You are a helpful HR and company policy assistant for Meridian Analytics Group.

Answer the user's question using ONLY the context provided below. If the answer is not
in the context, say "I don't have information about that in the company documents."

Always cite the source document when you provide an answer.

CONTEXT:
{context_text}"""


# ── Model ──────────────────────────────────────────────────────
def chat(system_prompt, question):
    response = requests.post(OLLAMA_CHAT_URL, json={
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "stream": False
    })
    response.raise_for_status()
    return response.json()["message"]["content"]


def answer(question, plain=False, n_results=N_RESULTS, threshold=RELEVANCE_THRESHOLD):
    """Return (reply, chunks). chunks is empty for plain."""
    if plain:
        return chat(PLAIN_SYSTEM_PROMPT, question), []
    chunks = retrieve_context(question, n_results=n_results)
    relevant = filter_relevant(chunks, threshold)
    if not relevant:
        return DECLINE, chunks
    return chat(build_system_prompt(relevant), question), chunks


# ── Command line ───────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Meridian HR assistant")
    parser.add_argument("question", nargs="+", help="the question to ask")
    parser.add_argument("--plain", action="store_true", help="answer without retrieval")
    parser.add_argument("--show", action="store_true", help="print the retrieved chunks")
    parser.add_argument("--threshold", type=float, default=RELEVANCE_THRESHOLD,
                        help=f"drop chunks farther than this cosine distance (default {RELEVANCE_THRESHOLD})")
    args = parser.parse_args()
    question = " ".join(args.question)

    start = time.time()
    try:
        reply, chunks = answer(question, plain=args.plain, threshold=args.threshold)
    except requests.exceptions.ConnectionError:
        print("Cannot connect to Ollama. Is it running? Try: make serve")
        return
    seconds = time.time() - start

    if args.show:
        for i, c in enumerate(chunks, 1):
            kept = "kept" if is_relevant(c, args.threshold) else "dropped"
            print(f"Chunk {i} | {c['source']} | distance {c['distance']:.4f} ({kept})")
            print(c["text"][:400] + ("..." if len(c["text"]) > 400 else ""))
            print("-" * 60)

    print(reply)
    model = "no model call" if reply == DECLINE else CHAT_MODEL
    print(f"\n[{'plain LLM' if args.plain else 'RAG'}, {model}, {seconds:.0f} s]")


if __name__ == "__main__":
    main()
