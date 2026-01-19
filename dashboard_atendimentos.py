import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# 📋 Configuração da Página
title = 'Análises de Atendimentos - UPA 24H Dona Zulmira Soares'
st.set_page_config(page_title=title, layout='wide')
st.image('TESTEIRA PAINEL UPA1.png', width=100)
st.title(title)

# 📋 Sidebar - Upload e Filtros
st.sidebar.image('TESTEIRA PAINEL UPA1.png', width=350)
st.sidebar.header('Filtros')
uploaded_files = st.sidebar.file_uploader(
    "Envie as planilhas de atendimentos", type=["xlsx"], accept_multiple_files=True
)

# 🔍 Função para processar planilha
def processar_planilha(file):
    df_raw = pd.read_excel(file, skiprows=1, header=None)
    df_raw = df_raw.dropna(how='all')
    df_raw.columns = [
        'CPF', 'Paciente', 'Data', 'Hora', 'Especialidade', 'Profissional',
        'Motivo Alta', 'Procedimento', 'Cid10', 'Prioridade'
    ]
    return df_raw

# 📊 Funções de gráficos
def criar_grafico_barra(df, coluna, titulo, top_n=10):
    contagem = df[coluna].value_counts().reset_index()
    contagem.columns = [coluna, 'Quantidade']
    return px.bar(
        contagem.head(top_n),
        x=coluna,
        y='Quantidade',
        title=titulo,
        color='Quantidade',
        template='plotly_white'
    )

def criar_grafico_pizza(df, coluna, titulo, top_n=10):
    contagem = df[coluna].value_counts().reset_index()
    contagem.columns = [coluna, 'Quantidade']
    return px.pie(
        contagem.head(top_n),
        names=coluna,
        values='Quantidade',
        title=titulo
    )

# ⚛️ Processamento
if uploaded_files:
    dataframes = [processar_planilha(file) for file in uploaded_files]
    df_final = pd.concat(dataframes, ignore_index=True)

    # ---------------- FILTROS ----------------
    for col in df_final.columns:
        valores = df_final[col].dropna().unique()
        if len(valores) > 0:
            filtro = st.sidebar.multiselect(f'Filtrar por {col}', valores)
            if filtro:
                df_final = df_final[df_final[col].isin(filtro)]

    # ---------------- DATA / TURNO ----------------
    df_final['Data Atendimento'] = pd.to_datetime(df_final['Data'], errors='coerce')
    df_final['Hora'] = pd.to_datetime(df_final['Hora'], errors='coerce').dt.hour

    def identificar_turno(h):
        if pd.isnull(h): return 'Indefinido'
        if 6 <= h < 12: return 'Manhã'
        if 12 <= h < 18: return 'Tarde'
        if 18 <= h < 24: return 'Noite'
        return 'Madrugada'

    df_final['Turno'] = df_final['Hora'].apply(identificar_turno)

    # ==========================
    # 🔎 RESOLUTIVIDADE – SUS
    # ==========================
    def classificar_resolutividade(motivo):
        if pd.isnull(motivo):
            return 'Indefinido'
        m = str(motivo).lower()
        if any(x in m for x in ['alta', 'prescrição', 'observação', 'encerramento']):
            return 'Resolvido na UPA'
        if any(x in m for x in ['transfer', 'óbito', 'regulado']):
            return 'Não resolvido na UPA'
        return 'Indefinido'

    df_final['Resolutividade'] = df_final['Motivo Alta'].apply(classificar_resolutividade)

    # ---------------- INDICADORES ----------------
    total = len(df_final)
    taxa_resolucao = len(df_final[df_final['Resolutividade'] == 'Resolvido na UPA']) / total

    df_final = df_final.sort_values(['CPF', 'Data Atendimento'])
    df_final['Retorno_72h'] = (
        df_final.groupby('CPF')['Data Atendimento']
        .diff().dt.total_seconds().div(3600).le(72)
    )
    taxa_retorno = df_final['Retorno_72h'].mean()

    amarelos = df_final[df_final['Prioridade'].str.contains('Amarelo', case=False, na=False)]
    taxa_amarelo = (
        len(amarelos[amarelos['Resolutividade'] == 'Resolvido na UPA']) / len(amarelos)
        if len(amarelos) > 0 else 0
    )

    perfil = df_final['Prioridade'].value_counts(normalize=True) * 100
    verde_azul = perfil.filter(like='Verde').sum() + perfil.filter(like='Azul').sum()

    score = taxa_resolucao * 0.4 + (1 - taxa_retorno) * 0.2 + taxa_amarelo * 0.4

    if score >= 0.80:
        status = '🟢 UPA RESOLUTIVA'
    elif score >= 0.60:
        status = '🟡 PARCIALMENTE RESOLUTIVA'
    else:
        status = '🔴 BAIXA RESOLUTIVIDADE'

    # ==========================
    # PAINEL GERENCIAL
    # ==========================
    st.markdown("## 🏥 Avaliação de Resolutividade – SUS")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Resolução na UPA", f"{taxa_resolucao:.1%}", "≥ 85%")
    c2.metric("Retorno até 72h", f"{taxa_retorno:.1%}", "< 5%")
    c3.metric("Resolução Amarelos", f"{taxa_amarelo:.1%}", "≥ 80%")
    c4.metric("Score Geral", f"{score:.2f}", status)

    if verde_azul > 60:
        st.warning(f"⚠️ {verde_azul:.1f}% dos atendimentos são Verde/Azul — indício de sobrecarga da Atenção Básica.")

    fig_res = px.histogram(
        df_final,
        x='Resolutividade',
        color='Prioridade',
        barmode='group',
        title='Desfecho dos Atendimentos por Classificação de Risco'
    )
    st.plotly_chart(fig_res, use_container_width=True)

    # ==========================
    # ANÁLISES EXISTENTES
    # ==========================
    colunas_para_analisar = ['Especialidade', 'Motivo Alta', 'Profissional', 'Prioridade', 'Cid10', 'Procedimento']
    top_n = st.sidebar.slider("Número de itens no gráfico", 5, 20, 10)
    tipo_grafico = st.sidebar.selectbox("Tipo de gráfico", ["Barras", "Pizza"])

    for col in colunas_para_analisar:
        st.subheader(f"Análises para {col}")
        if tipo_grafico == "Barras":
            st.plotly_chart(criar_grafico_barra(df_final, col, f'Top {top_n} {col}', top_n), use_container_width=True)
        else:
            st.plotly_chart(criar_grafico_pizza(df_final, col, f'Top {top_n} {col}', top_n), use_container_width=True)

    # ==========================
    # CONCLUSÃO TÉCNICA
    # ==========================
    st.markdown(f"""
### 📝 Conclusão Técnica

Com base nos indicadores analisados, a **UPA Dona Zulmira Soares** apresenta:

- **Taxa de resolução:** {taxa_resolucao:.1%}  
- **Retorno em até 72h:** {taxa_retorno:.1%}  
- **Score de resolutividade:** {score:.2f}  

**Classificação final:** **{status}**

Avaliação fundamentada na Política Nacional de Atenção às Urgências (PNAU) e normas do SUS.
""")

    st.success("✅ Análise concluída com sucesso!")









