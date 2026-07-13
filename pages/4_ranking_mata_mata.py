from supabase import create_client, Client
from dateutil import parser
from datetime import timezone, timedelta
import streamlit as st
import pandas as pd

from services.auth import verificar_login
from services.util import dict_pais_bandeira, dict_jogadores

verificar_login()

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

user_name = st.session_state["user_name"]
user_id = st.session_state["user_id"]

@st.cache_data(ttl=300)
def carregar_ranking():
    res = supabase.table("ranking_mata_mata").select("*").order("pontos", desc=True).order("nome", desc=False).execute()
    return res.data

@st.cache_data(ttl=300)
def carregar_jogos_passados():
    from datetime import datetime
    agora = datetime.now(timezone.utc).isoformat()

    res = (
        supabase.table("jogos")
        .select("id, time1, time2, gols_time1, gols_time2, data_hora")
        # .not_.is_("gols_time1", "null")
        # .not_.is_("gols_time2", "null")
        .lt("data_hora", agora)
        .neq("fase", "Fase de Grupos")
        .order("data_hora", desc=True)
        .execute()
    )
    return res.data

@st.cache_data(ttl=300)
def carregar_palpites_encerrados():
    jogos = carregar_jogos_passados()
    jogo_ids = [j["id"] for j in jogos]
    
    res_usuarios = supabase.table("usuarios").select("id, nome").execute()
    mapa_nomes = {u["id"]: u["nome"] for u in res_usuarios.data}

    todos_palpites = []
    tamanho_lote = 30

    for i in range(0, len(jogo_ids), tamanho_lote):
        lote = jogo_ids[i:i + tamanho_lote]
        res = (
            supabase.table("palpites")
            .select("usuario_id, jogo_id, palpite_time1, palpite_time2, atualizado_em")
            .in_("jogo_id", lote)
            .limit(1000)
            .execute()
        )
        todos_palpites.extend(res.data)

    for p in todos_palpites:
        p["nome"] = mapa_nomes.get(p["usuario_id"], f"Usuário {p['usuario_id']}")

    return todos_palpites

@st.cache_data(ttl=300)
def carregar_palpites_extras():
    res_extras = (
        supabase.table("palpites_extras")
        .select("usuario_id, selecao_campea, artilheiro, atualizado_em")
        .execute()
    )

    res_usuarios = supabase.table("usuarios").select("id, nome").execute()
    mapa_nomes = {u["id"]: u["nome"] for u in res_usuarios.data}

    for p in res_extras.data:
        p["nome"] = mapa_nomes.get(p["usuario_id"], f"Usuário {p['usuario_id']}")

    return res_extras.data

def render_ranking_html(dados: list, nome_logado: str):
    css = """
    <style>
        .ranking-table {
            width: 100%;
            border-collapse: collapse;
            font-family: sans-serif;
            font-size: 0.95rem;
        }
        .ranking-table thead tr {
            background: #0F2340;
            color: #94a3b8;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            border-bottom: 2px solid #1e3a5f;
        }
        .ranking-table th {
            padding: 10px 12px;
            text-align: center;
            font-weight: 500;
        }
        .ranking-table th:nth-child(2) {
            text-align: left;
        }
        .ranking-table tbody tr {
            border-bottom: 1px solid #1e3a5f;
            color: #E2E8F0;
        }
        .ranking-table tbody tr:hover {
            background: #0F2340;
        }
    </style>
    """

    linhas = ""
    for i, row in enumerate(dados, start=1):
        nome = row["nome"]
        destaque = nome == nome_logado

        if i == 1:
            medalha = "🥇"
        elif i == 2:
            medalha = "🥈"
        elif i == 3:
            medalha = "🥉"
        else:
            medalha = f"{i}º"

        estilo_linha = 'background: rgba(34, 197, 94, 0.1); font-weight: 600;' if destaque else ''
        tag_voce = '<span style="font-size:0.7rem; background:rgba(34,197,94,0.2); color:#22C55E; border-radius:4px; padding:1px 6px; margin-left:6px;">você</span>' if destaque else ''

        linhas += (
            f'<tr style="{estilo_linha}">'
            f'<td style="text-align:center; padding:8px 12px;">{medalha}</td>'
            f'<td style="padding:8px 12px;">{nome} {tag_voce}</td>'
            f'<td style="text-align:center; padding:8px 12px;">{row["acertos_exatos"]}</td>'
            f'<td style="text-align:center; padding:8px 12px;">{row["acertos_resultado"]}</td>'
            f'<td style="text-align:center; padding:8px 12px; font-weight:700;">{row["pontos"]}</td>'
            f'</tr>'
        )

    tabela = (
        '<table class="ranking-table">'
        '<thead><tr>'
        '<th>Posição</th><th>Participante</th><th>🎯 Exato</th><th>✅ Resultado</th><th>Pontos</th>'
        '</tr></thead>'
        f'<tbody>{linhas}</tbody>'
        '</table>'
    )

    st.markdown(css + tabela, unsafe_allow_html=True)

def encontrar_pais(jogador: str, dados: dict = dict_jogadores):
    for pais, posicoes in dados.items():
        for lista_jogadores in posicoes.values():
            if jogador in lista_jogadores:
                return pais
    return None

def img_bandeira(nome_pais: str):
    """Retorna a tag <img> da bandeira, ou string vazia se o país não for mapeado."""
    if not nome_pais:
        return ""
    codigo = dict_pais_bandeira.get(nome_pais)
    if not codigo:
        return ""
    return (
        f'<img src="https://a.espncdn.com/i/teamlogos/countries/500/{codigo}.png" '
        f'style="height:16px; border-radius:2px; vertical-align:middle; margin-right:6px;">'
    )

def render_palpites_extras_html(dados: list, nome_logado: str):
    css = """
    <style>
        .extras-table {
            width: 100%;
            border-collapse: collapse;
            font-family: sans-serif;
            font-size: 0.95rem;
        }
        .extras-table thead tr {
            background: #0F2340;
            color: #94a3b8;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            border-bottom: 2px solid #1e3a5f;
        }
        .extras-table th {
            padding: 10px 12px;
            text-align: center;
            font-weight: 500;
        }
        .extras-table th:nth-child(1) {
            text-align: left;
        }
        .extras-table tbody tr {
            border-bottom: 1px solid #1e3a5f;
            color: #E2E8F0;
        }
        .extras-table tbody tr:hover {
            background: #0F2340;
        }
    </style>
    """

    linhas = ""
    for row in dados:
        nome = row["nome"]
        destaque = nome == nome_logado

        campeao = row["selecao_campea"] or "—"

        artilheiro = row["artilheiro"] or "—"
        pais_artilheiro = encontrar_pais(artilheiro)

        estilo_linha = 'background: rgba(34, 197, 94, 0.1); font-weight: 600;' if destaque else ''
        tag_voce = '<span style="font-size:0.7rem; background:rgba(34,197,94,0.2); color:#22C55E; border-radius:4px; padding:1px 6px; margin-left:6px;">você</span>' if destaque else ''

        linhas += (
            f'<tr style="{estilo_linha}">'
            f'<td style="padding:8px 12px;">{nome} {tag_voce}</td>'
            f'<td style="text-align:center; padding:8px 12px;">{img_bandeira(campeao)} {campeao}</td>'
            f'<td style="text-align:center; padding:8px 12px;">{img_bandeira(pais_artilheiro)} {artilheiro}</td>'
            f'</tr>'
        )

    tabela = (
        '<table class="extras-table">'
        '<thead><tr>'
        '<th>Participante</th><th>Campeão</th><th>Artilheiro</th>'
        '</tr></thead>'
        f'<tbody>{linhas}</tbody>'
        '</table>'
    )

    st.markdown(css + tabela, unsafe_allow_html=True)

# ── Página ────────────────────────────────────────────────────────────────────

st.title("🏆 Ranking & Palpites - Fase Mata Mata")

aba_ranking, aba_palpites, aba_extras = st.tabs(
    ["🥇 Ranking", "🔍 Palpites dos Jogos", "🏆 Palpites Extras"]
)

# ── Aba Ranking ───────────────────────────────────────────────────────────────

with aba_ranking:
    dados = carregar_ranking()

    if not dados:
        st.info("Nenhum resultado disponível ainda.")
    else:
        render_ranking_html(dados, user_name)

# ── Aba Palpites ──────────────────────────────────────────────────────────────

with aba_palpites:
    jogos = carregar_jogos_passados()
    palpites = carregar_palpites_encerrados()

    if not jogos:
        st.info("Nenhum jogo encerrado ainda.")
    else:
        # Indexa palpites por jogo_id
        from collections import defaultdict
        palpites_por_jogo = defaultdict(list)
        for p in palpites:
            palpites_por_jogo[p["jogo_id"]].append(p)

        for jogo in jogos:
            jogo_id = jogo["id"]
            t1, t2 = jogo["time1"], jogo["time2"]
            g1, g2 = jogo["gols_time1"], jogo["gols_time2"]

            if g1 is not None and g2 is not None:
                titulo = f"**{t1} {g1} x {g2} {t2}**"
            else:
                titulo = f"**{t1} x {t2}** — em andamento"

            with st.expander(titulo, expanded=False):
                lista = palpites_por_jogo.get(jogo_id, [])

                if not lista:
                    st.caption("Nenhum palpite registrado.")
                    continue

                rows = []
                for p in lista:
                    nome = p["nome"] #["usuarios"]
                    p1, p2 = p["palpite_time1"], p["palpite_time2"]
                    dt = parser.parse(p["atualizado_em"])
                    dt_brt = dt.astimezone(timezone(timedelta(hours=-3)))
                    dt_formatado = dt_brt.strftime("%d/%m %H:%M")

                    if g1 is None or g2 is None:
                        status = "⏳ Aguardando resultado"
                    # Avalia acerto
                    else:
                        if (p1, p2) == (g1, g2):
                            status = "🎯 Placar exato"
                        elif (p1 is not None and p2 is not None and
                            (p1 > p2) == (g1 > g2) and (p1 < p2) == (g1 < g2)):
                            status = "✅ Resultado certo"
                        else:
                            status = "❌ Errou"

                    destaque = nome == user_name
                    rows.append({
                        "Participante": f"⭐ {nome}" if destaque else nome,
                        "Palpite": f"{p1} x {p2}" if p1 is not None else "—",
                        "Data de Envio": dt_formatado,
                        "Resultado": status,
                    })

                # Ordena: usuário logado primeiro, depois por status
                ordem_status = {"🎯 Placar exato": 0, "✅ Resultado certo": 1, "❌ Errou": 2}
                rows.sort(key=lambda r: (
                    0 if user_name in r["Participante"] else 1,
                    ordem_status.get(r["Resultado"], 3)
                ))

                df_p = pd.DataFrame(rows)

                def destacar_palpite(row):
                    if user_name in row["Participante"]:
                        return ["background-color: #22c55e1a; font-weight: bold"] * len(row)
                    return [""] * len(row)

                st.dataframe(
                    df_p.style.apply(destacar_palpite, axis=1),
                    use_container_width=True,
                    hide_index=True,
                )

with aba_extras:
    extras = carregar_palpites_extras()

    if not extras:
        st.info("Nenhum palpite extra registrado ainda.")
    else:
        # Ordena: usuário logado primeiro, depois alfabético
        extras.sort(key=lambda r: (r["nome"] != user_name, r["nome"]))
        render_palpites_extras_html(extras, user_name)