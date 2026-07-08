import streamlit as st
import sqlite3
import os
import hashlib
from datetime import datetime, date

st.set_page_config(page_title="MARMED - Gestao Financeira", page_icon="🏛️", layout="wide", initial_sidebar_state="expanded")

# ===================== CSS =====================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Inter:wght@400;600&display=swap');

.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0f172a 100%);
    color: #e2e8f0;
}

.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(circle at 20% 30%, rgba(59,130,246,0.15) 0%, transparent 50%),
                radial-gradient(circle at 80% 70%, rgba(99,102,241,0.12) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid rgba(59,130,246,0.2);
}

.title-marmed {
    font-family: 'Orbitron', sans-serif;
    font-size: 140px;
    font-weight: 900;
    background: linear-gradient(90deg, #60a5fa, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin: 0;
    line-height: 1;
    letter-spacing: 4px;
}

.title-login {
    font-family: 'Orbitron', sans-serif;
    font-size: 120px;
    font-weight: 900;
    background: linear-gradient(90deg, #60a5fa, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin: 0;
    line-height: 1;
    letter-spacing: 4px;
}

.subtitle {
    text-align: center;
    color: #94a3b8;
    font-family: 'Inter', sans-serif;
    font-size: 18px;
    margin-top: 10px;
}

.glass-card {
    background: rgba(30,41,59,0.5);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(59,130,246,0.3);
    border-radius: 20px;
    padding: 40px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}

.esfera-card {
    background: rgba(30,41,59,0.6);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border: 1px solid rgba(59,130,246,0.3);
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    transition: transform 0.3s, box-shadow 0.3s;
}

.esfera-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 40px rgba(59,130,246,0.3);
}

.esfera-nome {
    font-family: 'Orbitron', sans-serif;
    font-size: 22px;
    color: #60a5fa;
    margin-bottom: 8px;
}

.esfera-valor {
    font-size: 28px;
    font-weight: 700;
    color: #a7f3d0;
    margin: 10px 0;
}

.badge {
    display: inline-block;
    padding: 6px 16px;
    margin: 4px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
}
.badge-seguro { background: rgba(34,197,94,0.2); color: #4ade80; border: 1px solid rgba(34,197,94,0.4); }
.badge-moderno { background: rgba(59,130,246,0.2); color: #60a5fa; border: 1px solid rgba(59,130,246,0.4); }
.badge-sus { background: rgba(168,85,247,0.2); color: #c084fc; border: 1px solid rgba(168,85,247,0.4); }

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background: rgba(15,23,42,0.8);
    color: #e2e8f0;
    border: 1px solid rgba(59,130,246,0.3);
    border-radius: 10px;
}

.stSelectbox > div > div > div {
    background: rgba(15,23,42,0.8);
    color: #e2e8f0;
    border: 1px solid rgba(59,130,246,0.3);
    border-radius: 10px;
}

div[data-bare="true"] {
    background: rgba(15,23,42,0.95) !important;
    color: #e2e8f0 !important;
}

.stDateInput > div > div > input {
    background: rgba(15,23,42,0.8);
    color: #e2e8f0;
    border: 1px solid rgba(59,130,246,0.3);
    border-radius: 10px;
}

.stButton > button {
    background: linear-gradient(90deg, #2563eb, #7c3aed);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    transition: all 0.3s;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #1d4ed8, #6d28d9);
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(59,130,246,0.4);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    background: rgba(15,23,42,0.6);
    color: #94a3b8;
    border-radius: 10px 10px 0 0;
}
.stTabs [aria-selected="true"] {
    background: rgba(59,130,246,0.3);
    color: #60a5fa;
}

table {
    width: 100%;
    border-collapse: collapse;
    color: #e2e8f0;
}
th {
    background: rgba(59,130,246,0.2);
    padding: 12px;
    text-align: left;
    border-bottom: 2px solid rgba(59,130,246,0.4);
    color: #60a5fa;
}
td {
    padding: 10px 12px;
    border-bottom: 1px solid rgba(59,130,246,0.15);
}
tr:hover td {
    background: rgba(59,130,246,0.1);
}

.section-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 32px;
    color: #60a5fa;
    margin-bottom: 20px;
}

.info-box {
    background: rgba(30,41,59,0.5);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(59,130,246,0.3);
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# ===================== BANCO DE DADOS =====================
DB_NAME = "marmed.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        nome TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS contas_receber (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        esfera TEXT,
        numero_conta TEXT,
        fonte TEXT,
        programa TEXT,
        tipo_recurso TEXT,
        valor_total REAL,
        data_cadastro TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS superavit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        esfera TEXT,
        descricao TEXT,
        valor REAL,
        data TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS ordens_compra (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conta_id INTEGER,
        descricao TEXT,
        fornecedor TEXT,
        valor REAL,
        data TEXT,
        FOREIGN KEY (conta_id) REFERENCES contas_receber(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS arquivos_saude (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria TEXT,
        nome_arquivo TEXT,
        data_upload TEXT,
        conteudo BLOB
    )""")
    # Usuario admin padrao
    senha_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    c.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO users (username, password, nome) VALUES (?, ?, ?)", ("admin", senha_hash, "Administrador"))
    conn.commit()
    conn.close()

init_db()

def get_conn():
    return sqlite3.connect(DB_NAME)

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_senha(senha, hash_salvo):
    return hash_senha(senha) == hash_salvo

# ===================== FUNCOES AUXILIARES =====================
ESFERAS = ["Federal", "Estadual", "Municipal", "Transferencia", "Transposicao"]

def get_fonte(esfera):
    fontes = {
        "Federal": "1.600",
        "Estadual": "1.621",
        "Municipal": "1.500",
        "Transferencia": "1.700",
        "Transposicao": "1.800"
    }
    return fontes.get(esfera, "")

def format_currency(valor):
    if valor is None:
        valor = 0.0
    valor = float(valor)
    s = "{:,.2f}".format(valor)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + s

def total_esfera(esfera):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(valor_total),0) FROM contas_receber WHERE esfera=?", (esfera,))
    total = c.fetchone()[0]
    conn.close()
    return total

def compras_conta(conta_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(valor),0) FROM ordens_compra WHERE conta_id=?", (conta_id,))
    total = c.fetchone()[0]
    conn.close()
    return total

def valor_restante(conta_id, valor_total):
    return valor_total - compras_conta(conta_id)

def listar_contas(esfera=None):
    conn = get_conn()
    c = conn.cursor()
    if esfera:
        c.execute("SELECT * FROM contas_receber WHERE esfera=? ORDER BY id DESC", (esfera,))
    else:
        c.execute("SELECT * FROM contas_receber ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def listar_compras(conta_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM ordens_compra WHERE conta_id=? ORDER BY id DESC", (conta_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def listar_superavits():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM superavit ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def listar_arquivos(categoria=None):
    conn = get_conn()
    c = conn.cursor()
    if categoria:
        c.execute("SELECT id, categoria, nome_arquivo, data_upload FROM arquivos_saude WHERE categoria=? ORDER BY id DESC", (categoria,))
    else:
        c.execute("SELECT id, categoria, nome_arquivo, data_upload FROM arquivos_saude ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

# ===================== SESSAO =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"
if "esfera_selecionada" not in st.session_state:
    st.session_state.esfera_selecionada = None
if "editar_conta_id" not in st.session_state:
    st.session_state.editar_conta_id = None

# ===================== TELA DE LOGIN =====================
def tela_login():
    st.markdown("<div style='margin-top:30px'></div>", unsafe_allow_html=True)
    st.markdown("<h1 class='title-login'>MARMED</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Sistema Integrado de Gestao Publica Municipal</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align:center; color:#60a5fa; font-family:Orbitron;'>🔐 Acesso ao Sistema</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#94a3b8;'>Prefeitura Municipal de Luminarias - MG</p>", unsafe_allow_html=True)

        usuario = st.text_input("Usuario", key="login_user")
        senha = st.text_input("Senha", type="password", key="login_pass")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Entrar", use_container_width=True):
                conn = get_conn()
                c = conn.cursor()
                c.execute("SELECT password, nome FROM users WHERE username=?", (usuario,))
                result = c.fetchone()
                conn.close()
                if result and verificar_senha(senha, result[0]):
                    st.session_state.logged_in = True
                    st.session_state.username = usuario
                    st.session_state.pagina = "inicio"
                    st.rerun()
                else:
                    st.error("Usuario ou senha invalidos.")
        with col_btn2:
            if st.button("Limpar", use_container_width=True):
                st.rerun()

        st.markdown("<div style='text-align:center; margin-top:20px;'>", unsafe_allow_html=True)
        st.markdown("<span class='badge badge-seguro'>🔒 SEGURO</span>", unsafe_allow_html=True)
        st.markdown("<span class='badge badge-moderno'>⚡ MODERNO</span>", unsafe_allow_html=True)
        st.markdown("<span class='badge badge-sus'>🏥 SUS</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ===================== PAGINA INICIAL =====================
def pagina_inicial():
    st.markdown("<h1 class='title-marmed'>MARMED</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Sistema Integrado de Gestao Publica</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#60a5fa; font-size:20px; margin-top:5px;'>Prefeitura Municipal de Luminarias - MG</p>", unsafe_allow_html=True)
    st.markdown("<div style='margin:30px 0'></div>", unsafe_allow_html=True)

    st.markdown("<h2 style='text-align:center; color:#94a3b8; font-family:Orbitron; font-size:24px;'>Esferas de Gestao</h2>", unsafe_allow_html=True)
    st.markdown("<div style='margin:20px 0'></div>", unsafe_allow_html=True)

    cols = st.columns(5)
    for i, esfera in enumerate(ESFERAS):
        total = total_esfera(esfera)
        with cols[i]:
            st.markdown(f"""
            <div class='esfera-card'>
                <div class='esfera-nome'>{esfera}</div>
                <div style='color:#94a3b8; font-size:12px;'>Fonte: {get_fonte(esfera)}</div>
                <div class='esfera-valor'>{format_currency(total)}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Acessar {esfera}", key=f"btn_esfera_{esfera}", use_container_width=True):
                st.session_state.esfera_selecionada = esfera
                st.session_state.pagina = "esfera_detalhe"
                st.rerun()

# ===================== ESFERA DETALHE =====================
def pagina_esfera_detalhe():
    esfera = st.session_state.esfera_selecionada
    if esfera is None:
        st.session_state.pagina = "inicio"
        st.rerun()
        return

    st.markdown(f"<h1 class='section-title'>🏛️ {esfera}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#94a3b8; font-size:18px;'>Fonte vinculada: <b style='color:#60a5fa;'>{get_fonte(esfera)}</b></p>", unsafe_allow_html=True)
    total = total_esfera(esfera)
    st.markdown(f"<div class='info-box'><h3 style='color:#a7f3d0;'>Total da Esfera: {format_currency(total)}</h3></div>", unsafe_allow_html=True)

    if st.button("⬅ Voltar"):
        st.session_state.pagina = "inicio"
        st.rerun()

    st.markdown("<div style='margin:20px 0'></div>", unsafe_allow_html=True)
    contas = listar_contas(esfera)
    if not contas:
        st.info(f"Nenhuma conta cadastrada para a esfera {esfera}.")
        return

    for conta in contas:
        conta_id, esfera_c, numero, fonte, programa, tipo_recurso, valor_total, data_cad = conta
        restante = valor_restante(conta_id, valor_total)
        with st.expander(f"Conta {numero} - {programa} | Restante: {format_currency(restante)}"):
            st.markdown(f"""
            <table>
                <tr><th>Numero da Conta</th><td>{numero}</td></tr>
                <tr><th>Fonte</th><td>{fonte}</td></tr>
                <tr><th>Programa/Politica</th><td>{programa}</td></tr>
                <tr><th>Tipo de Recurso</th><td>{tipo_recurso}</td></tr>
                <tr><th>Valor Total</th><td style='color:#a7f3d0;'>{format_currency(valor_total)}</td></tr>
                <tr><th>Valor Restante</th><td style='color:{'#a7f3d0' if restante >= 0 else '#f87171'};'>{format_currency(restante)}</td></tr>
            </table>
            """, unsafe_allow_html=True)
            compras = listar_compras(conta_id)
            if compras:
                st.markdown("<h4 style='color:#60a5fa; margin-top:15px;'>Compras Realizadas</h4>", unsafe_allow_html=True)
                html_compras = "<table><tr><th>Data</th><th>Descricao</th><th>Fornecedor</th><th>Valor</th></tr>"
                for comp in compras:
                    comp_id, _, descricao, fornecedor, valor, data_comp = comp
                    html_compras += f"<tr><td>{data_comp}</td><td>{descricao}</td><td>{fornecedor}</td><td>{format_currency(valor)}</td></tr>"
                html_compras += "</table>"
                st.markdown(html_compras, unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:#94a3b8;'>Nenhuma compra registrada.</p>", unsafe_allow_html=True)

# ===================== CADASTRO DE CONTAS =====================
def pagina_cadastro_contas():
    st.markdown("<h1 class='section-title'>📝 Cadastro de Contas</h1>", unsafe_allow_html=True)

    editando = st.session_state.editar_conta_id is not None
    conta_edit = None
    if editando:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM contas_receber WHERE id=?", (st.session_state.editar_conta_id,))
        conta_edit = c.fetchone()
        conn.close()
        st.markdown("<div class='info-box'><p style='color:#fbbf24;'>✏️ Editando conta existente</p></div>", unsafe_allow_html=True)
        if st.button("Cancelar Edicao"):
            st.session_state.editar_conta_id = None
            st.rerun()

    esfera_sel = conta_edit[1] if conta_edit else ESFERAS[0]
    esfera = st.selectbox("Esfera", ESFERAS, index=ESFERAS.index(esfera_sel) if conta_edit else 0)
    fonte_auto = get_fonte(esfera)
    st.markdown(f"<p style='color:#60a5fa;'>Fonte vinculada automaticamente: <b>{fonte_auto}</b></p>", unsafe_allow_html=True)

    numero_default = conta_edit[2] if conta_edit else ""
    programa_default = conta_edit[4] if conta_edit else ""
    tipo_default = conta_edit[5] if conta_edit else ""
    valor_default = conta_edit[6] if conta_edit else 0.0

    numero_conta = st.text_input("Numero da Conta", value=numero_default)
    programa = st.text_input("Programa / Politica", value=programa_default)
    tipo_recurso = st.selectbox("Tipo de Recurso", ["Ordinario", "Vinculado", "Saude", "Educacao", "Outros"],
                                 index=["Ordinario", "Vinculado", "Saude", "Educacao", "Outros"].index(tipo_default) if conta_edit and tipo_default in ["Ordinario", "Vinculado", "Saude", "Educacao", "Outros"] else 0)
    valor_total = st.number_input("Valor Total", min_value=0.0, value=float(valor_default), format="%.2f")

    if st.button("Salvar Conta", use_container_width=True):
        if not numero_conta:
            st.error("Informe o numero da conta.")
        else:
            conn = get_conn()
            c = conn.cursor()
            if editando:
                c.execute("UPDATE contas_receber SET esfera=?, numero_conta=?, fonte=?, programa=?, tipo_recurso=?, valor_total=? WHERE id=?",
                          (esfera, numero_conta, fonte_auto, programa, tipo_recurso, valor_total, st.session_state.editar_conta_id))
                st.session_state.editar_conta_id = None
                st.success("Conta atualizada com sucesso!")
            else:
                c.execute("INSERT INTO contas_receber (esfera, numero_conta, fonte, programa, tipo_recurso, valor_total, data_cadastro) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (esfera, numero_conta, fonte_auto, programa, tipo_recurso, valor_total, datetime.now().strftime("%Y-%m-%d")))
                st.success("Conta cadastrada com sucesso!")
            conn.commit()
            conn.close()
            st.rerun()

# ===================== CONTAS CADASTRADAS =====================
def pagina_contas_cadastradas():
    st.markdown("<h1 class='section-title'>📋 Contas Cadastradas</h1>", unsafe_allow_html=True)
    abas = st.tabs(ESFERAS)
    for i, esfera in enumerate(ESFERAS):
        with abas[i]:
            contas = listar_contas(esfera)
            if not contas:
                st.info(f"Nenhuma conta cadastrada em {esfera}.")
            else:
                html = "<table><tr><th>ID</th><th>Numero</th><th>Fonte</th><th>Programa</th><th>Tipo</th><th>Valor Total</th><th>Restante</th><th>Acoes</th></tr>"
                for conta in contas:
                    conta_id, _, numero, fonte, programa, tipo_recurso, valor_total, _ = conta
                    restante = valor_restante(conta_id, valor_total)
                    html += f"<tr><td>{conta_id}</td><td>{numero}</td><td>{fonte}</td><td>{programa}</td><td>{tipo_recurso}</td><td>{format_currency(valor_total)}</td><td>{format_currency(restante)}</td><td>Ver botoes abaixo</td></tr>"
                html += "</table>"
                st.markdown(html, unsafe_allow_html=True)

                st.markdown("<div style='margin:15px 0'></div>", unsafe_allow_html=True)
                for conta in contas:
                    conta_id, _, numero, fonte, programa, tipo_recurso, valor_total, _ = conta
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"<p style='color:#94a3b8;'>Conta: <b style='color:#60a5fa;'>{numero}</b> - {programa}</p>", unsafe_allow_html=True)
                    with col2:
                        if st.button("Editar", key=f"edit_{conta_id}"):
                            st.session_state.editar_conta_id = conta_id
                            st.session_state.pagina = "cadastro_contas"
                            st.rerun()
                    with col3:
                        if st.button("Excluir", key=f"del_{conta_id}"):
                            conn = get_conn()
                            c = conn.cursor()
                            c.execute("DELETE FROM ordens_compra WHERE conta_id=?", (conta_id,))
                            c.execute("DELETE FROM contas_receber WHERE id=?", (conta_id,))
                            conn.commit()
                            conn.close()
                            st.success("Conta excluida com sucesso!")
                            st.rerun()

# ===================== REALIZAR COMPRAS =====================
def pagina_compras():
    st.markdown("<h1 class='section-title'>🛒 Realizar Compras</h1>", unsafe_allow_html=True)
    contas = listar_contas()
    if not contas:
        st.info("Nenhuma conta cadastrada. Cadastre uma conta primeiro.")
        return

    opcoes = {}
    for conta in contas:
        conta_id, esfera, numero, fonte, programa, tipo_recurso, valor_total, _ = conta
        restante = valor_restante(conta_id, valor_total)
        label = f"{numero} - {esfera} - {programa} (Restante: {format_currency(restante)})"
        opcoes[label] = conta_id

    label_sel = st.selectbox("Selecione a Conta", list(opcoes.keys()))
    conta_id_sel = opcoes[label_sel]

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT valor_total FROM contas_receber WHERE id=?", (conta_id_sel,))
    valor_total = c.fetchone()[0]
    conn.close()
    restante = valor_restante(conta_id_sel, valor_total)

    st.markdown(f"""
    <div class='info-box'>
        <p style='color:#94a3b8;'>Saldo Total: <b style='color:#a7f3d0;'>{format_currency(valor_total)}</b></p>
        <p style='color:#94a3b8;'>Saldo Restante: <b style='color:{'#a7f3d0' if restante >= 0 else '#f87171'};'>{format_currency(restante)}</b></p>
    </div>
    """, unsafe_allow_html=True)

    descricao = st.text_input("Descricao da Compra")
    fornecedor = st.text_input("Fornecedor")
    valor_compra = st.number_input("Valor da Compra", min_value=0.0, format="%.2f")
    data_compra = st.date_input("Data da Compra", value=date.today())

    if st.button("Registrar Compra", use_container_width=True):
        if not descricao or not fornecedor:
            st.error("Preencha descricao e fornecedor.")
        elif valor_compra <= 0:
            st.error("Valor da compra deve ser maior que zero.")
        elif valor_compra > restante:
            st.error(f"Valor excede o saldo restante ({format_currency(restante)}).")
        else:
            conn = get_conn()
            c = conn.cursor()
            c.execute("INSERT INTO ordens_compra (conta_id, descricao, fornecedor, valor, data) VALUES (?, ?, ?, ?, ?)",
                      (conta_id_sel, descricao, fornecedor, valor_compra, data_compra.strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.success("Compra registrada com sucesso!")
            st.rerun()

    st.markdown("<div style='margin:20px 0'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#60a5fa;'>Compras desta Conta</h3>", unsafe_allow_html=True)
    compras = listar_compras(conta_id_sel)
    if compras:
        html = "<table><tr><th>Data</th><th>Descricao</th><th>Fornecedor</th><th>Valor</th><th>Acao</th></tr>"
        for comp in compras:
            comp_id, _, desc, forn, val, dt = comp
            html += f"<tr><td>{dt}</td><td>{desc}</td><td>{forn}</td><td>{format_currency(val)}</td><td>Botao abaixo</td></tr>"
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)
        for comp in compras:
            comp_id, _, desc, forn, val, dt = comp
            if st.button(f"Excluir compra {comp_id} - {desc[:20]}", key=f"delcomp_{comp_id}"):
                conn = get_conn()
                c = conn.cursor()
                c.execute("DELETE FROM ordens_compra WHERE id=?", (comp_id,))
                conn.commit()
                conn.close()
                st.success("Compra excluida!")
                st.rerun()
    else:
        st.info("Nenhuma compra registrada para esta conta.")

# ===================== SUPERAVIT FINANCEIRO =====================
def pagina_superavit():
    st.markdown("<h1 class='section-title'>💰 Superavit Financeiro</h1>", unsafe_allow_html=True)

    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#60a5fa;'>Registrar Superavit</h3>", unsafe_allow_html=True)
    esfera = st.selectbox("Esfera", ESFERAS)
    descricao = st.text_input("Descricao")
    valor = st.number_input("Valor", min_value=0.0, format="%.2f")
    data_sup = st.date_input("Data", value=date.today())

    if st.button("Registrar Superavit", use_container_width=True):
        if not descricao:
            st.error("Informe uma descricao.")
        else:
            conn = get_conn()
            c = conn.cursor()
            c.execute("INSERT INTO superavit (esfera, descricao, valor, data) VALUES (?, ?, ?, ?)",
                      (esfera, descricao, valor, data_sup.strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.success("Superavit registrado com sucesso!")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin:20px 0'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#60a5fa;'>Superavits Registrados</h3>", unsafe_allow_html=True)
    sups = listar_superavits()
    if sups:
        html = "<table><tr><th>ID</th><th>Esfera</th><th>Descricao</th><th>Valor</th><th>Data</th><th>Acao</th></tr>"
        for s in sups:
            sid, esf, desc, val, dt = s
            html += f"<tr><td>{sid}</td><td>{esf}</td><td>{desc}</td><td>{format_currency(val)}</td><td>{dt}</td><td>Botao</td></tr>"
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)
        for s in sups:
            sid, esf, desc, val, dt = s
            if st.button(f"Excluir #{sid}", key=f"delsup_{sid}"):
                conn = get_conn()
                c = conn.cursor()
                c.execute("DELETE FROM superavit WHERE id=?", (sid,))
                conn.commit()
                conn.close()
                st.success("Superavit excluido!")
                st.rerun()
    else:
        st.info("Nenhum superavit registrado.")

# ===================== UPLOAD DE ARQUIVOS =====================
def pagina_upload():
    st.markdown("<h1 class='section-title'>📎 Upload de Arquivos</h1>", unsafe_allow_html=True)

    categoria = st.selectbox("Categoria", ["Contas", "Compras", "Outros"])
    uploaded = st.file_uploader("Selecione o arquivo", type=["pdf", "png", "jpg", "jpeg", "xlsx", "docx", "txt", "csv"])

    if st.button("Enviar Arquivo", use_container_width=True):
        if uploaded is not None:
            conteudo = uploaded.read()
            conn = get_conn()
            c = conn.cursor()
            c.execute("INSERT INTO arquivos_saude (categoria, nome_arquivo, data_upload, conteudo) VALUES (?, ?, ?, ?)",
                      (categoria, uploaded.name, datetime.now().strftime("%Y-%m-%d %H:%M"), conteudo))
            conn.commit()
            conn.close()
            st.success(f"Arquivo '{uploaded.name}' enviado com sucesso!")
            st.rerun()
        else:
            st.error("Selecione um arquivo.")

    st.markdown("<div style='margin:20px 0'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#60a5fa;'>Arquivos Enviados</h3>", unsafe_allow_html=True)
    arqs = listar_arquivos()
    if arqs:
        html = "<table><tr><th>ID</th><th>Categoria</th><th>Nome</th><th>Data</th><th>Acao</th></tr>"
        for a in arqs:
            aid, cat, nome, dt = a
            html += f"<tr><td>{aid}</td><td>{cat}</td><td>{nome}</td><td>{dt}</td><td>Botao</td></tr>"
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)
        for a in arqs:
            aid, cat, nome, dt = a
            if st.button(f"Excluir #{aid} - {nome[:20]}", key=f"delarq_{aid}"):
                conn = get_conn()
                c = conn.cursor()
                c.execute("DELETE FROM arquivos_saude WHERE id=?", (aid,))
                conn.commit()
                conn.close()
                st.success("Arquivo excluido!")
                st.rerun()
    else:
        st.info("Nenhum arquivo enviado.")

# ===================== TROCAR SENHA =====================
def pagina_trocar_senha():
    st.markdown("<h1 class='section-title'>🔑 Trocar Senha</h1>", unsafe_allow_html=True)
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    senha_atual = st.text_input("Senha Atual", type="password")
    nova_senha = st.text_input("Nova Senha", type="password")
    confirmar = st.text_input("Confirmar Nova Senha", type="password")

    if st.button("Alterar Senha", use_container_width=True):
        if not senha_atual or not nova_senha or not confirmar:
            st.error("Preencha todos os campos.")
        elif nova_senha != confirmar:
            st.error("As senhas nao coincidem.")
        else:
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT password FROM users WHERE username=?", (st.session_state.username,))
            result = c.fetchone()
            if result and verificar_senha(senha_atual, result[0]):
                c.execute("UPDATE users SET password=? WHERE username=?", (hash_senha(nova_senha), st.session_state.username))
                conn.commit()
                st.success("Senha alterada com sucesso!")
            else:
                st.error("Senha atual incorreta.")
            conn.close()
    st.markdown("</div>", unsafe_allow_html=True)

# ===================== SIDEBAR E ROTEAMENTO =====================
def sidebar_menu():
    with st.sidebar:
        st.markdown("<h2 style='color:#60a5fa; font-family:Orbitron;'>🏛️ MARMED</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94a3b8;'>Usuario: <b>{st.session_state.username}</b></p>", unsafe_allow_html=True)
        st.markdown("<div style='margin:15px 0; border-top:1px solid rgba(59,130,246,0.2);'></div>", unsafe_allow_html=True)

        if st.button("🏠 Pagina Inicial", use_container_width=True, key="menu_inicio"):
            st.session_state.pagina = "inicio"
            st.rerun()
        if st.button("📝 Cadastrar Contas", use_container_width=True, key="menu_cad"):
            st.session_state.pagina = "cadastro_contas"
            st.session_state.editar_conta_id = None
            st.rerun()
        if st.button("📋 Contas Cadastradas", use_container_width=True, key="menu_lista"):
            st.session_state.pagina = "contas_cadastradas"
            st.rerun()
        if st.button("🛒 Realizar Compras", use_container_width=True, key="menu_compras"):
            st.session_state.pagina = "compras"
            st.rerun()
        if st.button("💰 Superavit Financeiro", use_container_width=True, key="menu_superavit"):
            st.session_state.pagina = "superavit"
            st.rerun()
        if st.button("📎 Upload de Arquivos", use_container_width=True, key="menu_upload"):
            st.session_state.pagina = "upload"
            st.rerun()
        if st.button("🔑 Trocar Senha", use_container_width=True, key="menu_senha"):
            st.session_state.pagina = "trocar_senha"
            st.rerun()

        st.markdown("<div style='margin:15px 0; border-top:1px solid rgba(59,130,246,0.2);'></div>", unsafe_allow_html=True)
        if st.button("🚪 Sair", use_container_width=True, key="menu_sair"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.pagina = "inicio"
            st.rerun()

# ===================== APP PRINCIPAL =====================
if not st.session_state.logged_in:
    tela_login()
else:
    sidebar_menu()
    if st.session_state.pagina == "inicio":
        pagina_inicial()
    elif st.session_state.pagina == "esfera_detalhe":
        pagina_esfera_detalhe()
    elif st.session_state.pagina == "cadastro_contas":
        pagina_cadastro_contas()
    elif st.session_state.pagina == "contas_cadastradas":
        pagina_contas_cadastradas()
    elif st.session_state.pagina == "compras":
        pagina_compras()
    elif st.session_state.pagina == "superavit":
        pagina_superavit()
    elif st.session_state.pagina == "upload":
        pagina_upload()
    elif st.session_state.pagina == "trocar_senha":
        pagina_trocar_senha()
    else:
        pagina_inicial()
