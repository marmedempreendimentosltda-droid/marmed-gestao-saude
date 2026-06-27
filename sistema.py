import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, date

st.set_page_config(page_title="MARMED", layout="wide", initial_sidebar_state="expanded")

def init_db():
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nome TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  senha TEXT NOT NULL,
                  tipo TEXT DEFAULT 'usuario',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
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
    
    c.execute('''CREATE TABLE IF NOT EXISTS superavit
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  esfera TEXT,
                  valor REAL,
                  data DATE,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS programas_saude
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  nome TEXT,
                  descricao TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS uploads
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  categoria TEXT,
                  nome_arquivo TEXT,
                  conteudo TEXT,
                  data DATE,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    
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

def format_currency(valor):
    if valor is None:
        return "R$ 0,00"
    v = float(valor)
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

init_db()

if 'usuario_id' not in st.session_state:
    st.session_state.usuario_id = None
if 'usuario_nome' not in st.session_state:
    st.session_state.usuario_nome = None
if 'usuario_tipo' not in st.session_state:
    st.session_state.usuario_tipo = None
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'login'
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%);
    }
    
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
    }
    
    .metric-label {
        color: #94a3b8;
        font-size: 0.85rem;
        margin-top: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

if st.session_state.pagina == 'login':
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<div class="login-logo"><h1>MARMED</h1><p>Gestao de Saude Municipal</p></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Entrar", "Cadastrar"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Usuario", placeholder="Digite seu email ou usuario")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            submit = st.form_submit_button("Entrar")
            if submit:
                if not email or not senha:
                    st.error("Preencha todos os campos!")
                else:
                    usuario = verificar_login(email, senha)
                    if usuario:
                        st.session_state.usuario_id = usuario[0]
                        st.session_state.usuario_nome = usuario[1]
                        st.session_state.usuario_tipo = usuario[4]
                        st.session_state.pagina = 'dashboard'
                        st.rerun()
                    else:
                        st.error("Usuario ou senha invalidos!")
    
    with tab2:
        with st.form("cadastro_form"):
            nome = st.text_input("Nome completo")
            email = st.text_input("Email")
            senha = st.text_input("Senha", type="password")
            confirmar_senha = st.text_input("Confirmar senha", type="password")
            submit = st.form_submit_button("Cadastrar")
            if submit:
                if not nome or not email or not senha:
                    st.error("Preencha todos os campos!")
                elif senha != confirmar_senha:
                    st.error("Senhas nao conferem!")
                elif len(senha) < 6:
                    st.error("Senha deve ter pelo menos 6 caracteres!")
                else:
                    conn = sqlite3.connect('marmed.db')
                    c = conn.cursor()
                    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
                    try:
                        c.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                                  (nome, email, senha_hash))
                        conn.commit()
                        st.success("Cadastro realizado com sucesso! Faca login.")
                    except:
                        st.error("Email ja cadastrado!")
                    finally:
                        conn.close()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    elif st.session_state.pagina == 'dashboard':
    st.sidebar.markdown(f"**Bem-vindo, {st.session_state.usuario_nome}**")
    st.sidebar.markdown("---")
    
    menu = st.sidebar.selectbox("Menu", [
        "Dashboard",
        "Contas",
        "Compras",
        "Superavit Financeiro",
        "Programas de Saude",
        "Plano Municipal de Saude",
        "Norte da Minha Gestao",
        "Conselho Municipal de Saude",
        "Trocar Senha",
        "Sair"
    ])
    
    if menu == "Sair":
        st.session_state.pagina = 'login'
        st.rerun()
    
    elif menu == "Trocar Senha":
        st.title("Trocar Senha")
        with st.form("trocar_senha"):
            senha_atual = st.text_input("Senha atual", type="password")
            nova_senha = st.text_input("Nova senha", type="password")
            confirmar = st.text_input("Confirmar nova senha", type="password")
            submit = st.form_submit_button("Alterar senha")
            if submit:
                if not senha_atual or not nova_senha or not confirmar:
                    st.error("Preencha todos os campos!")
                elif nova_senha != confirmar:
                    st.error("Nova senha nao confere!")
                elif len(nova_senha) < 6:
                    st.error("Nova senha deve ter pelo menos 6 caracteres!")
                else:
                    conn = sqlite3.connect('marmed.db')
                    c = conn.cursor()
                    senha_hash_atual = hashlib.sha256(senha_atual.encode()).hexdigest()
                    c.execute("SELECT id FROM usuarios WHERE id = ? AND senha = ?",
                              (st.session_state.usuario_id, senha_hash_atual))
                    if c.fetchone():
                        nova_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
                        c.execute("UPDATE usuarios SET senha = ? WHERE id = ?",
                                  (nova_hash, st.session_state.usuario_id))
                        conn.commit()
                        st.success("Senha alterada com sucesso!")
                    else:
                        st.error("Senha atual incorreta!")
                    conn.close()
    
    elif menu == "Dashboard":
        st.markdown('<div class="dashboard-title">Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<div class="dashboard-subtitle">Visao geral do sistema</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown('<div class="metric-card"><div class="metric-value">R$ 0,00</div><div class="metric-label">Total de Contas</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="metric-card"><div class="metric-value">0</div><div class="metric-label">Compras Pendentes</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="metric-card"><div class="metric-value">R$ 0,00</div><div class="metric-label">Superavit</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown('<div class="metric-card"><div class="metric-value">0</div><div class="metric-label">Programas</div></div>', unsafe_allow_html=True)
    
    elif menu == "Contas":
        st.title("Contas")
        esfera = st.selectbox("Esfera", ["Federal", "Estadual", "Municipal", "Transferencia", "Transposicao"])
        st.info(f"Contas da esfera: {esfera}")
    
    elif menu == "Compras":
        st.title("Compras")
        st.info("Modulo de compras")
    
    elif menu == "Superavit Financeiro":
        st.title("Superavit Financeiro")
        st.info("Modulo de superavit financeiro")
    
    elif menu == "Programas de Saude":
        st.title("Programas de Saude")
        st.info("Modulo de programas de saude")
    
    elif menu == "Plano Municipal de Saude":
        st.title("Plano Municipal de Saude")
        st.info("Modulo do Plano Municipal de Saude")
    
    elif menu == "Norte da Minha Gestao":
        st.title("Norte da Minha Gestao")
        st.info("Modulo Norte da Minha Gestao")
    
    elif menu == "Conselho Municipal de Saude":
        st.title("Conselho Municipal de Saude")
        st.info("Modulo do Conselho Municipal de Saude")
