import streamlit as st

st.set_page_config(
    page_title="Lab 2",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("Homework Directory")



hw_1 = st.Page("Homeworks/hw1.py", title="Homework 1", icon=":material/book_2:")
hw_2 = st.Page("Homeworks/hw2_streamlit_app.py", title="Homework 2", icon=":material/book_2:")
hw_3 = st.Page("Homeworks/hw_3.py", title="Homework 3", icon=":material/book_2:")

lab_1 = st.Page("Labs/lab1.py", title="Lab 1", icon=":material/book_2:")
lab_2 = st.Page("Labs/lab2.py", title="Lab 2", icon=":material/book_2:")
lab_3 = st.Page("Labs/lab3.py", title="Lab 3", icon=":material/book_2:")
lab_4= st.Page("Labs/lab4.py", title="Lab 4", icon=":material/book_2:")

pg = st.navigation([hw_1, hw_2,hw_3, lab_1, lab_2, lab_3, lab_4])
st.set_page_config(page_title="Data manager", page_icon=":material/edit:")
pg.run()

