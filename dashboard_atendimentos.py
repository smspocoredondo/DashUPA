import streamlit as st
import pandas as pd
import plotly.express as px

# 📋 Configuração da Página
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
    df_raw = pd.read_excel(file, skiprows=1)
    df_raw.columns = df_raw.iloc[0]
    df_clean = df_raw[1:].reset_index(drop=True)
    df_clean.columns = df_clean.columns.str.strip()
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
            color_continuous_scale=['#e0f2f1', '#4dd0e1', '#009688']
        )
        grafico.update_layout(
            title_font=dict(size=20, color='#009688'),
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
            color_discrete_sequence=['#e0f2f1', '#4dd0e1', '#009688', '#b2dfdb', '#80cbc4']
        )
        grafico.update_layout(
            title_font=dict(size=20, color='#009688'),
            template='plotly_white'
        )
        return grafico
    return None

# ⚛️ Processamento ao carregar arquivos
if uploaded_files:
    dataframes = [processar_planilha(file) for file in uploaded_files]
    df_final = pd.concat(dataframes, ignore_index=True)

    colunas_esperadas = ['Especialidade', 'Motivo Alta', 'Usuário', 'Profissional', 'Prioridade', 'Cid10', 'Procedimento']
    for coluna in colunas_esperadas:
        if coluna not in df_final.columns:
            st.warning(f"A coluna esperada '{coluna}' não foi encontrada nos dados carregados.")

    colunas_disponiveis = df_final.columns.tolist()
    filtros = {
        col: st.sidebar.multiselect(f'Filtrar por {col}', df_final[col].dropna().unique())
        for col in colunas_disponiveis
    }
    for coluna, filtro in filtros.items():
        if filtro:
            df_final = df_final[df_final[coluna].isin(filtro)]

    if 'Data' in df_final.columns:
        df_final['Data Atendimento'] = pd.to_datetime(df_final['Data'], errors='coerce')
        df_final['Hora'] = pd.to_datetime(df_final['Hora'], errors='coerce').dt.hour

        def identificar_turno(hora):
            if pd.isnull(hora): return 'Indefinido'
            if 6 <= hora < 12: return 'Manhã (06h-12h)'
            elif 12 <= hora < 18: return 'Tarde (12h-18h)'
            elif 18 <= hora < 24: return 'Noite (18h-00h)'
            else: return 'Madrugada (00h-06h)'

        df_final['Turno'] = df_final['Hora'].apply(identificar_turno)

    st.markdown(f"""
        <div style="padding:22px; margin-bottom:24px; background-color:#e0f7fa; 
                    border-left:10px solid #009688; border-radius:14px; 
                    font-size:28px; font-weight:bold; color:#009688; 
                    box-shadow: 0 2px 12px rgba(0,150,136,0.10); text-align:center;">
            🏥 Total Geral de Atendimentos: {len(df_final)}
        </div>
        """, unsafe_allow_html=True)

    if 'Especialidade' in df_final.columns:
        especialidades = df_final['Especialidade'].dropna().unique()
        cols = st.columns(min(len(especialidades), 4))
        for idx, esp in enumerate(especialidades):
            total = df_final[df_final['Especialidade'] == esp].shape[0]
            with cols[idx % 4]:
                st.markdown(f"""
                    <div style="padding:18px; margin-bottom:18px; background-color:#e6f9f0;
                                border-left:7px solid #009688; border-radius:12px;
                                font-size:20px; font-weight:bold; color:#009688;
                                box-shadow: 0 2px 8px rgba(0,150,136,0.09); text-align:center;">
                        💼<br>{esp}<br><span style="font-size:28px; color:#222;">{total}</span>
                    </div>
                """, unsafe_allow_html=True)

    colunas_para_analisar = ['Especialidade', 'Motivo Alta', 'Usuário', 'Profissional', 'Prioridade', 'Cid10', 'Procedimento']
    top_n = st.sidebar.slider("Número de itens no gráfico", 5, 20, 10)
    tipo_grafico = st.sidebar.selectbox("Tipo de gráfico", ["Barras", "Pizza"])

    for col in colunas_para_analisar:
        if col in df_final.columns:
            st.subheader(f"Análises para {col}")
            if tipo_grafico == "Barras":
                grafico = criar_grafico_barra(df_final, col, f'Top {top_n} {col} Mais Frequentes', top_n)
            else:
                grafico = criar_grafico_pizza(df_final, col, f'Top {top_n} {col} Mais Frequentes', top_n)
            if grafico:
                st.plotly_chart(grafico, use_container_width=True)

    if 'Data Atendimento' in df_final.columns:
        data_min, data_max = st.sidebar.date_input("Intervalo de Datas", [])
        if data_min and data_max:
            df_final = df_final[(df_final['Data Atendimento'] >= pd.to_datetime(data_min)) &
                                (df_final['Data Atendimento'] <= pd.to_datetime(data_max))]

        df_final['Semana'] = df_final['Data Atendimento'].dt.to_period('W').astype(str)
        semana = df_final.groupby('Semana').size().reset_index(name='Quantidade')
        fig_semana = px.line(semana, x='Semana', y='Quantidade', title='Atendimentos por Semana')
        st.plotly_chart(fig_semana, use_container_width=True)

        df_final['Dia da Semana'] = df_final['Data Atendimento'].dt.day_name(locale='pt_BR').fillna("Indefinido").str.lower()
        ordem_dias = ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo']
        df_final['Dia da Semana'] = pd.Categorical(df_final['Dia da Semana'], categories=ordem_dias, ordered=True)

        fig_turno = px.histogram(df_final, x='Dia da Semana', color='Turno', barmode='group',
                                 title='Distribuição de Atendimentos por Dia da Semana e Turno')
        st.plotly_chart(fig_turno, use_container_width=True)

    if 'Hora' in df_final.columns:
        fig_hora = px.histogram(df_final, x='Hora', nbins=24, title='Distribuição de Atendimentos por Hora')
        st.plotly_chart(fig_hora, use_container_width=True)

    if 'Especialidade' in df_final.columns and 'Prioridade' in df_final.columns:
        fig_stack = px.histogram(df_final, x='Especialidade', color='Prioridade', barmode='stack',
                                 title='Prioridade por Especialidade')
        st.plotly_chart(fig_stack, use_container_width=True)

    if 'Especialidade' in df_final.columns:
        st.subheader("Resumo por Especialidade")
        resumo_esp = df_final['Especialidade'].value_counts().reset_index()
        resumo_esp.columns = ['Especialidade', 'Quantidade']
        st.dataframe(resumo_esp)

    st.success("✅ Análise concluída com sucesso!")




