import streamlit as st
from openai import OpenAI
import PyPDF2  # best for simple text doc like the one we are going to use here


def extract_text_from_pdf(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ''
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text

def extract_text_from_txt(uploaded_file):
    """Extract text from a .txt file uploaded via Streamlit."""
    try:
        return uploaded_file.read().decode("utf-8")
    except UnicodeDecodeError:
        # fallback encoding
        return uploaded_file.read().decode("latin-1")

# Show title and description.
st.title("📄 HW1: Document question answering")
st.write(
    "Upload a document below and ask a question about it – GPT will answer! "
    "To use this app, you need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys). "
)

# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:

    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)

    # Let the user upload a file via `st.file_uploader`.
    uploaded_file = st.file_uploader("Upload a document (.txt or .pdf)", type=("txt", "pdf"))

    document = None  # if file removed, delete it from memory

    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        if file_extension == "txt":
            document = extract_text_from_txt(uploaded_file)
        elif file_extension == "pdf":
            document = extract_text_from_pdf(uploaded_file)
        else:
            st.error("Unsupported file type.")

    # Ask the user for a question via `st.text_area`.
    question = st.text_area(
        "Now ask a question about the document!",
        placeholder="Is the course hard?",
        disabled=not uploaded_file,
    )

    if document and question:
        models = [
            "gpt-3.5-turbo",
            "gpt-4.1",
            "gpt-5-chat-latest",
            "gpt-5-nano"
        ]

        for model in models:
            with st.expander(f"Answer using {model}", expanded=True):
                messages = [
                    {
                        "role": "user",
                        "content": f"Here's a document: {document}\n\n---\n\n{question}",
                    }
                ]
                try:
                    stream = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        stream=True,
                    )
                    st.write_stream(stream)
                except Exception as e:
                    st.error(f"Error with {model}: {e}")
