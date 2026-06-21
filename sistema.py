import streamlit as st
import sqlite3
import hashlib
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
    c.execute("DROP TABLE IF EXISTS contas_receber")
    c.execute("""
        CREATE TABLE contas_receber (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_conta TEXT,
            referencia_tipo TEXT,
            referencia_numero TEXT,
            tipo_recurso TEXT,
            valor_pago_custeio REAL DEFAULT 0,
            valor_pago_investimento REAL DEFAULT 0,
            valor_total REAL DEFAULT 0,
            data_recebimento TEXT,
            programa_politica TEXT,
            setor_gasto TEXT
        )
    """)
    c.execute("CREATE TABLE IF NOT EXISTS contas_pagar (id INTEGER PRIMARY KEY AUTOINCREMENT, fornecedor TEXT, descricao TEXT, valor REAL, vencimento TEXT, status TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS compras (id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, quantidade REAL, valor_unitario REAL, valor_total REAL, data TEXT, setor TEXT)")
    default_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)", ("admin", default_hash))
    conn.commit()
    conn.close()

init_db()

def login_page():
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #0f172a, #1e3a8a, #0f172a); overflow: hidden; }
        div[data-testid="column"]:nth-child(2) {
            background: rgba(15, 23, 42, 0.75) !important;
            backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(14, 165, 233, 0.3) !important;
            border-radius: 24px !important;
            padding: 48px 40px !important;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5) !important;
            margin-top: 80px !important;
            max-width: 420px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
        .marmed-title { font-size: 52px; font-weight: 800; text-align: center; color: #e0f2fe; letter-spacing: 6px; margin-bottom: 8px; }
        .subtitle { text-align: center; color: #7dd3fc; font-size: 14px; letter-spacing: 4px; margin-bottom: 36px; text-transform: uppercase; }
        .stTextInput label { color: #22d3ee !important; font-weight: 600; font-size: 13px; letter-spacing: 1px; }
        .stSelectbox label { color: #22d3ee !important; font-weight: 600; font-size: 13px; letter-spacing: 1px; }
        .stNumberInput label { color: #22d3ee !important; font-weight: 600; font-size: 13px; letter-spacing: 1px; }
        .stTextInput > div > div > input { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; color: #e0f2fe !important; border-radius: 10px !important; }
        .stButton > button { background: linear-gradient(90deg, #06b6d4, #3b82f6) !important; color: #fff !important; font-weight: 700 !important; border-radius: 10px !important; border: none !important; width: 100%; padding: 12px !important; letter-spacing: 2px; }
        .stSelectbox > div > div { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; border-radius: 10px !important; color: #e0f2fe !important; }
        .stNumberInput > div > div > input { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; color: #e0f2fe !important; border-radius: 10px !important; }
        .stDateInput > div > div > input { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; color: #e0f2fe !important; border-radius: 10px !important; }
        </style>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="marmed-title">MARMED</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">SISTEMA INTEGRADO DE GESTÃO</div>', unsafe_allow_html=True)
        username = st.text_input("USUÁRIO", key="login_user")
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
                st.error("Usuário ou senha inválidos")
        st.markdown('<p style="text-align:center;color:#94a3b8;font-size:12px;margin-top:28px;">Acesso restrito a usuários autorizados</p>', unsafe_allow_html=True)

def dashboard():
    st.markdown('<h1 style="color:#e0f2fe;text-align:center;font-size:48px;font-weight:800;letter-spacing:6px;">MARMED</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#7dd3fc;text-align:center;letter-spacing:4px;margin-bottom:4px;">SISTEMA INTEGRADO DE GESTÃO</h3>', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#1e40af;text-align:center;letter-spacing:3px;font-size:20px;font-weight:700;margin-bottom:16px;">PREFEITURA MUNICIPAL DE LUMINÁRIAS</h2>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(valor_total),0) FROM contas_receber")
    total_cadastrado = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM contas_receber")
    total_contas = c.fetchone()[0]
    c.execute("SELECT COALESCE(COUNT(*),0) FROM compras")
    total_compras = c.fetchone()[0]
    conn.close()
    cols = st.columns(5)
    dados = [
        ("REPASSE FEDERAL", total_cadastrado * 0.3, "#3b82f6"),
        ("REPASSE ESTADUAL", total_cadastrado * 0.2, "#22c55e"),
        ("RECURSO MUNICIPAL", total_cadastrado * 0.15, "#eab308"),
        ("TRANSFERÊNCIA", total_cadastrado * 0.25, "#a855f7"),
        ("TRANSPOSIÇÃO", total_cadastrado * 0.1, "#ef4444")
    ]
    for i, (tit, val, cor) in enumerate(dados):
        with cols[i]:
            st.markdown(f'<div style="background:linear-gradient(135deg,#1a2a3a,#0f2027);border-radius:15px;padding:20px;text-align:center;border-left:4px solid {cor};border:1px solid rgba(34,211,238,0.3);min-height:130px;display:flex;flex-direction:column;justify-content:center;"><div style="color:#b0eaff;font-size:11px;letter-spacing:1px;font-weight:600;margin-bottom:8px;">{tit}</div><div style="color:#00d4ff;font-size:20px;font-weight:700;">{format_currency(val)}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center;color:#64748b;font-size:12px;margin-top:20px;">{total_contas} conta(s) cadastrada(s) | {total_compras} compra(s) - Painel gerencial MARMED - {datetime.now().strftime("%d/%m/%Y")}</p>', unsafe_allow_html=True)

def cadastrar_contas():
    st.markdown('<h1 style="color:#e0f2fe;">CADASTRAR CONTAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    df = conn.execute("SELECT id, numero_conta, referencia_tipo, referencia_numero, tipo_recurso, valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento, programa_politica, setor_gasto FROM contas_receber ORDER BY id DESC").fetchall()
    cols = ["ID", "Nº Conta", "Referência", "Nº/Ano", "Tipo Recurso", "Valor Custeio", "Valor Investimento", "Valor Total", "Data Receb.", "Programa/Política", "Setor Gasto"]
    conn.close()
    if df:
        import pandas as pd
        pdf = pd.DataFrame(df, columns=cols)
        if "Valor Custeio" in pdf.columns:
            pdf["Valor Custeio"] = pdf["Valor Custeio"].apply(lambda x: format_currency(x))
        if "Valor Investimento" in pdf.columns:
            pdf["Valor Investimento"] = pdf["Valor Investimento"].apply(lambda x: format_currency(x))
        if "Valor Total" in pdf.columns:
            pdf["Valor Total"] = pdf["Valor Total"].apply(lambda x: format_currency(x))
        st.dataframe(pdf, use_container_width=True, hide_index=True)
    with st.expander("NOVO CADASTRO", expanded=False):
        num_conta = st.text_input("Número da Conta")
        ref_contrato = st.selectbox("Referência do Contrato", ["", "Resolução", "Deliberação", "Portaria"])
        num_ano_ref = st.text_input("Número/Ano")
        tipo_recurso = st.selectbox("Tipo de Recurso", ["", "Custeio", "Investimento", "Custeio/Investimento"], key="tipo_recurso_cad")
        if tipo_recurso == "Custeio/Investimento":
            val_custeio = st.number_input("Valor Pago Custeio", min_value=0.0, step=0.01, format="%.2f")
            val_invest = st.number_input("Valor Pago Investimento", min_value=0.0, step=0.01, format="%.2f")
            val_total = val_custeio + val_invest
        elif tipo_recurso == "Custeio":
            val_pago = st.number_input("Valor Pago", min_value=0.0, step=0.01, format="%.2f")
            val_custeio = val_pago
            val_invest = 0.0
            val_total = val_pago
        elif tipo_recurso == "Investimento":
            val_pago = st.number_input("Valor Pago", min_value=0.0, step=0.01, format="%.2f")
            val_custeio = 0.0
            val_invest = val_pago
            val_total = val_pago
        else:
            val_custeio = 0.0
            val_invest = 0.0
            val_total = 0.0
        data_receb = st.text_input("Data de Recebimento", value=datetime.now().strftime("%d/%m/%Y"))
        programa_politica = st.text_input("Programa/Política")
        setor_gasto = st.text_input("Setor de Referência de Gasto")
        if st.button("Salvar Conta", key="salvar_conta"):
            if not num_conta or not ref_contrato or not tipo_recurso:
                st.error("Preencha os campos obrigatórios: Número da Conta, Referência do Contrato e Tipo de Recurso")
            else:
                conn = sqlite3.connect("marmed.db")
                c = conn.cursor()
                c.execute("""
                    INSERT INTO contas_receber 
                    (numero_conta, referencia_tipo, referencia_numero, tipo_recurso, 
                     valor_pago_custeio, valor_pago_investimento, valor_total, 
                     data_recebimento, programa_politica, setor_gasto)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (num_conta, ref_contrato, num_ano_ref, tipo_recurso, 
                      val_custeio, val_invest, val_total,
                      data_receb, programa_politica, setor_gasto))
                conn.commit()
                conn.close()
                st.success("Conta cadastrada com sucesso!")
                st.rerun()

def contas_cadastradas():
    st.markdown('<h1 style="color:#e0f2fe;">CONTAS CADASTRADAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    df = conn.execute("SELECT id, numero_conta, referencia_tipo, referencia_numero, tipo_recurso, valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento, programa_politica, setor_gasto FROM contas_receber ORDER BY id DESC").fetchall()
    cols = ["ID", "Nº Conta", "Referência", "Nº/Ano", "Tipo Recurso", "Valor Custeio", "Valor Investimento", "Valor Total", "Data Receb.", "Programa/Política", "Setor Gasto"]
    conn.close()
    if df:
        import pandas as pd
        pdf = pd.DataFrame(df, columns=cols)
        if "Valor Custeio" in pdf.columns:
            pdf["Valor Custeio"] = pdf["Valor Custeio"].apply(lambda x: format_currency(x))
        if "Valor Investimento" in pdf.columns:
            pdf["Valor Investimento"] = pdf["Valor Investimento"].apply(lambda x: format_currency(x))
        if "Valor Total" in pdf.columns:
            pdf["Valor Total"] = pdf["Valor Total"].apply(lambda x: format_currency(x))
        st.dataframe(pdf, use_container_width=True, hide_index=True)
        st.markdown(f'<p style="color:#64748b;font-size:12px;text-align:center;">Total de registros: {len(df)}</p>', unsafe_allow_html=True)
    else:
        st.info("Nenhuma conta cadastrada ainda.")

def realizar_compras():
    st.markdown('<h1 style="color:#e0f2fe;">REALIZAR COMPRAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    df = conn.execute("SELECT id, item, quantidade, valor_unitario, valor_total, data, setor FROM compras ORDER BY id DESC").fetchall()
    cols = ["ID", "Item", "Qtd", "Valor Unit.", "Valor Total", "Data", "Setor"]
    conn.close()
    if df:
        import pandas as pd
        pdf = pd.DataFrame(df, columns=cols)
        if "Valor Unit." in pdf.columns:
            pdf["Valor Unit."] = pdf["Valor Unit."].apply(lambda x: format_currency(x))
        if "Valor Total" in pdf.columns:
            pdf["Valor Total"] = pdf["Valor Total"].apply(lambda x: format_currency(x))
        st.dataframe(pdf, use_container_width=True, hide_index=True)
    with st.expander("NOVA COMPRA", expanded=False):
        item = st.text_input("Item/Produto")
        qtd = st.number_input("Quantidade", min_value=1.0, step=1.0, format="%.0f")
        val_unit = st.number_input("Valor Unitário", min_value=0.0, step=0.01, format="%.2f")
        val_total_compra = qtd * val_unit
        st.markdown(f'<p style="color:#00d4ff;font-size:18px;font-weight:700;">Valor Total: {format_currency(val_total_compra)}</p>', unsafe_allow_html=True)
        data_compra = st.text_input("Data da Compra", value=datetime.now().strftime("%d/%m/%Y"))
        setor = st.text_input("Setor")
        if st.button("Registrar Compra", key="salvar_compra"):
            if not item or not setor:
                st.error("Preencha os campos obrigatórios: Item e Setor")
            else:
                conn = sqlite3.connect("marmed.db")
                c = conn.cursor()
                c.execute("INSERT INTO compras (item, quantidade, valor_unitario, valor_total, data, setor) VALUES (?, ?, ?, ?, ?, ?)", (item, qtd, val_unit, val_total_compra, data_compra, setor))
                conn.commit()
                conn.close()
                st.success("Compra registrada com sucesso!")
                st.rerun()

def change_password():
    st.markdown('<h1 style="color:#e0f2fe;">Trocar Senha</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    current = st.text_input("Senha atual", type="password")
    new_pass = st.text_input("Nova senha", type="password")
    confirm = st.text_input("Confirmar nova senha", type="password")
    if st.button("Salvar nova senha"):
        if new_pass != confirm:
            st.error("As senhas não conferem")
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

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "page" not in st.session_state:
        st.session_state["page"] = "Dashboard"
    if not st.session_state["logged_in"]:
        login_page()
    else:
        st.sidebar.markdown('<h3 style="color:#22d3ee;text-align:center;letter-spacing:2px;">ABA DE NAVEGAÇÃO</h3>', unsafe_allow_html=True)
        st.sidebar.markdown('<hr>', unsafe_allow_html=True)
        if st.sidebar.button("🏠 INÍCIO", key="nav_inicio", use_container_width=True):
            st.session_state["page"] = "Dashboard"
            st.rerun()
        if st.sidebar.button("CADASTRAR CONTAS", key="nav_cadastrar", use_container_width=True):
            st.session_state["page"] = "CADASTRAR CONTAS"
            st.rerun()
        if st.sidebar.button("CONTAS CADASTRADAS", key="nav_cadastradas", use_container_width=True):
            st.session_state["page"] = "CONTAS CADASTRADAS"
            st.rerun()
        if st.sidebar.button("REALIZAR COMPRAS", key="nav_compras", use_container_width=True):
            st.session_state["page"] = "REALIZAR COMPRAS"
            st.rerun()
        st.sidebar.markdown('<hr>', unsafe_allow_html=True)
        if st.sidebar.button("Sair", key="logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()
        page = st.session_state["page"]
        if page == "Dashboard":
            dashboard()
        elif page == "CADASTRAR CONTAS":
            cadastrar_contas()
        elif page == "CONTAS CADASTRADAS":
            contas_cadastradas()
        elif page == "REALIZAR COMPRAS":
            realizar_compras()
        elif page == "Trocar Senha":
            change_password()

if __name__ == "__main__":
    main()
