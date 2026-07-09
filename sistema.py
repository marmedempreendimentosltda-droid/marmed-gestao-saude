import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="MARMED - Gestao Financeira", page_icon="🏛️", layout="wide")

DB_PATH = "marmed.db"

# ===================== CSS =====================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&display=swap');

.stApp {
    background: linear-gradient(135deg, #0a0e27 0%, #16213e 50%, #0f3460 100%);
    background-attachment: fixed;
    color: #e0e0e0;
}

section[data-testid="stSidebar"] {
    background: rgba(10, 14, 39, 0.95);
    border-right: 1px solid rgba(0, 212, 255, 0.2);
}

.glass-card {
    background: rgba(22, 33, 62, 0.6);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 20px;
    padding: 40px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    text-align: center;
    margin: 0 auto;
    max-width: 500px;
}

.mm-brand-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 96px;
    font-weight: 900;
    background: linear-gradient(90deg, #00d4ff, #00ff88, #00d4ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    letter-spacing: 8px;
    margin: 0;
    text-shadow: 0 0 40px rgba(0, 212, 255, 0.3);
}

.mm-login-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 84px;
    font-weight: 900;
    background: linear-gradient(90deg, #00d4ff, #00ff88);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    letter-spacing: 6px;
    margin: 0;
}

.mm-brand-subtitle {
    font-family: 'Inter', sans-serif;
    font-size: 22px;
    color: #00d4ff;
    text-align: center;
    margin-top: 10px;
    letter-spacing: 4px;
}

.mm-brand-institution {
    font-family: 'Inter', sans-serif;
    font-size: 18px;
    color: #a0a0a0;
    text-align: center;
    margin-top: 5px;
    letter-spacing: 2px;
}

.mm-badge {
    display: inline-block;
    background: rgba(0, 212, 255, 0.15);
    border: 1px solid rgba(0, 212, 255, 0.4);
    color: #00d4ff;
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 13px;
    margin: 5px;
    font-family: 'Inter', sans-serif;
}

.mm-card {
    background: rgba(22, 33, 62, 0.7);
    border: 1px solid rgba(0, 212, 255, 0.25);
    border-radius: 16px;
    padding: 20px;
    margin: 15px 0;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.mm-esfera-btn {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.15), rgba(0, 255, 136, 0.1));
    border: 2px solid rgba(0, 212, 255, 0.4);
    border-radius: 16px;
    padding: 25px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;
}

.mm-esfera-btn:hover {
    border-color: #00d4ff;
    box-shadow: 0 0 25px rgba(0, 212, 255, 0.4);
}

.mm-total-label {
    font-size: 14px;
    color: #a0a0a0;
    font-family: 'Inter', sans-serif;
}

.mm-total-value {
    font-size: 28px;
    font-weight: 700;
    color: #00ff88;
    font-family: 'Orbitron', sans-serif;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background: rgba(10, 14, 39, 0.8);
    color: #e0e0e0;
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 10px;
}

.stButton > button {
    background: linear-gradient(90deg, #00d4ff, #00ff88);
    color: #0a0e27;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    padding: 10px 24px;
    transition: all 0.3s;
}

.stButton > button:hover {
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.6);
    transform: translateY(-2px);
}

.stMetric {
    background: rgba(22, 33, 62, 0.6);
    border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: 12px;
    padding: 15px;
}

h1, h2, h3 {
    color: #00d4ff !important;
    font-family: 'Orbitron', sans-serif;
}

.stSidebar .stMarkdown, .stSidebar label, .stSidebar span {
    color: #e0e0e0 !important;
}
</style>
""", unsafe_allow_html=True)

# ===================== BANCO DE DADOS =====================
def init_db():
    conn = sqlite3.connect(DB_PATH)
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
        dados_arquivo BLOB,
        data_upload TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS recursos_extra (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conta_receber_id INTEGER,
        valor REAL,
        descricao TEXT,
        data_add TEXT,
        created_at TEXT
    )""")
    # Criar usuario admin padrao
    senha_hash = hash_senha("Diretor2025#")
    c.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password_hash, nome) VALUES (?, ?, ?)",
                  ("admin", senha_hash, "Administrador MARMED"))
    conn.commit()
    conn.close()

def get_conn():
    return sqlite3.connect(DB_PATH)

# ===================== FUNCOES OBRIGATORIAS =====================
def get_fonte(esfera):
    fontes = {
        "Federal": "1.600",
        "Estadual": "1.621",
        "Municipal": "1.500",
        "Transferencia": "1.700",
        "Transposicao": "1.800"
    }
    return fontes.get(esfera, "1.500")

def get_fonte_superavit(esfera):
    fontes = {
        "Federal": "2.600",
        "Estadual": "2.621"
    }
    return fontes.get(esfera, "2.600")

def format_currency(valor):
    if valor is None:
        return "R$ 0,00"
    try:
        valor = float(valor)
    except (ValueError, TypeError):
        return "R$ 0,00"
    s = f"{valor:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def verificar_login(username, senha):
    conn = get_conn()
    c = conn.cursor()
    senha_hash = hash_senha(senha)
    c.execute("SELECT id, username, nome FROM users WHERE username = ? AND password_hash = ?",
              (username, senha_hash))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "username": row[1], "nome": row[2]}
    return None

def parse_valor(texto):
    if texto is None:
        return 0.0
    texto = str(texto).strip()
    if texto == "":
        return 0.0
    texto = texto.replace("R$", "").replace(" ", "").replace("\u00a0", "")
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return 0.0

# ===================== HELPERS DB =====================
def total_esfera(esfera):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(valor_total), 0) FROM contas_receber WHERE esfera = ?", (esfera,))
    total = c.fetchone()[0]
    conn.close()
    return total

def listar_contas_esfera(esfera):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT id, numero_conta, fonte, tipo_recurso, valor_total, data_recebimento,
                programa_politica, setor_gasto, referencia_tipo, referencia_numero,
                valor_pago_custeio, valor_pago_investimento
                FROM contas_receber WHERE esfera = ? ORDER BY id DESC""", (esfera,))
    rows = c.fetchall()
    conn.close()
    return rows

def total_recursos_extra(conta_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(valor), 0) FROM recursos_extra WHERE conta_receber_id = ?", (conta_id,))
    total = c.fetchone()[0]
    conn.close()
    return total

def listar_recursos_extra(conta_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, valor, descricao, data_add, created_at FROM recursos_extra WHERE conta_receber_id = ? ORDER BY id DESC", (conta_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def listar_compras_conta(conta_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT id, ficha, tipo_despesa, data_compra, valor_compra, produto_servico
                FROM ordens_compra WHERE conta_receber_id = ? ORDER BY id DESC""", (conta_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def listar_todas_contas():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT id, esfera, numero_conta, fonte, tipo_recurso, valor_total,
                data_recebimento, programa_politica, setor_gasto
                FROM contas_receber ORDER BY id DESC""")
    rows = c.fetchall()
    conn.close()
    return rows

def listar_superavit():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, created_at FROM superavit ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def listar_arquivos():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, bloco, nome_arquivo, data_upload FROM arquivos_saude ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

# ===================== PAGINAS =====================
def tela_login():
    st.markdown("<div style='margin-top:60px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="glass-card">
        <h1 class="mm-login-title">MARMED</h1>
        <p class="mm-brand-subtitle">GESTAO FINANCEIRA PUBLICA</p>
        <p class="mm-brand-institution">Municipal de Luminarias - MG</p>
        <div style='margin-top:20px'>
            <span class="mm-badge">🏛️ Setor Publico</span>
            <span class="mm-badge">💰 Gestao Financeira</span>
            <span class="mm-badge">📊 Controle Total</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='max-width:400px;margin:30px auto 0 auto'>", unsafe_allow_html=True)
    with st.form("login_form"):
        username = st.text_input("👤 Usuario", key="login_user")
        senha = st.text_input("🔒 Senha", type="password", key="login_pass")
        submit = st.form_submit_button("Entrar", use_container_width=True)
        if submit:
            user = verificar_login(username, senha)
            if user:
                st.session_state["logado"] = True
                st.session_state["usuario"] = user
                st.session_state["pagina"] = "inicio"
                st.rerun()
            else:
                st.error("Usuario ou senha invalidos!")
    st.markdown("</div>", unsafe_allow_html=True)

def pagina_inicial():
    st.markdown("<h1 class='mm-brand-title'>MARMED</h1>", unsafe_allow_html=True)
    st.markdown("<p class='mm-brand-subtitle'>GESTAO FINANCEIRA PUBLICA MUNICIPAL</p>", unsafe_allow_html=True)
    st.markdown("<p class='mm-brand-institution'>Prefeitura Municipal de Luminarias - Minas Gerais</p>", unsafe_allow_html=True)
    st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)

    st.markdown("<h3 style='text-align:center'>Esferas Financeiras</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#a0a0a0'>Selecione uma esfera para ver detalhes</p>", unsafe_allow_html=True)

    esferas = ["Federal", "Estadual", "Municipal", "Transferencia", "Transposicao"]
    cols = st.columns(len(esferas))
    for i, esfera in enumerate(esferas):
        with cols[i]:
            total = total_esfera(esfera)
            st.markdown(f"""
            <div class="mm-esfera-btn">
                <div style='font-size:20px;font-weight:700;color:#00d4ff;font-family:Orbitron'>{esfera}</div>
                <div style='font-size:12px;color:#a0a0a0;margin-top:5px'>Fonte: {get_fonte(esfera)}</div>
                <div class="mm-total-label" style='margin-top:15px'>Total</div>
                <div class="mm-total-value">{format_currency(total)}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Acessar {esfera}", key=f"btn_esfera_{esfera}", use_container_width=True):
                st.session_state["pagina"] = "esfera_detalhe"
                st.session_state["esfera_selecionada"] = esfera
                st.rerun()

def pagina_esfera_detalhe():
    esfera = st.session_state.get("esfera_selecionada", "Federal")
    if st.button("⬅ Voltar", key="voltar_esfera"):
        st.session_state["pagina"] = "inicio"
        st.rerun()

    st.markdown(f"<h2>Esfera: {esfera}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#00d4ff'>Fonte Vinculada: <b>{get_fonte(esfera)}</b></p>", unsafe_allow_html=True)

    total = total_esfera(esfera)
    st.metric(label="Total da Esfera", value=format_currency(total))
    st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

    contas = listar_contas_esfera(esfera)
    if not contas:
        st.info("Nenhuma conta cadastrada nesta esfera.")
        return

    st.markdown("<h3>Contas Recebidas</h3>", unsafe_allow_html=True)
    for conta in contas:
        cid = conta[0]
        numero_conta = conta[1]
        fonte = conta[2]
        tipo_recurso = conta[3]
        valor_total = conta[4]
        data_receb = conta[5]
        programa = conta[6]
        setor = conta[7]
        ref_tipo = conta[8]
        ref_num = conta[9]
        custeio = conta[10]
        investimento = conta[11]

        extra_total = total_recursos_extra(cid)
        valor_original = valor_total - extra_total

        st.markdown(f"""
        <div class="mm-card">
            <div style='display:flex;justify-content:space-between;align-items:center'>
                <div>
                    <div style='font-size:18px;font-weight:700;color:#00d4ff'>Conta: {numero_conta}</div>
                    <div style='font-size:13px;color:#a0a0a0'>Fonte: {fonte} | Tipo: {tipo_recurso or 'N/A'}</div>
                    <div style='font-size:13px;color:#a0a0a0'>Data: {data_receb or 'N/A'}</div>
                    <div style='font-size:13px;color:#a0a0a0'>Programa: {programa or 'N/A'} | Setor: {setor or 'N/A'}</div>
                    <div style='font-size:13px;color:#a0a0a0'>Referencia: {ref_tipo or 'N/A'} {ref_num or ''}</div>
                </div>
                <div style='text-align:right'>
                    <div style='font-size:12px;color:#a0a0a0'>Valor Original</div>
                    <div style='font-size:18px;color:#e0e0e0;font-weight:700'>{format_currency(valor_original)}</div>
                    <div style='font-size:12px;color:#00ff88;margin-top:8px'>Recursos Extra</div>
                    <div style='font-size:16px;color:#00ff88;font-weight:700'>{format_currency(extra_total)}</div>
                    <div style='font-size:12px;color:#00d4ff;margin-top:8px'>Valor Atual</div>
                    <div style='font-size:22px;color:#00d4ff;font-weight:900'>{format_currency(valor_total)}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_btn, col_info = st.columns([1, 3])
        with col_btn:
            if st.button(f"➕ Adicionar Recurso Extra", key=f"btn_extra_{cid}", use_container_width=True):
                st.session_state[f"show_form_extra_{cid}"] = True
                st.rerun()

        if st.session_state.get(f"show_form_extra_{cid}", False):
            with st.form(f"form_extra_{cid}"):
                st.markdown("#### Adicionar Recurso Extra")
                valor_extra = st.text_input("Valor (R$)", key=f"val_extra_{cid}")
                descricao = st.text_area("Descricao", key=f"desc_extra_{cid}")
                data_add = st.date_input("Data", value=datetime.now(), key=f"data_extra_{cid}")
                col_s, col_c = st.columns(2)
                with col_s:
                    salvar = st.form_submit_button("Salvar Recurso Extra", use_container_width=True)
                with col_c:
                    cancelar = st.form_submit_button("Cancelar", use_container_width=True)
                if salvar:
                    v = parse_valor(valor_extra)
                    if v <= 0:
                        st.error("Informe um valor valido maior que zero.")
                    else:
                        conn = get_conn()
                        c = conn.cursor()
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        c.execute("""INSERT INTO recursos_extra (conta_receber_id, valor, descricao, data_add, created_at)
                                    VALUES (?, ?, ?, ?, ?)""",
                                  (cid, v, descricao, str(data_add), now))
                        c.execute("UPDATE contas_receber SET valor_total = valor_total + ? WHERE id = ?", (v, cid))
                        conn.commit()
                        conn.close()
                        st.session_state[f"show_form_extra_{cid}"] = False
                        st.success("Recurso extra adicionado com sucesso!")
                        st.rerun()
                if cancelar:
                    st.session_state[f"show_form_extra_{cid}"] = False
                    st.rerun()

        # Historico de recursos extras
        extras = listar_recursos_extra(cid)
        if extras:
            st.markdown("<div style='margin-left:20px;margin-top:10px'>", unsafe_allow_html=True)
            st.markdown("**Historico de Recursos Extras:**")
            for ex in extras:
                st.markdown(f"- {format_currency(ex[1])} | {ex[2] or 'Sem descricao'} | Data: {ex[3]} | Criado: {ex[4]}")
            st.markdown("</div>", unsafe_allow_html=True)

        # Compras da conta
        compras = listar_compras_conta(cid)
        if compras:
            st.markdown("<div style='margin-left:20px;margin-top:10px'>", unsafe_allow_html=True)
            st.markdown("**Compras da Conta:**")
            for cp in compras:
                st.markdown(f"- Ficha: {cp[1]} | {cp[2]} | {cp[3]} | {format_currency(cp[4])} | {cp[5]}")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)

def pagina_cadastro_contas():
    st.markdown("<h2>Cadastro de Contas</h2>", unsafe_allow_html=True)

    esfera = st.selectbox("Esfera", ["Federal", "Estadual", "Municipal", "Transferencia", "Transposicao"],
                          key="esfera_cad_fora")

    st.markdown(f"""
    <div class="mm-card">
        <div style='font-size:14px;color:#a0a0a0'>Fonte Vinculada (tempo real)</div>
        <div style='font-size:32px;font-weight:900;color:#00d4ff;font-family:Orbitron'>{get_fonte(esfera)}</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("form_cadastro_conta"):
        numero_conta = st.text_input("Numero da Conta")
        fonte = st.text_input("Fonte", value=get_fonte(esfera))
        referencia_tipo = st.text_input("Tipo de Referencia")
        referencia_numero = st.text_input("Numero de Referencia")
        tipo_recurso = st.text_input("Tipo de Recurso")
        valor_custeio = st.text_input("Valor Pago Custeio (R$)")
        valor_invest = st.text_input("Valor Pago Investimento (R$)")
        valor_total = st.text_input("Valor Total (R$)")
        data_receb = st.date_input("Data de Recebimento", value=datetime.now())
        programa = st.text_input("Programa / Politica")
        setor = st.text_input("Setor do Gasto")
        submit = st.form_submit_button("Cadastrar Conta", use_container_width=True)

        if submit:
            vc = parse_valor(valor_custeio)
            vi = parse_valor(valor_invest)
            vt = parse_valor(valor_total)
            if vt <= 0:
                vt = vc + vi
            if numero_conta == "":
                st.error("Informe o numero da conta.")
            else:
                conn = get_conn()
                c = conn.cursor()
                c.execute("""INSERT INTO contas_receber
                    (esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso,
                     valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento,
                     programa_politica, setor_gasto)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                          (esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso,
                           vc, vi, vt, str(data_receb), programa, setor))
                conn.commit()
                conn.close()
                st.success("Conta cadastrada com sucesso!")

def pagina_contas_cadastradas():
    st.markdown("<h2>Contas Cadastradas</h2>", unsafe_allow_html=True)
    contas = listar_todas_contas()
    if not contas:
        st.info("Nenhuma conta cadastrada.")
        return
    dados = []
    for c in contas:
        dados.append({
            "ID": c[0],
            "Esfera": c[1],
            "Numero Conta": c[2],
            "Fonte": c[3],
            "Tipo Recurso": c[4],
            "Valor Total": format_currency(c[5]),
            "Data Recebimento": c[6],
            "Programa": c[7],
            "Setor": c[8]
        })
    st.dataframe(pd.DataFrame(dados), use_container_width=True)

def pagina_realizar_compras():
    st.markdown("<h2>Realizar Compras</h2>", unsafe_allow_html=True)
    contas = listar_todas_contas()
    if not contas:
        st.info("Nenhuma conta disponivel. Cadastre uma conta primeiro.")
        return
    opcoes = {f"{c[0]} - {c[1]} - {c[2]}": c for c in contas}
    selecionada = st.selectbox("Selecione a Conta", list(opcoes.keys()))
    conta = opcoes[seleciona_da] if selecionada else None
    if conta is None:
        return
    conta_id = conta[0]
    esfera = conta[1]
    numero_conta = conta[2]
    fonte = conta[3]

    with st.form("form_compra"):
        ficha = st.text_input("Ficha")
        tipo_despesa = st.text_input("Tipo de Despesa")
        data_compra = st.date_input("Data da Compra", value=datetime.now())
        valor_compra = st.text_input("Valor da Compra (R$)")
        produto = st.text_area("Produto / Servico")
        submit = st.form_submit_button("Registrar Compra", use_container_width=True)
        if submit:
            v = parse_valor(valor_compra)
            if v <= 0:
                st.error("Informe um valor valido.")
            else:
                conn = get_conn()
                c = conn.cursor()
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("""INSERT INTO ordens_compra
                    (conta_receber_id, esfera, numero_conta, fonte, ficha, tipo_despesa,
                     data_compra, valor_compra, produto_servico, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                          (conta_id, esfera, numero_conta, fonte, ficha, tipo_despesa,
                           str(data_compra), v, produto, now))
                conn.commit()
                conn.close()
                st.success("Compra registrada com sucesso!")

def pagina_superavit():
    st.markdown("<h2>Superavit</h2>", unsafe_allow_html=True)
    with st.form("form_superavit"):
        esfera = st.selectbox("Esfera", ["Federal", "Estadual"], key="sup_esfera")
        fonte_original = st.text_input("Fonte Original", value=get_fonte(esfera))
        fonte_superavit = st.text_input("Fonte Superavit", value=get_fonte_superavit(esfera))
        saldo_total = st.text_input("Saldo Total (R$)")
        saldo_restante = st.text_input("Saldo Restante (R$)")
        submit = st.form_submit_button("Cadastrar Superavit", use_container_width=True)
        if submit:
            st_ = parse_valor(saldo_total)
            sr = parse_valor(saldo_restante)
            conn = get_conn()
            c = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""INSERT INTO superavit
                (esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                      (esfera, fonte_original, fonte_superavit, st_, sr, now))
            conn.commit()
            conn.close()
            st.success("Superavit cadastrado!")

    st.markdown("<h3>Lista de Superavit</h3>", unsafe_allow_html=True)
    sups = listar_superavit()
    if not sups:
        st.info("Nenhum superavit cadastrado.")
    else:
        for s in sups:
            st.markdown(f"""
            <div class="mm-card">
                <b>Esfera:</b> {s[1]} | <b>Fonte Original:</b> {s[2]} | <b>Fonte Superavit:</b> {s[3]}<br>
                <b>Saldo Total:</b> {format_currency(s[4])} | <b>Saldo Restante:</b> {format_currency(s[5])}<br>
                <b>Criado:</b> {s[6]}
            </div>
            """, unsafe_allow_html=True)

def pagina_upload():
    st.markdown("<h2>Upload de Arquivos - Saude</h2>", unsafe_allow_html=True)
    bloco = st.text_input("Bloco", key="up_bloco")
    arquivo = st.file_uploader("Selecione o arquivo", key="up_file")
    if st.button("Enviar Arquivo", key="btn_upload"):
        if arquivo is not None:
            conteudo = arquivo.read()
            texto = conteudo.decode("utf-8", errors="ignore")
            conn = get_conn()
            c = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("""INSERT INTO arquivos_saude (bloco, nome_arquivo, conteudo_texto, dados_arquivo, data_upload)
                        VALUES (?, ?, ?, ?, ?)""",
                      (bloco, arquivo.name, texto, conteudo, now))
            conn.commit()
            conn.close()
            st.success("Arquivo enviado com sucesso!")
        else:
            st.error("Selecione um arquivo.")

    st.markdown("<h3>Arquivos Enviados</h3>", unsafe_allow_html=True)
    arqs = listar_arquivos()
    if not arqs:
        st.info("Nenhum arquivo enviado.")
    else:
        for a in arqs:
            st.markdown(f"""
            <div class="mm-card">
                <b>ID:</b> {a[0]} | <b>Bloco:</b> {a[1]} | <b>Arquivo:</b> {a[2]} | <b>Data:</b> {a[3]}
            </div>
            """, unsafe_allow_html=True)

def pagina_trocar_senha():
    st.markdown("<h2>Trocar Senha</h2>", unsafe_allow_html=True)
    usuario = st.session_state.get("usuario", {})
    with st.form("form_senha"):
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar = st.text_input("Confirmar Nova Senha", type="password")
        submit = st.form_submit_button("Alterar Senha", use_container_width=True)
        if submit:
            user = verificar_login(usuario.get("username", ""), senha_atual)
            if not user:
                st.error("Senha atual incorreta.")
            elif nova_senha != confirmar:
                st.error("As senhas nao conferem.")
            elif len(nova_senha) < 6:
                st.error("A nova senha deve ter no minimo 6 caracteres.")
            else:
                conn = get_conn()
                c = conn.cursor()
                c.execute("UPDATE users SET password_hash = ? WHERE username = ?",
                          (hash_senha(nova_senha), usuario.get("username")))
                conn.commit()
                conn.close()
                st.success("Senha alterada com sucesso!")

# ===================== NAVEGACAO =====================
def menu_lateral():
    with st.sidebar:
        st.markdown("## 🏛️ MARMED")
        st.markdown("*Gestao Financeira*")
        st.markdown("---")
        usuario = st.session_state.get("usuario", {})
        st.markdown(f"**Usuario:** {usuario.get('nome', 'N/A')}")
        st.markdown("---")

        paginas = [
            ("inicio", "🏠 Pagina Inicial"),
            ("esfera_detalhe", "📊 Esfera Detalhe"),
            ("cadastro_contas", "📝 Cadastrar Contas"),
            ("contas_cadastradas", "📋 Contas Cadastradas"),
            ("realizar_compras", "🛒 Realizar Compras"),
            ("superavit", "💰 Superavit"),
            ("upload", "📎 Upload Arquivos"),
            ("trocar_senha", "🔑 Trocar Senha"),
        ]
        for key, label in paginas:
            if st.button(label, key=f"menu_{key}", use_container_width=True):
                st.session_state["pagina"] = key
                if key == "esfera_detalhe" and "esfera_selecionada" not in st.session_state:
                    st.session_state["esfera_selecionada"] = "Federal"
                st.rerun()

        st.markdown("---")
        if st.button("🚪 Sair", key="menu_sair", use_container_width=True):
            st.session_state["logado"] = False
            st.session_state["usuario"] = None
            st.session_state["pagina"] = "login"
            st.rerun()

def main():
    init_db()
    if not st.session_state.get("logado", False):
        tela_login()
        return

    menu_lateral()
    pagina = st.session_state.get("pagina", "inicio")

    if pagina == "inicio":
        pagina_inicial()
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
        pagina_inicial()

if __name__ == "__main__":
    main()
