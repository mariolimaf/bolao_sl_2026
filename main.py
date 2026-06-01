import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Bolão Copa 2026", page_icon="⚽")

# --- 2. CONEXÃO COM O SUPABASE ---
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# --- 3. CONTROLE DE SESSÃO (Para manter logado) ---
if 'user' not in st.session_state:
    st.session_state.user = None

# --- 4. FUNÇÕES DE AUTENTICAÇÃO ---
def check_login(login_data: dict, user: str, password: str):
    df_login = pd.DataFrame(login_data.data)

    df_login_user = df_login[df_login["login"] == user]

    if df_login_user.empty:
        return False, "Usuário não encontrado."

    else:
        if df_login_user.iloc[0]["senha"] == password:
            return True, "Login bem sucedido."
        else:
            return False, "Senha incorreta."

def login(user, password):
    login_data = supabase.table("usuarios").select("id, login, senha").execute()

    result_login = check_login(login_data, user, password)

    if result_login[0]:
        st.session_state.user = user
        st.success("Login realizado com sucesso!")
        st.rerun() # Atualiza a página para tirar a tela de login
    
    else:
        st.error(f"Erro ao fazer login: {result_login[1]}")

def logout():
    st.session_state.user = None
    st.rerun()

# --- 5. INTERFACE DO USUÁRIO ---
if st.session_state.user is None:
    # TELA DE LOGIN
    st.title("⚽ Bolão da Copa - SL Tributos 2026")
    st.markdown("Faça login para deixar seus palpites!")
    
    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit_button = st.form_submit_button("Entrar")
        
        if submit_button:
            if usuario and password:
                login(usuario, password)
            else:
                st.warning("Por favor, preencha todos os campos.")
                
    st.markdown("---")
    # st.markdown("Ainda não tem conta? *[A funcionalidade de cadastro entraria aqui]*")

else:
    # TELA DO SISTEMA (PÓS-LOGIN)
    st.title("🏆 Bem-vindo ao Bolão!")
    st.write(f"Você está logado como: **{st.session_state.user}**")
    
    # Aqui entraria a sua dashboard com os jogos...
    
    if st.button("Sair"):
        logout()