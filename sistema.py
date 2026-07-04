import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, timedelta
import random
import time

st.set_page_config(
    page_title="MARMED",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def format_currency(value):
    if value is None:
        return "R$ 0,00"
    try:
        number = float(value)
        return f"R$ {number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect("marmed.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE,
            data_nascimento TEXT,
            telefone TEXT,
            email TEXT,
            endereco TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            crm TEXT UNIQUE,
            especialidade TEXT,
            telefone TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            medico_id INTEGER NOT NULL,
            data_hora TEXT NOT NULL,
            status TEXT DEFAULT 'Agendada',
            observacoes TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
            FOREIGN KEY (medico_id) REFERENCES medicos(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS financeiro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            tipo TEXT NOT NULL,
            valor REAL NOT NULL,
            data TEXT NOT NULL,
            categoria TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER NOT NULL,
            tipo_exame TEXT NOT NULL,
            data_solicitacao TEXT NOT NULL,
            data_resultado TEXT,
            resultado TEXT,
            status TEXT DEFAULT 'Pendente',
            FOREIGN KEY (paciente_id) REFERENCES pacientes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            principio_ativo TEXT,
            quantidade INTEGER DEFAULT 0,
            validade TEXT,
            fornecedor TEXT
        )
    """)

    default_user = "admin"
    default_pass = "Diretor2025#"
    default_hash = hashlib.sha256(default_pass.encode()).hexdigest()

    cursor.execute("SELECT id FROM users WHERE username = ?", (default_user,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (default_user, default_hash, "Diretor")
        )

    conn.commit()


init_database()


def verify_password(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute(
        "SELECT * FROM users WHERE username = ? AND password_hash = ?",
        (username, password_hash)
    )
    user = cursor.fetchone()
    return dict(user) if user else None


def update_password(username, new_password):
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = hashlib.sha256(new_password.encode()).hexdigest()
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE username = ?",
        (password_hash, username)
    )
    conn.commit()


def get_count(table):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    return cursor.fetchone()[0]


def get_total_financeiro(tipo="receita"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COALESCE(SUM(valor), 0) FROM financeiro WHERE tipo = ?",
        (tipo,)
    )
    return cursor.fetchone()[0]


def load_data(table, columns="*"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT {columns} FROM {table}")
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def insert_row(table, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?" for _ in data])
    cursor.execute(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
        tuple(data.values())
    )
    conn.commit()
    return cursor.lastrowid


def update_row(table, id_value, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    sets = ", ".join([f"{k} = ?" for k in data.keys()])
    cursor.execute(
        f"UPDATE {table} SET {sets} WHERE id = ?",
        tuple(list(data.values()) + [id_value])
    )
    conn.commit()


def delete_row(table, id_value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table} WHERE id = ?", (id_value,))
    conn.commit()


def login_page():
    st.markdown("""
        <style>
        .main {
            background: radial-gradient(circle at center, #0a0a1a 0%, #000000 100%);
            color: #e0f7ff;
        }
        .title-3d {
            font-size: 5.5rem;
            font-weight: 900;
            text-align: center;
            color: #00d4ff;
            text-shadow: 0 0 20px #00d4ff, 0 0 40px #0099cc, 0 0 80px #006699;
            letter-spacing: 0.5rem;
            animation: flyIn 2s ease-out forwards;
            margin-bottom: 1rem;
        }
        .subtitle {
            font-size: 2.2rem;
            text-align: center;
            color: #b3f0ff;
            text-shadow: 0 0 15px #00d4ff;
            margin-bottom: 3rem;
            letter-spacing: 0.3rem;
        }
        .glass-card {
            background: rgba(0, 20, 40, 0.6);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 25px;
            padding: 2.5rem;
            box-shadow: 0 0 50px rgba(0, 212, 255, 0.2), inset 0 0 30px rgba(0, 212, 255, 0.05);
            max-width: 450px;
            margin: 0 auto;
        }
        .login-label {
            color: #00d4ff;
            font-size: 1.1rem;
            font-weight: 600;
            text-shadow: 0 0 10px #00d4ff;
            margin-bottom: 0.5rem;
        }
        .login-input {
            background: rgba(0, 10, 20, 0.7);
            border: 1px solid #00d4ff;
            border-radius: 12px;
            color: #ffffff;
            padding: 0.8rem;
            font-size: 1rem;
            width: 100%;
        }
        .login-input:focus {
            outline: none;
            box-shadow: 0 0 15px #00d4ff;
        }
        .login-button {
            background: linear-gradient(135deg, #00d4ff, #006699);
            color: white;
            font-size: 1.2rem;
            font-weight: 700;
            padding: 0.9rem 2rem;
            border: none;
            border-radius: 15px;
            cursor: pointer;
            width: 100%;
            margin-top: 1.5rem;
            box-shadow: 0 0 25px rgba(0, 212, 255, 0.5);
            transition: all 0.3s ease;
        }
        .login-button:hover {
            transform: scale(1.05);
            box-shadow: 0 0 40px rgba(0, 212, 255, 0.8);
        }
        .acesso-text {
            text-align: center;
            color: #66d9ff;
            font-size: 0.95rem;
            margin-top: 1.5rem;
            letter-spacing: 0.1rem;
        }
        @keyframes flyIn {
            0% { opacity: 0; transform: translateY(-100px) scale(2); letter-spacing: 2rem; }
            100% { opacity: 1; transform: translateY(0) scale(1); letter-spacing: 0.5rem; }
        }
        .particle {
            position: fixed;
            border-radius: 50%;
            background: rgba(0, 212, 255, 0.6);
            animation: float 8s infinite ease-in-out;
            pointer-events: none;
            z-index: 0;
        }
        @keyframes float {
            0%, 100% { transform: translateY(0) translateX(0); opacity: 0.3; }
            50% { transform: translateY(-100px) translateX(50px); opacity: 0.8; }
        }
        </style>
    """, unsafe_allow_html=True)

    particles = ""
    for i in range(50):
        size = random.randint(2, 6)
        left = random.randint(0, 100)
        top = random.randint(0, 100)
        delay = random.uniform(0, 8)
        duration = random.uniform(6, 12)
        particles += f'<div class="particle" style="width:{size}px;height:{size}px;left:{left}vw;top:{top}vh;animation-delay:{delay}s;animation-duration:{duration}s;"></div>'
    st.markdown(particles, unsafe_allow_html=True)

    st.markdown("<<h1 class='title-3d'>MARMED</h1>", unsafe_allow_html=True)
    st.markdown("<<p class='subtitle'>SISTEMA INTEGRADO DE GESTAO</p>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<<p class='login-label'>Usuario</p>", unsafe_allow_html=True)
        username = st.text_input("Usuario", label_visibility="collapsed", key="login_user")
        st.markdown("<<p class='login-label'>Senha</p>", unsafe_allow_html=True)
        password = st.text_input("Senha", type="password", label_visibility="collapsed", key="login_pass")

        if st.button("Entrar", key="login_btn", use_container_width=True):
            user = verify_password(username, password)
            if user:
                st.session_state["authenticated"] = True
                st.session_state["user"] = user
                st.session_state["page"] = "Dashboard"
                st.rerun()
            else:
                st.error("Usuario ou senha incorretos!")

        st.markdown("<<p class='acesso-text'>ACESSO</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


def dashboard():
    st.markdown("<<h1 style='text-align:center; color:#00d4ff; text-shadow: 0 0 20px #00d4ff;'>Dashboard MARMED</h1>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
            <div style='background: rgba(0,20,40,0.6); border:1px solid #00d4ff; border-radius:15px; padding:1.5rem; text-align:center; box-shadow: 0 0 20px rgba(0,212,255,0.3);'>
                <h3 style='color:#00d4ff; margin:0;'>Pacientes</h3>
                <p style='font-size:2.5rem; font-weight:900; color:#ffffff; margin:0;'>{get_count('pacientes')}</p>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div style='background: rgba(0,20,40,0.6); border:1px solid #00d4ff; border-radius:15px; padding:1.5rem; text-align:center; box-shadow: 0 0 20px rgba(0,212,255,0.3);'>
                <h3 style='color:#00d4ff; margin:0;'>Medicos</h3>
                <p style='font-size:2.5rem; font-weight:900; color:#ffffff; margin:0;'>{get_count('medicos')}</p>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div style='background: rgba(0,20,40,0.6); border:1px solid #00d4ff; border-radius:15px; padding:1.5rem; text-align:center; box-shadow: 0 0 20px rgba(0,212,255,0.3);'>
                <h3 style='color:#00d4ff; margin:0;'>Consultas</h3>
                <p style='font-size:2.5rem; font-weight:900; color:#ffffff; margin:0;'>{get_count('consultas')}</p>
            </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
            <div style='background: rgba(0,20,40,0.6); border:1px solid #00d4ff; border-radius:15px; padding:1.5rem; text-align:center; box-shadow: 0 0 20px rgba(0,212,255,0.3);'>
                <h3 style='color:#00d4ff; margin:0;'>Receitas</h3>
                <p style='font-size:2.5rem; font-weight:900; color:#ffffff; margin:0;'>{format_currency(get_total_financeiro('receita'))}</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<<hr style='border-color:#00d4ff;'>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<<h3 style='color:#00d4ff;'>Ultimos Pacientes</h3>", unsafe_allow_html=True)
        pacientes = load_data("pacientes", "id, nome, telefone")
        if pacientes:
            st.dataframe(pd.DataFrame(pacientes).tail(5), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum paciente cadastrado.")
    with col2:
        st.markdown("<<h3 style='color:#00d4ff;'>Consultas de Hoje</h3>", unsafe_allow_html=True)
        hoje = datetime.now().strftime("%Y-%m-%d")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, p.nome as paciente, m.nome as medico, c.data_hora, c.status
            FROM consultas c
            JOIN pacientes p ON c.paciente_id = p.id
            JOIN medicos m ON c.medico_id = m.id
            WHERE c.data_hora LIKE ?
        """, (f"{hoje}%",))
        consultas_hoje = [dict(row) for row in cursor.fetchall()]
        if consultas_hoje:
            st.dataframe(pd.DataFrame(consultas_hoje), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma consulta agendada para hoje.")


def crud_page(title, table, fields, list_columns):
    st.markdown(f"<<h1 style='text-align:center; color:#00d4ff; text-shadow: 0 0 20px #00d4ff;'>{title}</h1>", unsafe_allow_html=True)

    tab_list, tab_create, tab_edit = st.tabs(["Listar", "Cadastrar", "Editar"])

    with tab_list:
        data = load_data(table)
        if data:
            df = pd.DataFrame(data)
            if list_columns:
                df = df[[col for col in list_columns if col in df.columns]]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro encontrado.")

    with tab_create:
        with st.form(f"form_create_{table}"):
            values = {}
            for field in fields:
                key, label, ftype = field
                if ftype == "text":
                    values[key] = st.text_input(label)
                elif ftype == "date":
                    values[key] = st.date_input(label, datetime.now()).strftime("%Y-%m-%d")
                elif ftype == "number":
                    values[key] = st.number_input(label, value=0, step=1)
                elif ftype == "select":
                    options = field[3]
                    values[key] = st.selectbox(label, options)
                elif ftype == "textarea":
                    values[key] = st.text_area(label)
            submitted = st.form_submit_button("Salvar")
            if submitted:
                insert_row(table, values)
                st.success("Registro cadastrado com sucesso!")
                time.sleep(1)
                st.rerun()

    with tab_edit:
        data = load_data(table, "id, nome")
        if not data:
            st.info("Nenhum registro para editar.")
            return

        registros = {f"{d['id']} - {d.get('nome', 'Item')}": d["id"] for d in data}
        selected = st.selectbox("Selecione o registro", list(registros.keys()))
        reg_id = registros[selected]

        registro = next((d for d in load_data(table) if d["id"] == reg_id), None)
        if not registro:
            return

        with st.form(f"form_edit_{table}"):
            values = {}
            for field in fields:
                key, label, ftype = field
                current = registro.get(key, "")
                if ftype == "text":
                    values[key] = st.text_input(label, value=current or "")
                elif ftype == "date":
                    try:
                        default = datetime.strptime(current, "%Y-%m-%d") if current else datetime.now()
                    except Exception:
                        default = datetime.now()
                    values[key] = st.date_input(label, default).strftime("%Y-%m-%d")
                elif ftype == "number":
                    values[key] = st.number_input(label, value=int(current) if current else 0, step=1)
                elif ftype == "select":
                    options = field[3]
                    values[key] = st.selectbox(label, options, index=options.index(current) if current in options else 0)
                elif ftype == "textarea":
                    values[key] = st.text_area(label, value=current or "")

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Atualizar"):
                    update_row(table, reg_id, values)
                    st.success("Registro atualizado!")
                    time.sleep(1)
                    st.rerun()
            with col2:
                if st.form_submit_button("Excluir"):
                    delete_row(table, reg_id)
                    st.warning("Registro excluido!")
                    time.sleep(1)
                    st.rerun()


def pacientes_page():
    fields = [
        ("nome", "Nome", "text"),
        ("cpf", "CPF", "text"),
        ("data_nascimento", "Data de Nascimento", "date"),
        ("telefone", "Telefone", "text"),
        ("email", "Email", "text"),
        ("endereco", "Endereco", "textarea")
    ]
    crud_page("Cadastro de Pacientes", "pacientes", fields, ["id", "nome", "cpf", "telefone", "email"])


def medicos_page():
    fields = [
        ("nome", "Nome", "text"),
        ("crm", "CRM", "text"),
        ("especialidade", "Especialidade", "text"),
        ("telefone", "Telefone", "text"),
        ("email", "Email", "text")
    ]
    crud_page("Cadastro de Medicos", "medicos", fields, ["id", "nome", "crm", "especialidade", "telefone"])


def consultas_page():
    st.markdown("<<h1 style='text-align:center; color:#00d4ff; text-shadow: 0 0 20px #00d4ff;'>Agenda de Consultas</h1>", unsafe_allow_html=True)

    tab_list, tab_create, tab_edit = st.tabs(["Listar", "Agendar", "Editar"])

    pacientes = load_data("pacientes", "id, nome")
    medicos = load_data("medicos", "id, nome")

    paciente_options = {p["nome"]: p["id"] for p in pacientes}
    medico_options = {m["nome"]: m["id"] for m in medicos}

    with tab_list:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, p.nome as paciente, m.nome as medico, c.data_hora, c.status, c.observacoes
            FROM consultas c
            JOIN pacientes p ON c.paciente_id = p.id
            JOIN medicos m ON c.medico_id = m.id
        """)
        rows = [dict(row) for row in cursor.fetchall()]
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma consulta agendada.")

    with tab_create:
        with st.form("form_create_consulta"):
            paciente_nome = st.selectbox("Paciente", list(paciente_options.keys()))
            medico_nome = st.selectbox("Medico", list(medico_options.keys()))
            data_consulta = st.date_input("Data", datetime.now())
            hora_consulta = st.time_input("Hora", datetime.strptime("09:00", "%H:%M"))
            status = st.selectbox("Status", ["Agendada", "Confirmada", "Concluida", "Cancelada"])
            observacoes = st.text_area("Observacoes")
            submitted = st.form_submit_button("Agendar")
            if submitted:
                data_hora = f"{data_consulta.strftime('%Y-%m-%d')} {hora_consulta.strftime('%H:%M')}"
                insert_row("consultas", {
                    "paciente_id": paciente_options[paciente_nome],
                    "medico_id": medico_options[medico_nome],
                    "data_hora": data_hora,
                    "status": status,
                    "observacoes": observacoes
                })
                st.success("Consulta agendada!")
                time.sleep(1)
                st.rerun()

    with tab_edit:
        consultas = load_data("consultas", "id, paciente_id, medico_id, data_hora, status")
        if not consultas:
            st.info("Nenhuma consulta para editar.")
            return
        options = {f"{c['id']} - {c['data_hora']}": c["id"] for c in consultas}
        selected = st.selectbox("Selecione a consulta", list(options.keys()))
        consulta_id = options[selected]
        consulta = next((c for c in load_data("consultas") if c["id"] == consulta_id), None)
        if not consulta:
            return

        with st.form("form_edit_consulta"):
            paciente_nome = st.selectbox("Paciente", list(paciente_options.keys()), index=list(paciente_options.values()).index(consulta["paciente_id"]))
            medico_nome = st.selectbox("Medico", list(medico_options.keys()), index=list(medico_options.values()).index(consulta["medico_id"]))
            try:
                dt = datetime.strptime(consulta["data_hora"], "%Y-%m-%d %H:%M")
            except Exception:
                dt = datetime.now()
            data_consulta = st.date_input("Data", dt)
            hora_consulta = st.time_input("Hora", dt)
            status = st.selectbox("Status", ["Agendada", "Confirmada", "Concluida", "Cancelada"], index=["Agendada", "Confirmada", "Concluida", "Cancelada"].index(consulta["status"]))
            observacoes = st.text_area("Observacoes", value=consulta.get("observacoes", ""))
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Atualizar"):
                    data_hora = f"{data_consulta.strftime('%Y-%m-%d')} {hora_consulta.strftime('%H:%M')}"
                    update_row("consultas", consulta_id, {
                        "paciente_id": paciente_options[paciente_nome],
                        "medico_id": medico_options[medico_nome],
                        "data_hora": data_hora,
                        "status": status,
                        "observacoes": observacoes
                    })
                    st.success("Consulta atualizada!")
                    time.sleep(1)
                    st.rerun()
            with col2:
                if st.form_submit_button("Excluir"):
                    delete_row("consultas", consulta_id)
                    st.warning("Consulta excluida!")
                    time.sleep(1)
                    st.rerun()


def financeiro_page():
    fields = [
        ("descricao", "Descricao", "text"),
        ("tipo", "Tipo", "select", ["receita", "despesa"]),
        ("valor", "Valor", "number"),
        ("data", "Data", "date"),
        ("categoria", "Categoria", "text")
    ]
    crud_page("Financeiro", "financeiro", fields, ["id", "descricao", "tipo", "valor", "data", "categoria"])

    st.markdown("<<hr style='border-color:#00d4ff;'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<<h3 style='color:#00d4ff;'>Total Receitas: {format_currency(get_total_financeiro('receita'))}</h3>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<<h3 style='color:#ff6b6b;'>Total Despesas: {format_currency(get_total_financeiro('despesa'))}</h3>", unsafe_allow_html=True)


def exames_page():
    st.markdown("<<h1 style='text-align:center; color:#00d4ff; text-shadow: 0 0 20px #00d4ff;'>Exames</h1>", unsafe_allow_html=True)
    pacientes = load_data("pacientes", "id, nome")
    paciente_options = {p["nome"]: p["id"] for p in pacientes}

    tab_list, tab_create, tab_edit = st.tabs(["Listar", "Solicitar", "Editar"])

    with tab_list:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id, p.nome as paciente, e.tipo_exame, e.data_solicitacao, e.data_resultado, e.status
            FROM exames e
            JOIN pacientes p ON e.paciente_id = p.id
        """)
        rows = [dict(row) for row in cursor.fetchall()]
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum exame registrado.")

    with tab_create:
        with st.form("form_create_exame"):
            paciente_nome = st.selectbox("Paciente", list(paciente_options.keys()))
            tipo_exame = st.text_input("Tipo de Exame")
            data_solicitacao = st.date_input("Data de Solicitacao", datetime.now()).strftime("%Y-%m-%d")
            submitted = st.form_submit_button("Solicitar")
            if submitted:
                insert_row("exames", {
                    "paciente_id": paciente_options[paciente_nome],
                    "tipo_exame": tipo_exame,
                    "data_solicitacao": data_solicitacao
                })
                st.success("Exame solicitado!")
                time.sleep(1)
                st.rerun()

    with tab_edit:
        exames = load_data("exames", "id, tipo_exame, data_solicitacao, status")
        if not exames:
            st.info("Nenhum exame para editar.")
            return
        options = {f"{e['id']} - {e['tipo_exame']} ({e['data_solicitacao']})": e["id"] for e in exames}
        selected = st.selectbox("Selecione o exame", list(options.keys()))
        exame_id = options[selected]
        exame = next((e for e in load_data("exames") if e["id"] == exame_id), None)
        if not exame:
            return

        with st.form("form_edit_exame"):
            paciente_nome = st.selectbox("Paciente", list(paciente_options.keys()), index=list(paciente_options.values()).index(exame["paciente_id"]))
            tipo_exame = st.text_input("Tipo de Exame", value=exame["tipo_exame"])
            data_solicitacao = st.date_input("Data de Solicitacao", datetime.strptime(exame["data_solicitacao"], "%Y-%m-%d") if exame["data_solicitacao"] else datetime.now()).strftime("%Y-%m-%d")
            data_resultado = st.date_input("Data do Resultado", datetime.strptime(exame["data_resultado"], "%Y-%m-%d") if exame.get("data_resultado") else datetime.now()).strftime("%Y-%m-%d")
            resultado = st.text_area("Resultado", value=exame.get("resultado", ""))
            status = st.selectbox("Status", ["Pendente", "Concluido", "Cancelado"], index=["Pendente", "Concluido", "Cancelado"].index(exame["status"]))
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Atualizar"):
                    update_row("exames", exame_id, {
                        "paciente_id": paciente_options[paciente_nome],
                        "tipo_exame": tipo_exame,
                        "data_solicitacao": data_solicitacao,
                        "data_resultado": data_resultado,
                        "resultado": resultado,
                        "status": status
                    })
                    st.success("Exame atualizado!")
                    time.sleep(1)
                    st.rerun()
            with col2:
                if st.form_submit_button("Excluir"):
                    delete_row("exames", exame_id)
                    st.warning("Exame excluido!")
                    time.sleep(1)
                    st.rerun()


def medicamentos_page():
    fields = [
        ("nome", "Nome", "text"),
        ("principio_ativo", "Principio Ativo", "text"),
        ("quantidade", "Quantidade", "number"),
        ("validade", "Validade", "date"),
        ("fornecedor", "Fornecedor", "text")
    ]
    crud_page("Estoque de Medicamentos", "medicamentos", fields, ["id", "nome", "principio_ativo", "quantidade", "validade"])


def trocar_senha_page():
    st.markdown("<<h1 style='text-align:center; color:#00d4ff; text-shadow: 0 0 20px #00d4ff;'>Trocar Senha</h1>", unsafe_allow_html=True)

    with st.form("form_trocar_senha"):
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
        submitted = st.form_submit_button("Alterar Senha")
        if submitted:
            user = st.session_state.get("user")
            if not verify_password(user["username"], senha_atual):
                st.error("Senha atual incorreta!")
            elif nova_senha != confirmar_senha:
                st.error("A nova senha e a confirmacao nao coincidem!")
            elif len(nova_senha) < 6:
                st.error("A nova senha deve ter pelo menos 6 caracteres!")
            else:
                update_password(user["username"], nova_senha)
                st.success("Senha alterada com sucesso!")


def main():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "page" not in st.session_state:
        st.session_state["page"] = "Login"

    if not st.session_state["authenticated"]:
        login_page()
        return

    st.markdown("""
        <style>
        .main {
            background: radial-gradient(circle at center, #0a0a1a 0%, #000000 100%);
            color: #e0f7ff;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.sidebar.markdown('<h1 style="text-align:center; color:#00d4ff; text-shadow: 0 0 20px #00d4ff;">MARMED</h1>', unsafe_allow_html=True)
        st.sidebar.markdown("<<hr style='border-color:#00d4ff;'>", unsafe_allow_html=True)

        menu = [
            "Dashboard",
            "Pacientes",
            "Medicos",
            "Consultas",
            "Financeiro",
            "Exames",
            "Medicamentos",
            "Trocar Senha"
        ]
        for item in menu:
            if st.sidebar.button(item, use_container_width=True, key=f"nav_{item}"):
                st.session_state["page"] = item
                st.rerun()

        st.sidebar.markdown("<<hr style='border-color:#00d4ff;'>", unsafe_allow_html=True)
        if st.sidebar.button("Sair", use_container_width=True, key="logout_btn"):
            st.session_state["authenticated"] = False
            st.session_state["page"] = "Login"
            st.session_state.pop("user", None)
            st.rerun()

        st.sidebar.markdown(f"<<p style='text-align:center; color:#66d9ff;'>Usuario: {st.session_state.get('user', {}).get('username', '')}</p>", unsafe_allow_html=True)
        st.sidebar.markdown(f"<<p style='text-align:center; color:#66d9ff;'>Perfil: {st.session_state.get('user', {}).get('role', '')}</p>", unsafe_allow_html=True)

    page = st.session_state.get("page", "Dashboard")
    if page == "Dashboard":
        dashboard()
    elif page == "Pacientes":
        pacientes_page()
    elif page == "Medicos":
        medicos_page()
    elif page == "Consultas":
        consultas_page()
    elif page == "Financeiro":
        financeiro_page()
    elif page == "Exames":
        exames_page()
    elif page == "Medicamentos":
        medicamentos_page()
    elif page == "Trocar Senha":
        trocar_senha_page()
    else:
        dashboard()


if __name__ == "__main__":
    main()
