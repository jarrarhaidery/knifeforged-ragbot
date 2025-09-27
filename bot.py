import chromadb
from config import VECTOR_DB, CHROMA_DB_DIR, FAISS_DIR, EMBEDDING_MODEL
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()

# Load embedding model
embedding_model = SentenceTransformer(EMBEDDING_MODEL)

# Configure Gemini with API key only (no ADC!)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
llm_model = "gemini-2.5-flash"   # or "gemini-1.5-pro" if you prefer

def get_chroma_collection():
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    return client.get_or_create_collection("products")

def retrieve(query, top_k=5):
    query_emb = embedding_model.encode(query).tolist()

    if VECTOR_DB.lower() == "chroma":
        collection = get_chroma_collection()
        results = collection.query(query_embeddings=[query_emb], n_results=top_k)
        return results
    else:
        return None

def generate_answer(query, top_k=5):
    results = retrieve(query, top_k=top_k)

    # ---- Handle empty results ----
    if not results or not results.get("documents"):
        prompt = f"""
You are a helpful shopping assistant.

The user asked: {query}

No matching products were found in the database.
Keep your answer short, like a salesperson talking to a customer, not an essay.
Please still respond naturally, suggest alternatives, or guide the user politely.
"""
        model = genai.GenerativeModel(llm_model)
        response = model.generate_content(prompt)
        return response.text.strip(), []

    # ---- Flatten docs + metadata ----
    docs = [doc for sublist in results["documents"] for doc in sublist]
    metas = [m for sublist in results["metadatas"] for m in sublist]

    # build readable chunks for the LLM
    chunks = []
    sources = []
    for i, (doc, meta) in enumerate(zip(docs, metas), start=1):
        title = meta.get("title") or meta.get("name") or "Product"
        price = meta.get("price", "N/A")
        url = meta.get("product_url", "")
        cats = meta.get("categories", "")
        avail = meta.get("availability", "")
        img = meta.get("images", "")

        desc = " ".join(doc.split())[:250]  # trim description
        chunks.append(f"{i}. {title} — {price}\n{desc}\nURL: {url}")

        sources.append({
            "title": title,
            "price": price,
            "product_url": url,
            "categories": cats,
            "availability": avail,
            "images": img
        })

    retrieved_chunks = "\n\n".join(chunks)

    # ---- Build prompt ----
    prompt = f"""
You are a helpful shopping assistant for an e-commerce store.

User asked: {query}

Here are some product descriptions from the store (with title, price, and URL):
{retrieved_chunks}

Answer naturally like a real assistant. 
- Mention product **names, prices, and include their URLs**.
- Suggest multiple matching products if possible.
- Keep the tone short, friendly, like a salesperson.
"""

    # ---- Call Gemini ----
    model = genai.GenerativeModel(llm_model)
    response = model.generate_content(prompt)

    return response.text.strip(), sources
