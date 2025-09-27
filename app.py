# app.py
import streamlit as st
import os
from config import CHROMA_DB_DIR, FAISS_DIR, VECTOR_DB, EMBEDDING_MODEL
from bot import generate_answer
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="Shop RAG Chatbot", layout="centered")

st.title("🛍️ Shop Assistant (RAG)")

def check_index():
    if VECTOR_DB.lower() == "chroma":
        return os.path.exists(CHROMA_DB_DIR) and any(os.scandir(CHROMA_DB_DIR))
    else:
        return os.path.exists(os.path.join(FAISS_DIR, "index.faiss"))

if not check_index():
    st.warning("Vector DB not found. Run `scraper.py` then `embed.py` before using the chat. See README.")
    st.stop()

# chat history stored in session state
if "history" not in st.session_state:
    st.session_state.history = []

st.write("Ask about products (examples: 'Show me products under $150', 'Do you have D2 Steel Knives?')")

user_input = st.text_input("Your question", key="user_input")
if st.button("Ask") or (user_input and st.session_state.get("last_query") != user_input):
    if not user_input.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Retrieving relevant products and generating answer..."):
            try:
                answer, docs = generate_answer(user_input)

                # Extract product metadata
                sources_meta = []
                for d in docs:
                    if hasattr(d, "metadata"):
                        sources_meta.append({
                            "title": d.metadata.get("title", "Product"),
                            "price": d.metadata.get("price", "N/A"),
                            "url": d.metadata.get("product_url", ""),
                            "image": d.metadata.get("images", "").split(",")[0]
                        })

            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

        st.session_state.history.append({
            "q": user_input,
            "a": answer,
            "sources": sources_meta
        })
        st.session_state.last_query = user_input

# Display last 10 conversation turns
for item in reversed(st.session_state.history[-10:]):
    st.markdown(f"**🧑 You:** {item['q']}")
    st.markdown(f"**🤖 Assistant:** {item['a']}")

    if item.get("sources"):
        st.subheader("✨ Matched Products:")

        cols = st.columns(3)  # 3 products per row
        for i, src in enumerate(item["sources"]):
            title = src.get("title", "Product")
            price = src.get("price", "N/A")
            url = src.get("product_url", "")
            img = (src.get("images") or "").split(",")[0]

            with cols[i % 3]:
                st.markdown(f"""
                <div style="border:1px solid #ddd; padding:10px; 
                            margin:10px 0; border-radius:12px; 
                            box-shadow:2px 2px 8px rgba(0,0,0,0.1);
                            text-align:center;">
                    <img src="{img}" width="160" style="border-radius:10px;"><br>
                    <b>{title}</b><br>
                    💲{price}<br>
                    <a href="{url}" target="_blank">
                        <button style="margin-top:5px; padding:5px 10px; 
                                       background:#007bff; color:white; 
                                       border:none; border-radius:5px; 
                                       cursor:pointer;">🔗 View Product</button>
                    </a>
                </div>
                """, unsafe_allow_html=True)







