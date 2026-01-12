import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dashboard Comercial & Marketing",
    page_icon="🚀",
    layout="wide"
)

# --- 2. CARREGAMENTO E TRATAMENTO DE DADOS ---
@st.cache_data
def carregar_dados():
    arquivo = "base_tratada_powerbi.xlsx"
    
    try:
        df = pd.read_excel(arquivo)
    except FileNotFoundError:
        st.error(f"Erro: O arquivo '{arquivo}' não foi encontrado.")
        st.stop()

    # Tratamento de Vendas e Valores Monetários (Blindagem)
    cols_monetarias = ['VENDAS', 'INV. FACE VENDAS', 'TRAFEGO', 'GADS', 'CAC', 'ROAS']
    
    for col in cols_monetarias:
        if col in df.columns and df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.replace('R$', '', regex=False)
            df[col] = df[col].str.replace('.', '', regex=False)
            df[col] = df[col].str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Ordenação Cronológica dos Meses
    mapa_meses = {
        'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12
    }
    
    # Cria ID para ordenar (ex: mar -> 3)
    if 'MÊS' in df.columns:
        df['Mes_ID'] = df['MÊS'].astype(str).str.strip().str.lower().str[:3].map(mapa_meses)
        df = df.sort_values('Mes_ID')

    # Criar coluna de Investimento Total (se não existir)
    if 'INVESTIMENTO_TOTAL' not in df.columns:
        df['INVESTIMENTO_TOTAL'] = df['INV. FACE VENDAS'] + df['TRAFEGO'] + df['GADS']

    return df

# Carrega os dados
df = carregar_dados()

# --- 3. BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros")
if 'MÊS' in df.columns:
    meses_disponiveis = df['MÊS'].unique()
    mes_selecionado = st.sidebar.multiselect(
        "Selecione o Mês:",
        options=meses_disponiveis,
        default=meses_disponiveis
    )

    if not mes_selecionado:
        df_filtrado = df.copy()
    else:
        df_filtrado = df[df['MÊS'].isin(mes_selecionado)]
else:
    df_filtrado = df.copy()

# --- 4. CÁLCULO DE KPIs ---
total_vendas = df_filtrado['VENDAS'].sum()
investimento_total = df_filtrado['INVESTIMENTO_TOTAL'].sum()
total_clientes = df_filtrado['QUANTIDADE DE CLIENTES'].sum()

# Evitar divisão por zero
roas_geral = total_vendas / investimento_total if investimento_total > 0 else 0
cac_geral = investimento_total / total_clientes if total_clientes > 0 else 0

# --- 5. LAYOUT PRINCIPAL (KPIs) ---
st.title("📊 Painel Estratégico de Vendas")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Faturamento", f"R$ {total_vendas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col2.metric("ROAS Geral", f"{roas_geral:.2f}x")
col3.metric("CAC Médio", f"R$ {cac_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col4.metric("Novos Clientes", int(total_clientes))

st.markdown("---")

# --- 6. GRÁFICO DE EVOLUÇÃO (VENDAS) ---
st.subheader("📈 Evolução de Vendas")
df_chart = df_filtrado.sort_values("Mes_ID")

fig_vendas = px.area(
    df_chart, x="MÊS", y="VENDAS",
    markers=True,
    template="plotly_dark"
)
fig_vendas.update_traces(line_color='#00FFFF', fillcolor='rgba(0, 255, 255, 0.2)')
fig_vendas.update_yaxes(tickprefix="R$ ")
fig_vendas.update_layout(xaxis_title=None, yaxis_title="Faturamento", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

st.plotly_chart(fig_vendas, use_container_width=True)

# --- 7. ANÁLISE AVANÇADA (NOVO!) ---
st.markdown("---")
st.header("🚀 Eficiência e Escala")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Matriz de Escala (Investimento x ROAS)")
    # Gráfico de Dispersão
    fig_scatter = px.scatter(
        df_filtrado,
        x="INVESTIMENTO_TOTAL",
        y="ROAS",
        size="VENDAS",
        color="MÊS",
        template="plotly_dark",
        labels={"INVESTIMENTO_TOTAL": "Investimento Total (R$)", "ROAS": "ROAS (Múltiplo)"}
    )
    # Linha de média
    media_roas = df_filtrado['ROAS'].mean()
    fig_scatter.add_hline(y=media_roas, line_dash="dot", annotation_text="Média ROAS")
    
    fig_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.info("🎯 **Objetivo:** Bolhas no topo direito (Alto Investimento e Alto ROAS).")

with col_right:
    st.subheader("Funil: Leads vs Conversão")
    # Gráfico de Eixo Duplo
    fig_dual = go.Figure()

    # Barras (Leads)
    fig_dual.add_trace(go.Bar(
        x=df_chart['MÊS'],
        y=df_chart['LEADS FACE'],
        name='Leads',
        marker_color='#1f77b4',
        opacity=0.6
    ))

    # Linha (Conversão)
    fig_dual.add_trace(go.Scatter(
        x=df_chart['MÊS'],
        y=df_chart['TX CONVERSÃO'] * 100, # Converter para %
        name='Taxa Conv. (%)',
        yaxis='y2',
        line=dict(color='#FF4500', width=3),
        mode='lines+markers'
    ))

    fig_dual.update_layout(
        template="plotly_dark",
        yaxis=dict(title="Volume de Leads"),
        yaxis2=dict(title="Conversão (%)", overlaying='y', side='right', showgrid=False),
        legend=dict(orientation="h", y=1.1),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_dual, use_container_width=True)
    st.warning("⚠️ **Atenção:** Se a barra azul sobe e a linha laranja cai, a qualidade do lead piorou.")
