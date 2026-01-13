import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64

# --- 1. CONFIGURAÇÃO GERAL ---
st.set_page_config(
    page_title="Dashboard Quad Code",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CORES ---
COR_VERDE = "#00C853"        # Verde Neon
COR_AZUL = "#2979FF"         # Azul Tech
COR_CINZA_CHECKBOX = "#404040" # Cinza Escuro
COR_CINZA_GRAFICO = "#B0BEC5" # Cinza Claro
COR_FUNDO_DARK = "#000000"   # Preto Absoluto

# --- CSS VISUAL ---
def set_style(image_file):
    try:
        with open(image_file, "rb") as f:
            data = f.read()
        bin_str = base64.b64encode(data).decode()
        bg_image_css = f'url("data:image/png;base64,{bin_str}")'
    except:
        bg_image_css = "none"

    style = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Montserrat', sans-serif;
    }}

    .stApp {{
        background-color: {COR_FUNDO_DARK};
        background-image: {bg_image_css};
        background-size: cover;
        background-attachment: fixed;
        color: white !important;
    }}
    
    /* GLOBAL: Força textos comuns a serem brancos */
    h1, h2, h3, h4, h5, h6, p, label, li {{
        color: white !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: #050505 !important;
        border-right: 1px solid #222;
    }}

    /* CHECKBOX */
    .stCheckbox {{ background-color: transparent !important; }}
    .stCheckbox label {{ background-color: transparent !important; }}
    
    /* Desmarcado */
    .stCheckbox div[role="checkbox"] {{
        background-color: transparent !important; 
        border: 1px solid #AAA !important;
    }}
    .stCheckbox input + div {{
        background-color: transparent !important;
        border: 1px solid #AAA !important;
    }}

    /* Marcado */
    .stCheckbox input:checked + div {{
        background-color: {COR_CINZA_CHECKBOX} !important;
        border: 1px solid {COR_CINZA_CHECKBOX} !important;
    }}
    .stCheckbox input:checked + div svg {{
        fill: white !important;
    }}
    
    /* SLIDER */
    div[data-testid="stSliderTickBarMin"], div[data-testid="stSliderTickBarMax"] {{
        color: #FFFFFF !important;
    }}
    div[data-baseweb="slider"] > div {{
        background-color: #333 !important;
    }}
    div[data-baseweb="slider"] div[style*="width"] {{
        background-color: {COR_VERDE} !important;
    }}
    div[data-baseweb="slider"] div[role="slider"] {{
        background-color: white !important;
        border: 2px solid {COR_VERDE} !important;
    }}

    /* INPUTS */
    div[data-baseweb="input"] {{
        background-color: #FFFFFF !important;
        border-radius: 5px !important;
    }}
    input[type="number"] {{
        color: #000000 !important;
        font-weight: 800 !important;
        background-color: transparent !important;
        -webkit-text-fill-color: #000000 !important;
    }}

    /* KPIS */
    div[data-testid="stMetric"] {{
        background-color: rgba(15, 15, 15, 0.9);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 15px;
    }}
    div[data-testid="stMetricLabel"] label {{ color: #CCC !important; }}
    div[data-testid="stMetricValue"] {{ color: white !important; }}

    header[data-testid="stHeader"] {{ visibility: visible !important; background-color: transparent !important; }}
    div[data-testid="stDecoration"] {{ display: none; }}
    header[data-testid="stHeader"] button, header[data-testid="stHeader"] .stAction {{ color: white !important; }}
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

set_style('fundo.jpg')

# --- FUNÇÃO FORMATAR MOEDA BR ---
def fmt(valor):
    return f"R$ {valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- DADOS ---
@st.cache_data
def carregar_dados():
    try: df = pd.read_excel("base_tratada_powerbi.xlsx")
    except: st.stop()
    
    cols = ['VENDAS', 'INV. FACE VENDAS', 'TRAFEGO', 'GADS', 'CAC', 'ROAS']
    for col in cols:
        if col in df.columns and df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    mapa = {'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6, 'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12}
    if 'MÊS' in df.columns:
        df['Mes_ID'] = df['MÊS'].astype(str).str.strip().str.lower().str[:3].map(mapa)
        df = df.sort_values('Mes_ID')
    return df

df = carregar_dados()

# --- SIDEBAR ---
try: st.sidebar.image("logo.png", use_container_width=True)
except: pass

st.sidebar.markdown("### 🎛️ Filtros")

# Filtro Data
if 'Mes_ID' in df.columns:
    min_id, max_id = int(df['Mes_ID'].min()), int(df['Mes_ID'].max())
    nomes = df.set_index('Mes_ID')['MÊS'].to_dict()
    
    st.sidebar.markdown("**Período**")
    id_sele = st.sidebar.slider("filtro_data", min_id, max_id, (min_id, max_id), label_visibility="collapsed")
    st.sidebar.markdown(f"🗓️ **{nomes.get(id_sele[0], '?').upper()}** até **{nomes.get(id_sele[1], '?').upper()}**")
    df_f = df[(df['Mes_ID'] >= id_sele[0]) & (df['Mes_ID'] <= id_sele[1])].copy()
else:
    df_f = df.copy()

st.sidebar.markdown("---")

# Filtro Canais
st.sidebar.markdown("**Canais de Mídia**")
canais = {'Facebook Ads': 'INV. FACE VENDAS', 'Google Ads': 'GADS', 'Outros': 'TRAFEGO'}
sel_canais = []
for n, c in canais.items():
    if st.sidebar.checkbox(n, value=True):
        sel_canais.append(c)
df_f['INVESTIMENTO_ADAPTADO'] = df_f[sel_canais].sum(axis=1) if sel_canais else 0

# --- SIMULADOR CORRIGIDO (SEM IDENTAÇÃO PARA NÃO QUEBRAR O HTML) ---
st.sidebar.markdown("---")
st.sidebar.markdown("**Simulador de Meta** 🔮")

inv_sim = st.sidebar.number_input("Digite o Investimento (R$)", value=5000, step=1000)

roas_medio = df_f['VENDAS'].sum() / df_f['INVESTIMENTO_ADAPTADO'].sum() if df_f['INVESTIMENTO_ADAPTADO'].sum() > 0 else 0
fat_proj = inv_sim * roas_medio
lucro_proj = fat_proj - inv_sim

# AQUI ESTAVA O ERRO: IDENTAÇÃO. O CÓDIGO ABAIXO ESTÁ COLADO NA ESQUERDA.
# E TROCAMOS <P> POR <DIV/SPAN> PARA FUGIR DO CSS GLOBAL BRANCO.
html_simulador = f"""
<div style="background-color:#FFFFFF; padding:15px; border-radius:10px; border:1px solid #CCC; margin-top:10px;">
<span style="color:#666 !important; font-size:10px; font-weight:700; text-transform:uppercase; display:block;">FATURAMENTO PROJETADO</span>
<span style="color:#000000 !important; font-size:24px; font-weight:800; display:block; margin-top:5px;">{fmt(fat_proj)}</span>
<div style="border-top:1px solid #EEE; margin:10px 0;"></div>
<span style="color:#666 !important; font-size:10px; font-weight:700; text-transform:uppercase; display:block;">LUCRO ESTIMADO</span>
<span style="color:{COR_VERDE} !important; font-size:18px; font-weight:700; display:block; margin-top:5px;">{fmt(lucro_proj)}</span>
</div>
"""
st.sidebar.markdown(html_simulador, unsafe_allow_html=True)

# --- KPI PRINCIPAL ---
st.title("📊 Painel Estratégico")

vendas = df_f['VENDAS'].sum()
inv = df_f['INVESTIMENTO_ADAPTADO'].sum()
lucro = vendas - inv
roas = vendas / inv if inv > 0 else 0

def kpi(label, val, cor_borda):
    st.markdown(f"""
    <div style="background-color:rgba(0,0,0,0.7);padding:15px;border-radius:10px;border-left:5px solid {cor_borda};margin-bottom:10px;">
        <span style="color:#BBB;font-size:12px;font-weight:600;text-transform:uppercase;">{label}</span><br>
        <span style="color:white;font-size:26px;font-weight:700;">{val}</span>
    </div>
    """, unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1: kpi("FATURAMENTO", fmt(vendas), COR_VERDE)
with c2: kpi("INVESTIMENTO", fmt(inv), COR_VERDE) 
with c3: kpi("LUCRO BRUTO", fmt(lucro), COR_VERDE)
with c4: kpi("ROAS", f"{roas:.2f}x", COR_AZUL)

st.markdown("---")
tab1, tab2 = st.tabs(["Tendência", "Financeiro"])

def tema(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        title_font=dict(color="white"),
        legend_font=dict(color="white"),
        xaxis=dict(showgrid=False, color="white", title_font=dict(color="white"), tickfont=dict(color="white")),
        yaxis=dict(showgrid=True, gridcolor="#333", color="white", title_font=dict(color="white"), tickfont=dict(color="white")),
    )
    return fig

with tab1:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df_f['MÊS'], y=df_f['INVESTIMENTO_ADAPTADO'], name='Investimento', marker_color=COR_CINZA_GRAFICO, opacity=0.6))
    fig.add_trace(go.Scatter(x=df_f['MÊS'], y=df_f['VENDAS'], name='Vendas', yaxis='y2', mode='lines+markers',
                             line=dict(color=COR_AZUL, width=4), marker=dict(color='white', size=6)))
    fig.update_layout(title="Vendas vs. Investimento", yaxis2=dict(overlaying='y', side='right', showgrid=False), legend=dict(orientation="h", y=1.1, font=dict(color="white")))
    st.plotly_chart(tema(fig), use_container_width=True)
    st.caption("ℹ️ **Análise:** Compare a evolução das Vendas (Linha Azul) em relação ao Investimento (Barras Cinzas).")

with tab2:
    c_a, c_b = st.columns(2)
    with c_a:
        totais = {k: df_f[v].sum() for k,v in canais.items() if v in df.columns}
        fig_p = px.pie(pd.DataFrame(list(totais.items()), columns=['C', 'V']), values='V', names='C', title="Mix de Mídia", hole=0.5)
        st.plotly_chart(tema(fig_p), use_container_width=True)
        st.caption("ℹ️ **Análise:** Distribuição do orçamento entre os canais.")
        
    with c_b:
        df_f['L'] = df_f['VENDAS'] - df_f['INVESTIMENTO_ADAPTADO']
        fig_l = go.Figure(go.Bar(x=df_f['MÊS'], y=df_f['L'], marker_color=COR_VERDE, name="Lucro"))
        fig_l.update_layout(title="Lucro Líquido")
        st.plotly_chart(tema(fig_l), use_container_width=True)
        st.caption("ℹ️ **Análise:** Sobra de caixa após descontar o investimento.")
