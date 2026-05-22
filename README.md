# 🔪 KnifeForged RAG Chatbot

An intelligent, context-aware product assistant for an e-commerce knife store — built with a full RAG pipeline that fetches live inventory from WordPress and delivers accurate product Q&A with near-zero hallucination.

---

## 🚀 What It Does

- Answers customer questions about products, availability, pricing, and specs in natural language
- Pulls **live inventory data** directly from the WordPress REST API — always up to date
- Uses **FAISS vector search** to retrieve the most relevant product context before generating a response
- Powered by **Gemini API** for response generation with a grounded, retrieval-first approach
- Deployed via **Streamlit** for a clean, interactive chat interface

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| LLM | Gemini API |
| RAG Framework | LangChain |
| Vector Store | FAISS, ChromaDB |
| Data Source | WordPress REST API |
| Embedding | LangChain Embeddings |
| Frontend | Streamlit |
| Backend | Python |

---

## 📁 Project Structure

```
knifeforged-ragbot/
├── app.py          # Streamlit chat interface
├── bot.py          # Core RAG pipeline & response logic
├── config.py       # API keys and configuration
├── embed.py        # Embedding generation & vector store setup
├── fetch_wp.py     # WordPress REST API data fetcher
├── scraper.py      # Product data scraper
└── requirements.txt
```

---

## ⚙️ Setup & Installation

```bash
# 1. Clone the repository
git clone https://github.com/jarrarhaidery/knifeforged-ragbot.git
cd knifeforged-ragbot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Add your GEMINI_API_KEY and WordPress site URL to .env

# 4. Embed the product data
python embed.py

# 5. Run the chatbot
streamlit run app.py
```

---

## 💡 How It Works

1. **Data Ingestion** — `fetch_wp.py` pulls product data from the WordPress REST API
2. **Embedding** — `embed.py` converts product data into vector embeddings stored in FAISS/ChromaDB
3. **Retrieval** — On each user query, the most relevant product chunks are retrieved via similarity search
4. **Generation** — Retrieved context is passed to Gemini API to generate a grounded, accurate response
5. **Interface** — `app.py` serves the whole pipeline through a Streamlit chat UI

---

## 📌 Topics

`langchain` `rag` `gemini-api` `faiss` `chromadb` `chatbot` `llm` `e-commerce` `wordpress` `streamlit` `python` `generative-ai`
