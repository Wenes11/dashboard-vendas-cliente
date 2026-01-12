import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dashboard Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CARREGAMENTO E LIMPEZA ---
@st.cache_data
def carregar_dados():
    arquivo = "base_tratada_powerbi.xlsx"
    try:
        df = pd.read_excel(arquivo)
    except FileNotFoundError:
        st.error(f"Erro: Arquivo '{arquivo}' não encontrado.")
        st.stop()

    # Tratamento Monetário
    cols_monetarias = ['VENDAS', 'INV. FACE VENDAS', 'TRAFEGO', 'GADS', 'CAC', 'ROAS']
    for col in cols_monetarias:
        if col in df.columns and df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.replace('R$', '', regex=False)
            df[col] = df[col].str.replace('.', '', regex=False)
            df[col] = df[col].str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Ordenação e Mapa de Meses
    mapa_meses = {'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
                  'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12}
    
    if 'MÊS' in df.columns:
        df['Mes_ID'] = df['MÊS'].astype(str).str.strip().str.lower().str[:3].map(mapa_meses)
        df = df.sort_values('Mes_ID')

    return df

df = carregar_dados()

# --- 3. BARRA LATERAL (FILTROS INTELIGENTES) ---
st.sidebar.header("🎛️ Painel de Controle")

# A. Filtro de Período (Slider)
st.sidebar.subheader("1. Período")
if 'Mes_ID' in df.columns:
    min_id = int(df['Mes_ID'].min())
    max_id = int(df['Mes_ID'].max())
    
    # Dicionário reverso para mostrar nomes no slider (3 -> 'mar')
    nomes_meses = df.set_index('Mes_ID')['MÊS'].to_dict()
    
    id_selecionado = st.sidebar.slider(
        "Selecione o Intervalo:",
        min_value=min_id,
        max_value=max_id,
        value=(min_id, max_id), # Padrão: Começo ao fim
        format="%d" # Apenas visual, o nome aparece abaixo
    )
    
    # Mostra para o usuário o que ele selecionou
    st.sidebar.caption(f"De: **{nomes_meses.get(id_selecionado[0], '?')}** até **{nomes_meses.get(id_selecionado[1], '?')}**")
    
    # Aplica filtro de data
    df_filtrado = df[(df['Mes_ID'] >= id_selecionado[0]) & (df['Mes_ID'] <= id_selecionado[1])].copy()
else:
    df_filtrado = df.copy()

st.sidebar.markdown("---")

# B. Filtro de Canais (Dinâmico)
st.sidebar.subheader("2. Composição de Custo")
st.sidebar.info("Selecione quais investimentos somar:")

canais_map = {
    'Facebook Ads': 'INV. FACE VENDAS',
    'Google Ads': 'GADS',
    'Tráfego Pago': 'TRAFEGO'
}

canais_selecionados = []
for nome, coluna in canais_map.items():
    if st.sidebar.checkbox(nome, value=True): # Todos marcados por padrão
        canais_selecionados.append(coluna)

# Recalcular Investimento Total baseado na escolha
if canais_selecionados:
    df_filtrado['INVESTIMENTO_ADAPTADO'] = df_filtrado[canais_selecionados].sum(axis=1)
else:
    df_filtrado['INVESTIMENTO_ADAPTADO'] = 0

# Recalcular KPIs baseados no novo investimento
# Evitar divisão por zero
df_filtrado['ROAS_REAL'] = df_filtrado.apply(
    lambda x: x['VENDAS'] / x['INVESTIMENTO_ADAPTADO'] if x['INVESTIMENTO_ADAPTADO'] > 0 else 0, axis=1
)
df_filtrado['CAC_REAL'] = df_filtrado.apply(
    lambda x: x['INVESTIMENTO_ADAPTADO'] / x['QUANTIDADE DE CLIENTES'] if x['QUANTIDADE DE CLIENTES'] > 0 else 0, axis=1
)

# --- 4. SIMULADOR (NOVIDADE) ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔮 Simulador de Meta")
investimento_simulado = st.sidebar.number_input("Se eu investir (R$):", value=50000, step=1000)
roas_medio_periodo = df_filtrado['ROAS_REAL'].mean()
projecao_venda = investimento_simulado * roas_medio_periodo

st.sidebar.metric(
    label="Venda Projetada (Baseado no ROAS Atual)",
    value=f"R$ {projecao_venda:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    delta=f"ROAS Médio: {roas_medio_periodo:.2f}x"
)

# --- 5. KPIs DO TOPO ---
st.title("📊 Análise de Performance Dinâmica")

total_vendas = df_filtrado['VENDAS'].sum()
total_inv = df_filtrado['INVESTIMENTO_ADAPTADO'].sum()
roas_periodo = total_vendas / total_inv if total_inv > 0 else 0
cac_periodo = total_inv / df_filtrado['QUANTIDADE DE CLIENTES'].sum() if df_filtrado['QUANTIDADE DE CLIENTES'].sum() > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Faturamento Selecionado", f"R$ {total_vendas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col2.metric("Investimento (Canais Ativos)", f"R$ {total_inv:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col3.metric("ROAS Dinâmico", f"{roas_periodo:.2f}x", delta_color="normal")
col4.metric("CAC Dinâmico", f"R$ {cac_periodo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), delta_color="inverse")

# --- 6. GRÁFICOS ---
st.markdown("---")

tab1, tab2 = st.tabs(["📈 Visão Geral", "🔬 Detalhamento de Canais"])

with tab1:
    # Gráfico Principal: Vendas x Investimento (Comparativo)
    fig_combo = go.Figure()
    
    # Barras: Vendas
    fig_combo.add_trace(go.Bar(
        x=df_filtrado['MÊS'],
        y=df_filtrado['VENDAS'],
        name='Faturamento',
        marker_color='#00FFFF' # Ciano Neon
    ))
    
    # Linha: Investimento Selecionado
    fig_combo.add_trace(go.Scatter(
        x=df_filtrado['MÊS'],
        y=df_filtrado['INVESTIMENTO_ADAPTADO'],
        name='Investimento (Filtro)',
        yaxis='y2',
        line=dict(color='#FF007F', width=3), # Rosa Neon
        mode='lines+markers'
    ))

    fig_combo.update_layout(
        title="Correlação: Quanto coloquei vs. Quanto voltou",
        template="plotly_dark",
        yaxis=dict(title="Faturamento"),
        yaxis2=dict(title="Investimento", overlaying='y', side='right', showgrid=False),
        legend=dict(orientation="h", y=1.1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified"
    )
    st.plotly_chart(fig_combo, use_container_width=True)

with tab2:
    # Gráfico de Rosca: Onde estamos gastando?
    col_rosca1, col_rosca2 = st.columns(2)
    
    with col_rosca1:
        # Soma total dos canais ORIGINAIS (independente do filtro, para contexto)
        totais_canais = {
            'Facebook': df_filtrado['INV. FACE VENDAS'].sum(),
            'Google': df_filtrado['GADS'].sum(),
            'Tráfego': df_filtrado['TRAFEGO'].sum()
        }
        df_pizza = pd.DataFrame(list(totais_canais.items()), columns=['Canal', 'Valor'])
        
        fig_pizza = px.pie(
            df_pizza, values='Valor', names='Canal',
            title="Share de Investimento (No período)",
            template="plotly_dark",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        fig_pizza.update_layout(paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_pizza, use_container_width=True)
        
    with col_rosca2:
        # Gráfico de ROAS Mês a Mês (Barra)
        fig_roas = px.bar(
            df_filtrado, x="MÊS", y="ROAS_REAL",
            title="Eficiência (ROAS) Mensal",
            template="plotly_dark",
            color="ROAS_REAL",
            color_continuous_scale="Blugrn"
        )
        fig_roas.add_hline(y=roas_periodo, line_dash="dot", annotation_text="Média")
        fig_roas.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_roas, use_container_width=True)
