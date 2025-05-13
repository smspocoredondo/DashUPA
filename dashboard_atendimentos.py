import streamlit as st
import pandas as pd
import plotly.express as px

# 🧾 Configuração da Página
title = 'Análises de Atendimentos - UPA 24H Dona Zulmira Soares'
st.set_page_config(page_title=title, layout='wide')
st.image('TESTEIRA PAINEL UPA1.png', width=100)
st.title(title)

# 📁 Sidebar - Upload e Filtros
st.sidebar.image('TESTEIRA PAINEL UPA1.png', width=350)
st.sidebar.header('Filtros')
uploaded_files = st.sidebar.file_uploader(
    "Envie as planilhas de atendimentos", type=["xlsx"], accept_multiple_files=True
)

# 🔍 Função para processar planilha
def processar_planilha(file):
    df = pd.read_excel(file)
    df_clean = df.dropna(how="all").reset_index(drop=True)
    df_clean.columns = df_clean.iloc[0]
    df_clean = df_clean[1:].reset_index(drop=True)
    return df_clean

# 📊 Função para gráfico de barras
def criar_grafico_barra(df, coluna, titulo, top_n=10):
    if coluna in df.columns:
        contagem = df[coluna].value_counts().reset_index()
        contagem.columns = [coluna, 'Quantidade']
        grafico = px.bar(
            contagem.head(top_n),
            x=coluna,
            y='Quantidade',
            title=titulo,
            color='Quantidade',
            color_continuous_scale=['#F00011','#B8F059','#33F000']  # Paleta de cores suaves
        )
        grafico.update_layout(
            title_font=dict(size=20, color='darkblue'),
            xaxis_title_font=dict(size=14),
            yaxis_title_font=dict(size=14),
            template='plotly_white'
        )
        return grafico
    return None

# 📊 Função para gráfico de pizza
def criar_grafico_pizza(df, coluna, titulo, top_n=10):
    if coluna in df.columns:
        contagem = df[coluna].value_counts().reset_index()
        contagem.columns = [coluna, 'Quantidade']
        grafico = px.pie(
            contagem.head(top_n),
            names=coluna,
            values='Quantidade',
            title=titulo,
            color_discrete_sequence=['#33F000', '#B8F059', '#F02700','#F01D0A']  # Paleta de cores suaves
        )
        grafico.update_layout(
            title_font=dict(size=20, color='gray'),
            template='plotly_white'
        )
        return grafico
    return None

# 🚀 Processamento ao carregar arquivos
if uploaded_files:
    dataframes = [processar_planilha(file) for file in uploaded_files]
    df_final = pd.concat(dataframes, ignore_index=True)

    # 🎯 Validação de colunas esperadas
    colunas_esperadas = ['Especialidade', 'Motivo Alta', 'Usuário', 'Profissional', 'Prioridade', 'Cid10']
    for coluna in colunas_esperadas:
        if coluna not in df_final.columns:
            st.warning(f"A coluna esperada '{coluna}' não foi encontrada nos dados carregados.")

    # 🎯 Filtros dinâmicos
    colunas_disponiveis = df_final.columns.tolist()
    filtros = {
        col: st.sidebar.multiselect(f'Filtrar por {col}', df_final[col].unique())
        for col in colunas_disponiveis
    }

    for coluna, filtro in filtros.items():
        if filtro:
            df_final = df_final[df_final[coluna].isin(filtro)]

    # 🔢 Total geral de atendimentos com destaque visual
    total_atendimentos = len(df_final)
    st.markdown(
        f"""
        <div style="padding:20px; margin-bottom:20px; background-color:#e0f7fa; 
                    border-left:8px solid #007BFF; border-radius:10px; 
                    font-size:24px; font-weight:bold; color:#007BFF; 
                    box-shadow: 0 0 10px rgba(0,123,255,0.1);">
            💧 Total Geral de Atendimentos: {total_atendimentos}
        </div>
        """,
        unsafe_allow_html=True
    )

    # 📈 Geração dos gráficos para cada coluna
    colunas_para_analisar = ['Especialidade', 'Motivo Alta', 'Usuário', 'Profissional', 'Prioridade', 'Cid10']
    top_n = st.sidebar.slider("Número de itens no gráfico", min_value=5, max_value=20, value=10, step=1)
    tipo_grafico = st.sidebar.selectbox("Selecione o tipo de gráfico", ["Barras", "Pizza"])

    for col in colunas_para_analisar:
        if col in df_final.columns:
            st.subheader(f"Análises para {col}")
            if tipo_grafico == "Barras":
                grafico = criar_grafico_barra(df_final, col, f'Top {top_n} {col} Mais Frequentes', top_n=top_n)
            elif tipo_grafico == "Pizza":
                grafico = criar_grafico_pizza(df_final, col, f'Top {top_n} {col} Mais Frequentes', top_n=top_n)
            if grafico:
                st.plotly_chart(grafico, use_container_width=True)

    # 📈 Gráfico de séries temporais
    if 'Data Atendimento' in df_final.columns:
        df_final['Data Atendimento'] = pd.to_datetime(df_final['Data Atendimento'])
        data_min, data_max = st.sidebar.date_input("Filtrar por intervalo de datas", [])
        if data_min and data_max:
            df_final = df_final[(df_final['Data Atendimento'] >= data_min) & (df_final['Data Atendimento'] <= data_max)]
        atendimentos_por_data = df_final.groupby('Data Atendimento').size().reset_index(name='Quantidade')
        grafico_temporal = px.line(atendimentos_por_data, x='Data Atendimento', y='Quantidade', title='Atendimentos ao Longo do Tempo')
        st.plotly_chart(grafico_temporal, use_container_width=True)

    # 📊 Análise de correlação
    colunas_numericas = df_final.select_dtypes(include=['number']).columns
    if len(colunas_numericas) > 1:
        st.subheader("Mapa de Correlação")
        correlacao = df_final[colunas_numericas].corr()
        fig_corr = px.imshow(correlacao, text_auto=True, color_continuous_scale=['#FF9999', '#99CCFF', '#99FF99'], title="Correlação entre Variáveis")
        st.plotly_chart(fig_corr, use_container_width=True)

    # 📋 Resumo estatístico
    st.subheader("Resumo Estatístico")
    st.write(df_final.describe())

    # 📤 Exportação de dados filtrados
    st.sidebar.download_button(
        label="Baixar dados filtrados",
        data=df_final.to_csv(index=False).encode('utf-8'),
        file_name='dados_filtrados.csv',
        mime='text/csv'
    )

    # 📋 Tabela final
    st.write("Visualização dos dados:", df_final)
    st.success("Análise concluída com sucesso!")
