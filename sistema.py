import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime
import os
import json

# ============================================================
# CONFIGURACAO DA PAGINA
# ============================================================
st.set_page_config(page_title="MARMED - Gestao Financeira Publica", page_icon="🏛️", layout="wide")

# ============================================================
# CSS PERSONALIZADO
# ============================================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0a1f44 0%, #102a5c 50%, #0d2347 100%);
        color: #ffffff;
    }
    section[data-testid="stSidebar"] {
        background-color: #071533 !important;
        color: #ffffff;
    }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label {
        color: #ffffff !important;
    }
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stDateInput > div > div > input,
    .stSelectbox > div > div > div {
        background-color: #0f2747 !important;
        color: #ffffff !important;
        border: 1px solid #1e3a6b !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #1e60d8 0%, #0a47a8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: bold !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #2a7bff 0%, #1559c9 100%) !important;
    }
    .metric-card {
        background: rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.12);
    }
    .metric-card h3 {
        color: #7fb2ff;
        margin: 0;
        font-size: 14px;
    }
    .metric-card h1 {
        color: #ffffff;
        margin: 6px 0 0 0;
        font-size: 26px;
    }
    .esfera-card {
        background: rgba(255,255,255,0.07);
        border-radius: 14px;
        padding: 22px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.15);
        cursor: pointer;
    }
    .esfera-card h2 {
        color: #7fb2ff;
        margin: 0 0 8px 0;
        font-size: 20px;
    }
    .esfera-card p {
        color: #d6e4ff;
        margin: 0;
        font-size: 13px;
    }
    .titulo {
        color: #7fb2ff;
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .subtitulo {
        color: #cfe0ff;
        font-size: 16px;
        margin-bottom: 20px;
    }
    .stDataFrame, .stTable {
        color: #ffffff;
    }
    div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] li {
        color: #e8efff;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONEXAO COM BANCO DE DADOS
# ============================================================
DB_PATH = "marmed.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
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
        valor_pago_custeio REAL,
        valor_pago_investimento REAL,
        valor_total REAL,
        data_recebimento TEXT,
        programa_politica TEXT,
        setor_gasto TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS superavit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        esfera TEXT,
        fonte_original TEXT,
        fonte_superavit TEXT,
        saldo_total REAL,
        saldo_restante REAL,
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
        valor_compra REAL,
        produto_servico TEXT,
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS arquivos_saude (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bloco TEXT,
        nome_arquivo TEXT,
        conteudo_texto TEXT,
        dados_arquivo TEXT,
        data_upload TEXT
    )""")
    # Usuario admin padrao
    c.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    if c.fetchone() is None:
        c.execute("INSERT INTO users (username, password_hash, nome) VALUES (?, ?, ?)",
                  ("admin", hash_senha("Diretor2025#"), "Administrador"))
    conn.commit()
    conn.close()

# ============================================================
# FUNCOES UTILITARIAS
# ============================================================
def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def get_fonte(esfera):
    fontes = {
        "Federal": "1.600",
        "Estadual": "1.621",
        "Municipal": "1.500",
        "Transferencia": "1.700",
        "Transposicao": "1.800",
    }
    return fontes.get(esfera, "")

def get_fonte_superavit(esfera):
    fontes = {
        "Federal": "2.600",
        "Estadual": "2.621",
    }
    return fontes.get(esfera, "")

def format_currency(valor):
    if valor is None:
        valor = 0.0
    try:
        valor = float(valor)
    except Exception:
        valor = 0.0
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"

def parse_valor(texto):
    if texto is None:
        return 0.0
    if isinstance(texto, (int, float)):
        return float(texto)
    t = str(texto).strip()
    if t == "":
        return 0.0
    t = t.replace("R$", "").replace(" ", "")
    t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except Exception:
        return 0.0

def verificar_login(username, senha):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?",
              (username, hash_senha(senha)))
    user = c.fetchone()
    conn.close()
    return user

def trocar_senha(username, nova_senha):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET password_hash = ? WHERE username = ?",
              (hash_senha(nova_senha), username))
    conn.commit()
    conn.close()

# ============================================================
# ESFERAS
# ============================================================
ESFERAS = ["Federal", "Estadual", "Municipal", "Transferencia", "Transposicao"]

# ============================================================
# INICIALIZACAO DE ESTADO
# ============================================================
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"
if "esfera_selecionada" not in st.session_state:
    st.session_state.esfera_selecionada = None

init_db()

# ============================================================
# TELA DE LOGIN
# ============================================================
def tela_login():
    st.markdown("<div class='titulo'>🏛️ MARMED - Gestao Financeira Publica Municipal</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo'>Sistema de gestao de contas publicas, compras e superavit</div>", unsafe_allow_html=True)
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Acesso ao Sistema")
        username = st.text_input("Usuario", key="login_user")
        senha = st.text_input("Senha", type="password", key="login_senha")
        if st.button("Entrar", use_container_width=True):
            user = verificar_login(username, senha)
            if user:
                st.session_state.logado = True
                st.session_state.usuario = user["username"]
                st.session_state.pagina = "inicio"
                st.rerun()
            else:
                st.error("Usuario ou senha invalidos.")
        st.caption("Usuario padrao: admin | Senha: Diretor2025#")

# ============================================================
# SIDEBAR
# ============================================================
def sidebar():
    with st.sidebar:
        st.markdown("## 🧭 Navegacao")
        if st.button("🏠 Inicio", use_container_width=True):
            st.session_state.pagina = "inicio"
            st.session_state.esfera_selecionada = None
        if st.button("📋 Cadastrar Conta", use_container_width=True):
            st.session_state.pagina = "cadastro_contas"
        if st.button("📑 Contas Cadastradas", use_container_width=True):
            st.session_state.pagina = "contas_cadastradas"
        if st.button("🛒 Realizar Compras", use_container_width=True):
            st.session_state.pagina = "realizar_compras"
        if st.button("💰 Superavit", use_container_width=True):
            st.session_state.pagina = "superavit"
        if st.button("📤 Upload Saude", use_container_width=True):
            st.session_state.pagina = "upload"
        if st.button("🔑 Trocar Senha", use_container_width=True):
            st.session_state.pagina = "trocar_senha"
        st.markdown("---")
        st.markdown(f"**Usuario:** {st.session_state.usuario}")
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.logado = False
            st.session_state.usuario = None
            st.session_state.pagina = "inicio"
            st.rerun()

# ============================================================
# PAGINA INICIO - 5 ESFERAS
# ============================================================
def pagina_inicio():
    st.markdown("<div class='titulo'>🏠 Inicio - Esferas de Gestao</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo'>Selecione uma esfera para visualizar detalhes</div>", unsafe_allow_html=True)
    st.markdown("")

    cols = st.columns(5)
    for i, esfera in enumerate(ESFERAS):
        with cols[i]:
            fonte = get_fonte(esfera)
            st.markdown(f"""
            <div class='esfera-card'>
                <h2>{esfera}</h2>
                <p>Fonte: {fonte}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Acessar {esfera}", key=f"btn_{esfera}", use_container_width=True):
                st.session_state.esfera_selecionada = esfera
                st.session_state.pagina = "esfera_detalhe"
                st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Resumo Geral")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM contas_receber", conn)
    df_c = pd.read_sql_query("SELECT * FROM ordens_compra", conn)
    conn.close()
    total_receber = df["valor_total"].sum() if len(df) > 0 else 0.0
    total_compras = df_c["valor_compra"].sum() if len(df_c) > 0 else 0.0
    saldo = total_receber - total_compras
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='metric-card'><h3>Total a Receber</h3><h1>{format_currency(total_receber)}</h1></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><h3>Total Compras</h3><h1>{format_currency(total_compras)}</h1></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><h3>Saldo</h3><h1>{format_currency(saldo)}</h1></div>", unsafe_allow_html=True)

# ============================================================
# PAGINA ESFERA DETALHE
# ============================================================
def pagina_esfera_detalhe():
    esfera = st.session_state.esfera_selecionada
    st.markdown(f"<div class='titulo'>📌 Esfera: {esfera}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitulo'>Fonte: {get_fonte(esfera)}</div>", unsafe_allow_html=True)

    if st.button("⬅️ Voltar ao Inicio"):
        st.session_state.pagina = "inicio"
        st.session_state.esfera_selecionada = None
        st.rerun()

    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM contas_receber WHERE esfera = ?", conn, params=(esfera,))
    df_c = pd.read_sql_query("SELECT * FROM ordens_compra WHERE esfera = ?", conn, params=(esfera,))
    conn.close()

    total_receber = df["valor_total"].sum() if len(df) > 0 else 0.0
    total_compras = df_c["valor_compra"].sum() if len(df_c) > 0 else 0.0
    saldo = total_receber - total_compras

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='metric-card'><h3>Recebido</h3><h1>{format_currency(total_receber)}</h1></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><h3>Compras</h3><h1>{format_currency(total_compras)}</h1></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><h3>Saldo</h3><h1>{format_currency(saldo)}</h1></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📋 Contas desta Esfera")
    if len(df) > 0:
        df_show = df.copy()
        df_show["valor_total"] = df_show["valor_total"].apply(format_currency)
        df_show["valor_pago_custeio"] = df_show["valor_pago_custeio"].apply(format_currency)
        df_show["valor_pago_investimento"] = df_show["valor_pago_investimento"].apply(format_currency)
        st.dataframe(df_show, use_container_width=True)
    else:
        st.info("Nenhuma conta cadastrada para esta esfera.")

    st.markdown("### 🛒 Compras desta Esfera")
    if len(df_c) > 0:
        df_c_show = df_c.copy()
        df_c_show["valor_compra"] = df_c_show["valor_compra"].apply(format_currency)
        st.dataframe(df_c_show, use_container_width=True)
    else:
        st.info("Nenhuma compra registrada para esta esfera.")

# ============================================================
# PAGINA CADASTRO DE CONTAS (esfera FORA do form)
# ============================================================
def pagina_cadastro_contas():
    st.markdown("<div class='titulo'>📋 Cadastro de Contas a Receber</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo'>Selecione a esfera abaixo e depois preencha o formulario</div>", unsafe_allow_html=True)

    esfera = st.selectbox("Esfera *", ESFERAS, key="cad_esfera")
    fonte = get_fonte(esfera)
    st.info(f"Fonte definida automaticamente: **{fonte}**")

    with st.form("form_conta"):
        st.markdown("### Dados da Conta")
        numero_conta = st.text_input("Numero da Conta *")
        referencia_tipo = st.selectbox("Tipo de Referencia", ["Nota", "Processo", "Portaria", "Oficio", "Outro"])
        referencia_numero = st.text_input("Numero de Referencia")
        tipo_recurso = st.selectbox("Tipo de Recurso", ["Custeio", "Investimento", "Custeio/Investimento"])

        c1, c2 = st.columns(2)
        with c1:
            vc_txt = st.text_input("Valor Pago Custeio (R$)", value="0,00")
        with c2:
            vi_txt = st.text_input("Valor Pago Investimento (R$)", value="0,00")

        data_recebimento = st.date_input("Data de Recebimento", value=datetime.today())
        programa_politica = st.text_input("Programa / Politica")
        setor_gasto = st.text_input("Setor de Gasto")

        submitted = st.form_submit_button("💾 Cadastrar Conta", use_container_width=True)

    if submitted:
        vc = parse_valor(vc_txt)
        vi = parse_valor(vi_txt)
        vt = vc + vi
        if numero_conta.strip() == "":
            st.error("Numero da conta e obrigatorio.")
        elif vt <= 0:
            st.error("O valor total deve ser maior que zero.")
        else:
            conn = get_conn()
            c = conn.cursor()
            c.execute("""INSERT INTO contas_receber
                (esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso,
                 valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento,
                 programa_politica, setor_gasto)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
                esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso,
                vc, vi, vt, str(data_recebimento), programa_politica, setor_gasto
            ))
            conn.commit()
            conn.close()
            st.success(f"Conta cadastrada com sucesso! Valor total: {format_currency(vt)}")

# ============================================================
# PAGINA CONTAS CADASTRADAS
# ============================================================
def pagina_contas_cadastradas():
    st.markdown("<div class='titulo'>📑 Contas Cadastradas</div>", unsafe_allow_html=True)
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM contas_receber ORDER BY id DESC", conn)
    conn.close()

    filtro = st.selectbox("Filtrar por Esfera", ["Todas"] + ESFERAS)
    if filtro != "Todas":
        df = df[df["esfera"] == filtro]

    if len(df) > 0:
        df_show = df.copy()
        for col in ["valor_pago_custeio", "valor_pago_investimento", "valor_total"]:
            df_show[col] = df_show[col].apply(format_currency)
        st.dataframe(df_show, use_container_width=True)

        st.markdown("---")
        st.markdown("### Excluir Conta")
        id_del = st.number_input("ID da conta para excluir", min_value=1, step=1)
        if st.button("🗑️ Excluir Conta Selecionada"):
            conn = get_conn()
            c = conn.cursor()
            c.execute("DELETE FROM contas_receber WHERE id = ?", (int(id_del),))
            c.execute("DELETE FROM ordens_compra WHERE conta_receber_id = ?", (int(id_del),))
            conn.commit()
            conn.close()
            st.success("Conta excluida com sucesso.")
            st.rerun()
    else:
        st.info("Nenhuma conta cadastrada.")

# ============================================================
# PAGINA REALIZAR COMPRAS
# ============================================================
def pagina_realizar_compras():
    st.markdown("<div class='titulo'>🛒 Realizar Compras</div>", unsafe_allow_html=True)
    conn = get_conn()
    df_contas = pd.read_sql_query("SELECT id, esfera, numero_conta, fonte, valor_total FROM contas_receber ORDER BY id DESC", conn)
    conn.close()

    if len(df_contas) == 0:
        st.warning("Nenhuma conta cadastrada. Cadastre uma conta primeiro.")
        return

    with st.form("form_compra"):
        st.markdown("### Nova Ordem de Compra")
        opcoes = [f"{r['id']} - {r['esfera']} - Conta {r['numero_conta']}" for _, r in df_contas.iterrows()]
        escolha = st.selectbox("Conta a Receber *", opcoes)
        id_sel = int(escolha.split(" - ")[0])
        row = df_contas[df_contas["id"] == id_sel].iloc[0]

        st.info(f"Esfera: {row['esfera']} | Fonte: {row['fonte']} | Saldo Conta: {format_currency(row['valor_total'])}")

        ficha = st.text_input("Ficha *")
        tipo_despesa = st.selectbox("Tipo de Despesa", ["Custeio", "Investimento"])
        data_compra = st.date_input("Data da Compra", value=datetime.today())
        valor_compra_txt = st.text_input("Valor da Compra (R$) *", value="0,00")
        produto_servico = st.text_area("Produto / Servico")

        submitted = st.form_submit_button("💾 Registrar Compra", use_container_width=True)

    if submitted:
        valor_compra = parse_valor(valor_compra_txt)
        if ficha.strip() == "":
            st.error("Ficha e obrigatoria.")
        elif valor_compra <= 0:
            st.error("O valor da compra deve ser maior que zero.")
        else:
            conn = get_conn()
            c = conn.cursor()
            c.execute("""INSERT INTO ordens_compra
                (conta_receber_id, esfera, numero_conta, fonte, ficha, tipo_despesa,
                 data_compra, valor_compra, produto_servico, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)""", (
                id_sel, row["esfera"], row["numero_conta"], row["fonte"], ficha, tipo_despesa,
                str(data_compra), valor_compra, produto_servico, datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
            st.success(f"Compra registrada com sucesso! Valor: {format_currency(valor_compra)}")

    st.markdown("---")
    st.markdown("### 📑 Compras Registradas")
    conn = get_conn()
    df_c = pd.read_sql_query("SELECT * FROM ordens_compra ORDER BY id DESC", conn)
    conn.close()
    if len(df_c) > 0:
        df_c_show = df_c.copy()
        df_c_show["valor_compra"] = df_c_show["valor_compra"].apply(format_currency)
        st.dataframe(df_c_show, use_container_width=True)
    else:
        st.info("Nenhuma compra registrada.")

# ============================================================
# PAGINA SUPERAVIT
# ============================================================
def pagina_superavit():
    st.markdown("<div class='titulo'>💰 Superavit Financeiro</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo'>Gestao de saldos superavit por esfera</div>", unsafe_allow_html=True)

    with st.form("form_superavit"):
        st.markdown("### Cadastrar Superavit")
        esfera = st.selectbox("Esfera *", ["Federal", "Estadual"], key="sup_esfera")
        fonte_original = st.text_input("Fonte Original *", value=get_fonte(esfera))
        fonte_sup = st.text_input("Fonte Superavit *", value=get_fonte_superavit(esfera))
        saldo_total_txt = st.text_input("Saldo Total (R$) *", value="0,00")
        submitted = st.form_submit_button("💾 Cadastrar Superavit", use_container_width=True)

    if submitted:
        saldo_total = parse_valor(saldo_total_txt)
        if saldo_total <= 0:
            st.error("O saldo total deve ser maior que zero.")
        else:
            conn = get_conn()
            c = conn.cursor()
            c.execute("""INSERT INTO superavit
                (esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, created_at)
                VALUES (?,?,?,?,?,?)""", (
                esfera, fonte_original, fonte_sup, saldo_total, saldo_total, datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
            st.success(f"Superavit cadastrado: {format_currency(saldo_total)}")

    st.markdown("---")
    st.markdown("### 📊 Superavits Cadastrados")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM superavit ORDER BY id DESC", conn)
    conn.close()
    if len(df) > 0:
        df_show = df.copy()
        df_show["saldo_total"] = df_show["saldo_total"].apply(format_currency)
        df_show["saldo_restante"] = df_show["saldo_restante"].apply(format_currency)
        st.dataframe(df_show, use_container_width=True)

        st.markdown("### Atualizar Saldo Restante")
        id_upd = st.number_input("ID do superavit", min_value=1, step=1, key="sup_id_upd")
        novo_saldo_txt = st.text_input("Novo Saldo Restante (R$)", value="0,00", key="sup_novo")
        if st.button("✏️ Atualizar Saldo"):
            novo = parse_valor(novo_saldo_txt)
            if novo < 0:
                st.error("Saldo nao pode ser negativo.")
            else:
                conn = get_conn()
                c = conn.cursor()
                c.execute("UPDATE superavit SET saldo_restante = ? WHERE id = ?", (novo, int(id_upd)))
                conn.commit()
                conn.close()
                st.success("Saldo atualizado.")
                st.rerun()
    else:
        st.info("Nenhum superavit cadastrado.")

# ============================================================
# PAGINA UPLOAD SAUDE
# ============================================================
def pagina_upload():
    st.markdown("<div class='titulo'>📤 Upload de Arquivos de Saude</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitulo'>Envio de arquivos por bloco</div>", unsafe_allow_html=True)

    bloco = st.selectbox("Bloco", ["Bloco 1", "Bloco 2", "Bloco 3", "Bloco 4", "Outro"])
    arquivo = st.file_uploader("Selecione o arquivo", type=["txt", "csv", "json", "pdf", "xlsx"])

    if st.button("📤 Enviar Arquivo", use_container_width=True):
        if arquivo is None:
            st.error("Selecione um arquivo.")
        else:
            try:
                raw = arquivo.read()
                try:
                    conteudo = raw.decode("utf-8")
                except Exception:
                    conteudo = raw.decode("latin-1", errors="ignore")
                dados = json.dumps({"size": len(raw), "type": arquivo.type})
                conn = get_conn()
                c = conn.cursor()
                c.execute("""INSERT INTO arquivos_saude
                    (bloco, nome_arquivo, conteudo_texto, dados_arquivo, data_upload)
                    VALUES (?,?,?,?,?)""", (
                    bloco, arquivo.name, conteudo[:50000], dados, datetime.now().isoformat()
                ))
                conn.commit()
                conn.close()
                st.success(f"Arquivo '{arquivo.name}' enviado com sucesso para {bloco}.")
            except Exception as e:
                st.error(f"Erro ao enviar arquivo: {e}")

    st.markdown("---")
    st.markdown("### 📂 Arquivos Enviados")
    conn = get_conn()
    df = pd.read_sql_query("SELECT id, bloco, nome_arquivo, data_upload FROM arquivos_saude ORDER BY id DESC", conn)
    conn.close()
    if len(df) > 0:
        st.dataframe(df, use_container_width=True)
        id_ver = st.number_input("ID do arquivo para visualizar conteudo", min_value=1, step=1)
        if st.button("👁️ Visualizar"):
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT * FROM arquivos_saude WHERE id = ?", (int(id_ver),))
            r = c.fetchone()
            conn.close()
            if r:
                st.text_area("Conteudo", value=r["conteudo_texto"][:5000], height=300)
            else:
                st.warning("Arquivo nao encontrado.")
    else:
        st.info("Nenhum arquivo enviado.")

# ============================================================
# PAGINA TROCAR SENHA
# ============================================================
def pagina_trocar_senha():
    st.markdown("<div class='titulo'>🔑 Trocar Senha</div>", unsafe_allow_html=True)
    with st.form("form_senha"):
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirma = st.text_input("Confirmar Nova Senha", type="password")
        submitted = st.form_submit_button("🔐 Alterar Senha", use_container_width=True)

    if submitted:
        user = verificar_login(st.session_state.usuario, senha_atual)
        if user is None:
            st.error("Senha atual incorreta.")
        elif nova_senha != confirma:
            st.error("As senhas nao coincidem.")
        elif len(nova_senha) < 6:
            st.error("A nova senha deve ter no minimo 6 caracteres.")
        else:
            trocar_senha(st.session_state.usuario, nova_senha)
            st.success("Senha alterada com sucesso!")

# ============================================================
# ROTEAMENTO PRINCIPAL
# ============================================================
if not st.session_state.logado:
    tela_login()
else:
    sidebar()
    pagina = st.session_state.pagina
    if pagina == "inicio":
        pagina_inicio()
    elif pagina == "esfera_detalhe":
        pagina_esfera_detalhe()
    elif pagina == "cadastro_contas":
        pagina_cadastro_contas()
    elif pagina == "contas_cadastradas":
        pagina_contas_cadastradas()
    elif pagina == "realizar_compras":
        pagina_realizar_compras()
    elif pagina == "superavit":
        pagina_superavit()
    elif pagina == "upload":
        pagina_upload()
    elif pagina == "trocar_senha":
        pagina_trocar_senha()
    else:
        pagina_inicio()
