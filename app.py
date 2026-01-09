import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Vendas",
    page_icon="💰",
    layout="wide"
)

# --- 2. FUNÇÃO DE LIMPEZA E CARREGAMENTO ---
@st.cache_data
def carregar_dados():
    # Tenta ler o arquivo (seja ele o tratado ou o original)
    # Sugestão: Use o arquivo que geramos antes, mas vamos garantir a limpeza aqui também
    arquivo = "base_tratada_powerbi.xlsx" 
    
    try:
        df = pd.read_excel(arquivo)
    except FileNotFoundError:
        st.error(f"Erro: O arquivo '{arquivo}' não foi encontrado. Verifique se ele está na mesma pasta do app.py")
        st.stop()

    # --- TRATAMENTO DE VENDAS (Blindagem) ---
    # Se a coluna VENDAS vier como texto (com R$), vamos limpar
    if df['VENDAS'].dtype == 'object':
        df['VENDAS'] = df['VENDAS'].astype(str).str.replace('R$', '', regex=False)
        df['VENDAS'] = df['VENDAS'].str.replace('.', '', regex=False) # Tira ponto de milhar
        df['VENDAS'] = df['VENDAS'].str.replace(',', '.', regex=False) # Troca virgula por ponto
        df['VENDAS'] = pd.to_numeric(df['VENDAS'], errors='coerce').fillna(0)

    # --- ORDENAÇÃO DOS MESES ---
    mapa_meses = {
        'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12
    }
    
    # Cria uma coluna de ID para ordenar (ex: mar -> 3)
    # .strip() tira espaços, .lower() deixa minusculo, .slice(0,3) pega as 3 primeiras letras
    df['Mes_ID'] = df['MÊS'].astype(str).str.strip().str.lower().str[:3].map(mapa_meses)
    df = df.sort_values('Mes_ID') # Ordena a tabela cronologicamente

    return df

# Carrega os dados
df = carregar_dados()

# --- 3. BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros")
meses_disponiveis = df['MÊS'].unique()
mes_selecionado = st.sidebar.multiselect(
    "Selecione o Mês:",
    options=meses_disponiveis,
    default=meses_disponiveis # Já inicia com todos marcados
)

# Aplica o filtro
if not mes_selecionado:
    df_filtrado = df.copy()
else:
    df_filtrado = df[df['MÊS'].isin(mes_selecionado)]

# --- 4. CÁLCULOS DOS KPIs ---
total_vendas = df_filtrado['VENDAS'].sum()
# Formatação Brasileira para o Cartão (R$ 1.000,00)
vendas_formatado = f"R$ {total_vendas:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

ticket_medio = df_filtrado['VENDAS'].mean()
ticket_formatado = f"R$ {ticket_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

total_clientes = int(df_filtrado['QUANTIDADE DE CLIENTES'].sum())

# --- 5. LAYOUT DO DASHBOARD ---
st.title("📊 Painel de Vendas")
st.markdown("---")

# Colunas dos KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Faturamento Total", vendas_formatado)
col2.metric("Ticket Médio", ticket_formatado)
col3.metric("Total Clientes", total_clientes)

st.markdown("---")

# --- 6. GRÁFICO DE VENDAS ---
# Garante que o gráfico obedeça a ordem dos meses (Mes_ID)
df_chart = df_filtrado.sort_values("Mes_ID")

fig = px.area(
    df_chart,
    x="MÊS",
    y="VENDAS",
    title="Evolução de Vendas (R$)",
    markers=True,
    template="plotly_dark"
)

# Customização Visual (Estilo Neon)
fig.update_traces(
    line_color='#00FFFF', # Ciano Neon
    fillcolor='rgba(0, 255, 255, 0.2)', # Transparencia
    hovertemplate='Mês: %{x}<br>Vendas: R$ %{y:,.2f}' # Tooltip bonito com R$
)

fig.update_layout(
    xaxis_title=None, # Remove titulo eixo X
    yaxis_title="Faturamento",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(size=14, color="white")
)

# Ajuste do Eixo Y para mostrar R$ no gráfico
fig.update_yaxes(tickprefix="R$ ")

st.plotly_chart(fig, use_container_width=True)