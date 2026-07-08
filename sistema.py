import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, date
import os

st.set_page_config(page_title="MARMED - Gestao Inteligente de Saude Municipal", page_icon="🏥", layout="wide", initial_sidebar_state="expanded")

DB_PATH = "marmed.db"

# ===================== CSS =====================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0a1628 0%, #0f1f3d 50%, #0a1628 100%);
    color: #e2e8f0;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a1628 0%, #0f1f3d 100%);
    border-right: 1px solid rgba(255,255,255,0.08);
}

section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span {
    color: #b3c5e8 !important;
}

.main-title {
    font-size: 140px;
    font-weight: 900;
    color: #f0f4ff;
    text-align: center;
    letter-spacing: -4px;
    line-height: 1;
    margin: 0;
    text-shadow: 0 0 60px rgba(96,165,250,0.3);
}

.login-title {
    font-size: 120px;
    font-weight: 900;
    color: #f0f4ff;
    text-align: center;
    letter-spacing: -3px;
    line-height: 1;
    margin: 0;
    text-shadow: 0 0 60px rgba(96,165,250,0.3);
}

.subtitle {
    font-size: 22px;
    color: #93a3c4;
    text-align: center;
    font-weight: 400;
    margin-top: 10px;
    letter-spacing: 2px;
}

.card-container {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    transition: all 0.3s ease;
}

.card-container:hover {
    border-color: #60a5fa;
    background: rgba(96,165,250,0.08);
}

.card-title {
    font-size: 18px;
    font-weight: 700;
    color: #f0f4ff;
    margin-bottom: 8px;
    letter-spacing: 1px;
}

.card-value {
    font-size: 28px;
    font-weight: 800;
    color: #b3d4ff;
    margin: 10px 0;
}

.card-label {
    font-size: 13px;
    color: #93a3c4;
}

.badge {
    display: inline-block;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1px;
    background: rgba(96,165,250,0.15);
    border: 1px solid rgba(96,165,250,0.3);
    color: #60a5fa;
    margin: 4px;
}

.section-title {
    font-size: 32px;
    font-weight: 800;
    color: #f0f4ff;
    margin-bottom: 8px;
}

.section-subtitle {
    font-size: 16px;
    color: #93a3c4;
    margin-bottom: 24px;
}

.stButton > button {
    background: linear-gradient(135deg, #1a56db 0%, #1e40af 100%);
    color: #ffffff;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    padding: 10px 24px;
    transition: all 0.3s ease;
    width: 100%;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
    border-color: #60a5fa;
    box-shadow: 0 0 20px rgba(96,165,250,0.3);
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div {
    background: #1a2744 !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stNumberInput > div > div > input:focus {
    border-color: #60a5fa !important;
    box-shadow: 0 0 0 2px rgba(96,165,250,0.2) !important;
}

.stSelectbox > div > div > div {
    background: #1a2744 !important;
}

div[data-bare="true"] [role="listbox"],
.stSelectbox [role="option"],
.stMultiSelect [role="option"] {
    background: #1a2744 !important;
    color: #e2e8f0 !important;
}

.stSelectbox [role="option"]:hover,
.stMultiSelect [role="option"]:hover {
    background: #253a5c !important;
}

label, .stForm label, .stMarkdown label {
    color: #b3c5e8 !important;
}

.stTabs [data-baseline="true"] {
    background: transparent;
}

.stTabs .stTabsTabButton {
    color: rgba(255,255,255,0.5) !important;
    border-bottom: 3px solid rgba(255,255,255,0.15) !important;
}

.stTabs .stTabsTabButton[data-active="true"] {
    color: #60a5fa !important;
    border-bottom: 3px solid #60a5fa !important;
}

.stTabs [data-active="true"] {
    background: transparent;
}

.stDataFrame {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
}

.stExpander {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
}

.stExpander > details > summary {
    color: #b3c5e8;
}

hr {
    border-color: rgba(255,255,255,0.08);
}

.stAlert {
    border-radius: 10px;
}

.stMetric {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 16px;
}

.stMetric label {
    color: #93a3c4 !important;
}

.stMetric [data-testid="stMetricValue"] {
    color: #b3d4ff !important;
}

.divider {
    height: 1px;
    background: rgba(255,255,255,0.08);
    margin: 20px 0;
}

.login-box {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 40px;
    max-width: 420px;
    margin: 0 auto;
}

.value-text {
    color: #b3d4ff;
    font-weight: 700;
}

.accent {
    color: #60a5fa;
}

.stFileUploader {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px;
    padding: 16px;
}

.stSidebar .stButton > button {
    background: transparent;
    border: 1px solid rgba(255,255,255,0.1);
}

.stSidebar .stButton > button:hover {
    background: rgba(96,165,250,0.1);
    border-color: #60a5fa;
}

div[data-testid="stSidebarUserContent"] {
    padding-top: 20px;
}

.stForm {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 24px;
}

.stDateInput > div > div > input {
    background: #1a2744 !important;
    color: #e2e8f0 !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
}

.stDateInput [data-bare="true"] {
    background: #1a2744 !important;
}

.stAlert > div {
    background: rgba(96,165,250,0.1) !important;
    border: 1px solid rgba(96,165,250,0.3) !important;
    color: #b3d4ff !important;
}

.stAlert[data-testid="stAlert"] {
    background: rgba(96,165,250,0.1) !important;
}
</style>
""", unsafe_allow_html=True)

# ===================== FUNCOES UTILITARIAS =====================
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def verificar_login(username, senha):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash, nome FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    if row["password_hash"] == hash_senha(senha):
        return {"id": row["id"], "username": row["username"], "nome": row["nome"]}
    return None

def format_currency(valor):
    if valor is None:
        valor = 0
    valor = float(valor)
    s = f"{valor:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

def get_fonte(esfera):
    fontes = {
        "Federal": "1.600",
        "Estadual": "1.621",
        "Municipal": "1.500",
        "Transferencia": "1.700",
        "Transposicao": "1.800"
    }
    return fontes.get(esfera, "")

ESFERAS = ["Federal", "Estadual", "Municipal", "Transferencia", "Transposicao"]

# ===================== INICIALIZACAO DE ESTADO =====================
def init_state():
    if "logado" not in st.session_state:
        st.session_state.logado = False
    if "usuario" not in st.session_state:
        st.session_state.usuario = None
    if "pagina" not in st.session_state:
        st.session_state.pagina = "Inicio"
    if "esfera_detalhe" not in st.session_state:
        st.session_state.esfera_detalhe = None
    if "editando_conta" not in st.session_state:
        st.session_state.editando_conta = None

init_state()

# ===================== TELA DE LOGIN =====================
def tela_login():
    col_spacer1, col_main, col_spacer2 = st.columns([1, 2, 1])
    with col_main:
        st.markdown('<div style="margin-top: 40px;"></div>', unsafe_allow_html=True)
        st.markdown('<h1 class="login-title">MARMED</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Gestao Inteligente de Saude Municipal</p>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center; margin: 20px 0;">'
                    '<span class="badge">SEGURO</span>'
                    '<span class="badge">MODERNO</span>'
                    '<span class="badge">SUS</span>'
                    '</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown('<h3 style="color:#f0f4ff; text-align:center; margin-bottom:20px;">Acesso ao Sistema</h3>', unsafe_allow_html=True)
        username = st.text_input("Usuario", key="login_user", placeholder="Digite seu usuario")
        senha = st.text_input("Senha", type="password", key="login_pass", placeholder="Digite sua senha")
        if st.button("Entrar", key="btn_login"):
            user = verificar_login(username, senha)
            if user:
                st.session_state.logado = True
                st.session_state.usuario = user
                st.session_state.pagina = "Inicio"
                st.rerun()
            else:
                st.error("Usuario ou senha invalidos.")
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; color:#93a3c4; font-size:12px;">'
                    'Acesso restrito a servidores autorizados</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ===================== SIDEBAR =====================
def sidebar():
    with st.sidebar:
        st.markdown('<h2 style="color:#f0f4ff; font-weight:800; letter-spacing:1px;">MARMED</h2>', unsafe_allow_html=True)
        st.markdown('<p style="color:#93a3c4; font-size:13px; margin-top:-10px;">Gestao Financeira Municipal</p>', unsafe_allow_html=True)
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        if st.session_state.usuario:
            st.markdown(f'<p style="color:#b3c5e8; font-size:13px;">Usuario: <span class="accent">{st.session_state.usuario["nome"]}</span></p>', unsafe_allow_html=True)
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        opcoes = [
            "Inicio",
            "Esfera Detalhe",
            "Cadastrar Conta",
            "Contas Cadastradas",
            "Realizar Compras",
            "Superavit Financeiro",
            "Upload de Arquivos",
            "Trocar Senha"
        ]
        for op in opcoes:
            if st.button(op, key=f"menu_{op}"):
                st.session_state.pagina = op
                if op != "Esfera Detalhe":
                    st.session_state.esfera_detalhe = None
                st.rerun()
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        if st.button("Sair", key="btn_sair"):
            st.session_state.logado = False
            st.session_state.usuario = None
            st.session_state.pagina = "Inicio"
            st.rerun()

# ===================== PAGINA INICIAL =====================
def pagina_inicial():
    st.markdown('<h1 class="main-title">MARMED</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Gestao Inteligente de Saude Municipal</p>', unsafe_allow_html=True)
    st.markdown('<div style="margin: 30px 0;"></div>', unsafe_allow_html=True)
    st.markdown('<h3 class="section-title">Esferas de Financiamento</h3>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Selecione uma esfera para acessar os detalhes financeiros</p>', unsafe_allow_html=True)
    conn = get_conn()
    cur = conn.cursor()
    cols = st.columns(5)
    for i, esfera in enumerate(ESFERAS):
        cur.execute("SELECT COALESCE(SUM(valor_total),0) as total FROM contas_receber WHERE esfera = ?", (esfera,))
        row = cur.fetchone()
        total = row["total"] if row else 0
        with cols[i]:
            st.markdown(f'<div class="card-container">'
                        f'<div class="card-title">{esfera.upper()}</div>'
                        f'<div class="card-label">Fonte {get_fonte(esfera)}</div>'
                        f'<div class="card-value">{format_currency(total)}</div>'
                        f'</div>', unsafe_allow_html=True)
            if st.button("Acessar", key=f"acessar_{esfera}"):
                st.session_state.esfera_detalhe = esfera
                st.session_state.pagina = "Esfera Detalhe"
                st.rerun()
    conn.close()
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<h3 class="section-title">Resumo Geral</h3>', unsafe_allow_html=True)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(valor_total),0) as total FROM contas_receber")
    total_geral = cur.fetchone()["total"]
    cur.execute("SELECT COALESCE(SUM(valor_compra),0) as total FROM ordens_compra")
    total_compras = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) as qtd FROM contas_receber")
    qtd_contas = cur.fetchone()["qtd"]
    cur.execute("SELECT COUNT(*) as qtd FROM ordens_compra")
    qtd_compras = cur.fetchone()["qtd"]
    conn.close()
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(label="Total Recebido", value=format_currency(total_geral))
    with m2:
        st.metric(label="Total Compras", value=format_currency(total_compras))
    with m3:
        st.metric(label="Contas Cadastradas", value=str(qtd_contas))
    with m4:
        st.metric(label="Ordens de Compra", value=str(qtd_compras))

# ===================== ESFERA DETALHE =====================
def get_valor_restante(conta_id, valor_total):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(valor_compra),0) as total FROM ordens_compra WHERE conta_receber_id = ?", (conta_id,))
    gasto = cur.fetchone()["total"]
    conn.close()
    return float(valor_total) - float(gasto)

def pagina_esfera_detalhe():
    esfera = st.session_state.esfera_detalhe
    if esfera is None:
        st.markdown('<h3 class="section-title">Esfera Detalhe</h3>', unsafe_allow_html=True)
        st.info("Selecione uma esfera na pagina Inicial.")
        if st.button("Voltar ao Inicio"):
            st.session_state.pagina = "Inicio"
            st.rerun()
        return
    st.markdown(f'<h3 class="section-title">Esfera: {esfera.upper()}</h3>', unsafe_allow_html=True)
    st.markdown(f'<p class="section-subtitle">Fonte: {get_fonte(esfera)} | Contas cadastradas nesta esfera</p>', unsafe_allow_html=True)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM contas_receber WHERE esfera = ? ORDER BY id DESC", (esfera,))
    contas = cur.fetchall()
    if len(contas) == 0:
        st.info("Nenhuma conta cadastrada nesta esfera.")
        conn.close()
        if st.button("Voltar ao Inicio"):
            st.session_state.pagina = "Inicio"
            st.rerun()
        return
    for conta in contas:
        restante = get_valor_restante(conta["id"], conta["valor_total"])
        with st.expander(f"Conta {conta['numero_conta']} - {conta['fonte']} | {format_currency(conta['valor_total'])} | Restante: {format_currency(restante)}"):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<p style="color:#93a3c4; font-size:13px;">Numero da Conta</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="value-text">{conta["numero_conta"]}</p>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<p style="color:#93a3c4; font-size:13px;">Fonte</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="value-text">{conta["fonte"]}</p>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<p style="color:#93a3c4; font-size:13px;">Programa/Politica</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="value-text">{conta["programa_politica"] or "-"}</p>', unsafe_allow_html=True)
            c4, c5, c6 = st.columns(3)
            with c4:
                st.markdown(f'<p style="color:#93a3c4; font-size:13px;">Valor Total</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="value-text">{format_currency(conta["valor_total"])}</p>', unsafe_allow_html=True)
            with c5:
                st.markdown(f'<p style="color:#93a3c4; font-size:13px;">Valor Restante</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="value-text accent">{format_currency(restante)}</p>', unsafe_allow_html=True)
            with c6:
                st.markdown(f'<p style="color:#93a3c4; font-size:13px;">Data Recebimento</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="value-text">{conta["data_recebimento"] or "-"}</p>', unsafe_allow_html=True)
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown('<p style="color:#b3c5e8; font-weight:600;">Ordens de Compra</p>', unsafe_allow_html=True)
            cur.execute("SELECT * FROM ordens_compra WHERE conta_receber_id = ? ORDER BY id DESC", (conta["id"],))
            compras = cur.fetchall()
            if len(compras) == 0:
                st.markdown('<p style="color:#93a3c4; font-size:13px;">Nenhuma compra registrada.</p>', unsafe_allow_html=True)
            else:
                dados = []
                for c in compras:
                    dados.append({
                        "Ficha": c["ficha"],
                        "Tipo Despesa": c["tipo_despesa"],
                        "Data": c["data_compra"],
                        "Produto/Servico": c["produto_servico"],
                        "Valor": format_currency(c["valor_compra"])
                    })
                st.dataframe(pd.DataFrame(dados), use_container_width=True, hide_index=True)
    conn.close()
    if st.button("Voltar ao Inicio"):
        st.session_state.pagina = "Inicio"
        st.rerun()

# ===================== CADASTRAR CONTA =====================
def pagina_cadastrar_conta():
    st.markdown('<h3 class="section-title">Cadastrar Conta a Receber</h3>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Preencha os dados da conta</p>', unsafe_allow_html=True)
    editando = st.session_state.editando_conta is not None
    with st.form("form_conta"):
        esfera = st.selectbox("Esfera", ESFERAS, index=ESFERAS.index(st.session_state.editando_conta["esfera"]) if editando else 0)
        fonte = get_fonte(esfera)
        st.markdown(f'<p style="color:#b3c5e8;">Fonte (automatica): <span class="accent">{fonte}</span></p>', unsafe_allow_html=True)
        numero_conta = st.text_input("Numero da Conta", value=st.session_state.editando_conta["numero_conta"] if editando else "")
        referencia_tipo = st.text_input("Tipo de Referencia", value=st.session_state.editando_conta["referencia_tipo"] if editando else "")
        referencia_numero = st.text_input("Numero de Referencia", value=st.session_state.editando_conta["referencia_numero"] if editando else "")
        tipo_recurso = st.text_input("Tipo de Recurso", value=st.session_state.editando_conta["tipo_recurso"] if editando else "")
        valor_pago_custeio = st.number_input("Valor Pago Custeio", min_value=0.0, value=float(st.session_state.editando_conta["valor_pago_custeio"]) if editando and st.session_state.editando_conta["valor_pago_custeio"] else 0.0, format="%.2f")
        valor_pago_investimento = st.number_input("Valor Pago Investimento", min_value=0.0, value=float(st.session_state.editando_conta["valor_pago_investimento"]) if editando and st.session_state.editando_conta["valor_pago_investimento"] else 0.0, format="%.2f")
        valor_total = st.number_input("Valor Total", min_value=0.0, value=float(st.session_state.editando_conta["valor_total"]) if editando and st.session_state.editando_conta["valor_total"] else 0.0, format="%.2f")
        data_recebimento = st.text_input("Data de Recebimento (AAAA-MM-DD)", value=st.session_state.editando_conta["data_recebimento"] if editando else datetime.now().strftime("%Y-%m-%d"))
        programa_politica = st.text_input("Programa/Politica", value=st.session_state.editando_conta["programa_politica"] if editando else "")
        setor_gasto = st.text_input("Setor do Gasto", value=st.session_state.editando_conta["setor_gasto"] if editando else "")
        submitted = st.form_submit_button("Salvar Conta")
        if submitted:
            if numero_conta.strip() == "":
                st.error("Numero da conta e obrigatorio.")
            else:
                conn = get_conn()
                cur = conn.cursor()
                if editando:
                    cur.execute("""UPDATE contas_receber SET esfera=?, numero_conta=?, fonte=?, referencia_tipo=?,
                        referencia_numero=?, tipo_recurso=?, valor_pago_custeio=?, valor_pago_investimento=?,
                        valor_total=?, data_recebimento=?, programa_politica=?, setor_gasto=? WHERE id=?""",
                        (esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso,
                         valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento,
                         programa_politica, setor_gasto, st.session_state.editando_conta["id"]))
                    conn.commit()
                    st.success("Conta atualizada com sucesso!")
                    st.session_state.editando_conta = None
                else:
                    cur.execute("""INSERT INTO contas_receber (esfera, numero_conta, fonte, referencia_tipo,
                        referencia_numero, tipo_recurso, valor_pago_custeio, valor_pago_investimento,
                        valor_total, data_recebimento, programa_politica, setor_gasto)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso,
                         valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento,
                         programa_politica, setor_gasto))
                    conn.commit()
                    st.success("Conta cadastrada com sucesso!")
                conn.close()
    if editando:
        if st.button("Cancelar Edicao"):
            st.session_state.editando_conta = None
            st.rerun()

# ===================== CONTAS CADASTRADAS =====================
def pagina_contas_cadastradas():
    st.markdown('<h3 class="section-title">Contas Cadastradas</h3>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Gerencie todas as contas por esfera</p>', unsafe_allow_html=True)
    tabs = st.tabs([e.upper() for e in ESFERAS])
    for i, esfera in enumerate(ESFERAS):
        with tabs[i]:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM contas_receber WHERE esfera = ? ORDER BY id DESC", (esfera,))
            contas = cur.fetchall()
            if len(contas) == 0:
                st.info(f"Nenhuma conta cadastrada em {esfera}.")
            else:
                dados = []
                for c in contas:
                    restante = get_valor_restante(c["id"], c["valor_total"])
                    dados.append({
                        "ID": c["id"],
                        "Numero": c["numero_conta"],
                        "Fonte": c["fonte"],
                        "Programa/Politica": c["programa_politica"] or "-",
                        "Valor Total": format_currency(c["valor_total"]),
                        "Restante": format_currency(restante),
                        "Data": c["data_recebimento"] or "-"
                    })
                st.dataframe(pd.DataFrame(dados), use_container_width=True, hide_index=True)
                st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
                st.markdown('<p style="color:#b3c5e8; font-weight:600;">Acoes por Conta</p>', unsafe_allow_html=True)
                for c in contas:
                    cc1, cc2, cc3 = st.columns([3, 1, 1])
                    with cc1:
                        st.markdown(f'<p style="color:#e2e8f0;">Conta {c["numero_conta"]} - {format_currency(c["valor_total"])}</p>', unsafe_allow_html=True)
                    with cc2:
                        if st.button("Editar", key=f"edit_{c['id']}"):
                            st.session_state.editando_conta = dict(c)
                            st.session_state.pagina = "Cadastrar Conta"
                            st.rerun()
                    with cc3:
                        if st.button("Excluir", key=f"del_{c['id']}"):
                            conn2 = get_conn()
                            cur2 = conn2.cursor()
                            cur2.execute("DELETE FROM ordens_compra WHERE conta_receber_id = ?", (c["id"],))
                            cur2.execute("DELETE FROM contas_receber WHERE id = ?", (c["id"],))
                            conn2.commit()
                            conn2.close()
                            st.success("Conta excluida com sucesso!")
                            st.rerun()
            conn.close()

# ===================== REALIZAR COMPRAS =====================
def pagina_realizar_compras():
    st.markdown('<h3 class="section-title">Realizar Compras</h3>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Registre uma ordem de compra vinculada a uma conta</p>', unsafe_allow_html=True)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, esfera, numero_conta, fonte, valor_total FROM contas_receber ORDER BY id DESC")
    contas = cur.fetchall()
    if len(contas) == 0:
        st.info("Nenhuma conta cadastrada. Cadastre uma conta primeiro.")
        conn.close()
        return
    opcoes_contas = {f"{c['esfera']} - {c['numero_conta']} (Fonte {c['fonte']})": c["id"] for c in contas}
    conta_sel = st.selectbox("Selecione a Conta", list(opcoes_contas.keys()))
    conta_id = opcoes_contas[conta_sel]
    cur.execute("SELECT * FROM contas_receber WHERE id = ?", (conta_id,))
    conta = cur.fetchone()
    restante = get_valor_restante(conta_id, conta["valor_total"])
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(label="Valor Total da Conta", value=format_currency(conta["valor_total"]))
    with c2:
        st.metric(label="Valor Restante", value=format_currency(restante))
    with c3:
        st.metric(label="Esfera", value=conta["esfera"])
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    with st.form("form_compra"):
        ficha = st.text_input("Ficha", value="")
        tipo_despesa = st.selectbox("Tipo de Despesa", ["Custeio", "Investimento"])
        data_compra = st.text_input("Data da Compra (AAAA-MM-DD)", value=datetime.now().strftime("%Y-%m-%d"))
        valor_compra = st.number_input("Valor da Compra", min_value=0.0, format="%.2f")
        produto_servico = st.text_area("Produto/Servico", value="")
        submitted = st.form_submit_button("Registrar Compra")
        if submitted:
            if ficha.strip() == "":
                st.error("Ficha e obrigatoria.")
            elif valor_compra <= 0:
                st.error("Valor da compra deve ser maior que zero.")
            elif valor_compra > restante:
                st.error("Valor da compra maior que o restante disponivel.")
            else:
                cur.execute("""INSERT INTO ordens_compra (conta_receber_id, esfera, numero_conta, fonte, ficha,
                    tipo_despesa, data_compra, valor_compra, produto_servico, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (conta_id, conta["esfera"], conta["numero_conta"], conta["fonte"], ficha,
                     tipo_despesa, data_compra, valor_compra, produto_servico, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                st.success("Compra registrada com sucesso!")
    conn.close()

# ===================== SUPERAVIT FINANCEIRO =====================
def pagina_superavit():
    st.markdown('<h3 class="section-title">Superavit Financeiro</h3>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Gerencie saldos superavitarios entre fontes</p>', unsafe_allow_html=True)
    with st.form("form_superavit"):
        esfera = st.selectbox("Esfera", ESFERAS)
        fonte_original = st.text_input("Fonte Original", value=get_fonte(esfera))
        fonte_superavit = st.text_input("Fonte Superavit", value="")
        saldo_total = st.number_input("Saldo Total", min_value=0.0, format="%.2f")
        saldo_restante = st.number_input("Saldo Restante", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Salvar Superavit")
        if submitted:
            if fonte_superavit.strip() == "":
                st.error("Fonte superavit e obrigatoria.")
            else:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("""INSERT INTO superavit (esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, created_at)
                    VALUES (?,?,?,?,?,?)""",
                    (esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                st.success("Superavit cadastrado com sucesso!")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#b3c5e8; font-weight:600;">Superavits Cadastrados</p>', unsafe_allow_html=True)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM superavit ORDER BY id DESC")
    sups = cur.fetchall()
    if len(sups) == 0:
        st.info("Nenhum superavit cadastrado.")
    else:
        dados = []
        for s in sups:
            dados.append({
                "ID": s["id"],
                "Esfera": s["esfera"],
                "Fonte Original": s["fonte_original"],
                "Fonte Superavit": s["fonte_superavit"],
                "Saldo Total": format_currency(s["saldo_total"]),
                "Saldo Restante": format_currency(s["saldo_restante"]),
                "Criado em": s["created_at"]
            })
        st.dataframe(pd.DataFrame(dados), use_container_width=True, hide_index=True)
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        for s in sups:
            sc1, sc2 = st.columns([4, 1])
            with sc1:
                st.markdown(f'<p style="color:#e2e8f0;">{s["esfera"]} - Fonte {s["fonte_superavit"]} - {format_currency(s["saldo_restante"])}</p>', unsafe_allow_html=True)
            with sc2:
                if st.button("Excluir", key=f"del_sup_{s['id']}"):
                    conn2 = get_conn()
                    cur2 = conn2.cursor()
                    cur2.execute("DELETE FROM superavit WHERE id = ?", (s["id"],))
                    conn2.commit()
                    conn2.close()
                    st.success("Superavit excluido!")
                    st.rerun()
    conn.close()

# ===================== UPLOAD DE ARQUIVOS =====================
def pagina_upload_arquivos():
    st.markdown('<h3 class="section-title">Upload de Arquivos</h3>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Envie arquivos de saude (blocos SUS)</p>', unsafe_allow_html=True)
    with st.form("form_upload"):
        bloco = st.selectbox("Bloco", ["Bloco I", "Bloco II", "Bloco III", "Bloco IV", "Bloco V", "Outro"])
        uploaded = st.file_uploader("Selecione o arquivo", type=["txt", "csv", "pdf", "xlsx", "xls", "json", "xml"])
        submitted = st.form_submit_button("Enviar Arquivo")
        if submitted:
            if uploaded is None:
                st.error("Selecione um arquivo.")
            else:
                conteudo = uploaded.read()
                try:
                    texto = conteudo.decode("utf-8", errors="ignore")
                except Exception:
                    texto = ""
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("""INSERT INTO arquivos_saude (bloco, nome_arquivo, conteudo_texto, dados_arquivo, data_upload)
                    VALUES (?,?,?,?,?)""",
                    (bloco, uploaded.name, texto, conteudo, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                st.success(f"Arquivo '{uploaded.name}' enviado com sucesso!")
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#b3c5e8; font-weight:600;">Arquivos Enviados</p>', unsafe_allow_html=True)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, bloco, nome_arquivo, data_upload FROM arquivos_saude ORDER BY id DESC")
    arqs = cur.fetchall()
    if len(arqs) == 0:
        st.info("Nenhum arquivo enviado.")
    else:
        dados = []
        for a in arqs:
            dados.append({
                "ID": a["id"],
                "Bloco": a["bloco"],
                "Nome": a["nome_arquivo"],
                "Data Upload": a["data_upload"]
            })
        st.dataframe(pd.DataFrame(dados), use_container_width=True, hide_index=True)
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        for a in arqs:
            ac1, ac2 = st.columns([4, 1])
            with ac1:
                st.markdown(f'<p style="color:#e2e8f0;">{a["bloco"]} - {a["nome_arquivo"]}</p>', unsafe_allow_html=True)
            with ac2:
                if st.button("Excluir", key=f"del_arq_{a['id']}"):
                    conn2 = get_conn()
                    cur2 = conn2.cursor()
                    cur2.execute("DELETE FROM arquivos_saude WHERE id = ?", (a["id"],))
                    conn2.commit()
                    conn2.close()
                    st.success("Arquivo excluido!")
                    st.rerun()
    conn.close()

# ===================== TROCAR SENHA =====================
def pagina_trocar_senha():
    st.markdown('<h3 class="section-title">Trocar Senha</h3>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Atualize sua senha de acesso</p>', unsafe_allow_html=True)
    with st.form("form_senha"):
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar = st.text_input("Confirmar Nova Senha", type="password")
        submitted = st.form_submit_button("Alterar Senha")
        if submitted:
            if senha_atual.strip() == "" or nova_senha.strip() == "":
                st.error("Preencha todos os campos.")
            elif nova_senha != confirmar:
                st.error("As senhas nao conferem.")
            else:
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("SELECT password_hash FROM users WHERE id = ?", (st.session_state.usuario["id"],))
                row = cur.fetchone()
                if row is None:
                    st.error("Usuario nao encontrado.")
                elif row["password_hash"] != hash_senha(senha_atual):
                    st.error("Senha atual incorreta.")
                else:
                    cur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_senha(nova_senha), st.session_state.usuario["id"]))
                    conn.commit()
                    st.success("Senha alterada com sucesso!")
                conn.close()

# ===================== ROTEAMENTO PRINCIPAL =====================
def main():
    if not st.session_state.logado:
        tela_login()
        return
    sidebar()
    pagina = st.session_state.pagina
    if pagina == "Inicio":
        pagina_inicial()
    elif pagina == "Esfera Detalhe":
        pagina_esfera_detalhe()
    elif pagina == "Cadastrar Conta":
        pagina_cadastrar_conta()
    elif pagina == "Contas Cadastradas":
        pagina_contas_cadastradas()
    elif pagina == "Realizar Compras":
        pagina_realizar_compras()
    elif pagina == "Superavit Financeiro":
        pagina_superavit()
    elif pagina == "Upload de Arquivos":
        pagina_upload_arquivos()
    elif pagina == "Trocar Senha":
        pagina_trocar_senha()
    else:
        pagina_inicial()

if __name__ == "__main__":
    main()
