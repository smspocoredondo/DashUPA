import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# ===============================
# CONFIGURAÇÃO DA PÁGINA
# ===============================
title = 'Análises de Atendimentos - UPA 24H Dona Zulmira Soares'
st.set_page_config(page_title=title, layout='wide')

st.image('TESTEIRA PAINEL UPA1.png', width=120)
st.title(title)

# ===============================
# SIDEBAR
# ===============================
st.sidebar.image('TESTEIRA PAINEL UPA1.png', width=300)
st.sidebar.header('Filtros e Upload')

uploaded_files = st.sidebar.file_uploader(
    "Envie as planilhas de atendimentos",
    type=["xlsx"],
    accept_multiple_files=True
)

# ===============================
# FUNÇÃO DE LEITURA
# ===============================
def processar_planilha(file):
    df = pd.read_excel(file, skiprows=1, header=None)
    df = df.dropna(how='all')

    df.columns = [
        'CPF', 'Paciente', 'Data', 'Hora', 'Especialidade',
        'Profissional', 'Motivo Alta', 'Procedimento',
        'Cid10', 'Prioridade'
    ]

    # Padronização básica (não altera significado)
    df['Motivo Alta'] = df['Motivo Alta'].astype(str).str.strip().str.upper()
    df['Prioridade'] = df['Prioridade'].astype(str).str.strip().str.upper()
    df['Cid10'] = df['Cid10'].astype(str).str.upper().str[:3]

    return df

# ===============================
# FUNÇÕES DE GRÁFICO
# ===============================
def grafico_barra(df, coluna, titulo, top_n):
    cont = df[coluna].value_counts().reset_index()
    cont.columns = [coluna, 'Quantidade']
    return px.bar(
        cont.head(top_n),
        x=coluna,
        y='Quantidade',
        title=titulo,
        template='plotly_white'
    )

def grafico_pizza(df, coluna, titulo, top_n):
    cont = df[coluna].value_counts().reset_index()
    cont.columns = [coluna, 'Quantidade']
    return px.pie(
        cont.head(top_n),
        names=coluna,
        values='Quantidade',
        title=titulo
    )

# ===============================
# PROCESSAMENTO PRINCIPAL
# ===============================
if uploaded_files:
    dfs = [processar_planilha(f) for f in uploaded_files]
    df_final = pd.concat(dfs, ignore_index=True)

    # ===============================
    # FILTROS (CORRIGIDOS)
    # ===============================
    for col in df_final.columns:
        valores = df_final[col].dropna().astype(str).unique().tolist()
        valores.sort()

        filtro = st.sidebar.multiselect(f'Filtrar por {col}', valores)

        if filtro:
            df_final = df_final[df_final[col].astype(str).isin(filtro)]

    # ===============================
    # DATA / TURNO
    # ===============================
    df_final['Data Atendimento'] = pd.to_datetime(df_final['Data'], errors='coerce')
    df_final['Hora'] = pd.to_datetime(df_final['Hora'], errors='coerce').dt.hour

    def identificar_turno(h):
        if pd.isnull(h): return 'Indefinido'
        if 6 <= h < 12: return 'Manhã'
        if 12 <= h < 18: return 'Tarde'
        if 18 <= h < 24: return 'Noite'
        return 'Madrugada'

    df_final['Turno'] = df_final['Hora'].apply(identificar_turno)

    # ===============================
    # 🔎 RESOLUTIVIDADE – SUS
    # ===============================
    def classificar_resolutividade(m):
        if pd.isnull(m): return 'Indefinido'
        m = m.lower()
        if any(x in m for x in ['alta', 'prescrição', 'observação', 'encerramento']):
            return 'Resolvido na UPA'
        if any(x in m for x in ['transfer', 'regulação', 'óbito', 'internação']):
            return 'Não resolvido na UPA'
        return 'Indefinido'

    df_final['Resolutividade'] = df_final['Motivo Alta'].apply(classificar_resolutividade)

    # ===============================
    # INDICADORES
    # ===============================
    total = len(df_final)
    taxa_resolucao = len(df_final[df_final['Resolutividade'] == 'Resolvido na UPA']) / total

    df_final = df_final.sort_values(['CPF', 'Data Atendimento'])
    df_final['Retorno_72h'] = (
        df_final.groupby('CPF')['Data Atendimento']
        .diff().dt.total_seconds().div(3600).le(72)
    )

    taxa_retorno = df_final['Retorno_72h'].mean()

    amarelos = df_final[df_final['Prioridade'].str.contains('AMARELO', na=False)]
    taxa_amarelo = (
        len(amarelos[amarelos['Resolutividade'] == 'Resolvido na UPA']) / len(amarelos)
        if len(amarelos) > 0 else 0
    )

    score = taxa_resolucao * 0.4 + (1 - taxa_retorno) * 0.2 + taxa_amarelo * 0.4

    status = (
        '🟢 UPA RESOLUTIVA' if score >= 0.80 else
        '🟡 PARCIALMENTE RESOLUTIVA' if score >= 0.60 else
        '🔴 BAIXA RESOLUTIVIDADE'
    )

    # ===============================
    # PAINEL GERENCIAL
    # ===============================
    st.markdown("## 🏥 Avaliação de Resolutividade – SUS")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Resolução na UPA", f"{taxa_resolucao:.1%}")
    c2.metric("Retorno ≤ 72h", f"{taxa_retorno:.1%}")
    c3.metric("Resolução Amarelos", f"{taxa_amarelo:.1%}")
    c4.metric("Score Geral", f"{score:.2f}", status)

    # ===============================
    # GRÁFICOS ORIGINAIS
    # ===============================
    colunas_analise = [
        'Especialidade', 'Motivo Alta', 'Profissional',
        'Prioridade', 'Cid10', 'Procedimento'
    ]

    top_n = st.sidebar.slider("Quantidade nos gráficos", 5, 20, 10)
    tipo = st.sidebar.selectbox("Tipo de gráfico", ["Barras", "Pizza"])

    for col in colunas_analise:
        st.subheader(f"Análise: {col}")
        if tipo == "Barras":
            st.plotly_chart(
                grafico_barra(df_final, col, f"Top {top_n} {col}", top_n),
                use_container_width=True
            )
        else:
            st.plotly_chart(
                grafico_pizza(df_final, col, f"Top {top_n} {col}", top_n),
                use_container_width=True
            )

    # ===============================
    # DIA / TURNO
    # ===============================
    dias_pt = {
        'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
        'Thursday': 'Quinta', 'Friday': 'Sexta',
        'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }

    df_final['Dia Semana'] = df_final['Data Atendimento'].dt.day_name().map(dias_pt)

    fig_turno = px.histogram(
        df_final,
        x='Dia Semana',
        color='Turno',
        barmode='group',
        title='Atendimentos por Dia da Semana e Turno'
    )
    st.plotly_chart(fig_turno, use_container_width=True)

    fig_hora = px.histogram(df_final, x='Hora', nbins=24, title='Atendimentos por Hora')
    st.plotly_chart(fig_hora, use_container_width=True)

    # ===============================
    # CONCLUSÃO TÉCNICA
    # ===============================
    st.markdown(f"""
### 📝 Conclusão Técnica

A **UPA Dona Zulmira Soares** apresenta **{status}**, com:

- Taxa de resolução: **{taxa_resolucao:.1%}**
- Retorno em até 72h: **{taxa_retorno:.1%}**
- Score geral: **{score:.2f}**

Avaliação fundamentada na **Política Nacional de Atenção às Urgências (PNAU)** e parâmetros do SUS.
""")

    st.success("✅ Análise concluída com sucesso!")














