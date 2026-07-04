import streamlit as st
import sqlite3
import hashlib
import time
import random
from datetime import datetime, date

DB = "marmed.db"


def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE,
            senha TEXT
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
            ano TEXT,
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
            ano TEXT,
            objeto TEXT,
            modalidade TEXT,
            valor REAL,
            status TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT,
            ano TEXT,
            contratado TEXT,
            objeto TEXT,
            valor REAL,
            inicio TEXT,
            fim TEXT,
            status TEXT
        )
    ''')
    senha_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO usuarios (usuario, senha) VALUES (?, ?)", ("admin", senha_hash))
    conn.commit()
    conn.close()


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


def verificar_login(usuario, senha):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT senha FROM usuarios WHERE usuario = ?", (usuario,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == hash_senha(senha):
        return True
    return False


def trocar_senha(usuario, senha_atual, nova_senha):
    if not verificar_login(usuario, senha_atual):
        return False
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET senha = ? WHERE usuario = ?", (hash_senha(nova_senha), usuario))
    conn.commit()
    conn.close()
    return True


def layout_animated():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');

        .main {
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            background-attachment: fixed;
            color: #ffffff;
        }

        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        .marmed-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 4.5rem;
            font-weight: 900;
            text-align: center;
            letter-spacing: 0.3em;
            color: #ffffff;
            text-shadow: 0 0 10px #00d2ff, 0 0 20px #00d2ff, 0 0 40px #00d2ff;
            margin-top: 0.5rem;
            margin-bottom: 0.2rem;
            animation: marmedPulse 3s ease-in-out infinite;
        }

        @keyframes marmedPulse {
            0% { text-shadow: 0 0 10px #00d2ff, 0 0 20px #00d2ff; transform: translateY(0px); }
            50% { text-shadow: 0 0 20px #00d2ff, 0 0 40px #00d2ff, 0 0 60px #00d2ff; transform: translateY(-5px); }
            100% { text-shadow: 0 0 10px #00d2ff, 0 0 20px #00d2ff; transform: translateY(0px); }
        }

        .marmed-letter {
            display: inline-block;
            animation: letter3D 2.5s ease-in-out infinite;
        }

        .marmed-letter:nth-child(1) { animation-delay: 0s; }
        .marmed-letter:nth-child(2) { animation-delay: 0.2s; }
        .marmed-letter:nth-child(3) { animation-delay: 0.4s; }
        .marmed-letter:nth-child(4) { animation-delay: 0.6s; }
        .marmed-letter:nth-child(5) { animation-delay: 0.8s; }
        .marmed-letter:nth-child(6) { animation-delay: 1.0s; }

        @keyframes letter3D {
            0%, 100% { transform: rotateX(0deg) rotateY(0deg) scale(1); }
            50% { transform: rotateX(15deg) rotateY(15deg) scale(1.1); }
        }

        .subtitle {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.2rem;
            font-weight: 400;
            text-align: center;
            letter-spacing: 0.4em;
            color: #a0d2ff;
            margin-bottom: 2rem;
            text-shadow: 0 0 5px rgba(0, 210, 255, 0.5);
        }

        .glass-card {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 2.5rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            max-width: 420px;
            margin: auto;
        }

        .login-label {
            font-family: 'Orbitron', sans-serif;
            color: #a0d2ff;
            font-size: 0.85rem;
            letter-spacing: 0.1em;
        }

        .metric-card {
            background: rgba(255, 255, 255, 0.07);
            border: 1px solid rgba(0, 210, 255, 0.3);
            border-radius: 15px;
            padding: 1.2rem;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0, 210, 255, 0.3);
        }

        .metric-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 0.85rem;
            letter-spacing: 0.08em;
            color: #a0d2ff;
            margin-bottom: 0.5rem;
        }

        .metric-value {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            color: #ffffff;
        }

        .stButton button {
            background: linear-gradient(90deg, #00d2ff, #3a7bd5);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.6rem 1.5rem;
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            letter-spacing: 0.1em;
            width: 100%;
        }

        .stButton button:hover {
            background: linear-gradient(90deg, #3a7bd5, #00d2ff);
            color: white;
        }

        .crud-container {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 15px;
            padding: 1.5rem;
            margin-top: 1rem;
        }

        .css-1d391kg, .css-1v3fvcr {
            background-color: rgba(15, 12, 41, 0.95) !important;
        }

        .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox select {
            background-color: rgba(255, 255, 255, 0.08);
            color: #ffffff;
            border: 1px solid rgba(0, 210, 255, 0.3);
            border-radius: 8px;
        }

        .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stSelectbox select:focus {
            border: 1px solid #00d2ff;
            box-shadow: 0 0 10px rgba(0, 210, 255, 0.4);
        }

        .sidebar-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 1.1rem;
            color: #00d2ff;
            text-align: center;
            margin-bottom: 1rem;
            letter-spacing: 0.1em;
        }
        </style>
    """, unsafe_allow_html=True)

    particles = ""
    for i in range(50):
        x = random.randint(0, 100)
        y = random.randint(0, 100)
        size = random.randint(2, 6)
        delay = random.random() * 5
        duration = random.randint(5, 15)
        particles += f"<<span style='position:fixed;left:{x}%;top:{y}%;width:{size}px;height:{size}px;background:rgba(0,210,255,0.6);border-radius:50%;animation:particle {duration}s linear {delay}s infinite;pointer-events:none;z-index:0;'></span>"
    st.markdown(f"""
        <style>
        @keyframes particle {{
            0% {{ transform: translateY(0) scale(1); opacity: 0.6; }}
            50% {{ opacity: 1; }}
            100% {{ transform: translateY(-100vh) scale(0.2); opacity: 0; }}
        }}
        </style>
        {particles}
    """, unsafe_allow_html=True)


def show_header():
    st.markdown("""
        <div class="marmed-title">
            <span class="marmed-letter">M</span>
            <span class="marmed-letter">A</span>
            <span class="marmed-letter">R</span>
            <span class="marmed-letter">M</span>
            <span class="marmed-letter">E</span>
            <span class="marmed-letter">D</span>
        </div>
        <div class="subtitle">SISTEMA INTEGRADO DE GESTAO</div>
    """, unsafe_allow_html=True)


def tela_login():
    layout_animated()
    show_header()
    st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<<div class='login-label'>USUARIO</div>", unsafe_allow_html=True)
    usuario = st.text_input("", key="login_user", label_visibility="collapsed")
    st.markdown("<<div class='login-label' style='margin-top:1rem;'>SENHA</div>", unsafe_allow_html=True)
    senha = st.text_input("", type="password", key="login_pass", label_visibility="collapsed")
    st.markdown("<<br>", unsafe_allow_html=True)
    if st.button("ENTRAR", key="btn_entrar"):
        if verificar_login(usuario, senha):
            st.session_state.logado = True
            st.session_state.usuario = usuario
            st.rerun()
        else:
            st.error("Usuario ou senha invalidos")
    st.markdown("</div>", unsafe_allow_html=True)


def dashboard():
    show_header()
    st.markdown("<<h3 style='text-align:center; color:#a0d2ff; font-family:Orbitron; letter-spacing:0.2em;'>DASHBOARD FINANCEIRA</h3>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT SUM(valor) FROM contas_receber WHERE status = 'A receber'")
    repasse_federal = c.fetchone()[0] or 0
    c.execute("SELECT SUM(valor) FROM contas_receber WHERE status = 'A receber'")
    repasse_estadual = c.fetchone()[0] or 0
    c.execute("SELECT SUM(valor) FROM contas_receber WHERE status = 'A receber'")
    recurso_municipal = c.fetchone()[0] or 0
    c.execute("SELECT SUM(valor) FROM contas_receber WHERE status = 'A receber'")
    transferencia = c.fetchone()[0] or 0
    c.execute("SELECT SUM(valor) FROM contas_receber WHERE status = 'A receber'")
    transposicao = c.fetchone()[0] or 0
    conn.close()
    cols = st.columns(5)
    metricas = [
        ("REPASSE FEDERAL", repasse_federal),
        ("REPASSE ESTADUAL", repasse_estadual),
        ("RECURSO MUNICIPAL", recurso_municipal),
        ("TRANSFERENCIA", transferencia),
        ("TRANSPOSICAO", transposicao)
    ]
    for i, (titulo, valor) in enumerate(metricas):
        with cols[i]:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">{titulo}</div>
                    <div class="metric-value">R$ {valor:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)


def crud_contas_pagar():
    show_header()
    st.markdown("<<h3 style='text-align:center; color:#a0d2ff; font-family:Orbitron; letter-spacing:0.2em;'>CONTAS A PAGAR</h3>", unsafe_allow_html=True)
    st.markdown("<<div class='crud-container'>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    with st.form("form_pagar", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fornecedor = st.text_input("Fornecedor")
            descricao = st.text_input("Descricao")
        with col2:
            valor = st.number_input("Valor", min_value=0.0, format="%.2f")
            vencimento = st.date_input("Vencimento", value=date.today())
            status = st.selectbox("Status", ["Pendente", "Pago", "Atrasado"])
        submitted = st.form_submit_button("SALVAR")
        if submitted:
            c.execute("INSERT INTO contas_pagar (fornecedor, descricao, valor, vencimento, status) VALUES (?, ?, ?, ?, ?)",
                      (fornecedor, descricao, valor, vencimento.strftime("%Y-%m-%d"), status))
            conn.commit()
            st.success("Registro salvo")
    c.execute("SELECT * FROM contas_pagar ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    for row in rows:
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.write(f"ID {row[0]} - {row[1]} - {row[2]} - R$ {row[3]:,.2f} - Venc: {row[4]} - {row[5]}")
        with col2:
            if st.button("Editar", key=f"edit_pagar_{row[0]}"):
                st.session_state.edit_pagar = row
        with col3:
            if st.button("Excluir", key=f"del_pagar_{row[0]}"):
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("DELETE FROM contas_pagar WHERE id = ?", (row[0],))
                conn.commit()
                conn.close()
                st.rerun()
    if "edit_pagar" in st.session_state:
        row = st.session_state.edit_pagar
        with st.form("edit_pagar_form"):
            col1, col2 = st.columns(2)
            with col1:
                e_fornecedor = st.text_input("Fornecedor", value=row[1])
                e_descricao = st.text_input("Descricao", value=row[2])
            with col2:
                e_valor = st.number_input("Valor", value=row[3], format="%.2f")
                e_vencimento = st.date_input("Vencimento", value=datetime.strptime(row[4], "%Y-%m-%d").date())
                e_status = st.selectbox("Status", ["Pendente", "Pago", "Atrasado"], index=["Pendente", "Pago", "Atrasado"].index(row[5]))
            if st.form_submit_button("ATUALIZAR"):
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("UPDATE contas_pagar SET fornecedor=?, descricao=?, valor=?, vencimento=?, status=? WHERE id=?",
                          (e_fornecedor, e_descricao, e_valor, e_vencimento.strftime("%Y-%m-%d"), e_status, row[0]))
                conn.commit()
                conn.close()
                del st.session_state.edit_pagar
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def crud_contas_receber():
    show_header()
    st.markdown("<<h3 style='text-align:center; color:#a0d2ff; font-family:Orbitron; letter-spacing:0.2em;'>CONTAS A RECEBER</h3>", unsafe_allow_html=True)
    st.markdown("<<div class='crud-container'>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    with st.form("form_receber", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            devedor = st.text_input("Devedor")
            descricao = st.text_input("Descricao")
        with col2:
            valor = st.number_input("Valor", min_value=0.0, format="%.2f")
            vencimento = st.date_input("Vencimento", value=date.today())
            status = st.selectbox("Status", ["A receber", "Recebido", "Atrasado"])
        submitted = st.form_submit_button("SALVAR")
        if submitted:
            c.execute("INSERT INTO contas_receber (devedor, descricao, valor, vencimento, status) VALUES (?, ?, ?, ?, ?)",
                      (devedor, descricao, valor, vencimento.strftime("%Y-%m-%d"), status))
            conn.commit()
            st.success("Registro salvo")
    c.execute("SELECT * FROM contas_receber ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    for row in rows:
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.write(f"ID {row[0]} - {row[1]} - {row[2]} - R$ {row[3]:,.2f} - Venc: {row[4]} - {row[5]}")
        with col2:
            if st.button("Editar", key=f"edit_receber_{row[0]}"):
                st.session_state.edit_receber = row
        with col3:
            if st.button("Excluir", key=f"del_receber_{row[0]}"):
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("DELETE FROM contas_receber WHERE id = ?", (row[0],))
                conn.commit()
                conn.close()
                st.rerun()
    if "edit_receber" in st.session_state:
        row = st.session_state.edit_receber
        with st.form("edit_receber_form"):
            col1, col2 = st.columns(2)
            with col1:
                e_devedor = st.text_input("Devedor", value=row[1])
                e_descricao = st.text_input("Descricao", value=row[2])
            with col2:
                e_valor = st.number_input("Valor", value=row[3], format="%.2f")
                e_vencimento = st.date_input("Vencimento", value=datetime.strptime(row[4], "%Y-%m-%d").date())
                e_status = st.selectbox("Status", ["A receber", "Recebido", "Atrasado"], index=["A receber", "Recebido", "Atrasado"].index(row[5]))
            if st.form_submit_button("ATUALIZAR"):
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("UPDATE contas_receber SET devedor=?, descricao=?, valor=?, vencimento=?, status=? WHERE id=?",
                          (e_devedor, e_descricao, e_valor, e_vencimento.strftime("%Y-%m-%d"), e_status, row[0]))
                conn.commit()
                conn.close()
                del st.session_state.edit_receber
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def crud_empenhos():
    show_header()
    st.markdown("<<h3 style='text-align:center; color:#a0d2ff; font-family:Orbitron; letter-spacing:0.2em;'>EMPENHOS</h3>", unsafe_allow_html=True)
    st.markdown("<<div class='crud-container'>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    with st.form("form_empenho", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            numero = st.text_input("Numero")
            ano = st.text_input("Ano")
            objeto = st.text_input("Objeto")
        with col2:
            valor = st.number_input("Valor", min_value=0.0, format="%.2f")
            data = st.date_input("Data", value=date.today())
            status = st.selectbox("Status", ["Ativo", "Anulado", "Liquidado"])
        submitted = st.form_submit_button("SALVAR")
        if submitted:
            c.execute("INSERT INTO empenhos (numero, ano, objeto, valor, data, status) VALUES (?, ?, ?, ?, ?, ?)",
                      (numero, ano, objeto, valor, data.strftime("%Y-%m-%d"), status))
            conn.commit()
            st.success("Registro salvo")
    c.execute("SELECT * FROM empenhos ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    for row in rows:
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.write(f"ID {row[0]} - {row[1]}/{row[2]} - {row[3]} - R$ {row[4]:,.2f} - {row[5]} - {row[6]}")
        with col2:
            if st.button("Editar", key=f"edit_emp_{row[0]}"):
                st.session_state.edit_emp = row
        with col3:
            if st.button("Excluir", key=f"del_emp_{row[0]}"):
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("DELETE FROM empenhos WHERE id = ?", (row[0],))
                conn.commit()
                conn.close()
                st.rerun()
    if "edit_emp" in st.session_state:
        row = st.session_state.edit_emp
        with st.form("edit_emp_form"):
            col1, col2 = st.columns(2)
            with col1:
                e_numero = st.text_input("Numero", value=row[1])
                e_ano = st.text_input("Ano", value=row[2])
                e_objeto = st.text_input("Objeto", value=row[3])
            with col2:
                e_valor = st.number_input("Valor", value=row[4], format="%.2f")
                e_data = st.date_input("Data", value=datetime.strptime(row[5], "%Y-%m-%d").date())
                e_status = st.selectbox("Status", ["Ativo", "Anulado", "Liquidado"], index=["Ativo", "Anulado", "Liquidado"].index(row[6]))
            if st.form_submit_button("ATUALIZAR"):
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("UPDATE empenhos SET numero=?, ano=?, objeto=?, valor=?, data=?, status=? WHERE id=?",
                          (e_numero, e_ano, e_objeto, e_valor, e_data.strftime("%Y-%m-%d"), e_status, row[0]))
                conn.commit()
                conn.close()
                del st.session_state.edit_emp
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def crud_licitacoes():
    show_header()
    st.markdown("<<h3 style='text-align:center; color:#a0d2ff; font-family:Orbitron; letter-spacing:0.2em;'>LICITACOES</h3>", unsafe_allow_html=True)
    st.markdown("<<div class='crud-container'>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    with st.form("form_lic", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            numero = st.text_input("Numero")
            ano = st.text_input("Ano")
            objeto = st.text_input("Objeto")
        with col2:
            modalidade = st.selectbox("Modalidade", ["Pregao", "Concorrencia", "Convite", "Tomada de Precos", "Concurso", "Leilao"])
            valor = st.number_input("Valor", min_value=0.0, format="%.2f")
            status = st.selectbox("Status", ["Em andamento", "Concluida", "Cancelada", "Homologada"])
        submitted = st.form_submit_button("SALVAR")
        if submitted:
            c.execute("INSERT INTO licitacoes (numero, ano, objeto, modalidade, valor, status) VALUES (?, ?, ?, ?, ?, ?)",
                      (numero, ano, objeto, modalidade, valor, status))
            conn.commit()
            st.success("Registro salvo")
    c.execute("SELECT * FROM licitacoes ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    for row in rows:
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.write(f"ID {row[0]} - {row[1]}/{row[2]} - {row[3]} - {row[4]} - R$ {row[5]:,.2f} - {row[6]}")
        with col2:
            if st.button("Editar", key=f"edit_lic_{row[0]}"):
                st.session_state.edit_lic = row
        with col3:
            if st.button("Excluir", key=f"del_lic_{row[0]}"):
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("DELETE FROM licitacoes WHERE id = ?", (row[0],))
                conn.commit()
                conn.close()
                st.rerun()
    if "edit_lic" in st.session_state:
        row = st.session_state.edit_lic
        with st.form("edit_lic_form"):
            col1, col2 = st.columns(2)
            with col1:
                e_numero = st.text_input("Numero", value=row[1])
                e_ano = st.text_input("Ano", value=row[2])
                e_objeto = st.text_input("Objeto", value=row[3])
            with col2:
                e_modalidade = st.selectbox("Modalidade", ["Pregao", "Concorrencia", "Convite", "Tomada de Precos", "Concurso", "Leilao"], index=["Pregao", "Concorrencia", "Convite", "Tomada de Precos", "Concurso", "Leilao"].index(row[4]))
                e_valor = st.number_input("Valor", value=row[5], format="%.2f")
                e_status = st.selectbox("Status", ["Em andamento", "Concluida", "Cancelada", "Homologada"], index=["Em andamento", "Concluida", "Cancelada", "Homologada"].index(row[6]))
            if st.form_submit_button("ATUALIZAR"):
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("UPDATE licitacoes SET numero=?, ano=?, objeto=?, modalidade=?, valor=?, status=? WHERE id=?",
                          (e_numero, e_ano, e_objeto, e_modalidade, e_valor, e_status, row[0]))
                conn.commit()
                conn.close()
                del st.session_state.edit_lic
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def crud_contratos():
    show_header()
    st.markdown("<<h3 style='text-align:center; color:#a0d2ff; font-family:Orbitron; letter-spacing:0.2em;'>CONTRATOS</h3>", unsafe_allow_html=True)
    st.markdown("<<div class='crud-container'>", unsafe_allow_html=True)
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    with st.form("form_contr", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            numero = st.text_input("Numero")
            ano = st.text_input("Ano")
            contratado = st.text_input("Contratado")
            objeto = st.text_input("Objeto")
        with col2:
            valor = st.number_input("Valor", min_value=0.0, format="%.2f")
            inicio = st.date_input("Inicio", value=date.today())
            fim = st.date_input("Fim", value=date.today())
            status = st.selectbox("Status", ["Vigente", "Encerrado", "Rescindido", "Aditivado"])
        submitted = st.form_submit_button("SALVAR")
        if submitted:
            c.execute("INSERT INTO contratos (numero, ano, contratado, objeto, valor, inicio, fim, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (numero, ano, contratado, objeto, valor, inicio.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d"), status))
            conn.commit()
            st.success("Registro salvo")
    c.execute("SELECT * FROM contratos ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    for row in rows:
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.write(f"ID {row[0]} - {row[1]}/{row[2]} - {row[3]} - {row[4]} - R$ {row[5]:,.2f} - {row[6]} a {row[7]} - {row[8]}")
        with col2:
            if st.button("Editar", key=f"edit_contr_{row[0]}"):
                st.session_state.edit_contr = row
        with col3:
            if st.button("Excluir", key=f"del_contr_{row[0]}"):
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("DELETE FROM contratos WHERE id = ?", (row[0],))
                conn.commit()
                conn.close()
                st.rerun()
    if "edit_contr" in st.session_state:
        row = st.session_state.edit_contr
        with st.form("edit_contr_form"):
            col1, col2 = st.columns(2)
            with col1:
                e_numero = st.text_input("Numero", value=row[1])
                e_ano = st.text_input("Ano", value=row[2])
                e_contratado = st.text_input("Contratado", value=row[3])
                e_objeto = st.text_input("Objeto", value=row[4])
            with col2:
                e_valor = st.number_input("Valor", value=row[5], format="%.2f")
                e_inicio = st.date_input("Inicio", value=datetime.strptime(row[6], "%Y-%m-%d").date())
                e_fim = st.date_input("Fim", value=datetime.strptime(row[7], "%Y-%m-%d").date())
                e_status = st.selectbox("Status", ["Vigente", "Encerrado", "Rescindido", "Aditivado"], index=["Vigente", "Encerrado", "Rescindido", "Aditivado"].index(row[8]))
            if st.form_submit_button("ATUALIZAR"):
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                c.execute("UPDATE contratos SET numero=?, ano=?, contratado=?, objeto=?, valor=?, inicio=?, fim=?, status=? WHERE id=?",
                          (e_numero, e_ano, e_contratado, e_objeto, e_valor, e_inicio.strftime("%Y-%m-%d"), e_fim.strftime("%Y-%m-%d"), e_status, row[0]))
                conn.commit()
                conn.close()
                del st.session_state.edit_contr
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def trocar_senha_page():
    show_header()
    st.markdown("<<h3 style='text-align:center; color:#a0d2ff; font-family:Orbitron; letter-spacing:0.2em;'>TROCAR SENHA</h3>", unsafe_allow_html=True)
    st.markdown("<<div class='crud-container'>", unsafe_allow_html=True)
    with st.form("form_senha"):
        senha_atual = st.text_input("Senha atual", type="password")
        nova_senha = st.text_input("Nova senha", type="password")
        confirma = st.text_input("Confirmar nova senha", type="password")
        if st.form_submit_button("ALTERAR SENHA"):
            if nova_senha != confirma:
                st.error("Nova senha e confirmacao nao conferem")
            elif trocar_senha(st.session_state.usuario, senha_atual, nova_senha):
                st.success("Senha alterada com sucesso")
            else:
                st.error("Senha atual incorreta")
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    init_db()
    st.set_page_config(page_title="MARMED - Sistema Integrado de Gestao", layout="wide", initial_sidebar_state="expanded")
    if "logado" not in st.session_state:
        st.session_state.logado = False
    if not st.session_state.logado:
        tela_login()
    else:
        layout_animated()
        st.sidebar.markdown("<<div class='sidebar-title'>MARMED</div>", unsafe_allow_html=True)
        st.sidebar.markdown("---")
        menu = st.sidebar.radio("MENU", ["Dashboard", "Contas a Pagar", "Contas a Receber", "Empenhos", "Licitacoes", "Contratos", "Trocar Senha"])
        st.sidebar.markdown("---")
        if st.sidebar.button("SAIR"):
            st.session_state.logado = False
            st.session_state.usuario = None
            st.rerun()
        if menu == "Dashboard":
            dashboard()
        elif menu == "Contas a Pagar":
            crud_contas_pagar()
        elif menu == "Contas a Receber":
            crud_contas_receber()
        elif menu == "Empenhos":
            crud_empenhos()
        elif menu == "Licitacoes":
            crud_licitacoes()
        elif menu == "Contratos":
            crud_contratos()
        elif menu == "Trocar Senha":
            trocar_senha_page()


if __name__ == "__main__":
    main()
