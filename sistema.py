import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime
import random
import math

st.set_page_config(page_title="MARMED", page_icon="<<img src='https://cdn-icons-png.flaticon.com/512/3774/3774299.png' width='32'/>", layout="wide")


def format_currency(value):
    if value is None:
        value = 0.0
    try:
        value = float(value)
    except Exception:
        value = 0.0
    s = f"{value:,.2f}"
    return "R$ " + s


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
            valor REAL,
            vencimento TEXT,
            status TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS contas_receber (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            valor REAL,
            vencimento TEXT,
            status TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS empenhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            descricao TEXT,
            valor REAL,
            data TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS licitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            objeto TEXT,
            valor REAL,
            status TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            contratada TEXT,
            valor REAL,
            vigencia TEXT
        )
    ''')
    default_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)", ("admin", default_hash))
    conn.commit()
    conn.close()


init_db()


def login_page():
    st.markdown('''
        <style>
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .main {
            background: linear-gradient(-45deg, #0f172a, #1e3a8a, #0f172a, #0ea5e9);
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
        }
        .glass-card {
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(14, 165, 233, 0.3);
            border-radius: 24px;
            padding: 48px;
            max-width: 420px;
            margin: 0 auto;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 30px rgba(14, 165, 233, 0.1);
        }
        .marmed-title {
            font-size: 52px;
            font-weight: 800;
            text-align: center;
            color: #e0f2fe;
            letter-spacing: 6px;
            text-shadow: 0 0 20px rgba(14, 165, 233, 0.6);
            animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { text-shadow: 0 0 20px rgba(14, 165, 233, 0.6); }
            50% { text-shadow: 0 0 40px rgba(34, 211, 238, 0.9); }
        }
        .subtitle {
            text-align: center;
            color: #7dd3fc;
            font-size: 14px;
            letter-spacing: 4px;
            margin-top: 8px;
            margin-bottom: 32px;
            text-transform: uppercase;
        }
        .stTextInput > label {
            color: #22d3ee !important;
            font-weight: 600;
            font-size: 13px;
            letter-spacing: 1px;
        }
        .stTextInput > div > div > input {
            background: rgba(30, 41, 59, 0.8) !important;
            border: 1px solid rgba(34, 211, 238, 0.3) !important;
            color: #e0f2fe !important;
            border-radius: 10px !important;
        }
        .stButton > button {
            background: linear-gradient(90deg, #06b6d4, #3b82f6) !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
            border: none !important;
            width: 100%;
            padding: 12px !important;
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        .acesso-text {
            text-align: center;
            color: #94a3b8;
            font-size: 12px;
            margin-top: 24px;
        }
        .particle {
            position: fixed;
            border-radius: 50%;
            background: rgba(34, 211, 238, 0.15);
            pointer-events: none;
            z-index: 0;
        }
        </style>
    ''', unsafe_allow_html=True)
    particles_html = ""
    for i in range(30):
        size = random.randint(4, 12)
        left = random.randint(0, 100)
        top = random.randint(0, 100)
        duration = random.randint(10, 25)
        delay = random.randint(0, 10)
        particles_html += f'<div class="particle" style="width:{size}px;height:{size}px;left:{left}vw;top:{top}vh;animation:float {duration}s linear {delay}s infinite;"></div>'
    st.markdown(particles_html, unsafe_allow_html=True)
    st.markdown('''
        <style>
        @keyframes float {
            0% { transform: translateY(0) translateX(0); opacity: 0.2; }
            50% { opacity: 0.5; }
            100% { transform: translateY(-100vh) translateX(20px); opacity: 0; }
        }
        </style>
    ''', unsafe_allow_html=True)
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.markdown('''
            <div class="glass-card">
                <div class="marmed-title">MARMED</div>
                <div class="subtitle">SISTEMA INTEGRADO DE GESTAO</div>
            </div>
        ''', unsafe_allow_html=True)
        st.markdown('<div class="glass-card" style="margin-top:-20px;padding-top:20px;">', unsafe_allow_html=True)
        username = st.text_input("USUARIO", key="login_user")
        password = st.text_input("SENHA", type="password", key="login_pass")
        if st.button("Acessar", key="login_btn"):
            pw_hash = hashlib.sha256(password.encode()).hexdigest()
            conn = sqlite3.connect("marmed.db")
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (username, pw_hash))
            user = c.fetchone()
            conn.close()
            if user:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["page"] = "Dashboard"
                st.rerun()
            else:
                st.error("Usuario ou senha invalidos")
        st.markdown('''
            <div class="acesso-text">Acesso restrito a usuarios autorizados</div>
            </div>
        ''', unsafe_allow_html=True)


def change_password():
    st.markdown('<h1 style="color:#e0f2fe;">Trocar Senha</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    current = st.text_input("Senha atual", type="password")
    new_pass = st.text_input("Nova senha", type="password")
    confirm = st.text_input("Confirmar nova senha", type="password")
    if st.button("Salvar nova senha"):
        if new_pass != confirm:
            st.error("As senhas nao conferem")
        elif len(new_pass) < 6:
            st.error("A nova senha deve ter pelo menos 6 caracteres")
        else:
            current_hash = hashlib.sha256(current.encode()).hexdigest()
            conn = sqlite3.connect("marmed.db")
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE username=? AND password_hash=?", (st.session_state["username"], current_hash))
            row = c.fetchone()
            if row:
                new_hash = hashlib.sha256(new_pass.encode()).hexdigest()
                c.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, row[0]))
                conn.commit()
                conn.close()
                st.success("Senha alterada com sucesso")
            else:
                conn.close()
                st.error("Senha atual incorreta")


def dashboard():
    st.markdown('<h1 style="color:#e0f2fe;text-align:center;text-shadow:0 0 20px rgba(14,165,233,0.4);">MARMED</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#7dd3fc;text-align:center;letter-spacing:4px;">SISTEMA INTEGRADO DE GESTAO</h3>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    c = conn.cursor()
    c.execute("SELECT SUM(valor) FROM contas_pagar")
    total_pagar = c.fetchone()[0] or 0.0
    c.execute("SELECT SUM(valor) FROM contas_receber")
    total_receber = c.fetchone()[0] or 0.0
    c.execute("SELECT SUM(valor) FROM empenhos")
    total_empenhos = c.fetchone()[0] or 0.0
    c.execute("SELECT SUM(valor) FROM licitacoes")
    total_licitacoes = c.fetchone()[0] or 0.0
    c.execute("SELECT SUM(valor) FROM contratos")
    total_contratos = c.fetchone()[0] or 0.0
    conn.close()
    cards = [
        ("Contas a Pagar", total_pagar, "#ef4444"),
        ("Contas a Receber", total_receber, "#22c55e"),
        ("Empenhos", total_empenhos, "#eab308"),
        ("Licitações", total_licitacoes, "#a855f7"),
        ("Contratos", total_contratos, "#3b82f6"),
    ]
    st.markdown('''
        <style>
        .metric-card {
            background: rgba(15, 23, 42, 0.7);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(34, 211, 238, 0.2);
            box-shadow: 0 8px 30px rgba(0,0,0,0.3);
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-4px);
        }
        .metric-title {
            color: #94a3b8;
            font-size: 13px;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        .metric-value {
            color: #e0f2fe;
            font-size: 26px;
            font-weight: 700;
            margin-top: 8px;
        }
        </style>
    ''', unsafe_allow_html=True)
    cols = st.columns(5)
    for i, (title, value, color) in enumerate(cards):
        with cols[i]:
            st.markdown(f'''
                <div class="metric-card" style="border-left: 4px solid {color};">
                    <div class="metric-title">{title}</div>
                    <div class="metric-value">{format_currency(value)}</div>
                </div>
            ''', unsafe_allow_html=True)
    st.markdown('<br>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;color:#64748b;font-size:12px;">Painel gerencial MARMED - ' + datetime.now().strftime("%d/%m/%Y") + '</div>', unsafe_allow_html=True)


def crud_page(table, fields, title, value_field="valor"):
    st.markdown(f'<h1 style="color:#e0f2fe;">{title}</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table}")
    rows = c.fetchall()
    cols = [desc[0] for desc in c.description]
    conn.close()
    df = pd.DataFrame(rows, columns=cols)
    if not df.empty and value_field in df.columns:
        df[value_field] = df[value_field].apply(format_currency)
    st.markdown('<h3 style="color:#7dd3fc;">Registros</h3>', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
    with st.expander("Adicionar / Editar"):
        record_id = st.number_input("ID (0 para novo)", min_value=0, step=1, value=0)
        inputs = {}
        for field in fields:
            if field == value_field:
                inputs[field] = st.number_input(field.capitalize(), min_value=0.0, step=0.01, value=0.0)
            elif "data" in field or "vencimento" in field or "vigencia" in field:
                inputs[field] = st.text_input(field.capitalize(), value=datetime.now().strftime("%d/%m/%Y"))
            else:
                inputs[field] = st.text_input(field.capitalize())
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Salvar"):
                conn = sqlite3.connect("marmed.db")
                c = conn.cursor()
                placeholders = ", ".join(["?"] * len(fields))
                values = [inputs[f] for f in fields]
                if record_id == 0:
                    c.execute(f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({placeholders})", values)
                    st.success("Registro criado")
                else:
                    set_clause = ", ".join([f"{f}=?" for f in fields])
                    c.execute(f"UPDATE {table} SET {set_clause} WHERE id=?", values + [record_id])
                    st.success("Registro atualizado")
                conn.commit()
                conn.close()
                st.rerun()
        with col2:
            if st.button("Excluir") and record_id > 0:
                conn = sqlite3.connect("marmed.db")
                c = conn.cursor()
                c.execute(f"DELETE FROM {table} WHERE id=?", (record_id,))
                conn.commit()
                conn.close()
                st.success("Registro excluido")
                st.rerun()
        with col3:
            if st.button("Limpar"):
                st.rerun()


def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "page" not in st.session_state:
        st.session_state["page"] = "Dashboard"
    if not st.session_state["logged_in"]:
        login_page()
    else:
        st.markdown('''
            <style>
            .main {
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            }
            .stSidebar {
                background: rgba(15, 23, 42, 0.95);
            }
            .stSidebar .stButton > button {
                background: rgba(30, 41, 59, 0.8) !important;
                color: #e0f2fe !important;
                border: 1px solid rgba(34, 211, 238, 0.3) !important;
                border-radius: 8px !important;
                text-align: left !important;
            }
            .stSidebar .stButton > button:hover {
                background: rgba(34, 211, 238, 0.15) !important;
            }
            </style>
        ''', unsafe_allow_html=True)
        st.sidebar.markdown(f'<h2 style="color:#22d3ee;text-align:center;">MARMED</h2>', unsafe_allow_html=True)
        st.sidebar.markdown(f'<p style="color:#94a3b8;text-align:center;font-size:12px;">{st.session_state["username"]}</p>', unsafe_allow_html=True)
        st.sidebar.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
        pages = ["Dashboard", "Contas a Pagar", "Contas a Receber", "Empenhos", "Licitacoes", "Contratos", "Trocar Senha"]
        for p in pages:
            if st.sidebar.button(p, key=f"nav_{p}"):
                st.session_state["page"] = p
                st.rerun()
        st.sidebar.markdown('<br>', unsafe_allow_html=True)
        if st.sidebar.button("Sair", key="logout"):
            st.session_state["logged_in"] = False
            st.session_state["page"] = "Dashboard"
            st.rerun()
        page = st.session_state["page"]
        if page == "Dashboard":
            dashboard()
        elif page == "Contas a Pagar":
            crud_page("contas_pagar", ["fornecedor", "valor", "vencimento", "status"], "Contas a Pagar")
        elif page == "Contas a Receber":
            crud_page("contas_receber", ["cliente", "valor", "vencimento", "status"], "Contas a Receber")
        elif page == "Empenhos":
            crud_page("empenhos", ["numero", "descricao", "valor", "data"], "Empenhos")
        elif page == "Licitacoes":
            crud_page("licitacoes", ["numero", "objeto", "valor", "status"], "Licitacoes")
        elif page == "Contratos":
            crud_page("contratos", ["numero", "contratada", "valor", "vigencia"], "Contratos")
        elif page == "Trocar Senha":
            change_password()


if __name__ == "__main__":
    main()
