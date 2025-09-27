import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL, CHROMA_DB_DIR, FAISS_DIR, VECTOR_DB
from tqdm import tqdm

DATA_FILE = "data/products.json"
BATCH_SIZE = 50  # process products in batches

os.makedirs(CHROMA_DB_DIR, exist_ok=True)
os.makedirs(FAISS_DIR, exist_ok=True)


# ----------------- Helpers -----------------
def safe_str(v):
    """Ensure everything is a string (avoid NoneType errors)."""
    return str(v) if v is not None else ""


def clean_categories(cats):
    if isinstance(cats, list):
        out = []
        for c in cats:
            if isinstance(c, dict):
                out.append(safe_str(c.get("name")))
            else:
                out.append(safe_str(c))
        return ", ".join([c for c in out if c])
    return safe_str(cats)


def clean_list_of_dicts(field, key="src"):
    """Turn list of dicts into a comma-separated string of values by key"""
    if isinstance(field, list):
        out = []
        for item in field:
            if isinstance(item, dict):
                out.append(safe_str(item.get(key)))
            else:
                out.append(safe_str(item))
        return ", ".join([x for x in out if x])
    return safe_str(field)


# ----------------- Core funcs -----------------
def load_products(path=DATA_FILE):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def make_text(product):
    parts = [safe_str(product.get("title"))]
    desc = product.get("description", "")
    if desc:
        parts.append(safe_str(desc))

    cats = product.get("categories")
    if cats:
        parts.append("Categories: " + clean_categories(cats))

    return "\n".join(parts)


def build_embeddings(products, model_name=EMBEDDING_MODEL):
    print("Loading embedding model:", model_name)
    model = SentenceTransformer(model_name)

    texts = [make_text(p) for p in products]
    embeddings = []

    for i in tqdm(range(0, len(texts), BATCH_SIZE), desc="Encoding batches"):
        batch_texts = texts[i:i + BATCH_SIZE]
        batch_embs = model.encode(
            batch_texts, show_progress_bar=False, convert_to_numpy=True
        )
        embeddings.append(batch_embs)

    embeddings = np.vstack(embeddings)
    return embeddings, texts


# ----------------- Save to Chroma -----------------
def save_chroma(products, embeddings, texts):
    import chromadb

    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
    collection_name = "products"

    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass

    col = client.create_collection(
        name=collection_name, metadata={"source": "woocommerce-scrape"}
    )

    ids = [f"prod_{i}" for i in range(len(products))]
    metadatas = []
    for p in products:
        meta = {
            "title": safe_str(p.get("title")),
            "price": safe_str(p.get("price")),
            "product_url": safe_str(p.get("product_url")),
            "images": clean_list_of_dicts(p.get("images"), key="src"),
            "availability": safe_str(p.get("availability")),
            "categories": clean_categories(p.get("categories")),
        }
        metadatas.append(meta)

    # Insert in batches
    for i in tqdm(range(0, len(products), BATCH_SIZE), desc="Saving to Chroma"):
        batch_ids = ids[i:i + BATCH_SIZE]
        batch_metas = metadatas[i:i + BATCH_SIZE]
        batch_texts = texts[i:i + BATCH_SIZE]
        batch_embs = embeddings[i:i + BATCH_SIZE]

        col.add(
            ids=batch_ids,
            metadatas=batch_metas,
            documents=batch_texts,
            embeddings=batch_embs.tolist(),
        )

    print(f"✅ Saved {len(products)} items to Chroma at {CHROMA_DB_DIR}")


# ----------------- Save to FAISS -----------------
def save_faiss(products, embeddings):
    import faiss

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings.astype(np.float32))
    faiss.write_index(index, os.path.join(FAISS_DIR, "index.faiss"))

    metas = []
    for p in products:
        metas.append({
            "title": safe_str(p.get("title")),
            "price": safe_str(p.get("price")),
            "product_url": safe_str(p.get("product_url")),
            "images": clean_list_of_dicts(p.get("images"), key="src"),
            "categories": clean_categories(p.get("categories")),
            "availability": safe_str(p.get("availability")),
            "description": safe_str(p.get("description")),
        })
    with open(os.path.join(FAISS_DIR, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metas, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved FAISS index and metadata to {FAISS_DIR}")


# ----------------- Main -----------------
def main():
    products = load_products()
    if not products:
        print("⚠️ No products found in data/products.json. Run fetch_wp.py first.")
        return

    embeddings, texts = build_embeddings(products)

    if VECTOR_DB.lower() == "chroma":
        save_chroma(products, embeddings, texts)
    elif VECTOR_DB.lower() == "faiss":
        save_faiss(products, embeddings)
    else:
        print("⚠️ Unknown VECTOR_DB:", VECTOR_DB)
        save_chroma(products, embeddings, texts)
        save_faiss(products, embeddings)


if __name__ == "__main__":
    main()
