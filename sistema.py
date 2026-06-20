import streamlit as st
import hashlib
import sqlite3
import pandas as pd
import json
import random
from datetime import datetime, timedelta

st.set_page_config(
    page_title="MARMED - Sistema Integrado",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============== CSS CUSTOMIZADO ==============
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700;800&display=swap');

/* Reset */
* { font-family: 'Montserrat', sans-serif; box-sizing: border-box; }

/* Background gradiente */
.stApp {
    background: linear-gradient(135deg, #0a0e27 0%, #0d2137 50%, #1a3a5c 100%) !important;
    color: #ffffff !important;
}

/* Canvas de partículas */
#particles-canvas {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 0;
    pointer-events: none;
}

/* Container principal */
.main-container {
    position: relative;
    z-index: 10;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
}

/* Cartão de vidro */
.glass-card {
    background: rgba(255, 255, 255, 0.08) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 24px !important;
    padding: 3rem 2.5rem !important;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.4), 0 0 60px rgba(0, 212, 255, 0.1) !important;
    width: 100%;
    max-width: 460px;
    text-align: center;
    perspective: 1000px;
}

/* Logo MARMED 3D animação */
.logo-container {
    display: flex;
    justify-content: center;
    gap: 6px;
    margin-bottom: 1.5rem;
    perspective: 800px;
}

.logo-letter {
    display: inline-block;
    font-size: 3.2rem;
    font-weight: 800;
    color: #00d4ff;
    text-shadow: 0 0 20px rgba(0, 212, 255, 0.6), 0 0 40px rgba(0, 212, 255, 0.3);
    transform-style: preserve-3d;
    opacity: 0;
    animation: flyIn3D 1.2s ease-out forwards;
}

.logo-letter:nth-child(1) { animation-delay: 0.0s; transform: translate3d(-200px, -150px, -300px) rotateX(45deg) rotateY(-60deg); }
.logo-letter:nth-child(2) { animation-delay: 0.15s; transform: translate3d(180px, -200px, -250px) rotateX(-60deg) rotateY(45deg); }
.logo-letter:nth-child(3) { animation-delay: 0.3s; transform: translate3d(0px, -250px, -400px) rotateX(75deg) rotateY(0deg); }
.logo-letter:nth-child(4) { animation-delay: 0.45s; transform: translate3d(-220px, 150px, -350px) rotateX(-45deg) rotateY(60deg); }
.logo-letter:nth-child(5) { animation-delay: 0.6s; transform: translate3d(200px, 180px, -300px) rotateX(30deg) rotateY(-45deg); }
.logo-letter:nth-child(6) { animation-delay: 0.75s; transform: translate3d(0px, 220px, -500px) rotateX(-75deg) rotateY(30deg); }

@keyframes flyIn3D {
    0% {
        opacity: 0;
    }
    30% {
        opacity: 0.5;
    }
    100% {
        opacity: 1;
        transform: translate3d(0, 0, 0) rotateX(0) rotateY(0);
    }
}

/* Subtítulo */
.subtitle {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    letter-spacing: 2px !important;
    margin-bottom: 2.5rem !important;
    text-transform: uppercase;
    text-shadow: 0 0 15px rgba(255, 255, 255, 0.3);
}

/* Labels de usuário e senha */
.login-label {
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    color: #00d4ff !important;
    text-shadow: 0 0 10px rgba(0, 212, 255, 0.5), 0 0 20px rgba(0, 212, 255, 0.3) !important;
    margin-bottom: 0.5rem !important;
    display: block;
    text-align: left;
    letter-spacing: 0.5px;
}

/* Campos de input */
.stTextInput > div > div > input {
    background: rgba(0, 0, 0, 0.25) !important;
    border: 2px solid rgba(0, 212, 255, 0.3) !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    font-size: 1rem !important;
    padding: 1rem 1.2rem !important;
    transition: all 0.3s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color: #00d4ff !important;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.3) !important;
    background: rgba(0, 0, 0, 0.35) !important;
}

/* Botão invisível do form */
.invisible-submit {
    display: none !important;
}

/* Texto Acesso */
.acesso-text {
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    color: #ffffff !important;
    margin-top: 2rem !important;
    letter-spacing: 3px !important;
    text-transform: uppercase;
    opacity: 0.9;
    text-shadow: 0 0 15px rgba(255, 255, 255, 0.2);
}

.acesso-divider {
    width: 80px;
    height: 3px;
    background: linear-gradient(90deg, transparent, #00d4ff, transparent);
    margin: 0 auto 0.8rem auto;
    border-radius: 2px;
}

/* Mensagens de erro */
.stAlert {
    background: rgba(255, 0, 0, 0.15) !important;
    border: 1px solid rgba(255, 100, 100, 0.4) !important;
    color: #ffcccc !important;
    border-radius: 12px !important;
}

/* Dashboard cards */
.metric-card {
    background: rgba(255, 255, 255, 0.08) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
    text-align: center !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
    transition: transform 0.3s ease !important;
}
.metric-card:hover {
    transform: translateY(-5px) !important;
}
.metric-value {
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    color: #00d4ff !important;
}
.metric-label {
    font-size: 0.95rem !important;
    color: rgba(255, 255, 255, 0.8) !important;
    margin-top: 0.5rem !important;
}

/* Tabelas */
.stDataFrame {
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* Sidebar */
.css-1d391kg, .css-163ttbj {
    background: rgba(10, 14, 39, 0.95) !important;
}

/* Botões */
.stButton > button {
    background: linear-gradient(135deg, #00d4ff, #0077b6) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.7rem 1.5rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 25px rgba(0, 212, 255, 0.4) !important;
}

/* Esconder footer e menu padrão */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
</style>

<<canvas id="particles-canvas"></canvas>

<script>
const canvas = document.getElementById('particles-canvas');
const ctx = canvas.getContext('2d');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const particles = [];
for (let i = 0; i < 60; i++) {
    particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        radius: Math.random() * 2 + 0.5,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        alpha: Math.random() * 0.5 + 0.2
    });
}

function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 212, 255, ${p.alpha})`;
        ctx.fill();
    });
    requestAnimationFrame(animate);
}
animate();

window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});
</script>
""", unsafe_allow_html=True)

# ============== BANCO DE DADOS ==============
@st.cache_resource
def get_db():
    conn = sqlite3.connect('marmed.db', check_same_thread=False)
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            nome TEXT NOT NULL,
            email TEXT,
            perfil TEXT DEFAULT 'usuario',
            ativo INTEGER DEFAULT 1,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            objeto TEXT NOT NULL,
            contratada TEXT NOT NULL,
            cnpj TEXT,
            valor REAL DEFAULT 0,
            data_inicio TEXT,
            data_fim TEXT,
            status TEXT DEFAULT 'Ativo',
            gestor TEXT,
            observacoes TEXT,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS financeiro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            tipo TEXT NOT NULL,
            categoria TEXT,
            valor REAL DEFAULT 0,
            data_vencimento TEXT,
            data_pagamento TEXT,
            status TEXT DEFAULT 'Pendente',
            contrato_id INTEGER,
            observacoes TEXT,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contrato_id) REFERENCES contratos(id)
        );
        CREATE TABLE IF NOT EXISTS fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            razao_social TEXT NOT NULL,
            nome_fantasia TEXT,
            cnpj TEXT UNIQUE,
            email TEXT,
            telefone TEXT,
            endereco TEXT,
            categoria TEXT,
            status TEXT DEFAULT 'Ativo',
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS medicamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            principio_ativo TEXT,
            fabricante TEXT,
            codigo TEXT UNIQUE,
            quantidade INTEGER DEFAULT 0,
            valor_unitario REAL DEFAULT 0,
            validade TEXT,
            status TEXT DEFAULT 'Ativo',
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS relatorios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            tipo TEXT,
            conteudo TEXT,
            data_geracao TEXT DEFAULT CURRENT_TIMESTAMP,
            gerado_por TEXT
        );
    ''')
    conn.commit()
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM usuarios WHERE usuario='admin'")
    if c.fetchone()[0] == 0:
        senha_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
        c.execute("""
            INSERT INTO usuarios (usuario, senha_hash, nome, email, perfil)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", senha_hash, "Administrador MARMED", "admin@marmed.com", "admin"))
        conn.commit()
    return conn

def verify_password(password, stored_hash):
    return hashlib.sha256(password.encode()).hexdigest() == stored_hash

def get_user(username):
    conn = init_db()
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE usuario=? AND ativo=1", (username,))
    return c.fetchone()

# ============== ESTADOS DE SESSÃO ==============
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'nome' not in st.session_state:
    st.session_state.nome = None
if 'perfil' not in st.session_state:
    st.session_state.perfil = None
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'Dashboard'
if 'login_error' not in st.session_state:
    st.session_state.login_error = None

# ============== PÁGINA DE LOGIN ==============
def login_page():
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    # Logo MARMED 3D animado
    st.markdown('''
        <div class="logo-container">
            <span class="logo-letter">M</span>
            <span class="logo-letter">A</span>
            <span class="logo-letter">R</span>
            <span class="logo-letter">M</span>
            <span class="logo-letter">E</span>
            <span class="logo-letter">D</span>
        </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('<div class="subtitle">SISTEMA INTEGRADO DE GESTAO</div>', unsafe_allow_html=True)
    
    # Formulário de login (submissão por Enter)
    with st.form("login_form", clear_on_submit=False):
        st.markdown('<label class="login-label">👤 Usuário</label>', unsafe_allow_html=True)
        username = st.text_input("", key="login_user", placeholder="Digite seu usuário", label_visibility="collapsed")
        
        st.markdown('<label class="login-label">🔒 Senha</label>', unsafe_allow_html=True)
        password = st.text_input("", type="password", key="login_pass", placeholder="Digite sua senha", label_visibility="collapsed")
        
        # Botão invisível que mantém funcionalidade de Enter
        submitted = st.form_submit_button("Entrar", use_container_width=True)
    
    # Ocultar botão via CSS após renderização
    st.markdown('''
        <style>
        div[data-testid="stForm"] button[kind="secondaryFormSubmit"] {
            display: none !important;
        }
        </style>
    ''', unsafe_allow_html=True)
    
    # Texto Acesso no rodapé do card
    st.markdown('<div class="acesso-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="acesso-text">Acesso</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # fecha glass-card
    st.markdown('</div>', unsafe_allow_html=True)  # fecha main-container
    
    if submitted:
        if not username or not password:
            st.error("⚠️ Preencha usuário e senha.")
        else:
            user = get_user(username)
            if user and verify_password(password, user[2]):
                st.session_state.autenticado = True
                st.session_state.usuario = user[1]
                st.session_state.nome = user[3]
                st.session_state.perfil = user[5]
                st.session_state.pagina = 'Dashboard'
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos.")

# ============== SIDEBAR ==============
def sidebar():
    if not st.session_state.autenticado:
        return
    
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: #00d4ff; font-weight: 800;">MARMED</h2>
            <p style="color: rgba(255,255,255,0.7);">Olá, {st.session_state.nome}</p>
        </div>
        """, unsafe_allow_html=True)
        
        paginas = ['Dashboard', 'Contratos', 'Financeiro', 'Fornecedores', 'Medicamentos', 'Usuários', 'Relatórios', 'Trocar Senha']
        
        for pagina in paginas:
            if pagina == 'Usuários' and st.session_state.perfil != 'admin':
                continue
            if st.button(pagina, key=f"nav_{pagina}", use_container_width=True):
                st.session_state.pagina = pagina
                st.rerun()
        
        st.markdown('<hr style="border-color: rgba(255,255,255,0.1); margin: 2rem 0;">', unsafe_allow_html=True)
        if st.button('🚪 Sair', key='btn_sair', use_container_width=True):
            for key in ['autenticado', 'usuario', 'nome', 'perfil', 'pagina']:
                st.session_state[key] = None if key in ['usuario', 'nome', 'perfil', 'pagina'] else False
            st.rerun()

# ============== DASHBOARD ==============
def dashboard():
    st.markdown(<<h1 style='color: #ffffff; font-weight: 800;'>Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: rgba(255,255,255,0.7);'>Visão geral do sistema MARMED</p>", unsafe_allow_html=True)
    
    conn = init_db()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM contratos")
    total_contratos = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(valor), 0) FROM financeiro WHERE tipo='Receita'")
    total_receitas = c.fetchone()[0] or 0
    c.execute("SELECT COALESCE(SUM(valor), 0) FROM financeiro WHERE tipo='Despesa'")
    total_despesas = c.fetchone()[0] or 0
    c.execute("SELECT COUNT(*) FROM fornecedores WHERE status='Ativo'")
    total_fornecedores = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM medicamentos")
    total_medicamentos = c.fetchone()[0]
    
    col1, col2, col3, col4, col5 = st.columns(5)
    metricas = [
        (col1, "Contratos", total_contratos, "📄"),
        (col2, "Receitas", f"R$ {total_receitas:,.2f}", "💰"),
        (col3, "Despesas", f"R$ {total_despesas:,.2f}", "💸"),
        (col4, "Fornecedores", total_fornecedores, "🏢"),
        (col5, "Medicamentos", total_medicamentos, "💊")
    ]
    
    for col, label, value, icon in metricas:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 2rem;">{icon}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>, unsafe_allow_html=True)
    
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("<h3 style='color: #00d4ff;'>Contratos Recentes</h3>", unsafe_allow_html=True)
        df = pd.read_sql_query("SELECT numero, contratada, valor, status FROM contratos ORDER BY id DESC LIMIT 5", conn)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    with col_right:
        st.markdown("<h3 style='color: #00d4ff;'>Movimentações Financeiras</h3>", unsafe_allow_html=True)
        df = pd.read_sql_query("SELECT descricao, tipo, valor, status FROM financeiro ORDER BY id DESC LIMIT 5", conn)
        st.dataframe(df, use_container_width=True, hide_index=True)

# ============== CRUD GENÉRICO ==============
def crud_page(tabela, colunas, titulo, form_fields):
    st.markdown(f"<h1 style='color: #ffffff; font-weight: 800;'>{titulo}</h1>", unsafe_allow_html=True)
    
    conn = init_db()
    c = conn.cursor()
    
    tab_list, tab_create, tab_edit = st.tabs(["📋 Listar", "➕ Cadastrar", "✏️ Editar/Excluir"])
    
    # LISTAR
    with tab_list:
        df = pd.read_sql_query(f"SELECT {', '.join(colunas)} FROM {tabela} ORDER BY id DESC", conn)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # CRIAR
    with tab_create:
        with st.form(f"form_criar_{tabela}"):
            valores = {}
            for field in form_fields:
                nome = field['nome']
                tipo = field.get('tipo', 'text')
                if tipo == 'text':
                    valores[nome] = st.text_input(field['label'])
                elif tipo == 'number':
                    valores[nome] = st.number_input(field['label'], value=0.0)
                elif tipo == 'date':
                    valores[nome] = st.date_input(field['label'], datetime.today()).strftime('%Y-%m-%d')
                elif tipo == 'select':
                    valores[nome] = st.selectbox(field['label'], field['opcoes'])
                elif tipo == 'textarea':
                    valores[nome] = st.text_area(field['label'])
            
            submitted = st.form_submit_button("Salvar", use_container_width=True)
            if submitted:
                campos = list(valores.keys())
                placeholders = ', '.join(['?' for _ in campos])
                c.execute(f"INSERT INTO {tabela} ({', '.join(campos)}) VALUES ({placeholders})", list(valores.values()))
                conn.commit()
                st.success("✅ Cadastro realizado com sucesso!")
                st.rerun()
    
    # EDITAR / EXCLUIR
    with tab_edit:
        df = pd.read_sql_query(f"SELECT id, {', '.join(colunas)} FROM {tabela} ORDER BY id DESC", conn)
        if df.empty:
            st.info("Nenhum registro encontrado.")
        else:
            id_sel = st.selectbox("Selecione o registro", df['id'].tolist(), format_func=lambda x: f"ID {x}")
            registro = df[df['id'] == id_sel].iloc[0]
            
            with st.form(f"form_editar_{tabela}"):
                valores = {}
                for field in form_fields:
                    nome = field['nome']
                    tipo = field.get('tipo', 'text')
                    val_atual = registro.get(nome, '')
                    if tipo == 'text':
                        valores[nome] = st.text_input(field['label'], value=str(val_atual) if val_atual else '')
                    elif tipo == 'number':
                        valores[nome] = st.number_input(field['label'], value=float(val_atual) if val_atual else 0.0)
                    elif tipo == 'date':
                        try:
                            default = datetime.strptime(val_atual, '%Y-%m-%d')
                        except:
                            default = datetime.today()
                        valores[nome] = st.date_input(field['label'], default).strftime('%Y-%m-%d')
                    elif tipo == 'select':
                        valores[nome] = st.selectbox(field['label'], field['opcoes'], index=field['opcoes'].index(val_atual) if val_atual in field['opcoes'] else 0)
                    elif tipo == 'textarea':
                        valores[nome] = st.text_area(field['label'], value=str(val_atual) if val_atual else '')
                
                col1, col2 = st.columns(2)
                with col1:
                    atualizar = st.form_submit_button("Atualizar", use_container_width=True)
                with col2:
                    excluir = st.form_submit_button("Excluir", use_container_width=True)
                
                if atualizar:
                    sets = ', '.join([f"{k}=?" for k in valores.keys()])
                    vals = list(valores.values()) + [id_sel]
                    c.execute(f"UPDATE {tabela} SET {sets} WHERE id=?", vals)
                    conn.commit()
                    st.success("✅ Registro atualizado!")
                    st.rerun()
                
                if excluir:
                    c.execute(f"DELETE FROM {tabela} WHERE id=?", (id_sel,))
                    conn.commit()
                    st.warning("🗑️ Registro excluído!")
                    st.rerun()

# ============== PÁGINAS DE MÓDULOS ==============
def contratos_page():
    form_fields = [
        {'nome': 'numero', 'label': 'Número do Contrato', 'tipo': 'text'},
        {'nome': 'objeto', 'label': 'Objeto', 'tipo': 'text'},
        {'nome': 'contratada', 'label': 'Contratada', 'tipo': 'text'},
        {'nome': 'cnpj', 'label': 'CNPJ', 'tipo': 'text'},
        {'nome': 'valor', 'label': 'Valor (R$)', 'tipo': 'number'},
        {'nome': 'data_inicio', 'label': 'Data Início', 'tipo': 'date'},
        {'nome': 'data_fim', 'label': 'Data Fim', 'tipo': 'date'},
        {'nome': 'status', 'label': 'Status', 'tipo': 'select', 'opcoes': ['Ativo', 'Inativo', 'Encerrado', 'Suspenso']},
        {'nome': 'gestor', 'label': 'Gestor', 'tipo': 'text'},
        {'nome': 'observacoes', 'label': 'Observações', 'tipo': 'textarea'},
    ]
    crud_page('contratos', ['numero', 'objeto', 'contratada', 'valor', 'data_inicio', 'data_fim', 'status'], 'Gestão de Contratos', form_fields)

def financeiro_page():
    conn = init_db()
    contratos = pd.read_sql_query("SELECT id, numero FROM contratos", conn)
    opcoes_contratos = contratos['numero'].tolist() if not contratos.empty else ['Nenhum']
    
    form_fields = [
        {'nome': 'descricao', 'label': 'Descrição', 'tipo': 'text'},
        {'nome': 'tipo', 'label': 'Tipo', 'tipo': 'select', 'opcoes': ['Receita', 'Despesa']},
        {'nome': 'categoria', 'label': 'Categoria', 'tipo': 'select', 'opcoes': ['Pessoa', 'Material', 'Serviço', 'Medicamento', 'Outros']},
        {'nome': 'valor', 'label': 'Valor (R$)', 'tipo': 'number'},
        {'nome': 'data_vencimento', 'label': 'Data Vencimento', 'tipo': 'date'},
        {'nome': 'data_pagamento', 'label': 'Data Pagamento', 'tipo': 'date'},
        {'nome': 'status', 'label': 'Status', 'tipo': 'select', 'opcoes': ['Pendente', 'Pago', 'Atrasado', 'Cancelado']},
        {'nome': 'contrato_id', 'label': 'Contrato (ID)', 'tipo': 'text'},
        {'nome': 'observacoes', 'label': 'Observações', 'tipo': 'textarea'},
    ]
    crud_page('financeiro', ['descricao', 'tipo', 'categoria', 'valor', 'data_vencimento', 'status'], 'Gestão Financeira', form_fields)

def fornecedores_page():
    form_fields = [
        {'nome': 'razao_social', 'label': 'Razão Social', 'tipo': 'text'},
        {'nome': 'nome_fantasia', 'label': 'Nome Fantasia', 'tipo': 'text'},
        {'nome': 'cnpj', 'label': 'CNPJ', 'tipo': 'text'},
        {'nome': 'email', 'label': 'E-mail', 'tipo': 'text'},
        {'nome': 'telefone', 'label': 'Telefone', 'tipo': 'text'},
        {'nome': 'endereco', 'label': 'Endereço', 'tipo': 'text'},
        {'nome': 'categoria', 'label': 'Categoria', 'tipo': 'select', 'opcoes': ['Medicamentos', 'Material Médico', 'Serviços', 'Tecnologia', 'Outros']},
        {'nome': 'status', 'label': 'Status', 'tipo': 'select', 'opcoes': ['Ativo', 'Inativo', 'Bloqueado']},
    ]
    crud_page('fornecedores', ['razao_social', 'nome_fantasia', 'cnpj', 'categoria', 'status'], 'Cadastro de Fornecedores', form_fields)

def medicamentos_page():
    form_fields = [
        {'nome': 'nome', 'label': 'Nome do Medicamento', 'tipo': 'text'},
        {'nome': 'principio_ativo', 'label': 'Princípio Ativo', 'tipo': 'text'},
        {'nome': 'fabricante', 'label': 'Fabricante', 'tipo': 'text'},
        {'nome': 'codigo', 'label': 'Código', 'tipo': 'text'},
        {'nome': 'quantidade', 'label': 'Quantidade', 'tipo': 'number'},
        {'nome': 'valor_unitario', 'label': 'Valor Unitário (R$)', 'tipo': 'number'},
        {'nome': 'validade', 'label': 'Validade', 'tipo': 'date'},
        {'nome': 'status', 'label': 'Status', 'tipo': 'select', 'opcoes': ['Ativo', 'Inativo', 'Vencido', 'Em Falta']},
    ]
    crud_page('medicamentos', ['nome', 'principio_ativo', 'fabricante', 'quantidade', 'validade', 'status'], 'Controle de Medicamentos', form_fields)

def usuarios_page():
    if st.session_state.perfil != 'admin':
        st.error("Acesso negado.")
        return
    
    form_fields = [
        {'nome': 'usuario', 'label': 'Usuário', 'tipo': 'text'},
        {'nome': 'senha_hash', 'label': 'Senha (será criptografada)', 'tipo': 'text'},
        {'nome': 'nome', 'label': 'Nome Completo', 'tipo': 'text'},
        {'nome': 'email', 'label': 'E-mail', 'tipo': 'text'},
        {'nome': 'perfil', 'label': 'Perfil', 'tipo': 'select', 'opcoes': ['admin', 'gestor', 'usuario']},
        {'nome': 'ativo', 'label': 'Ativo', 'tipo': 'select', 'opcoes': ['1', '0']},
    ]
    
    st.markdown("<h1 style='color: #ffffff; font-weight: 800;'>Gestão de Usuários</h1>", unsafe_allow_html=True)
    conn = init_db()
    c = conn.cursor()
    
    tab_list, tab_create, tab_edit = st.tabs(["📋 Listar", "➕ Cadastrar", "✏️ Editar/Excluir"])
    
    with tab_list:
        df = pd.read_sql_query("SELECT id, usuario, nome, email, perfil, ativo, data_criacao FROM usuarios ORDER BY id DESC", conn)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    with tab_create:
        with st.form("form_criar_usuario"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            nome = st.text_input("Nome Completo")
            email = st.text_input("E-mail")
            perfil = st.selectbox("Perfil", ['admin', 'gestor', 'usuario'])
            ativo = st.selectbox("Ativo", ['1', '0'])
            
            submitted = st.form_submit_button("Salvar", use_container_width=True)
            if submitted:
                senha_hash = hashlib.sha256(senha.encode()).hexdigest()
                c.execute("INSERT INTO usuarios (usuario, senha_hash, nome, email, perfil, ativo) VALUES (?, ?, ?, ?, ?, ?)",
                         (usuario, senha_hash, nome, email, perfil, int(ativo)))
                conn.commit()
                st.success("✅ Usuário cadastrado com sucesso!")
                st.rerun()
    
    with tab_edit:
        df = pd.read_sql_query("SELECT id, usuario, nome, email, perfil, ativo FROM usuarios ORDER BY id DESC", conn)
        if df.empty:
            st.info("Nenhum usuário encontrado.")
        else:
            id_sel = st.selectbox("Selecione o usuário", df['id'].tolist(), format_func=lambda x: f"ID {x}")
            registro = df[df['id'] == id_sel].iloc[0]
            
            with st.form("form_editar_usuario"):
                usuario = st.text_input("Usuário", value=registro['usuario'])
                senha = st.text_input("Nova Senha (deixe em branco para manter)", type="password")
                nome = st.text_input("Nome Completo", value=registro['nome'])
                email = st.text_input("E-mail", value=registro['email'])
                perfil = st.selectbox("Perfil", ['admin', 'gestor', 'usuario'], index=['admin', 'gestor', 'usuario'].index(registro['perfil']))
                ativo = st.selectbox("Ativo", ['1', '0'], index=['1', '0'].index(str(registro['ativo'])))
                
                col1, col2 = st.columns(2)
                with col1:
                    atualizar = st.form_submit_button("Atualizar", use_container_width=True)
                with col2:
                    excluir = st.form_submit_button("Excluir", use_container_width=True)
                
                if atualizar:
                    if senha:
                        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
                        c.execute("UPDATE usuarios SET usuario=?, senha_hash=?, nome=?, email=?, perfil=?, ativo=? WHERE id=?",
                                 (usuario, senha_hash, nome, email, perfil, int(ativo), id_sel))
                    else:
                        c.execute("UPDATE usuarios SET usuario=?, nome=?, email=?, perfil=?, ativo=? WHERE id=?",
                                 (usuario, nome, email, perfil, int(ativo), id_sel))
                    conn.commit()
                    st.success("✅ Usuário atualizado!")
                    st.rerun()
                
                if excluir:
                    c.execute("DELETE FROM usuarios WHERE id=?", (id_sel,))
                    conn.commit()
                    st.warning("🗑️ Usuário excluído!")
                    st.rerun()

def relatorios_page():
    st.markdown("<h1 style='color: #ffffff; font-weight: 800;'>Relatórios</h1>", unsafe_allow_html=True)
    
    conn = init_db()
    c = conn.cursor()
    
    tipo_relatorio = st.selectbox("Tipo de Relatório", [
        "Contratos por Status",
        "Movimentação Financeira",
        "Fornecedores Ativos",
        "Medicamentos em Estoque",
        "Resumo Geral"
    ])
    
    if st.button("Gerar Relatório", use_container_width=True):
        if tipo_relatorio == "Contratos por Status":
            df = pd.read_sql_query("SELECT status, COUNT(*) as quantidade, SUM(valor) as valor_total FROM contratos GROUP BY status", conn)
            st.dataframe(df, use_container_width=True, hide_index=True)
        elif tipo_relatorio == "Movimentação Financeira":
            df = pd.read_sql_query("SELECT tipo, SUM(valor) as total FROM financeiro GROUP BY tipo", conn)
            st.dataframe(df, use_container_width=True, hide_index=True)
        elif tipo_relatorio == "Fornecedores Ativos":
            df = pd.read_sql_query("SELECT * FROM fornecedores WHERE status='Ativo'", conn)
            st.dataframe(df, use_container_width=True, hide_index=True)
        elif tipo_relatorio == "Medicamentos em Estoque":
            df = pd.read_sql_query("SELECT nome, quantidade, valor_unitario, validade FROM medicamentos ORDER BY quantidade ASC", conn)
            st.dataframe(df, use_container_width=True, hide_index=True)
        elif tipo_relatorio == "Resumo Geral":
            c.execute("SELECT COUNT(*) FROM contratos")
            contratos = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM financeiro")
            financeiro = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM fornecedores")
            fornecedores = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM medicamentos")
            medicamentos = c.fetchone()[0]
            
            resumo = pd.DataFrame({
                'Módulo': ['Contratos', 'Financeiro', 'Fornecedores', 'Medicamentos'],
                'Quantidade': [contratos, financeiro, fornecedores, medicamentos]
            })
            st.dataframe(resumo, use_container_width=True, hide_index=True)
        
        c.execute("INSERT INTO relatorios (titulo, tipo, gerado_por) VALUES (?, ?, ?)",
                 (tipo_relatorio, tipo_relatorio, st.session_state.usuario))
        conn.commit()
        st.success("✅ Relatório gerado e salvo!")

def trocar_senha_page():
    st.markdown("<h1 style='color: #ffffff; font-weight: 800;'>Trocar Senha</h1>", unsafe_allow_html=True)
    
    conn = init_db()
    c = conn.cursor()
    
    with st.form("form_trocar_senha"):
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
        
        submitted = st.form_submit_button("Alterar Senha", use_container_width=True)
        if submitted:
            if not senha_atual or not nova_senha or not confirmar_senha:
                st.error("⚠️ Preencha todos os campos.")
            elif nova_senha != confirmar_senha:
                st.error("⚠️ As senhas não conferem.")
            else:
                c.execute("SELECT senha_hash FROM usuarios WHERE usuario=?", (st.session_state.usuario,))
                resultado = c.fetchone()
                if resultado and verify_password(senha_atual, resultado[0]):
                    nova_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
                    c.execute("UPDATE usuarios SET senha_hash=? WHERE usuario=?", (nova_hash, st.session_state.usuario))
                    conn.commit()
                    st.success("✅ Senha alterada com sucesso!")
                else:
                    st.error("❌ Senha atual incorreta.")

# ============== ROTEAMENTO ==============
if not st.session_state.autenticado:
    login_page()
else:
    sidebar()
    pagina = st.session_state.pagina
    
    if pagina == 'Dashboard':
        dashboard()
    elif pagina == 'Contratos':
        contratos_page()
    elif pagina == 'Financeiro':
        financeiro_page()
    elif pagina == 'Fornecedores':
        fornecedores_page()
    elif pagina == 'Medicamentos':
        medicamentos_page()
    elif pagina == 'Usuários':
        usuarios_page()
    elif pagina == 'Relatórios':
        relatorios_page()
    elif pagina == 'Trocar Senha':
        trocar_senha_page()
