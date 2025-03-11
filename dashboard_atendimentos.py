import streamlit as st
import pandas as pd
import plotly.express as px

# Título da aplicação
st.set_page_config(page_title='Dashboard UPA 24H', layout='wide')
st.title('Dashboard de Análise de Atendimentos UPA 24H')

# Sidebar
st.sidebar.header('Filtros')

# Upload do arquivo Excel
uploaded_file = st.sidebar.file_uploader("Envie a planilha de atendimentos", type=["xlsx"])

if uploaded_file:
    # Carregar os dados
    df = pd.read_excel(uploaded_file)

    # Limpar e ajustar dados
    df_clean = df.dropna(how="all").reset_index(drop=True)
    df_clean.columns = df_clean.iloc[0]  # Definir cabeçalho correto
    df_clean = df_clean[1:].reset_index(drop=True)

    # Filtros
    especialidade_filter = st.sidebar.multiselect('Filtrar por Especialidade', df_clean['Especialidade'].unique())
    profissional_filter = st.sidebar.multiselect('Filtrar por Profissional', df_clean['Profissional'].unique())
    cid10_filter = st.sidebar.multiselect('Filtrar por CID-10', df_clean['Cid10'].unique())

    if especialidade_filter:
        df_clean = df_clean[df_clean['Especialidade'].isin(especialidade_filter)]

    if profissional_filter:
        df_clean = df_clean[df_clean['Profissional'].isin(profissional_filter)]

    if cid10_filter:
        df_clean = df_clean[df_clean['Cid10'].isin(cid10_filter)]

    col1, col2 = st.columns(2)

    # Gráfico de especialidades
    if 'Especialidade' in df_clean.columns:
        especialidades = df_clean['Especialidade'].value_counts().reset_index()
        especialidades.columns = ['Especialidade', 'Quantidade']
        fig1 = px.pie(especialidades, names='Especialidade', values='Quantidade', title='Distribuição de Especialidades')
        col1.plotly_chart(fig1)

    # Seleção e contagem por categoria de profissional
    if 'Especialidade' in df_clean.columns:
        categorias = df_clean['Especialidade'].value_counts().reset_index()
        categorias.columns = ['Categoria Profissional', 'Quantidade']
        st.write("Contagem por Categoria Profissional:", categorias)

    # Gráfico de motivos de alta
    if 'Motivo Alta' in df_clean.columns:
        motivos_alta = df_clean['Motivo Alta'].value_counts().reset_index()
        motivos_alta.columns = ['Motivo Alta', 'Quantidade']
        fig2 = px.bar(motivos_alta, x='Motivo Alta', y='Quantidade', title='Motivos de Alta')
        col2.plotly_chart(fig2)

    # Gráfico de CID-10 - Somente os mais predominantes
    if 'Cid10' in df_clean.columns:
        cid10_counts = df_clean['Cid10'].value_counts().reset_index()
        cid10_counts.columns = ['Cid10', 'Quantidade']
        cid10_top = cid10_counts.head(10)  # Pegar os 10 mais frequentes
        fig3 = px.bar(cid10_top, x='Cid10', y='Quantidade', title='Top 10 CID-10 Mais Frequentes')
        st.plotly_chart(fig3)

    # Contagem de atendimentos por usuário - Top 10
    if 'Usuário' in df_clean.columns:
        usuarios_counts = df_clean['Usuário'].value_counts().reset_index()
        usuarios_counts.columns = ['Usuário', 'Quantidade de Atendimentos']
        usuarios_top10 = usuarios_counts.head(10)
        st.write("Top 10 Usuários com Mais Atendimentos:", usuarios_top10)

    # Contagem de atendimentos por profissional - Top 10
    if 'Profissional' in df_clean.columns:
        profissionais_counts = df_clean['Profissional'].value_counts().reset_index()
        profissionais_counts.columns = ['Profissional', 'Quantidade de Atendimentos']
        profissionais_top10 = profissionais_counts.head(10)
        st.write("Top 10 Profissionais com Mais Atendimentos:", profissionais_top10)
        fig4 = px.line(profissionais_top10, x='Profissional', y='Quantidade de Atendimentos', title='Top 10 Profissionais com Mais Atendimentos (Gráfico Linear)')
        st.plotly_chart(fig4)

    # Análise combinada de Profissional e Especialidade
    if 'Profissional' in df_clean.columns and 'Especialidade' in df_clean.columns:
        prof_esp_counts = df_clean.groupby(['Profissional', 'Especialidade']).size().reset_index(name='Quantidade')
        for especialidade in prof_esp_counts['Especialidade'].unique():
            esp_data = prof_esp_counts[prof_esp_counts['Especialidade'] == especialidade]
            fig = px.bar(esp_data, x='Profissional', y='Quantidade', title=f'Atendimentos por Profissional - {especialidade}')
            st.plotly_chart(fig)

    # Visualização dos dados ao final
    st.write("Visualização dos dados:", df_clean)

    st.success("Análise concluída com sucesso!")
