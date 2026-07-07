import streamlit as st
import sqlite3
import hashlib
import re
from datetime import datetime

st.set_page_config(page_title="MARMED", layout="wide")


def apply_global_css():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #16213e 50%, #0f3460 100%) !important;
        color: #e0f2fe !important;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0e27 0%, #16213e 100%) !important;
        border-right: 1px solid rgba(56,189,248,0.15) !important;
    }
    section[data-testid="stSidebar"] * {
        color: #e0f2fe !important;
    }
    .stTextInput label, .stSelectbox label, .stNumberInput label, .stTextArea label, .stDateInput label, .stMultiSelect label {
        color: #22d3ee !important;
        font-weight: 600 !important;
    }
    .stTextInput > div > div > input {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(34, 211, 238, 0.3) !important;
        color: #e0f2fe !important;
        border-radius: 10px !important;
    }
    .stSelectbox > div > div {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(34, 211, 238, 0.3) !important;
        border-radius: 10px !important;
        color: #e0f2fe !important;
    }
    .stNumberInput > div > div > input {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(34, 211, 238, 0.3) !important;
        color: #e0f2fe !important;
        border-radius: 10px !important;
    }
    .stTextArea > div > textarea {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px solid rgba(34, 211, 238, 0.3) !important;
        color: #e0f2fe !important;
        border-radius: 10px !important;
    }
    .stButton > button {
        background: linear-gradient(90deg, #06b6d4, #3b82f6) !important;
        color: #fff !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        border: none !important;
    }
    .stDataFrame {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(34, 211, 238, 0.3) !important;
        border-radius: 10px !important;
    }
    .stDataFrame td { color: #e0f2fe !important; }
    .stDataFrame th { color: #22d3ee !important; }
    .stFileUploader > div {
        background: rgba(30, 41, 59, 0.8) !important;
        border: 1px dashed rgba(34, 211, 238, 0.4) !important;
        border-radius: 10px !important;
        color: #e0f2fe !important;
    }
    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #e0f2fe !important;
    }
    </style>
    """, unsafe_allow_html=True)


apply_global_css()


def format_currency(valor):
    if valor is None:
        valor = 0.0
    v = float(valor)
    texto = f"{v:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def get_fonte(esfera):
    if esfera == "Federal": return "1.600"
    elif esfera == "Estadual": return "1.621"
    elif esfera == "Municipal": return "1.500"
    return ""


def get_fonte_superavit(esfera):
    if esfera == "Federal": return "2.600"
    elif esfera == "Estadual": return "2.621"
    return None


def extract_text_from_bytes(file_bytes, filename):
    text = ""
    try:
        if filename.lower().endswith(('.txt', '.csv')):
            text = file_bytes.decode('utf-8', errors='replace')
        else:
            text = f"[Arquivo: {filename}]"
    except:
        text = f"[Nao foi possivel extrair texto]"
    return text


def init_db():
    conn = sqlite3.connect("marmed.db")
    cur = conn.cursor()
    schema = {
        "users": [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),("username", "TEXT UNIQUE"),("password_hash", "TEXT"),],
        "contas_receber": [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),("esfera", "TEXT"),("numero_conta", "TEXT"),("fonte", "TEXT"),("referencia_tipo", "TEXT"),("referencia_numero", "TEXT"),("tipo_recurso", "TEXT"),("valor_pago_custeio", "REAL DEFAULT 0"),("valor_pago_investimento", "REAL DEFAULT 0"),("valor_total", "REAL DEFAULT 0"),("data_recebimento", "TEXT"),("programa_politica", "TEXT"),("setor_gasto", "TEXT"),],
        "superavit": [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),("esfera", "TEXT"),("fonte_original", "TEXT"),("fonte_superavit", "TEXT"),("saldo_total", "REAL DEFAULT 0"),("saldo_restante", "REAL DEFAULT 0"),("created_at", "TEXT"),],
        "ordens_compra": [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),("conta_receber_id", "INTEGER"),("esfera", "TEXT"),("numero_conta", "TEXT"),("fonte", "TEXT"),("ficha", "TEXT"),("tipo_despesa", "TEXT"),("data_compra", "TEXT"),("valor_compra", "REAL DEFAULT 0"),("produto_servico", "TEXT"),("created_at", "TEXT"),],
        "arquivos_saude": [("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),("bloco", "TEXT"),("nome_arquivo", "TEXT"),("conteudo_texto", "TEXT"),("dados_arquivo", "BLOB"),("data_upload", "TEXT"),],
    }
    for tabela, colunas in schema.items():
        colunas_sql = ", ".join(f"{nome} {definicao}" for nome, definicao in colunas)
        cur.execute(f"CREATE TABLE IF NOT EXISTS {tabela} ({colunas_sql})")
    for tabela, colunas in schema.items():
        colunas_existentes = {row[1] for row in cur.execute(f"PRAGMA table_info({tabela})").fetchall()}
        for nome_coluna, definicao in colunas:
            if nome_coluna in colunas_existentes: continue
            if "PRIMARY KEY" in definicao.upper(): continue
            try: cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {nome_coluna} {definicao}")
            except sqlite3.OperationalError: pass
    admin_hash = hashlib.sha256("Diretor2025#".encode("utf-8")).hexdigest()
    try:
        cur.execute("INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)", ("admin", admin_hash))
    except sqlite3.OperationalError: pass
    conn.commit()
    conn.close()

init_db()


def login_page():
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #0a0e27 0%, #16213e 50%, #0f3460 100%) !important; }
        div[data-testid="column"]:nth-child(2) {
            background: rgba(15, 23, 42, 0.75) !important;
            backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(14, 165, 233, 0.3) !important;
            border-radius: 24px !important;
            padding: 48px 40px !important;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5) !important;
            margin-top: 80px !important; max-width: 420px !important;
            margin-left: auto !important; margin-right: auto !important;
        }
        .marmed-title { font-size: 52px; font-weight: 800; text-align: center; color: #e0f2fe; letter-spacing: 6px; margin-bottom: 8px; }
        .subtitle { text-align: center; color: #7dd3fc; font-size: 14px; letter-spacing: 4px; margin-bottom: 36px; text-transform: uppercase; }
        .stTextInput label { color: #22d3ee !important; font-weight: 600; }
        .stTextInput > div > div > input { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; color: #e0f2fe !important; border-radius: 10px !important; }
        .stButton > button { background: linear-gradient(90deg, #06b6d4, #3b82f6) !important; color: #fff !important; font-weight: 700 !important; border-radius: 10px !important; border: none !important; width: 100%; padding: 12px !important; }
        .stSelectbox > div > div { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; border-radius: 10px !important; color: #e0f2fe !important; }
        .stNumberInput > div > div > input { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; color: #e0f2fe !important; border-radius: 10px !important; }
        .stDataFrame { background: rgba(15, 23, 42, 0.6) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; border-radius: 10px !important; }
        .stDataFrame td { color: #e0f2fe !important; }
        .stDataFrame th { color: #22d3ee !important; }
        .stFileUploader > div { background: rgba(30, 41, 59, 0.8) !important; border: 1px dashed rgba(34, 211, 238, 0.4) !important; border-radius: 10px !important; color: #e0f2fe !important; }
        .stTextArea > div > textarea { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; color: #e0f2fe !important; border-radius: 10px !important; }
        </style>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="marmed-title">MARMED</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">SISTEMA INTEGRADO DE GESTAO</div>', unsafe_allow_html=True)
        username = st.text_input("USUARIO", key="login_user")
        password = st.text_input("SENHA", type="password", key="login_pass")
        if st.button("Acessar"):
            pw_hash = hashlib.sha256(password.encode()).hexdigest()
            conn = sqlite3.connect("marmed.db")
            user = conn.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (username, pw_hash)).fetchone()
            conn.close()
            if user:
                st.session_state["logged_in"] = True
                st.session_state["page"] = "Dashboard"
                st.rerun()
            else:
                st.error("Usuario ou senha invalidos")


def dashboard():
    st.markdown('<h1 style="color:#e0f2fe;text-align:center;font-size:48px;font-weight:800;letter-spacing:6px;">MARMED</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#7dd3fc;text-align:center;letter-spacing:4px;margin-bottom:4px;">SISTEMA INTEGRADO DE GESTAO</h3>', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#1e40af;text-align:center;letter-spacing:3px;font-size:20px;font-weight:700;margin-bottom:16px;">PREFEITURA MUNICIPAL DE LUMINARIAS</h2>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    cols = st.columns(5)
    for i, (tit, esf, cor) in enumerate(zip(
        ["REPASSE FEDERAL", "REPASSE ESTADUAL", "RECURSO MUNICIPAL", "TRANSFERENCIA", "TRANSPOSICAO"],
        ["Federal", "Estadual", "Municipal", "Transferencia", "Transposicao"],
        ["#3b82f6", "#22c55e", "#eab308", "#a855f7", "#ef4444"]
    )):
        tc = conn.execute("SELECT COALESCE(SUM(valor_total),0) FROM contas_receber WHERE esfera=?", (esf,)).fetchone()[0]
        tg = conn.execute("SELECT COALESCE(SUM(valor_compra),0) FROM ordens_compra WHERE esfera=?", (esf,)).fetchone()[0]
        saldo = tc - tg
        with cols[i]:
            st.markdown(f'<div style="background:linear-gradient(135deg,#1a2a3a,#0f2027);border-radius:15px;padding:15px;text-align:center;border-left:4px solid {cor};border:1px solid rgba(34,211,238,0.3);margin-bottom:8px;"><div style="color:#b0eaff;font-size:11px;font-weight:600;">{tit}</div><div style="color:#00d4ff;font-size:18px;font-weight:700;">{format_currency(tc)}</div></div>', unsafe_allow_html=True)
            if st.button(f"Ver {esf}", key=f"b_{esf}"):
                st.session_state["esfera_view"] = esf
                st.session_state["page"] = "ESFERA DETALHE"; st.rerun()
    tc = conn.execute("SELECT COUNT(*) FROM contas_receber").fetchone()[0]
    tco = conn.execute("SELECT COUNT(*) FROM ordens_compra").fetchone()[0]
    conn.close()
    st.markdown(f'<p style="text-align:center;color:#64748b;font-size:12px;margin-top:10px;">{tc} conta(s) | {tco} ordem(ns) de compra - {datetime.now().strftime("%d/%m/%Y")}</p>', unsafe_allow_html=True)

# ... (rest of the functions remain unchanged)
