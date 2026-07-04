import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime, date
from pathlib import Path
import pandas as pd
import time

# ============== CONFIGURAÇÃO INICIAL ==============
DB_FILE = "marmed.db"

# Cores do tema
COR_FUNDO = "#0a0e27"
COR_FUNDO2 = "#0d2137"
COR_CIANO = "#00d4ff"
COR_DOURADO = "#ffd700"
COR_TEXTO = "#e6f7ff"
COR_CARD = "rgba(16, 30, 66, 0.65)"
COR_CARD_BORDA = "rgba(0, 212, 255, 0.25)"

# ============== CSS GLOBAL ==============
CSS_GLOBAL = f"""
<style>
/* Reset básico */
html, body, .stApp, [data-testid="stAppViewContainer"] {{
    background: linear-gradient(135deg, {COR_FUNDO} 0%, {COR_FUNDO2} 100%) !important;
    color: {COR_TEXTO} !important;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    overflow-x: hidden;
}}

/* Container principal */
[data-testid="stAppViewContainer"] > .main {{
    background: transparent !important;
}}

/* Animação de partículas no fundo */
.particulas {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}}
.particulas span {{
    position: absolute;
    display: block;
    width: 6px;
    height: 6px;
    background: {COR_CIANO};
    border-radius: 50%;
    opacity: 0.35;
    animation: flutuar 18s linear infinite;
    bottom: -10px;
}}
.particulas span:nth-child(1) {{ left: 10%; animation-duration: 14s; animation-delay: 0s; width: 4px; height: 4px; }}
.particulas span:nth-child(2) {{ left: 20%; animation-duration: 22s; animation-delay: 2s; width: 8px; height: 8px; opacity: 0.25; }}
.particulas span:nth-child(3) {{ left: 30%; animation-duration: 16s; animation-delay: 4s; }}
.particulas span:nth-child(4) {{ left: 40%; animation-duration: 24s; animation-delay: 1s; width: 3px; height: 3px; }}
.particulas span:nth-child(5) {{ left: 50%; animation-duration: 19s; animation-delay: 6s; width: 7px; height: 7px; opacity: 0.2; }}
.particulas span:nth-child(6) {{ left: 60%; animation-duration: 13s; animation-delay: 3s; }}
.particulas span:nth-child(7) {{ left: 70%; animation-duration: 21s; animation-delay: 5s; width: 5px; height: 5px; }}
.particulas span:nth-child(8) {{ left: 80%; animation-duration: 17s; animation-delay: 7s; }}
.particulas span:nth-child(9) {{ left: 90%; animation-duration: 25s; animation-delay: 2s; width: 4px; height: 4px; opacity: 0.3; }}
.particulas span:nth-child(10) {{ left: 5%; animation-duration: 20s; animation-delay: 8s; width: 6px; height: 6px; }}
.particulas span:nth-child(11) {{ left: 15%; animation-duration: 15s; animation-delay: 10s; width: 3px; height: 3px; }}
.particulas span:nth-child(12) {{ left: 85%; animation-duration: 23s; animation-delay: 9s; width: 5px; height: 5px; opacity: 0.22; }}

@keyframes flutuar {{
    0% {{ transform: translateY(0) translateX(0); opacity: 0; }}
    10% {{ opacity: 0.4; }}
    90% {{ opacity: 0.4; }}
    100% {{ transform: translateY(-110vh) translateX(30px); opacity: 0; }}
}}

/* Glassmorphism */
.glass-card {{
    background: {COR_CARD} !important;
    backdrop-filter: blur(14px) saturate(140%) !important;
    -webkit-backdrop-filter: blur(14px) saturate(140%) !important;
    border: 1px solid {COR_CARD_BORDA} !important;
    border-radius: 18px !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35) !important;
    padding: 24px !important;
    transition: all 0.3s ease !important;
}}
.glass-card:hover {{
    border-color: rgba(0, 212, 255, 0.55) !important;
    box-shadow: 0 0 25px rgba(0, 212, 255, 0.15) !important;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: rgba(8, 15, 38, 0.82) !important;
    backdrop-filter: blur(16px) !important;
    border-right: 1px solid rgba(0, 212, 255, 0.18) !important;
}}
[data-testid="stSidebar"] .css-1v3fvcr, [data-testid="stSidebar"] .css-163ttxy, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {{
    color: {COR_TEXTO} !important;
}}

/* Títulos */
h1, h2, h3, h4, h5, h6 {{
    color: {COR_TEXTO} !important;
    font-weight: 600 !important;
}}

/* Textos */
.css-10trblm, .css-1q8dd3e, p, label, .stMarkdown, .stTextInput label, .stSelectbox label, .stDateInput label, .stNumberInput label {{
    color: {COR_TEXTO} !important;
}}

/* Inputs */
input[type="text"], input[type="password"], input[type="number"], input[type="date"], .stTextInput input, .stSelectbox div[data-baseweb="select"], .stDateInput input, .stNumberInput input {{
    background: rgba(0, 0, 0, 0.35) !important;
    color: {COR_TEXTO} !important;
    border: 1px solid rgba(0, 212, 255, 0.25) !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
}}
input[type="text"]:focus, input[type="password"]:focus, input[type="number"]:focus, input[type="date"]:focus, .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus, .stDateInput input:focus, .stNumberInput input:focus {{
    border-color: {COR_CIANO} !important;
    box-shadow: 0 0 12px rgba(0, 212, 255, 0.35) !important;
    outline: none !important;
}}

/* Botões primários */
.stButton>button {{
    background: linear-gradient(90deg, {COR_CIANO}, #0077b6) !important;
    color: #0a0e27 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 10px 24px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3) !important;
}}
.stButton>button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 22px rgba(0, 212, 255, 0.5) !important;
}}

/* Botões secundários */
.stButton>button[kind="secondary"] {{
    background: rgba(0, 0, 0, 0.4) !important;
    color: {COR_CIANO} !important;
    border: 1px solid {COR_CIANO} !important;
}}

/* Título MARMED brilhante */
.marmed-title {{
    color: {COR_CIANO} !important;
    text-shadow: 0 0 10px rgba(0, 212, 255, 0.6), 0 0 20px rgba(0, 212, 255, 0.3) !important;
    font-weight: 800 !important;
    letter-spacing: 2px !important;
    text-align: center !important;
}}

/* Cards de métricas */
.metric-card {{
    background: {COR_CARD} !important;
    backdrop-filter: blur(14px) !important;
    border: 1px solid {COR_CARD_BORDA} !important;
    border-radius: 16px !important;
    padding: 18px !important;
    text-align: center !important;
    transition: all 0.3s ease !important;
    height: 100%;
}}
.metric-card:hover {{
    border-color: rgba(0, 212, 255, 0.55) !important;
    transform: translateY(-4px) !important;
    box-shadow: 0 12px 35px rgba(0, 212, 255, 0.15) !important;
}}
.metric-label {{
    color: {COR_CIANO} !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    margin-bottom: 8px !important;
}}
.metric-value {{
    color: {COR_DOURADO} !important;
    font-size: 1.3rem !important;
    font-weight: 700 !important;
}}

/* Tabelas */
.dataframe {{
    background: rgba(0, 0, 0, 0.25) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(0, 212, 255, 0.15) !important;
}}
.dataframe th {{
    background: rgba(0, 212, 255, 0.18) !important;
    color: {COR_CIANO} !important;
    font-weight: 700 !important;
}}
.dataframe td {{
    color: {COR_TEXTO} !important;
    border-bottom: 1px solid rgba(0, 212, 255, 0.08) !important;
}}

/* Ocultar elementos padrão do Streamlit */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}

/* Garantir que tudo fique acima das partículas */
.main .block-container, [data-testid="stSidebar"] {{
    position: relative;
    z-index: 1;
}}
</style>

<div class="particulas">
    <span></span><span></span><span></span><span></span><span></span><span></span>
    <span></span><span></span><span></span><span></span><span></span><span></span>
</div>
"""

# ============== BANCO DE DADOS ==============
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        nome TEXT NOT NULL,
        perfil TEXT NOT NULL DEFAULT 'admin',
        criado_em TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contas_pagar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fornecedor TEXT NOT NULL,
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        vencimento TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pendente',
        criado_em TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contas_receber (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente TEXT NOT NULL,
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        vencimento TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pendente',
        criado_em TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS empenhos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_empenho TEXT UNIQUE NOT NULL,
        fornecedor TEXT NOT NULL,
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        data_empenho TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Ativo',
        criado_em TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS licitacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        modalidade TEXT NOT NULL,
        objeto TEXT NOT NULL,
        valor_estimado REAL NOT NULL,
        data_abertura TEXT NOT NULL,
        situacao TEXT NOT NULL DEFAULT 'Em Andamento',
        criado_em TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contratos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_contrato TEXT UNIQUE NOT NULL,
        fornecedor TEXT NOT NULL,
        objeto TEXT NOT NULL,
        valor REAL NOT NULL,
        data_inicio TEXT NOT NULL,
        data_fim TEXT NOT NULL,
        situacao TEXT NOT NULL DEFAULT 'Vigente',
        criado_em TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        data TEXT NOT NULL,
        criado_em TEXT NOT NULL
    )
    ''')

    # Usuário padrão
    senha_padrao = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    cursor.execute('''
    INSERT OR IGNORE INTO usuarios (usuario, senha_hash, nome, perfil, criado_em)
    VALUES (?, ?, ?, ?, ?)
    ''', ("admin", senha_padrao, "Administrador", "admin", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    # Dados simulados iniciais
    cursor.execute("SELECT COUNT(*) FROM contas_pagar")
    if cursor.fetchone()[0] == 0:
        dados_pagar = [
            ("FORNECEDOR A", "Material de expediente", 2450.00, "2025-01-15", "Pendente"),
            ("FORNECEDOR B", "Serviços de limpeza", 3800.00, "2025-01-20", "Pago"),
            ("FORNECEDOR C", "Manutenção de veículos", 1250.00, "2025-01-25", "Pendente"),
            ("FORNECEDOR D", "Medicamentos", 8750.00, "2025-02-05", "Pendente"),
            ("FORNECEDOR E", "Consultoria técnica", 4200.00, "2025-02-10", "Pago"),
        ]
        for d in dados_pagar:
            cursor.execute('''
            INSERT INTO contas_pagar (fornecedor, descricao, valor, vencimento, status, criado_em)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (*d, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    cursor.execute("SELECT COUNT(*) FROM contas_receber")
    if cursor.fetchone()[0] == 0:
        dados_receber = [
            ("MUNICÍPIO A", "Convenio de saúde", 15000.00, "2025-01-18", "Recebido"),
            ("MUNICÍPIO B", "Repasse estadual", 22000.00, "2025-01-22", "Pendente"),
            ("MUNICÍPIO C", "Transferência", 8500.00, "2025-01-30", "Pendente"),
            ("MUNICÍPIO D", "Transposição", 12000.00, "2025-02-08", "Recebido"),
        ]
        for d in dados_receber:
            cursor.execute('''
            INSERT INTO contas_receber (cliente, descricao, valor, vencimento, status, criado_em)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (*d, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    cursor.execute("SELECT COUNT(*) FROM empenhos")
    if cursor.fetchone()[0] == 0:
        dados_empenhos = [
            ("2025/001", "FORNECEDOR X", "Aquisição de ambulância", 185000.00, "2025-01-10", "Ativo"),
            ("2025/002", "FORNECEDOR Y", "Reforma de UBS", 95000.00, "2025-01-12", "Ativo"),
            ("2025/003", "FORNECEDOR Z", "Equipamentos médicos", 67000.00, "2025-01-18", "Liquidado"),
            ("2025/004", "FORNECEDOR W", "Material de consumo", 23500.00, "2025-01-22", "Ativo"),
        ]
        for d in dados_empenhos:
            cursor.execute('''
            INSERT INTO empenhos (numero_empenho, fornecedor, descricao, valor, data_empenho, status, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (*d, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    cursor.execute("SELECT COUNT(*) FROM licitacoes")
    if cursor.fetchone()[0] == 0:
        dados_licitacoes = [
            ("Pregão Eletrônico", "Aquisição de medicamentos", 450000.00, "2025-02-01", "Em Andamento"),
            ("Tomada de Preços", "Serviços de limpeza hospitalar", 120000.00, "2025-02-15", "Em Andamento"),
            ("Concorrência", "Construção de UPA", 2500000.00, "2025-03-01", "Publicada"),
            ("Dispensa", "Material de escritório", 15000.00, "2025-01-28", "Concluída"),
        ]
        for d in dados_licitacoes:
            cursor.execute('''
            INSERT INTO licitacoes (modalidade, objeto, valor_estimado, data_abertura, situacao, criado_em)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (*d, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    cursor.execute("SELECT COUNT(*) FROM contratos")
    if cursor.fetchone()[0] == 0:
        dados_contratos = [
            ("2025/001", "CONSTRUTORA A", "Reforma do Pronto Socorro", 320000.00, "2025-01-05", "2025-06-30", "Vigente"),
            ("2025/002", "LABORATÓRIO B", "Serviços de análises clínicas", 180000.00, "2025-01-10", "2025-12-31", "Vigente"),
            ("2024/045", "FORNECEDOR C", "Manutenção de equipamentos", 45000.00, "2024-03-01", "2025-02-28", "Encerrado"),
            ("2025/003", "DISTRIBUIDORA D", "Distribuição de medicamentos", 540000.00, "2025-01-15", "2025-12-31", "Vigente"),
        ]
        for d in dados_contratos:
            cursor.execute('''
            INSERT INTO contratos (numero_contrato, fornecedor, objeto, valor, data_inicio, data_fim, situacao, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*d, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    cursor.execute("SELECT COUNT(*) FROM movimentacoes")
    if cursor.fetchone()[0] == 0:
        dados_mov = [
            ("Entrada", "Repasse Federal - Janeiro", 1250000.00, "2025-01-05"),
            ("Entrada", "Repasse Estadual - Janeiro", 890000.00, "2025-01-08"),
            ("Saída", "Pagamento de empenhos", 487000.00, "2025-01-12"),
            ("Entrada", "Recurso Municipal", 450000.00, "2025-01-15"),
            ("Saída", "Pagamento de fornecedores", 234000.00, "2025-01-20"),
            ("Entrada", "Transferência", 320000.00, "2025-01-22"),
            ("Entrada", "Transposição", 180000.00, "2025-01-25"),
            ("Saída", "Investimentos em infraestrutura", 385000.00, "2025-01-28"),
        ]
        for d in dados_mov:
            cursor.execute('''
            INSERT INTO movimentacoes (tipo, descricao, valor, data, criado_em)
            VALUES (?, ?, ?, ?, ?)
            ''', (*d, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()

# ============== FUNÇÕES AUXILIARES ==============
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_login(usuario, senha):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,))
    user = cursor.fetchone()
    conn.close()
    if user and user["senha_hash"] == hash_senha(senha):
        return dict(user)
    return None

def alterar_senha(usuario_id, nova_senha):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET senha_hash = ? WHERE id = ?", (hash_senha(nova_senha), usuario_id))
    conn.commit()
    conn.close()

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def carregar_dados(tabela):
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT * FROM {tabela} ORDER BY id DESC", conn)
    conn.close()
    return df

def inserir_registro(tabela, dados):
    conn = get_db_connection()
    cursor = conn.cursor()
    colunas = ", ".join(dados.keys())
    placeholders = ", ".join(["?"] * len(dados))
    valores = list(dados.values())
    cursor.execute(f"INSERT INTO {tabela} ({colunas}, criado_em) VALUES ({placeholders}, ?)",
                   valores + [datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    conn.commit()
    conn.close()

def atualizar_registro(tabela, id_reg, dados):
    conn = get_db_connection()
    cursor = conn.cursor()
    sets = ", ".join([f"{k} = ?" for k in dados.keys()])
    valores = list(dados.values()) + [id_reg]
    cursor.execute(f"UPDATE {tabela} SET {sets} WHERE id = ?", valores)
    conn.commit()
    conn.close()

def excluir_registro(tabela, id_reg):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {tabela} WHERE id = ?", (id_reg,))
    conn.commit()
    conn.close()

# ============== COMPONENTES UI ==============
def render_login():
    st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<<br><br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="glass-card" style="text-align:center;">
            <h1 class="marmed-title">MARMED</h1>
            <p style="color:#00d4ff; font-size:1.05rem; margin-top:-8px; letter-spacing:1px;">
                Gestão em Saúde Pública
            </p>
            <p style="color:#ffd700; font-size:0.85rem; margin-bottom:24px; letter-spacing:2px;">
                Luminárias - MG
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
            usuario = st.text_input("Usuário", key="login_usuario", placeholder="Digite seu usuário")
            senha = st.text_input("Senha", type="password", key="login_senha", placeholder="Digite sua senha")

            if st.button("Entrar", use_container_width=True):
                user = verificar_login(usuario, senha)
                if user:
                    st.session_state.autenticado = True
                    st.session_state.usuario = user
                    st.session_state.menu = "Dashboard"
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

            st.markdown("<<p style='text-align:center; font-size:0.8rem; color:rgba(230,247,255,0.6); margin-top:16px;'>Usuário padrão: admin / Diretor2025#</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

def render_sidebar():
    user = st.session_state.usuario
    st.sidebar.markdown(f"""
    <div style="text-align:center; padding:20px 10px; border-bottom:1px solid rgba(0,212,255,0.2); margin-bottom:16px;">
        <div style="font-size:2.5rem; color:#00d4ff; margin-bottom:8px;">👤</div>
        <p style="color:#00d4ff; font-weight:700; margin:0;">{user['nome']}</p>
        <p style="color:#ffd700; font-size:0.8rem; margin:0; text-transform:uppercase;">{user['perfil']}</p>
    </div>
    """, unsafe_allow_html=True)

    menu_items = [
        "Dashboard", "Contas a Pagar", "Contas a Receber", "Empenhos",
        "Licitações", "Contratos", "Relatórios", "Trocar Senha", "Sair"
    ]

    for item in menu_items:
        if st.sidebar.button(item, use_container_width=True, key=f"menu_{item}"):
            if item == "Sair":
                st.session_state.autenticado = False
                st.session_state.usuario = None
                st.session_state.menu = None
                st.rerun()
            else:
                st.session_state.menu = item
                st.rerun()

# ============== DASHBOARD ==============
def render_dashboard():
    st.markdown("<<h1 style='color:#00d4ff; text-shadow:0 0 10px rgba(0,212,255,0.4);'>Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<<p style='color:#ffd700; letter-spacing:1px; margin-bottom:24px;'>MARMED - Gestão em Saúde Pública de Luminárias-MG</p>", unsafe_allow_html=True)

    metricas = [
        ("REPASSE FEDERAL", 1250000.00),
        ("REPASSE ESTADUAL", 890000.00),
        ("RECURSO MUNICIPAL", 450000.00),
        ("TRANSFERÊNCIA", 320000.00),
        ("TRANSPOSIÇÃO", 180000.00),
    ]

    cols = st.columns(5)
    for i, (label, value) in enumerate(metricas):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{formatar_moeda(value)}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<<br>", unsafe_allow_html=True)

    conn = get_db_connection()
    df_mov = pd.read_sql_query("SELECT tipo, descricao, valor, data FROM movimentacoes ORDER BY data DESC, id DESC LIMIT 10", conn)
    df_pagar = pd.read_sql_query("SELECT SUM(valor) as total FROM contas_pagar", conn)
    df_receber = pd.read_sql_query("SELECT SUM(valor) as total FROM contas_receber", conn)
    df_empenhos = pd.read_sql_query("SELECT SUM(valor) as total FROM empenhos", conn)
    df_contratos = pd.read_sql_query("SELECT SUM(valor) as total FROM contratos WHERE situacao = 'Vigente'", conn)
    conn.close()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<<h3 style='color:#00d4ff; margin-bottom:16px;'>Últimas Movimentações</h3>", unsafe_allow_html=True)
        df_mov["valor"] = df_mov["valor"].apply(formatar_moeda)
        st.dataframe(df_mov, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<<h3 style='color:#00d4ff; margin-bottom:16px;'>Resumo do Mês</h3>", unsafe_allow_html=True)
        resumo = {
            "Contas a Pagar": df_pagar.iloc[0]["total"] or 0,
            "Contas a Receber": df_receber.iloc[0]["total"] or 0,
            "Empenhos": df_empenhos.iloc[0]["total"] or 0,
            "Contratos Vigentes": df_contratos.iloc[0]["total"] or 0,
        }
        for k, v in resumo.items():
            st.markdown(f"""
            <div style="margin-bottom:14px; padding:12px; background:rgba(0,0,0,0.25); border-radius:10px; border-left:3px solid #00d4ff;">
                <p style="margin:0; color:#00d4ff; font-size:0.85rem; font-weight:600;">{k}</p>
                <p style="margin:0; color:#ffd700; font-size:1.1rem; font-weight:700;">{formatar_moeda(v)}</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ============== CRUD GENÉRICO ==============
def render_crud(tabela, titulo, campos, chave_unica=None):
    st.markdown(f"<<h1 style='color:#00d4ff; text-shadow:0 0 10px rgba(0,212,255,0.4);'>{titulo}</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Listar", "➕ Adicionar", "✏️ Editar / Excluir"])

    df = carregar_dados(tabela)

    with tab1:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"<<h3 style='color:#00d4ff;'>Registros de {titulo}</h3>", unsafe_allow_html=True)
        if not df.empty:
            st.dataframe(df.drop(columns=["criado_em"], errors="ignore"), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro encontrado.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"<<h3 style='color:#00d4ff;'>Adicionar {titulo}</h3>", unsafe_allow_html=True)
        with st.form(f"form_add_{tabela}"):
            valores = {}
            col_inputs = st.columns(2)
            for idx, (campo, config) in enumerate(campos.items()):
                with col_inputs[idx % 2]:
                    if config["tipo"] == "text":
                        valores[campo] = st.text_input(config["label"], key=f"add_{tabela}_{campo}")
                    elif config["tipo"] == "number":
                        valores[campo] = st.number_input(config["label"], min_value=0.0, format="%.2f", key=f"add_{tabela}_{campo}")
                    elif config["tipo"] == "date":
                        valores[campo] = st.date_input(config["label"], key=f"add_{tabela}_{campo}").strftime("%Y-%m-%d")
                    elif config["tipo"] == "select":
                        valores[campo] = st.selectbox(config["label"], config["opcoes"], key=f"add_{tabela}_{campo}")
            submitted = st.form_submit_button("Salvar", use_container_width=True)
            if submitted:
                erro = False
                for c, v in valores.items():
                    if v == "" or v is None:
                        st.error(f"O campo {campos[c]['label']} é obrigatório.")
                        erro = True
                        break
                if not erro:
                    try:
                        inserir_registro(tabela, valores)
                        st.success("Registro adicionado com sucesso!")
                        time.sleep(0.5)
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error(f"Já existe um registro com esse {chave_unica}.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"<<h3 style='color:#00d4ff;'>Editar / Excluir {titulo}</h3>", unsafe_allow_html=True)
        if not df.empty:
            registro_id = st.selectbox("Selecione o registro", df["id"].tolist(), format_func=lambda x: f"ID {x} - {df[df['id']==x].iloc[0].to_dict().get(campos[list(campos.keys())[0]]['label'].lower(), '')}", key=f"sel_edit_{tabela}")
            registro = df[df["id"] == registro_id].iloc[0].to_dict()
            with st.form(f"form_edit_{tabela}"):
                valores_edit = {}
                col_inputs = st.columns(2)
                for idx, (campo, config) in enumerate(campos.items()):
                    with col_inputs[idx % 2]:
                        val = registro.get(campo, "")
                        if config["tipo"] == "text":
                            valores_edit[campo] = st.text_input(config["label"], value=str(val), key=f"edit_{tabela}_{campo}")
                        elif config["tipo"] == "number":
                            valores_edit[campo] = st.number_input(config["label"], min_value=0.0, value=float(val), format="%.2f", key=f"edit_{tabela}_{campo}")
                        elif config["tipo"] == "date":
                            valores_edit[campo] = st.date_input(config["label"], value=datetime.strptime(val, "%Y-%m-%d").date(), key=f"edit_{tabela}_{campo}").strftime("%Y-%m-%d")
                        elif config["tipo"] == "select":
                            valores_edit[campo] = st.selectbox(config["label"], config["opcoes"], index=config["opcoes"].index(val), key=f"edit_{tabela}_{campo}")
                col_s, col_d = st.columns(2)
                with col_s:
                    if st.form_submit_button("Atualizar", use_container_width=True):
                        atualizar_registro(tabela, registro_id, valores_edit)
                        st.success("Registro atualizado com sucesso!")
                        time.sleep(0.5)
                        st.rerun()
                with col_d:
                    if st.form_submit_button("Excluir", use_container_width=True):
                        excluir_registro(tabela, registro_id)
                        st.success("Registro excluído com sucesso!")
                        time.sleep(0.5)
                        st.rerun()
        else:
            st.info("Nenhum registro disponível para edição.")
        st.markdown("</div>", unsafe_allow_html=True)

# ============== RELATÓRIOS ==============
def render_relatorios():
    st.markdown("<<h1 style='color:#00d4ff; text-shadow:0 0 10px rgba(0,212,255,0.4);'>Relatórios</h1>", unsafe_allow_html=True)

    st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data Início", value=date(2025, 1, 1))
    with col2:
        data_fim = st.date_input("Data Fim", value=date(2025, 12, 31))

    data_inicio_str = data_inicio.strftime("%Y-%m-%d")
    data_fim_str = data_fim.strftime("%Y-%m-%d")

    conn = get_db_connection()
    df_pagar = pd.read_sql_query(f"SELECT * FROM contas_pagar WHERE vencimento BETWEEN ? AND ?", conn, params=(data_inicio_str, data_fim_str))
    df_receber = pd.read_sql_query(f"SELECT * FROM contas_receber WHERE vencimento BETWEEN ? AND ?", conn, params=(data_inicio_str, data_fim_str))
    df_empenhos = pd.read_sql_query(f"SELECT * FROM empenhos WHERE data_empenho BETWEEN ? AND ?", conn, params=(data_inicio_str, data_fim_str))
    df_licitacoes = pd.read_sql_query(f"SELECT * FROM licitacoes WHERE data_abertura BETWEEN ? AND ?", conn, params=(data_inicio_str, data_fim_str))
    df_contratos = pd.read_sql_query(f"SELECT * FROM contratos WHERE data_inicio BETWEEN ? AND ?", conn, params=(data_inicio_str, data_fim_str))
    df_mov = pd.read_sql_query(f"SELECT * FROM movimentacoes WHERE data BETWEEN ? AND ?", conn, params=(data_inicio_str, data_fim_str))
    conn.close()

    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Contas a Pagar</div>
            <div class="metric-value">{formatar_moeda(df_pagar['valor'].sum() if not df_pagar.empty else 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Contas a Receber</div>
            <div class="metric-value">{formatar_moeda(df_receber['valor'].sum() if not df_receber.empty else 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Empenhos</div>
            <div class="metric-value">{formatar_moeda(df_empenhos['valor'].sum() if not df_empenhos.empty else 0)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<<br>", unsafe_allow_html=True)

    tabelas = [
        ("Contas a Pagar", df_pagar.drop(columns=["criado_em"], errors="ignore")),
        ("Contas a Receber", df_receber.drop(columns=["criado_em"], errors="ignore")),
        ("Empenhos", df_empenhos.drop(columns=["criado_em"], errors="ignore")),
        ("Licitações", df_licitacoes.drop(columns=["criado_em"], errors="ignore")),
        ("Contratos", df_contratos.drop(columns=["criado_em"], errors="ignore")),
        ("Movimentações", df_mov.drop(columns=["criado_em"], errors="ignore")),
    ]

    for titulo, dframe in tabelas:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"<<h3 style='color:#00d4ff;'>{titulo}</h3>", unsafe_allow_html=True)
        if not dframe.empty:
            st.dataframe(dframe, use_container_width=True, hide_index=True)
        else:
            st.info(f"Nenhum registro de {titulo} no período selecionado.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<<br>", unsafe_allow_html=True)

# ============== TROCAR SENHA ==============
def render_trocar_senha():
    st.markdown("<<h1 style='color:#00d4ff; text-shadow:0 0 10px rgba(0,212,255,0.4);'>Trocar Senha</h1>", unsafe_allow_html=True)

    st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
    with st.form("form_trocar_senha"):
        senha_atual = st.text_input("Senha Atual", type="password", placeholder="Digite sua senha atual")
        nova_senha = st.text_input("Nova Senha", type="password", placeholder="Digite a nova senha")
        confirmar_senha = st.text_input("Confirmar Nova Senha", type="password", placeholder="Confirme a nova senha")
        submitted = st.form_submit_button("Alterar Senha", use_container_width=True)
        if submitted:
            if not senha_atual or not nova_senha or not confirmar_senha:
                st.error("Todos os campos são obrigatórios.")
            elif hash_senha(senha_atual) != st.session_state.usuario["senha_hash"]:
                st.error("Senha atual incorreta.")
            elif len(nova_senha) < 6:
                st.error("A nova senha deve ter pelo menos 6 caracteres.")
            elif nova_senha != confirmar_senha:
                st.error("A nova senha e a confirmação não coincidem.")
            else:
                alterar_senha(st.session_state.usuario["id"], nova_senha)
                st.session_state.usuario["senha_hash"] = hash_senha(nova_senha)
                st.success("Senha alterada com sucesso!")
    st.markdown("</div>", unsafe_allow_html=True)

# ============== MAIN ==============
def main():
    st.set_page_config(
        page_title="MARMED - Gestão em Saúde Pública",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="collapsed" if not st.session_state.get("autenticado") else "expanded"
    )

    init_db()

    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    if "usuario" not in st.session_state:
        st.session_state.usuario = None
    if "menu" not in st.session_state:
        st.session_state.menu = "Dashboard"

    if not st.session_state.autenticado:
        render_login()
        return

    st.markdown(CSS_GLOBAL, unsafe_allow_html=True)
    render_sidebar()

    menu = st.session_state.get("menu", "Dashboard")

    if menu == "Dashboard":
        render_dashboard()
    elif menu == "Contas a Pagar":
        render_crud("contas_pagar", "Contas a Pagar", {
            "fornecedor": {"label": "Fornecedor", "tipo": "text"},
            "descricao": {"label": "Descrição", "tipo": "text"},
            "valor": {"label": "Valor", "tipo": "number"},
            "vencimento": {"label": "Vencimento", "tipo": "date"},
            "status": {"label": "Status", "tipo": "select", "opcoes": ["Pendente", "Pago", "Vencido"]},
        })
    elif menu == "Contas a Receber":
        render_crud("contas_receber", "Contas a Receber", {
            "cliente": {"label": "Cliente", "tipo": "text"},
            "descricao": {"label": "Descrição", "tipo": "text"},
            "valor": {"label": "Valor", "tipo": "number"},
            "vencimento": {"label": "Vencimento", "tipo": "date"},
            "status": {"label": "Status", "tipo": "select", "opcoes": ["Pendente", "Recebido", "Atrasado"]},
        })
    elif menu == "Empenhos":
        render_crud("empenhos", "Empenhos", {
            "numero_empenho": {"label": "Número do Empenho", "tipo": "text"},
            "fornecedor": {"label": "Fornecedor", "tipo": "text"},
            "descricao": {"label": "Descrição", "tipo": "text"},
            "valor": {"label": "Valor", "tipo": "number"},
            "data_empenho": {"label": "Data do Empenho", "tipo": "date"},
            "status": {"label": "Status", "tipo": "select", "opcoes": ["Ativo", "Liquidado", "Anulado"]},
        }, chave_unica="Número do Empenho")
    elif menu == "Licitações":
        render_crud("licitacoes", "Licitações", {
            "modalidade": {"label": "Modalidade", "tipo": "text"},
            "objeto": {"label": "Objeto", "tipo": "text"},
            "valor_estimado": {"label": "Valor Estimado", "tipo": "number"},
            "data_abertura": {"label": "Data de Abertura", "tipo": "date"},
            "situacao": {"label": "Situação", "tipo": "select", "opcoes": ["Publicada", "Em Andamento", "Concluída", "Cancelada"]},
        })
    elif menu == "Contratos":
        render_crud("contratos", "Contratos", {
            "numero_contrato": {"label": "Número do Contrato", "tipo": "text"},
            "fornecedor": {"label": "Fornecedor", "tipo": "text"},
            "objeto": {"label": "Objeto", "tipo": "text"},
            "valor": {"label": "Valor", "tipo": "number"},
            "data_inicio": {"label": "Data Início", "tipo": "date"},
            "data_fim": {"label": "Data Fim", "tipo": "date"},
            "situacao": {"label": "Situação", "tipo": "select", "opcoes": ["Vigente", "Encerrado", "Rescindido"]},
        }, chave_unica="Número do Contrato")
    elif menu == "Relatórios":
        render_relatorios()
    elif menu == "Trocar Senha":
        render_trocar_senha()

if __name__ == "__main__":
    main()
