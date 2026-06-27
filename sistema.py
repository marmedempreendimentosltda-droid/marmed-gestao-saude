import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, date

st.set_page_config(page_title="MARMED", 
# ============================================================
# BANCO DE DADOS
# ============================================================
def init_db():
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    
    # Tabela de usuários
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nome TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  senha TEXT NOT NULL,
                  tipo TEXT DEFAULT 'usuario',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Tabela de contas
    c.execute('''CREATE TABLE IF NOT EXISTS contas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  esfera TEXT,
                  tipo TEXT,
                  fonte TEXT,
                  valor REAL,
                  descricao TEXT,
                  data DATE,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    
    # Tabela de compras
    c.execute('''CREATE TABLE IF NOT EXISTS compras
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  esfera TEXT,
                  descricao TEXT,
                  valor REAL,
                  data DATE,
                  status TEXT DEFAULT 'pendente',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    
    # Tabela de superavit
    c.execute('''CREATE TABLE IF NOT EXISTS superavit
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  esfera TEXT,
                  valor REAL,
                  data DATE,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    
    # Tabela de programas de saude
    c.execute('''CREATE TABLE IF NOT EXISTS programas_saude
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  nome TEXT,
                  descricao TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    
    # Tabela de uploads
    c.execute('''CREATE TABLE IF NOT EXISTS uploads
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  categoria TEXT,
                  nome_arquivo TEXT,
                  conteudo TEXT,
                  data DATE,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    
    # Criar usuario admin padrao
    senha_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    try:
        c.execute("INSERT OR IGNORE INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                  ("Administrador", "admin", senha_hash, "admin"))
    except:
        pass
    
    conn.commit()
    conn.close()

def verificar_login(email, senha):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    c.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha_hash))
    usuario = c.fetchone()
    conn.close()
    return usuario

# ============================================================
# INICIALIZACAO
# ============================================================
init_db()

if 'usuario_id' not in st.session_state:
    st.session_state.usuario_id = None
if 'usuario_nome' not in st.session_state:
    st.session_state.usuario_nome = None
if 'usuario_tipo' not in st.session_state:
    st.session_state.usuario_tipo = None
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'login'

# ============================================================
# CSS - DESIGN MODERNO
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%);
    }
    
    /* TELA DE LOGIN */
    .login-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: 2rem;
    }
    
    .login-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 3rem;
        width: 100%;
        max-width: 420px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    }
    
    .login-logo {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .login-logo h1 {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        letter-spacing: -1px;
    }
    
    .login-logo p {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    .login-subtitle {
        color: #64748b;
        text-align: center;
        font-size: 0.85rem;
        margin-bottom: 1.5rem;
    }
    
    /* CAMPOS DE LOGIN */
    .stTextInput label {
        color: #cbd5e1 !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
    }
    
    .stTextInput input {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        color: #f1f5f9 !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput input:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2) !important;
        background: rgba(255, 255, 255, 0.12) !important;
    }
    
    .stTextInput input::placeholder {
        color: #475569 !important;
    }
    
    /* BOTAO */
    .stButton button {
        background: linear-gradient(135deg, #38bdf8, #818cf8) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(56, 189, 248, 0.3) !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(56, 189, 248, 0.4) !important;
    }
    
    .stButton button:active {
        transform: translateY(0) !important;
    }
    
    /* ABAS */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        padding: 4px !important;
        gap: 4px !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        color: #94a3b8 !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #38bdf8, #818cf8) !important;
        color: white !important;
    }
    
    /* MENSAGENS */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
    }
    
    .stAlert [data-baseweb="notification"] {
        border-radius: 12px !important;
    }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1a2a4a 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    section[data-testid="stSidebar"] .stSelectbox label {
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    
    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
    }
    
    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] span {
        color: #e2e8f0 !important;
    }
    
    /* DASHBOARD */
    .dashboard-title {
        font-size: 2rem;
        font-weight: 800;
        color: #f1f5f9;
        margin-bottom: 0.5rem;
    }
    
    .dashboard-subtitle {
        color: #64748b;
        font-size: 0.9rem;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3);
        border-color: rgba(56, 189, 248, 0.3);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
   
