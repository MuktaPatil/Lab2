import streamlit as st

st.set_page_config(
    page_title="Lab 2",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("🎈 Multipage navigation")

hw_1 = st.Page("hw1_streamlit_app.py", title="Homework 1", icon=":material/book_2:")
hw_2 = st.Page("hw2_streamlit_app copy.py", title="Lab 2", icon=":material/book_2:")

pg = st.navigation([hw_1, hw_2])
st.set_page_config(page_title="Data manager", page_icon=":material/edit:")
pg.run()

