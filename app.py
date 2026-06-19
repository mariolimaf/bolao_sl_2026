from supabase import create_client
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Bolão SL - Copa 2026",
    page_icon="⚽",
    layout="wide",
)
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

if "logado" not in st.session_state:
    st.session_state.logado = False

if "user_id" not in st.session_state:
    st.session_state.usuario = None

if "user" not in st.session_state:
    st.session_state.user = None

def check_login(login_data: dict, user: str, password: str):
    df_login = pd.DataFrame(login_data.data)
    df_login_user = df_login[df_login["login"] == user]

    if df_login_user.empty:
        return False, "Usuário não encontrado.", None, None, None

    if df_login_user.iloc[0]["senha_hash"] != password:
        return False, "Senha incorreta.", None, None, None

    # if user == "mariolimaf":
    #     return False, "Acesso revogado temporariamente após deliberação unânime da equipe responsável.", None, None, None
    
    user_id = df_login_user.iloc[0]["id"]
    user_name = df_login_user.iloc[0]["nome"]
    user_adm = df_login_user.iloc[0]["admin"]

    return True, "Login bem sucedido.", user_id, user_name, user_adm

def login(user: str, password: str) -> bool:
    login_data = supabase.table("usuarios").select("id, login, senha_hash, nome, admin").execute()
    result_login, message, user_id, user_name, user_adm = check_login(login_data, user, password)

    if not result_login:
        st.error(f"Erro ao fazer login: {message}")
        return False

    st.session_state.logado = True
    st.session_state.user_id = user_id
    st.session_state.user = user
    st.session_state.user_name = user_name
    st.session_state.user_adm = user_adm
    return True

def logout():
    st.session_state.logado = False
    st.session_state.user_id = None
    st.session_state.user = None
    st.session_state.user_name = None
    st.session_state.user_adm = None
    st.session_state.pop("jogos_modificados", None)
    st.session_state.pop("palpites_salvos", None)
    st.rerun()

def tela_login():
    _, col2, _ = st.columns([1, 2, 1])

    with col2:
        st.title("⚽ Bolão SL - Copa 2026")
        st.markdown("Faça login para deixar seus palpites!")

        with st.form("login_form"): #, width="content"
            usuario = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submit_button = st.form_submit_button("Entrar")

            if submit_button:
                if not usuario or not password:
                    st.warning("Por favor, preencha todos os campos.")
                    return

                if login(usuario, password):
                    st.success("Login realizado com sucesso!")
                    st.rerun()

        st.markdown("---")
        st.markdown("Ainda não tem conta? *Fale com o adm para cadastro*")

if st.session_state.logado:
    pages = [
        st.Page("pages/1_palpites.py", title="Palpites", default=True),
        st.Page("pages/2_regras.py", title="Regras"),
        st.Page("pages/3_ranking.py", title="Classificação"),
        st.Page("pages/4_campeao_e_artilheiro.py", title="Campeão e Artilheiro"),
        # st.Page("pages/regras.py", title="Regras", icon="📖"),
    ]

    # if st.session_state.user_adm:
    #     pages.append(st.Page("pages/4_campeao_e_artilheiro.py", title="Campeão e Artilheiro"))

    with st.sidebar:
        st.write(f"👤 {st.session_state.user}")

        if st.button("Sair"):
            logout()
else:
    pages = [
        st.Page(tela_login, title="Login", icon="🔐", default=True),
    ]

pg = st.navigation(pages)
pg.run()
