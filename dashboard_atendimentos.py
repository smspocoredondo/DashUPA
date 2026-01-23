import streamlit as st
import pandas as pd
import plotly.express as px

# ===============================
# CONFIGURAÇÃO DA PÁGINA
# ===============================
st.set_page_config(
    page_title='Painel de Resolutividade – UPA Dona Zulmira Soares',
    layout='wide'
)

st.image('TESTEIRA PAINEL UPA1.png', width=120)
st.title('Painel de Avaliação de Resolutividade – UPA 24h Dona Zulmira Soares')

# ===============================
# SIDEBAR
# ===============================
st.sidebar.image('TESTEIRA PAINEL UPA1.png', width=300)
st.sidebar.header('Upload e Filtros')

uploaded_files = st.sidebar.file_uploader(
    'Envie as planilhas de atendimentos',
    type=['xlsx'],
    accept_multiple_files=True
)

# ===============================
# FUNÇÃO DE LEITURA DA PLANILHA
# ===============================
def processar_planilha(file):
    df = pd.read_excel(file, skiprows=1, header=None)
    df = df.dropna(how='all')

    df.columns = [
        'CPF', 'Paciente', 'Data', 'Hora', 'Especialidade',
        'Profissional', 'Motivo Alta', 'Procedimento',
        'Cid10', 'Prioridade'
    ]

    # Padronizações críticas
    df['Motivo Alta'] = df['Motivo Alta'].astype(str).str.strip().str.upper()
    df['Prioridade'] = df['Prioridade'].astype(str).str.strip().str.upper()
    df['Cid10'] = df['Cid10'].astype(str).str.upper().str[:3]

    return df

# ===============================
# PROCESSAMENTO
# ===============================
if uploaded_files:
    dfs = [processar_planilha(f) for f in uploaded_files]
    df_final = pd.concat(dfs, ignore_index=True)

    # -------------------------------
    # FILTROS DINÂMICOS
    # -------------------------------
    for col in ['Especialidade', 'Profissional', 'Prioridade']:
        valores = sorted(df_final[col].dropna().unique())
        filtro = st.sidebar.multiselect(f'Filtrar por {col}', valores)
        if filtro:
            df_final = df_final[df_final[col].isin(filtro)]

    # -------------------------------
    # DATA E TURNO
    # -------------------------------
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
    # RESOLUTIVIDADE – REGRA REALISTA
    # ===============================
    def classificar_resolutividade(motivo):
        if pd.isnull(motivo):
            return 'Indefinido'

        m = motivo.lower()

        resolvido = [
            'alta médica', 'alta com prescrição',
            'alta após observação', 'encaminhado para ubs'
        ]

        nao_resolvido = [
            'transferência', 'regulação',
            'internação', 'óbito', 'evasão'
        ]

        if any(x in m for x in resolvido):
            return 'Resolvido na UPA'
        if any(x in m for x in nao_resolvido):
            return 'Não resolvido na UPA'

        return 'Indefinido'

    df_final['Resolutividade'] = df_final['Motivo Alta'].apply(classificar_resolutividade)

    # ===============================
    # INDICADORES PRINCIPAIS
    # ===============================
    total = len(df_final)

    taxa_resolucao = (
        len(df_final[df_final['Resolutividade'] == 'Resolvido na UPA']) / total
    )

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

    perfil_risco = df_final['Prioridade'].value_counts(normalize=True) * 100
    verde_azul = perfil_risco.filter(like='VERDE').sum() + perfil_risco.filter(like='AZUL').sum()

    # Transferência potencialmente evitável
    transf_ev = df_final[
        (df_final['Resolutividade'] == 'Não resolvido na UPA') &
        (df_final['Prioridade'].str.contains('VERDE|AMARELO', na=False))
    ]

    taxa_transf_ev = len(transf_ev) / total

    # ===============================
    # SCORE DE RESOLUTIVIDADE
    # ===============================
    score = (
        taxa_resolucao * 0.4 +
        (1 - taxa_retorno) * 0.2 +
        taxa_amarelo * 0.4
    )

    if score >= 0.80:
        status = '🟢 UPA RESOLUTIVA'
    elif score >= 0.60:
        status = '🟡 PARCIALMENTE RESOLUTIVA'
    else:
        status = '🔴 BAIXA RESOLUTIVIDADE'

    # ===============================
    # PAINEL GERENCIAL
    # ===============================
    st.markdown('## 🏥 Indicadores de Resolutividade – SUS')

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric('Resolução na UPA', f'{taxa_resolucao:.1%}', 'Meta ≥ 85%')
    c2.metric('Retorno ≤ 72h', f'{taxa_retorno:.1%}', 'Ideal < 5%')
    c3.metric('Resolução Amarelos', f'{taxa_amarelo:.1%}', 'Meta ≥ 80%')
    c4.metric('Transferências Evitáveis', f'{taxa_transf_ev:.1%}', '< 10%')
    c5.metric('Score Geral', f'{score:.2f}', status)

    if verde_azul > 60:
        st.warning(
            f'⚠️ {verde_azul:.1f}% dos atendimentos são Verde/Azul — possível sobrecarga da Atenção Básica.'
        )

    # ===============================
    # RESOLUTIVIDADE POR CID-10
    # ===============================
    st.markdown('## 🧬 Resolutividade por CID-10')

    cid_res = (
        df_final.groupby(['Cid10', 'Resolutividade'])
        .size()
        .unstack(fill_value=0)
    )

    cid_res['Taxa Resolutividade'] = (
        cid_res.get('Resolvido na UPA', 0) /
        cid_res.sum(axis=1)
    )

    st.dataframe(
        cid_res.sort_values('Taxa Resolutividade', ascending=False).head(15),
        use_container_width=True
    )

    # ===============================
    # PRODUÇÃO POR PROFISSIONAL
    # ===============================
    st.markdown('## 👩‍⚕️ Produção por Profissional × Desfecho')

    prof_res = (
        df_final.groupby(['Profissional', 'Resolutividade'])
        .size()
        .unstack(fill_value=0)
    )

    st.dataframe(prof_res, use_container_width=True)

    # ===============================
    # CONCLUSÃO TÉCNICA
    # ===============================
    if taxa_resolucao >= 0.85 and taxa_retorno < 0.05:
        parecer = (
            'A UPA apresenta adequada capacidade resolutiva, em conformidade '
            'com a Política Nacional de Atenção às Urgências.'
        )
    elif taxa_resolucao >= 0.60:
        parecer = (
            'A UPA apresenta resolutividade parcial, sendo recomendados ajustes '
            'organizacionais e clínico-assistenciais.'
        )
    else:
        parecer = (
            'A UPA apresenta baixa resolutividade, indicando necessidade de '
            'reavaliação dos fluxos assistenciais e da articulação com a rede.'
        )

    st.markdown(f"""
### 📝 Conclusão Técnica

**Classificação Final:** **{status}**

{parecer}

Avaliação baseada em indicadores assistenciais, conforme a PNAU e diretrizes do SUS,
com dados extraídos dos registros reais de atendimento da unidade.
""")

    st.success('✅ Avaliação concluída com sucesso.')










