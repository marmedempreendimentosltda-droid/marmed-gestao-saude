import streamlit as st
import sqlite3
import hashlib
import random
from datetime import datetime

st.set_page_config(page_title="MARMED", layout="wide")

def format_currency(value):
    if value is None:
        value = 0.0
    return f"R$ {float(value):,.2f}"

def init_db():
    conn = sqlite3.connect("marmed.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS contas_pagar (id INTEGER PRIMARY KEY AUTOINCREMENT, fornecedor TEXT, descricao TEXT, valor REAL, vencimento TEXT, status TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS contas_receber (id INTEGER PRIMARY KEY AUTOINCREMENT, devedor TEXT, descricao TEXT, valor REAL, vencimento TEXT, status TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS empenhos (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, objeto TEXT, valor REAL, data TEXT, status TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS licitacoes (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, objeto TEXT, modalidade TEXT, valor REAL, data TEXT, status TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS contratos (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, contratado TEXT, objeto TEXT, valor REAL, inicio TEXT, fim TEXT, status TEXT)")
    default_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)", ("admin", default_hash))
    conn.commit()
    conn.close()

init_db()

def login_page():
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #0f172a, #1e3a8a, #0f172a); overflow: hidden; }
        .card-unico {
            background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(16px);
            border: 1px solid rgba(14, 165, 233, 0.3); border-radius: 24px;
            padding: 48px; max-width: 420px; margin: 80px auto;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            text-align: center;
        }
        .marmed-title { font-size: 52px; font-weight: 800; color: #e0f2fe; letter-spacing: 6px; text-shadow: 0 0 20px rgba(14, 165, 233, 0.6); }
        .subtitle { color: #7dd3fc; font-size: 14px; letter-spacing: 4px; margin-top: 8px; margin-bottom: 32px; }
        .stTextInput > label { color: #22d3ee !important; font-weight: 600; font-size: 13px; letter-spacing: 1px; }
        .stTextInput > div > div > input {
            background: rgba(30, 41, 59, 0.8) !important;
            border: 1px solid rgba(34, 211, 238, 0.3) !important;
            color: #e0f2fe !important; border-radius: 10px !important;
        }
        .stButton > button {
            background: linear-gradient(90deg, #06b6d4, #3b82f6) !important;
            color: #fff !important; font-weight: 700 !important;
            border-radius: 10px !important; border: none !important;
            width: 100%; padding: 12px !important; letter-spacing: 2px;
        }
        .acesso-text { color: #94a3b8; font-size: 12px; margin-top: 24px; }
        </style>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="card-unico">', unsafe_allow_html=True)
        st.markdown('<div class="marmed-title">MARMED</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">SISTEMA INTEGRADO DE GESTAO</div>', unsafe_allow_html=True)
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
        st.markdown('<div class="acesso-text">Acesso restrito a usuarios autorizados</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
def dashboard():
    st.markdown('<h1 style="color:#e0f2fe;text-align:center;">MARMED</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#7dd3fc;text-align:center;letter-spacing:4px;">SISTEMA INTEGRADO DE GESTAO</h3>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(valor),0) FROM contas_pagar")
    tp = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(valor),0) FROM contas_receber")
    tr = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(valor),0) FROM empenhos")
    te = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(valor),0) FROM licitacoes")
    tl = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(valor),0) FROM contratos")
    tc = c.fetchone()[0]
    conn.close()
    cols = st.columns(5)
    dados = [
        ("REPASSE FEDERAL", tp, "#ef4444"),
        ("REPASSE ESTADUAL", tr, "#22c55e"),
        ("RECURSO MUNICIPAL", te, "#eab308"),
        ("TRANSFERENCIA", tl, "#a855f7"),
        ("TRANSPOSICAO", tc, "#3b82f6"),
    ]
    for i, (tit, val, cor) in enumerate(dados):
        with cols[i]:
            st.markdown(f'<div style="background:linear-gradient(135deg,#1a2a3a,#0f2027);border-radius:15px;padding:20px;text-align:center;border-left:4px solid {cor};border:1px solid rgba(34,211,238,0.3);box-shadow:0 0 15px rgba(0,212,255,0.2);"><div style="color:#b0eaff;font-size:12px;letter-spacing:1px;">{tit}</div><div style="color:#00d4ff;font-size:22px;font-weight:700;">{format_currency(val)}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;color:#64748b;font-size:12px;margin-top:20px;">Painel gerencial MARMED - {datetime.now().strftime("%d/%m/%Y")}</div>', unsafe_allow_html=True)

def change_password():
    st.markdown('<h1 style="color:#e0f2fe;">Trocar Senha</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    current = st.text_input("Senha atual", type="password")
    new_pass = st.text_input("Nova senha", type="password")
    confirm = st.text_input("Confirmar nova senha", type="password")
    if st.button("Salvar nova senha"):
        if new_pass != confirm:
            st.error("As senhas nao conferem")
        else:
            ch = hashlib.sha256(current.encode()).hexdigest()
            conn = sqlite3.connect("marmed.db")
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE username=? AND password_hash=?", (st.session_state["username"], ch))
            row = c.fetchone()
            if row:
                nh = hashlib.sha256(new_pass.encode()).hexdigest()
                c.execute("UPDATE users SET password_hash=? WHERE id=?", (nh, row[0]))
                conn.commit()
                conn.close()
                st.success("Senha alterada com sucesso")
            else:
                conn.close()
                st.error("Senha atual incorreta")

def crud_page(table, fields, title):
    st.markdown(f'<h1 style="color:#e0f2fe;">{title}</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    df = conn.execute(f"SELECT * FROM {table}").fetchall()
    cols = [desc[0] for desc in conn.execute(f"SELECT * FROM {table} LIMIT 0").description]
    conn.close()
    if df:
        import pandas as pd
        pdf = pd.DataFrame(df, columns=cols)
        if "valor" in pdf.columns:
            pdf["valor"] = pdf["valor"].apply(lambda x: format_currency(x))
        st.dataframe(pdf, use_container_width=True, hide_index=True)
    with st.expander("Adicionar registro"):
        inp = {}
        for f in fields:
            if f == "valor":
                inp[f] = st.number_input("Valor", min_value=0.0, step=0.01, key=f"{table}_{f}")
            elif "data" in f or "vencimento" in f or "inicio" in f or "fim" in f:
                inp[f] = st.text_input(f.capitalize(), value=datetime.now().strftime("%d/%m/%Y"), key=f"{table}_{f}")
            else:
                inp[f] = st.text_input(f.capitalize(), key=f"{table}_{f}")
        if st.button("Salvar", key=f"{table}_save"):
            conn = sqlite3.connect("marmed.db")
            vals = [inp[f] for f in fields]
            conn.execute(f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({', '.join(['?'] * len(fields))})", vals)
            conn.commit()
            conn.close()
            st.success("Registro salvo")
            st.rerun()

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "page" not in st.session_state:
        st.session_state["page"] = "Dashboard"
    if not st.session_state["logged_in"]:
        login_page()
    else:
        st.sidebar.markdown('<h2 style="color:#22d3ee;text-align:center;">MARMED</h2>', unsafe_allow_html=True)
        st.sidebar.markdown(f'<p style="color:#94a3b8;text-align:center;font-size:12px;">{st.session_state["username"]}</p>', unsafe_allow_html=True)
        st.sidebar.markdown('<hr>', unsafe_allow_html=True)
        pages = ["Dashboard", "Contas a Pagar", "Contas a Receber", "Empenhos", "Licitacoes", "Contratos", "Trocar Senha"]
        for p in pages:
            if st.sidebar.button(p, key=f"nav_{p}", use_container_width=True):
                st.session_state["page"] = p
                st.rerun()
        st.sidebar.markdown('<hr>', unsafe_allow_html=True)
        if st.sidebar.button("Sair", key="logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()
        page = st.session_state["page"]
        if page == "Dashboard":
            dashboard()
        elif page == "Contas a Pagar":
            crud_page("contas_pagar", ["fornecedor", "descricao", "valor", "vencimento", "status"], "Contas a Pagar")
        elif page == "Contas a Receber":
            crud_page("contas_receber", ["devedor", "descricao", "valor", "vencimento", "status"], "Contas a Receber")
        elif page == "Empenhos":
            crud_page("empenhos", ["numero", "objeto", "valor", "data", "status"], "Empenhos")
        elif page == "Licitacoes":
            crud_page("licitacoes", ["numero", "objeto", "modalidade", "valor", "data", "status"], "Licitacoes")
        elif page == "Contratos":
            crud_page("contratos", ["numero", "contratado", "objeto", "valor", "inicio", "fim", "status"], "Contratos")
        elif page == "Trocar Senha":
            change_password()

if __name__ == "__main__":
    main()
