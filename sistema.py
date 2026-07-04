import streamlit as st
import sqlite3
import base64
import os
import hashlib
from datetime import datetime
import pandas as pd

# ============================================================
# CARREGAMENTO DE LOGO (definicoes mantidas, mas nao exibidas
# visualmente em tela_login() e pagina_inicio() por enquanto)
# ============================================================

def get_logo_base64():
    caminho = "logo.png"
    if os.path.exists(caminho):
        try:
            with open(caminho, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception:
            return None
    return None

LOGO_BASE64 = get_logo_base64()

# ============================================================
# CONFIGURACAO DO BANCO DE DADOS
# ============================================================

def init_db():
    conn = sqlite3.connect("marmed.db", check_same_thread=False)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            nome TEXT,
            perfil TEXT DEFAULT 'usuario'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS contas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            categoria TEXT,
            valor REAL,
            vencimento TEXT,
            status TEXT DEFAULT 'pendente'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            fornecedor TEXT,
            quantidade INTEGER,
            valor_unitario REAL,
            data TEXT,
            esfera TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS programas_saude (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            area TEXT,
            responsavel TEXT,
            orcamento REAL,
            status TEXT DEFAULT 'ativo'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS arquivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT,
            tamanho INTEGER,
            data_upload TEXT,
            esfera TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS plano_municipal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eixo TEXT NOT NULL,
            objetivo TEXT,
            meta TEXT,
            prazo TEXT,
            responsavel TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS conselho (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cargo TEXT,
            segmento TEXT,
            telefone TEXT,
            email TEXT
        )
    """)

    # Usuario padrao
    c.execute("SELECT * FROM usuarios WHERE usuario = ?", ("admin",))
    if not c.fetchone():
        senha_hash = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute(
            "INSERT INTO usuarios (usuario, senha, nome, perfil) VALUES (?, ?, ?, ?)",
            ("admin", senha_hash, "Administrador", "admin"),
        )

    conn.commit()
    return conn


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


# ============================================================
# ESTILOS GLOBAIS
# ============================================================

ESTILOS_GLOBAIS = """
<style>
/* ===== Reset / base ===== */
.stApp { background: #0a0e1a; }

/* ===== Aurora background ===== */
.aurora-bg {
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    z-index: 0; overflow: hidden; pointer-events: none;
}
.aurora-blob {
    position: absolute; border-radius: 50%; filter: blur(90px); opacity: 0.45;
}
.aurora-blob.b1 { width: 480px; height: 480px; background: #00d4ff; top: -120px; left: -100px; animation: float1 12s ease-in-out infinite; }
.aurora-blob.b2 { width: 420px; height: 420px; background: #7b2ff7; bottom: -120px; right: -80px; animation: float2 14s ease-in-out infinite; }
.aurora-blob.b3 { width: 360px; height: 360px; background: #ff2d75; top: 40%; left: 50%; animation: float3 16s ease-in-out infinite; }
@keyframes float1 { 0%,100% { transform: translate(0,0); } 50% { transform: translate(60px,40px); } }
@keyframes float2 { 0%,100% { transform: translate(0,0); } 50% { transform: translate(-50px,-30px); } }
@keyframes float3 { 0%,100% { transform: translate(-50%,-50%); } 50% { transform: translate(-30%,-60%); } }

/* ===== Login card (glassmorphism) ===== */
.login-card {
    position: relative; z-index: 10;
    max-width: 460px; margin: 80px auto 0 auto;
    padding: 50px 44px;
    background: rgba(255,255,255,0.07);
    backdrop-filter: blur(22px); -webkit-backdrop-filter: blur(22px);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 24px;
    box-shadow: 0 24px 70px rgba(0,0,0,0.45);
}
.login-title {
    font-size: 84px;
    font-weight: 800;
    letter-spacing: 6px;
    text-align: center;
    margin: 0 0 6px 0;
    background: linear-gradient(135deg, #00d4ff, #7b2ff7, #ff2d75);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.05;
}
.login-subtitle {
    text-align: center; color: rgba(255,255,255,0.6);
    font-size: 15px; letter-spacing: 2px; margin-bottom: 30px;
    text-transform: uppercase;
}

/* ===== Inicio - cabecalho ===== */
.mm-brand-title {
    font-size: 96px;
    font-weight: 800;
    letter-spacing: 8px;
    text-align: center;
    margin: 0 0 8px 0;
    background: linear-gradient(135deg, #00d4ff, #7b2ff7, #ff2d75);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1.05;
}
.mm-brand-subtitle {
    font-size: 34px;
    font-weight: 600;
    text-align: center;
    color: rgba(255,255,255,0.85);
    margin: 0 0 6px 0;
    letter-spacing: 3px;
}
.mm-brand-institution {
    font-size: 24px;
    font-weight: 400;
    text-align: center;
    color: rgba(255,255,255,0.5);
    margin: 0 0 40px 0;
    letter-spacing: 2px;
}

/* ===== Esferas clicaveis ===== */
.esferas-grid {
    display: flex; flex-wrap: wrap; justify-content: center;
    gap: 28px; margin-top: 20px;
}
.esfera-card {
    width: 200px; height: 200px; border-radius: 50%;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    cursor: pointer; transition: transform 0.3s ease, box-shadow 0.3s ease;
    text-decoration: none; color: #fff;
    box-shadow: 0 12px 40px rgba(0,0,0,0.4);
}
.esfera-card:hover {
    transform: scale(1.08);
    box-shadow: 0 18px 55px rgba(0,0,0,0.55);
}
.esfera-card .esfera-icon { font-size: 52px; margin-bottom: 8px; }
.esfera-card .esfera-label { font-size: 16px; font-weight: 600; text-align: center; padding: 0 10px; }
.esfera-1 { background: linear-gradient(135deg, #00d4ff, #0066ff); }
.esfera-2 { background: linear-gradient(135deg, #7b2ff7, #b347ff); }
.esfera-3 { background: linear-gradient(135deg, #ff2d75, #ff6b6b); }
.esfera-4 { background: linear-gradient(135deg, #00e8a0, #00b377); }
.esfera-5 { background: linear-gradient(135deg, #ffa600, #ff6b00); }

/* ===== Titulos de pagina ===== */
.page-title {
    font-size: 38px; font-weight: 700; color: #fff;
    margin-bottom: 24px; letter-spacing: 1px;
}
.section-title {
    font-size: 22px; font-weight: 600; color: rgba(255,255,255,0.9);
    margin: 20px 0 12px 0;
}

/* ===== Menu lateral ===== */
.nav-section-label {
    font-size: 11px; text-transform: uppercase; letter-spacing: 2px;
    color: rgba(255,255,255,0.4); margin: 18px 0 8px 6px; font-weight: 700;
}
</style>
"""


# ============================================================
# TELA DE LOGIN
# ============================================================

def tela_login():
    st.markdown(ESTILOS_GLOBAIS, unsafe_allow_html=True)

    st.markdown('<div class="aurora-bg"><div class="aurora-blob b1"></div><div class="aurora-blob b2"></div><div class="aurora-blob b3"></div></div>', unsafe_allow_html=True)

    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<h1 class="login-title">MARMED</h1>', unsafe_allow_html=True)
    st.markdown('<p class="login-subtitle">Gestao Publica Municipal</p>', unsafe_allow_html=True)

    col_spacer = st.columns([1, 3, 1])
    with col_spacer[1]:
        usuario = st.text_input("Usuario", key="login_usuario", label_visibility="collapsed", placeholder="Usuario")
        senha = st.text_input("Senha", type="password", key="login_senha", label_visibility="collapsed", placeholder="Senha")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("Entrar", key="btn_entrar", use_container_width=True):
            conn = init_db()
            c = conn.cursor()
            senha_hash = hash_senha(senha)
            c.execute("SELECT * FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, senha_hash))
            user = c.fetchone()
            if user:
                st.session_state["logado"] = True
                st.session_state["usuario"] = usuario
                st.session_state["nome"] = user[3] if user[3] else usuario
                st.session_state["perfil"] = user[4] if user[4] else "usuario"
                st.session_state["pagina"] = "Inicio"
                st.rerun()
            else:
                st.error("Usuario ou senha invalidos.")

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# MENU LATERAL
# ============================================================

def menu_lateral():
    with st.sidebar:
        st.markdown("<div class='nav-section-label'>Aba de Navegacao</div>", unsafe_allow_html=True)

        paginas = [
            "Inicio",
            "Cadastro de Contas",
            "Contas Cadastradas",
            "Realizar Compras",
            "Superavit",
            "Programas de Saude",
            "Upload de Arquivos",
            "Plano Municipal",
            "Norte da Gestao",
            "Conselho",
            "Trocar Senha",
        ]

        escolha = st.radio("Navegacao", paginas, key="nav_radio", label_visibility="collapsed")
        st.session_state["pagina"] = escolha

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color:rgba(255,255,255,0.1)'>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:rgba(255,255,255,0.5);font-size:13px'>Usuario: <b>{st.session_state.get('nome','')}</b></p>", unsafe_allow_html=True)

        if st.button("Sair", key="btn_sair", use_container_width=True):
            st.session_state["logado"] = False
            st.session_state["pagina"] = "Inicio"
            st.rerun()


# ============================================================
# PAGINA INICIO
# ============================================================

ESFERAS = [
    {"id": 1, "nome": "Saude", "icone": "\u2695", "classe": "esfera-1"},
    {"id": 2, "nome": "Educacao", "icone": "\u270D", "classe": "esfera-2"},
    {"id": 3, "nome": "Assistencia Social", "icone": "\u2764", "classe": "esfera-3"},
    {"id": 4, "nome": "Infraestrutura", "icone": "\u26CF", "classe": "esfera-4"},
    {"id": 5, "nome": "Administracao", "icone": "\u2696", "classe": "esfera-5"},
]


def pagina_inicio():
    st.markdown(ESTILOS_GLOBAIS, unsafe_allow_html=True)

    st.markdown('<h1 class="mm-brand-title">MARMED</h1>', unsafe_allow_html=True)
    st.markdown('<h2 class="mm-brand-subtitle">Gestao Publica Municipal</h2>', unsafe_allow_html=True)
    st.markdown('<p class="mm-brand-institution">Sistema Integrado de Gestao</p>', unsafe_allow_html=True)

    st.markdown('<div class="esferas-grid">', unsafe_allow_html=True)
    cols = st.columns(5)
    for i, esfera in enumerate(ESFERAS):
        with cols[i]:
            if st.button(f"{esfera['icone']}\n{esfera['nome']}", key=f"esfera_{esfera['id']}", use_container_width=True):
                st.session_state["esfera_ativa"] = esfera["id"]
                st.session_state["pagina"] = "Esfera Detalhe"
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:rgba(255,255,255,0.4);font-size:14px'>Clique em uma esfera para acessar os detalhes.</p>", unsafe_allow_html=True)


# ============================================================
# ESFERA DETALHE
# ============================================================

def esfera_detalhe():
    esfera_id = st.session_state.get("esfera_ativa", 1)
    esfera = next((e for e in ESFERAS if e["id"] == esfera_id), ESFERAS[0])

    st.markdown(f"<h1 class='page-title'>{esfera['icone']} {esfera['nome']}</h1>", unsafe_allow_html=True)

    if st.button("\u2190 Voltar para Inicio", key="btn_voltar_esfera"):
        st.session_state["pagina"] = "Inicio"
        st.rerun()

    st.markdown(f"<div style='height:20px'></div>", unsafe_allow_html=True)

    st.markdown(f"<h3 class='section-title'>Resumo - {esfera['nome']}</h3>", unsafe_allow_html=True)

    conn = init_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*), COALESCE(SUM(valor),0) FROM contas")
    total_contas = c.fetchone()
    c.execute("SELECT COUNT(*), COALESCE(SUM(quantidade * valor_unitario),0) FROM compras WHERE esfera = ?", (esfera["nome"],))
    total_compras = c.fetchone()
    c.execute("SELECT COUNT(*) FROM arquivos WHERE esfera = ?", (esfera["nome"],))
    total_arquivos = c.fetchone()

    col1, col2, col3 = st.columns(3)
    col1.metric("Contas Cadastradas", total_contas[0])
    col2.metric("Compras nesta Esfera", total_compras[0])
    col3.metric("Arquivos desta Esfera", total_arquivos[0])

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown("<h3 class='section-title'>Acoes Rápidas</h3>", unsafe_allow_html=True)

    acoes = st.columns(3)
    with acoes[0]:
        if st.button("Cadastrar Conta", key="act_conta"):
            st.session_state["pagina"] = "Cadastro de Contas"
            st.rerun()
    with acoes[1]:
        if st.button("Realizar Compra", key="act_compra"):
            st.session_state["pagina"] = "Realizar Compras"
            st.rerun()
    with acoes[2]:
        if st.button("Upload de Arquivo", key="act_upload"):
            st.session_state["pagina"] = "Upload de Arquivos"
            st.rerun()


# ============================================================
# CADASTRO DE CONTAS
# ============================================================

def cadastro_contas():
    st.markdown("<h1 class='page-title'>\u270D Cadastro de Contas</h1>", unsafe_allow_html=True)

    with st.form("form_conta"):
        descricao = st.text_input("Descricao da Conta")
        categoria = st.selectbox("Categoria", ["Saude", "Educacao", "Assistencia Social", "Infraestrutura", "Administracao", "Outros"])
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        vencimento = st.date_input("Vencimento")
        status = st.selectbox("Status", ["pendente", "paga", "atrasada"])
        submitted = st.form_submit_button("Cadastrar Conta")

    if submitted:
        if descricao.strip() == "":
            st.error("Informe a descricao da conta.")
        else:
            conn = init_db()
            c = conn.cursor()
            c.execute(
                "INSERT INTO contas (descricao, categoria, valor, vencimento, status) VALUES (?, ?, ?, ?, ?)",
                (descricao, categoria, valor, str(vencimento), status),
            )
            conn.commit()
            st.success("Conta cadastrada com sucesso!")


# ============================================================
# CONTAS CADASTRADAS
# ============================================================

def contas_cadastradas():
    st.markdown("<h1 class='page-title'>\u2709 Contas Cadastradas</h1>", unsafe_allow_html=True)

    conn = init_db()
    df = pd.read_sql_query("SELECT id, descricao, categoria, valor, vencimento, status FROM contas ORDER BY id DESC", conn)

    if df.empty:
        st.info("Nenhuma conta cadastrada ainda.")
    else:
        st.dataframe(df, use_container_width=True)

        st.markdown("<h3 class='section-title'>Resumo Financeiro</h3>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Contas", len(df))
        col2.metric("Valor Total", f"R$ {df['valor'].sum():.2f}")
        col3.metric("Pendentes", len(df[df["status"] == "pendente"]))

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        conta_id = st.selectbox("Selecionar conta para remover", df["id"].tolist(), format_func=lambda x: f"ID {x}")
        if st.button("Remover Conta", key="btn_remover_conta"):
            c = conn.cursor()
            c.execute("DELETE FROM contas WHERE id = ?", (conta_id,))
            conn.commit()
            st.success("Conta removida.")
            st.rerun()


# ============================================================
# REALIZAR COMPRAS
# ============================================================

def realizar_compras():
    st.markdown("<h1 class='page-title'>\u26CF Realizar Compras</h1>", unsafe_allow_html=True)

    esferas_nomes = [e["nome"] for e in ESFERAS]

    with st.form("form_compra"):
        item = st.text_input("Item")
        fornecedor = st.text_input("Fornecedor")
        quantidade = st.number_input("Quantidade", min_value=1, step=1)
        valor_unitario = st.number_input("Valor Unitario (R$)", min_value=0.0, format="%.2f")
        esfera = st.selectbox("Esfera", esferas_nomes)
        data = st.date_input("Data da Compra")
        submitted = st.form_submit_button("Registrar Compra")

    if submitted:
        if item.strip() == "":
            st.error("Informe o item da compra.")
        else:
            conn = init_db()
            c = conn.cursor()
            c.execute(
                "INSERT INTO compras (item, fornecedor, quantidade, valor_unitario, data, esfera) VALUES (?, ?, ?, ?, ?, ?)",
                (item, fornecedor, int(quantidade), valor_unitario, str(data), esfera),
            )
            conn.commit()
            st.success("Compra registrada com sucesso!")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown("<h3 class='section-title'>Compras Recentes</h3>", unsafe_allow_html=True)
    conn = init_db()
    df = pd.read_sql_query("SELECT id, item, fornecedor, quantidade, valor_unitario, data, esfera FROM compras ORDER BY id DESC LIMIT 20", conn)
    if df.empty:
        st.info("Nenhuma compra registrada.")
    else:
        df["valor_total"] = df["quantidade"] * df["valor_unitario"]
        st.dataframe(df, use_container_width=True)


# ============================================================
# SUPERAVIT
# ============================================================

def superavit():
    st.markdown("<h1 class='page-title'>\u2696 Superavit</h1>", unsafe_allow_html=True)

    conn = init_db()
    c = conn.cursor()

    c.execute("SELECT COALESCE(SUM(valor),0) FROM contas WHERE status = 'paga'")
    despesas = c.fetchone()[0]

    c.execute("SELECT COALESCE(SUM(quantidade * valor_unitario),0) FROM compras")
    compras_total = c.fetchone()[0]

    receita = st.number_input("Receita Total Prevista (R$)", min_value=0.0, value=100000.0, format="%.2f", key="receita_superavit")

    total_despesas = despesas + compras_total
    resultado = receita - total_despesas

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Receita Prevista", f"R$ {receita:.2f}")
    col2.metric("Total de Despesas", f"R$ {total_despesas:.2f}")
    col3.metric("Resultado (Superavit/Deficit)", f"R$ {resultado:.2f}")

    if resultado >= 0:
        st.success(f"Superavit de R$ {resultado:.2f}")
    else:
        st.error(f"Deficit de R$ {abs(resultado):.2f}")


# ============================================================
# PROGRAMAS DE SAUDE
# ============================================================

def programas_saude():
    st.markdown("<h1 class='page-title'>\u2695 Programas de Saude</h1>", unsafe_allow_html=True)

    with st.form("form_programa"):
        nome = st.text_input("Nome do Programa")
        area = st.selectbox("Area", ["Atencao Basica", "Vigilancia em Saude", "Saude Mental", "Saude da Mulher", "Saude da Crianca", "Outros"])
        responsavel = st.text_input("Responsavel")
        orcamento = st.number_input("Orcamento (R$)", min_value=0.0, format="%.2f")
        status = st.selectbox("Status", ["ativo", "planejado", "encerrado"])
        submitted = st.form_submit_button("Cadastrar Programa")

    if submitted:
        if nome.strip() == "":
            st.error("Informe o nome do programa.")
        else:
            conn = init_db()
            c = conn.cursor()
            c.execute(
                "INSERT INTO programas_saude (nome, area, responsavel, orcamento, status) VALUES (?, ?, ?, ?, ?)",
                (nome, area, responsavel, orcamento, status),
            )
            conn.commit()
            st.success("Programa cadastrado com sucesso!")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown("<h3 class='section-title'>Programas Cadastrados</h3>", unsafe_allow_html=True)
    conn = init_db()
    df = pd.read_sql_query("SELECT id, nome, area, responsavel, orcamento, status FROM programas_saude ORDER BY id DESC", conn)
    if df.empty:
        st.info("Nenhum programa cadastrado.")
    else:
        st.dataframe(df, use_container_width=True)


# ============================================================
# UPLOAD DE ARQUIVOS
# ============================================================

def upload_arquivos():
    st.markdown("<h1 class='page-title'>\u2191 Upload de Arquivos</h1>", unsafe_allow_html=True)

    esferas_nomes = [e["nome"] for e in ESFERAS]
    esfera = st.selectbox("Esfera relacionada", esferas_nomes, key="upload_esfera")
    arquivo = st.file_uploader("Selecione o arquivo", type=["pdf", "docx", "xlsx", "csv", "png", "jpg", "jpeg", "txt"])

    if st.button("Registrar Upload", key="btn_upload"):
        if arquivo is not None:
            conn = init_db()
            c = conn.cursor()
            c.execute(
                "INSERT INTO arquivos (nome, tipo, tamanho, data_upload, esfera) VALUES (?, ?, ?, ?, ?)",
                (arquivo.name, arquivo.type, len(arquivo.getvalue()), datetime.now().strftime("%Y-%m-%d %H:%M"), esfera),
            )
            conn.commit()
            st.success(f"Arquivo '{arquivo.name}' registrado para a esfera {esfera}.")
        else:
            st.warning("Selecione um arquivo primeiro.")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown("<h3 class='section-title'>Arquivos Registrados</h3>", unsafe_allow_html=True)
    conn = init_db()
    df = pd.read_sql_query("SELECT id, nome, tipo, tamanho, data_upload, esfera FROM arquivos ORDER BY id DESC", conn)
    if df.empty:
        st.info("Nenhum arquivo registrado.")
    else:
        st.dataframe(df, use_container_width=True)


# ============================================================
# PLANO MUNICIPAL
# ============================================================

def plano_municipal():
    st.markdown("<h1 class='page-title'>\u270D Plano Municipal</h1>", unsafe_allow_html=True)

    with st.form("form_plano"):
        eixo = st.text_input("Eixo")
        objetivo = st.text_area("Objetivo")
        meta = st.text_area("Meta")
        prazo = st.date_input("Prazo")
        responsavel = st.text_input("Responsavel")
        submitted = st.form_submit_button("Adicionar ao Plano")

    if submitted:
        if eixo.strip() == "":
            st.error("Informe o eixo.")
        else:
            conn = init_db()
            c = conn.cursor()
            c.execute(
                "INSERT INTO plano_municipal (eixo, objetivo, meta, prazo, responsavel) VALUES (?, ?, ?, ?, ?)",
                (eixo, objetivo, meta, str(prazo), responsavel),
            )
            conn.commit()
            st.success("Item adicionado ao plano municipal.")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown("<h3 class='section-title'>Itens do Plano</h3>", unsafe_allow_html=True)
    conn = init_db()
    df = pd.read_sql_query("SELECT id, eixo, objetivo, meta, prazo, responsavel FROM plano_municipal ORDER BY id DESC", conn)
    if df.empty:
        st.info("Nenhum item no plano municipal.")
    else:
        st.dataframe(df, use_container_width=True)


# ============================================================
# NORTE DA GESTAO
# ============================================================

def norte_gestao():
    st.markdown("<h1 class='page-title'>\u2605 Norte da Gestao</h1>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);
    border-radius:16px;padding:30px;color:rgba(255,255,255,0.8);font-size:16px;line-height:1.8'>
    <h3 style='color:#00d4ff;margin-bottom:16px'>Principios e Diretrizes</h3>
    <p><b>Transparencia:</b> Garantir acesso a informacoes publicas de forma clara e acessivel.</p>
    <p><b>Eficiencia:</b> Otimizar recursos publicos para maximo impacto social.</p>
    <p><b>Participacao:</b> Envolver a comunidade nas decisoes municipais.</p>
    <p><b>Sustentabilidade:</b> Promover desenvolvimento ambientalmente responsavel.</p>
    <p><b>Equidade:</b> Assegurar servicos de qualidade para toda a populacao.</p>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# CONSELHO
# ============================================================

def conselho():
    st.markdown("<h1 class='page-title'>\u2696 Conselho</h1>", unsafe_allow_html=True)

    with st.form("form_conselho"):
        nome = st.text_input("Nome do Membro")
        cargo = st.text_input("Cargo")
        segmento = st.selectbox("Segmento", ["Governo", "Sociedade Civil", "Trabalhadores", "Empregadores", "Outros"])
        telefone = st.text_input("Telefone")
        email = st.text_input("E-mail")
        submitted = st.form_submit_button("Cadastrar Membro")

    if submitted:
        if nome.strip() == "":
            st.error("Informe o nome do membro.")
        else:
            conn = init_db()
            c = conn.cursor()
            c.execute(
                "INSERT INTO conselho (nome, cargo, segmento, telefone, email) VALUES (?, ?, ?, ?, ?)",
                (nome, cargo, segmento, telefone, email),
            )
            conn.commit()
            st.success("Membro cadastrado no conselho.")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown("<h3 class='section-title'>Membros do Conselho</h3>", unsafe_allow_html=True)
    conn = init_db()
    df = pd.read_sql_query("SELECT id, nome, cargo, segmento, telefone, email FROM conselho ORDER BY id DESC", conn)
    if df.empty:
        st.info("Nenhum membro cadastrado.")
    else:
        st.dataframe(df, use_container_width=True)


# ============================================================
# TROCAR SENHA
# ============================================================

def trocar_senha():
    st.markdown("<h1 class='page-title'>\u2709 Trocar Senha</h1>", unsafe_allow_html=True)

    usuario = st.session_state.get("usuario", "")
    senha_atual = st.text_input("Senha Atual", type="password")
    nova_senha = st.text_input("Nova Senha", type="password")
    confirmar = st.text_input("Confirmar Nova Senha", type="password")

    if st.button("Alterar Senha", key="btn_trocar_senha"):
        if not senha_atual or not nova_senha or not confirmar:
            st.error("Preencha todos os campos.")
        elif nova_senha != confirmar:
            st.error("A nova senha e a confirmacao nao coincidem.")
        else:
            conn = init_db()
            c = conn.cursor()
            c.execute("SELECT * FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, hash_senha(senha_atual)))
            if not c.fetchone():
                st.error("Senha atual incorreta.")
            else:
                c.execute("UPDATE usuarios SET senha = ? WHERE usuario = ?", (hash_senha(nova_senha), usuario))
                conn.commit()
                st.success("Senha alterada com sucesso!")


# ============================================================
# MAIN
# ============================================================

def main():
    st.set_page_config(page_title="MARMED - Gestao Publica Municipal", page_icon="\u2695", layout="wide")

    if "logado" not in st.session_state:
        st.session_state["logado"] = False
    if "pagina" not in st.session_state:
        st.session_state["pagina"] = "Inicio"

    if not st.session_state["logado"]:
        tela_login()
        return

    menu_lateral()

    pagina = st.session_state.get("pagina", "Inicio")

    if pagina == "Inicio":
        pagina_inicio()
    elif pagina == "Esfera Detalhe":
        esfera_detalhe()
    elif pagina == "Cadastro de Contas":
        cadastro_contas()
    elif pagina == "Contas Cadastradas":
        contas_cadastradas()
    elif pagina == "Realizar Compras":
        realizar_compras()
    elif pagina == "Superavit":
        superavit()
    elif pagina == "Programas de Saude":
        programas_saude()
    elif pagina == "Upload de Arquivos":
        upload_arquivos()
    elif pagina == "Plano Municipal":
        plano_municipal()
    elif pagina == "Norte da Gestao":
        norte_gestao()
    elif pagina == "Conselho":
        conselho()
    elif pagina == "Trocar Senha":
        trocar_senha()
    else:
        pagina_inicio()


if __name__ == "__main__":
    main()
