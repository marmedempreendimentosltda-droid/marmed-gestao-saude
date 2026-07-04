import streamlit as st
import sqlite3
import hashlib
import time
import random
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(
    page_title="MARMED - Gestão em Saúde Pública",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Database setup ---
DATABASE = "marmed.db"

TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        nome TEXT,
        perfil TEXT DEFAULT 'usuario',
        ativo INTEGER DEFAULT 1
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS contas_pagar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fornecedor TEXT NOT NULL,
        descricao TEXT,
        valor REAL NOT NULL,
        vencimento DATE NOT NULL,
        status TEXT DEFAULT 'Pendente',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS contas_receber (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        devedor TEXT NOT NULL,
        descricao TEXT,
        valor REAL NOT NULL,
        vencimento DATE NOT NULL,
        status TEXT DEFAULT 'Pendente',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS empenhos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT NOT NULL,
        fornecedor TEXT NOT NULL,
        descricao TEXT,
        valor REAL NOT NULL,
        data_empenho DATE NOT NULL,
        status TEXT DEFAULT 'Empenhado',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS licitacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT NOT NULL,
        objeto TEXT NOT NULL,
        modalidade TEXT,
        valor REAL NOT NULL,
        data_abertura DATE NOT NULL,
        status TEXT DEFAULT 'Aberta',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS contratos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT NOT NULL,
        contratado TEXT NOT NULL,
        objeto TEXT,
        valor REAL NOT NULL,
        inicio DATE NOT NULL,
        fim DATE NOT NULL,
        status TEXT DEFAULT 'Vigente',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        descricao TEXT,
        valor REAL NOT NULL,
        data_mov DATE NOT NULL,
        categoria TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
]


def get_conn():
    return sqlite3.connect(DATABASE, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    for sql in TABLES_SQL:
        cur.executescript(sql)
    # Insert default admin
    default_user = "admin"
    default_pass = "Diretor2025#"
    pass_hash = hashlib.sha256(default_pass.encode()).hexdigest()
    cur.execute(
        "INSERT OR IGNORE INTO usuarios (username, password_hash, nome, perfil) VALUES (?, ?, ?, ?)",
        (default_user, pass_hash, "Administrador", "admin")
    )
    conn.commit()
    conn.close()


init_db()

# --- Session state ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"


# --- Helpers ---
def check_password(username, password):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, password_hash, nome, perfil FROM usuarios WHERE username = ? AND ativo = 1",
        (username,)
    )
    row = cur.fetchone()
    conn.close()
    if row:
        pass_hash = hashlib.sha256(password.encode()).hexdigest()
        if row[2] == pass_hash:
            return row
    return None


def login():
    username = st.session_state.get("username_input", "")
    password = st.session_state.get("password_input", "")
    user = check_password(username, password)
    if user:
        st.session_state.authenticated = True
        st.session_state.user = {
            "id": user[0],
            "username": user[1],
            "nome": user[3],
            "perfil": user[4]
        }
        st.session_state.page = "Dashboard"
        st.success("Login realizado com sucesso!")
        time.sleep(0.5)
        st.rerun()
    else:
        st.error("Usuário ou senha inválidos.")


def logout():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.page = "Dashboard"
    st.rerun()


def change_password():
    new_password = st.session_state.get("new_password", "")
    confirm_password = st.session_state.get("confirm_password", "")
    if not new_password or not confirm_password:
        st.error("Preencha todos os campos.")
        return
    if new_password != confirm_password:
        st.error("As senhas não coincidem.")
        return
    pass_hash = hashlib.sha256(new_password.encode()).hexdigest()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE usuarios SET password_hash = ? WHERE id = ?",
        (pass_hash, st.session_state.user["id"])
    )
    conn.commit()
    conn.close()
    st.success("Senha alterada com sucesso!")


# --- UI: CSS ---
LOGIN_CSS = """
<style>
html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main {
    margin: 0;
    padding: 0;
    height: 100vh;
    overflow: hidden;
    background: linear-gradient(135deg, #0a0e27 0%, #0d2137 100%);
    font-family: 'Segoe UI', sans-serif;
}
#particles-canvas {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 0;
    pointer-events: none;
}
.login-container {
    position: absolute;
    z-index: 10;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    width: 420px;
    max-width: 95vw;
    padding: 42px 34px 34px 34px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 24px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(255, 255, 255, 0.18);
    text-align: center;
}
.animated-title {
    display: inline-block;
    font-size: 3.6rem;
    font-weight: 900;
    letter-spacing: 0.12em;
    color: #fff;
    margin-bottom: 0.2em;
    perspective: 1000px;
    text-shadow: 0 0 10px #00d4ff, 0 0 20px #00d4ff, 0 0 40px #00d4ff;
}
.animated-title span {
    display: inline-block;
    transform-style: preserve-3d;
    animation: assemble 3.2s cubic-bezier(0.22, 0.61, 0.36, 1) forwards,
               flash 0.7s 3.2s ease-in-out forwards,
               glow 2.5s 3.7s ease-in-out infinite alternate;
    opacity: 0;
}
.animated-title span:nth-child(1) { animation-delay: 0.0s, 3.2s, 3.7s; }
.animated-title span:nth-child(2) { animation-delay: 0.18s, 3.2s, 3.7s; }
.animated-title span:nth-child(3) { animation-delay: 0.36s, 3.2s, 3.7s; }
.animated-title span:nth-child(4) { animation-delay: 0.54s, 3.2s, 3.7s; }
.animated-title span:nth-child(5) { animation-delay: 0.72s, 3.2s, 3.7s; }
.animated-title span:nth-child(6) { animation-delay: 0.90s, 3.2s, 3.7s; }

.animated-title span:nth-child(1) { --tx: -120vw; --ty: -80vh; --tz: 600px; --rx: 120deg; --ry: -90deg; }
.animated-title span:nth-child(2) { --tx: 120vw; --ty: -90vh; --tz: -500px; --rx: -100deg; --ry: 80deg; }
.animated-title span:nth-child(3) { --tx: -90vw; --ty: 100vh; --tz: 700px; --rx: 90deg; --ry: -120deg; }
.animated-title span:nth-child(4) { --tx: 100vw; --ty: 80vh; --tz: -600px; --rx: -70deg; --ry: 100deg; }
.animated-title span:nth-child(5) { --tx: -60vw; --ty: -110vh; --tz: 800px; --rx: 130deg; --ry: 60deg; }
.animated-title span:nth-child(6) { --tx: 80vw; --ty: 110vh; --tz: -700px; --rx: -110deg; --ry: -70deg; }

@keyframes assemble {
    0% {
        opacity: 0;
        transform: translate3d(var(--tx), var(--ty), var(--tz)) rotateX(var(--rx)) rotateY(var(--ry)) scale(0.6);
        text-shadow: 0 0 0 transparent;
    }
    60% {
        opacity: 1;
    }
    100% {
        opacity: 1;
        transform: translate3d(0, 0, 0) rotateX(0deg) rotateY(0deg) scale(1);
        text-shadow: 0 0 10px #00d4ff, 0 0 20px #00d4ff;
    }
}
@keyframes flash {
    0% { text-shadow: 0 0 10px #00d4ff, 0 0 20px #00d4ff; color: #fff; }
    50% { color: #ffd700; text-shadow: 0 0 30px #fff, 0 0 60px #ffd700, 0 0 100px #ffd700; }
    100% { color: #fff; text-shadow: 0 0 10px #00d4ff, 0 0 20px #00d4ff; }
}
@keyframes glow {
    0% { text-shadow: 0 0 10px #00d4ff, 0 0 20px #00d4ff; }
    100% { text-shadow: 0 0 18px #00d4ff, 0 0 40px #00d4ff, 0 0 70px #00d4ff; }
}
.subtitle {
    font-size: 1.1rem;
    color: #00d4ff;
    letter-spacing: 0.08em;
    margin-top: 0.4em;
    text-shadow: 0 0 8px rgba(0, 212, 255, 0.3);
}
.location {
    font-size: 0.95rem;
    color: #aeeaff;
    margin-bottom: 1.8em;
}
.login-label {
    display: block;
    text-align: left;
    color: #fff;
    font-weight: 600;
    font-size: 0.92rem;
    margin-bottom: 0.3em;
    margin-top: 0.8em;
}
input[type="text"], input[type="password"] {
    width: 100%;
    padding: 12px 14px;
    border-radius: 10px;
    border: 2px solid #00d4ff;
    background: rgba(255, 255, 255, 0.15);
    color: #fff;
    font-size: 1rem;
    outline: none;
    transition: all 0.2s ease;
}
input[type="text"]:focus, input[type="password"]:focus {
    background: rgba(255, 255, 255, 0.22);
    border-color: #ffd700;
    box-shadow: 0 0 12px rgba(0, 212, 255, 0.5);
}
input[type="text"]::placeholder, input[type="password"]::placeholder {
    color: rgba(255, 255, 255, 0.7);
}
button[kind="formSubmit"] {
    width: 100%;
    margin-top: 1.2em;
    padding: 12px 0;
    border-radius: 10px;
    border: none;
    background: linear-gradient(90deg, #00d4ff, #008cff);
    color: #fff;
    font-weight: 700;
    font-size: 1.05rem;
    cursor: pointer;
    box-shadow: 0 0 14px rgba(0, 212, 255, 0.4);
    transition: transform 0.2s;
}
button[kind="formSubmit"]:hover {
    transform: scale(1.02);
}
.stForm > div[data-testid="stForm"] {
    border: none;
    background: transparent;
    padding: 0;
}
</style>
<<canvas id="particles-canvas"></canvas>
<script>
(function(){
    const canvas = document.getElementById('particles-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W = canvas.width = window.innerWidth;
    let H = canvas.height = window.innerHeight;
    const particles = [];
    for (let i = 0; i < 70; i++) {
        particles.push({
            x: Math.random() * W,
            y: Math.random() * H,
            r: Math.random() * 2 + 1,
            dx: (Math.random() - 0.5) * 0.6,
            dy: (Math.random() - 0.5) * 0.6,
            alpha: Math.random() * 0.5 + 0.2
        });
    }
    function animate() {
        ctx.clearRect(0, 0, W, H);
        for (let p of particles) {
            p.x += p.dx;
            p.y += p.dy;
            if (p.x < 0 || p.x > W) p.dx *= -1;
            if (p.y < 0 || p.y > H) p.dy *= -1;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(0, 212, 255, ' + p.alpha + ')';
            ctx.fill();
        }
        requestAnimationFrame(animate);
    }
    animate();
    window.addEventListener('resize', () => {
        W = canvas.width = window.innerWidth;
        H = canvas.height = window.innerHeight;
    });
})();
</script>
"""

APP_CSS = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0a0e27 0%, #0d2137 100%);
}
.glass-card {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    padding: 20px;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 0 8px 32px rgba(0,0,0,0.25);
    color: #fff;
}
.metric-card {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 18px 14px;
    backdrop-filter: blur(12px);
    border: 1px solid rgba(0, 212, 255, 0.25);
    box-shadow: 0 6px 24px rgba(0,0,0,0.2);
    text-align: center;
}
.metric-label {
    font-size: 0.9rem;
    color: #aeeaff;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #00d4ff;
}
.sidebar-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #00d4ff;
    text-align: center;
    margin-bottom: 0.8em;
}
.stButton > button {
    border-radius: 10px;
    background: rgba(0, 212, 255, 0.12);
    border: 1px solid rgba(0, 212, 255, 0.3);
    color: #fff;
}
.stButton > button:hover {
    background: rgba(0, 212, 255, 0.22);
}
.stTextInput > div > div > input, .stNumberInput input, .stDateInput input, .stTextArea textarea, .stSelectbox > div > div {
    background: rgba(255, 255, 255, 0.10) !important;
    color: #fff !important;
    border: 1.5px solid #00d4ff !important;
    border-radius: 10px !important;
}
.stTextInput label, .stNumberInput label, .stDateInput label, .stTextArea label, .stSelectbox label {
    color: #fff !important;
    font-weight: 600 !important;
}
h1, h2, h3, h4, p, label, .stMarkdown {
    color: #fff;
}
[data-testid="stSidebar"] {
    background: rgba(10, 14, 39, 0.92);
}
</style>
"""


# --- Login Page ---
def show_login():
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="login-container">
        <div class="animated-title">
            <span>M</span><span>A</span><span>R</span><span>M</span><span>E</span><span>D</span>
        </div>
        <div class="subtitle">Gestão em Saúde Pública</div>
        <div class="location">Luminárias - MG</div>
    </div>
    """, unsafe_allow_html=True)
    with st.form("login_form"):
        st.markdown("<<label class='login-label'>Usuário</label>", unsafe_allow_html=True)
        st.text_input("", key="username_input", placeholder="Digite seu usuário", label_visibility="collapsed")
        st.markdown("<<label class='login-label'>Senha</label>", unsafe_allow_html=True)
        st.text_input("", key="password_input", type="password", placeholder="Digite sua senha", label_visibility="collapsed")
        submitted = st.form_submit_button("Entrar")
        if submitted:
            login()


# --- App Pages ---
APP_PAGES = ["Dashboard", "Contas a Pagar", "Contas a Receber", "Empenhos", "Licitações", "Contratos", "Relatórios", "Trocar Senha"]


def sidebar():
    st.markdown("<<div class='sidebar-title'>MARMED</div>", unsafe_allow_html=True)
    st.markdown("<<p style='text-align:center;color:#aeeaff;'>Gestão em Saúde Pública</p>", unsafe_allow_html=True)
    st.markdown("<<p style='text-align:center;color:#fff;'>Luminárias - MG</p>", unsafe_allow_html=True)
    st.divider()
    for p in APP_PAGES:
        if st.button(p, key=f"nav_{p}"):
            st.session_state.page = p
            st.rerun()
    st.divider()
    st.markdown(f"<<p style='text-align:center;color:#fff;'>Logado como: <b>{st.session_state.user['nome']}</b></p>", unsafe_allow_html=True)
    if st.button("Sair", key="logout_btn"):
        logout()


def format_currency(val):
    try:
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return f"R$ {val}"


def dashboard():
    st.header("Dashboard")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(valor),0) FROM movimentacoes WHERE categoria = 'REPASSE FEDERAL'")
    repasse_federal = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(valor),0) FROM movimentacoes WHERE categoria = 'REPASSE ESTADUAL'")
    repasse_estadual = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(valor),0) FROM movimentacoes WHERE categoria = 'RECURSO MUNICIPAL'")
    recurso_municipal = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(valor),0) FROM movimentacoes WHERE categoria = 'TRANSFERÊNCIA'")
    transferencia = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(valor),0) FROM movimentacoes WHERE categoria = 'TRANSPOSIÇÃO'")
    transposicao = cur.fetchone()[0]
    conn.close()

    metricas = {
        "REPASSE FEDERAL": repasse_federal,
        "REPASSE ESTADUAL": repasse_estadual,
        "RECURSO MUNICIPAL": recurso_municipal,
        "TRANSFERÊNCIA": transferencia,
        "TRANSPOSIÇÃO": transposicao
    }
    cols = st.columns(5)
    for i, (label, value) in enumerate(metricas.items()):
        cols[i].markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{format_currency(value)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Resumo Contas a Pagar")
        conn = get_conn()
        df = pd.read_sql_query("SELECT status, COALESCE(SUM(valor),0) as total FROM contas_pagar GROUP BY status", conn)
        conn.close()
        st.bar_chart(df.set_index("status")["total"])
    with c2:
        st.subheader("Resumo Contas a Receber")
        conn = get_conn()
        df = pd.read_sql_query("SELECT status, COALESCE(SUM(valor),0) as total FROM contas_receber GROUP BY status", conn)
        conn.close()
        st.bar_chart(df.set_index("status")["total"])


def crud_page(title, table, columns, form_fields, default_values):
    st.header(title)
    conn = get_conn()
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()

    tab_list, tab_add = st.tabs(["Listar", "Adicionar/Editar"])

    with tab_list:
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhum registro encontrado.")

    with tab_add:
        with st.form(f"form_{table}"):
            values = {}
            for field in form_fields:
                label = field["label"]
                key = field["key"]
                ftype = field["type"]
                if ftype == "text":
                    values[key] = st.text_input(label, value=default_values.get(key, ""))
                elif ftype == "number":
                    values[key] = st.number_input(label, value=float(default_values.get(key, 0) or 0), step=0.01)
                elif ftype == "date":
                    default = default_values.get(key, datetime.today().date())
                    if isinstance(default, str):
                        try:
                            default = datetime.strptime(default, "%Y-%m-%d").date()
                        except Exception:
                            default = datetime.today().date()
                    values[key] = st.date_input(label, value=default)
                elif ftype == "select":
                    options = field.get("options", [])
                    values[key] = st.selectbox(label, options, index=0)
                elif ftype == "textarea":
                    values[key] = st.text_area(label, value=default_values.get(key, ""))
            cols = st.columns([1, 1, 1])
            with cols[0]:
                submit = st.form_submit_button("Salvar")
            with cols[1]:
                delete = st.form_submit_button("Excluir")
            with cols[2]:
                clear = st.form_submit_button("Limpar")
            if submit:
                conn = get_conn()
                cur = conn.cursor()
                placeholders = ", ".join(["?"] * len(columns))
                cur.execute(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})", [values[c] for c in columns])
                conn.commit()
                conn.close()
                st.success("Registro salvo com sucesso!")
                st.rerun()
            if delete:
                id_to_delete = values.get("id")
                if id_to_delete:
                    conn = get_conn()
                    cur = conn.cursor()
                    cur.execute(f"DELETE FROM {table} WHERE id = ?", (id_to_delete,))
                    conn.commit()
                    conn.close()
                    st.success("Registro excluído com sucesso!")
                    st.rerun()
                else:
                    st.error("Informe o ID para exclusão.")
            if clear:
                st.rerun()


def contas_pagar_page():
    form_fields = [
        {"label": "ID", "key": "id", "type": "number"},
        {"label": "Fornecedor", "key": "fornecedor", "type": "text"},
        {"label": "Descrição", "key": "descricao", "type": "textarea"},
        {"label": "Valor", "key": "valor", "type": "number"},
        {"label": "Vencimento", "key": "vencimento", "type": "date"},
        {"label": "Status", "key": "status", "type": "select", "options": ["Pendente", "Pago", "Cancelado"]}
    ]
    crud_page("Contas a Pagar", "contas_pagar", ["fornecedor", "descricao", "valor", "vencimento", "status"], form_fields, {})


def contas_receber_page():
    form_fields = [
        {"label": "ID", "key": "id", "type": "number"},
        {"label": "Devedor", "key": "devedor", "type": "text"},
        {"label": "Descrição", "key": "descricao", "type": "textarea"},
        {"label": "Valor", "key": "valor", "type": "number"},
        {"label": "Vencimento", "key": "vencimento", "type": "date"},
        {"label": "Status", "key": "status", "type": "select", "options": ["Pendente", "Recebido", "Cancelado"]}
    ]
    crud_page("Contas a Receber", "contas_receber", ["devedor", "descricao", "valor", "vencimento", "status"], form_fields, {})


def empenhos_page():
    form_fields = [
        {"label": "ID", "key": "id", "type": "number"},
        {"label": "Número", "key": "numero", "type": "text"},
        {"label": "Fornecedor", "key": "fornecedor", "type": "text"},
        {"label": "Descrição", "key": "descricao", "type": "textarea"},
        {"label": "Valor", "key": "valor", "type": "number"},
        {"label": "Data do Empenho", "key": "data_empenho", "type": "date"},
        {"label": "Status", "key": "status", "type": "select", "options": ["Empenhado", "Pago", "Cancelado"]}
    ]
    crud_page("Empenhos", "empenhos", ["numero", "fornecedor", "descricao", "valor", "data_empenho", "status"], form_fields, {})


def licitacoes_page():
    form_fields = [
        {"label": "ID", "key": "id", "type": "number"},
        {"label": "Número", "key": "numero", "type": "text"},
        {"label": "Objeto", "key": "objeto", "type": "text"},
        {"label": "Modalidade", "key": "modalidade", "type": "text"},
        {"label": "Valor", "key": "valor", "type": "number"},
        {"label": "Data de Abertura", "key": "data_abertura", "type": "date"},
        {"label": "Status", "key": "status", "type": "select", "options": ["Aberta", "Fechada", "Cancelada", "Homologada"]}
    ]
    crud_page("Licitações", "licitacoes", ["numero", "objeto", "modalidade", "valor", "data_abertura", "status"], form_fields, {})


def contratos_page():
    form_fields = [
        {"label": "ID", "key": "id", "type": "number"},
        {"label": "Número", "key": "numero", "type": "text"},
        {"label": "Contratado", "key": "contratado", "type": "text"},
        {"label": "Objeto", "key": "objeto", "type": "textarea"},
        {"label": "Valor", "key": "valor", "type": "number"},
        {"label": "Início", "key": "inicio", "type": "date"},
        {"label": "Fim", "key": "fim", "type": "date"},
        {"label": "Status", "key": "status", "type": "select", "options": ["Vigente", "Encerrado", "Cancelado"]}
    ]
    crud_page("Contratos", "contratos", ["numero", "contratado", "objeto", "valor", "inicio", "fim", "status"], form_fields, {})


def relatorios_page():
    st.header("Relatórios")
    st.markdown("Selecione os relatórios para visualização/exportação.")

    relatorios = {
        "Contas a Pagar": "contas_pagar",
        "Contas a Receber": "contas_receber",
        "Empenhos": "empenhos",
        "Licitações": "licitacoes",
        "Contratos": "contratos",
        "Movimentações": "movimentacoes"
    }
    for nome, tabela in relatorios.items():
        with st.expander(nome):
            conn = get_conn()
            df = pd.read_sql_query(f"SELECT * FROM {tabela}", conn)
            conn.close()
            st.dataframe(df, use_container_width=True)
            if not df.empty:
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=f"Exportar {nome} (CSV)",
                    data=csv,
                    file_name=f"{tabela}.csv",
                    mime="text/csv",
                    key=f"dl_{tabela}"
                )


def trocar_senha_page():
    st.header("Trocar Senha")
    with st.form("change_password_form"):
        st.text_input("Nova Senha", type="password", key="new_password")
        st.text_input("Confirmar Nova Senha", type="password", key="confirm_password")
        submitted = st.form_submit_button("Alterar Senha")
        if submitted:
            change_password()


# --- Main ---
if not st.session_state.authenticated:
    show_login()
else:
    st.markdown(APP_CSS, unsafe_allow_html=True)
    with st.sidebar:
        sidebar()

    page = st.session_state.page
    if page == "Dashboard":
        dashboard()
    elif page == "Contas a Pagar":
        contas_pagar_page()
    elif page == "Contas a Receber":
        contas_receber_page()
    elif page == "Empenhos":
        empenhos_page()
    elif page == "Licitações":
        licitacoes_page()
    elif page == "Contratos":
        contratos_page()
    elif page == "Relatórios":
        relatorios_page()
    elif page == "Trocar Senha":
        trocar_senha_page()
    else:
        dashboard()
