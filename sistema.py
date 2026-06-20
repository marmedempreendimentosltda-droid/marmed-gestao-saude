import streamlit as st
import hashlib
import sqlite3
import pandas as pd
import random
from datetime import datetime, date
import plotly.express as px

st.set_page_config(
    page_title="MARMED - Gestão em Saúde Pública",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

DEFAULT_USER = "admin"
DEFAULT_PASS = "Diretor2025#"
DEFAULT_HASH = hashlib.sha256(DEFAULT_PASS.encode()).hexdigest()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None
if "edit_table" not in st.session_state:
    st.session_state.edit_table = None


def init_db():
    conn = sqlite3.connect("marmed.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS contas_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT,
            credor TEXT,
            valor REAL,
            vencimento TEXT,
            status TEXT,
            categoria TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS contas_receber (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT,
            devedor TEXT,
            valor REAL,
            vencimento TEXT,
            status TEXT,
            categoria TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS empenhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            descricao TEXT,
            valor REAL,
            data TEXT,
            fonte TEXT,
            status TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS licitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            objeto TEXT,
            modalidade TEXT,
            valor REAL,
            data_abertura TEXT,
            status TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            contratado TEXT,
            objeto TEXT,
            valor REAL,
            inicio TEXT,
            fim TEXT,
            status TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS transferencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT,
            origem TEXT,
            destino TEXT,
            valor REAL,
            data TEXT,
            tipo TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS transposicoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT,
            origem TEXT,
            destino TEXT,
            valor REAL,
            data TEXT,
            tipo TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS repasses_federal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT,
            valor REAL,
            data TEXT,
            programa TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS repasses_estadual (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT,
            valor REAL,
            data TEXT,
            programa TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS recursos_municipal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT,
            valor REAL,
            data TEXT,
            origem TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE,
            senha_hash TEXT
        )
    """)
    c.execute("""
        INSERT OR IGNORE INTO usuarios (usuario, senha_hash) VALUES (?, ?)
    """, (DEFAULT_USER, DEFAULT_HASH))
    conn.commit()
    return conn


conn = init_db()


def login_page():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    .main { background: linear-gradient(135deg, #050510 0%, #0a0a20 50%, #02020a 100%); min-height: 100vh; }
    .login-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        padding: 20px;
    }
    .title-3d {
        font-family: 'Orbitron', sans-serif;
        font-size: 5rem;
        font-weight: 900;
        color: #00d4ff;
        text-align: center;
        perspective: 1000px;
        margin-bottom: 10px;
        text-shadow: 0 0 10px #00d4ff, 0 0 30px #00d4ff, 0 0 60px #008cff;
    }
    .title-3d span {
        display: inline-block;
        animation: flyIn 3s ease-out forwards, glowPulse 2s ease-in-out infinite 3s, flash 0.4s ease-out 3s;
        opacity: 0;
        transform-style: preserve-3d;
    }
    .title-3d .m1 { --tx: -500px; --ty: -300px; --tz: 800px; --rx: 120deg; --ry: -80deg; animation-delay: 0s, 3s, 3s; }
    .title-3d .a1 { --tx: 400px; --ty: -250px; --tz: -600px; --rx: -100deg; --ry: 90deg; animation-delay: 0.18s, 3.18s, 3.18s; }
    .title-3d .r1 { --tx: -300px; --ty: 350px; --tz: 500px; --rx: 80deg; --ry: -120deg; animation-delay: 0.36s, 3.36s, 3.36s; }
    .title-3d .m2 { --tx: 500px; --ty: 300px; --tz: -400px; --rx: -70deg; --ry: 100deg; animation-delay: 0.54s, 3.54s, 3.54s; }
    .title-3d .e1 { --tx: -400px; --ty: -200px; --tz: 700px; --rx: 110deg; --ry: -90deg; animation-delay: 0.72s, 3.72s, 3.72s; }
    .title-3d .d1 { --tx: 300px; --ty: 250px; --tz: -800px; --rx: -130deg; --ry: 70deg; animation-delay: 0.90s, 3.90s, 3.90s; }
    @keyframes flyIn {
        0% { opacity: 0; transform: translate3d(var(--tx), var(--ty), var(--tz)) rotateX(var(--rx)) rotateY(var(--ry)); }
        60% { opacity: 1; }
        100% { opacity: 1; transform: translate3d(0, 0, 0) rotateX(0deg) rotateY(0deg); }
    }
    @keyframes glowPulse {
        0%, 100% { text-shadow: 0 0 10px #00d4ff, 0 0 30px #00d4ff, 0 0 60px #008cff; }
        50% { text-shadow: 0 0 20px #00d4ff, 0 0 50px #00d4ff, 0 0 100px #008cff, 0 0 150px #ffffff; }
    }
    @keyframes flash {
        0% { text-shadow: 0 0 5px #fff, 0 0 20px #ffd700; color: #ffffff; }
        50% { text-shadow: 0 0 50px #ffd700, 0 0 100px #ffffff; color: #ffd700; }
        100% { text-shadow: 0 0 10px #00d4ff, 0 0 30px #00d4ff; color: #00d4ff; }
    }
    .subtitle-cyan { color: #00d4ff; font-size: 1.5rem; text-align: center; font-family: 'Orbitron', sans-serif; margin-top: 0; }
    .subtitle-blue { color: #87cefa; font-size: 1.2rem; text-align: center; font-family: 'Orbitron', sans-serif; margin-top: 5px; }
    .glass-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 20px;
        padding: 40px;
        width: 100%;
        max-width: 420px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5), 0 0 30px rgba(0, 212, 255, 0.1);
        margin-top: 30px;
    }
    .field-label { color: #e0f7ff; font-weight: 600; margin-bottom: 5px; display: block; }
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.15) !important;
        border: 2px solid #00d4ff !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        padding: 12px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #ffd700 !important;
        box-shadow: 0 0 15px #ffd700 !important;
        outline: none !important;
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #00d4ff, #008cff) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #008cff, #00d4ff) !important;
        box-shadow: 0 0 25px #00d4ff !important;
        transform: translateY(-2px) !important;
    }
    #particles-canvas {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        pointer-events: none;
    }
    </style>
    <canvas id="particles-canvas"></canvas>
    <script>
    (function(){
        const canvas = document.getElementById('particles-canvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        let particles = [];
        function resize(){ canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
        window.addEventListener('resize', resize);
        resize();
        for (let i = 0; i < 80; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                r: Math.random() * 2 + 1,
                dx: (Math.random() - 0.5) * 0.5,
                dy: (Math.random() - 0.5) * 0.5,
                alpha: Math.random() * 0.5 + 0.2
            });
        }
        function animate(){
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            particles.forEach(p => {
                p.x += p.dx;
                p.y += p.dy;
                if (p.x < 0 || p.x > canvas.width) p.dx *= -1;
                if (p.y < 0 || p.y > canvas.height) p.dy *= -1;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(0, 212, 255, ' + p.alpha + ')';
                ctx.fill();
            });
            requestAnimationFrame(animate);
        }
        animate();
    })();
    </script>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="login-container">
        <div class="title-3d">
            <span class="m1">M</span><span class="a1">A</span><span class="r1">R</span><span class="m2">M</span><span class="e1">E</span><span class="d1">D</span>
        </div>
        <div class="subtitle-cyan">Gestão em Saúde Pública</div>
        <div class="subtitle-blue">Luminárias - MG</div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<span class='field-label'>Usuário</span>", unsafe_allow_html=True)
        usuario = st.text_input("", key="user_login", label_visibility="collapsed")
        st.markdown("<span class='field-label'>Senha</span>", unsafe_allow_html=True)
        senha = st.text_input("", type="password", key="pass_login", label_visibility="collapsed")
        if st.button("Entrar", key="btn_login"):
            h = hashlib.sha256(senha.encode()).hexdigest()
            c = conn.cursor()
            c.execute("SELECT * FROM usuarios WHERE usuario=? AND senha_hash=?", (usuario, h))
            if c.fetchone():
                st.session_state.logged_in = True
                st.session_state.page = "Dashboard"
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
        st.markdown("</div>", unsafe_allow_html=True)


def global_css():
    st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #050510 0%, #0a0a20 50%, #02020a 100%); color: #ffffff; }
    .block-container { padding-top: 2rem; }
    h1, h2, h3 { color: #00d4ff; font-family: 'Orbitron', sans-serif; }
    .metric-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 10px 40px rgba(0,0,0,0.4);
    }
    .metric-card h3 { margin: 0; font-size: 1rem; color: #87cefa; }
    .metric-card p { margin: 10px 0 0; font-size: 1.6rem; font-weight: 700; color: #00d4ff; }
    .glass-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .stButton > button {
        background: linear-gradient(90deg, #00d4ff, #008cff) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    .stButton > button:hover {
        box-shadow: 0 0 20px #00d4ff !important;
    }
    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stDateInput > div > div > input, .stSelectbox > div > div > div {
        background: rgba(255, 255, 255, 0.12) !important;
        border: 1px solid rgba(0, 212, 255, 0.5) !important;
        color: #ffffff !important;
        border-radius: 8px !important;
    }
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)


def sidebar():
    menu_items = [
        "Dashboard", "Contas a Pagar", "Contas a Receber", "Empenhos",
        "Licitações", "Contratos", "Relatórios", "Trocar Senha", "Sair"
    ]
    st.sidebar.markdown("<h1 style="text-align:center; color:#00d4ff;'>MARMED</h1>", unsafe_allow_html=True)
    st.sidebar.markdown("<<p style='text-align:center; color:#87cefa;'>Luminárias - MG</p>", unsafe_allow_html=True)
    for item in menu_items:
        if st.sidebar.button(item, key=f"menu_{item}", use_container_width=True):
            if item == "Sair":
                st.session_state.logged_in = False
                st.session_state.page = "Dashboard"
                st.rerun()
            else:
                st.session_state.page = item
                st.session_state.edit_id = None
                st.session_state.edit_table = None
                st.rerun()


def totals():
    c = conn.cursor()
    total = 0.0
    for t in ["repasses_federal", "repasses_estadual", "recursos_municipal", "transferencias", "transposicoes"]:
        c.execute(f"SELECT COALESCE(SUM(valor),0) FROM {t}")
        total += c.fetchone()[0]
    federal = 1250000
    estadual = 890000
    municipal = 450000
    transferencia = 320000
    transposicao = 180000
    if total == 0:
        for t, v, d in [
            ("repasses_federal", federal, "Repasse Federal 2025"),
            ("repasses_estadual", estadual, "Repasse Estadual 2025"),
            ("recursos_municipal", municipal, "Recurso Municipal 2025"),
            ("transferencias", transferencia, "Transferência 2025"),
            ("transposicoes", transposicao, "Transposição 2025")
        ]:
            c.execute(f"INSERT INTO {t} (descricao, valor, data, programa) VALUES (?, ?, ?, ?)", (d, v, "2025-01-01", "Saúde"))
        conn.commit()
    c.execute("SELECT COALESCE(SUM(valor),0) FROM repasses_federal")
    federal = c.fetchone()[0] or 1250000
    c.execute("SELECT COALESCE(SUM(valor),0) FROM repasses_estadual")
    estadual = c.fetchone()[0] or 890000
    c.execute("SELECT COALESCE(SUM(valor),0) FROM recursos_municipal")
    municipal = c.fetchone()[0] or 450000
    c.execute("SELECT COALESCE(SUM(valor),0) FROM transferencias")
    transferencia = c.fetchone()[0] or 320000
    c.execute("SELECT COALESCE(SUM(valor),0) FROM transposicoes")
    transposicao = c.fetchone()[0] or 180000
    return {
        "REPASSE FEDERAL": federal,
        "REPASSE ESTADUAL": estadual,
        "RECURSO MUNICIPAL": municipal,
        "TRANSFERÊNCIA": transferencia,
        "TRANSPOSIÇÃO": transposicao
    }


def dashboard_page():
    st.title("Dashboard")
    values = totals()
    cols = st.columns(5)
    for col, (label, value) in zip(cols, values.items()):
        col.markdown(f"""
        <div class="metric-card">
            <h3>{label}</h3>
            <p>R$ {value:,.2f}</p>
        </div>
        """, unsafe_allow_html=True)

    c = conn.cursor()
    c.execute("SELECT status, SUM(valor) FROM contas_pagar GROUP BY status")
    rows_pagar = c.fetchall()
    c.execute("SELECT status, SUM(valor) FROM contas_receber GROUP BY status")
    rows_receber = c.fetchall()

    if not rows_pagar:
        rows_pagar = [("Pendente", 0)]
    if not rows_receber:
        rows_receber = [("Pendente", 0)]

    df_pagar = pd.DataFrame(rows_pagar, columns=["Status", "Valor"])
    df_receber = pd.DataFrame(rows_receber, columns=["Status", "Valor"])

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Contas a Pagar por Status")
        fig1 = px.pie(df_pagar, values="Valor", names="Status", color_discrete_sequence=["#00d4ff", "#008cff", "#ffd700", "#87cefa"], template="plotly_dark")
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Contas a Receber por Status")
        fig2 = px.pie(df_receber, values="Valor", names="Status", color_discrete_sequence=["#00d4ff", "#008cff", "#ffd700", "#87cefa"], template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


def crud_page(table, columns, labels, title, status_options=None):
    st.title(title)
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table}")
    rows = c.fetchall()
    df = pd.DataFrame(rows, columns=["id"] + columns)

    st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Cadastrar / Editar")
    with st.form(f"form_{table}"):
        inputs = {}
        colunas = st.columns(min(len(labels), 3))
        for i, (col, label) in enumerate(zip(columns, labels)):
            with colunas[i % 3]:
                st.markdown("<span class='field-label'>Senha</span>", unsafe_allow_html=True)
                if col in ["valor"]:
                    inputs[col] = st.number_input("", value=0.0, step=0.01, key=f"{table}_{col}", label_visibility="collapsed")
                elif "data" in col or "vencimento" in col or "inicio" in col or "fim" in col or "abertura" in col:
                    inputs[col] = st.date_input("", value=date.today(), key=f"{table}_{col}", label_visibility="collapsed").isoformat()
                elif col == "status" and status_options:
                    inputs[col] = st.selectbox("", status_options, key=f"{table}_{col}", label_visibility="collapsed")
                elif col in ["tipo", "modalidade", "fonte", "categoria", "origem", "destino", "programa"]:
                    inputs[col] = st.text_input("", key=f"{table}_{col}", label_visibility="collapsed")
                else:
                    inputs[col] = st.text_input("", key=f"{table}_{col}", label_visibility="collapsed")
        cols = st.columns(2)
        with cols[0]:
            submitted = st.form_submit_button("Salvar")
        with cols[1]:
            if st.session_state.edit_id and st.session_state.edit_table == table:
                cancel = st.form_submit_button("Cancelar Edição")
                if cancel:
                    st.session_state.edit_id = None
                    st.session_state.edit_table = None
                    st.rerun()

    if submitted:
        if st.session_state.edit_id and st.session_state.edit_table == table:
            sets = ", ".join([f"{col}=?" for col in columns])
            vals = list(inputs.values()) + [st.session_state.edit_id]
            c.execute(f"UPDATE {table} SET {sets} WHERE id=?", vals)
            st.success("Registro atualizado com sucesso!")
            st.session_state.edit_id = None
            st.session_state.edit_table = None
        else:
            cols_sql = ", ".join(columns)
            placeholders = ", ".join(["?"] * len(columns))
            c.execute(f"INSERT INTO {table} ({cols_sql}) VALUES ({placeholders})", list(inputs.values()))
            st.success("Registro salvo com sucesso!")
        conn.commit()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Registros")
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        cols = st.columns(len(df))
        for idx, row in df.iterrows():
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Editar", key=f"edit_{table}_{row['id']}"):
                    st.session_state.edit_id = row["id"]
                    st.session_state.edit_table = table
                    for col in columns:
                        if col in ["valor"]:
                            st.session_state[f"{table}_{col}"] = float(row[col])
                        elif col in ["vencimento", "data", "data_abertura", "inicio", "fim"]:
                            try:
                                st.session_state[f"{table}_{col}"] = datetime.strptime(row[col], "%Y-%m-%d").date()
                            except:
                                st.session_state[f"{table}_{col}"] = date.today()
                        else:
                            st.session_state[f"{table}_{col}"] = row[col]
                    st.rerun()
            with c2:
                if st.button("Excluir", key=f"del_{table}_{row['id']}"):
                    c.execute(f"DELETE FROM {table} WHERE id=?", (row["id"],))
                    conn.commit()
                    st.success("Registro excluído!")
                    st.rerun()
    else:
        st.info("Nenhum registro cadastrado.")
    st.markdown("</div>", unsafe_allow_html=True)


def contas_pagar_page():
    crud_page(
        "contas_pagar",
        ["descricao", "credor", "valor", "vencimento", "status", "categoria"],
        ["Descrição", "Credor", "Valor", "Vencimento", "Status", "Categoria"],
        "Contas a Pagar",
        status_options=["Pendente", "Pago", "Vencido", "Cancelado"]
    )


def contas_receber_page():
    crud_page(
        "contas_receber",
        ["descricao", "devedor", "valor", "vencimento", "status", "categoria"],
        ["Descrição", "Devedor", "Valor", "Vencimento", "Status", "Categoria"],
        "Contas a Receber",
        status_options=["Pendente", "Recebido", "Vencido", "Cancelado"]
    )


def empenhos_page():
    crud_page(
        "empenhos",
        ["numero", "descricao", "valor", "data", "fonte", "status"],
        ["Número", "Descrição", "Valor", "Data", "Fonte", "Status"],
        "Empenhos",
        status_options=["Ativo", "Anulado", "Liquidado", "Pago"]
    )


def licitacoes_page():
    crud_page(
        "licitacoes",
        ["numero", "objeto", "modalidade", "valor", "data_abertura", "status"],
        ["Número", "Objeto", "Modalidade", "Valor", "Data Abertura", "Status"],
        "Licitações",
        status_options=["Em Andamento", "Concluída", "Cancelada", "Adjudicada"]
    )


def contratos_page():
    crud_page(
        "contratos",
        ["numero", "contratado", "objeto", "valor", "inicio", "fim", "status"],
        ["Número", "Contratado", "Objeto", "Valor", "Início", "Fim", "Status"],
        "Contratos",
        status_options=["Vigente", "Encerrado", "Rescindido", "Renovado"]
    )


def relatorios_page():
    st.title("Relatórios")
    c = conn.cursor()
    tables = {
        "Contas a Pagar": "contas_pagar",
        "Contas a Receber": "contas_receber",
        "Empenhos": "empenhos",
        "Licitações": "licitacoes",
        "Contratos": "contratos"
    }
    st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
    selected = st.selectbox("Selecione o relatório", list(tables.keys()))
    t = tables[selected]
    c.execute(f"SELECT * FROM {t}")
    rows = c.fetchall()
    if rows:
        cols = [desc[0] for desc in c.description]
        df = pd.DataFrame(rows, columns=cols)
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, f"relatorio_{t}.csv", "text/csv")
    else:
        st.info("Nenhum dado disponível.")
    st.markdown("</div>", unsafe_allow_html=True)


def trocar_senha_page():
    st.title("Trocar Senha")
    st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<span class='field-label'>Senha</span>", unsafe_allow_html=True)
    atual = st.text_input("", type="password", key="senha_atual", label_visibility="collapsed")
    st.markdown("<span class='field-label'>Senha</span>", unsafe_allow_html=True)
    nova = st.text_input("", type="password", key="senha_nova", label_visibility="collapsed")
   st.markdown("<span class='field-label'>Senha</span>", unsafe_allow_html=True)
    confirma = st.text_input("", type="password", key="senha_confirma", label_visibility="collapsed")
    if st.button("Alterar Senha"):
        if nova != confirma:
            st.error("As senhas não conferem.")
        else:
            c = conn.cursor()
            h_atual = hashlib.sha256(atual.encode()).hexdigest()
            c.execute("SELECT * FROM usuarios WHERE usuario=? AND senha_hash=?", (DEFAULT_USER, h_atual))
            if not c.fetchone():
                st.error("Senha atual incorreta.")
            else:
                h_nova = hashlib.sha256(nova.encode()).hexdigest()
                c.execute("UPDATE usuarios SET senha_hash=? WHERE usuario=?", (h_nova, DEFAULT_USER))
                conn.commit()
                st.success("Senha alterada com sucesso!")
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        global_css()
        sidebar()
        page = st.session_state.page
        if page == "Dashboard":
            dashboard_page()
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


if __name__ == "__main__":
    main()
