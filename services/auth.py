import streamlit as st

def verificar_login():
    if not st.session_state.get("logado", False):
        st.switch_page("app.py")
        st.stop()