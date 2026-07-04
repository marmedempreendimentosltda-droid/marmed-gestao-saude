import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import random
from datetime import datetime, date

# =============================================================================
# MARMED - Sistema de Gestão Financeira e Contratual (Streamlit)
# =============================================================================

st.set_page_config(
    page_title="MARMED",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CSS Customizado (Tema escuro, partículas, glassmorphism, título 3D)
# =============================================================================
def inject_custom_css():
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Montserrat:wght@300;400;600;700&display=swap');

    :root {
        --primary: #00d4ff;
        --secondary: #7b2cbf;
        --accent: #ff006e;
        --bg-dark: #0a0a1a;
        --bg-panel: rgba(15, 20, 35, 0.75);
        --glass: rgba(255, 255, 255, 0.08);
        --border: rgba(0, 212, 255, 0.25);
        --text: #e6f7ff;
        --muted: #a0b4c0;
    }

    html, body, [class*="stApp"] {
        background: var(--bg-dark) !important;
        color: var(--text) !important;
        font-family: 'Montserrat', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 20% 20%, rgba(0, 212, 255, 0.08) 0%, transparent 40%),
                    radial-gradient(circle at 80% 80%, rgba(123, 44, 191, 0.1) 0%, transparent 45%),
                    linear-gradient(135deg, #0a0a1a 0%, #101526 50%, #0a0a1a 100%) !important;
        min-height: 100vh;
    }

    #particles-canvas {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        z-index: 0;
    }

    .glass-card {
        background: var(--glass);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 28px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 20px rgba(0, 212, 255, 0.1);
        transition: all 0.3s ease;
    }

    .glass-card:hover {
        border-color: rgba(0, 212, 255, 0.6);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5), 0 0 30px rgba(0, 212, 255, 0.2);
    }

    .metric-card {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.15), rgba(123, 44, 191, 0.15));
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        transition: transform 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-5px);
    }

    .metric-value {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.2rem;
        font-weight: 900;
        color: var(--primary);
        text-shadow: 0 0 15px rgba(0, 212, 255, 0.5);
    }

    .metric-label {
        color: var(--muted);
        font-size: 0.95rem;
        margin-top: 8px;
        font-weight: 600;
    }

    .marmed-title {
        font-family: 'Orbitron', sans-serif;
        font-weight: 900;
        font-size: 5rem;
        text-align: center;
        color: #fff;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.8),
                     0 0 30px rgba(0, 212, 255, 0.6),
                     0 0 60px rgba(123, 44, 191, 0.6);
        letter-spacing: 12px;
        margin-bottom: 10px;
        perspective: 1000px;
    }

    .marmed-letter {
        display: inline-block;
        animation: flyIn 1.5s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        opacity: 0;
        transform: translateZ(-1000px) rotateY(180deg) scale(0.2);
    }

    @keyframes flyIn {
        0% { opacity: 0; transform: translateZ(-1000px) rotateY(180deg) scale(0.2); filter: blur(20px); }
        60% { opacity: 1; transform: translateZ(100px) rotateY(-10deg) scale(1.1); filter: blur(0px); }
        100% { opacity: 1; transform: translateZ(0) rotateY(0) scale(1); filter: blur(0px); }
    }

    .subtitle {
        text-align: center;
        color: var(--muted);
        font-size: 1.3rem;
        margin-bottom: 30px;
        font-weight: 300;
    }

    .sidebar-title {
        font-family: 'Orbitron', sans-serif;
        font-weight: 900;
        font-size: 2rem;
        text-align: center;
        color: var(--primary) !important;
        text-shadow: 0 0 15px rgba(0, 212, 255, 0.5);
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Orbitron', sans-serif;
        color: var(--primary) !important;
    }

    .stButton>button {
        background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 700 !important;
        font-family: 'Montserrat', sans-serif !important;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3) !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0, 212, 255, 0.5) !important;
    }

    .stButton>button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid var(--border) !important;
    }

    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>div>input,
    .stDateInput>div>div>input, .stSelectbox>div>div>div {
        background: rgba(0, 0, 0, 0.3) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
    }

    .stDataFrame {
        border: 1px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 1px solid var(--border);
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(0, 0, 0, 0.2) !important;
        border-radius: 10px 10px 0 0 !important;
        color: var(--muted) !important;
        font-weight: 600 !important;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(0, 212, 255, 0.15) !important;
        color: var(--primary) !important;
        border-bottom: 2px solid var(--primary) !important;
    }

    hr {
        border-color: var(--border) !important;
    }

    .success-msg { color: #4ade80; font-weight: 700; }
    .error-msg { color: #f87171; font-weight: 700; }
    .warning-msg { color: #fbbf24; font-weight: 700; }

    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: rgba(0, 0, 0, 0.2); }
    ::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 4px; }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def inject_particles():
    html = """
    <canvas id="particles-canvas"></canvas>
    <script>
    (function() {
        const canvas = document.getElementById('particles-canvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        let width, height;
        const particles = [];
        const count = 70;

        function resize() {
            width = canvas.width = window.innerWidth;
            height = canvas.height = window.innerHeight;
        }
        resize();
        window.addEventListener('resize', resize);

        for (let i = 0; i < count; i++) {
            particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                r: Math.random() * 2 + 0.5,
                dx: (Math.random() - 0.5) * 0.5,
                dy: (Math.random() - 0.5) * 0.5,
                alpha: Math.random() * 0.5 + 0.2
            });
        }

        function animate() {
            ctx.clearRect(0, 0, width, height);
            particles.forEach(p => {
                p.x += p.dx;
                p.y += p.dy;
                if (p.x < 0 || p.x > width) p.dx *= -1;
                if (p.y < 0 || p.y > height) p.dy *= -1;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(0, 212, 255, ' + p.alpha + ')';
                ctx.fill();
            });
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const dist = Math.sqrt(dx*dx + dy*dy);
                    if (dist < 120) {
                        ctx.beginPath();
                        ctx.strokeStyle = 'rgba(0, 212, 255, ' + (0.15 * (1 - dist/120)) + ')';
                        ctx.lineWidth = 1;
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
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
    st.markdown(html, unsafe_allow_html=True)


# =============================================================================
# Banco de Dados SQLite
# =============================================================================
DB_FILE = "marmed.db"


def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS contas_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            fornecedor TEXT,
            valor REAL NOT NULL,
            vencimento TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pendente',
            categoria TEXT,
            observacao TEXT,
            created_at TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS contas_receber (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            cliente TEXT,
            valor REAL NOT NULL,
            vencimento TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pendente',
            categoria TEXT,
            observacao TEXT,
            created_at TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS empenhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            data_empenho TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Ativo',
            dotacao TEXT,
            observacao TEXT,
            created_at TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS licitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            objeto TEXT NOT NULL,
            modalidade TEXT NOT NULL,
            valor_estimado REAL,
            data_abertura TEXT,
            status TEXT NOT NULL DEFAULT 'Em Andamento',
            vencedor TEXT,
            observacao TEXT,
            created_at TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            objeto TEXT NOT NULL,
            contratada TEXT NOT NULL,
            valor REAL NOT NULL,
            inicio TEXT NOT NULL,
            fim TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Vigente',
            observacao TEXT,
            created_at TEXT NOT NULL
        )
    ''')

    # Usuário padrão
    c.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    if not c.fetchone():
        c.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            ("admin", hash_password("Diretor2025#"), now_str())
        )

    conn.commit()
    conn.close()


# =============================================================================
# Utilitários
# =============================================================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_currency(value: float) -> str:
    if value is None:
        value = 0.0
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def status_color(status: str) -> str:
    status = status.lower()
    if status in ("pago", "recebido", "ativo", "vigente", "concluído", "concluido"):
        return "#4ade80"
    elif status in ("pendente", "em andamento"):
        return "#fbbf24"
    elif status in ("atrasado", "vencido", "cancelado", "inadimplente"):
        return "#f87171"
    return "#a0b4c0"


# =============================================================================
# Autenticação
# =============================================================================
def check_credentials(username: str, password: str) -> bool:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if not row:
        return False
    return row[0] == hash_password(password)


def change_password(username: str, new_password: str) -> bool:
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hash_password(new_password), username))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0


# =============================================================================
# CRUD Genérico
# =============================================================================
def execute_query(query: str, params=()):
    conn = get_connection()
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    last_id = c.lastrowid
    conn.close()
    return last_id


def fetch_all(query: str, params=()) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows


def fetch_one(query: str, params=()) -> tuple:
    conn = get_connection()
    c = conn.cursor()
    c.execute(query, params)
    row = c.fetchone()
    conn.close()
    return row


def delete_record(table: str, id_val: int):
    execute_query(f"DELETE FROM {table} WHERE id = ?", (id_val,))


def count_records(table: str) -> int:
    row = fetch_one(f"SELECT COUNT(*) FROM {table}")
    return row[0] if row else 0


def sum_column(table: str, column: str) -> float:
    row = fetch_one(f"SELECT COALESCE(SUM({column}), 0) FROM {table}")
    return row[0] if row else 0.0


# =============================================================================
# Componentes de UI
# =============================================================================
def animated_title():
    letters = "MARMED"
    html = '<div class="marmed-title">'
    for i, letter in enumerate(letters):
        html += f'<span class="marmed-letter" style="animation-delay: {i * 0.12}s">{letter}</span>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def metric_card(label: str, value: str, color: str = "#00d4ff"):
    html = f"""
    <div class="metric-card">
        <div class="metric-value" style="color: {color};">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def section_header(title: str):
    st.markdown(f"<<h2 style='margin-top: 0; margin-bottom: 20px; color: #00d4ff;'>{title}</h2>", unsafe_allow_html=True)


def glass_container_start():
    st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)


def glass_container_end():
    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# Módulos do Sistema
# =============================================================================
def dashboard():
    section_header("Dashboard")

    total_pagar = sum_column("contas_pagar", "valor")
    total_receber = sum_column("contas_receber", "valor")
    total_empenhos = sum_column("empenhos", "valor")
    total_contratos = sum_column("contratos", "valor")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Contas a Pagar", format_currency(total_pagar), "#ff6b6b")
    with col2:
        metric_card("Contas a Receber", format_currency(total_receber), "#4ade80")
    with col3:
        metric_card("Empenhos", format_currency(total_empenhos), "#00d4ff")
    with col4:
        metric_card("Contratos", format_currency(total_contratos), "#a855f7")

    st.markdown("<<hr/>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<<h3 style='color: #ff6b6b;'>Resumo Contas a Pagar</h3>", unsafe_allow_html=True)
        data = fetch_all("SELECT status, COUNT(*), SUM(valor) FROM contas_pagar GROUP BY status")
        if data:
            df = pd.DataFrame(data, columns=["Status", "Quantidade", "Valor"])
            df["Valor"] = df["Valor"].apply(format_currency)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma conta a pagar cadastrada.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<<h3 style='color: #4ade80;'>Resumo Contas a Receber</h3>", unsafe_allow_html=True)
        data = fetch_all("SELECT status, COUNT(*), SUM(valor) FROM contas_receber GROUP BY status")
        if data:
            df = pd.DataFrame(data, columns=["Status", "Quantidade", "Valor"])
            df["Valor"] = df["Valor"].apply(format_currency)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma conta a receber cadastrada.")
        st.markdown("</div>", unsafe_allow_html=True)


def manage_contas_pagar():
    section_header("Contas a Pagar")
    tab1, tab2 = st.tabs(["Listar", "Cadastrar / Editar"])

    with tab1:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        rows = fetch_all("SELECT id, descricao, fornecedor, valor, vencimento, status, categoria, observacao FROM contas_pagar ORDER BY vencimento")
        if rows:
            df = pd.DataFrame(rows, columns=["ID", "Descrição", "Fornecedor", "Valor", "Vencimento", "Status", "Categoria", "Observação"])
            df["Valor"] = df["Valor"].apply(format_currency)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro encontrado.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        edit_id = st.session_state.get("edit_pagar", None)
        descricao = ""
        fornecedor = ""
        valor = 0.0
        vencimento = date.today()
        status = "Pendente"
        categoria = ""
        observacao = ""

        if edit_id:
            row = fetch_one("SELECT * FROM contas_pagar WHERE id = ?", (edit_id,))
            if row:
                descricao = row[1]
                fornecedor = row[2] or ""
                valor = row[3]
                vencimento = datetime.strptime(row[4], "%Y-%m-%d").date()
                status = row[5]
                categoria = row[6] or ""
                observacao = row[7] or ""

        with st.form("form_pagar", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                descricao = st.text_input("Descrição", value=descricao)
                fornecedor = st.text_input("Fornecedor", value=fornecedor)
                valor = st.number_input("Valor (R$)", min_value=0.0, value=valor, step=0.01, format="%.2f")
            with col2:
                vencimento = st.date_input("Vencimento", value=vencimento)
                status = st.selectbox("Status", ["Pendente", "Pago", "Atrasado", "Cancelado"], index=["Pendente", "Pago", "Atrasado", "Cancelado"].index(status))
                categoria = st.text_input("Categoria", value=categoria)
            observacao = st.text_area("Observação", value=observacao)

            submitted = st.form_submit_button("Salvar")
            if submitted:
                if not descricao or valor <= 0:
                    st.error("Descrição e valor são obrigatórios.")
                else:
                    if edit_id:
                        execute_query(
                            "UPDATE contas_pagar SET descricao=?, fornecedor=?, valor=?, vencimento=?, status=?, categoria=?, observacao=? WHERE id=?",
                            (descricao, fornecedor, valor, vencimento.strftime("%Y-%m-%d"), status, categoria, observacao, edit_id)
                        )
                        st.success("Registro atualizado com sucesso!")
                        st.session_state.edit_pagar = None
                        st.rerun()
                    else:
                        execute_query(
                            "INSERT INTO contas_pagar (descricao, fornecedor, valor, vencimento, status, categoria, observacao, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (descricao, fornecedor, valor, vencimento.strftime("%Y-%m-%d"), status, categoria, observacao, now_str())
                        )
                        st.success("Registro cadastrado com sucesso!")
                        st.rerun()

        if edit_id:
            if st.button("Cancelar Edição", key="cancel_pagar"):
                st.session_state.edit_pagar = None
                st.rerun()

        st.markdown("<<h4>Ações</h4>", unsafe_allow_html=True)
        ids = [r[0] for r in fetch_all("SELECT id, descricao FROM contas_pagar")]
        if ids:
            selected = st.selectbox("Selecione para editar/excluir", ids, format_func=lambda x: f"#{x} - {fetch_one('SELECT descricao FROM contas_pagar WHERE id=?', (x,))[0]}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Editar", key="edit_pagar_btn"):
                    st.session_state.edit_pagar = selected
                    st.rerun()
            with c2:
                if st.button("Excluir", key="del_pagar_btn"):
                    delete_record("contas_pagar", selected)
                    st.success("Registro excluído!")
                    if st.session_state.get("edit_pagar") == selected:
                        st.session_state.edit_pagar = None
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def manage_contas_receber():
    section_header("Contas a Receber")
    tab1, tab2 = st.tabs(["Listar", "Cadastrar / Editar"])

    with tab1:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        rows = fetch_all("SELECT id, descricao, cliente, valor, vencimento, status, categoria, observacao FROM contas_receber ORDER BY vencimento")
        if rows:
            df = pd.DataFrame(rows, columns=["ID", "Descrição", "Cliente", "Valor", "Vencimento", "Status", "Categoria", "Observação"])
            df["Valor"] = df["Valor"].apply(format_currency)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro encontrado.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        edit_id = st.session_state.get("edit_receber", None)
        descricao = ""
        cliente = ""
        valor = 0.0
        vencimento = date.today()
        status = "Pendente"
        categoria = ""
        observacao = ""

        if edit_id:
            row = fetch_one("SELECT * FROM contas_receber WHERE id = ?", (edit_id,))
            if row:
                descricao = row[1]
                cliente = row[2] or ""
                valor = row[3]
                vencimento = datetime.strptime(row[4], "%Y-%m-%d").date()
                status = row[5]
                categoria = row[6] or ""
                observacao = row[7] or ""

        with st.form("form_receber", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                descricao = st.text_input("Descrição", value=descricao)
                cliente = st.text_input("Cliente", value=cliente)
                valor = st.number_input("Valor (R$)", min_value=0.0, value=valor, step=0.01, format="%.2f")
            with col2:
                vencimento = st.date_input("Vencimento", value=vencimento)
                status = st.selectbox("Status", ["Pendente", "Recebido", "Atrasado", "Cancelado"], index=["Pendente", "Recebido", "Atrasado", "Cancelado"].index(status))
                categoria = st.text_input("Categoria", value=categoria)
            observacao = st.text_area("Observação", value=observacao)

            submitted = st.form_submit_button("Salvar")
            if submitted:
                if not descricao or valor <= 0:
                    st.error("Descrição e valor são obrigatórios.")
                else:
                    if edit_id:
                        execute_query(
                            "UPDATE contas_receber SET descricao=?, cliente=?, valor=?, vencimento=?, status=?, categoria=?, observacao=? WHERE id=?",
                            (descricao, cliente, valor, vencimento.strftime("%Y-%m-%d"), status, categoria, observacao, edit_id)
                        )
                        st.success("Registro atualizado com sucesso!")
                        st.session_state.edit_receber = None
                        st.rerun()
                    else:
                        execute_query(
                            "INSERT INTO contas_receber (descricao, cliente, valor, vencimento, status, categoria, observacao, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (descricao, cliente, valor, vencimento.strftime("%Y-%m-%d"), status, categoria, observacao, now_str())
                        )
                        st.success("Registro cadastrado com sucesso!")
                        st.rerun()

        if edit_id:
            if st.button("Cancelar Edição", key="cancel_receber"):
                st.session_state.edit_receber = None
                st.rerun()

        st.markdown("<<h4>Ações</h4>", unsafe_allow_html=True)
        ids = [r[0] for r in fetch_all("SELECT id, descricao FROM contas_receber")]
        if ids:
            selected = st.selectbox("Selecione para editar/excluir", ids, format_func=lambda x: f"#{x} - {fetch_one('SELECT descricao FROM contas_receber WHERE id=?', (x,))[0]}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Editar", key="edit_receber_btn"):
                    st.session_state.edit_receber = selected
                    st.rerun()
            with c2:
                if st.button("Excluir", key="del_receber_btn"):
                    delete_record("contas_receber", selected)
                    st.success("Registro excluído!")
                    if st.session_state.get("edit_receber") == selected:
                        st.session_state.edit_receber = None
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def manage_empenhos():
    section_header("Empenhos")
    tab1, tab2 = st.tabs(["Listar", "Cadastrar / Editar"])

    with tab1:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        rows = fetch_all("SELECT id, numero, descricao, valor, data_empenho, status, dotacao, observacao FROM empenhos ORDER BY data_empenho DESC")
        if rows:
            df = pd.DataFrame(rows, columns=["ID", "Número", "Descrição", "Valor", "Data Empenho", "Status", "Dotação", "Observação"])
            df["Valor"] = df["Valor"].apply(format_currency)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro encontrado.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        edit_id = st.session_state.get("edit_empenho", None)
        numero = ""
        descricao = ""
        valor = 0.0
        data_empenho = date.today()
        status = "Ativo"
        dotacao = ""
        observacao = ""

        if edit_id:
            row = fetch_one("SELECT * FROM empenhos WHERE id = ?", (edit_id,))
            if row:
                numero = row[1]
                descricao = row[2]
                valor = row[3]
                data_empenho = datetime.strptime(row[4], "%Y-%m-%d").date()
                status = row[5]
                dotacao = row[6] or ""
                observacao = row[7] or ""

        with st.form("form_empenho", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                numero = st.text_input("Número do Empenho", value=numero)
                descricao = st.text_input("Descrição", value=descricao)
                valor = st.number_input("Valor (R$)", min_value=0.0, value=valor, step=0.01, format="%.2f")
            with col2:
                data_empenho = st.date_input("Data do Empenho", value=data_empenho)
                status = st.selectbox("Status", ["Ativo", "Anulado", "Liquidado", "Cancelado"], index=["Ativo", "Anulado", "Liquidado", "Cancelado"].index(status))
                dotacao = st.text_input("Dotação Orçamentária", value=dotacao)
            observacao = st.text_area("Observação", value=observacao)

            submitted = st.form_submit_button("Salvar")
            if submitted:
                if not numero or not descricao or valor <= 0:
                    st.error("Número, descrição e valor são obrigatórios.")
                else:
                    if edit_id:
                        execute_query(
                            "UPDATE empenhos SET numero=?, descricao=?, valor=?, data_empenho=?, status=?, dotacao=?, observacao=? WHERE id=?",
                            (numero, descricao, valor, data_empenho.strftime("%Y-%m-%d"), status, dotacao, observacao, edit_id)
                        )
                        st.success("Empenho atualizado com sucesso!")
                        st.session_state.edit_empenho = None
                        st.rerun()
                    else:
                        execute_query(
                            "INSERT INTO empenhos (numero, descricao, valor, data_empenho, status, dotacao, observacao, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (numero, descricao, valor, data_empenho.strftime("%Y-%m-%d"), status, dotacao, observacao, now_str())
                        )
                        st.success("Empenho cadastrado com sucesso!")
                        st.rerun()

        if edit_id:
            if st.button("Cancelar Edição", key="cancel_empenho"):
                st.session_state.edit_empenho = None
                st.rerun()

        st.markdown("<<h4>Ações</h4>", unsafe_allow_html=True)
        ids = [r[0] for r in fetch_all("SELECT id, numero FROM empenhos")]
        if ids:
            selected = st.selectbox("Selecione para editar/excluir", ids, format_func=lambda x: f"#{x} - {fetch_one('SELECT numero FROM empenhos WHERE id=?', (x,))[0]}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Editar", key="edit_empenho_btn"):
                    st.session_state.edit_empenho = selected
                    st.rerun()
            with c2:
                if st.button("Excluir", key="del_empenho_btn"):
                    delete_record("empenhos", selected)
                    st.success("Registro excluído!")
                    if st.session_state.get("edit_empenho") == selected:
                        st.session_state.edit_empenho = None
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def manage_licitacoes():
    section_header("Licitações")
    tab1, tab2 = st.tabs(["Listar", "Cadastrar / Editar"])

    with tab1:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        rows = fetch_all("SELECT id, numero, objeto, modalidade, valor_estimado, data_abertura, status, vencedor, observacao FROM licitacoes ORDER BY data_abertura DESC")
        if rows:
            df = pd.DataFrame(rows, columns=["ID", "Número", "Objeto", "Modalidade", "Valor Estimado", "Data Abertura", "Status", "Vencedor", "Observação"])
            df["Valor Estimado"] = df["Valor Estimado"].apply(format_currency)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro encontrado.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        edit_id = st.session_state.get("edit_licitacao", None)
        numero = ""
        objeto = ""
        modalidade = "Pregão"
        valor_estimado = 0.0
        data_abertura = date.today()
        status = "Em Andamento"
        vencedor = ""
        observacao = ""

        if edit_id:
            row = fetch_one("SELECT * FROM licitacoes WHERE id = ?", (edit_id,))
            if row:
                numero = row[1]
                objeto = row[2]
                modalidade = row[3]
                valor_estimado = row[4] or 0.0
                data_abertura = datetime.strptime(row[5], "%Y-%m-%d").date() if row[5] else date.today()
                status = row[6]
                vencedor = row[7] or ""
                observacao = row[8] or ""

        with st.form("form_licitacao", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                numero = st.text_input("Número da Licitação", value=numero)
                objeto = st.text_input("Objeto", value=objeto)
                modalidade = st.selectbox("Modalidade", ["Pregão", "Concorrência", "Convite", "Tomada de Preços", "Leilão", "Dispensa", "Inexigibilidade"], index=["Pregão", "Concorrência", "Convite", "Tomada de Preços", "Leilão", "Dispensa", "Inexigibilidade"].index(modalidade))
            with col2:
                valor_estimado = st.number_input("Valor Estimado (R$)", min_value=0.0, value=valor_estimado, step=0.01, format="%.2f")
                data_abertura = st.date_input("Data de Abertura", value=data_abertura)
                status = st.selectbox("Status", ["Em Andamento", "Concluída", "Cancelada", "Adiada", "Revogada"], index=["Em Andamento", "Concluída", "Cancelada", "Adiada", "Revogada"].index(status))
            vencedor = st.text_input("Empresa Vencedora", value=vencedor)
            observacao = st.text_area("Observação", value=observacao)

            submitted = st.form_submit_button("Salvar")
            if submitted:
                if not numero or not objeto:
                    st.error("Número e objeto são obrigatórios.")
                else:
                    if edit_id:
                        execute_query(
                            "UPDATE licitacoes SET numero=?, objeto=?, modalidade=?, valor_estimado=?, data_abertura=?, status=?, vencedor=?, observacao=? WHERE id=?",
                            (numero, objeto, modalidade, valor_estimado, data_abertura.strftime("%Y-%m-%d"), status, vencedor, observacao, edit_id)
                        )
                        st.success("Licitação atualizada com sucesso!")
                        st.session_state.edit_licitacao = None
                        st.rerun()
                    else:
                        execute_query(
                            "INSERT INTO licitacoes (numero, objeto, modalidade, valor_estimado, data_abertura, status, vencedor, observacao, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (numero, objeto, modalidade, valor_estimado, data_abertura.strftime("%Y-%m-%d"), status, vencedor, observacao, now_str())
                        )
                        st.success("Licitação cadastrada com sucesso!")
                        st.rerun()

        if edit_id:
            if st.button("Cancelar Edição", key="cancel_licitacao"):
                st.session_state.edit_licitacao = None
                st.rerun()

        st.markdown("<<h4>Ações</h4>", unsafe_allow_html=True)
        ids = [r[0] for r in fetch_all("SELECT id, numero FROM licitacoes")]
        if ids:
            selected = st.selectbox("Selecione para editar/excluir", ids, format_func=lambda x: f"#{x} - {fetch_one('SELECT numero FROM licitacoes WHERE id=?', (x,))[0]}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Editar", key="edit_licitacao_btn"):
                    st.session_state.edit_licitacao = selected
                    st.rerun()
            with c2:
                if st.button("Excluir", key="del_licitacao_btn"):
                    delete_record("licitacoes", selected)
                    st.success("Registro excluído!")
                    if st.session_state.get("edit_licitacao") == selected:
                        st.session_state.edit_licitacao = None
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def manage_contratos():
    section_header("Contratos")
    tab1, tab2 = st.tabs(["Listar", "Cadastrar / Editar"])

    with tab1:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        rows = fetch_all("SELECT id, numero, objeto, contratada, valor, inicio, fim, status, observacao FROM contratos ORDER BY inicio DESC")
        if rows:
            df = pd.DataFrame(rows, columns=["ID", "Número", "Objeto", "Contratada", "Valor", "Início", "Fim", "Status", "Observação"])
            df["Valor"] = df["Valor"].apply(format_currency)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro encontrado.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        edit_id = st.session_state.get("edit_contrato", None)
        numero = ""
        objeto = ""
        contratada = ""
        valor = 0.0
        inicio = date.today()
        fim = date.today()
        status = "Vigente"
        observacao = ""

        if edit_id:
            row = fetch_one("SELECT * FROM contratos WHERE id = ?", (edit_id,))
            if row:
                numero = row[1]
                objeto = row[2]
                contratada = row[3]
                valor = row[4]
                inicio = datetime.strptime(row[5], "%Y-%m-%d").date()
                fim = datetime.strptime(row[6], "%Y-%m-%d").date()
                status = row[7]
                observacao = row[8] or ""

        with st.form("form_contrato", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                numero = st.text_input("Número do Contrato", value=numero)
                objeto = st.text_input("Objeto", value=objeto)
                contratada = st.text_input("Contratada", value=contratada)
            with col2:
                valor = st.number_input("Valor (R$)", min_value=0.0, value=valor, step=0.01, format="%.2f")
                inicio = st.date_input("Data de Início", value=inicio)
                fim = st.date_input("Data de Fim", value=fim)
            status = st.selectbox("Status", ["Vigente", "Concluído", "Cancelado", "Suspenso", "Rescindido"], index=["Vigente", "Concluído", "Cancelado", "Suspenso", "Rescindido"].index(status))
            observacao = st.text_area("Observação", value=observacao)

            submitted = st.form_submit_button("Salvar")
            if submitted:
                if not numero or not objeto or not contratada:
                    st.error("Número, objeto e contratada são obrigatórios.")
                elif fim < inicio:
                    st.error("A data de fim não pode ser anterior à data de início.")
                else:
                    if edit_id:
                        execute_query(
                            "UPDATE contratos SET numero=?, objeto=?, contratada=?, valor=?, inicio=?, fim=?, status=?, observacao=? WHERE id=?",
                            (numero, objeto, contratada, valor, inicio.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d"), status, observacao, edit_id)
                        )
                        st.success("Contrato atualizado com sucesso!")
                        st.session_state.edit_contrato = None
                        st.rerun()
                    else:
                        execute_query(
                            "INSERT INTO contratos (numero, objeto, contratada, valor, inicio, fim, status, observacao, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (numero, objeto, contratada, valor, inicio.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d"), status, observacao, now_str())
                        )
                        st.success("Contrato cadastrado com sucesso!")
                        st.rerun()

        if edit_id:
            if st.button("Cancelar Edição", key="cancel_contrato"):
                st.session_state.edit_contrato = None
                st.rerun()

        st.markdown("<<h4>Ações</h4>", unsafe_allow_html=True)
        ids = [r[0] for r in fetch_all("SELECT id, numero FROM contratos")]
        if ids:
            selected = st.selectbox("Selecione para editar/excluir", ids, format_func=lambda x: f"#{x} - {fetch_one('SELECT numero FROM contratos WHERE id=?', (x,))[0]}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Editar", key="edit_contrato_btn"):
                    st.session_state.edit_contrato = selected
                    st.rerun()
            with c2:
                if st.button("Excluir", key="del_contrato_btn"):
                    delete_record("contratos", selected)
                    st.success("Registro excluído!")
                    if st.session_state.get("edit_contrato") == selected:
                        st.session_state.edit_contrato = None
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def change_password_page():
    section_header("Trocar Senha")
    st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
    with st.form("form_senha"):
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
        submitted = st.form_submit_button("Alterar Senha")

        if submitted:
            if not senha_atual or not nova_senha or not confirmar_senha:
                st.error("Todos os campos são obrigatórios.")
            elif not check_credentials(st.session_state.username, senha_atual):
                st.error("Senha atual incorreta.")
            elif nova_senha != confirmar_senha:
                st.error("A nova senha e a confirmação não coincidem.")
            elif len(nova_senha) < 6:
                st.error("A nova senha deve ter no mínimo 6 caracteres.")
            else:
                if change_password(st.session_state.username, nova_senha):
                    st.success("Senha alterada com sucesso!")
                else:
                    st.error("Erro ao alterar senha.")
    st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# Sidebar
# =============================================================================
def sidebar_menu():
    st.sidebar.markdown('<h1 style="text-align:center; color:#00d4ff;">MARMED</h1>', unsafe_allow_html=True)
    st.sidebar.markdown(f"<<p style='text-align:center; color:#a0b4c0;'>Usuário: <b>{st.session_state.username}</b></p>", unsafe_allow_html=True)
    st.sidebar.markdown("<<hr/>", unsafe_allow_html=True)

    menu = st.sidebar.radio(
        "Menu",
        ["Dashboard", "Contas a Pagar", "Contas a Receber", "Empenhos", "Licitações", "Contratos", "Trocar Senha", "Sair"],
        label_visibility="collapsed"
    )
    st.sidebar.markdown("<<hr/>", unsafe_allow_html=True)
    st.sidebar.markdown("<<p style='text-align:center; color:#a0b4c0; font-size:0.85rem;'>MARMED v1.0</p>", unsafe_allow_html=True)
    return menu


# =============================================================================
# Login
# =============================================================================
def login_page():
    inject_custom_css()
    inject_particles()

    st.markdown("<<div style='height: 10vh;'></div>", unsafe_allow_html=True)

    animated_title()
    st.markdown("<<p class='subtitle'>Sistema Integrado de Gestão Financeira e Contratual</p>", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<<h3 style='text-align:center; color:#00d4ff; margin-top:0;'>Acesso ao Sistema</h3>", unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar")

            if submitted:
                if check_credentials(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")

        st.markdown("<<p style='text-align:center; color:#a0b4c0; font-size:0.85rem; margin-bottom:0;'>Usuário padrão: admin | Senha: Diretor2025#</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# =============================================================================
# Main
# =============================================================================
def main():
    init_db()

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        login_page()
    else:
        inject_custom_css()
        inject_particles()

        menu = sidebar_menu()

        if menu == "Dashboard":
            dashboard()
        elif menu == "Contas a Pagar":
            manage_contas_pagar()
        elif menu == "Contas a Receber":
            manage_contas_receber()
        elif menu == "Empenhos":
            manage_empenhos()
        elif menu == "Licitações":
            manage_licitacoes()
        elif menu == "Contratos":
            manage_contratos()
        elif menu == "Trocar Senha":
            change_password_page()
        elif menu == "Sair":
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()


if __name__ == "__main__":
    main()
