import streamlit as st

st.set_page_config(
    page_title="Lab 2",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("Homework Directory")

widget =  st.sidebar.radio("Summary options", ["Summarize the document in 100 words","Summarize the document in 2 connecting paragraphs","Summarize the document in 5 bullet points."])

st.session_state['instruction'] = widget

st.sidebar.write("Advanced Options")

if st.sidebar.checkbox("Use Advanced Model"):
    #use 4o
    st.session_state['model'] = "gpt-4o"
else:
    st.session_state['model'] = "gpt-4o-mini"


hw_1 = st.Page("hw1.py", title="Homework 1", icon=":material/book_2:")
hw_2 = st.Page("hw2_streamlit_app.py", title="Homework 2", icon=":material/book_2:")

pg = st.navigation([hw_1, hw_2])
st.set_page_config(page_title="Data manager", page_icon=":material/edit:")
pg.run()

