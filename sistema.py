import streamlit as st
import sqlite3
import hashlib
import time
import random
import os
from datetime import datetime, timedelta

DB_PATH = "marmed.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        nome TEXT,
        created_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS pacientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cpf TEXT,
        telefone TEXT,
        email TEXT,
        data_nascimento TEXT,
        endereco TEXT,
        convenio TEXT,
        observacoes TEXT,
        created_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS medicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        crm TEXT,
        especialidade TEXT,
        telefone TEXT,
        email TEXT,
        created_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS consultas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER,
        medico_id INTEGER,
        data_hora TEXT,
        motivo TEXT,
        status TEXT,
        observacoes TEXT,
        created_at TEXT,
        FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
        FOREIGN KEY (medico_id) REFERENCES medicos(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS procedimentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        valor REAL,
        created_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS exames (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER,
        nome TEXT NOT NULL,
        resultado TEXT,
        data TEXT,
        medico_id INTEGER,
        created_at TEXT,
        FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
        FOREIGN KEY (medico_id) REFERENCES medicos(id)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS financeiro (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        descricao TEXT,
        valor REAL,
        data TEXT,
        categoria TEXT,
        created_at TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS usuarios_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        acao TEXT,
        data_hora TEXT
    )''')

    default_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    c.execute("SELECT id FROM usuarios WHERE username = ?", ("admin",))
    if not c.fetchone():
        c.execute('''INSERT INTO usuarios (username, password_hash, role, nome, created_at)
                     VALUES (?, ?, ?, ?, ?)''',
                  ("admin", default_hash, "administrador", "Administrador", now_str()))

    conn.commit()
    conn.close()


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, password_hash, role, nome FROM usuarios WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[1] == hash_password(password):
        return {"id": row[0], "username": username, "role": row[2], "nome": row[3]}
    return None


def log_action(username, acao):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO usuarios_log (username, acao, data_hora) VALUES (?, ?, ?)",
              (username, acao, now_str()))
    conn.commit()
    conn.close()


def change_password(username, current, new, confirm):
    if not current or not new or not confirm:
        return "Preencha todos os campos."
    if new != confirm:
        return "Nova senha e confirmacao nao coincidem."
    if len(new) < 6:
        return "Nova senha deve ter no minimo 6 caracteres."
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password_hash FROM usuarios WHERE username = ?", (username,))
    row = c.fetchone()
    if not row or row[0] != hash_password(current):
        conn.close()
        return "Senha atual incorreta."
    c.execute("UPDATE usuarios SET password_hash = ? WHERE username = ?",
              (hash_password(new), username))
    conn.commit()
    conn.close()
    return None


def format_currency(value):
    if value is None:
        value = 0.0
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def load_css():
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');

    html, body, .stApp {
        background: #050b14 !important;
        color: #e0f7ff !important;
        font-family: 'Orbitron', sans-serif;
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

    .glass-card {
        position: relative;
        z-index: 10;
        background: rgba(10, 20, 35, 0.75);
        border: 1px solid rgba(0, 212, 255, 0.25);
        border-radius: 20px;
        padding: 2.5rem;
        max-width: 480px;
        margin: 0 auto;
        box-shadow: 0 0 40px rgba(0, 212, 255, 0.15), inset 0 0 20px rgba(0, 212, 255, 0.05);
        backdrop-filter: blur(12px);
    }

    .title-3d {
        font-family: 'Orbitron', sans-serif;
        font-size: 3.5rem;
        font-weight: 900;
        text-align: center;
        color: #00d4ff;
        text-shadow: 0 0 20px rgba(0, 212, 255, 0.8), 0 0 40px rgba(0, 212, 255, 0.5);
        margin-bottom: 0.5rem;
    }

    .title-3d span {
        display: inline-block;
        animation: flyIn 1.2s ease-out forwards;
        opacity: 0;
        transform: translate3d(120px, -120px, 300px) rotateY(90deg);
    }

    .title-3d span:nth-child(1) { animation-delay: 0.0s; }
    .title-3d span:nth-child(2) { animation-delay: 0.1s; }
    .title-3d span:nth-child(3) { animation-delay: 0.2s; }
    .title-3d span:nth-child(4) { animation-delay: 0.3s; }
    .title-3d span:nth-child(5) { animation-delay: 0.4s; }
    .title-3d span:nth-child(6) { animation-delay: 0.5s; }

    @keyframes flyIn {
        0% {
            opacity: 0;
            transform: translate3d(120px, -120px, 300px) rotateY(90deg);
            text-shadow: 0 0 0 transparent;
        }
        60% {
            opacity: 1;
            transform: translate3d(-10px, 5px, -30px) rotateY(-10deg);
            text-shadow: 0 0 30px rgba(0, 212, 255, 1);
        }
        100% {
            opacity: 1;
            transform: translate3d(0, 0, 0) rotateY(0deg);
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.8), 0 0 40px rgba(0, 212, 255, 0.5);
        }
    }

    .subtitle-glow {
        text-align: center;
        font-size: 1.8rem;
        color: #a0eaff;
        text-shadow: 0 0 15px rgba(0, 212, 255, 0.6);
        margin-bottom: 2rem;
        letter-spacing: 2px;
    }

    .cyan-label {
        color: #00d4ff !important;
        font-weight: 700;
        text-shadow: 0 0 8px rgba(0, 212, 255, 0.8);
        font-size: 1rem;
        margin-bottom: 0.25rem;
    }

    .access-text {
        text-align: center;
        color: #00d4ff;
        font-size: 0.95rem;
        margin-top: 1.5rem;
        text-shadow: 0 0 8px rgba(0, 212, 255, 0.5);
    }

    .stTextInput > div > div > input {
        background: rgba(0, 20, 40, 0.6) !important;
        color: #e0f7ff !important;
        border: 1px solid rgba(0, 212, 255, 0.4) !important;
        border-radius: 10px !important;
        box-shadow: 0 0 10px rgba(0, 212, 255, 0.1) inset !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #00d4ff !important;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.3) !important;
    }

    .stButton > button {
        background: linear-gradient(90deg, #00d4ff, #0066ff) !important;
        color: #050b14 !important;
        font-weight: 900 !important;
        border: none !important;
        border-radius: 12px !important;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.4) !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        transform: scale(1.03);
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.7) !important;
    }

    .metric-card {
        background: rgba(10, 25, 45, 0.8);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 15px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.1);
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 900;
        color: #00d4ff;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.6);
    }

    .metric-label {
        font-size: 0.95rem;
        color: #a0eaff;
        margin-top: 0.3rem;
    }

    .sidebar-title {
        font-family: 'Orbitron', sans-serif;
        font-weight: 900;
        text-shadow: 0 0 15px rgba(0, 212, 255, 0.6);
    }

    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #e0f7ff !important;
    }

    .stDataFrame, .stTable {
        background: rgba(10, 25, 45, 0.6) !important;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def particles_html():
    return """
    <canvas id="particles-canvas"></canvas>
    <script>
    const canvas = document.getElementById('particles-canvas');
    const ctx = canvas.getContext('2d');
    let particles = [];
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
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
    function animate() {
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
    </script>
    """


def login_page():
    load_css()
    st.markdown(particles_html(), unsafe_allow_html=True)

    st.markdown("<<div style='height:10vh;'></div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="glass-card">'
        '<div class="title-3d">'
        '<span>M</span><span>A</span><span>R</span><span>M</span><span>E</span><span>D</span>'
        '</div>'
        '<div class="subtitle-glow">SISTEMA INTEGRADO DE GESTAO</div>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("<<div style='height:2vh;'></div>", unsafe_allow_html=True)

    with st.container():
        st.markdown(
            '<div class="glass-card">',
            unsafe_allow_html=True
        )

        st.markdown('<div class="cyan-label">Usuario</div>', unsafe_allow_html=True)
        username = st.text_input("", key="login_user", label_visibility="collapsed")

        st.markdown('<div class="cyan-label">Senha</div>', unsafe_allow_html=True)
        password = st.text_input("", type="password", key="login_pass", label_visibility="collapsed")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.button("ENTRAR", use_container_width=True, key="login_btn")

        if submitted:
            user = verify_user(username, password)
            if user:
                st.session_state["user"] = user
                st.session_state["authenticated"] = True
                st.session_state["page"] = "Dashboard"
                log_action(username, "Login realizado")
                st.rerun()
            else:
                st.error("Usuario ou senha invalidos.")

        st.markdown('<div class="access-text">Acesso</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


def sidebar():
    st.sidebar.markdown('<h1 style="text-align:center; color:#00d4ff;">MARMED</h1>', unsafe_allow_html=True)
    st.sidebar.markdown(f"<<p style='text-align:center;'>Usuario: {st.session_state['user']['nome']}</p>", unsafe_allow_html=True)

    menu = [
        "Dashboard",
        "Pacientes",
        "Medicos",
        "Consultas",
        "Procedimentos",
        "Exames",
        "Financeiro",
        "Usuarios",
        "Trocar Senha",
        "Sair"
    ]
    choice = st.sidebar.radio("Navegacao", menu, label_visibility="collapsed")
    return choice


def count_rows(table):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"SELECT COUNT(*) FROM {table}")
    result = c.fetchone()[0]
    conn.close()
    return result


def dashboard_page():
    st.markdown("<<h1 style='color:#00d4ff;'>Dashboard</h1>", unsafe_allow_html=True)

    cols = st.columns(4)
    metrics = [
        ("Pacientes", count_rows("pacientes")),
        ("Medicos", count_rows("medicos")),
        ("Consultas", count_rows("consultas")),
        ("Exames", count_rows("exames")),
    ]
    for col, (label, value) in zip(cols, metrics):
        col.markdown(
            f'<div class="metric-card"><div class="metric-value">{value}</div><div class="metric-label">{label}</div></div>',
            unsafe_allow_html=True
        )

    st.markdown("<<div style='height:20px;'></div>", unsafe_allow_html=True)

    cols2 = st.columns(4)
    metrics2 = [
        ("Procedimentos", count_rows("procedimentos")),
        ("Usuarios", count_rows("usuarios")),
        ("Financeiro", count_rows("financeiro")),
    ]
    for col, (label, value) in zip(cols2, metrics2):
        col.markdown(
            f'<div class="metric-card"><div class="metric-value">{value}</div><div class="metric-label">{label}</div></div>',
            unsafe_allow_html=True
        )

    st.markdown("<<div style='height:30px;'></div>", unsafe_allow_html=True)
    st.markdown("<<h3 style='color:#00d4ff;'>Acoes Recentes</h3>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, acao, data_hora FROM usuarios_log ORDER BY id DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    if rows:
        st.table({"Usuario": [r[0] for r in rows], "Acao": [r[1] for r in rows], "Data/Hora": [r[2] for r in rows]})
    else:
        st.info("Nenhuma acao registrada.")


def generic_crud_page(title, table, fields, list_columns, order_by="id"):
    st.markdown(f"<<h1 style='color:#00d4ff;'>{title}</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Listar", "Adicionar", "Editar/Excluir"])

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"SELECT {', '.join(list_columns)} FROM {table} ORDER BY {order_by} DESC")
    rows = c.fetchall()
    conn.close()

    with tab1:
        if rows:
            st.table({col: [r[i] for r in rows] for i, col in enumerate(list_columns)})
        else:
            st.info("Nenhum registro encontrado.")

    with tab2:
        with st.form(f"add_{table}"):
            values = {}
            for field in fields:
                if field["type"] == "text":
                    values[field["name"]] = st.text_input(field["label"])
                elif field["type"] == "number":
                    values[field["name"]] = st.number_input(field["label"], min_value=0.0, step=0.01)
                elif field["type"] == "date":
                    values[field["name"]] = st.date_input(field["label"]).strftime("%Y-%m-%d")
                elif field["type"] == "datetime":
                    values[field["name"]] = st.text_input(field["label"], value=now_str())
                elif field["type"] == "select":
                    values[field["name"]] = st.selectbox(field["label"], field["options"])
                elif field["type"] == "textarea":
                    values[field["name"]] = st.text_area(field["label"])
            submitted = st.form_submit_button("Salvar")
            if submitted:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                cols = [f"{k}" for k in values.keys()] + ["created_at"]
                placeholders = ["?"] * len(cols)
                c.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(placeholders)})",
                          list(values.values()) + [now_str()])
                conn.commit()
                conn.close()
                log_action(st.session_state["user"]["username"], f"Adicionou {title}")
                st.success("Registro salvo com sucesso!")
                st.rerun()

    with tab3:
        if not rows:
            st.info("Nenhum registro para editar ou excluir.")
            return

        selected_id = st.selectbox("Selecione o registro", [r[0] for r in rows], format_func=lambda x: f"ID {x}")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(f"SELECT * FROM {table} WHERE id = ?", (selected_id,))
        record = c.fetchone()
        col_names = [desc[0] for desc in c.description]
        conn.close()

        record_dict = dict(zip(col_names, record))

        with st.form(f"edit_{table}"):
            updated = {}
            for field in fields:
                current = record_dict.get(field["name"], "")
                if field["type"] == "text":
                    updated[field["name"]] = st.text_input(field["label"], value=str(current) if current else "")
                elif field["type"] == "number":
                    updated[field["name"]] = st.number_input(field["label"], value=float(current) if current else 0.0, step=0.01)
                elif field["type"] == "date":
                    updated[field["name"]] = st.text_input(field["label"], value=str(current) if current else "")
                elif field["type"] == "datetime":
                    updated[field["name"]] = st.text_input(field["label"], value=str(current) if current else now_str())
                elif field["type"] == "select":
                    updated[field["name"]] = st.selectbox(field["label"], field["options"], index=field["options"].index(current) if current in field["options"] else 0)
                elif field["type"] == "textarea":
                    updated[field["name"]] = st.text_area(field["label"], value=str(current) if current else "")

            col_save, col_delete = st.columns(2)
            with col_save:
                save = st.form_submit_button("Atualizar")
            with col_delete:
                delete = st.form_submit_button("Excluir")

            if save:
                set_clause = ", ".join([f"{k} = ?" for k in updated.keys()])
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute(f"UPDATE {table} SET {set_clause} WHERE id = ?", list(updated.values()) + [selected_id])
                conn.commit()
                conn.close()
                log_action(st.session_state["user"]["username"], f"Editou {title}")
                st.success("Registro atualizado!")
                st.rerun()

            if delete:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute(f"DELETE FROM {table} WHERE id = ?", (selected_id,))
                conn.commit()
                conn.close()
                log_action(st.session_state["user"]["username"], f"Excluiu {title}")
                st.success("Registro excluido!")
                st.rerun()


def pacientes_page():
    fields = [
        {"name": "nome", "label": "Nome", "type": "text"},
        {"name": "cpf", "label": "CPF", "type": "text"},
        {"name": "telefone", "label": "Telefone", "type": "text"},
        {"name": "email", "label": "Email", "type": "text"},
        {"name": "data_nascimento", "label": "Data de Nascimento", "type": "date"},
        {"name": "endereco", "label": "Endereco", "type": "text"},
        {"name": "convenio", "label": "Convenio", "type": "text"},
        {"name": "observacoes", "label": "Observacoes", "type": "textarea"},
    ]
    generic_crud_page("Pacientes", "pacientes", fields, ["id", "nome", "cpf", "telefone"])


def medicos_page():
    fields = [
        {"name": "nome", "label": "Nome", "type": "text"},
        {"name": "crm", "label": "CRM", "type": "text"},
        {"name": "especialidade", "label": "Especialidade", "type": "text"},
        {"name": "telefone", "label": "Telefone", "type": "text"},
        {"name": "email", "label": "Email", "type": "text"},
    ]
    generic_crud_page("Medicos", "medicos", fields, ["id", "nome", "crm", "especialidade"])


def get_select_options(table, id_col="id", label_col="nome"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f"SELECT {id_col}, {label_col} FROM {table}")
    rows = c.fetchall()
    conn.close()
    return {f"{r[1]} (ID {r[0]})": r[0] for r in rows}


def consultas_page():
    st.markdown("<<h1 style='color:#00d4ff;'>Consultas</h1>", unsafe_allow_html=True)

    pacientes = get_select_options("pacientes")
    medicos = get_select_options("medicos")

    if not pacientes or not medicos:
        st.warning("Cadastre pacientes e medicos antes de agendar consultas.")
        return

    tab1, tab2, tab3 = st.tabs(["Listar", "Adicionar", "Editar/Excluir"])

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT c.id, p.nome, m.nome, c.data_hora, c.status
                 FROM consultas c
                 JOIN pacientes p ON c.paciente_id = p.id
                 JOIN medicos m ON c.medico_id = m.id
                 ORDER BY c.id DESC''')
    rows = c.fetchall()
    conn.close()

    with tab1:
        if rows:
            st.table({"ID": [r[0] for r in rows], "Paciente": [r[1] for r in rows],
                      "Medico": [r[2] for r in rows], "Data/Hora": [r[3] for r in rows], "Status": [r[4] for r in rows]})
        else:
            st.info("Nenhuma consulta encontrada.")

    with tab2:
        with st.form("add_consulta"):
            paciente_label = st.selectbox("Paciente", list(pacientes.keys()))
            medico_label = st.selectbox("Medico", list(medicos.keys()))
            data_hora = st.text_input("Data e Hora", value=now_str())
            motivo = st.text_input("Motivo")
            status = st.selectbox("Status", ["Agendada", "Confirmada", "Cancelada", "Realizada"])
            observacoes = st.text_area("Observacoes")
            submitted = st.form_submit_button("Salvar")
            if submitted:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('''INSERT INTO consultas (paciente_id, medico_id, data_hora, motivo, status, observacoes, created_at)
                             VALUES (?, ?, ?, ?, ?, ?, ?)''',
                          (pacientes[paciente_label], medicos[medico_label], data_hora, motivo, status, observacoes, now_str()))
                conn.commit()
                conn.close()
                log_action(st.session_state["user"]["username"], "Adicionou consulta")
                st.success("Consulta salva!")
                st.rerun()

    with tab3:
        if not rows:
            st.info("Nenhuma consulta para editar.")
            return

        selected_id = st.selectbox("Selecione a consulta", [r[0] for r in rows], format_func=lambda x: f"Consulta ID {x}")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM consultas WHERE id = ?", (selected_id,))
        record = c.fetchone()
        col_names = [desc[0] for desc in c.description]
        conn.close()
        record_dict = dict(zip(col_names, record))

        with st.form("edit_consulta"):
            paciente_label = st.selectbox("Paciente", list(pacientes.keys()),
                                          index=list(pacientes.values()).index(record_dict["paciente_id"]))
            medico_label = st.selectbox("Medico", list(medicos.keys()),
                                        index=list(medicos.values()).index(record_dict["medico_id"]))
            data_hora = st.text_input("Data e Hora", value=record_dict["data_hora"])
            motivo = st.text_input("Motivo", value=record_dict["motivo"] or "")
            status = st.selectbox("Status", ["Agendada", "Confirmada", "Cancelada", "Realizada"],
                                  index=["Agendada", "Confirmada", "Cancelada", "Realizada"].index(record_dict["status"]) if record_dict["status"] in ["Agendada", "Confirmada", "Cancelada", "Realizada"] else 0)
            observacoes = st.text_area("Observacoes", value=record_dict["observacoes"] or "")

            col_save, col_delete = st.columns(2)
            with col_save:
                save = st.form_submit_button("Atualizar")
            with col_delete:
                delete = st.form_submit_button("Excluir")

            if save:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('''UPDATE consultas SET paciente_id=?, medico_id=?, data_hora=?, motivo=?, status=?, observacoes=?
                             WHERE id=?''',
                          (pacientes[paciente_label], medicos[medico_label], data_hora, motivo, status, observacoes, selected_id))
                conn.commit()
                conn.close()
                log_action(st.session_state["user"]["username"], "Editou consulta")
                st.success("Consulta atualizada!")
                st.rerun()

            if delete:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("DELETE FROM consultas WHERE id = ?", (selected_id,))
                conn.commit()
                conn.close()
                log_action(st.session_state["user"]["username"], "Excluiu consulta")
                st.success("Consulta excluida!")
                st.rerun()


def procedimentos_page():
    fields = [
        {"name": "nome", "label": "Nome", "type": "text"},
        {"name": "descricao", "label": "Descricao", "type": "textarea"},
        {"name": "valor", "label": "Valor", "type": "number"},
    ]
    generic_crud_page("Procedimentos", "procedimentos", fields, ["id", "nome", "valor"])


def exames_page():
    st.markdown("<<h1 style='color:#00d4ff;'>Exames</h1>", unsafe_allow_html=True)

    pacientes = get_select_options("pacientes")
    medicos = get_select_options("medicos")

    if not pacientes or not medicos:
        st.warning("Cadastre pacientes e medicos antes de registrar exames.")
        return

    tab1, tab2, tab3 = st.tabs(["Listar", "Adicionar", "Editar/Excluir"])

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT e.id, p.nome, e.nome, e.resultado, e.data, m.nome
                 FROM exames e
                 JOIN pacientes p ON e.paciente_id = p.id
                 JOIN medicos m ON e.medico_id = m.id
                 ORDER BY e.id DESC''')
    rows = c.fetchall()
    conn.close()

    with tab1:
        if rows:
            st.table({"ID": [r[0] for r in rows], "Paciente": [r[1] for r in rows],
                      "Exame": [r[2] for r in rows], "Resultado": [r[3] for r in rows],
                      "Data": [r[4] for r in rows], "Medico": [r[5] for r in rows]})
        else:
            st.info("Nenhum exame encontrado.")

    with tab2:
        with st.form("add_exame"):
            paciente_label = st.selectbox("Paciente", list(pacientes.keys()))
            nome = st.text_input("Nome do Exame")
            resultado = st.text_area("Resultado")
            data = st.text_input("Data", value=datetime.now().strftime("%Y-%m-%d"))
            medico_label = st.selectbox("Medico", list(medicos.keys()))
            submitted = st.form_submit_button("Salvar")
            if submitted:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('''INSERT INTO exames (paciente_id, nome, resultado, data, medico_id, created_at)
                             VALUES (?, ?, ?, ?, ?, ?)''',
                          (pacientes[paciente_label], nome, resultado, data, medicos[medico_label], now_str()))
                conn.commit()
                conn.close()
                log_action(st.session_state["user"]["username"], "Adicionou exame")
                st.success("Exame salvo!")
                st.rerun()

    with tab3:
        if not rows:
            st.info("Nenhum exame para editar.")
            return

        selected_id = st.selectbox("Selecione o exame", [r[0] for r in rows], format_func=lambda x: f"Exame ID {x}")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM exames WHERE id = ?", (selected_id,))
        record = c.fetchone()
        col_names = [desc[0] for desc in c.description]
        conn.close()
        record_dict = dict(zip(col_names, record))

        with st.form("edit_exame"):
            paciente_label = st.selectbox("Paciente", list(pacientes.keys()),
                                          index=list(pacientes.values()).index(record_dict["paciente_id"]))
            nome = st.text_input("Nome do Exame", value=record_dict["nome"])
            resultado = st.text_area("Resultado", value=record_dict["resultado"] or "")
            data = st.text_input("Data", value=record_dict["data"] or "")
            medico_label = st.selectbox("Medico", list(medicos.keys()),
                                        index=list(medicos.values()).index(record_dict["medico_id"]))

            col_save, col_delete = st.columns(2)
            with col_save:
                save = st.form_submit_button("Atualizar")
            with col_delete:
                delete = st.form_submit_button("Excluir")

            if save:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('''UPDATE exames SET paciente_id=?, nome=?, resultado=?, data=?, medico_id=? WHERE id=?''',
                          (pacientes[paciente_label], nome, resultado, data, medicos[medico_label], selected_id))
                conn.commit()
                conn.close()
                log_action(st.session_state["user"]["username"], "Editou exame")
                st.success("Exame atualizado!")
                st.rerun()

            if delete:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("DELETE FROM exames WHERE id = ?", (selected_id,))
                conn.commit()
                conn.close()
                log_action(st.session_state["user"]["username"], "Excluiu exame")
                st.success("Exame excluido!")
                st.rerun()


def financeiro_page():
    st.markdown("<<h1 style='color:#00d4ff;'>Financeiro</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Listar", "Adicionar", "Editar/Excluir"])

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, tipo, descricao, valor, data, categoria FROM financeiro ORDER BY id DESC")
    rows = c.fetchall()
    c.execute("SELECT SUM(valor) FROM financeiro WHERE tipo = 'Receita'")
    receitas = c.fetchone()[0] or 0.0
    c.execute("SELECT SUM(valor) FROM financeiro WHERE tipo = 'Despesa'")
    despesas = c.fetchone()[0] or 0.0
    conn.close()

    saldo = receitas - despesas

    cols = st.columns(3)
    cols[0].markdown(f'<div class="metric-card"><div class="metric-value">{format_currency(receitas)}</div><div class="metric-label">Receitas</div></div>', unsafe_allow_html=True)
    cols[1].markdown(f'<div class="metric-card"><div class="metric-value">{format_currency(despesas)}</div><div class="metric-label">Despesas</div></div>', unsafe_allow_html=True)
    cols[2].markdown(f'<div class="metric-card"><div class="metric-value">{format_currency(saldo)}</div><div class="metric-label">Saldo</div></div>', unsafe_allow_html=True)

    st.markdown("<<div style='height:20px;'></div>", unsafe_allow_html=True)

    with tab1:
        if rows:
            st.table({"ID": [r[0] for r in rows], "Tipo": [r[1] for r in rows], "Descricao": [r[2] for r in rows],
                      "Valor": [format_currency(r[3]) for r in rows], "Data": [r[4] for r in rows], "Categoria": [r[5] for r in rows]})
        else:
            st.info("Nenhum lancamento financeiro.")

    with tab2:
        with st.form("add_financeiro"):
            tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
            descricao = st.text_input("Descricao")
            valor = st.number_input("Valor", min_value=0.0, step=0.01)
            data = st.text_input("Data", value=datetime.now().strftime("%Y-%m-%d"))
            categoria = st.text_input("Categoria")
            submitted = st.form_submit_button("Salvar")
            if submitted:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('''INSERT INTO financeiro (tipo, descricao, valor, data, categoria, created_at)
                             VALUES (?, ?, ?, ?, ?, ?)''',
                          (tipo, descricao, valor, data, categoria, now_str()))
                conn.commit()
                conn.close()
                log_action(st.session_state["user"]["username"], "Adicionou lancamento financeiro")
                st.success("Lancamento salvo!")
                st.rerun()

    with tab3:
        if not rows:
            st.info("Nenhum lancamento para editar.")
            return

        selected_id = st.selectbox("Selecione o lancamento", [r[0] for r in rows], format_func=lambda x: f"Lancamento ID {x}")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM financeiro WHERE id = ?", (selected_id,))
        record = c.fetchone()
        col_names = [desc[0] for desc in c.description]
        conn.close()
        record_dict = dict(zip(col_names, record))

        with st.form("edit_financeiro"):
            tipo = st.selectbox("Tipo", ["Receita", "Despesa"],
                                index=["Receita", "Despesa"].index(record_dict["tipo"]) if record_dict["tipo"] in ["Receita", "Despesa"] else 0)
            descricao = st.text_input("Descricao", value=record_dict["descricao"] or "")
            valor = st.number_input("Valor", value=float(record_dict["valor"]) if record_dict["valor"] else 0.0, step=0.01)
            data = st.text_input("Data", value=record_dict["data"] or "")
            categoria = st.text_input("Categoria", value=record_dict["categoria"] or "")

            col_save, col_delete = st.columns(2)
            with col_save:
                save = st.form_submit_button("Atualizar")
            with col_delete:
                delete = st.form_submit_button("Excluir")

            if save:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('''UPDATE financeiro SET tipo=?, descricao=?, valor=?, data=?, categoria=? WHERE id=?''',
                          (tipo, descricao, valor, data, categoria, selected_id))
                conn.commit()
                conn.close()
                log_action(st.session_state["user"]["username"], "Editou lancamento financeiro")
                st.success("Lancamento atualizado!")
                st.rerun()

            if delete:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("DELETE FROM financeiro WHERE id = ?", (selected_id,))
                conn.commit()
                conn.close()
                log_action(st.session_state["user"]["username"], "Excluiu lancamento financeiro")
                st.success("Lancamento excluido!")
                st.rerun()


def usuarios_page():
    st.markdown("<<h1 style='color:#00d4ff;'>Usuarios</h1>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Listar", "Adicionar", "Editar/Excluir"])

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, username, role, nome, created_at FROM usuarios ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    with tab1:
        if rows:
            st.table({"ID": [r[0] for r in rows], "Usuario": [r[1] for r in rows], "Perfil": [r[2] for r in rows],
                      "Nome": [r[3] for r in rows], "Criado em": [r[4] for r in rows]})
        else:
            st.info("Nenhum usuario encontrado.")

    with tab2:
        with st.form("add_usuario"):
            username = st.text_input("Usuario")
            nome = st.text_input("Nome")
            role = st.selectbox("Perfil", ["administrador", "medico", "recepcionista", "financeiro"])
            password = st.text_input("Senha", type="password")
            confirm = st.text_input("Confirmar Senha", type="password")
            submitted = st.form_submit_button("Salvar")
            if submitted:
                if password != confirm:
                    st.error("Senhas nao coincidem.")
                elif len(password) < 6:
                    st.error("Senha deve ter no minimo 6 caracteres.")
                else:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    try:
                        c.execute('''INSERT INTO usuarios (username, password_hash, role, nome, created_at)
                                     VALUES (?, ?, ?, ?, ?)''',
                                  (username, hash_password(password), role, nome, now_str()))
                        conn.commit()
                        conn.close()
                        log_action(st.session_state["user"]["username"], "Adicionou usuario")
                        st.success("Usuario salvo!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Nome de usuario ja existe.")

    with tab3:
        if not rows:
            st.info("Nenhum usuario para editar.")
            return

        selected_id = st.selectbox("Selecione o usuario", [r[0] for r in rows], format_func=lambda x: f"Usuario ID {x}")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE id = ?", (selected_id,))
        record = c.fetchone()
        col_names = [desc[0] for desc in c.description]
        conn.close()
        record_dict = dict(zip(col_names, record))

        with st.form("edit_usuario"):
            username = st.text_input("Usuario", value=record_dict["username"])
            nome = st.text_input("Nome", value=record_dict["nome"] or "")
            role = st.selectbox("Perfil", ["administrador", "medico", "recepcionista", "financeiro"],
                                index=["administrador", "medico", "recepcionista", "financeiro"].index(record_dict["role"]) if record_dict["role"] in ["administrador", "medico", "recepcionista", "financeiro"] else 0)
            new_password = st.text_input("Nova Senha (deixe em branco para manter)", type="password")

            col_save, col_delete = st.columns(2)
            with col_save:
                save = st.form_submit_button("Atualizar")
            with col_delete:
                delete = st.form_submit_button("Excluir")

            if save:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                if new_password:
                    if len(new_password) < 6:
                        st.error("Nova senha deve ter no minimo 6 caracteres.")
                    else:
                        c.execute("UPDATE usuarios SET username=?, password_hash=?, role=?, nome=? WHERE id=?",
                                  (username, hash_password(new_password), role, nome, selected_id))
                        conn.commit()
                        conn.close()
                        log_action(st.session_state["user"]["username"], "Editou usuario")
                        st.success("Usuario atualizado!")
                        st.rerun()
                else:
                    c.execute("UPDATE usuarios SET username=?, role=?, nome=? WHERE id=?",
                              (username, role, nome, selected_id))
                    conn.commit()
                    conn.close()
                    log_action(st.session_state["user"]["username"], "Editou usuario")
                    st.success("Usuario atualizado!")
                    st.rerun()

            if delete:
                if selected_id == st.session_state["user"]["id"]:
                    st.error("Nao e possivel excluir o proprio usuario.")
                else:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("DELETE FROM usuarios WHERE id = ?", (selected_id,))
                    conn.commit()
                    conn.close()
                    log_action(st.session_state["user"]["username"], "Excluiu usuario")
                    st.success("Usuario excluido!")
                    st.rerun()


def trocar_senha_page():
    st.markdown("<<h1 style='color:#00d4ff;'>Trocar Senha</h1>", unsafe_allow_html=True)

    with st.form("change_password"):
        st.markdown('<div class="cyan-label">Senha Atual</div>', unsafe_allow_html=True)
        current = st.text_input("", type="password", key="current_pass", label_visibility="collapsed")

        st.markdown('<div class="cyan-label">Nova Senha</div>', unsafe_allow_html=True)
        new = st.text_input("", type="password", key="new_pass", label_visibility="collapsed")

        st.markdown('<div class="cyan-label">Confirmar Nova Senha</div>', unsafe_allow_html=True)
        confirm = st.text_input("", type="password", key="confirm_pass", label_visibility="collapsed")

        submitted = st.form_submit_button("Trocar Senha")
        if submitted:
            result = change_password(st.session_state["user"]["username"], current, new, confirm)
            if result:
                st.error(result)
            else:
                log_action(st.session_state["user"]["username"], "Trocou senha")
                st.success("Senha alterada com sucesso!")


def main():
    init_db()

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "page" not in st.session_state:
        st.session_state["page"] = "Login"

    if not st.session_state["authenticated"]:
        login_page()
    else:
        load_css()
        st.markdown(particles_html(), unsafe_allow_html=True)
        choice = sidebar()
        st.session_state["page"] = choice

        if choice == "Dashboard":
            dashboard_page()
        elif choice == "Pacientes":
            pacientes_page()
        elif choice == "Medicos":
            medicos_page()
        elif choice == "Consultas":
            consultas_page()
        elif choice == "Procedimentos":
            procedimentos_page()
        elif choice == "Exames":
            exames_page()
        elif choice == "Financeiro":
            financeiro_page()
        elif choice == "Usuarios":
            usuarios_page()
        elif choice == "Trocar Senha":
            trocar_senha_page()
        elif choice == "Sair":
            log_action(st.session_state["user"]["username"], "Logout")
            st.session_state["authenticated"] = False
            st.session_state["user"] = None
            st.session_state["page"] = "Login"
            st.rerun()


if __name__ == "__main__":
    main()
