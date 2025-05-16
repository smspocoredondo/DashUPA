import streamlit as st
import pandas as pd

# 🧾 Configuração da Página
title = 'Análises de Atendimentos - UPA 24H Dona Zulmira Soares'
st.set_page_config(page_title=title, layout='wide')
st.image('UPA.png', width=100)
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

# 🎨 Função para escolher cor e ícone por coluna
def get_card_style(coluna, valor):
    cores = {
        'Especialidade':      ("#e6f9f0", "#009688", "🩺"),
        'Motivo Alta':        ("#e3f2fd", "#1976d2", "✅"),
        'Usuário':            ("#f1f8e9", "#388e3c", "🙍‍♂️"),
        'Profissional':       ("#fffde7", "#fbc02d", "👨‍⚕️"),
        'Prioridade':         ("#fce4ec", "#d81b60", "⚡"),
        'Cid10':              ("#ede7f6", "#7b1fa2", "🔖"),
        'default':            ("#f5f5f5", "#607d8b", "📋"),
    }
    cor_card, cor_borda, icone = cores.get(coluna, cores['default'])
    if coluna == "Especialidade" or coluna == "Profissional":
        valor_str = str(valor)
        if "Médico" in valor_str or "Clínico" in valor_str:
            icone = "🩺"
        elif "Enferm" in valor_str:
            icone = "👩‍⚕️"
        elif "Odonto" in valor_str:
            icone = "🦷"
        elif "Social" in valor_str or "Assistente" in valor_str:
            icone = "🧑‍💼"
    return cor_card, cor_borda, icone

# 🚀 Processamento ao carregar arquivos
if uploaded_files:
    dataframes = [processar_planilha(file) for file in uploaded_files]
    df_final = pd.concat(dataframes, ignore_index=True)

    # 🎯 Filtros dinâmicos
    colunas_disponiveis = df_final.columns.tolist()
    filtros = {
        col: st.sidebar.multiselect(f'Filtrar por {col}', df_final[col].unique())
        for col in colunas_disponiveis
    }
    for coluna, filtro in filtros.items():
        if filtro:
            df_final = df_final[df_final[coluna].isin(filtro)]

    # 🔢 Card do total geral
    total_atendimentos = len(df_final)
    st.markdown(
        f"""
        <div style="padding:22px; margin-bottom:24px; background-color:#e0f7fa; 
                    border-left:10px solid #009688; border-radius:14px; 
                    font-size:28px; font-weight:bold; color:#009688; 
                    box-shadow: 0 2px 12px rgba(0,150,136,0.10); text-align:center;">
            💧 Total Geral de Atendimentos: {total_atendimentos}
        </div>
        """,
        unsafe_allow_html=True
    )

    # 🔢 Cards para cada coluna de interesse (Usuário removido)
    colunas_para_analisar = ['Especialidade', 'Motivo Alta', 'Profissional', 'Prioridade', 'Cid10']
    for coluna in colunas_para_analisar:
        if coluna in df_final.columns:
            if coluna == "Profissional":
                st.markdown(f"<h3 style='color:#fbc02d; margin-top:32px;'>Total por Profissional (Categorias)</h3>", unsafe_allow_html=True)
                # Agrupando profissionais por categorias comuns
                categorias_profissionais = {
                    "Médicos": ["Médico", "Clínico"],
                    "Enfermagem": ["Enferm", "Técnico de Enfermagem", "Enfermeiro"],
                    "Odontologia": ["Odonto"],
                    "Assistente Social": ["Social", "Assistente"],
                }
                outros = []
                for cat_nome, palavras in categorias_profissionais.items():
                    total = df_final[coluna].dropna().apply(lambda x: any(p in str(x) for p in palavras)).sum()
                    if total > 0:
                        cor_card, cor_borda, icone = get_card_style(coluna, cat_nome)
                        with st.container():
                            st.markdown(
                                f"""
                                <div style="padding:18px; margin-bottom:12px; background-color:{cor_card};
                                            border-left:7px solid {cor_borda}; border-radius:14px;
                                            font-size:20px; font-weight:bold; color:{cor_borda};
                                            box-shadow: 0 2px 12px rgba(251,192,45,0.08); text-align:left;">
                                    <span style="font-size:32px;">{icone}</span>
                                    <span style="margin-left:12px;">{cat_nome}</span><br>
                                    <span style="font-size:28px; color:#222;">{total}</span>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                # Profissionais não classificados nas categorias acima
                classificados = [palavra for palavras in categorias_profissionais.values() for palavra in palavras]
                for prof in df_final[coluna].dropna().unique():
                    if not any(p in str(prof) for p in classificados):
                        outros.append(prof)
                if outros:
                    st.markdown("<b>Outros Profissionais:</b>", unsafe_allow_html=True)
                    cols = st.columns(len(outros) if len(outros) < 4 else 4)
                    for idx, prof in enumerate(outros):
                        total = df_final[df_final[coluna] == prof].shape[0]
                        cor_card, cor_borda, icone = get_card_style(coluna, prof)
                        with cols[idx % 4]:
                            st.markdown(
                                f"""
                                <div style="padding:14px; margin-bottom:10px; background-color:{cor_card};
                                            border-left:7px solid {cor_borda}; border-radius:12px;
                                            font-size:16px; font-weight:bold; color:{cor_borda};
                                            box-shadow: 0 2px 8px rgba(251,192,45,0.07); text-align:center;">
                                    <span style="font-size:28px;">{icone}</span><br>
                                    <span>{prof}</span><br>
                                    <span style="font-size:22px; color:#222;">{total}</span>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
            else:
                st.subheader(f"Top 10 - Totais por {coluna}")
                top_categorias = df_final[coluna].value_counts().head(10).index.tolist()
                n = len(top_categorias)
                cols = st.columns(n if n < 4 else 4)
                for idx, categoria in enumerate(top_categorias):
                    total_categoria = df_final[df_final[coluna] == categoria].shape[0]
                    cor_card, cor_borda, icone = get_card_style(coluna, categoria)
                    cat_str = str(categoria)
                    with cols[idx % 4]:
                        st.markdown(
                            f"""
                            <div style="padding:18px; margin-bottom:18px; background-color:{cor_card};
                                        border-left:7px solid {cor_borda}; border-radius:14px;
                                        font-size:20px; font-weight:bold; color:{cor_borda};
                                        box-shadow: 0 2px 12px rgba(0,150,136,0.08); text-align:center;">
                                <span style="font-size:32px;">{icone}</span><br>
                                <span>{cat_str}</span><br>
                                <span style="font-size:28px; color:#222;">{total_categoria}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

    st.success("Análise concluída com sucesso!")
