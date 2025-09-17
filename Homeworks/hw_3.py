import streamlit as st
import requests
from bs4 import BeautifulSoup

# LLM clients
from openai import OpenAI
import anthropic
import google.generativeai as genai


# Init session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# 🔥 FIX: make sure awaiting_more exists before we use it
if "awaiting_more" not in st.session_state:
    st.session_state.awaiting_more = False

# Helper: Fetch URL text
def fetch_url_text(url):
    if not url:
        return ""
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        return f"Error fetching {url}: {e}"

def convert_to_gemini_history(messages):
    gemini_messages = []
    for m in messages:
        gemini_messages.append({
            "role": m["role"],  # must be "user" or "model"
            "parts": [{"text": m["content"]}]
        })
    return gemini_messages


# Helper: Memory handling
def apply_memory(messages, memory_type):
    if memory_type.startswith("Buffer of"):
        return messages[-12:]  # 6 Q&A pairs
    elif memory_type == "Summary":
        # For demo: simple placeholder summary
        return [{"role": "system", "content": "Summary of past conversation so far."}] + messages[-2:]
    elif memory_type.startswith("Long buffer"):
        return messages[-2000:]
    return messages


# Helper: Get LLM Response (stream)
def get_llm_stream(vendor, model, messages, source_text):
    # Grab the last user question
    last_user_msg = messages[-1]["content"] if messages else ""
    
    # Combine question + context
    combined_prompt = (
        f"User question: {last_user_msg}\n\n"
        f"Reference context:\n{source_text}\n\n"
        f"Please answer the user’s question directly and simply, using the context when useful."
    )

    if vendor == "OpenAI":
        client = OpenAI(api_key=st.secrets["openai_api_key"])
        return client.chat.completions.create(
            model=model,
            messages=messages[:-1] + [{"role": "user", "content": combined_prompt}],
            stream=True
        )

    elif vendor == "Anthropic":
        client = anthropic.Anthropic(api_key=st.secrets["claude_api_key"])
        return client.messages.stream(
            model=model,
            max_tokens=500,
            messages=messages[:-1] + [{"role": "user", "content": combined_prompt}],
        )

    elif vendor == "Gemini":
        genai.configure(api_key=st.secrets["gemini_api_key"])
        model_obj = genai.GenerativeModel(model)
        return model_obj.generate_content(
            [combined_prompt],
            stream=True,
            generation_config={"temperature": 0.7},
        )

    else:
        raise ValueError("Unsupported vendor")


# Streamlit UI
st.title("📄 HW3 – URL Chatbot")

st.sidebar.header("Chatbot Options")

# URLs
url1 = st.sidebar.text_input("URL 1", value="https://www.howbaseballworks.com/TheBasics.htm")
url2 = st.sidebar.text_input("URL 2", value="https://www.pbs.org/kenburns/baseball/baseball-for-beginners")

# Vendors/models
vendor = st.sidebar.selectbox("Select LLM Vendor", ["OpenAI", "Anthropic", "Gemini"])
if vendor == "OpenAI":
    model = st.sidebar.selectbox("Model", ["gpt-4o"])
elif vendor == "Anthropic":
    model = st.sidebar.selectbox("Model", ["claude-opus-4-1-20250805"])
elif vendor == "Gemini":
    model = st.sidebar.selectbox("Model", ["gemini-2.5-pro"])
else:
    model = None

# Memory options
memory_type = st.sidebar.selectbox(
    "Conversation Memory",
    ["Buffer of 6 questions", "Summary", "Long buffer of 2000 tokens"]
)

# Fetch docs
doc1 = fetch_url_text(url1)
doc2 = fetch_url_text(url2)
source_text = doc1 + "\n\n" + doc2 if url2 else doc1

# Init messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past chat
for msg in st.session_state.messages:
    chat_msg = st.chat_message(msg["role"])
    chat_msg.write(msg["content"])

# Chat input
if prompt := st.chat_input("Enter your questions..."):
    # ---- NEW BLOCK: handle follow-up answers ----
    if st.session_state.awaiting_more:
        if prompt.strip().lower() in ["yes", "y"]:
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                response = ""

                try:
                    # Create a "more detail" prompt
                    combined_prompt = (
                        f"Earlier answer: {st.session_state.messages[-1]['content']}\n\n"
                        f"User asked for more detail. Expand the explanation with richer details from the reference context.\n\n"
                        f"Reference context:\n{source_text}"
                    )

                    # ✅ FIX: mark this as a user message, not assistant
                    stream = get_llm_stream(
                        vendor,
                        model,
                        apply_memory(st.session_state.messages, memory_type)
                        + [{"role": "user", "content": combined_prompt}],
                        source_text
                    )

                    if vendor == "OpenAI":
                        for chunk in stream:
                            delta = chunk.choices[0].delta.content or ""
                            response += delta
                            response_placeholder.markdown(response)

                    elif vendor == "Anthropic":
                        with stream as s:
                            for event in s:
                                if event.type == "content_block_delta":
                                    delta = getattr(event.delta, "text", "")
                                    response += delta
                                    response_placeholder.markdown(response)
                                elif event.type == "message_stop":
                                    break

                    elif vendor == "Gemini":
                        for chunk in stream:
                            # Gemini chunks may have parts or candidates instead of raw text
                            if hasattr(chunk, "text") and chunk.text:
                                response += chunk.text
                                response_placeholder.markdown(response)
                            elif hasattr(chunk, "candidates"):
                                for cand in chunk.candidates:
                                    if hasattr(cand, "content") and cand.content.parts:
                                        for part in cand.content.parts:
                                            if hasattr(part, "text") and part.text:
                                                response += part.text
                                                response_placeholder.markdown(response)

                except Exception as e:
                    response = f"Error: {e}"
                    response_placeholder.markdown(response)

            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.awaiting_more = False  # reset


        elif prompt.strip().lower() in ["no", "n"]:
            st.session_state.awaiting_more = False
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                st.markdown("Okay, I’ll wait for your next question.")
            st.session_state.messages.append({"role": "assistant", "content": "Okay, I’ll wait for your next question."})
        else:
            # Normal flow resumes if input not yes/no
            st.session_state.awaiting_more = False
            st.session_state.messages.append({"role": "user", "content": prompt})

    else:
        # ---- NORMAL CHAT FLOW ----
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            response = ""

            try:
                stream = get_llm_stream(
                    vendor,
                    model,
                    apply_memory(st.session_state.messages, memory_type),
                    source_text
                )

                if vendor == "OpenAI":
                    for chunk in stream:
                        delta = chunk.choices[0].delta.content or ""
                        response += delta
                        response_placeholder.markdown(response)

                elif vendor == "Anthropic":
                    with stream as s:
                        for event in s:
                            if event.type == "content_block_delta":
                                delta = getattr(event.delta, "text", "")
                                response += delta
                                response_placeholder.markdown(response)
                            elif event.type == "message_stop":
                                break

                elif vendor == "Gemini":
                    for chunk in stream:
                        for text in chunk.text:
                            response += text
                            response_placeholder.markdown(response)

            except Exception as e:
                response = f"Error: {e}"
                response_placeholder.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

        # ---- NEW: add "Would you like to know more?" ----
        with st.chat_message("assistant"):
            st.markdown("Would you like to know more?")
        st.session_state.messages.append({"role": "assistant", "content": "Would you like to know more?"})
        st.session_state.awaiting_more = True