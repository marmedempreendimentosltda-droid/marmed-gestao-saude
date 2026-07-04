import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import datetime
import random
import time
import os

# ================= CONFIG =================
st.set_page_config(
    page_title="MARMED - Gestão em Saúde Pública de Luminárias-MG",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ================= CSS GLOBAL =================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600;700&display=swap');

:root {
    --primary: #00d4ff;
    --secondary: #ff006e;
    --accent: #8338ec;
    --success: #06d6a0;
    --warning: #ffd166;
    --danger: #ef476f;
    --bg: #0a0f1c;
    --card: rgba(255, 255, 255, 0.07);
    --card-border: rgba(255, 255, 255, 0.12);
    --text: #ffffff;
    --muted: rgba(255, 255, 255, 0.7);
}

html, body, [class*="stApp"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Inter', sans-serif;
}

/* Particles background */
#particles-canvas {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: -1;
    pointer-events: none;
}

/* Glassmorphism */
.glass-card {
    background: var(--card) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 20px !important;
    padding: 1.5rem !important;
    box-shadow: 0 8px 32px rgba(0, 212, 255, 0.1) !important;
    transition: all 0.3s ease !important;
}
.glass-card:hover {
    transform: translateY(-4px) !important;
    box-shadow: 0 12px 40px rgba(0, 212, 255, 0.18) !important;
    border-color: rgba(0, 212, 255, 0.4) !important;
}

/* 3D Animated Title */
.title-3d {
    font-family: 'Orbitron', sans-serif;
    font-weight: 900;
    font-size: clamp(3rem, 10vw, 7rem);
    text-align: center;
    color: var(--primary);
    text-shadow:
        0 0 10px rgba(0, 212, 255, 0.8),
        0 0 40px rgba(0, 212, 255, 0.5),
        0 0 80px rgba(0, 212, 255, 0.3);
    perspective: 1000px;
    letter-spacing: 0.2em;
    margin: 0;
    line-height: 1.1;
}
.letter {
    display: inline-block;
    animation: flyIn 1.2s cubic-bezier(0.23, 1, 0.32, 1) forwards;
    opacity: 0;
    transform: translateZ(-800px) rotateY(90deg) scale(0.3);
}
@keyframes flyIn {
    0% { opacity: 0; transform: translateZ(-800px) rotateY(90deg) scale(0.3); }
    60% { opacity: 1; transform: translateZ(50px) rotateY(-10deg) scale(1.1); }
    100% { opacity: 1; transform: translateZ(0) rotateY(0deg) scale(1); }
}

/* Subtitle glow */
.subtitle {
    text-align: center;
    font-family: 'Inter', sans-serif;
    font-weight: 300;
    font-size: 1.2rem;
    color: var(--muted);
    margin-top: 1rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: rgba(10, 15, 28, 0.95) !important;
    border-right: 1px solid var(--card-border) !important;
}
[data-testid="stSidebar"] .css-1d391kg, [data-testid="stSidebar"] .css-qri22k {
    color: white !important;
}

/* Buttons */
.stButton>button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    border: 1px solid rgba(0, 212, 255, 0.4) !important;
    background: rgba(0, 212, 255, 0.12) !important;
    color: white !important;
}
.stButton>button:hover {
    background: rgba(0, 212, 255, 0.25) !important;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.4) !important;
    transform: translateY(-2px) !important;
}

/* Inputs */
.stTextInput>div>div>input, .stNumberInput>div>div>input, .stDateInput>div>div>input, .stSelectbox>div>div>div, .stTextArea>div>div>textarea {
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 12px !important;
    color: white !important;
}
.stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus, .stDateInput>div>div>input:focus, .stSelectbox>div>div>div:focus, .stTextArea>div>div>textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 15px rgba(0, 212, 255, 0.3) !important;
}

/* DataFrames */
.stDataFrame {
    background: rgba(255, 255, 255, 0.04) !important;
    border-radius: 16px !important;
    border: 1px solid var(--card-border) !important;
}
.stDataFrame th {
    background: rgba(0, 212, 255, 0.12) !important;
    color: white !important;
    font-weight: 700 !important;
}
.stDataFrame td {
    color: rgba(255, 255, 255, 0.85) !important;
}

/* Metric cards */
.metric-card {
    background: rgba(255, 255, 255, 0.06) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 20px !important;
    padding: 1.5rem !important;
    text-align: center !important;
    transition: all 0.3s ease !important;
}
.metric-card:hover {
    transform: translateY(-6px) !important;
    box-shadow: 0 12px 35px rgba(0, 212, 255, 0.15) !important;
}
.metric-value {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: var(--primary);
    text-shadow: 0 0 20px rgba(0, 212, 255, 0.4);
}
.metric-label {
    font-size: 0.85rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.5rem;
}

/* Hide hamburger */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 12px !important;
}
.stTabs [data-baseweb="tab"] {
    background: rgba(255, 255, 255, 0.05) !important;
    border-radius: 12px !important;
    color: white !important;
    font-weight: 600 !important;
    border: 1px solid var(--card-border) !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(0, 212, 255, 0.2) !important;
    border-color: var(--primary) !important;
    color: white !important;
}
</style>
"""

PARTICLES_JS = """
<script>
(function() {
    const canvas = document.createElement('canvas');
    canvas.id = 'particles-canvas';
    document.body.prepend(canvas);
    const ctx = canvas.getContext('2d');
    let width, height, particles = [];
    function resize() { width = canvas.width = window.innerWidth; height = canvas.height = window.innerHeight; }
    window.addEventListener('resize', resize);
    resize();
    for (let i = 0; i < 70; i++) {
        particles.push({
            x: Math.random() * width,
            y: Math.random() * height,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            r: Math.random() * 2 + 1,
            a: Math.random() * 0.5 + 0.2
        });
    }
    function animate() {
        ctx.clearRect(0, 0, width, height);
        for (let p of particles) {
            p.x += p.vx; p.y += p.vy;
            if (p.x < 0 || p.x > width) p.vx *= -1;
            if (p.y < 0 || p.y > height) p.vy *= -1;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(0, 212, 255, ' + p.a + ')';
            ctx.fill();
        }
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const d = Math.sqrt(dx*dx + dy*dy);
                if (d < 120) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = 'rgba(0, 212, 255, ' + (0.12 * (1 - d/120)) + ')';
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(animate);
    }
    animate();
})();
</script>
"""

# ================= BANCO DE DADOS =================
DB_PATH = "marmed.db"


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nome TEXT,
            perfil TEXT DEFAULT 'admin'
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS contas_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fornecedor TEXT NOT NULL,
            descricao TEXT,
            valor REAL NOT NULL,
            vencimento DATE NOT NULL,
            status TEXT DEFAULT 'Pendente',
            categoria TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS contas_receber (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            descricao TEXT,
            valor REAL NOT NULL,
            vencimento DATE NOT NULL,
            status TEXT DEFAULT 'Pendente',
            categoria TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS empenhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            fornecedor TEXT NOT NULL,
            objeto TEXT,
            valor REAL NOT NULL,
            data_empenho DATE NOT NULL,
            status TEXT DEFAULT 'Ativo',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS licitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            modalidade TEXT NOT NULL,
            objeto TEXT,
            valor_estimado REAL NOT NULL,
            data_abertura DATE NOT NULL,
            status TEXT DEFAULT 'Em Andamento',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            fornecedor TEXT NOT NULL,
            objeto TEXT,
            valor REAL NOT NULL,
            inicio DATE NOT NULL,
            fim DATE NOT NULL,
            status TEXT DEFAULT 'Vigente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Usuario padrao
    default_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    c.execute("SELECT id FROM usuarios WHERE username = ?", ("admin",))
    if not c.fetchone():
        c.execute(
            "INSERT INTO usuarios (username, password_hash, nome, perfil) VALUES (?, ?, ?, ?)",
            ("admin", default_hash, "Administrador", "admin"),
        )
    conn.commit()
    conn.close()


# ================= UTILITARIOS =================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def format_currency(value):
    if value is None:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def authenticate(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, username, nome, perfil FROM usuarios WHERE username = ? AND password_hash = ?",
        (username, hash_password(password)),
    )
    user = c.fetchone()
    conn.close()
    return user


def update_password(username, new_password):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE usuarios SET password_hash = ? WHERE username = ?",
        (hash_password(new_password), username),
    )
    conn.commit()
    conn.close()


def load_table(table, order_by="id DESC"):
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM {table} ORDER BY {order_by}", conn)
    conn.close()
    return df


def insert_row(table, columns, values):
    conn = get_connection()
    c = conn.cursor()
    placeholders = ", ".join(["?"] * len(values))
    c.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", values)
    conn.commit()
    row_id = c.lastrowid
    conn.close()
    return row_id


def update_row(table, id_value, updates):
    conn = get_connection()
    c = conn.cursor()
    cols = ", ".join([f"{k} = ?" for k in updates.keys()])
    vals = list(updates.values()) + [id_value]
    c.execute(f"UPDATE {table} SET {cols} WHERE id = ?", vals)
    conn.commit()
    conn.close()


def delete_row(table, id_value):
    conn = get_connection()
    c = conn.cursor()
    c.execute(f"DELETE FROM {table} WHERE id = ?", (id_value,))
    conn.commit()
    conn.close()


def count_rows(table, where=None):
    conn = get_connection()
    c = conn.cursor()
    if where:
        c.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}")
    else:
        c.execute(f"SELECT COUNT(*) FROM {table}")
    result = c.fetchone()[0]
    conn.close()
    return result


def sum_column(table, column, where=None):
    conn = get_connection()
    c = conn.cursor()
    if where:
        c.execute(f"SELECT COALESCE(SUM({column}), 0) FROM {table} WHERE {where}")
    else:
        c.execute(f"SELECT COALESCE(SUM({column}), 0) FROM {table}")
    result = c.fetchone()[0]
    conn.close()
    return result


def render_title_3d(text):
    letters = ""
    for i, ch in enumerate(text):
        delay = 0.1 * i
        letters += f'<span class="letter" style="animation-delay: {delay}s">{ch}</span>'
    st.markdown(
        f'<div class="title-3d">{letters}</div><div class="subtitle">Gestão em Saúde Pública de Luminárias-MG</div>',
        unsafe_allow_html=True,
    )


def metric_card(label, value, col):
    with col:
        st.markdown(
            f'<div class="metric-card"><div class="metric-value">{value}</div><div class="metric-label">{label}</div></div>',
            unsafe_allow_html=True,
        )


# ================= PAGINAS =================
def login_page():
    st.markdown('<div class="glass-card" style="max-width: 500px; margin: auto; margin-top: 10vh;">', unsafe_allow_html=True)
    render_title_3d("MARMED")
    st.markdown("<<h3 style='text-align:center; color: white; margin-top: 2rem;'>Acesso ao Sistema</h3>", unsafe_allow_html=True)
    with st.form("login_form"):
        username = st.text_input("Usuário", value="admin")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar no Sistema")
        if submit:
            user = authenticate(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = user[1]
                st.session_state.nome = user[2]
                st.session_state.perfil = user[3]
                st.success("Login realizado com sucesso!")
                time.sleep(0.6)
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.markdown("</div>", unsafe_allow_html=True)


def dashboard_page():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_title_3d("MARMED")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<<br>", unsafe_allow_html=True)

    total_pagar = sum_column("contas_pagar", "valor")
    total_receber = sum_column("contas_receber", "valor")
    total_empenhos = sum_column("empenhos", "valor")
    total_licitacoes = sum_column("licitacoes", "valor_estimado")
    total_contratos = sum_column("contratos", "valor")

    c1, c2, c3, c4, c5 = st.columns(5)
    metric_card("Contas a Pagar", format_currency(total_pagar), c1)
    metric_card("Contas a Receber", format_currency(total_receber), c2)
    metric_card("Empenhos", format_currency(total_empenhos), c3)
    metric_card("Licitações", format_currency(total_licitacoes), c4)
    metric_card("Contratos", format_currency(total_contratos), c5)

    st.markdown("<<br>", unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("<<h3 style='color: #00d4ff;'>Resumo por Status</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<<h4 style='color: white;'>Contas a Pagar</h4>", unsafe_allow_html=True)
        df_pagar = pd.read_sql_query(
            "SELECT status, COUNT(*) as quantidade, SUM(valor) as total FROM contas_pagar GROUP BY status",
            get_connection(),
        )
        df_pagar["total"] = df_pagar["total"].apply(format_currency)
        st.dataframe(df_pagar, use_container_width=True, hide_index=True)
    with col2:
        st.markdown("<<h4 style='color: white;'>Contas a Receber</h4>", unsafe_allow_html=True)
        df_receber = pd.read_sql_query(
            "SELECT status, COUNT(*) as quantidade, SUM(valor) as total FROM contas_receber GROUP BY status",
            get_connection(),
        )
        df_receber["total"] = df_receber["total"].apply(format_currency)
        st.dataframe(df_receber, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def crud_page(title, table, columns, form_fields, status_options):
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_title_3d(title)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<<br>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Cadastrar", "Consultar / Editar", "Excluir"])

    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f"<<h3 style='color: #00d4ff;'>Novo {title}</h3>", unsafe_allow_html=True)
        with st.form(f"form_{table}"):
            values = []
            for field in form_fields:
                key = f"new_{table}_{field['name']}"
                if field["type"] == "text":
                    v = st.text_input(field["label"], key=key)
                elif field["type"] == "number":
                    v = st.number_input(field["label"], min_value=0.0, step=0.01, key=key)
                elif field["type"] == "date":
                    v = st.date_input(field["label"], key=key).strftime("%Y-%m-%d")
                elif field["type"] == "select":
                    v = st.selectbox(field["label"], field["options"], key=key)
                elif field["type"] == "textarea":
                    v = st.text_area(field["label"], key=key)
                values.append(v)
            submitted = st.form_submit_button("Salvar")
            if submitted:
                try:
                    insert_row(table, columns, values)
                    st.success("Registro salvo com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f"<<h3 style='color: #00d4ff;'>Listagem de {title}</h3>", unsafe_allow_html=True)
        df = load_table(table)
        if df.empty:
            st.info("Nenhum registro encontrado.")
        else:
            if "valor" in df.columns:
                df["valor"] = df["valor"].apply(format_currency)
            if "valor_estimado" in df.columns:
                df["valor_estimado"] = df["valor_estimado"].apply(format_currency)
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown("<<h4 style='color: #00d4ff;'>Editar Registro</h4>", unsafe_allow_html=True)
            ids = df["id"].tolist()
            selected_id = st.selectbox("Selecione o ID", ids, key=f"edit_id_{table}")
            if selected_id:
                conn = get_connection()
                row = pd.read_sql_query(f"SELECT * FROM {table} WHERE id = ?", conn, params=(selected_id,)).iloc[0]
                conn.close()
                with st.form(f"edit_form_{table}"):
                    updates = {}
                    for field in form_fields:
                        key = f"edit_{table}_{field['name']}_{selected_id}"
                        val = row[field["name"]]
                        if field["type"] == "text":
                            new_v = st.text_input(field["label"], value=str(val) if val else "", key=key)
                        elif field["type"] == "number":
                            new_v = st.number_input(field["label"], value=float(val) if val else 0.0, step=0.01, key=key)
                        elif field["type"] == "date":
                            new_v = st.date_input(field["label"], value=datetime.datetime.strptime(val, "%Y-%m-%d").date() if val else datetime.date.today(), key=key).strftime("%Y-%m-%d")
                        elif field["type"] == "select":
                            idx = field["options"].index(val) if val in field["options"] else 0
                            new_v = st.selectbox(field["label"], field["options"], index=idx, key=key)
                        elif field["type"] == "textarea":
                            new_v = st.text_area(field["label"], value=str(val) if val else "", key=key)
                        updates[field["name"]] = new_v
                    save = st.form_submit_button("Atualizar")
                    if save:
                        try:
                            update_row(table, selected_id, updates)
                            st.success("Registro atualizado com sucesso!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar: {e}")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f"<<h3 style='color: #ff006e;'>Excluir {title}</h3>", unsafe_allow_html=True)
        df = load_table(table)
        if df.empty:
            st.info("Nenhum registro para excluir.")
        else:
            ids = df["id"].tolist()
            del_id = st.selectbox("Selecione o ID para excluir", ids, key=f"del_id_{table}")
            if del_id:
                st.warning(f"Tem certeza que deseja excluir o registro ID {del_id}?")
                if st.button("Confirmar Exclusão", key=f"btn_del_{table}"):
                    delete_row(table, del_id)
                    st.success("Registro excluído com sucesso!")
                    time.sleep(0.5)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def trocar_senha_page():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    render_title_3d("Trocar Senha")
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<<br>", unsafe_allow_html=True)

    st.markdown('<div class="glass-card" style="max-width: 500px; margin: auto;">', unsafe_allow_html=True)
    with st.form("trocar_senha_form"):
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
        submit = st.form_submit_button("Alterar Senha")
        if submit:
            if not authenticate(st.session_state.username, senha_atual):
                st.error("Senha atual incorreta.")
            elif nova_senha != confirmar_senha:
                st.error("A nova senha e a confirmação não conferem.")
            elif len(nova_senha) < 6:
                st.warning("A nova senha deve ter pelo menos 6 caracteres.")
            else:
                update_password(st.session_state.username, nova_senha)
                st.success("Senha alterada com sucesso!")
    st.markdown("</div>", unsafe_allow_html=True)


# ================= MENU =================
def sidebar_menu():
    st.sidebar.markdown('<h1 style="text-align:center; color:#00d4ff;">MARMED</h1>', unsafe_allow_html=True)
    st.sidebar.markdown(
        f'<p style="text-align:center; color:rgba(255,255,255,0.7);">{st.session_state.nome}<br><small>{st.session_state.perfil}</small></p>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("<<hr>", unsafe_allow_html=True)
    menu = st.sidebar.radio(
        "Menu",
        [
            "Dashboard",
            "Contas a Pagar",
            "Contas a Receber",
            "Empenhos",
            "Licitações",
            "Contratos",
            "Trocar Senha",
        ],
        label_visibility="collapsed",
    )
    if st.sidebar.button("Sair do Sistema"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    return menu


# ================= MAIN =================
def main():
    init_db()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.components.v1.html(PARTICLES_JS, height=0)

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_page()
    else:
        menu = sidebar_menu()
        if menu == "Dashboard":
            dashboard_page()
        elif menu == "Contas a Pagar":
            crud_page(
                "Contas a Pagar",
                "contas_pagar",
                "fornecedor, descricao, valor, vencimento, status, categoria",
                [
                    {"name": "fornecedor", "label": "Fornecedor", "type": "text"},
                    {"name": "descricao", "label": "Descrição", "type": "textarea"},
                    {"name": "valor", "label": "Valor (R$)", "type": "number"},
                    {"name": "vencimento", "label": "Vencimento", "type": "date"},
                    {"name": "status", "label": "Status", "type": "select", "options": ["Pendente", "Pago", "Atrasado", "Cancelado"]},
                    {"name": "categoria", "label": "Categoria", "type": "text"},
                ],
                ["Pendente", "Pago", "Atrasado", "Cancelado"],
            )
        elif menu == "Contas a Receber":
            crud_page(
                "Contas a Receber",
                "contas_receber",
                "cliente, descricao, valor, vencimento, status, categoria",
                [
                    {"name": "cliente", "label": "Cliente", "type": "text"},
                    {"name": "descricao", "label": "Descrição", "type": "textarea"},
                    {"name": "valor", "label": "Valor (R$)", "type": "number"},
                    {"name": "vencimento", "label": "Vencimento", "type": "date"},
                    {"name": "status", "label": "Status", "type": "select", "options": ["Pendente", "Recebido", "Atrasado", "Cancelado"]},
                    {"name": "categoria", "label": "Categoria", "type": "text"},
                ],
                ["Pendente", "Recebido", "Atrasado", "Cancelado"],
            )
        elif menu == "Empenhos":
            crud_page(
                "Empenhos",
                "empenhos",
                "numero, fornecedor, objeto, valor, data_empenho, status",
                [
                    {"name": "numero", "label": "Número do Empenho", "type": "text"},
                    {"name": "fornecedor", "label": "Fornecedor", "type": "text"},
                    {"name": "objeto", "label": "Objeto", "type": "textarea"},
                    {"name": "valor", "label": "Valor (R$)", "type": "number"},
                    {"name": "data_empenho", "label": "Data do Empenho", "type": "date"},
                    {"name": "status", "label": "Status", "type": "select", "options": ["Ativo", "Anulado", "Liquidado", "Pago"]},
                ],
                ["Ativo", "Anulado", "Liquidado", "Pago"],
            )
        elif menu == "Licitações":
            crud_page(
                "Licitações",
                "licitacoes",
                "numero, modalidade, objeto, valor_estimado, data_abertura, status",
                [
                    {"name": "numero", "label": "Número da Licitação", "type": "text"},
                    {"name": "modalidade", "label": "Modalidade", "type": "text"},
                    {"name": "objeto", "label": "Objeto", "type": "textarea"},
                    {"name": "valor_estimado", "label": "Valor Estimado (R$)", "type": "number"},
                    {"name": "data_abertura", "label": "Data de Abertura", "type": "date"},
                    {"name": "status", "label": "Status", "type": "select", "options": ["Em Andamento", "Concluída", "Cancelada", "Suspensa"]},
                ],
                ["Em Andamento", "Concluída", "Cancelada", "Suspensa"],
            )
        elif menu == "Contratos":
            crud_page(
                "Contratos",
                "contratos",
                "numero, fornecedor, objeto, valor, inicio, fim, status",
                [
                    {"name": "numero", "label": "Número do Contrato", "type": "text"},
                    {"name": "fornecedor", "label": "Fornecedor", "type": "text"},
                    {"name": "objeto", "label": "Objeto", "type": "textarea"},
                    {"name": "valor", "label": "Valor (R$)", "type": "number"},
                    {"name": "inicio", "label": "Data de Início", "type": "date"},
                    {"name": "fim", "label": "Data de Término", "type": "date"},
                    {"name": "status", "label": "Status", "type": "select", "options": ["Vigente", "Encerrado", "Rescindido", "Renovado"]},
                ],
                ["Vigente", "Encerrado", "Rescindido", "Renovado"],
            )
        elif menu == "Trocar Senha":
            trocar_senha_page()


if __name__ == "__main__":
    main()
