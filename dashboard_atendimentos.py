import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
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
    df = pd.read_excel("Painel Atendimentos (3).xlsx")
    return df

df = carregar_dados()

# ======================================================
# CORREÇÃO DO ERRO DO MULTISELECT
# (tratamento de NaN e tipos mistos)
# ======================================================
st.sidebar.header("🔎 Filtros")

colunas_filtro = ["Turno", "Classificação de Risco", "Desfecho", "Dia da Semana"]

df_filtrado = df.copy()

for col in colunas_filtro:
    if col in df.columns:
        valores = (
            df[col]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

        filtro = st.sidebar.multiselect(
            f"Filtrar por {col}",
            options=sorted(valores)
        )

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

# Score simples de resolutividade (mantém lógica do painel)
score = (
    (taxa_resolucao * 0.5) +
    ((1 - taxa_retorno) * 0.3) +
    (taxa_amarelo * 0.2)
)

if score >= 0.8:
    status = "ALTA RESOLUTIVIDADE"
elif score >= 0.6:
    status = "RESOLUTIVIDADE MODERADA"
else:
    status = "BAIXA RESOLUTIVIDADE"

# ======================================================
# EXIBIÇÃO DOS KPIs
# ======================================================
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total de Atendimentos", total)
c2.metric("Taxa de Resolução", f"{taxa_resolucao:.1%}")
c3.metric("Retorno em 72h", f"{taxa_retorno:.1%}")
c4.metric("Score Geral", f"{score:.2f}")

st.markdown(f"### 🧾 Classificação Técnica: **{status}**")

# ======================================================
# GRÁFICOS (MANTIDOS)
# ======================================================
st.markdown("## 📈 Análises Gráficas")

col_g1, col_g2 = st.columns(2)

with col_g1:
    fig1 = plt.figure()
    df_filtrado["Classificação de Risco"].value_counts().plot(kind="bar")
    plt.title("Distribuição por Classificação de Risco")
    plt.xlabel("")
    plt.ylabel("Atendimentos")
    st.pyplot(fig1)

with col_g2:
    fig2 = plt.figure()
    df_filtrado["Turno"].value_counts().plot(kind="bar")
    plt.title("Atendimentos por Turno")
    plt.xlabel("")
    plt.ylabel("Atendimentos")
    st.pyplot(fig2)

# ======================================================
# FUNÇÃO – RELATÓRIO DOCX (RAG / PAS / TCE)
# ======================================================
def gerar_docx_relatorio(periodo, total, taxa_res, taxa_ret, taxa_am, score, status):
    doc = Document()

    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    titulo = doc.add_heading(
        'RELATÓRIO TÉCNICO DE AVALIAÇÃO DA UPA 24H',
        level=1
    )
    titulo.alignment = 1

    doc.add_paragraph(
        'Unidade: UPA Dona Zulmira Soares\n'
        'Município: Poço Redondo – SE\n'
        f'Período Avaliado: {periodo}\n'
    )

    doc.add_heading('1. INTRODUÇÃO', level=2)
    doc.add_paragraph(
        'Relatório elaborado para avaliação da resolutividade assistencial da '
        'Unidade de Pronto Atendimento – UPA 24h, em conformidade com a Política '
        'Nacional de Atenção às Urgências (PNAU), subsidiando o RAG, PAS e a '
        'prestação de contas ao Tribunal de Contas.'
    )

    doc.add_heading('2. METODOLOGIA', level=2)
    doc.add_paragraph(
        'Foram analisados registros assistenciais da unidade, considerando '
        'produção, desfechos clínicos, retorno precoce e classificação de risco.'
    )

    doc.add_heading('3. INDICADORES ASSISTENCIAIS', level=2)
    doc.add_paragraph(f'- Total de atendimentos: {total}')
    doc.add_paragraph(f'- Taxa de resolução na UPA: {taxa_res:.1%}')
    doc.add_paragraph(f'- Retorno em até 72h: {taxa_ret:.1%}')
    doc.add_paragraph(f'- Resolução dos casos Amarelos: {taxa_am:.1%}')

    doc.add_heading('4. AVALIAÇÃO DA RESOLUTIVIDADE', level=2)
    doc.add_paragraph(
        f'O score de resolutividade foi de {score:.2f}, '
        f'classificando a unidade como: {status}.'
    )

    doc.add_heading('5. CONCLUSÃO TÉCNICA', level=2)
    doc.add_paragraph(
        'Conclui-se que a unidade apresenta desempenho compatível com sua '
        'finalidade assistencial no âmbito da Rede de Atenção às Urgências, '
        'devendo os indicadores serem monitorados continuamente.'
    )

    doc.add_paragraph(
        '\nPoço Redondo/SE, ____ de ____________________ de 2025.\n\n'
        '______________________________________________\n'
        'Responsável Técnico'
    )

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return buffer

# ======================================================
# BOTÃO – GERAR RELATÓRIO
# ======================================================
st.markdown("## 📄 Relatórios Oficiais")

if st.button("Gerar Relatório RAG / PAS / TCE (DOCX)"):
    docx_file = gerar_docx_relatorio(
        periodo="Período filtrado no painel",
        total=total,
        taxa_res=taxa_resolucao,
        taxa_ret=taxa_retorno,
        taxa_am=taxa_amarelo,
        score=score,
        status=status
    )

    st.download_button(
        label="📥 Baixar Relatório Técnico (DOCX)",
        data=docx_file,
        file_name="Relatorio_UPA_Dona_Zulmira_RAG_PAS_TCE.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
















