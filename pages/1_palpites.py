from supabase import create_client, Client
from datetime import datetime
import streamlit as st
import pandas as pd

from services.auth import verificar_login
from services.util import dict_pais_bandeira, dias

verificar_login()

def calcular_pontos(
        real1,
        real2,
        palpite1,
        palpite2
    ):

    # placar exato
    if real1 == palpite1 and real2 == palpite2:
        return 5

    vencedor_real = (
        1 if real1 > real2
        else 2 if real2 > real1
        else 0
    )

    vencedor_palpite = (
        1 if palpite1 > palpite2
        else 2 if palpite2 > palpite1
        else 0
    )

    if vencedor_real == vencedor_palpite:
        return 3

    return 0

def marcar_modificado(jogo_id):
    st.session_state.setdefault("jogos_modificados", set()).add(jogo_id)

def carregar_palpites_existentes(user_id: int, jogos: list):
    """Busca palpites salvos e popula o session_state antes de renderizar os widgets."""
    
    # Evita recarregar a cada rerun desnecessário
    if st.session_state.get("palpites_carregados"):
        return

    jogo_ids = [jogo["id"] for jogo in jogos]

    resultado = (
        supabase
        .table("palpites")
        .select("jogo_id, palpite_time1, palpite_time2")
        .eq("usuario_id", user_id)
        .in_("jogo_id", jogo_ids)
        .execute()
    )

    palpites_salvos = {}
    for p in resultado.data:
        jogo_id = p["jogo_id"]
        st.session_state[f"casa_{jogo_id}"] = p["palpite_time1"]
        st.session_state[f"fora_{jogo_id}"] = p["palpite_time2"]
        palpites_salvos[jogo_id] = {
            "palpite_time1": p["palpite_time1"],
            "palpite_time2": p["palpite_time2"]
        }

    st.session_state["palpites_salvos"] = palpites_salvos
    st.session_state["palpites_carregados"] = True

def salvar_palpites(user_id: int, jogos: list[pd.Series]):
    jogos_modificados = st.session_state.get("jogos_modificados", set())

    if not jogos_modificados:
        st.toast("Nenhum palpite novo para salvar.", icon="ℹ️")
        return
    
    palpites = []

    for jogo in jogos:

        jogo_id = jogo["id"]

        if jogo_id not in jogos_modificados:  # ✅ pula os não alterados
            continue

        p1 = st.session_state.get(f"casa_{jogo_id}")
        p2 = st.session_state.get(f"fora_{jogo_id}")

        if p1 is None or p2 is None:
            continue
        
        palpites.append({
            "usuario_id": int(user_id),
            "jogo_id": int(jogo_id),
            "palpite_time1": p1,
            "palpite_time2": p2
        })

    try:
        (
            supabase
            .table("palpites")
            .upsert(palpites, on_conflict="usuario_id,jogo_id")
            .execute()
        )
        # st.session_state.pop("palpites_carregados", None)
        # st.toast("Palpites salvos com sucesso! ✅")
        # st.session_state["ultimo_salvamento"] = datetime.now()

        for p in palpites:
            st.session_state.setdefault("palpites_salvos", {})[p["jogo_id"]] = {
                "palpite_time1": p["palpite_time1"],
                "palpite_time2": p["palpite_time2"]
            }
        st.session_state["jogos_modificados"] = set()
        st.toast(f"{len(palpites)} palpite(s) salvo(s) com sucesso! ✅")

    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

user = st.session_state["user"]
user_id = st.session_state["user_id"]

supabase = create_client(url, key)
jogos = supabase.table("jogos").select("*").execute()

st.set_page_config(
    page_title="Bolão Copa 2026",
    layout="wide"
)

st.markdown("""
### ⚽ Como registrar seus palpites

Informe o placar desejado para cada partida e clique em **Salvar** para registrar um palpite individualmente.

Se preferir, preencha vários jogos de uma só vez. Os jogos alterados serão marcados automaticamente e poderão ser enviados juntos através do botão **Salvar Todos os Palpites** disponível na barra lateral.

> **Importante:** os palpites só podem ser alterados até o horário de início de cada partida.
""")

df_jogos = pd.DataFrame(jogos.data)
df_jogos["data_hora"] = pd.to_datetime(df_jogos["data_hora"]).dt.tz_convert("America/Sao_Paulo").dt.tz_localize(None)
df_jogos["criado_em"] = pd.to_datetime(df_jogos["criado_em"]).dt.tz_convert("America/Sao_Paulo").dt.tz_localize(None)
df_jogos = df_jogos.sort_values(by="data_hora")

jogos = [row[1] for row in df_jogos.iterrows()]

with st.sidebar:
    st.markdown("---")
    if st.button(
        "💾 Salvar Todos os Palpites",
        # on_click=salvar_palpites(user_id=user_id, jogos=jogos)
    ):
        salvar_palpites(user_id=user_id, jogos=jogos)

def card_jogo(jogo, idx):

    with st.container(border=True):
        data_hora = jogo["data_hora"]
        data_hora_fmt = f"{data_hora.strftime('%d/%m')} • {dias[data_hora.weekday()]} • {data_hora.strftime('%H:%M')}"
        time1 = jogo["time1"]
        time2 = jogo["time2"]
        url_flag_1 = f"https://a.espncdn.com/i/teamlogos/countries/500/{dict_pais_bandeira[time1]}.png"
        url_flag_2 = f"https://a.espncdn.com/i/teamlogos/countries/500/{dict_pais_bandeira[time2]}.png"
        estadio = jogo["estadio"]
        jogo_id = jogo["id"]

        cab1, cab2 = st.columns([1, 1])

        with cab1:
            st.markdown(f"**Grupo {jogo['grupo']}**")

        with cab2:
            st.markdown(
                f"<div style='text-align:right'>{data_hora_fmt}</div>",
                unsafe_allow_html=True
            )

        st.divider()

        t1_flag, t1_nome, p1, p2, t2_nome, t2_flag = st.columns(
                                                                [0.8, 3, 1, 1, 3, 0.8]
                                                            )

        with t1_flag:
            st.markdown(
                        f"""
                        <div style="display:flex; justify-content:center;">
                            <img src="{url_flag_1}" width="100">
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        with t1_nome:
            st.markdown(
                f"<div style='text-align:center'><b>{time1}</b></div>",
                # time1,
                unsafe_allow_html=True
            )

        with p1:
            palpite_1 = st.selectbox(
                "x",
                range(11),
                key=f"casa_{jogo_id}",
                label_visibility="collapsed",
                on_change=marcar_modificado,
                args=(jogo_id,)
            )

        with p2:
            palpite_2 = st.selectbox(
                "x",
                range(11),
                key=f"fora_{jogo_id}",
                label_visibility="collapsed",
                on_change=marcar_modificado,
                args=(jogo_id,)
            )

        with t2_nome:
            st.markdown(
                f"<div style='text-align:center'><b>{time2}</b></div>",
                # time2,
                unsafe_allow_html=True
            )

        with t2_flag:
            st.markdown(
                        f"""
                        <div style="display:flex; justify-content:center;">
                            <img src="{url_flag_2}" width="100">
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        st.markdown("")

        rod1, rod2, rod3 = st.columns([3, 2, 2])

        with rod1:
            st.caption(f"📍 {estadio}")

        with rod2:
            palpites_salvos = st.session_state.get("palpites_salvos", {})
            if jogo_id in palpites_salvos:
                p = palpites_salvos[jogo_id]
                st.caption(
                    f"✅ Palpite Enviado: **{p['palpite_time1']} x {p['palpite_time2']}**"
                )
            else:
                st.caption("⏳ Palpite Não enviado")

        with rod3:
            if st.button(
                "Salvar",
                key=f"btn_{idx}",
                use_container_width=True
            ):
                # supabase.table("palpites").upsert(
                #                                 {"usuario_id": int(user_id), 
                #                                  "jogo_id": int(jogo_id), 
                #                                  "palpite_time1": palpite_1, 
                #                                  "palpite_time2": palpite_2},
                #                                 on_conflict="usuario_id,jogo_id").execute()
                
                # st.toast('Palpite salvo com sucesso!', icon="✅")

                jogos_modificados = st.session_state.get("jogos_modificados", set())
                ja_salvo = jogo_id in st.session_state.get("palpites_salvos", {})

                if jogo_id in jogos_modificados or ja_salvo:
                    supabase.table("palpites").upsert(
                        {
                            "usuario_id": int(user_id),
                            "jogo_id": int(jogo_id),
                            "palpite_time1": palpite_1,
                            "palpite_time2": palpite_2
                        },
                        on_conflict="usuario_id,jogo_id"
                    ).execute()

                    # Atualiza cache local
                    st.session_state.setdefault("palpites_salvos", {})[jogo_id] = {
                        "palpite_time1": palpite_1,
                        "palpite_time2": palpite_2
                    }
                    jogos_modificados.discard(jogo_id)
                    st.toast('Palpite salvo com sucesso!', icon="✅")
                else:
                    st.toast('Altere o placar antes de salvar.', icon="⚠️")

carregar_palpites_existentes(user_id, jogos)

for i in range(0, len(jogos), 2):
    cols = st.columns(2)

    with cols[0]:
        card_jogo(jogos[i], i)

    if i + 1 < len(jogos):
        with cols[1]:
            card_jogo(jogos[i + 1], i + 1)