import streamlit as st
from openai import OpenAI
import os
from PyPDF2 import PdfReader

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb

chromaDB_path = "./chromaDB_labs"
chroma_client = chromadb.PersistentClient(chromaDB_path)

st.title("Lab 4: Embeddings")

openAI_model = st.sidebar.selectbox("Which Model?", ("mini", "regular"))
if openAI_model == "mini":
    model_to_use = "gpt-4o-mini"
else:
    model_to_use = "gpt-4o"

if "client" not in st.session_state:
    api_key = st.secrets["openai_api_key"]
    st.session_state.openai_client = OpenAI(api_key=api_key)


def build_lab4_vectorDB(pdf_folder="./pdfs"):
    if "Lab4_vectorDB" in st.session_state:
        return

    collection = chroma_client.get_or_create_collection("Lab4Collection")

    # Go through PDFs in given folder
    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith(".pdf")]
    openai_client = st.session_state.openai_client

    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_folder, pdf_file)
        reader = PdfReader(pdf_path)

        # Extract text from PDF
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""

        # Create embedding
        response = openai_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        embedding = response.data[0].embedding

        # Add to collection
        collection.add(
            documents=[text],
            ids=[pdf_file],
            embeddings=[embedding],
            metadatas=[{"filename": pdf_file}]
        )

    st.session_state.Lab4_vectorDB = collection
    st.write("✅ VectorDB created and stored in session_state.")



if "Lab4_vectorDB" not in st.session_state:
    build_lab4_vectorDB("./pdfs")



col1, col2 = st.columns([1, 2])

with col1:
    topic = st.selectbox("Choose a topic", ("", "Text Mining", "GenAI"))

with col2:
    custom_query = st.text_input("...or type your own query")

submit = st.button("Submit")

retrieved_context = None  # global storage for chatbot

if submit:
    if not topic and not custom_query:
        st.warning("Please select a topic or enter a query.")
    else:
        query_text = custom_query if custom_query else topic
        openai_client = st.session_state.openai_client

        response = openai_client.embeddings.create(
            input=query_text,
            model="text-embedding-3-small"
        )
        query_embedding = response.data[0].embedding

        collection = st.session_state.Lab4_vectorDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )

        st.subheader(f"🔎 Results for: {query_text}")
        retrieved_context = ""
        for i in range(len(results['documents'][0])):
            doc_id = results['ids'][0][i]
            st.write(f"{i+1}. The following file/syllabus might be helpful: **{doc_id}**")
            retrieved_context += results['documents'][0][i] + "\n\n"

        # Save retrieved text for chatbot
        st.session_state["retrieved_context"] = retrieved_context


# chatbot

st.markdown("---")
st.subheader("💬 Chatbot (RAG-powered)")

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "system", "content": "You are a helpful assistant. Clearly indicate when you are using retrieved knowledge."},
        {"role": "assistant", "content": "Hi! Ask me anything about the PDFs or your topic."}
    ]

# Show chat history
for msg in st.session_state.chat_messages[1:]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User input
if user_input := st.chat_input("Ask your question..."):
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Build prompt with RAG context if available
    if "retrieved_context" in st.session_state:
        context = st.session_state.retrieved_context[:2000]  # limit length
        augmented_prompt = f"""
You are a helpful assistant. The user asked: {user_input}

Here is some relevant context retrieved from documents:
---
{context}
---

When answering:
1. Use the context above if it is relevant, and explicitly say "Based on the documents..." when you use it.
2. If the context does not help, answer using your own knowledge.
"""
    else:
        augmented_prompt = f"You are a helpful assistant. The user asked: {user_input}"

    # Call the LLM
    stream = st.session_state.openai_client.chat.completions.create(
        model="gpt-5-nano",
        messages=[{"role": "system", "content": augmented_prompt}],
        stream=True
    )

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        response = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            response += delta
            response_placeholder.markdown(response)

    st.session_state.chat_messages.append({"role": "assistant", "content": response})