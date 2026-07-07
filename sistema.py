import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

st.set_page_config(page_title="MARMED - Gestao de Saude", page_icon="🏥", layout="wide", initial_sidebar_state="expanded")

# CSS GLOBAL - Fundo azul escuro em todo o sistema
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0a0e27 0%, #16213e 50%, #0f3460 100%); }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0a0e27 0%, #16213e 100%); border-right: 1px solid rgba(56,189,248,0.15); }
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label { color: #cbd5e1; }
.stButton>button { background: linear-gradient(135deg, #38bdf8, #6366f1); color: #ffffff; border: none; border-radius: 10px; font-weight: 700; padding: 12px 16px; font-size: 15px; }
.stButton>button:hover { filter: brightness(1.15); }
.stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] { background: rgba(255,255,255,0.06) !important; color: #f1f5f9 !important; border-radius: 12px !important; border: 1px solid rgba(148,163,184,0.25) !important; }
.stTextInput label, .stSelectbox label, .stNumberInput label, .stTextArea label, .stDateInput label { color: #e2e8f0 !important; font-weight: 500; }
h1, h2, h3, h4, h5, h6, p, span, div { color: #e0f2fe; }
.stDateInput input { background: rgba(255,255,255,0.06) !important; color: #f1f5f9 !important; border-radius: 12px !important; border: 1px solid rgba(148,163,184,0.25) !important; }
header[data-testid="stHeader"] { background: transparent !important; }
div[data-testid="stToolbar"] { background: transparent !important; }
div[data-testid="stDecoration"] { display: none !important; }
.stDataFrame { background: rgba(255,255,255,0.04); border-radius: 12px; }
.stDataFrame th, .stDataFrame td { color: #e0f2fe !important; }
.stAlert { border-radius: 12px; }
.stMetric { background: rgba(255,255,255,0.04); border-radius: 12px; padding: 16px; border: 1px solid rgba(148,163,184,0.15); }
.stMetric label { color: #94a3b8 !important; }
.stMetric div[data-testid="stMetricValue"] { color: #38bdf8 !important; }
</style>
""", unsafe_allow_html=True)

DB_NAME = "marmed.db"


def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


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
        esfera TEXT, numero_conta TEXT, fonte TEXT,
        referencia_tipo TEXT, referencia_numero TEXT,
        tipo_recurso TEXT,
        valor_pago_custeio REAL DEFAULT 0,
        valor_pago_investimento REAL DEFAULT 0,
        valor_total REAL DEFAULT 0,
        data_recebimento TEXT,
        programa_politica TEXT, setor_gasto TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS superavit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        esfera TEXT, fonte_original TEXT, fonte_superavit TEXT,
        saldo_total REAL DEFAULT 0, saldo_restante REAL DEFAULT 0,
        created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS ordens_compra (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conta_receber_id INTEGER, esfera TEXT, numero_conta TEXT, fonte TEXT,
        ficha TEXT, tipo_despesa TEXT, data_compra TEXT,
        valor_compra REAL DEFAULT 0, produto_servico TEXT, created_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS arquivos_saude (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bloco TEXT, nome_arquivo TEXT, conteudo_texto TEXT,
        dados_arquivo BLOB, data_upload TEXT
    )""")

    # Migracao defensiva
    for tabela in ["users", "contas_receber", "superavit", "ordens_compra", "arquivos_saude"]:
        try:
            c.execute(f"PRAGMA table_info({tabela})")
            colunas_existentes = {row[1] for row in c.fetchall()}
            schema_defs = {
                "users": [("nome", "TEXT")],
                "contas_receber": [("programa_politica", "TEXT"), ("setor_gasto", "TEXT")],
                "superavit": [],
                "ordens_compra": [],
                "arquivos_saude": []
            }
            for col, tip in schema_defs.get(tabela, []):
                if col not in colunas_existentes:
                    c.execute(f"ALTER TABLE {tabela} ADD COLUMN {col} {tip}")
        except Exception:
            pass

    admin_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password_hash, nome) VALUES (?, ?, ?)", ("admin", admin_hash, "Administrador"))
    conn.commit()
    conn.close()


init_db()


def format_currency(valor):
    if valor is None:
        valor = 0.0
    v = float(valor)
    texto = f"{v:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def parse_valor(texto):
    if texto is None:
        return 0.0
    if isinstance(texto, (int, float)):
        return float(texto)
    limpo = str(texto).replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(limpo)
    except Exception:
        return 0.0


def get_fonte(esfera):
    mapa = {"Federal": "1.600", "Estadual": "1.621", "Municipal": "1.500", "Transferencia": "1.700", "Transposicao": "1.800"}
    return mapa.get(esfera, "")


def get_fonte_superavit(esfera):
    mapa = {"Federal": "2.600", "Estadual": "2.621"}
    return mapa.get(esfera)


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "Inicio"


# --- TELA DE LOGIN ---
def tela_login():
    st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at 15% 20%, rgba(56,189,248,0.28) 0%, transparent 45%), radial-gradient(circle at 85% 15%, rgba(129,140,248,0.30) 0%, transparent 45%), radial-gradient(circle at 75% 85%, rgba(192,132,252,0.26) 0%, transparent 50%), linear-gradient(135deg, #0a0e27 0%, #16213e 50%, #0f3460 100%); }
    .login-card { background: rgba(255,255,255,0.07); backdrop-filter: blur(32px); border-radius: 32px; padding: 52px 44px; max-width: 460px; margin: 60px auto 0 auto; box-shadow: 0 30px 60px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.18), 0 0 0 1px rgba(129,140,248,0.18); }
    .login-title { font-size: 120px; font-weight: 800; text-align: center; background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 4px; margin: 0; }
    .login-subtitle { text-align: center; color: #cbd5e1; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 36px; margin-top: 6px; }
    .login-badge { display: flex; justify-content: center; gap: 10px; margin-top: 24px; flex-wrap: wrap; }
    .login-badge span { background: rgba(56,189,248,0.10); color: #bae6fd; font-size: 11px; padding: 6px 14px; border-radius: 999px; border: 1px solid rgba(56,189,248,0.28); letter-spacing: 1px; font-weight: 600; }
    .login-footer { text-align: center; margin-top: 22px; color: #94a3b8; font-size: 11px; letter-spacing: 1px; }
    div[data-testid="stForm"] .stButton>button { background: linear-gradient(135deg, #38bdf8, #6366f1, #c084fc) !important; color: #fff !important; border: none !important; border-radius: 14px !important; font-weight: 700 !important; padding: 12px !important; box-shadow: 0 10px 28px rgba(99,102,241,0.45) !important; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.3, 1])
    with col2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<p class="login-title">MARMED</p>', unsafe_allow_html=True)
        st.markdown('<p class="login-subtitle">Gestao Inteligente de Saude Municipal</p>', unsafe_allow_html=True)

        with st.form("form_login"):
            usuario = st.text_input("Usuario", placeholder="Digite seu usuario")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            entrar = st.form_submit_button("Entrar", use_container_width=True)
            if entrar:
                if not usuario or not senha:
                    st.error("Preencha usuario e senha.")
                else:
                    conn = get_conn()
                    row = conn.execute("SELECT id, username, nome FROM users WHERE username=? AND password_hash=?", (usuario, hash_senha(senha))).fetchone()
                    conn.close()
                    if row:
                        st.session_state["logged_in"] = True
                        st.session_state["usuario_id"] = row[0]
                        st.session_state["usuario_nome"] = row[2] or row[1]
                        st.session_state["pagina"] = "Inicio"
                        st.rerun()
                    else:
                        st.error("Usuario ou senha invalidos.")

        st.markdown('<div class="login-badge"><span>🔒 SEGURO</span><span>✦ MODERNO</span><span>✚ SUS</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="login-footer">MARMED &copy; 2026 - Gestao Inteligente de Saude</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# --- PAGINA INICIAL ---
def pagina_inicio():
    st.markdown('<p style="font-size:140px;font-weight:800;color:#f8fafc;text-align:center;letter-spacing:2px;margin-bottom:4px;">MARMED</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:50px;font-weight:600;color:#7dd3fc;text-align:center;margin-bottom:3px;">Sistema Integrado de Gestao Publica</p>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:36px;font-weight:500;color:#cbd5e1;text-align:center;margin-bottom:20px;">Prefeitura Municipal de Luminarias - MG</p>', unsafe_allow_html=True)

    conn = get_conn()
    esferas = ["Federal", "Estadual", "Municipal", "Transferencia", "Transposicao"]
    cores = ["#3b82f6", "#22c55e", "#eab308", "#a855f7", "#ef4444"]
    cols = st.columns(5)
    for i, esf in enumerate(esferas):
        total = conn.execute("SELECT COALESCE(SUM(valor_total),0) FROM contas_receber WHERE esfera=?", (esf,)).fetchone()[0]
        with cols[i]:
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#1a2a3a,#0f2027);'
                f'border-radius:15px;padding:15px;text-align:center;'
                f'border-left:4px solid {cores[i]};'
                f'border:1px solid rgba(34,211,238,0.3);margin-bottom:8px;">'
                f'<div style="color:#b0eaff;font-size:12px;font-weight:600;">{esf.upper()}</div>'
                f'<div style="color:#00d4ff;font-size:22px;font-weight:700;">{format_currency(total)}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
    conn.close()


# --- CADASTRO DE CONTAS ---
def pagina_cadastro_contas():
    st.markdown('<p style="font-size:34px;font-weight:800;color:#f1f5f9;margin-bottom:20px;">Cadastro de Contas a Receber</p>', unsafe_allow_html=True)

    esferas = ["Federal", "Estadual", "Municipal", "Transferencia", "Transposicao"]
    tipos_referencia = ["Nota Fiscal", "Documento", "Processo", "Outro"]
    tipos_recurso = ["Custeio", "Investimento", "Custeio + Investimento"]

    with st.form("form_conta"):
        col1, col2 = st.columns(2)
        with col1:
            esfera = st.selectbox("Esfera", esferas)
            numero_conta = st.text_input("Numero da Conta", placeholder="Ex: 12345-6")
            referencia_tipo = st.selectbox("Tipo de Referencia", tipos_referencia)
            referencia_numero = st.text_input("Numero de Referencia", placeholder="Ex: NF-001/2026")
            valor_custeio = st.text_input("Valor Pago - Custeio (R$)", placeholder="0,00")
        with col2:
            fonte = st.text_input("Fonte", value=get_fonte(esfera), disabled=True)
            tipo_recurso = st.selectbox("Tipo de Recurso", tipos_recurso)
            data_recebimento = st.date_input("Data de Recebimento", value=datetime.now())
            valor_investimento = st.text_input("Valor Pago - Investimento (R$)", placeholder="0,00")
            programa_politica = st.text_input("Programa / Politica", placeholder="Ex: Programa Saude na Escola")

        setor_gasto = st.text_input("Setor de Gasto", placeholder="Ex: Atencao Basica")
        salvar = st.form_submit_button("Cadastrar Conta", use_container_width=True)

        if salvar:
            if not numero_conta:
                st.error("Informe o numero da conta.")
            else:
                vc = parse_valor(valor_custeio)
                vi = parse_valor(valor_investimento)
                total = vc + vi
                conn = get_conn()
                conn.execute(
                    """INSERT INTO contas_receber
                    (esfera, numero_conta, fonte, referencia_tipo, referencia_numero,
                     tipo_recurso, valor_pago_custeio, valor_pago_investimento, valor_total,
                     data_recebimento, programa_politica, setor_gasto)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (esfera, numero_conta, get_fonte(esfera), referencia_tipo, referencia_numero,
                     tipo_recurso, vc, vi, total, str(data_recebimento), programa_politica, setor_gasto)
                )
                conn.commit()
                conn.close()
                st.success(f"Conta cadastrada com sucesso! Valor total: {format_currency(total)}")


# --- CONTAS CADASTRADAS ---
def pagina_contas_cadastradas():
    st.markdown('<p style="font-size:34px;font-weight:800;color:#f1f5f9;margin-bottom:20px;">Contas Cadastradas</p>', unsafe_allow_html=True)

    conn = get_conn()
    rows = conn.execute("""
        SELECT id, esfera, numero_conta, fonte, referencia_tipo, referencia_numero,
               tipo_recurso, valor_pago_custeio, valor_pago_investimento, valor_total,
               data_recebimento, programa_politica, setor_gasto
        FROM contas_receber ORDER BY id DESC
    """).fetchall()
    conn.close()

    if not rows:
        st.info("Nenhuma conta cadastrada ainda.")
        return

    filtro = st.selectbox("Filtrar por Esfera", ["Todas", "Federal", "Estadual", "Municipal", "Transferencia", "Transposicao"])

    for r in rows:
        if filtro != "Todas" and r[1] != filtro:
            continue
        with st.expander(f"{r[1]} - Conta {r[2]} | {format_currency(r[9])}"):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Esfera:** {r[1]}")
            c1.markdown(f"**Numero da Conta:** {r[2]}")
            c1.markdown(f"**Fonte:** {r[3]}")
            c2.markdown(f"**Referencia:** {r[4]} - {r[5]}")
            c2.markdown(f"**Tipo de Recurso:** {r[6]}")
            c2.markdown(f"**Data Recebimento:** {r[10]}")
            c3.markdown(f"**Custeio:** {format_currency(r[7])}")
            c3.markdown(f"**Investimento:** {format_currency(r[8])}")
            c3.markdown(f"**Valor Total:** {format_currency(r[9])}")
            if r[11]:
                st.markdown(f"**Programa/Politica:** {r[11]}")
            if r[12]:
                st.markdown(f"**Setor de Gasto:** {r[12]}")


# --- REALIZAR COMPRAS ---
def pagina_realizar_compras():
    st.markdown('<p style="font-size:34px;font-weight:800;color:#f1f5f9;margin-bottom:20px;">Realizar Compras</p>', unsafe_allow_html=True)

    conn = get_conn()
    contas = conn.execute("SELECT id, esfera, numero_conta, fonte, valor_total FROM contas_receber ORDER BY id DESC").fetchall()
    conn.close()

    if not contas:
        st.warning("Cadastre uma conta a receber antes de realizar compras.")
        return

    opcoes = {f"{c[1]} - Conta {c[2]} (Total: {format_currency(c[4])})": c for c in contas}
    conta_sel = st.selectbox("Selecione a Conta", list(opcoes.keys()))
    conta = opcoes[conta_sel]

    tipos_despesa = ["Custeio", "Investimento"]
    with st.form("form_compra"):
        c1, c2 = st.columns(2)
        with c1:
            ficha = st.text_input("Ficha", placeholder="Ex: 001")
            tipo_despesa = st.selectbox("Tipo de Despesa", tipos_despesa)
            data_compra = st.date_input("Data da Compra", value=datetime.now())
        with c2:
            produto_servico = st.text_input("Produto / Servico", placeholder="Ex: Medicamentos")
            valor_compra = st.text_input("Valor da Compra (R$)", placeholder="0,00")

        registrar = st.form_submit_button("Registrar Compra", use_container_width=True)

        if registrar:
            if not produto_servico or not valor_compra:
                st.error("Preencha produto/servico e valor.")
            else:
                vc = parse_valor(valor_compra)
                conn = get_conn()
                conn.execute(
                    """INSERT INTO ordens_compra
                    (conta_receber_id, esfera, numero_conta, fonte, ficha, tipo_despesa,
                     data_compra, valor_compra, produto_servico, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (conta[0], conta[1], conta[2], conta[3], ficha, tipo_despesa,
                     str(data_compra), vc, produto_servico, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
                conn.close()
                st.success(f"Compra registrada: {produto_servico} - {format_currency(vc)}")

    st.markdown("---")
    st.markdown('<p style="font-size:22px;font-weight:700;color:#7dd3fc;margin-bottom:12px;">Compras Registradas</p>', unsafe_allow_html=True)
    conn = get_conn()
    compras = conn.execute("""
        SELECT id, esfera, numero_conta, ficha, tipo_despesa, data_compra, valor_compra, produto_servico
        FROM ordens_compra WHERE conta_receber_id=? ORDER BY id DESC
    """, (conta[0],)).fetchall()
    conn.close()

    if not compras:
        st.info("Nenhuma compra registrada para esta conta.")
    else:
        for comp in compras:
            st.markdown(
                f'<div style="background:rgba(255,255,255,0.05);border-radius:10px;padding:12px 16px;'
                f'margin-bottom:8px;border-left:3px solid #38bdf8;">'
                f'<span style="color:#bae6fd;font-weight:600;">{comp[7]}</span> '
                f'<span style="color:#94a3b8;">- {comp[1]} / Conta {comp[2]} / Ficha {comp[3]}</span><br>'
                f'<span style="color:#00d4ff;font-weight:700;">{format_currency(comp[6])}</span> '
                f'<span style="color:#94a3b8;font-size:13px;">| {comp[4]} | {comp[5]}</span>'
                f'</div>',
                unsafe_allow_html=True
            )


# --- SUPERAVIT FINANCEIRO ---
def pagina_superavit():
    st.markdown('<p style="font-size:34px;font-weight:800;color:#f1f5f9;margin-bottom:20px;">Superavit Financeiro</p>', unsafe_allow_html=True)

    esferas_sup = ["Federal", "Estadual"]

    with st.form("form_superavit"):
        c1, c2 = st.columns(2)
        with c1:
            esfera = st.selectbox("Esfera", esferas_sup)
            fonte_original = st.text_input("Fonte Original", value=get_fonte(esfera), disabled=True)
        with c2:
            fonte_superavit = st.text_input("Fonte Superavit", value=get_fonte_superavit(esfera) or "", disabled=True)
            saldo_total = st.text_input("Saldo Total (R$)", placeholder="0,00")

        salvar = st.form_submit_button("Registrar Superavit", use_container_width=True)

        if salvar:
            if not saldo_total:
                st.error("Informe o saldo total.")
            else:
                st_val = parse_valor(saldo_total)
                conn = get_conn()
                conn.execute(
                    """INSERT INTO superavit
                    (esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, created_at)
                    VALUES (?,?,?,?,?,?)""",
                    (esfera, get_fonte(esfera), get_fonte_superavit(esfera) or "",
                     st_val, st_val, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
                conn.close()
                st.success(f"Superavit registrado: {format_currency(st_val)}")

    st.markdown("---")
    st.markdown('<p style="font-size:22px;font-weight:700;color:#7dd3fc;margin-bottom:12px;">Superavits Registrados</p>', unsafe_allow_html=True)
    conn = get_conn()
    sup_rows = conn.execute("""
        SELECT id, esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, created_at
        FROM superavit ORDER BY id DESC
    """).fetchall()
    conn.close()

    if not sup_rows:
        st.info("Nenhum superavit registrado.")
    else:
        for s in sup_rows:
            st.markdown(
                f'<div style="background:rgba(255,255,255,0.05);border-radius:10px;padding:12px 16px;'
                f'margin-bottom:8px;border-left:3px solid #a855f7;">'
                f'<span style="color:#bae6fd;font-weight:600;">{s[1]}</span> '
                f'<span style="color:#94a3b8;">| Fonte Orig: {s[2]} | Fonte Sup: {s[3]}</span><br>'
                f'<span style="color:#00d4ff;font-weight:700;">Saldo Total: {format_currency(s[4])}</span> '
                f'<span style="color:#94a3b8;">| Restante: {format_currency(s[5])}</span><br>'
                f'<span style="color:#64748b;font-size:12px;">{s[6]}</span>'
                f'</div>',
                unsafe_allow_html=True
            )


# --- UPLOAD DE ARQUIVOS ---
def pagina_upload_arquivos():
    st.markdown('<p style="font-size:34px;font-weight:800;color:#f1f5f9;margin-bottom:20px;">Upload de Arquivos</p>', unsafe_allow_html=True)

    blocos = ["Bloco 1 - Atendimento", "Bloco 2 - Producao", "Bloco 3 - Financeiro", "Bloco 4 - Outros"]

    with st.form("form_upload"):
        bloco = st.selectbox("Bloco", blocos)
        arquivo = st.file_uploader("Selecione o arquivo", type=["txt", "csv", "pdf", "xlsx", "docx"])
        enviar = st.form_submit_button("Enviar Arquivo", use_container_width=True)

        if enviar:
            if arquivo is None:
                st.error("Selecione um arquivo.")
            else:
                conteudo = arquivo.read()
                texto = ""
                try:
                    texto = conteudo.decode("utf-8")
                except Exception:
                    texto = "[Arquivo binario]"
                conn = get_conn()
                conn.execute(
                    """INSERT INTO arquivos_saude
                    (bloco, nome_arquivo, conteudo_texto, dados_arquivo, data_upload)
                    VALUES (?,?,?,?,?)""",
                    (bloco, arquivo.name, texto[:5000], conteudo, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                conn.commit()
                conn.close()
                st.success(f"Arquivo '{arquivo.name}' enviado para {bloco}.")

    st.markdown("---")
    st.markdown('<p style="font-size:22px;font-weight:700;color:#7dd3fc;margin-bottom:12px;">Arquivos Enviados</p>', unsafe_allow_html=True)
    conn = get_conn()
    arqs = conn.execute("SELECT id, bloco, nome_arquivo, data_upload FROM arquivos_saude ORDER BY id DESC").fetchall()
    conn.close()

    if not arqs:
        st.info("Nenhum arquivo enviado.")
    else:
        for a in arqs:
            st.markdown(
                f'<div style="background:rgba(255,255,255,0.05);border-radius:10px;padding:12px 16px;'
                f'margin-bottom:8px;border-left:3px solid #22c55e;">'
                f'<span style="color:#bae6fd;font-weight:600;">{a[2]}</span> '
                f'<span style="color:#94a3b8;">| {a[1]} | {a[3]}</span>'
                f'</div>',
                unsafe_allow_html=True
            )


# --- TROCAR SENHA ---
def pagina_trocar_senha():
    st.markdown('<p style="font-size:34px;font-weight:800;color:#f1f5f9;margin-bottom:20px;">Trocar Senha</p>', unsafe_allow_html=True)

    with st.form("form_senha"):
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar = st.text_input("Confirmar Nova Senha", type="password")
        trocar = st.form_submit_button("Trocar Senha", use_container_width=True)

        if trocar:
            if not senha_atual or not nova_senha or not confirmar:
                st.error("Preencha todos os campos.")
            elif nova_senha != confirmar:
                st.error("A nova senha e a confirmacao nao coincidem.")
            elif len(nova_senha) < 6:
                st.error("A nova senha deve ter no minimo 6 caracteres.")
            else:
                conn = get_conn()
                user_id = st.session_state.get("usuario_id")
                row = conn.execute("SELECT password_hash FROM users WHERE id=?", (user_id,)).fetchone()
                if row and row[0] == hash_senha(senha_atual):
                    conn.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_senha(nova_senha), user_id))
                    conn.commit()
                    conn.close()
                    st.success("Senha alterada com sucesso!")
                else:
                    conn.close()
                    st.error("Senha atual incorreta.")


# --- MENU LATERAL ---
def menu_lateral():
    with st.sidebar:
        st.markdown('<p style="color:#7dd3fc;font-size:16px;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-top:8px;margin-bottom:4px;">Aba de Navegacao</p>', unsafe_allow_html=True)
        nome = st.session_state.get("usuario_nome", "Usuario")
        st.markdown(f'<p style="color:#94a3b8;font-size:13px;margin-bottom:8px;">Usuario: <span style="color:#bae6fd;font-weight:600;">{nome}</span></p>', unsafe_allow_html=True)
        st.markdown("---")
        paginas = ["Inicio", "Cadastro de Contas", "Contas Cadastradas", "Realizar Compras", "Superavit Financeiro", "Upload de Arquivos", "Trocar Senha"]
        for p in paginas:
            if st.button(p, key=f"nav_{p}", use_container_width=True):
                st.session_state["pagina"] = p
                st.rerun()
        st.markdown("---")
        if st.button("Sair", key="nav_sair", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()


# --- MAIN ---
def main():
    if not st.session_state["logged_in"]:
        tela_login()
        return
    menu_lateral()
    p = st.session_state.get("pagina", "Inicio")
    if p == "Inicio":
        pagina_inicio()
    elif p == "Cadastro de Contas":
        pagina_cadastro_contas()
    elif p == "Contas Cadastradas":
        pagina_contas_cadastradas()
    elif p == "Realizar Compras":
        pagina_realizar_compras()
    elif p == "Superavit Financeiro":
        pagina_superavit()
    elif p == "Upload de Arquivos":
        pagina_upload_arquivos()
    elif p == "Trocar Senha":
        pagina_trocar_senha()
    else:
        pagina_inicio()


if __name__ == "__main__":
    main()
