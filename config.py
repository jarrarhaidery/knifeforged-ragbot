# config.py
# Put secrets in ENV variables in production. This file reads env vars and provides defaults.

import os

# Scraper
WP_SITE = os.getenv("WP_SITE", "https://knifeforged.shop")  # change to your store base URL

# Embeddings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Vector DB choice: "chroma" or "faiss"
VECTOR_DB = os.getenv("VECTOR_DB", "chroma")

# Chroma persistence folder
CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "./chroma_db")

# FAISS persistence folder
FAISS_DIR = os.getenv("FAISS_DIR", "./faiss_index")

# LLM choice: "gemini" or "openai"
LLM_BACKEND = os.getenv("LLM_BACKEND", "gemini")

# Gemini / Google Generative AI key (if using Gemini)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", None)

# OpenAI fallback
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)

# Retrieval parameters
TOP_K = int(os.getenv("TOP_K", "5"))

# Other
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))  # if you decide to chunk descriptions later
