import streamlit as st

from services.auth import verificar_login

verificar_login()

# st.title("Regras do Bolão")
# st.write(f"Você está logado como: **{st.session_state.usuario}**")

# st.info("Página inicial do sistema. Aqui você pode adicionar o conteúdo pós-login.")
# st.header("🏆 Regras do Bolão", divider="gray")

st.markdown(
"""
# - Regras do Bolão

## 💰 Valor de Entrada

**R$ 50,00 por participante**

---

## 📊 Pontuação dos Jogos

| Acerto | Pontos |
|----------|----------|
| Placar exato | **10 pontos** |
| Resultado da partida (vitória, derrota ou empate) | **3 pontos** |

### Exemplos

| Resultado Real | Seu Palpite | Pontuação |
|---------------|------------|------------|
| Brasil 2 x 1 Argentina | Brasil 2 x 1 Argentina | **10 pontos** |
| Brasil 2 x 1 Argentina | Brasil 3 x 0 Argentina | **3 pontos** |
| Brasil 2 x 1 Argentina | Brasil 1 x 2 Argentina | **0 pontos** |

---

## ⭐ Pontuação Bônus

| Evento | Pontos |
|----------|----------|
| Acertar o artilheiro da competição | **12 pontos** |
| Acertar a seleção campeã | **12 pontos** |

---

# 🎁 Premiações

## 🥇 1º Prêmio — Fase de Grupos

**Campeão da Fase de Grupos**

🏆 Premiação: **40% do valor arrecadado**

---

## 🥇 2º Prêmio — Mata-Mata

**Campeão da Fase Eliminatória**

🏆 Premiação: **60% do valor arrecadado**

Nesta fase também serão contabilizados os pontos referentes a:

- ⭐ Artilheiro da competição
- ⭐ Seleção campeã

---

## 🔄 Regra Importante

Ao término da fase de grupos:

✅ Todas as pontuações serão zeradas.

A disputa do mata-mata começará do zero para todos os participantes, garantindo uma nova oportunidade de competição.

---

## ⏰ Prazo para Palpites

Os palpites poderão ser alterados livremente até o horário de início de cada partida.

Após o início do jogo:

❌ Não será mais possível cadastrar ou modificar palpites.

---

### Boa sorte a todos! 🍀⚽🏆
"""
)