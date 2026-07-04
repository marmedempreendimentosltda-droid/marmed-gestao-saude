import streamlit as st
import sqlite3
import hashlib
import re
import base64
from datetime import datetime

def get_logo_base64():
    try:
        with open("logo.png", "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode("utf-8")
    except Exception:
        return None

LOGO_BASE64 = get_logo_base64()

st.set_page_config(page_title="MARMED - Gestao de Saude", page_icon="🏥", layout="wide", initial_sidebar_state="expanded")

DB_NAME = "marmed.db"

def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    schema = {
        "users": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("username", "TEXT UNIQUE"),
            ("password_hash", "TEXT"),
            ("nome", "TEXT"),
        ],
        "contas_receber": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("esfera", "TEXT"),
            ("numero_conta", "TEXT"),
            ("fonte", "TEXT"),
            ("referencia_tipo", "TEXT"),
            ("referencia_numero", "TEXT"),
            ("tipo_recurso", "TEXT"),
            ("valor_pago_custeio", "REAL DEFAULT 0"),
            ("valor_pago_investimento", "REAL DEFAULT 0"),
            ("valor_total", "REAL DEFAULT 0"),
            ("data_recebimento", "TEXT"),
            ("programa_politica", "TEXT"),
            ("setor_gasto", "TEXT"),
        ],
        "superavit": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("esfera", "TEXT"),
            ("fonte_original", "TEXT"),
            ("fonte_superavit", "TEXT"),
            ("saldo_total", "REAL DEFAULT 0"),
            ("saldo_restante", "REAL DEFAULT 0"),
            ("created_at", "TEXT"),
        ],
        "ordens_compra": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("conta_receber_id", "INTEGER"),
            ("esfera", "TEXT"),
            ("numero_conta", "TEXT"),
            ("fonte", "TEXT"),
            ("ficha", "TEXT"),
            ("tipo_despesa", "TEXT"),
            ("data_compra", "TEXT"),
            ("valor_compra", "REAL DEFAULT 0"),
            ("produto_servico", "TEXT"),
            ("created_at", "TEXT"),
        ],
        "arquivos_saude": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("bloco", "TEXT"),
            ("nome_arquivo", "TEXT"),
            ("conteudo_texto", "TEXT"),
            ("dados_arquivo", "BLOB"),
            ("data_upload", "TEXT"),
        ],
        "programas_saude": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("nome", "TEXT"),
            ("descricao", "TEXT"),
            ("created_at", "TEXT"),
        ],
        "conselho": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("nome", "TEXT"),
            ("segmento", "TEXT"),
            ("cargo", "TEXT"),
            ("email", "TEXT"),
            ("telefone", "TEXT"),
            ("data_posse", "TEXT"),
        ],
    }

    for tabela, colunas in schema.items():
        colunas_sql = ", ".join(f"{nome} {definicao}" for nome, definicao in colunas)
        cur.execute(f"CREATE TABLE IF NOT EXISTS {tabela} ({colunas_sql})")

    for tabela, colunas in schema.items():
        existentes = {row[1] for row in cur.execute(f"PRAGMA table_info({tabela})").fetchall()}
        for nome_coluna, definicao in colunas:
            if nome_coluna in existentes:
                continue
            if "PRIMARY KEY" in definicao.upper():
                continue
            try:
                cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {nome_coluna} {definicao}")
            except sqlite3.OperationalError:
                pass

    admin_hash = hashlib.sha256("Diretor2025#".encode("utf-8")).hexdigest()
    try:
        cur.execute("INSERT OR IGNORE INTO users (username, password_hash, nome) VALUES (?, ?, ?)", ("admin", admin_hash, "Administrador"))
    except sqlite3.OperationalError:
        pass

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
    except ValueError:
        return 0.0

def get_fonte(esfera):
    mapa = {"Federal": "1.600", "Estadual": "1.621", "Municipal": "1.500", "Transferencia": "1.700", "Transposicao": "1.800"}
    return mapa.get(esfera, "")

def get_fonte_superavit(esfera):
    mapa = {"Federal": "2.600", "Estadual": "2.621"}
    return mapa.get(esfera)

def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def verificar_login(usuario, senha):
    conn = get_conn()
    row = conn.execute("SELECT id, username, nome FROM users WHERE username=? AND password_hash=?", (usuario, hash_senha(senha))).fetchone()
    conn.close()
    return row

def extrair_texto(dados_bytes, nome_arquivo):
    try:
        if nome_arquivo.lower().endswith((".txt", ".csv")):
            return dados_bytes.decode("utf-8", errors="replace")
        return f"[Arquivo: {nome_arquivo}]"
    except Exception:
        return "[Nao foi possivel extrair texto]"

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "usuario_nome" not in st.session_state:
    st.session_state["usuario_nome"] = ""
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "Inicio"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #0a0e27 0%, #16213e 50%, #0f3460 100%); }
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0a0e27 0%, #16213e 100%); border-right: 1px solid rgba(56,189,248,0.15); }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label { color: #cbd5e1; }
    section[data-testid="stSidebar"] button { color: #f8fafc !important; }
    .stButton>button { background: linear-gradient(135deg, #38bdf8, #6366f1); color: #ffffff; border: none; border-radius: 10px; font-weight: 700; padding: 28px 16px; font-size: 17px; transition: all 0.2s ease; }
    .stButton>button:hover { filter: brightness(1.15); transform: translateY(-1px); }
    .stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] { background: rgba(255,255,255,0.06) !important; color: #f1f5f9 !important; border-radius: 12px !important; border: 1px solid rgba(148,163,184,0.25) !important; }
    .stTextInput label, .stSelectbox label, .stNumberInput label, .stTextArea label, .stDateInput label { color: #e2e8f0 !important; font-weight: 500; }
    .stTextInput > div, .stNumberInput > div, .stTextArea > div, .stDateInput > div { border-radius: 12px; transition: box-shadow 0.2s ease, border-color 0.2s ease; }
    .stTextInput > div:focus-within, .stNumberInput > div:focus-within, .stTextArea > div:focus-within, .stDateInput > div:focus-within { box-shadow: 0 0 0 2px rgba(56,189,248,0.45); border-color: rgba(56,189,248,0.6) !important; }
    .mm-title { font-size: 34px; font-weight: 800; color: #f1f5f9; margin-bottom: 4px; }
    .mm-subtitle { color: #cbd5e1; font-size: 14px; margin-bottom: 24px; }
    .mm-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 20px; text-align: center; }
    .mm-card-value { font-size: 22px; font-weight: 800; background: linear-gradient(135deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .mm-card-label { color: #cbd5e1; font-size: 12px; margin-top: 6px; }
    .mm-brand-title { font-size: 120px; font-weight: 800; color: #f8fafc; letter-spacing: 2px; text-align: center; margin-bottom: 4px; }
    .mm-brand-subtitle { font-size: 42px; font-weight: 600; color: #7dd3fc; text-align: center; margin-bottom: 3px; }
    .mm-brand-institution { font-size: 30px; font-weight: 500; color: #cbd5e1; text-align: center; margin-bottom: 20px; }
    header[data-testid="stHeader"] { background: transparent !important; box-shadow: none !important; }
    div[data-testid="stToolbar"] { background: transparent !important; }
    div[data-testid="stDecoration"] { background: transparent !important; display: none !important; }
    .stApp > header { background: transparent !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

def tela_login():
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at 15% 20%, rgba(56,189,248,0.28) 0%, transparent 45%),
                radial-gradient(circle at 85% 15%, rgba(129,140,248,0.30) 0%, transparent 45%),
                radial-gradient(circle at 75% 85%, rgba(192,132,252,0.26) 0%, transparent 50%),
                radial-gradient(circle at 25% 80%, rgba(56,189,248,0.18) 0%, transparent 45%),
                linear-gradient(135deg, #0a0e27 0%, #16213e 50%, #0f3460 100%);
            background-attachment: fixed;
        }
        .login-card {
            background: rgba(255,255,255,0.07);
            backdrop-filter: blur(32px);
            -webkit-backdrop-filter: blur(32px);
            border-radius: 32px;
            padding: 52px 44px;
            max-width: 460px;
            margin: 60px auto 0 auto;
            box-shadow:
                0 30px 60px rgba(0,0,0,0.45),
                inset 0 1px 0 rgba(255,255,255,0.18),
                0 0 0 1px rgba(129,140,248,0.18);
        }
        .login-title {
            font-size: 100px;
            font-weight: 800;
            text-align: center;
            background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 4px;
            margin: 0;
        }
        .login-subtitle { text-align: center; color: #cbd5e1; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 36px; margin-top: 6px; }
        .login-badge { display: flex; justify-content: center; gap: 10px; margin-top: 24px; flex-wrap: wrap; }
        .login-badge span {
            background: rgba(56,189,248,0.10);
            color: #bae6fd;
            font-size: 11px;
            padding: 6px 14px;
            border-radius: 999px;
            border: 1px solid rgba(56,189,248,0.28);
            letter-spacing: 1px;
            font-weight: 600;
        }
        .login-footer { text-align: center; margin-top: 22px; color: #94a3b8; font-size: 11px; letter-spacing: 1px; }
        div[data-testid="stForm"] .stButton>button {
            background: linear-gradient(135deg, #38bdf8, #6366f1, #c084fc) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 14px !important;
            font-weight: 700 !important;
            padding: 0.75rem 1rem !important;
            box-shadow: 0 10px 28px rgba(99,102,241,0.45) !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stForm"] .stButton>button:hover {
            filter: brightness(1.12);
            transform: scale(1.02);
            box-shadow: 0 14px 34px rgba(99,102,241,0.6) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

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
                    row = verificar_login(usuario, senha)
                    if row:
                        st.session_state["logged_in"] = True
                        st.session_state["usuario_id"] = row[0]
                        st.session_state["usuario_nome"] = row[2] or row[1]
                        st.session_state["pagina"] = "Inicio"
                        st.rerun()
                    else:
                        st.error("Usuario ou senha invalidos.")

        st.markdown('<div class="login-badge"><span>🔒 SEGURO</span><span>✦ MODERNO</span><span>✚ SUS</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="login-footer">MARMED © 2026 - Gestao Inteligente de Saude</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

def pagina_inicio():
    st.markdown('<p class="mm-brand-title">MARMED</p>', unsafe_allow_html=True)
    st.markdown('<p class="mm-brand-subtitle">Sistema Integrado de Gestao Publica</p>', unsafe_allow_html=True)
    st.markdown('<p class="mm-brand-institution">Prefeitura Municipal de Luminarias - MG</p>', unsafe_allow_html=True)

    conn = get_conn()
    esferas = ["Federal", "Estadual", "Municipal", "Transferencia", "Transposicao"]
    cols = st.columns(len(esferas))
    for i, esf in enumerate(esferas):
        total = conn.execute("SELECT COALESCE(SUM(valor_total),0) FROM contas_receber WHERE esfera=?", (esf,)).fetchone()[0]
        with cols[i]:
            if st.button(f"{esf}  ·  {format_currency(total)}", key=f"btn_esfera_{esf}", use_container_width=True):
                st.session_state["esfera_selecionada"] = esf
                st.session_state["pagina"] = "Esfera Detalhe"
                st.rerun()
    conn.close()

def pagina_esfera_detalhe():
    esfera = st.session_state.get("esfera_selecionada", "Federal")
    if esfera in ("Federal", "Estadual", "Municipal"):
        titulo = f"Esfera {esfera}"
    else:
        titulo = esfera

    st.markdown(f'<p class="mm-title">{titulo}</p>', unsafe_allow_html=True)
    st.markdown('<p class="mm-subtitle">Detalhamento das contas cadastradas para esta esfera</p>', unsafe_allow_html=True)

    conn = get_conn()
    total = conn.execute("SELECT COALESCE(SUM(valor_total),0) FROM contas_receber WHERE esfera=?", (esfera,)).fetchone()[0]
    linhas = conn.execute(
        "SELECT id, numero_conta, fonte, tipo_recurso, valor_total, data_recebimento FROM contas_receber WHERE esfera=? ORDER BY id DESC",
        (esfera,),
    ).fetchall()
    conn.close()

    st.markdown(
        f'<div class="mm-card" style="margin-bottom:20px;">'
        f'<div class="mm-card-label">Total da Esfera</div>'
        f'<div class="mm-card-value">{format_currency(total)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if not linhas:
        st.info("Nenhuma conta cadastrada para esta esfera ainda.")
    else:
        for linha in linhas:
            cid, numero_conta, fonte, tipo_recurso, valor_total, data_recebimento = linha
            st.markdown(
                f'<div class="mm-card" style="text-align:left;margin-bottom:10px;">'
                f'<strong>Conta {numero_conta}</strong> - Fonte {fonte}<br>'
                f'{tipo_recurso} - {format_currency(valor_total)} - {data_recebimento}'
                f'</div>',
                unsafe_allow_html=True,
            )

    if st.button("Voltar ao Inicio", key="btn_voltar_inicio", use_container_width=True):
        st.session_state["pagina"] = "Inicio"
        st.rerun()

def pagina_cadastro_contas():
    st.markdown('<p class="mm-title">Cadastro de Contas</p>', unsafe_allow_html=True)
    st.markdown('<p class="mm-subtitle">Registre as contas a receber por esfera de gestao</p>', unsafe_allow_html=True)

    esfera = st.selectbox("Esfera", ["Federal", "Estadual", "Municipal", "Transferencia", "Transposicao"], key="esfera_cad_fora")

    fonte_vinculada = get_fonte(esfera)
    st.markdown(
        f'<div class="mm-card" style="text-align:left;margin-bottom:16px;padding:14px 18px;">'
        f'<div class="mm-card-label">Fonte Vinculada</div>'
        f'<div class="mm-card-value" style="font-size:20px;">{fonte_vinculada}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    with st.form("form_cadastro_conta"):
        col1, col2 = st.columns(2)
        with col1:
            numero_conta = st.text_input("Numero da Conta")
            referencia_tipo = st.text_input("Tipo de Referencia")
            referencia_numero = st.text_input("Numero de Referencia")
        with col2:
            tipo_recurso = st.selectbox("Tipo de Recurso", ["Custeio", "Investimento", "Custeio e Investimento"])
            valor_custeio = st.text_input("Valor Custeio", value="R$ 0,00")
            valor_investimento = st.text_input("Valor Investimento", value="R$ 0,00")
            data_recebimento = st.date_input("Data de Recebimento", value=datetime.now())

        programa_politica = st.text_input("Programa / Politica")
        setor_gasto = st.text_input("Setor de Gasto")

        salvar = st.form_submit_button("Salvar Conta", use_container_width=True)

        if salvar:
            vc = parse_valor(valor_custeio)
            vi = parse_valor(valor_investimento)
            vt = vc + vi
            if vt <= 0:
                st.error("Informe pelo menos um valor de custeio ou investimento.")
            else:
                conn = get_conn()
                conn.execute(
                    "INSERT INTO contas_receber (esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso, valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento, programa_politica, setor_gasto) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (esfera, numero_conta, get_fonte(esfera), referencia_tipo, referencia_numero, tipo_recurso, vc, vi, vt, data_recebimento.strftime("%d/%m/%Y"), programa_politica, setor_gasto),
                )
                conn.commit()
                conn.close()
                st.success("Conta cadastrada com sucesso!")
                st.rerun()

def pagina_contas_cadastradas():
    st.markdown('<p class="mm-title">Contas Cadastradas</p>', unsafe_allow_html=True)
    st.markdown('<p class="mm-subtitle">Consulte todas as contas registradas no sistema</p>', unsafe_allow_html=True)

    conn = get_conn()
    linhas = conn.execute(
        "SELECT id, esfera, numero_conta, fonte, tipo_recurso, valor_total, data_recebimento FROM contas_receber ORDER BY id DESC"
    ).fetchall()
    conn.close()

    if not linhas:
        st.info("Nenhuma conta cadastrada ainda.")
        return

    for linha in linhas:
        cid, esfera, numero_conta, fonte, tipo_recurso, valor_total, data_recebimento = linha
        st.markdown(
            f'<div class="mm-card" style="text-align:left;margin-bottom:10px;">'
            f'<strong>{esfera}</strong> - Conta {numero_conta} - Fonte {fonte}<br>'
            f'{tipo_recurso} - {format_currency(valor_total)} - {data_recebimento}'
            f"</div>",
            unsafe_allow_html=True,
        )

def pagina_realizar_compras():
    st.markdown('<p class="mm-title">Realizar Compras</p>', unsafe_allow_html=True)
    st.markdown('<p class="mm-subtitle">Registre ordens de compra vinculadas as contas cadastradas</p>', unsafe_allow_html=True)

    conn = get_conn()
    contas = conn.execute("SELECT id, esfera, numero_conta, fonte, valor_total FROM contas_receber ORDER BY id DESC").fetchall()
    conn.close()

    if not contas:
        st.info("Cadastre uma conta antes de realizar compras.")
        return

    opcoes = {f"{c[1]} - Conta {c[2]} - Fonte {c[3]}": c for c in contas}
    escolha = st.selectbox("Selecione a conta", list(opcoes.keys()))
    conta_selecionada = opcoes[escolha]

    with st.form("form_compra"):
        ficha = st.text_input("Ficha")
        tipo_despesa = st.selectbox("Tipo de Despesa", ["Material de Consumo", "Servico PF", "Servico PJ", "Distribuicao Gratuita", "Equipamento"])
        data_compra = st.date_input("Data da Compra", value=datetime.now())
        valor_compra = st.text_input("Valor da Compra", value="R$ 0,00")
        produto_servico = st.text_area("Descricao do Produto/Servico")

        registrar = st.form_submit_button("Registrar Compra", use_container_width=True)

        if registrar:
            vc = parse_valor(valor_compra)
            if vc <= 0:
                st.error("Informe um valor de compra maior que zero.")
            else:
                conn = get_conn()
                conn.execute(
                    "INSERT INTO ordens_compra (conta_receber_id, esfera, numero_conta, fonte, ficha, tipo_despesa, data_compra, valor_compra, produto_servico, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (conta_selecionada[0], conta_selecionada[1], conta_selecionada[2], conta_selecionada[3], ficha, tipo_despesa, data_compra.strftime("%d/%m/%Y"), vc, produto_servico, datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
                )
                conn.commit()
                conn.close()
                st.success("Compra registrada com sucesso!")
                st.rerun()

def pagina_superavit():
    st.markdown('<p class="mm-title">Superavit Financeiro</p>', unsafe_allow_html=True)
    st.markdown('<p class="mm-subtitle">Controle o superavit de recursos de exercicios anteriores</p>', unsafe_allow_html=True)

    with st.form("form_superavit"):
        esfera = st.selectbox("Esfera", ["Federal", "Estadual"])
        valor = st.text_input("Valor do Superavit", value="R$ 0,00")
        registrar = st.form_submit_button("Registrar Superavit", use_container_width=True)

        if registrar:
            v = parse_valor(valor)
            if v <= 0:
                st.error("Informe um valor maior que zero.")
            else:
                conn = get_conn()
                conn.execute(
                    "INSERT INTO superavit (esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, created_at) VALUES (?,?,?,?,?,?)",
                    (esfera, get_fonte(esfera), get_fonte_superavit(esfera), v, v, datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
                )
                conn.commit()
                conn.close()
                st.success("Superavit registrado com sucesso!")
                st.rerun()

    conn = get_conn()
    linhas = conn.execute("SELECT esfera, fonte_superavit, saldo_total, saldo_restante, created_at FROM superavit ORDER BY id DESC").fetchall()
    conn.close()

    if linhas:
        st.markdown("<br>", unsafe_allow_html=True)
        for esfera, fonte_sup, saldo_total, saldo_restante, criado in linhas:
            st.markdown(
                f'<div class="mm-card" style="text-align:left;margin-bottom:10px;">'
                f"<strong>{esfera}</strong> - Fonte {fonte_sup}<br>"
                f"Total: {format_currency(saldo_total)} - Restante: {format_currency(saldo_restante)} - {criado}"
                f"</div>",
                unsafe_allow_html=True,
            )

def pagina_programas_saude():
    st.markdown('<p class="mm-title">Programas de Saude</p>', unsafe_allow_html=True)
    st.markdown('<p class="mm-subtitle">Cadastre e acompanhe os programas municipais de saude</p>', unsafe_allow_html=True)

    with st.form("form_programa"):
        nome = st.text_input("Nome do Programa")
        descricao = st.text_area("Descricao")
        salvar = st.form_submit_button("Salvar Programa", use_container_width=True)

        if salvar:
            if not nome:
                st.error("Informe o nome do programa.")
            else:
                conn = get_conn()
                conn.execute(
                    "INSERT INTO programas_saude (nome, descricao, created_at) VALUES (?,?,?)",
                    (nome, descricao, datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
                )
                conn.commit()
                conn.close()
                st.success("Programa cadastrado com sucesso!")
                st.rerun()

    conn = get_conn()
    linhas = conn.execute("SELECT nome, descricao, created_at FROM programas_saude ORDER BY id DESC").fetchall()
    conn.close()

    if linhas:
        st.markdown("<br>", unsafe_allow_html=True)
        for nome, descricao, criado in linhas:
            st.markdown(
                f'<div class="mm-card" style="text-align:left;margin-bottom:10px;">'
                f"<strong>{nome}</strong><br>{descricao}<br>"
                f'<span style="color:#94a3b8;font-size:11px;">{criado}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )

def pagina_upload_arquivos():
    st.markdown('<p class="mm-title">Upload de Arquivos</p>', unsafe_allow_html=True)
    st.markdown('<p class="mm-subtitle">Envie documentos e comprovantes do sistema</p>', unsafe_allow_html=True)

    bloco = st.selectbox("Categoria do Arquivo", ["Contas", "Compras", "Programas de Saude", "Plano Municipal", "Conselho", "Outros"])
    arquivo = st.file_uploader("Selecione o arquivo", type=["pdf", "docx", "doc", "txt", "csv", "xlsx"])

    if st.button("Enviar Arquivo", use_container_width=True):
        if not arquivo:
            st.error("Selecione um arquivo antes de enviar.")
        else:
            dados_bytes = arquivo.read()
            texto = extrair_texto(dados_bytes, arquivo.name)
            conn = get_conn()
            conn.execute(
                "INSERT INTO arquivos_saude (bloco, nome_arquivo, conteudo_texto, dados_arquivo, data_upload) VALUES (?,?,?,?,?)",
                (bloco, arquivo.name, texto, dados_bytes, datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
            )
            conn.commit()
            conn.close()
            st.success("Arquivo enviado com sucesso!")
            st.rerun()

    conn = get_conn()
    linhas = conn.execute("SELECT bloco, nome_arquivo, data_upload FROM arquivos_saude ORDER BY id DESC").fetchall()
    conn.close()

    if linhas:
        st.markdown("<br>", unsafe_allow_html=True)
        for bloco_item, nome_arquivo, data_upload in linhas:
            st.markdown(
                f'<div class="mm-card" style="text-align:left;margin-bottom:10px;">'
                f"<strong>{nome_arquivo}</strong> - {bloco_item}<br>"
                f'<span style="color:#94a3b8;font-size:11px;">{data_upload}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )

def pagina_plano_municipal():
    st.markdown('<p class="mm-title">Plano Municipal de Saude</p>', unsafe_allow_html=True)
    st.markdown('<p class="mm-subtitle">Diretrizes e eixos estrategicos do PMS</p>', unsafe_allow_html=True)

    st.markdown(
        '<div class="mm-card" style="text-align:left;">'
        "O Plano Municipal de Saude (PMS) e o instrumento de planejamento que orienta a gestao "
        "municipal do SUS, definindo diretrizes, objetivos, metas e indicadores para o periodo "
        "de vigencia establecido."
        "</div>",
        unsafe_allow_html=True,
    )

def pagina_norte_gestao():
    st.markdown('<p class="mm-title">Norte da Minha Gestao</p>', unsafe_allow_html=True)
    st.markdown('<p class="mm-subtitle">Diretrizes estrategicas da Secretaria Municipal de Saude</p>', unsafe_allow_html=True)

    diretrizes = [
        ("Fortalecimento da Atencao Primaria", "Ampliar a cobertura da Estrategia Saude da Familia e fortalecer o vinculo com a comunidade."),
        ("Eficiencia na Gestao Financeira", "Otimizar recursos publicos e garantir transparencia nos repasses."),
        ("Valorizacao dos Profissionais", "Investir em capacitacao continua e melhores condicoes de trabalho."),
        ("Integracao Regional", "Fortalecer a parceria com o CISLAV e demais consorcios, ampliando o acesso a consultas especializadas e exames."),
        ("Controle Social e Transparencia", "Garantir a participacao ativa do Conselho Municipal de Saude."),
    ]

    for titulo, descricao in diretrizes:
        st.markdown(
            f'<div class="mm-card" style="text-align:left;margin-bottom:10px;">'
            f"<strong>{titulo}</strong><br>{descricao}"
            f"</div>",
            unsafe_allow_html=True,
        )

def pagina_conselho():
    st.markdown('<p class="mm-title">Conselho Municipal de Saude</p>', unsafe_allow_html=True)
    st.markdown('<p class="mm-subtitle">Cadastro de membros do conselho</p>', unsafe_allow_html=True)

    with st.form("form_conselho"):
        nome = st.text_input("Nome")
        segmento = st.selectbox("Segmento", ["Usuarios", "Trabalhadores", "Gestores", "Prestadores"])
        cargo = st.text_input("Cargo")
        email = st.text_input("E-mail")
        telefone = st.text_input("Telefone")
        data_posse = st.date_input("Data de Posse", value=datetime.now())

        salvar = st.form_submit_button("Cadastrar Membro", use_container_width=True)

        if salvar:
            if not nome:
                st.error("Informe o nome do membro.")
            else:
                conn = get_conn()
                conn.execute(
                    "INSERT INTO conselho (nome, segmento, cargo, email, telefone, data_posse) VALUES (?,?,?,?,?,?)",
                    (nome, segmento, cargo, email, telefone, data_posse.strftime("%d/%m/%Y")),
                )
                conn.commit()
                conn.close()
                st.success("Membro cadastrado com sucesso!")
                st.rerun()

    conn = get_conn()
    linhas = conn.execute("SELECT nome, segmento, cargo, data_posse FROM conselho ORDER BY id DESC").fetchall()
    conn.close()

    if linhas:
        st.markdown("<br>", unsafe_allow_html=True)
        for nome, segmento, cargo, data_posse in linhas:
            st.markdown(
                f'<div class="mm-card" style="text-align:left;margin-bottom:10px;">'
                f"<strong>{nome}</strong> - {cargo}<br>"
                f'<span style="color:#94a3b8;font-size:11px;">{segmento} - Posse em {data_posse}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )

def pagina_trocar_senha():
    st.markdown('<p class="mm-title">Trocar Senha</p>', unsafe_allow_html=True)
    st.markdown('<p class="mm-subtitle">Atualize sua senha de acesso</p>', unsafe_allow_html=True)

    with st.form("form_trocar_senha"):
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
        salvar = st.form_submit_button("Alterar Senha", use_container_width=True)

        if salvar:
            conn = get_conn()
            row = conn.execute(
                "SELECT id FROM users WHERE id=? AND password_hash=?",
                (st.session_state.get("usuario_id"), hash_senha(senha_atual)),
            ).fetchone()

            if not row:
                st.error("Senha atual incorreta.")
            elif nova_senha != confirmar_senha:
                st.error("A nova senha e a confirmacao nao coincidem.")
            elif len(nova_senha) < 6:
                st.error("A nova senha deve ter pelo menos 6 caracteres.")
            else:
                conn.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_senha(nova_senha), row[0]))
                conn.commit()
                st.success("Senha alterada com sucesso!")
            conn.close()

def menu_lateral():
    with st.sidebar:
        st.markdown('<p style="color:#7dd3fc;font-size:16px;font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-top:8px;margin-bottom:4px;">Aba de Navegacao</p>', unsafe_allow_html=True)
        st.markdown("---")

        paginas = [
            "Inicio",
            "Cadastro de Contas",
            "Contas Cadastradas",
            "Realizar Compras",
            "Superavit Financeiro",
            "Programas de Saude",
            "Upload de Arquivos",
            "Plano Municipal de Saude",
            "Norte da Minha Gestao",
            "Conselho Municipal de Saude",
            "Trocar Senha",
        ]

        for pagina in paginas:
            if st.button(pagina, key=f"nav_{pagina}", use_container_width=True):
                st.session_state["pagina"] = pagina
                st.rerun()

        st.markdown("---")
        if st.button("Sair", key="nav_sair", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["pagina"] = "Inicio"
            st.rerun()

def main():
    if not st.session_state["logged_in"]:
        tela_login()
        return

    menu_lateral()
    pagina = st.session_state.get("pagina", "Inicio")

    if pagina == "Inicio":
        pagina_inicio()
    elif pagina == "Esfera Detalhe":
        pagina_esfera_detalhe()
    elif pagina == "Cadastro de Contas":
        pagina_cadastro_contas()
    elif pagina == "Contas Cadastradas":
        pagina_contas_cadastradas()
    elif pagina == "Realizar Compras":
        pagina_realizar_compras()
    elif pagina == "Superavit Financeiro":
        pagina_superavit()
    elif pagina == "Programas de Saude":
        pagina_programas_saude()
    elif pagina == "Upload de Arquivos":
        pagina_upload_arquivos()
    elif pagina == "Plano Municipal de Saude":
        pagina_plano_municipal()
    elif pagina == "Norte da Minha Gestao":
        pagina_norte_gestao()
    elif pagina == "Conselho Municipal de Saude":
        pagina_conselho()
    elif pagina == "Trocar Senha":
        pagina_trocar_senha()

if __name__ == "__main__":
    main()
