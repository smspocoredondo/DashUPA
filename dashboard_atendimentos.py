import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from docx import Document
from docx.shared import Pt

# ======================================================
# CONFIGURAÇÃO INICIAL
# ======================================================
st.set_page_config(
    page_title="Painel de Atendimentos – UPA 24h",
    layout="wide"
)

st.title("📊 Painel de Atendimentos – UPA Dona Zulmira Soares")

# ======================================================
# CARREGAMENTO DOS DADOS
# ======================================================
@st.cache_data
def carregar_dados():
    return pd.read_excel("Painel Atendimentos (3).xlsx")

df = carregar_dados()

# ======================================================
# FILTROS – CORREÇÃO DEFINITIVA (TIPOS MISTOS)
# ======================================================
st.sidebar.header("🔎 Filtros")

df_filtrado = df.copy()

colunas_filtro = ["Turno", "Classificação de Risco", "Desfecho", "Dia da Semana"]

for col in colunas_filtro:
    if col in df_filtrado.columns:
        valores = (
            df_filtrado[col]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        valores.sort()

        filtro = st.sidebar.multiselect(f"Filtrar por {col}", valores)

        if filtro:
            df_filtrado = df_filtrado[df_filtrado[col].astype(str).isin(filtro)]

# ======================================================
# INDICADORES PRINCIPAIS
# ======================================================
total = len(df_filtrado)

resolvidos = df_filtrado[df_filtrado["Desfecho"] == "Alta"].shape[0]
taxa_resolucao = resolvidos / total if total > 0 else 0

retornos = df_filtrado[df_filtrado["Retorno 72h"] == "Sim"].shape[0]
taxa_retorno = retornos / total if total > 0 else 0

amarelos = df_filtrado[df_filtrado["Classificação de Risco"] == "Amarelo"]
taxa_amarelo = (
    amarelos[amarelos["Desfecho"] == "Alta"].shape[0] / len(amarelos)
    if len(amarelos) > 0 else 0
)

# Score de resolutividade (mantido)
score = (
    (taxa_resolucao * 0.5) +
    ((1 - taxa_retorno) * 0.3) +
    (taxa_amarelo * 0.2)
)

if score >= 0.8:
    status = "🟢 ALTA RESOLUTIVIDADE"
elif score >= 0.6:
    status = "🟡 RESOLUTIVIDADE MODERADA"
else:
    status = "🔴 BAIXA RESOLUTIVIDADE"

# ======================================================
# KPIs
# ======================================================
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total de Atendimentos", total)
c2.metric("Taxa de Resolução", f"{taxa_resolucao:.1%}")
c3.metric("Retorno em 72h", f"{taxa_retorno:.1%}")
c4.metric("Score Geral", f"{score:.2f}", status)

# ======================================================
# GRÁFICOS (PLOTLY – SEM MATPLOTLIB)
# ======================================================
st.markdown("## 📈 Análises Gráficas")

col1, col2 = st.columns(2)

with col1:
    fig_risco = px.bar(
        df_filtrado["Classificação de Risco"].value_counts().reset_index(),
        x="index",
        y="Classificação de Risco",
        labels={"index": "Classificação", "Classificação de Risco": "Atendimentos"},
        title="Distribuição por Classificação de Risco"
    )
    st.plotly_chart(fig_risco, use_container_width=True)

with col2:
    fig_turno = px.bar(
        df_filtrado["Turno"].value_counts().reset_index(),
        x="index",
        y="Turno",
        labels={"index": "Turno", "Turno": "Atendimentos"},
        title="Atendimentos por Turno"
    )
    st.plotly_chart(fig_turno, use_container_width=True)

# ======================================================
# RELATÓRIO DOCX – RAG / PAS / TCE
# ======================================================
def gerar_relatorio_docx(total, taxa_res, taxa_ret, taxa_am, score, status):
    doc = Document()

    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    doc.add_heading("RELATÓRIO TÉCNICO – AVALIAÇÃO DA UPA 24H", level=1)

    doc.add_paragraph(
        "Unidade: UPA Dona Zulmira Soares\n"
        "Município: Poço Redondo – SE\n"
        "Base Legal: PNAU / SUS\n"
    )

    doc.add_heading("Indicadores Assistenciais", level=2)
    doc.add_paragraph(f"Total de atendimentos: {total}")
    doc.add_paragraph(f"Taxa de resolução na UPA: {taxa_res:.1%}")
    doc.add_paragraph(f"Retorno em até 72h: {taxa_ret:.1%}")
    doc.add_paragraph(f"Resolução dos casos Amarelos: {taxa_am:.1%}")

    doc.add_heading("Avaliação da Resolutividade", level=2)
    doc.add_paragraph(
        f"O score de resolutividade foi de {score:.2f}, "
        f"classificando a unidade como: {status}."
    )

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

st.markdown("## 📄 Relatórios Oficiais")

if st.button("📥 Gerar Relatório RAG / PAS / TCE (DOCX)"):
    arquivo = gerar_relatorio_docx(
        total,
        taxa_resolucao,
        taxa_retorno,
        taxa_amarelo,
        score,
        status
    )

    st.download_button(
        "Baixar Relatório DOCX",
        data=arquivo,
        file_name="Relatorio_UPA_Dona_Zulmira_RAG_PAS_TCE.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


















