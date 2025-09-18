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
collection = chroma_client.get_or_create_collection("Lab4Collection")


st.title("Lab 4: Embeddings")
openAI_model = st.sidebar.selectbox("Which Model?", ("mini", "regular"))
if openAI_model == "mini":
    model_to_use = "gpt-4o-mini"
else:
    model_to_use = "gpt-4o"

# Create an OpenAI client
if "client" not in st.session_state:
    api_key = st.secrets["openai_api_key"]
    st.session_state.openai_client = OpenAI(api_key=api_key)

# Initialize state
def build_lab4_vectorDB(pdf_folder="./pdfs"):
    if "Lab4_vectorDB" in st.session_state:
        return

    # Create or get collection
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

    # Save collection to session_state
    st.session_state.Lab4_vectorDB = collection
    st.write("✅ VectorDB created and stored in session_state.")

if "Lab4_vectorDB" not in st.session_state:
    build_lab4_vectorDB("./pdfs")  # change path if your PDFs are elsewhere



topic = st.sidebar.selectbox("Topic", ("Text Mining", "GenAI"))

if "Lab4_vectorDB" in st.session_state:
    openai_client = st.session_state.openai_client

    # Get embedding for the chosen topic
    response = openai_client.embeddings.create(
        input=topic,
        model="text-embedding-3-small"
    )
    query_embedding = response.data[0].embedding

    # Search the vector DB
    collection = st.session_state.Lab4_vectorDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3  # top 3 closest docs
    )

    # Show results
    for i in range(len(results['documents'][0])):
        doc_id = results['ids'][0][i]
        st.write(f"The following file/syllabus might be helpful: {doc_id}")