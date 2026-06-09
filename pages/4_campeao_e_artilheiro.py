from supabase import create_client, Client
import streamlit as st

from services.util import dict_jogadores

st.markdown("## 🏆 Palpites Especiais")
st.markdown(
    "Além dos resultados dos jogos, você pode registrar dois palpites especiais: "
    "qual seleção vai **levantar a taça** e quem será o **artilheiro da competição**. "
    "Esses palpites podem ser alterados a qualquer momento antes do início da Copa."
)
st.caption("Cada palpite correto valerá 12 Pontos conforme regulamento.")

selecoes = sorted(list(dict_jogadores.keys()))

user = st.session_state["user"]
user_id = st.session_state["user_id"]

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

def carregar_palpite_extra():
    resultado = (
        supabase
        .table("palpites_extras")
        .select("selecao_campea, artilheiro")
        .eq("usuario_id", user_id)
        .execute()
    )
    if resultado.data:
        return resultado.data[0]
    
    return None

if "palpite_extra_carregado" not in st.session_state:
    salvo = carregar_palpite_extra()
    if salvo:
        st.session_state["extra_selecao"] = salvo["selecao_campea"]
        st.session_state["extra_artilheiro"] = salvo["artilheiro"]

    st.session_state["palpite_extra_carregado"] = True

st.markdown("---")
st.markdown("## 🌍 Seleção Campeã")
# --- Selectbox seleção campeã ---
selecao_escolhida = st.selectbox(
        "-",
        options=[None]+selecoes,
        key="extra_selecao",
        format_func=lambda x: "— Escolha uma seleção —" if x is None else x,
        placeholder="— Escolha uma seleção —"
    )

st.markdown("---")

st.markdown("## ⚽ Artilheiro da Competição")

selecao_artilheiro = st.selectbox(
        "-",
        options=[None] + selecoes,
        key="extra_selecao_artilheiro",
        format_func=lambda x: "— 1️⃣ Escolha o País do Artilheiro —" if x is None else x,
        placeholder="— Escolha o País do Artilheiro —",
        label_visibility="collapsed"
    )

posicao_artilheiro = None
artilheiro = None

if selecao_artilheiro:
    posicoes = [pos for pos in list(dict_jogadores[selecao_artilheiro]) if pos != "Goleiros"]
    
    posicao_artilheiro = st.selectbox(
        "-",
        options=[None] + posicoes,
        key="extra_selecao_pos_artilheiro",
        format_func=lambda x: "— 2️⃣ Escolha a Posiçao do Jogador —" if x is None else x,
        placeholder="— Escolha a Posiçao do Jogador —",
        label_visibility="collapsed"
    )

if posicao_artilheiro:
    artilheiros = list(dict_jogadores[selecao_artilheiro][posicao_artilheiro])

    artilheiro = st.selectbox(
        "-",
        options=[None] + artilheiros,
        key="extra_artilheiro",
        format_func=lambda x: "— 3️⃣ Escolha o Jogador Artilheiro —" if x is None else x,
        placeholder="— Escolha o Jogador Artilheiro —",
        label_visibility="collapsed"
    )

palpites_salvos = st.session_state.get("palpites_extras_salvos")

if palpites_salvos:
    st.caption(
        f"✅ Palpite enviado: "
        f"**{palpites_salvos['selecao_campea']}** como campeã · "
        f"**{palpites_salvos['artilheiro']}** como artilheiro"
    )
else:
    st.caption("⏳ Nenhum palpite especial enviado ainda.")

if st.button("💾 Salvar Palpites Especiais", use_container_width=True):
    selecao = st.session_state.get("extra_selecao")
    art = st.session_state.get("extra_artilheiro")

    if not selecao:
        st.warning("Escolha uma seleção campeã antes de salvar.")
    elif not art:
        st.warning("Complete a escolha do artilheiro antes de salvar.")
    else:
        try:
            supabase.table("palpites_extras").upsert(
                {
                    "usuario_id": int(user_id),
                    "selecao_campea": selecao,
                    "artilheiro": art,
                },
                on_conflict="usuario_id"
            ).execute()

            st.session_state["palpites_extras_salvos"] = {
                "selecao_campea": selecao,
                "artilheiro": art
            }
            st.toast("Palpites especiais salvos com sucesso! ✅")

        except Exception as e:
            st.error(f"Erro ao salvar: {e}")