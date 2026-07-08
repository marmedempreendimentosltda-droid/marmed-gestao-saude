import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime, date

st.set_page_config(page_title="MARMED - Gestao Publica", page_icon="🏛️", layout="wide")

DB_NAME = "marmed.db"

# ----------------------------- CSS -----------------------------
st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        background: linear-gradient(135deg, #0a0e27 0%, #16213e 50%, #0f3460 100%);
        color: #f1f5f9;
    }
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #16213e 50%, #0f3460 100%);
        color: #f1f5f9;
    }
    section[data-testid="stSidebar"] {
        background-color: #0a0e27 !important;
        color: #f1f5f9 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #f1f5f9 !important;
    }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input,
    .stDateInput > div > div > input {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border: 1px solid #334155 !important;
    }
    .stSelectbox > div > div > div {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
    }
    div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
    }
    ul[data-baseweb="menu"] {
        background-color: #1e293b !important;
    }
    ul[data-baseweb="menu"] li {
        color: #f1f5f9 !important;
    }
    .stButton > button {
        background-color: #1e40af !important;
        color: #ffffff !important;
        border: none !important;
    }
    .stButton > button:hover {
        background-color: #1d4ed8 !important;
        color: #ffffff !important;
    }
    .stMetric {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border-radius: 10px;
        padding: 15px;
    }
    .card-esfera {
        background-color: #1e293b;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        border: 2px solid #334155;
    }
    .card-esfera:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(30, 64, 175, 0.5);
        border-color: #1e40af;
    }
    .card-esfera h3 {
        color: #93c5fd !important;
        margin-bottom: 10px;
    }
    .card-esfera p {
        color: #f1f5f9 !important;
        font-size: 22px;
        font-weight: bold;
        margin: 0;
    }
    .titulo-marmed {
        font-size: 140px !important;
        font-weight: 900 !important;
        text-align: center !important;
        background: linear-gradient(90deg, #60a5fa, #3b82f6, #93c5fd) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        margin: 0 !important;
        line-height: 1 !important;
    }
    .subtitulo-marmed {
        text-align: center !important;
        color: #93c5fd !important;
        font-size: 24px !important;
        margin-top: 10px !important;
    }
    .prefeitura-marmed {
        text-align: center !important;
        color: #cbd5e1 !important;
        font-size: 18px !important;
        margin-top: 5px !important;
        margin-bottom: 40px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------- BANCO DE DADOS -----------------------------
def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        nome TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS contas_receber (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        esfera TEXT,
        numero_conta TEXT,
        fonte TEXT,
        referencia_tipo TEXT,
        referencia_numero TEXT,
        tipo_recurso TEXT,
        valor_pago_custeio REAL DEFAULT 0,
        valor_pago_investimento REAL DEFAULT 0,
        valor_total REAL DEFAULT 0,
        data_recebimento TEXT,
        programa_politica TEXT,
        setor_gasto TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS superavit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        esfera TEXT,
        fonte_original TEXT,
        fonte_superavit TEXT,
        saldo_total REAL DEFAULT 0,
        saldo_restante REAL DEFAULT 0,
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS ordens_compra (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conta_receber_id INTEGER,
        esfera TEXT,
        numero_conta TEXT,
        fonte TEXT,
        ficha TEXT,
        tipo_despesa TEXT,
        data_compra TEXT,
        valor_compra REAL DEFAULT 0,
        produto_servico TEXT,
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS arquivos_saude (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bloco TEXT,
        nome_arquivo TEXT,
        conteudo_texto TEXT,
        dados_arquivo BLOB,
        data_upload TEXT
    )""")

    # Migracao defensiva de colunas
    tabelas_colunas = {
        "users": ["id", "username", "password_hash", "nome"],
        "contas_receber": ["id", "esfera", "numero_conta", "fonte", "referencia_tipo", "referencia_numero", "tipo_recurso", "valor_pago_custeio", "valor_pago_investimento", "valor_total", "data_recebimento", "programa_politica", "setor_gasto"],
        "superavit": ["id", "esfera", "fonte_original", "fonte_superavit", "saldo_total", "saldo_restante", "created_at"],
        "ordens_compra": ["id", "conta_receber_id", "esfera", "numero_conta", "fonte", "ficha", "tipo_despesa", "data_compra", "valor_compra", "produto_servico", "created_at"],
        "arquivos_saude": ["id", "bloco", "nome_arquivo", "conteudo_texto", "dados_arquivo", "data_upload"],
    }
    for tabela, colunas in tabelas_colunas.items():
        c.execute(f"PRAGMA table_info({tabela})")
        existentes = [row[1] for row in c.fetchall()]
        for col in colunas:
            if col not in existentes:
                try:
                    c.execute(f"ALTER TABLE {tabela} ADD COLUMN {col} TEXT")
                except Exception:
                    pass

    # Usuario admin padrao
    c.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    if not c.fetchone():
        hash_admin = hash_senha("Diretor2025#")
        c.execute("INSERT INTO users (username, password_hash, nome) VALUES (?, ?, ?)", ("admin", hash_admin, "Administrador"))
    conn.commit()
    conn.close()

# ----------------------------- FUNCOES -----------------------------
def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def verificar_login(usuario, senha):
    conn = get_conn()
    c = conn.cursor()
    senha_hash = hash_senha(senha)
    c.execute("SELECT id, username, nome FROM users WHERE username = ? AND password_hash = ?", (usuario, senha_hash))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "username": row[1], "nome": row[2]}
    return None

def format_currency(valor):
    if valor is None:
        valor = 0
    s = f"{valor:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

def get_fonte(esfera):
    fontes = {
        "Federal": 1600,
        "Estadual": 1621,
        "Municipal": 1500,
        "Transferencia": 1700,
        "Transposicao": 1800,
    }
    return fontes.get(esfera, 0)

def get_fonte_superavit(esfera):
    fontes = {
        "Federal": 2600,
        "Estadual": 2621,
    }
    return fontes.get(esfera, 0)

ESFERAS = ["Federal", "Estadual", "Municipal", "Transferencia", "Transposicao"]

# ----------------------------- SESSAO -----------------------------
def init_session():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "page" not in st.session_state:
        st.session_state.page = "inicio"
    if "esfera_detalhe" not in st.session_state:
        st.session_state.esfera_detalhe = None

# ----------------------------- PAGINA LOGIN -----------------------------
def pagina_login():
    st.markdown("<h1 style='text-align:center; color:#60a5fa;'>MARMED</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#93c5fd;'>Sistema Integrado de Gestao Publica</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#cbd5e1; margin-bottom:30px;'>Prefeitura Municipal de Luminarias - MG</p>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            st.markdown("<h3 style='text-align:center; color:#f1f5f9;'>Login</h3>", unsafe_allow_html=True)
            usuario = st.text_input("Usuario")
            senha = st.text_input("Senha", type="password")
            if st.button("Entrar", use_container_width=True):
                user = verificar_login(usuario, senha)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.session_state.page = "inicio"
                    st.rerun()
                else:
                    st.error("Usuario ou senha invalidos.")

# ----------------------------- PAGINA INICIAL -----------------------------
def pagina_inicio():
    st.markdown("<h1 class='titulo-marmed'>MARMED</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitulo-marmed'>Sistema Integrado de Gestao Publica</p>", unsafe_allow_html=True)
    st.markdown("<p class='prefeitura-marmed'>Prefeitura Municipal de Luminarias - MG</p>", unsafe_allow_html=True)

    conn = get_conn()
    c = conn.cursor()
    valores = {}
    for esfera in ESFERAS:
        c.execute("SELECT COALESCE(SUM(valor_total), 0) FROM contas_receber WHERE esfera = ?", (esfera,))
        total = c.fetchone()[0]
        valores[esfera] = total
    conn.close()

    cols = st.columns(5)
    for i, esfera in enumerate(ESFERAS):
        with cols[i]:
            if st.button(f"{esfera}\n{format_currency(valores[esfera])}", key=f"card_{esfera}", use_container_width=True):
                st.session_state.esfera_detalhe = esfera
                st.session_state.page = "esfera_detalhe"
                st.rerun()

# ----------------------------- CADASTRO DE CONTAS -----------------------------
def pagina_cadastro_contas():
    st.markdown("<h2 style='color:#60a5fa;'>Cadastro de Contas</h2>", unsafe_allow_html=True)
    with st.form("form_conta"):
        col1, col2 = st.columns(2)
        with col1:
            esfera = st.selectbox("Esfera", ESFERAS)
            numero_conta = st.text_input("Numero da Conta")
            fonte = st.text_input("Fonte", value=str(get_fonte(esfera)))
            referencia_tipo = st.text_input("Referencia Tipo")
            referencia_numero = st.text_input("Referencia Numero")
            tipo_recurso = st.text_input("Tipo de Recurso")
        with col2:
            valor_pago_custeio = st.number_input("Valor Pago Custeio", min_value=0.0, value=0.0, step=0.01)
            valor_pago_investimento = st.number_input("Valor Pago Investimento", min_value=0.0, value=0.0, step=0.01)
            valor_total = st.number_input("Valor Total", min_value=0.0, value=0.0, step=0.01)
            data_recebimento = st.date_input("Data de Recebimento", value=date.today())
            programa_politica = st.text_input("Programa/Politica")
            setor_gasto = st.text_input("Setor do Gasto")
        submitted = st.form_submit_button("Cadastrar Conta")
        if submitted:
            conn = get_conn()
            c = conn.cursor()
            c.execute("""INSERT INTO contas_receber
                (esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso,
                 valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento,
                 programa_politica, setor_gasto)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso,
                 float(valor_pago_custeio), float(valor_pago_investimento), float(valor_total),
                 str(data_recebimento), programa_politica, setor_gasto))
            conn.commit()
            conn.close()
            st.success("Conta cadastrada com sucesso!")

# ----------------------------- CONTAS CADASTRADAS -----------------------------
def pagina_contas_cadastradas():
    st.markdown("<h2 style='color:#60a5fa;'>Contas Cadastradas</h2>", unsafe_allow_html=True)
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM contas_receber ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    if not rows:
        st.info("Nenhuma conta cadastrada.")
        return
    dados = []
    for r in rows:
        dados.append({
            "ID": r["id"],
            "Esfera": r["esfera"],
            "Numero Conta": r["numero_conta"],
            "Fonte": r["fonte"],
            "Valor Total": format_currency(r["valor_total"]),
            "Data": r["data_recebimento"],
            "Setor": r["setor_gasto"],
        })
    st.dataframe(dados, use_container_width=True)

# ----------------------------- REALIZAR COMPRAS -----------------------------
def pagina_realizar_compras():
    st.markdown("<h2 style='color:#60a5fa;'>Realizar Compras</h2>", unsafe_allow_html=True)
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, esfera, numero_conta, fonte FROM contas_receber ORDER BY id DESC")
    contas = c.fetchall()
    conn.close()
    if not contas:
        st.info("Nenhuma conta disponivel. Cadastre contas primeiro.")
        return
    opcoes = {f"{r['id']} - {r['esfera']} - {r['numero_conta']}": r for r in contas}
    with st.form("form_compra"):
        conta_sel = st.selectbox("Conta Receber", list(opcoes.keys()))
        conta = opcoes[conta_sel]
        ficha = st.text_input("Ficha")
        tipo_despesa = st.selectbox("Tipo de Despesa", ["Custeio", "Investimento"])
        data_compra = st.date_input("Data da Compra", value=date.today())
        valor_compra = st.number_input("Valor da Compra", min_value=0.0, value=0.0, step=0.01)
        produto_servico = st.text_area("Produto/Servico")
        submitted = st.form_submit_button("Registrar Compra")
        if submitted:
            conn = get_conn()
            c = conn.cursor()
            c.execute("""INSERT INTO ordens_compra
                (conta_receber_id, esfera, numero_conta, fonte, ficha, tipo_despesa,
                 data_compra, valor_compra, produto_servico, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (conta["id"], conta["esfera"], conta["numero_conta"], conta["fonte"],
                 ficha, tipo_despesa, str(data_compra), float(valor_compra),
                 produto_servico, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            st.success("Compra registrada com sucesso!")

# ----------------------------- SUPERAVIT FINANCEIRO -----------------------------
def pagina_superavit():
    st.markdown("<h2 style='color:#60a5fa;'>Superavit Financeiro</h2>", unsafe_allow_html=True)
    with st.form("form_superavit"):
        col1, col2 = st.columns(2)
        with col1:
            esfera = st.selectbox("Esfera", ["Federal", "Estadual"])
            fonte_original = st.text_input("Fonte Original", value=str(get_fonte(esfera)))
            fonte_superavit = st.text_input("Fonte Superavit", value=str(get_fonte_superavit(esfera)))
        with col2:
            saldo_total = st.number_input("Saldo Total", min_value=0.0, value=0.0, step=0.01)
            saldo_restante = st.number_input("Saldo Restante", min_value=0.0, value=0.0, step=0.01)
        submitted = st.form_submit_button("Registrar Superavit")
        if submitted:
            conn = get_conn()
            c = conn.cursor()
            c.execute("""INSERT INTO superavit
                (esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, created_at)
                VALUES (?,?,?,?,?,?)""",
                (esfera, fonte_original, fonte_superavit, float(saldo_total),
                 float(saldo_restante), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            st.success("Superavit registrado com sucesso!")

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM superavit ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    if rows:
        st.markdown("<h3 style='color:#93c5fd;'>Superavits Registrados</h3>", unsafe_allow_html=True)
        dados = []
        for r in rows:
            dados.append({
                "ID": r["id"],
                "Esfera": r["esfera"],
                "Fonte Original": r["fonte_original"],
                "Fonte Superavit": r["fonte_superavit"],
                "Saldo Total": format_currency(r["saldo_total"]),
                "Saldo Restante": format_currency(r["saldo_restante"]),
                "Criado em": r["created_at"],
            })
        st.dataframe(dados, use_container_width=True)

# ----------------------------- UPLOAD DE ARQUIVOS -----------------------------
def pagina_upload_arquivos():
    st.markdown("<h2 style='color:#60a5fa;'>Upload de Arquivos</h2>", unsafe_allow_html=True)
    bloco = st.text_input("Bloco")
    uploaded = st.file_uploader("Selecionar Arquivo")
    if uploaded is not None and st.button("Enviar Arquivo"):
        conteudo = uploaded.read()
        try:
            texto = conteudo.decode("utf-8", errors="ignore")
        except Exception:
            texto = ""
        conn = get_conn()
        c = conn.cursor()
        c.execute("""INSERT INTO arquivos_saude
            (bloco, nome_arquivo, conteudo_texto, dados_arquivo, data_upload)
            VALUES (?,?,?,?,?)""",
            (bloco, uploaded.name, texto, conteudo,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        st.success("Arquivo enviado com sucesso!")

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, bloco, nome_arquivo, data_upload FROM arquivos_saude ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    if rows:
        st.markdown("<h3 style='color:#93c5fd;'>Arquivos Enviados</h3>", unsafe_allow_html=True)
        dados = []
        for r in rows:
            dados.append({
                "ID": r["id"],
                "Bloco": r["bloco"],
                "Nome Arquivo": r["nome_arquivo"],
                "Data Upload": r["data_upload"],
            })
        st.dataframe(dados, use_container_width=True)

# ----------------------------- TROCAR SENHA -----------------------------
def pagina_trocar_senha():
    st.markdown("<h2 style='color:#60a5fa;'>Trocar Senha</h2>", unsafe_allow_html=True)
    senha_atual = st.text_input("Senha Atual", type="password")
    nova_senha = st.text_input("Nova Senha", type="password")
    confirmar = st.text_input("Confirmar Nova Senha", type="password")
    if st.button("Trocar Senha"):
        if nova_senha != confirmar:
            st.error("As senhas nao conferem.")
            return
        user = verificar_login(st.session_state.user["username"], senha_atual)
        if not user:
            st.error("Senha atual incorreta.")
            return
        conn = get_conn()
        c = conn.cursor()
        c.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                  (hash_senha(nova_senha), st.session_state.user["id"]))
        conn.commit()
        conn.close()
        st.success("Senha alterada com sucesso!")

# ----------------------------- ESFERA DETALHE -----------------------------
def pagina_esfera_detalhe():
    esfera = st.session_state.esfera_detalhe
    st.markdown(f"<h2 style='color:#60a5fa;'>Esfera: {esfera}</h2>", unsafe_allow_html=True)
    if st.button("<- Voltar"):
        st.session_state.page = "inicio"
        st.rerun()

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM contas_receber WHERE esfera = ? ORDER BY id DESC", (esfera,))
    contas = c.fetchall()
    c.execute("SELECT COALESCE(SUM(valor_total), 0) FROM contas_receber WHERE esfera = ?", (esfera,))
    total = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(valor_compra), 0) FROM ordens_compra WHERE esfera = ?", (esfera,))
    total_compras = c.fetchone()[0]
    conn.close()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Recebido", format_currency(total))
    with col2:
        st.metric("Total Compras", format_currency(total_compras))
    with col3:
        st.metric("Saldo", format_currency(total - total_compras))

    st.markdown("<h3 style='color:#93c5fd;'>Contas desta Esfera</h3>", unsafe_allow_html=True)
    if contas:
        dados = []
        for r in contas:
            dados.append({
                "ID": r["id"],
                "Numero Conta": r["numero_conta"],
                "Fonte": r["fonte"],
                "Valor Total": format_currency(r["valor_total"]),
                "Data": r["data_recebimento"],
                "Setor": r["setor_gasto"],
            })
        st.dataframe(dados, use_container_width=True)
    else:
        st.info("Nenhuma conta cadastrada para esta esfera.")

# ----------------------------- SIDEBAR / NAVEGACAO -----------------------------
def sidebar_navegacao():
    with st.sidebar:
        st.markdown("<h3 style='color:#60a5fa;'>MARMED</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#cbd5e1;'>Usuario: {st.session_state.user['nome']}</p>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#334155;'>", unsafe_allow_html=True)
        if st.button("Inicio", use_container_width=True):
            st.session_state.page = "inicio"
            st.rerun()
        if st.button("Cadastro de Contas", use_container_width=True):
            st.session_state.page = "cadastro_contas"
            st.rerun()
        if st.button("Contas Cadastradas", use_container_width=True):
            st.session_state.page = "contas_cadastradas"
            st.rerun()
        if st.button("Realizar Compras", use_container_width=True):
            st.session_state.page = "realizar_compras"
            st.rerun()
        if st.button("Superavit Financeiro", use_container_width=True):
            st.session_state.page = "superavit"
            st.rerun()
        if st.button("Upload de Arquivos", use_container_width=True):
            st.session_state.page = "upload_arquivos"
            st.rerun()
        if st.button("Trocar Senha", use_container_width=True):
            st.session_state.page = "trocar_senha"
            st.rerun()
        st.markdown("<hr style='border-color:#334155;'>", unsafe_allow_html=True)
        if st.button("Sair", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.page = "inicio"
            st.rerun()

# ----------------------------- MAIN -----------------------------
def main():
    init_db()
    init_session()
    if not st.session_state.logged_in:
        pagina_login()
        return
    sidebar_navegacao()
    page = st.session_state.page
    if page == "inicio":
        pagina_inicio()
    elif page == "cadastro_contas":
        pagina_cadastro_contas()
    elif page == "contas_cadastradas":
        pagina_contas_cadastradas()
    elif page == "realizar_compras":
        pagina_realizar_compras()
    elif page == "superavit":
        pagina_superavit()
    elif page == "upload_arquivos":
        pagina_upload_arquivos()
    elif page == "trocar_senha":
        pagina_trocar_senha()
    elif page == "esfera_detalhe":
        pagina_esfera_detalhe()
    else:
        pagina_inicio()

if __name__ == "__main__":
    main()
