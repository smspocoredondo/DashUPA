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

# 📊 Funções de gráficos
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

# 🚀 Processamento
if uploaded_files:
    dataframes = [processar_planilha(file) for file in uploaded_files]
    df_final = pd.concat(dataframes, ignore_index=True)

    # 🎯 Validação
    colunas_esperadas = ['Especialidade', 'Motivo Alta', 'Usuário', 'Profissional', 'Prioridade', 'Cid10']
    for coluna in colunas_esperadas:
        if coluna not in df_final.columns:
            st.warning(f"A coluna esperada '{coluna}' não foi encontrada.")

    # 🎯 Filtros
    colunas_disponiveis = df_final.columns.tolist()
    filtros = {
        col: st.sidebar.multiselect(f'Filtrar por {col}', df_final[col].unique())
        for col in colunas_disponiveis
    }
    for coluna, filtro in filtros.items():
        if filtro:
            df_final = df_final[df_final[coluna].isin(filtro)]

    # 🔢 Total Geral
    total_atendimentos = len(df_final)
    st.markdown("""
    <style>
    .card-hover {
        transition: box-shadow 0.3s, transform 0.3s;
    }
    .card-hover:hover {
        box-shadow: 0 4px 24px rgba(0,150,136,0.25), 0 1.5px 8px rgba(0,150,136,0.15);
        transform: scale(1.03);
        border-left: 12px solid #1976d2;
        background-color: #e3f2fd;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="card-hover" style="padding:22px; margin-bottom:24px; background-color:#e0f7fa; 
                    border-left:10px solid #009688; border-radius:14px; 
                    font-size:28px; font-weight:bold; color:#009688; 
                    box-shadow: 0 2px 12px rgba(0,150,136,0.10); text-align:center;">
            🏥 Total Geral de Atendimentos: {total_atendimentos}
        </div>
        """,
        unsafe_allow_html=True
    )

    # 🔢 Cards por Especialidade
    if 'Especialidade' in df_final.columns:
        especialidades = df_final['Especialidade'].dropna().unique()
        n = len(especialidades)
        cols = st.columns(n if n < 4 else 4)
        for idx, especialidade in enumerate(especialidades):
            total_especialidade = df_final[df_final['Especialidade'] == especialidade].shape[0]
            cor_card = "#e6f9f0"
            cor_borda = "#009688"
            icone = "🩺" if "Médico" in str(especialidade) or "Clínico" in str(especialidade) else "👩‍⚕️"
            with cols[idx % 4]:
                st.markdown(
                    f"""
                    <div style="padding:18px; margin-bottom:18px; background-color:{cor_card};
                                border-left:7px solid {cor_borda}; border-radius:12px;
                                font-size:20px; font-weight:bold; color:{cor_borda};
                                box-shadow: 0 2px 8px rgba(0,150,136,0.09); text-align:center;">
                        {icone}<br>
                        {especialidade}<br>
                        <span style="font-size:28px; color:#222;">{total_especialidade}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # 📊 Gráficos principais
    colunas_para_analisar = ['Especialidade', 'Motivo Alta', 'Usuário', 'Profissional', 'Prioridade', 'Cid10']
    top_n = st.sidebar.slider("Número de itens no gráfico", 5, 20, 10)
    tipo_grafico = st.sidebar.selectbox("Selecione o tipo de gráfico", ["Barras", "Pizza"])
    for col in colunas_para_analisar:
        if col in df_final.columns:
            st.subheader(f"Análises para {col}")
            if tipo_grafico == "Barras":
                grafico = criar_grafico_barra(df_final, col, f'Top {top_n} {col} Mais Frequentes', top_n)
            elif tipo_grafico == "Pizza":
                grafico = criar_grafico_pizza(df_final, col, f'Top {top_n} {col} Mais Frequentes', top_n)
            if grafico:
                st.plotly_chart(grafico, use_container_width=True)

    # 📈 Série temporal
    if 'Data Atendimento' in df_final.columns:
        df_final['Data Atendimento'] = pd.to_datetime(df_final['Data Atendimento'], errors='coerce')
        data_min, data_max = st.sidebar.date_input("Filtrar por intervalo de datas", [])
        if data_min and data_max:
            df_final = df_final[
                (df_final['Data Atendimento'] >= pd.to_datetime(data_min)) & 
                (df_final['Data Atendimento'] <= pd.to_datetime(data_max))
            ]
        atendimentos_por_data = df_final.groupby('Data Atendimento').size().reset_index(name='Quantidade')
        grafico_temporal = px.line(
            atendimentos_por_data,
            x='Data Atendimento',
            y='Quantidade',
            title='Atendimentos ao Longo do Tempo',
            line_shape='spline',
            markers=True,
            color_discrete_sequence=['#009688']
        )
        grafico_temporal.update_layout(
            title_font=dict(size=20, color='#009688'),
            template='plotly_white'
        )
        st.plotly_chart(grafico_temporal, use_container_width=True)

    # 🕒 Distribuição por Turno
    if 'Hora Atendimento' in df_final.columns:
        df_final['Hora Atendimento'] = pd.to_datetime(df_final['Hora Atendimento'], errors='coerce').dt.time

    def classificar_turno(hora):
        if pd.isna(hora):
            return "Indefinido"
        if hora >= pd.to_datetime("00:00").time() and hora < pd.to_datetime("06:00").time():
            return "Madrugada (00:00-06:00)"
        elif hora < pd.to_datetime("12:00").time():
            return "Manhã (06:00-12:00)"
        elif hora < pd.to_datetime("18:00").time():
            return "Tarde (12:00-18:00)"
        else:
            return "Noite (18:00-00:00)"

    if 'Hora Atendimento' in df_final.columns:
        df_final['Turno'] = df_final['Hora Atendimento'].apply(classificar_turno)

        st.subheader("📈 Distribuição de Atendimentos por Turno")
        graf_turno = px.histogram(
            df_final,
            x='Turno',
            title="Distribuição por Turno",
            color='Turno',
            color_discrete_sequence=px.colors.sequential.Teal
        )
        graf_turno.update_layout(template='plotly_white')
        st.plotly_chart(graf_turno, use_container_width=True)

        # 📊 Comparativo entre Turnos
        st.subheader("📊 Comparativo entre Turnos")
        turno_counts = df_final['Turno'].value_counts().reset_index()
        turno_counts.columns = ['Turno', 'Quantidade']
        turno_counts['Percentual'] = (turno_counts['Quantidade'] / turno_counts['Quantidade'].sum() * 100).round(2)

        col1, col2 = st.columns([2, 1])
        with col1:
            fig_comp_turnos = px.bar(
                turno_counts,
                x='Turno',
                y='Quantidade',
                text='Quantidade',
                title="Comparação de Atendimentos por Turno",
                color='Turno',
                color_discrete_sequence=px.colors.sequential.Tealgrn
            )
            fig_comp_turnos.update_layout(template='plotly_white')
            st.plotly_chart(fig_comp_turnos, use_container_width=True)
        with col2:
            st.markdown("#### 🧾 Tabela Resumo")
            st.dataframe(turno_counts.style.format({'Percentual': '{:.2f}%'}), use_container_width=True)

        # 📊 Gráfico Empilhado: Turno x Especialidade
        if 'Especialidade' in df_final.columns:
            st.subheader("📊 Atendimentos por Especialidade e Turno")
            graf_empilhado = px.histogram(
                df_final,
                x='Especialidade',
                color='Turno',
                title='Especialidades por Turno',
                barmode='stack',
                color_discrete_sequence=px.colors.sequential.Tealgrn
            )
            graf_empilhado.update_layout(
                xaxis_title='Especialidade',
                yaxis_title='Total de Atendimentos',
                template='plotly_white'
            )
            st.plotly_chart(graf_empilhado, use_container_width=True)

    # 📈 Mapa de Correlação
    colunas_numericas = df_final.select_dtypes(include=['number']).columns
    if len(colunas_numericas) > 1:
        st.subheader("Mapa de Correlação")
        correlacao = df_final[colunas_numericas].corr()
        fig_corr = px.imshow(
            correlacao,
            text_auto=True,
            color_continuous_scale=['#e0f2f1', '#4dd0e1', '#009688'],
            title="Correlação entre Variáveis"
        )
        fig_corr.update_layout(template='plotly_white')
        st.plotly_chart(fig_corr, use_container_width=True)

    st.success("Análise concluída com sucesso!")


