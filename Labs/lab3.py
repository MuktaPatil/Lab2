import streamlit as st
from openai import OpenAI

st.title("Lab 3: Chatbot who remembers")
openAI_model = st.sidebar.selectbox("Which Model?", ("mini", "regular"))
if openAI_model == "mini":
    model_to_use = "gpt-4o-mini"
else:
    model_to_use = "gpt-4o"

# Create an OpenAI client
if "client" not in st.session_state:
    api_key = st.secrets["openai_api_key"]
    st.session_state.client = OpenAI(api_key=api_key)

# Initialize state
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": "You are a helpful assistant who explains things in a way a 10-year-old can understand."},
        {"role": "assistant", "content": "Hi! What do you want to know?"}
    ]
    st.session_state["awaiting_more_info"] = False

# Function: build limited context buffer
def build_limited_messages(buffer_size=20):
    # always include the system message
    base = [st.session_state["messages"][0]]
    # keep the last `buffer_size*2` messages (user+assistant pairs)
    base.extend(st.session_state["messages"][-(buffer_size*2):])
    return base

# Show the full conversation in the UI
for msg in st.session_state.messages[1:]:  # skip system for UI
    chat_msg = st.chat_message(msg["role"])
    chat_msg.write(msg["content"])

# Chat loop
if prompt := st.chat_input("Type here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client = st.session_state.client

    # Case 1: User answers yes/no for more info
    if st.session_state.awaiting_more_info:
        if prompt.strip().lower() in ["yes", "y", "sure", "ok"]:
            # Generate more detail
            messages_for_llm = build_limited_messages(20) + [
                {"role": "system", "content": "Give a longer, more detailed explanation that a 10-year-old can still understand."}
            ]
            stream = client.chat.completions.create(
                model=model_to_use,
                messages=messages_for_llm,
                stream=True
            )
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                response = ""
                for chunk in stream:
                    delta = chunk.choices[0].delta.content or ""
                    response += delta
                    response_placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

            # Ask again
            followup = "Do you want more info?"
            with st.chat_message("assistant"):
                st.write(followup)
            st.session_state.messages.append({"role": "assistant", "content": followup})

        elif prompt.strip().lower() in ["no", "n", "nah"]:
            followup = "Okay! What else can I help you with?"
            with st.chat_message("assistant"):
                st.write(followup)
            st.session_state.messages.append({"role": "assistant", "content": followup})
            st.session_state.awaiting_more_info = False
        else:
            followup = "Please answer with 'yes' or 'no'. Do you want more info?"
            with st.chat_message("assistant"):
                st.write(followup)
            st.session_state.messages.append({"role": "assistant", "content": followup})

    # Case 2: Normal Q&A
    else:
        messages_for_llm = build_limited_messages(20) + [
            {"role": "system", "content": "Answer the question in a way a 10-year-old can understand."}
        ]
        stream = client.chat.completions.create(
            model=model_to_use,
            messages=messages_for_llm,
            stream=True
        )
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            response = ""
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                response += delta
                response_placeholder.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

        # After first answer, offer "Do you want more info?"
        followup = "Do you want more info?"
        with st.chat_message("assistant"):
            st.write(followup)
        st.session_state.messages.append({"role": "assistant", "content": followup})
        st.session_state.awaiting_more_info = True