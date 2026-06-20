import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, timedelta
import random
import os
import json

# ============================================
# CONFIGURAÇÕES INICIAIS
# ============================================
st.set_page_config(
    page_title="MARMED - Gestão em Saúde Pública",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Força tema escuro para combinar com o design futurista
st.markdown("""
    <style>
        :root {
            --primary-color: #00d4ff;
            --secondary-color: #ffd700;
            --accent-color: #00b4d8;
            --dark-bg: #0a0e27;
            --deep-teal: #0d2137;
            --glass: rgba(255, 255, 255, 0.08);
            --glass-border: rgba(255, 255, 255, 0.15);
        }
    </style>
""", unsafe_allow_html=True)

# ============================================
# CSS FUTURISTA E ANIMAÇÕES 3D
# ============================================
FUTURISTIC_CSS = """
<style>
/* Reset de cores do Streamlit para tema escuro */
[data-testid="stApp"] {
    background: linear-gradient(135deg, #0a0e27 0%, #0d2137 50%, #061220 100%) !important;
    color: #e0f7ff !important;
    font-family: 'Segoe UI', 'Roboto', sans-serif !important;
}

/* Background animado com partículas */
.particles-bg {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: -1;
    background: linear-gradient(135deg, #0a0e27 0%, #0d2137 40%, #061220 100%);
    overflow: hidden;
}

.wave {
    position: absolute;
    width: 200%;
    height: 200%;
    top: -50%;
    left: -50%;
    background: radial-gradient(ellipse at 30% 50%, rgba(0, 212, 255, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 70% 50%, rgba(0, 180, 216, 0.06) 0%, transparent 50%);
    animation: waveMove 20s ease-in-out infinite;
}

@keyframes waveMove {
    0%, 100% { transform: translate(0, 0) rotate(0deg); }
    50% { transform: translate(5%, 3%) rotate(3deg); }
}

.particle {
    position: absolute;
    border-radius: 50%;
    background: rgba(0, 212, 255, 0.6);
    box-shadow: 0 0 10px rgba(0, 212, 255, 0.8);
    animation: floatUp linear infinite;
}

@keyframes floatUp {
    0% { transform: translateY(100vh) scale(0); opacity: 0; }
    10% { opacity: 1; }
    90% { opacity: 1; }
    100% { transform: translateY(-100vh) scale(1.5); opacity: 0; }
}

.dna-helix {
    position: absolute;
    width: 2px;
    height: 100px;
    background: linear-gradient(180deg, transparent, rgba(255, 215, 0, 0.6), transparent);
    animation: dnaSpin 8s ease-in-out infinite;
}

@keyframes dnaSpin {
    0%, 100% { transform: rotateY(0deg) translateY(0); }
    50% { transform: rotateY(180deg) translateY(-30px); }
}

/* Hexágonos flutuantes - quebra-cabeça */
.hex {
    position: absolute;
    width: 60px;
    height: 34px;
    background: rgba(0, 212, 255, 0.1);
    border: 1px solid rgba(0, 212, 255, 0.3);
    clip-path: polygon(25% 0%, 75% 0%, 100% 50%, 75% 100%, 25% 100%, 0% 50%);
    animation: hexFloat 15s ease-in-out infinite;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    color: rgba(0, 212, 255, 0.8);
}

@keyframes hexFloat {
    0%, 100% { transform: translateY(0) rotate(0deg); opacity: 0.3; }
    50% { transform: translateY(-40px) rotate(10deg); opacity: 0.8; }
}

/* Cards com efeito 3D e glassmorphism */
.glass-card {
    background: rgba(255, 255, 255, 0.06) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 20px !important;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4), 0 0 30px rgba(0, 212, 255, 0.1) !important;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    transform-style: preserve-3d !important;
    animation: cardBob 4s ease-in-out infinite !important;
}

.glass-card:hover {
    transform: translateY(-10px) rotateX(5deg) rotateY(5deg) scale(1.02) !important;
    box-shadow: 0 30px 60px rgba(0, 0, 0, 0.5), 0 0 50px rgba(0, 212, 255, 0.3) !important;
    border-color: rgba(0, 212, 255, 0.5) !important;
}

@keyframes cardBob {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
}

/* Cards de métricas específicos */
.metric-card {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.12), rgba(0, 180, 216, 0.06)) !important;
    border-left: 4px solid #00d4ff !important;
    position: relative;
    overflow: hidden;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: linear-gradient(45deg, transparent, rgba(255, 255, 255, 0.05), transparent);
    transform: rotate(45deg);
    animation: shimmer 6s infinite;
}

@keyframes shimmer {
    0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
    100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
}

.metric-card:nth-child(2) { border-left-color: #ffd700 !important; }
.metric-card:nth-child(3) { border-left-color: #00ff88 !important; }
.metric-card:nth-child(4) { border-left-color: #ff6b6b !important; }
.metric-card:nth-child(5) { border-left-color: #a855f7 !important; }

/* Título 3D MARMED */
.title-3d {
    font-size: 4rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.15em;
    background: linear-gradient(135deg, #00d4ff 0%, #ffffff 50%, #ffd700 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-shadow: 0 0 30px rgba(0, 212, 255, 0.5), 0 0 60px rgba(0, 212, 255, 0.3);
    animation: titleGlow 3s ease-in-out infinite;
    position: relative;
}

.title-3d::after {
    content: 'MARMED';
    position: absolute;
    left: 0;
    top: 0;
    z-index: -1;
    color: rgba(0, 212, 255, 0.3);
    filter: blur(15px);
    -webkit-text-fill-color: rgba(0, 212, 255, 0.3);
}

@keyframes titleGlow {
    0%, 100% { filter: drop-shadow(0 0 20px rgba(0, 212, 255, 0.6)); }
    50% { filter: drop-shadow(0 0 40px rgba(255, 215, 0, 0.6)); }
}

/* Sidebar glass */
[data-testid="stSidebar"] {
    background: rgba(10, 14, 39, 0.85) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
}

[data-testid="stSidebar"] .css-1d391kg {
    background: transparent !important;
}

/* Botões futuristas */
.stButton > button {
    background: linear-gradient(135deg, #00d4ff 0%, #0077b6 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.4) !important;
    transition: all 0.3s ease !important;
    animation: buttonPulse 2s ease-in-out infinite !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 0 40px rgba(0, 212, 255, 0.7) !important;
    filter: brightness(1.2) !important;
}

@keyframes buttonPulse {
    0%, 100% { box-shadow: 0 0 20px rgba(0, 212, 255, 0.4); }
    50% { box-shadow: 0 0 35px rgba(0, 212, 255, 0.7); }
}

/* Inputs com neon */
.stTextInput > div > div > input,
.stPasswordInput > div > div > input,
.stDateInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > select,
.stTextArea > div > div > textarea {
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    color: #e0f7ff !important;
    border-radius: 12px !important;
    transition: all 0.3s ease !important;
}

.stTextInput > div > div > input:focus,
.stPasswordInput > div > div > input:focus,
.stDateInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #00d4ff !important;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.4) !important;
    outline: none !important;
}

/* Animação de heartbeat */
.heartbeat {
    display: inline-block;
    animation: heartbeat 1.5s ease-in-out infinite;
}

@keyframes heartbeat {
    0%, 100% { transform: scale(1); }
    15% { transform: scale(1.3); }
    30% { transform: scale(1); }
    45% { transform: scale(1.15); }
}

/* Avatar com pulse */
.avatar-pulse {
    width: 70px;
    height: 70px;
    border-radius: 50%;
    background: linear-gradient(135deg, #00d4ff, #0077b6);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    color: white;
    box-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
    animation: avatarPulse 2s ease-in-out infinite;
}

@keyframes avatarPulse {
    0%, 100% { box-shadow: 0 0 20px rgba(0, 212, 255, 0.5); }
    50% { box-shadow: 0 0 50px rgba(0, 212, 255, 0.9); }
}

/* Tabelas futuristas */
.stDataFrame {
    border-radius: 15px !important;
    overflow: hidden !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.stDataFrame th {
    background: rgba(0, 212, 255, 0.2) !important;
    color: #00d4ff !important;
    font-weight: 700 !important;
}

.stDataFrame td {
    background: rgba(255, 255, 255, 0.03) !important;
    color: #e0f7ff !important;
}

.stDataFrame tr:hover td {
    background: rgba(0, 212, 255, 0.1) !important;
}

/* Loader de quebra-cabeça */
.puzzle-loader {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: #0a0e27;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    transition: opacity 0.8s ease;
}

.puzzle-loader.hidden {
    opacity: 0;
    pointer-events: none;
}

.puzzle-piece {
    width: 50px;
    height: 50px;
    background: linear-gradient(135deg, #00d4ff, #ffd700);
    margin: 5px;
    display: inline-block;
    animation: puzzleAssemble 1.5s ease-in-out infinite alternate;
    clip-path: polygon(0 0, 70% 0, 70% 30%, 100% 30%, 100% 100%, 30% 100%, 30% 70%, 0 70%);
}

@keyframes puzzleAssemble {
    0% { transform: translateY(0) rotate(0deg); opacity: 0.5; }
    100% { transform: translateY(-20px) rotate(15deg); opacity: 1; }
}

/* Conectores de quebra-cabeça nos cards */
.puzzle-connector {
    position: absolute;
    width: 20px;
    height: 20px;
    background: rgba(0, 212, 255, 0.3);
    border-radius: 50%;
    z-index: 1;
}

/* Esconde elementos padrão do Streamlit que não combinam */
footer { display: none !important; }
#MainMenu { visibility: hidden !important; }

/* Estilo de tabs */
.stTabs [role="tablist"] {
    background: rgba(255, 255, 255, 0.05) !important;
    border-radius: 15px !important;
    padding: 5px !important;
}

.stTabs [role="tab"] {
    color: #e0f7ff !important;
    border-radius: 10px !important;
    transition: all 0.3s ease !important;
}

.stTabs [role="tab"][aria-selected="true"] {
    background: rgba(0, 212, 255, 0.2) !important;
    color: #00d4ff !important;
    box-shadow: 0 0 15px rgba(0, 212, 255, 0.3) !important;
}

/* Expander futurista */
.streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.06) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #e0f7ff !important;
}

/* Animação de fade-in para transições de página */
.fade-in {
    animation: fadeIn 0.6s ease-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Cursor personalizado */
body {
    cursor: default;
}

a, button, input, select, textarea, [role="button"] {
    cursor: pointer !important;
}
</style>
"""

BACKGROUND_HTML = """
<div class="particles-bg">
    <div class="wave"></div>
    <div id="particles-container"></div>
</div>
<script>
(function() {
    const container = document.getElementById('particles-container');
    const icons = ['✚', '❤', '🧬', '💉', '➕'];
    
    // Criar partículas
    for (let i = 0; i < 50; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        p.style.left = Math.random() * 100 + '%';
        p.style.width = Math.random() * 6 + 2 + 'px';
        p.style.height = p.style.width;
        p.style.animationDuration = Math.random() * 15 + 10 + 's';
        p.style.animationDelay = Math.random() * 10 + 's';
        container.appendChild(p);
    }
    
    // Criar DNA hélices
    for (let i = 0; i < 8; i++) {
        const dna = document.createElement('div');
        dna.className = 'dna-helix';
        dna.style.left = Math.random() * 100 + '%';
        dna.style.top = Math.random() * 100 + '%';
        dna.style.animationDuration = Math.random() * 5 + 6 + 's';
        dna.style.animationDelay = Math.random() * 3 + 's';
        container.appendChild(dna);
    }
    
    // Criar hexágonos de quebra-cabeça
    for (let i = 0; i < 12; i++) {
        const hex = document.createElement('div');
        hex.className = 'hex';
        hex.innerHTML = icons[Math.floor(Math.random() * icons.length)];
        hex.style.left = Math.random() * 95 + '%';
        hex.style.top = Math.random() * 95 + '%';
        hex.style.animationDuration = Math.random() * 10 + 12 + 's';
        hex.style.animationDelay = Math.random() * 5 + 's';
        container.appendChild(hex);
    }
})();
</script>
"""

LOADER_HTML = """
<div class="puzzle-loader" id="puzzleLoader">
    <div style="margin-bottom: 30px;">
        <div class="puzzle-piece" style="animation-delay: 0s;"></div>
        <div class="puzzle-piece" style="animation-delay: 0.2s;"></div>
        <div class="puzzle-piece" style="animation-delay: 0.4s;"></div>
    </div>
    <h2 style="color: #00d4ff; font-weight: 700; letter-spacing: 3px;">MARMED</h2>
    <p style="color: rgba(255,255,255,0.6);">Montando sistema de saúde...</p>
</div>
<script>
window.addEventListener('load', function() {
    setTimeout(function() {
        const loader = document.getElementById('puzzleLoader');
        if (loader) {
            loader.classList.add('hidden');
        }
    }, 1800);
});
</script>
"""

def inject_design():
    """Injeta CSS e HTML futurista."""
    st.markdown(FUTURISTIC_CSS, unsafe_allow_html=True)
    st.markdown(BACKGROUND_HTML, unsafe_allow_html=True)
    st.markdown(LOADER_HTML, unsafe_allow_html=True)

# ============================================
# BANCO DE DADOS
# ============================================
DB_FILE = "marmed.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nome TEXT,
            perfil TEXT DEFAULT 'admin'
        )
    ''')
    
    # Contas a Pagar
    c.execute('''
        CREATE TABLE IF NOT EXISTS contas_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fornecedor TEXT NOT NULL,
            descricao TEXT,
            valor REAL NOT NULL,
            vencimento TEXT NOT NULL,
            status TEXT DEFAULT 'Pendente',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Contas a Receber
    c.execute('''
        CREATE TABLE IF NOT EXISTS contas_receber (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fonte TEXT NOT NULL,
            descricao TEXT,
            valor REAL NOT NULL,
            recebimento TEXT NOT NULL,
            status TEXT DEFAULT 'Pendente',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Empenhos
    c.execute('''
        CREATE TABLE IF NOT EXISTS empenhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT UNIQUE NOT NULL,
            fornecedor TEXT NOT NULL,
            objeto TEXT,
            valor REAL NOT NULL,
            data_empenho TEXT NOT NULL,
            status TEXT DEFAULT 'Ativo',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Licitações
    c.execute('''
        CREATE TABLE IF NOT EXISTS licitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            modalidade TEXT NOT NULL,
            objeto TEXT,
            valor_estimado REAL,
            data_abertura TEXT,
            status TEXT DEFAULT 'Em Andamento',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Contratos
    c.execute('''
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            fornecedor TEXT NOT NULL,
            objeto TEXT,
            valor REAL NOT NULL,
            inicio TEXT NOT NULL,
            fim TEXT NOT NULL,
            status TEXT DEFAULT 'Vigente',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Inserir usuário admin padrão se não existir
    admin_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    c.execute("SELECT id FROM usuarios WHERE username = 'admin'")
    if not c.fetchone():
        c.execute('''
            INSERT INTO usuarios (username, password_hash, nome, perfil)
            VALUES (?, ?, ?, ?)
        ''', ('admin', admin_hash, 'Administrador', 'admin'))
    
    conn.commit()
    conn.close()

init_db()

# ============================================
# FUNÇÕES AUXILIARES
# ============================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_login(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    if user and user['password_hash'] == hash_password(password):
        return user
    return None

def get_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def update_password(user_id, new_password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE usuarios SET password_hash = ? WHERE id = ?",
              (hash_password(new_password), user_id))
    conn.commit()
    conn.close()

def format_currency(value):
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def status_color(status):
    status = str(status).lower()
    if 'pago' in status or 'recebido' in status or 'ativo' in status or 'vigente' in status:
        return '#00ff88'
    elif 'pendente' in status or 'em andamento' in status:
        return '#ffd700'
    elif 'atrasado' in status or 'vencido' in status or 'cancelado' in status:
        return '#ff6b6b'
    return '#00d4ff'

# ============================================
# CRUD GENÉRICO
# ============================================
def crud_page(title, table_name, columns, form_fields, order_by='id DESC'):
    st.markdown(f"<<div class='fade-in'>", unsafe_allow_html=True)
    st.markdown(f"<<h2 style='color: #00d4ff; margin-bottom: 20px;'>✚ {title}</h2>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    c = conn.cursor()
    
    tab1, tab2, tab3 = st.tabs(["📋 Listar", "➕ Cadastrar", "✏️ Editar/Excluir"])
    
    # Listar
    with tab1:
        c.execute(f"SELECT * FROM {table_name} ORDER BY {order_by}")
        rows = c.fetchall()
        if rows:
            df = pd.DataFrame(rows, columns=[col[0] for col in c.description])
            df = df.drop(columns=['created_at'], errors='ignore')
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro encontrado.")
    
    # Cadastrar
    with tab2:
        with st.form(f"form_cadastrar_{table_name}", clear_on_submit=True):
            values = {}
            for field in form_fields:
                key = field['name']
                label = field['label']
                ftype = field['type']
                if ftype == 'text':
                    values[key] = st.text_input(label, key=f"cad_{table_name}_{key}")
                elif ftype == 'textarea':
                    values[key] = st.text_area(label, key=f"cad_{table_name}_{key}")
                elif ftype == 'number':
                    values[key] = st.number_input(label, min_value=0.0, step=0.01, key=f"cad_{table_name}_{key}")
                elif ftype == 'date':
                    values[key] = st.date_input(label, key=f"cad_{table_name}_{key}").strftime('%Y-%m-%d')
                elif ftype == 'select':
                    values[key] = st.selectbox(label, field['options'], key=f"cad_{table_name}_{key}")
            
            submitted = st.form_submit_button("💾 Salvar Cadastro")
            if submitted:
                try:
                    cols = list(values.keys())
                    vals = list(values.values())
                    placeholders = ', '.join(['?' for _ in vals])
                    c.execute(f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES ({placeholders})", vals)
                    conn.commit()
                    st.success("Registro cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar: {e}")
    
    # Editar/Excluir
    with tab3:
        c.execute(f"SELECT id FROM {table_name}")
        ids = [row[0] for row in c.fetchall()]
        if not ids:
            st.info("Nenhum registro para editar.")
        else:
            selected_id = st.selectbox("Selecione o registro", ids, key=f"edit_id_{table_name}")
            c.execute(f"SELECT * FROM {table_name} WHERE id = ?", (selected_id,))
            row = c.fetchone()
            
            if row:
                with st.form(f"form_editar_{table_name}"):
                    edit_values = {}
                    for field in form_fields:
                        key = field['name']
                        label = field['label']
                        ftype = field['type']
                        current_val = row[key] if key in row.keys() else None
                        if ftype == 'text':
                            edit_values[key] = st.text_input(label, value=current_val or '', key=f"edit_{table_name}_{key}")
                        elif ftype == 'textarea':
                            edit_values[key] = st.text_area(label, value=current_val or '', key=f"edit_{table_name}_{key}")
                        elif ftype == 'number':
                            edit_values[key] = st.number_input(label, min_value=0.0, step=0.01, value=float(current_val or 0), key=f"edit_{table_name}_{key}")
                        elif ftype == 'date':
                            try:
                                d = datetime.strptime(current_val, '%Y-%m-%d').date() if current_val else datetime.today().date()
                            except:
                                d = datetime.today().date()
                            edit_values[key] = st.date_input(label, value=d, key=f"edit_{table_name}_{key}").strftime('%Y-%m-%d')
                        elif ftype == 'select':
                            edit_values[key] = st.selectbox(label, field['options'], index=field['options'].index(current_val) if current_val in field['options'] else 0, key=f"edit_{table_name}_{key}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_btn = st.form_submit_button("🔄 Atualizar")
                    with col2:
                        delete_btn = st.form_submit_button("🗑️ Excluir")
                    
                    if update_btn:
                        try:
                            sets = ', '.join([f"{k} = ?" for k in edit_values.keys()])
                            vals = list(edit_values.values()) + [selected_id]
                            c.execute(f"UPDATE {table_name} SET {sets} WHERE id = ?", vals)
                            conn.commit()
                            st.success("Registro atualizado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar: {e}")
                    
                    if delete_btn:
                        try:
                            c.execute(f"DELETE FROM {table_name} WHERE id = ?", (selected_id,))
                            conn.commit()
                            st.warning("Registro excluído com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao excluir: {e}")
    
    conn.close()
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# PÁGINAS ESPECÍFICAS
# ============================================
def page_contas_pagar():
    fields = [
        {'name': 'fornecedor', 'label': 'Fornecedor', 'type': 'text'},
        {'name': 'descricao', 'label': 'Descrição', 'type': 'textarea'},
        {'name': 'valor', 'label': 'Valor (R$)', 'type': 'number'},
        {'name': 'vencimento', 'label': 'Data de Vencimento', 'type': 'date'},
        {'name': 'status', 'label': 'Status', 'type': 'select', 'options': ['Pendente', 'Pago', 'Atrasado', 'Cancelado']}
    ]
    crud_page("Contas a Pagar", "contas_pagar", fields, fields, 'vencimento DESC')

def page_contas_receber():
    fields = [
        {'name': 'fonte', 'label': 'Fonte de Receita', 'type': 'text'},
        {'name': 'descricao', 'label': 'Descrição', 'type': 'textarea'},
        {'name': 'valor', 'label': 'Valor (R$)', 'type': 'number'},
        {'name': 'recebimento', 'label': 'Data de Recebimento', 'type': 'date'},
        {'name': 'status', 'label': 'Status', 'type': 'select', 'options': ['Pendente', 'Recebido', 'Atrasado', 'Cancelado']}
    ]
    crud_page("Contas a Receber", "contas_receber", fields, fields, 'recebimento DESC')

def page_empenhos():
    fields = [
        {'name': 'numero', 'label': 'Número do Empenho', 'type': 'text'},
        {'name': 'fornecedor', 'label': 'Fornecedor', 'type': 'text'},
        {'name': 'objeto', 'label': 'Objeto', 'type': 'textarea'},
        {'name': 'valor', 'label': 'Valor Empenhado (R$)', 'type': 'number'},
        {'name': 'data_empenho', 'label': 'Data do Empenho', 'type': 'date'},
        {'name': 'status', 'label': 'Status', 'type': 'select', 'options': ['Ativo', 'Liquidado', 'Cancelado', 'Anulado']}
    ]
    crud_page("Empenhos", "empenhos", fields, fields, 'data_empenho DESC')

def page_licitacoes():
    fields = [
        {'name': 'numero', 'label': 'Número da Licitação', 'type': 'text'},
        {'name': 'modalidade', 'label': 'Modalidade', 'type': 'select', 'options': ['Pregão', 'Tomada de Preços', 'Concorrência', 'Convite', 'Dispensa', 'Inexigibilidade']},
        {'name': 'objeto', 'label': 'Objeto', 'type': 'textarea'},
        {'name': 'valor_estimado', 'label': 'Valor Estimado (R$)', 'type': 'number'},
        {'name': 'data_abertura', 'label': 'Data de Abertura', 'type': 'date'},
        {'name': 'status', 'label': 'Status', 'type': 'select', 'options': ['Em Andamento', 'Concluída', 'Cancelada', 'Adiada']}
    ]
    crud_page("Licitações", "licitacoes", fields, fields, 'data_abertura DESC')

def page_contratos():
    fields = [
        {'name': 'numero', 'label': 'Número do Contrato', 'type': 'text'},
        {'name': 'fornecedor', 'label': 'Fornecedor/Contratado', 'type': 'text'},
        {'name': 'objeto', 'label': 'Objeto', 'type': 'textarea'},
        {'name': 'valor', 'label': 'Valor do Contrato (R$)', 'type': 'number'},
        {'name': 'inicio', 'label': 'Data de Início', 'type': 'date'},
        {'name': 'fim', 'label': 'Data de Término', 'type': 'date'},
        {'name': 'status', 'label': 'Status', 'type': 'select', 'options': ['Vigente', 'Concluído', 'Rescindido', 'Aditivado']}
    ]
    crud_page("Contratos", "contratos", fields, fields, 'inicio DESC')

# ============================================
# DASHBOARD
# ============================================
def page_dashboard():
    st.markdown("<<div class='fade-in'>", unsafe_allow_html=True)
    
    # Header com heartbeat
    st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #00d4ff; font-weight: 800;">
                <span class="heartbeat">❤</span> Painel de Gestão MARMED
            </h1>
            <p style="color: rgba(255,255,255,0.6); font-size: 1.1rem;">
                Prefeitura Municipal de Luminárias - MG
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Cálculo de métricas
    c.execute("SELECT COALESCE(SUM(valor), 0) FROM contas_pagar WHERE status != 'Cancelado'")
    total_pagar = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(valor), 0) FROM contas_pagar WHERE status = 'Pendente'")
    pendente_pagar = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(valor), 0) FROM contas_receber WHERE status != 'Cancelado'")
    total_receber = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(valor), 0) FROM empenhos WHERE status = 'Ativo'")
    total_empenhos = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(valor), 0) FROM contratos WHERE status = 'Vigente'")
    total_contratos = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM licitacoes WHERE status = 'Em Andamento'")
    licitacoes_ativas = c.fetchone()[0]
    
    conn.close()
    
    # Cards de métricas
    metrics = [
        ("💰 Contas a Pagar", format_currency(total_pagar), "Total em débitos", "#00d4ff"),
        ("💵 Contas a Receber", format_currency(total_receber), "Total a receber", "#ffd700"),
        ("📋 Empenhos Ativos", format_currency(total_empenhos), "Compromissos", "#00ff88"),
        ("📄 Contratos Vigentes", format_currency(total_contratos), "Valor contratado", "#ff6b6b"),
        ("⚖️ Licitações Ativas", str(licitacoes_ativas), "Processos em andamento", "#a855f7")
    ]
    
    cols = st.columns(5)
    for i, (title, value, desc, color) in enumerate(metrics):
        with cols[i]:
            st.markdown(f"""
                <div class="glass-card metric-card" style="padding: 25px; text-align: center; min-height: 180px;">
                    <div style="font-size: 2.2rem; margin-bottom: 10px;">{title.split(' ')[0]}</div>
                    <h3 style="margin: 0; color: {color}; font-size: 1.1rem; font-weight: 700;">{' '.join(title.split(' ')[1:])}</h3>
                    <p style="font-size: 1.6rem; font-weight: 800; color: #ffffff; margin: 10px 0;">{value}</p>
                    <p style="font-size: 0.85rem; color: rgba(255,255,255,0.5); margin: 0;">{desc}</p>
                </div>
            """, unsafe_allow_html=True)
    
    # Gráficos e informações adicionais
    st.markdown("<<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div class="glass-card" style="padding: 25px;">
                <h3 style="color: #00d4ff; margin-top: 0;">📊 Resumo Financeiro</h3>
        """, unsafe_allow_html=True)
        
        resumo_data = {
            'Indicador': ['Total a Pagar', 'Pendente a Pagar', 'Total a Receber', 'Saldo Projetado', 'Empenhos', 'Contratos'],
            'Valor': [format_currency(total_pagar), format_currency(pendente_pagar), format_currency(total_receber),
                      format_currency(total_receber - total_pagar), format_currency(total_empenhos), format_currency(total_contratos)]
        }
        st.dataframe(pd.DataFrame(resumo_data), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="glass-card" style="padding: 25px;">
                <h3 style="color: #ffd700; margin-top: 0;">🏥 Status da Saúde Pública</h3>
                <div style="margin: 15px 0; padding: 15px; background: rgba(0,255,136,0.1); border-radius: 10px; border-left: 4px solid #00ff88;">
                    <strong style="color: #00ff88;">✓ Sistema operacional</strong><br>
                    <span style="color: rgba(255,255,255,0.7);">Todos os módulos ativos e sincronizados.</span>
                </div>
                <div style="margin: 15px 0; padding: 15px; background: rgba(0,212,255,0.1); border-radius: 10px; border-left: 4px solid #00d4ff;">
                    <strong style="color: #00d4ff;">✓ Transparência ativa</strong><br>
                    <span style="color: rgba(255,255,255,0.7);">Dados de despesas e receitas atualizados.</span>
                </div>
                <div style="margin: 15px 0; padding: 15px; background: rgba(255,215,0,0.1); border-radius: 10px; border-left: 4px solid #ffd700;">
                    <strong style="color: #ffd700;">✓ Licitações em dia</strong><br>
                    <span style="color: rgba(255,255,255,0.7);">{licitacoes} processo(s) em andamento.</span>
                </div>
            </div>
        """.format(licitacoes=licitacoes_ativas), unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# RELATÓRIOS
# ============================================
def page_relatorios():
    st.markdown("<<div class='fade-in'>", unsafe_allow_html=True)
    st.markdown("<<h2 style='color: #00d4ff; margin-bottom: 20px;'>📈 Relatórios e Análises</h2>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    c = conn.cursor()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Financeiro", "📋 Empenhos", "⚖️ Licitações", "📄 Contratos"])
    
    with tab1:
        c.execute("SELECT 'Contas a Pagar' as tipo, status, COUNT(*) as quantidade, SUM(valor) as total FROM contas_pagar GROUP BY status")
        rows_pagar = c.fetchall()
        c.execute("SELECT 'Contas a Receber' as tipo, status, COUNT(*) as quantidade, SUM(valor) as total FROM contas_receber GROUP BY status")
        rows_receber = c.fetchall()
        
        data = []
        for row in rows_pagar + rows_receber:
            data.append({
                'Tipo': row[0],
                'Status': row[1],
                'Quantidade': row[2],
                'Total': format_currency(row[3])
            })
        
        if data:
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum dado financeiro disponível.")
    
    with tab2:
        c.execute("SELECT status, COUNT(*) as quantidade, SUM(valor) as total FROM empenhos GROUP BY status")
        rows = c.fetchall()
        if rows:
            data = [{'Status': r[0], 'Quantidade': r[1], 'Total': format_currency(r[2])} for r in rows]
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum empenho registrado.")
    
    with tab3:
        c.execute("SELECT status, COUNT(*) as quantidade, SUM(valor_estimado) as total FROM licitacoes GROUP BY status")
        rows = c.fetchall()
        if rows:
            data = [{'Status': r[0], 'Quantidade': r[1], 'Total Estimado': format_currency(r[2])} for r in rows]
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma licitação registrada.")
    
    with tab4:
        c.execute("SELECT status, COUNT(*) as quantidade, SUM(valor) as total FROM contratos GROUP BY status")
        rows = c.fetchall()
        if rows:
            data = [{'Status': r[0], 'Quantidade': r[1], 'Total': format_currency(r[2])} for r in rows]
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum contrato registrado.")
    
    conn.close()
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# TROCAR SENHA
# ============================================
def page_trocar_senha():
    st.markdown("<<div class='fade-in'>", unsafe_allow_html=True)
    st.markdown("<<h2 style='color: #00d4ff; margin-bottom: 20px;'>🔐 Trocar Senha</h2>", unsafe_allow_html=True)
    
    user = get_user(st.session_state['user_id'])
    
    with st.form("form_trocar_senha"):
        st.markdown(f"<<p style='color: rgba(255,255,255,0.7);'>Usuário: <strong style='color: #00d4ff;'>{user['username']}</strong></p>", unsafe_allow_html=True)
        senha_atual = st.text_input("Senha Atual", type="password", key="senha_atual")
        nova_senha = st.text_input("Nova Senha", type="password", key="nova_senha")
        confirmar_senha = st.text_input("Confirmar Nova Senha", type="password", key="confirmar_senha")
        
        submitted = st.form_submit_button("🔄 Alterar Senha")
        if submitted:
            if not senha_atual or not nova_senha or not confirmar_senha:
                st.warning("Preencha todos os campos.")
            elif hash_password(senha_atual) != user['password_hash']:
                st.error("Senha atual incorreta.")
            elif nova_senha != confirmar_senha:
                st.error("As novas senhas não conferem.")
            elif len(nova_senha) < 6:
                st.warning("A nova senha deve ter pelo menos 6 caracteres.")
            else:
                update_password(user['id'], nova_senha)
                st.success("Senha alterada com sucesso! Faça login novamente.")
                if st.button("Sair"):
                    st.session_state.clear()
                    st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# LOGIN
# ============================================
def page_login():
    st.markdown("<<div class='fade-in'>", unsafe_allow_html=True)
    
    # Container centralizado
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div class="glass-card" style="padding: 50px 40px; text-align: center; margin-top: 10vh; animation: cardBob 3s ease-in-out infinite;">
                <div style="font-size: 5rem; margin-bottom: 15px;">🧩</div>
                <h1 class="title-3d" style="font-size: 3.5rem; margin-bottom: 10px;">MARMED</h1>
                <p style="color: rgba(255,255,255,0.6); font-size: 1.1rem; margin-bottom: 30px;">
                    Gestão em Saúde Pública<br>Prefeitura de Luminárias-MG
                </p>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("👤 Usuário", key="login_user", placeholder="Digite seu usuário")
            password = st.text_input("🔒 Senha", type="password", key="login_pass", placeholder="Digite sua senha")
            
            st.markdown("<<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🔓 Acessar Sistema")
            
            if submitted:
                user = verify_login(username, password)
                if user:
                    st.session_state['authenticated'] = True
                    st.session_state['user_id'] = user['id']
                    st.session_state['username'] = user['username']
                    st.session_state['nome'] = user['nome']
                    st.session_state['page'] = 'dashboard'
                    st.success(f"Bem-vindo, {user['nome'] or user['username']}!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
        
        st.markdown("""
            <p style="color: rgba(255,255,255,0.4); font-size: 0.8rem; margin-top: 20px;">
                🔐 Sistema seguro - Todos os dados são criptografados
            </p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================
# SIDEBAR
# ============================================
def render_sidebar():
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; padding: 20px 0;">
                <div class="avatar-pulse" style="margin: 0 auto 15px auto;">👤</div>
                <h3 style="color: #00d4ff; margin: 0;">{nome}</h3>
                <p style="color: rgba(255,255,255,0.5); font-size: 0.85rem; margin: 5px 0 0 0;">{username}</p>
            </div>
        """.format(nome=st.session_state.get('nome', 'Usuário'), username=st.session_state.get('username', '')), unsafe_allow_html=True)
        
        st.markdown("<<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        
        menu_items = {
            'dashboard': '🏠 Dashboard',
            'contas_pagar': '💰 Contas a Pagar',
            'contas_receber': '💵 Contas a Receber',
            'empenhos': '📋 Empenhos',
            'licitacoes': '⚖️ Licitações',
            'contratos': '📄 Contratos',
            'relatorios': '📈 Relatórios',
            'trocar_senha': '🔐 Trocar Senha'
        }
        
        for key, label in menu_items.items():
            active = st.session_state.get('page', 'dashboard') == key
            if st.button(label, key=f"nav_{key}", use_container_width=True,
                        type="primary" if active else "secondary"):
                st.session_state['page'] = key
                st.rerun()
        
        st.markdown("<<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
        
        if st.button("🚪 Sair do Sistema", key="logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        
        st.markdown("""
            <div style="text-align: center; margin-top: 30px; padding: 15px; background: rgba(0,212,255,0.1); border-radius: 15px; border: 1px solid rgba(0,212,255,0.2);">
                <p style="color: #00d4ff; font-size: 0.85rem; margin: 0;">🏥 MARMED</p>
                <p style="color: rgba(255,255,255,0.5); font-size: 0.75rem; margin: 5px 0 0 0;">Gestão em Saúde Pública</p>
                <p style="color: rgba(255,255,255,0.4); font-size: 0.7rem; margin: 5px 0 0 0;">Luminárias-MG</p>
            </div>
        """, unsafe_allow_html=True)

# ============================================
# MAIN
# ============================================
def main():
    inject_design()
    
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if 'page' not in st.session_state:
        st.session_state['page'] = 'login'
    
    if not st.session_state['authenticated']:
        page_login()
    else:
        render_sidebar()
        
        page = st.session_state.get('page', 'dashboard')
        
        if page == 'dashboard':
            page_dashboard()
        elif page == 'contas_pagar':
            page_contas_pagar()
        elif page == 'contas_receber':
            page_contas_receber()
        elif page == 'empenhos':
            page_empenhos()
        elif page == 'licitacoes':
            page_licitacoes()
        elif page == 'contratos':
            page_contratos()
        elif page == 'relatorios':
            page_relatorios()
        elif page == 'trocar_senha':
            page_trocar_senha()
        else:
            page_dashboard()

if __name__ == "__main__":
    main()
