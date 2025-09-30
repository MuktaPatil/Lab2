import streamlit as st
import os
from bs4 import BeautifulSoup

import pysqlite3
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from openai import OpenAI
import anthropic
import google.generativeai as genai


# Initialize clients
if "openai_client" not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["openai_api_key"])
if "anthropic_client" not in st.session_state:
    st.session_state.anthropic_client = anthropic.Anthropic(api_key=st.secrets["claude_api_key"])
if "gemini_client" not in st.session_state:
    genai.configure(api_key=st.secrets["gemini_api_key"])
    st.session_state.gemini_client = genai.GenerativeModel("gemini-2.5-pro")


chromaDB_path = "./chromaDB_hw4"
chroma_client = chromadb.PersistentClient(path=chromaDB_path)
collection = chroma_client.get_or_create_collection("HW4Collection")


def load_html_texts(folder="./su_orgs"):
    docs = []
    for fname in os.listdir(folder):
        if fname.endswith(".html"):
            with open(os.path.join(folder, fname), "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
                text = soup.get_text(separator=" ", strip=True)
                docs.append((fname, text))
    return docs


def chunk_document(text, chunks=2):
    midpoint = len(text) // 2
    return [text[:midpoint], text[midpoint:]]


def build_vectorDB():
    if collection.count() > 0:
        return
    docs = load_html_texts("./su_orgs")
    openai_client = st.session_state.openai_client
    for fname, text in docs:
        parts = chunk_document(text)
        for i, part in enumerate(parts):
            if not part.strip():
                continue
            resp = openai_client.embeddings.create(
                input=part, model="text-embedding-3-small"
            )
            embedding = resp.data[0].embedding
            collection.add(
                documents=[part],
                ids=[f"{fname}_chunk{i}"],
                metadatas=[{"filename": fname, "chunk": i}],
                embeddings=[embedding],
            )
    st.write("VectorDB created with HTML documents.")


build_vectorDB()


# Short-term memory (last 10 messages)
if "messages" not in st.session_state:
    st.session_state.messages = []


def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})
    if len(st.session_state.messages) > 10:
        st.session_state.messages = st.session_state.messages[-10:]


# 🔑 Step 1: Define vector search function
def get_relevant_info(query, top_k=3):
    openai_client = st.session_state.openai_client
    resp = openai_client.embeddings.create(
        input=query, model="text-embedding-3-small"
    )
    query_embedding = resp.data[0].embedding

    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    retrieved_docs = results["documents"][0]
    retrieved_meta = results["metadatas"][0]

    context_text = ""
    for doc, meta in zip(retrieved_docs, retrieved_meta):
        context_text += f"[{meta['filename']} - chunk {meta['chunk']}]\n{doc}\n\n"
    return context_text


# Streamlit UI
st.title("HW5: Intelligent iSchool Student Orgs. Chatbot")

model_choice = st.sidebar.selectbox(
    "Select LLM",
    ("gpt-5-nano", "gemini-2.5-pro", "claude-opus-4-1-20250805")
)

st.subheader("Chat with the Bot")
query = st.chat_input("Ask me about iSchool student organizations...")


if query:
    add_message("user", query)

    # 🔑 Step 2: Retrieve relevant info
    context_text = get_relevant_info(query)

    # 🔑 Step 3: Send both context + conversation history to LLM
    system_prompt = f"You are a helpful assistant for iSchool student organizations.\n\nHere is some context that might help:\n{context_text}\n\nAlways ground your answers in this info if relevant."

    if model_choice == "gpt-5-nano":
        completion = st.session_state.openai_client.chat.completions.create(
            model="gpt-5-nano",
            messages=[{"role": "system", "content": system_prompt}] + st.session_state.messages,
        )
        answer = completion.choices[0].message.content

    elif model_choice == "claude-opus-4-1-20250805":
        completion = st.session_state.anthropic_client.messages.create(
            model="claude-opus-4-1-20250805",
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": query}],
        )
        answer = completion.content[0].text

    elif model_choice == "gemini-2.5-pro":
        completion = st.session_state.gemini_client.generate_content(
            system_prompt + "\n\n" + query
        )
        answer = completion.text

    else:
        answer = "Unsupported model."

    add_message("assistant", answer)


# Render conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
