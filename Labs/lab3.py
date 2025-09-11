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

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

# Show the full conversation in the UI
for msg in st.session_state.messages:
    chat_msg = st.chat_message(msg["role"])
    chat_msg.write(msg["content"])

if prompt := st.chat_input("What is up?"):
    # Add user message to full history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Conversation buffer size (number of user turns to remember)
    buffer_size = 2

    # Build limited memory for the model
    limited_messages = [st.session_state["messages"][0]]  # always include the very first assistant/system
    user_turns = []
    for i, m in enumerate(st.session_state.messages):
        if m["role"] == "user":
            # collect this user message 
            turn = [m]
            if i + 1 < len(st.session_state.messages) and st.session_state.messages[i + 1]["role"] == "assistant":
                turn.append(st.session_state.messages[i + 1])
            user_turns.append(turn)

    # Flatten only the last `buffer_size` user turns into the memory
    for turn in user_turns[-buffer_size:]:
        limited_messages.extend(turn)

    # Call the model with trimmed memory
    client = st.session_state.client
    stream = client.chat.completions.create(
        model=model_to_use,
        messages=limited_messages,
        stream=True,
    )

    with st.chat_message("assistant"):
        response = st.write_stream(stream)

    # Save assistant response to the full history
    st.session_state.messages.append({"role": "assistant", "content": response})
