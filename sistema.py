import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, date

st.set_page_config(page_title="MARMED", layout="wide")


def init_db():
    conn = sqlite3.connect("marmed.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS contas_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fornecedor TEXT,
            descricao TEXT,
            valor REAL,
            vencimento TEXT,
            status TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS contas_receber (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            devedor TEXT,
            descricao TEXT,
            valor REAL,
            vencimento TEXT,
            status TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS empenhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            objeto TEXT,
            valor REAL,
            data TEXT,
            status TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS licitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            objeto TEXT,
            modalidade TEXT,
            valor REAL,
            data TEXT,
            status TEXT
        )
    ''')
    c.execute('''
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
    ''')
    default_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)", ("admin", default_hash))
    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_user(username, password):
    conn = sqlite3.connect("marmed.db")
    c = conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == hash_password(password):
        return True
    return False


def change_password(username, current, new):
    if not verify_user(username, current):
        return False
    conn = sqlite3.connect("marmed.db")
    c = conn.cursor()
    c.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hash_password(new), username))
    conn.commit()
    conn.close()
    return True


def format_currency(value):
    if value is None:
        value = 0
    return "R$ {:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")


def login_page():
    st.markdown(
        """
        <style>
        .login-bg {
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            z-index: -1;
        }
        .glass-card {
            background: rgba(255,255,255,0.07);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px 0 rgba(0,0,0,0.37);
            border: 1px solid rgba(255,255,255,0.18);
            max-width: 420px;
            margin: auto;
            margin-top: 80px;
            backdrop-filter: blur(10px);
        }
        .marmed-letter {
            display: inline-block;
            font-size: 52px;
            font-weight: 900;
            color: #00d4ff;
            text-shadow: 0 0 20px #00d4ff;
            animation: flyIn 1.2s ease forwards;
            opacity: 0;
        }
        @keyframes flyIn {
            0% {transform: translateY(-80px) scale(0.5); opacity: 0;}
            100% {transform: translateY(0) scale(1); opacity: 1;}
        }
        .subtitle {
            color: #b0eaff;
            letter-spacing: 4px;
            font-size: 14px;
            margin-top: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        .acesso-bottom {
            text-align: center;
            color: #00d4ff;
            font-size: 12px;
            margin-top: 20px;
            letter-spacing: 2px;
        }
        .particle {
            position: fixed;
            width: 6px;
            height: 6px;
            background: rgba(0,212,255,0.4);
            border-radius: 50%;
            animation: float 8s infinite linear;
        }
        @keyframes float {
            0% {transform: translateY(100vh) translateX(0); opacity: 0;}
            50% {opacity: 1;}
            100% {transform: translateY(-10vh) translateX(40px); opacity: 0;}
        }
        </style>
        <div class="login-bg"></div>
        <div class="particle" style="left:10%; animation-duration:7s;"></div>
        <div class="particle" style="left:25%; animation-duration:9s;"></div>
        <div class="particle" style="left:40%; animation-duration:6s;"></div>
        <div class="particle" style="left:55%; animation-duration:10s;"></div>
        <div class="particle" style="left:70%; animation-duration:8s;"></div>
        <div class="particle" style="left:85%; animation-duration:7s;"></div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <div class="glass-card">
            <div style="text-align:center;">
                <span class="marmed-letter" style="animation-delay:0s;">M</span>
                <span class="marmed-letter" style="animation-delay:0.1s;">A</span>
                <span class="marmed-letter" style="animation-delay:0.2s;">R</span>
                <span class="marmed-letter" style="animation-delay:0.3s;">M</span>
                <span class="marmed-letter" style="animation-delay:0.4s;">E</span>
                <span class="marmed-letter" style="animation-delay:0.5s;">D</span>
            </div>
            <div class="subtitle">SISTEMA INTEGRADO DE GESTAO</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                """
                <div style="max-width:340px; margin:auto; margin-top:20px;">
                """,
                unsafe_allow_html=True
            )
            st.markdown('<p style="color:#00d4ff;">Usuario</p>', unsafe_allow_html=True)
            username = st.text_input("", key="login_user", label_visibility="collapsed")
            st.markdown('<p style="color:#00d4ff;">Senha</p>', unsafe_allow_html=True)
            password = st.text_input("", type="password", key="login_pass", label_visibility="collapsed")
            if st.button("Entrar", use_container_width=True):
                if verify_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.page = "Dashboard"
                    st.rerun()
                else:
                    st.error("Usuario ou senha invalidos")
            st.markdown(
                """
                </div>
                <div class="acesso-bottom">ACESSO</div>
                """,
                unsafe_allow_html=True
            )


def get_total(table):
    conn = sqlite3.connect("marmed.db")
    c = conn.cursor()
    c.execute(f"SELECT COALESCE(SUM(valor),0) FROM {table}")
    total = c.fetchone()[0]
    conn.close()
    return total


def dashboard():
    st.markdown('<h1 style="text-align:center; color:#00d4ff;">Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    cols = st.columns(5)
    labels = ["REPASSE FEDERAL", "REPASSE ESTADUAL", "RECURSO MUNICIPAL", "TRANSFERENCIA", "TRANSPOSICAO"]
    values = [get_total("contas_receber")] * 5
    for i, (label, value) in enumerate(zip(labels, values)):
        with cols[i]:
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, #1a2a3a, #0f2027);
                border-radius: 15px; padding: 20px; text-align: center;
                border: 1px solid #00d4ff; box-shadow: 0 0 15px rgba(0,212,255,0.2);">
                <div style="color:#b0eaff; font-size:12px; letter-spacing:1px;">{label}</div>
                <div style="color:#00d4ff; font-size:22px; font-weight:700;">{format_currency(value)}</div>
                </div>
                """,
                unsafe_allow_html=True
            )


def crud_page(title, table, fields):
    st.markdown(f'<h1 style="text-align:center; color:#00d4ff;">{title}</h1>', unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
  st.markdown('<h3 style="color:#00d4ff;">Cadastrar / Editar</h3>', unsafe_allow_html=True)
    cols = st.columns(len(fields))
    inputs = {}
    for col, field in zip(cols, fields):
        with col:
            if field in ["vencimento", "data", "inicio", "fim"]:
                inputs[field] = st.date_input(field.capitalize(), key=f"{table}_{field}")
            elif field == "valor":
                inputs[field] = st.number_input("Valor", min_value=0.0, format="%.2f", key=f"{table}_{field}")
            else:
                inputs[field] = st.text_input(field.capitalize(), key=f"{table}_{field}")
    status = st.selectbox("Status", ["Pendente", "Pago", "Recebido", "Ativo", "Inativo", "Concluido", "Cancelado"], key=f"{table}_status")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Salvar", use_container_width=True, key=f"{table}_save"):
            conn = sqlite3.connect("marmed.db")
            c = conn.cursor()
            field_names = ", ".join(fields + ["status"])
            placeholders = ", ".join(["?"] * (len(fields) + 1))
            values = []
            for field in fields:
                if field in ["vencimento", "data", "inicio", "fim"]:
                    values.append(inputs[field].strftime("%Y-%m-%d"))
                else:
                    values.append(inputs[field])
            values.append(status)
            c.execute(f"INSERT INTO {table} ({field_names}) VALUES ({placeholders})", values)
            conn.commit()
            conn.close()
            st.success("Registro salvo")
            st.rerun()
    with c2:
        delete_id = st.number_input("ID para excluir", min_value=0, step=1, key=f"{table}_delete_id")
        if st.button("Excluir", use_container_width=True, key=f"{table}_delete"):
            conn = sqlite3.connect("marmed.db")
            c = conn.cursor()
            c.execute(f"DELETE FROM {table} WHERE id = ?", (delete_id,))
            conn.commit()
            conn.close()
            st.success("Registro excluido")
            st.rerun()


def contas_pagar():
    crud_page("Contas a Pagar", "contas_pagar", ["fornecedor", "descricao", "valor", "vencimento"])


def contas_receber():
    crud_page("Contas a Receber", "contas_receber", ["devedor", "descricao", "valor", "vencimento"])


def empenhos():
    crud_page("Empenhos", "empenhos", ["numero", "objeto", "valor", "data"])


def licitacoes():
    crud_page("Licitacoes", "licitacoes", ["numero", "objeto", "modalidade", "valor", "data"])


def contratos():
    crud_page("Contratos", "contratos", ["numero", "contratado", "objeto", "valor", "inicio", "fim"])


def trocar_senha():
    st.markdown('<h1 style="text-align:center; color:#00d4ff;">Trocar Senha</h1>', unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown('<p style="color:#00d4ff;">Senha Atual</p>', unsafe_allow_html=True)
    senha_atual = st.text_input("", type="password", key="senha_atual", label_visibility="collapsed")
    st.markdown('<p style="color:#00d4ff;">Nova Senha</p>', unsafe_allow_html=True)
    nova_senha = st.text_input("", type="password", key="nova_senha", label_visibility="collapsed")
    st.markdown('<p style="color:#00d4ff;">Confirmar Nova Senha</p>', unsafe_allow_html=True)
    confirmar_senha = st.text_input("", type="password", key="confirmar_senha", label_visibility="collapsed")
    if st.button("Alterar Senha"):
        if nova_senha != confirmar_senha:
            st.error("Nova senha e confirmacao nao conferem")
        elif change_password(st.session_state.username, senha_atual, nova_senha):
            st.success("Senha alterada com sucesso")
        else:
            st.error("Senha atual incorreta")


def sidebar():
    st.sidebar.markdown('<h1 style="text-align:center; color:#00d4ff;">MARMED</h1>', unsafe_allow_html=True)
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)
    menu = [
        "Dashboard", "Contas a Pagar", "Contas a Receber", "Empenhos",
        "Licitacoes", "Contratos", "Trocar Senha"
    ]
    for item in menu:
        if st.sidebar.button(item, use_container_width=True):
            st.session_state.page = item
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)
    if st.sidebar.button("Sair", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.page = "Login"
        st.rerun()


def main():
    init_db()
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "page" not in st.session_state:
        st.session_state.page = "Login"
    if not st.session_state.logged_in:
        login_page()
    else:
        sidebar()
        page = st.session_state.page
        if page == "Dashboard":
            dashboard()
        elif page == "Contas a Pagar":
            contas_pagar()
        elif page == "Contas a Receber":
            contas_receber()
        elif page == "Empenhos":
            empenhos()
        elif page == "Licitacoes":
            licitacoes()
        elif page == "Contratos":
            contratos()
        elif page == "Trocar Senha":
            trocar_senha()
        else:
            dashboard()


if __name__ == "__main__":
    main()
