import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime

st.set_page_config(page_title="MARMED - Gestao Financeira Publica Municipal", page_icon="🏛️", layout="wide")

DB_PATH = "marmed.db"

CSS = """
<style>
.stApp {
    background: linear-gradient(135deg, #0a0e27 0%, #16213e 50%, #0f3460 100%);
    color: #ffffff;
}
section[data-testid="stSidebar"] {
    background-color: #0a0e27;
    color: #ffffff;
}
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stSelectbox div {
    background-color: #16213e;
    color: #ffffff;
}
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    background-color: #16213e !important;
    color: #ffffff !important;
    border: 1px solid #0f3460 !important;
}
.stButton button {
    background: linear-gradient(135deg, #0f3460, #16213e) !important;
    color: #ffffff !important;
    border: 1px solid #1a73e8 !important;
    border-radius: 8px !important;
}
.stButton button:hover {
    background: linear-gradient(135deg, #1a73e8, #0f3460) !important;
}
.mm-brand-title {
    font-size: 96px;
    font-weight: bold;
    color: #ffffff;
    text-align: center;
    background: linear-gradient(135deg, #1a73e8, #00d2ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0px;
}
.mm-brand-subtitle {
    font-size: 34px;
    color: #a0c4ff;
    text-align: center;
    margin-top: 0px;
}
.mm-brand-institution {
    font-size: 24px;
    color: #7fa8d4;
    text-align: center;
    margin-top: 10px;
}
.mm-card {
    background-color: #16213e;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #0f3460;
    margin-bottom: 15px;
}
.mm-esfera-card {
    background: linear-gradient(135deg, #16213e, #0f3460);
    border-radius: 16px;
    padding: 30px;
    border: 1px solid #1a73e8;
    text-align: center;
    cursor: pointer;
}
.mm-esfera-card:hover {
    border-color: #00d2ff;
}
.mm-expander {
    background-color: #16213e !important;
    border-radius: 10px !important;
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


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
    admin_hash = hash_senha("Diretor2025#")
    c.execute("SELECT id FROM users WHERE username = ?", ("admin",))
    if c.fetchone() is None:
        c.execute("INSERT INTO users (username, password_hash, nome) VALUES (?, ?, ?)", ("admin", admin_hash, "Administrador"))
    conn.commit()
    conn.close()


def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def verificar_login(username, senha):
    conn = get_conn()
    c = conn.cursor()
    senha_hash = hash_senha(senha)
    c.execute("SELECT id, username, nome FROM users WHERE username = ? AND password_hash = ?", (username, senha_hash))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "username": row[1], "nome": row[2]}
    return None


def format_currency(valor):
    if valor is None:
        valor = 0.0
    s = f"{valor:,.2f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def get_fonte(esfera, tipo):
    fontes = {
        "Federal": 1600,
        "Estadual": 1621,
        "Municipal": 1500,
        "Transferencia": 1700,
        "Transposicao": 1800,
    }
    return fontes.get(esfera, 1500)


def get_fonte_superavit(esfera):
    fontes = {
        "Federal": 2600,
        "Estadual": 2621,
    }
    return fontes.get(esfera, 2600)


ESFERAS = ["Federal", "Estadual", "Municipal", "Transferencia", "Transposicao"]


def get_total_extra(conta_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(valor), 0) as total FROM recursos_extra WHERE conta_receber_id = ?", (conta_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0.0


def get_extras(conta_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, valor, descricao, data_add, created_at FROM recursos_extra WHERE conta_receber_id = ? ORDER BY created_at DESC", (conta_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_valor_original(conta_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(valor), 0) FROM recursos_extra WHERE conta_receber_id = ?", (conta_id,))
    total_extra = c.fetchone()[0]
    c.execute("SELECT valor_total FROM contas_receber WHERE id = ?", (conta_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0] - total_extra
    return 0.0


def pagina_login():
    st.markdown('<div class="mm-brand-title">MARMED</div>', unsafe_allow_html=True)
    st.markdown('<div class="mm-brand-subtitle">Gestao Financeira Publica Municipal</div>', unsafe_allow_html=True)
    st.markdown('<div class="mm-brand-institution">Prefeitura Municipal - Sistema Integrado de Gestao</div>', unsafe_allow_html=True)
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="mm-card">', unsafe_allow_html=True)
        st.subheader("🔐 Acesso ao Sistema")
        username = st.text_input("Usuario", key="login_user")
        senha = st.text_input("Senha", type="password", key="login_pass")
        if st.button("Entrar", use_container_width=True):
            user = verificar_login(username, senha)
            if user:
                st.session_state["logado"] = True
                st.session_state["usuario"] = user
                st.rerun()
            else:
                st.error("Usuario ou senha invalidos.")
        st.markdown("</div>", unsafe_allow_html=True)


def pagina_inicio():
    st.markdown('<div class="mm-brand-title">MARMED</div>', unsafe_allow_html=True)
    st.markdown('<div class="mm-brand-subtitle">Gestao Financeira Publica Municipal</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("🏛️ Esferas de Gestao")
    st.write("Selecione uma esfera para visualizar os detalhes das contas.")
    cols = st.columns(5)
    for i, esfera in enumerate(ESFERAS):
        with cols[i]:
            st.markdown('<div class="mm-esfera-card">', unsafe_allow_html=True)
            if st.button(esfera, key=f"btn_esfera_{esfera}", use_container_width=True):
                st.session_state["pagina"] = "esfera_detalhe"
                st.session_state["esfera_sel"] = esfera
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM contas_receber")
    total_contas = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(valor_total), 0) FROM contas_receber")
    total_valor = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ordens_compra")
    total_compras = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM superavit")
    total_superavit = c.fetchone()[0]
    conn.close()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Contas", total_contas)
    with col2:
        st.metric("Valor Total Recebido", format_currency(total_valor))
    with col3:
        st.metric("Ordens de Compra", total_compras)
    with col4:
        st.metric("Superavits", total_superavit)


def pagina_esfera_detalhe():
    esfera = st.session_state.get("esfera_sel", "Federal")
    st.subheader(f"🏛️ Esfera: {esfera}")
    if st.button("⬅️ Voltar ao Inicio"):
        st.session_state["pagina"] = "inicio"
        st.rerun()
    st.markdown("---")
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM contas_receber WHERE esfera = ? ORDER BY id DESC", (esfera,))
    contas = c.fetchall()
    if len(contas) == 0:
        st.info(f"Nenhuma conta cadastrada para a esfera {esfera}.")
        conn.close()
        return
    total_geral = 0
    for conta in contas:
        total_geral += conta["valor_total"] if conta["valor_total"] else 0
    st.metric(f"Valor Total da Esfera {esfera}", format_currency(total_geral))
    st.markdown("---")
    for conta in contas:
        conta_id = conta["id"]
        valor_original = get_valor_original(conta_id)
        total_extra = get_total_extra(conta_id)
        valor_atual = conta["valor_total"] if conta["valor_total"] else 0.0
        with st.expander(f"Conta #{conta_id} - {conta['numero_conta']} | {format_currency(valor_atual)}", expanded=False):
            st.markdown('<div class="mm-card">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Numero da Conta:** {conta['numero_conta']}")
                st.write(f"**Fonte:** {conta['fonte']}")
                st.write(f"**Tipo de Recurso:** {conta['tipo_recurso']}")
            with col2:
                st.write(f"**Referencia:** {conta['referencia_tipo']} {conta['referencia_numero']}")
                st.write(f"**Data Recebimento:** {conta['data_recebimento']}")
                st.write(f"**Setor Gasto:** {conta['setor_gasto']}")
            with col3:
                st.write(f"**Valor Original:** {format_currency(valor_original)}")
                st.write(f"**Valor Extra Total:** {format_currency(total_extra)}")
                st.write(f"**Valor Atual:** {format_currency(valor_atual)}")
            st.write(f"**Programa/Politica:** {conta['programa_politica']}")
            st.write(f"**Custeio:** {format_currency(conta['valor_pago_custeio'])} | **Investimento:** {format_currency(conta['valor_pago_investimento'])}")
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("#### ➕ Adicionar Recurso Extra")
            with st.form(key=f"form_extra_{conta_id}"):
                valor_extra = st.number_input("Valor (R$)", min_value=0.01, step=0.01, key=f"ve_{conta_id}")
                descricao_extra = st.text_area("Descricao", key=f"de_{conta_id}")
                submit_extra = st.form_submit_button("Salvar Recurso Extra")
                if submit_extra:
                    if valor_extra LESS_THAN= 0.01:
                        st.error("O valor deve ser maior que zero.")
                    else:
                        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        data_add = datetime.now().strftime("%Y-%m-%d")
                        c.execute("INSERT INTO recursos_extra (conta_receber_id, valor, descricao, data_add, created_at) VALUES (?, ?, ?, ?, ?)", (conta_id, valor_extra, descricao_extra, data_add, now))
                        c.execute("UPDATE contas_receber SET valor_total = valor_total + ? WHERE id = ?", (valor_extra, conta_id))
                        conn.commit()
                        st.success(f"Recurso extra de {format_currency(valor_extra)} adicionado com sucesso!")
                        st.rerun()
            st.markdown("---")
            st.markdown("#### 📋 Historico de Recursos Extras")
            extras = get_extras(conta_id)
            if len(extras) == 0:
                st.info("Nenhum recurso extra adicionado para esta conta.")
            else:
                for ex in extras:
                    st.markdown('<div class="mm-card">', unsafe_allow_html=True)
                    st.write(f"**ID:** {ex['id']} | **Valor:** {format_currency(ex['valor'])} | **Data:** {ex['data_add']}")
                    st.write(f"**Descricao:** {ex['descricao']}")
                    st.write(f"**Registrado em:** {ex['created_at']}")
                    st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("#### 🛒 Ordens de Compra desta Conta")
            c.execute("SELECT * FROM ordens_compra WHERE conta_receber_id = ? ORDER BY created_at DESC", (conta_id,))
            ordens = c.fetchall()
            if len(ordens) == 0:
                st.info("Nenhuma ordem de compra para esta conta.")
            else:
                for ordem in ordens:
                    st.write(f"**Ordem #{ordem['id']}** | Ficha: {ordem['ficha']} | {ordem['tipo_despesa']} | {format_currency(ordem['valor_compra'])} | {ordem['data_compra']}")
                    st.write(f"Produto/Servico: {ordem['produto_servico']}")
                    st.markdown("---")
    conn.close()


def pagina_cadastro_contas():
    st.subheader("📝 Cadastro de Contas a Receber")
    if st.button("⬅️ Voltar ao Inicio"):
        st.session_state["pagina"] = "inicio"
        st.rerun()
    st.markdown("---")
    st.write("**Selecione a Esfera (fora do formulario):**")
    esfera = st.selectbox("Esfera", ESFERAS, key="cad_esfera")
    st.markdown("---")
    with st.form("form_cadastro_conta"):
        col1, col2 = st.columns(2)
        with col1:
            numero_conta = st.text_input("Numero da Conta", key="cad_numero")
            fonte = st.text_input("Fonte", value=str(get_fonte(esfera, "")), key="cad_fonte")
            referencia_tipo = st.text_input("Tipo de Referencia", key="cad_ref_tipo")
            referencia_numero = st.text_input("Numero de Referencia", key="cad_ref_num")
            tipo_recurso = st.text_input("Tipo de Recurso", key="cad_tipo_recurso")
            valor_custeio = st.number_input("Valor Pago Custeio (R$)", min_value=0.0, step=0.01, key="cad_custeio")
            valor_investimento = st.number_input("Valor Pago Investimento (R$)", min_value=0.0, step=0.01, key="cad_invest")
        with col2:
            valor_total = st.number_input("Valor Total (R$)", min_value=0.0, step=0.01, key="cad_total")
            data_recebimento = st.date_input("Data de Recebimento", key="cad_data")
            programa_politica = st.text_input("Programa/Politica", key="cad_programa")
            setor_gasto = st.text_input("Setor Gasto", key="cad_setor")
        submit = st.form_submit_button("Cadastrar Conta")
        if submit:
            if numero_conta == "":
                st.error("Numero da conta e obrigatorio.")
            else:
                conn = get_conn()
                c = conn.cursor()
                c.execute("""INSERT INTO contas_receber
                    (esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso,
                     valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento,
                     programa_politica, setor_gasto)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso,
                     valor_custeio, valor_investimento, valor_total, str(data_recebimento),
                     programa_politica, setor_gasto))
                conn.commit()
                conn.close()
                st.success(f"Conta {numero_conta} cadastrada na esfera {esfera} com sucesso!")
                st.rerun()


def pagina_contas_cadastradas():
    st.subheader("📋 Contas Cadastradas")
    if st.button("⬅️ Voltar ao Inicio"):
        st.session_state["pagina"] = "inicio"
        st.rerun()
    st.markdown("---")
    filtro_esfera = st.selectbox("Filtrar por Esfera", ["Todas"] + ESFERAS, key="filtro_contas")
    conn = get_conn()
    c = conn.cursor()
    if filtro_esfera == "Todas":
        c.execute("SELECT * FROM contas_receber ORDER BY id DESC")
    else:
        c.execute("SELECT * FROM contas_receber WHERE esfera = ? ORDER BY id DESC", (filtro_esfera,))
    contas = c.fetchall()
    conn.close()
    if len(contas) == 0:
        st.info("Nenhuma conta cadastrada.")
        return
    for conta in contas:
        total_extra = get_total_extra(conta["id"])
        valor_original = conta["valor_total"] - total_extra if conta["valor_total"] else 0.0
        with st.expander(f"Conta #{conta['id']} - {conta['numero_conta']} | {conta['esfera']} | {format_currency(conta['valor_total'])}"):
            st.write(f"**Esfera:** {conta['esfera']}")
            st.write(f"**Fonte:** {conta['fonte']}")
            st.write(f"**Referencia:** {conta['referencia_tipo']} {conta['referencia_numero']}")
            st.write(f"**Tipo de Recurso:** {conta['tipo_recurso']}")
            st.write(f"**Valor Original:** {format_currency(valor_original)}")
            st.write(f"**Valor Extra Total:** {format_currency(total_extra)}")
            st.write(f"**Valor Total Atual:** {format_currency(conta['valor_total'])}")
            st.write(f"**Custeio:** {format_currency(conta['valor_pago_custeio'])}")
            st.write(f"**Investimento:** {format_currency(conta['valor_pago_investimento'])}")
            st.write(f"**Data Recebimento:** {conta['data_recebimento']}")
            st.write(f"**Programa/Politica:** {conta['programa_politica']}")
            st.write(f"**Setor Gasto:** {conta['setor_gasto']}")


def pagina_realizar_compras():
    st.subheader("🛒 Realizar Compras")
    if st.button("⬅️ Voltar ao Inicio"):
        st.session_state["pagina"] = "inicio"
        st.rerun()
    st.markdown("---")
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, numero_conta, esfera, fonte, valor_total FROM contas_receber ORDER BY id DESC")
    contas = c.fetchall()
    conn.close()
    if len(contas) == 0:
        st.info("Nenhuma conta disponivel. Cadastre uma conta primeiro.")
        return
    with st.form("form_compra"):
        conta_sel = st.selectbox("Selecionar Conta", [f"{c['id']} - {c['numero_conta']} ({c['esfera']})" for c in contas], key="compra_conta")
        conta_id = int(conta_sel.split(" - ")[0])
        conta_info = None
        for ct in contas:
            if ct["id"] == conta_id:
                conta_info = ct
                break
        ficha = st.text_input("Ficha", key="compra_ficha")
        tipo_despesa = st.selectbox("Tipo de Despesa", ["Custeio", "Investimento"], key="compra_tipo")
        data_compra = st.date_input("Data da Compra", key="compra_data")
        valor_compra = st.number_input("Valor da Compra (R$)", min_value=0.01, step=0.01, key="compra_valor")
        produto_servico = st.text_area("Produto/Servico", key="compra_produto")
        submit = st.form_submit_button("Registrar Compra")
        if submit:
            if ficha == "" or produto_servico == "":
                st.error("Ficha e Produto/Servico sao obrigatorios.")
            else:
                conn = get_conn()
                c = conn.cursor()
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("""INSERT INTO ordens_compra
                    (conta_receber_id, esfera, numero_conta, fonte, ficha, tipo_despesa, data_compra, valor_compra, produto_servico, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (conta_id, conta_info["esfera"], conta_info["numero_conta"], conta_info["fonte"],
                     ficha, tipo_despesa, str(data_compra), valor_compra, produto_servico, now))
                conn.commit()
                conn.close()
                st.success(f"Compra de {format_currency(valor_compra)} registrada com sucesso!")
                st.rerun()


def pagina_superavit():
    st.subheader("💰 Superavit")
    if st.button("⬅️ Voltar ao Inicio"):
        st.session_state["pagina"] = "inicio"
        st.rerun()
    st.markdown("---")
    with st.form("form_superavit"):
        col1, col2 = st.columns(2)
        with col1:
            esfera_sup = st.selectbox("Esfera", ["Federal", "Estadual"], key="sup_esfera")
            fonte_original = st.text_input("Fonte Original", key="sup_fonte_orig")
            fonte_superavit = st.text_input("Fonte Superavit", value=str(get_fonte_superavit(esfera_sup)), key="sup_fonte_sup")
        with col2:
            saldo_total = st.number_input("Saldo Total (R$)", min_value=0.0, step=0.01, key="sup_saldo_total")
            saldo_restante = st.number_input("Saldo Restante (R$)", min_value=0.0, step=0.01, key="sup_saldo_restante")
        submit = st.form_submit_button("Registrar Superavit")
        if submit:
            conn = get_conn()
            c = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO superavit (esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                      (esfera_sup, fonte_original, fonte_superavit, saldo_total, saldo_restante, now))
            conn.commit()
            conn.close()
            st.success("Superavit registrado com sucesso!")
            st.rerun()
    st.markdown("---")
    st.subheader("Superavits Registrados")
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM superavit ORDER BY id DESC")
    sups = c.fetchall()
    conn.close()
    if len(sups) == 0:
        st.info("Nenhum superavit registrado.")
    else:
        for sup in sups:
            with st.expander(f"Superavit #{sup['id']} - {sup['esfera']} | Saldo: {format_currency(sup['saldo_total'])}"):
                st.write(f"**Esfera:** {sup['esfera']}")
                st.write(f"**Fonte Original:** {sup['fonte_original']}")
                st.write(f"**Fonte Superavit:** {sup['fonte_superavit']}")
                st.write(f"**Saldo Total:** {format_currency(sup['saldo_total'])}")
                st.write(f"**Saldo Restante:** {format_currency(sup['saldo_restante'])}")
                st.write(f"**Criado em:** {sup['created_at']}")


def pagina_upload():
    st.subheader("📤 Upload de Arquivos de Saude")
    if st.button("⬅️ Voltar ao Inicio"):
        st.session_state["pagina"] = "inicio"
        st.rerun()
    st.markdown("---")
    bloco = st.selectbox("Bloco", ["Bloco 1", "Bloco 2", "Bloco 3", "Bloco 4"], key="up_bloco")
    arquivo = st.file_uploader("Selecionar Arquivo", type=["txt", "csv", "pdf", "xlsx", "docx"], key="up_arquivo")
    if st.button("Enviar Arquivo"):
        if arquivo is None:
            st.error("Selecione um arquivo.")
        else:
            conteudo = arquivo.read()
            try:
                texto = conteudo.decode("utf-8")
            except Exception:
                texto = "[Arquivo binario - conteudo nao textual]"
            conn = get_conn()
            c = conn.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO arquivos_saude (bloco, nome_arquivo, conteudo_texto, dados_arquivo, data_upload) VALUES (?, ?, ?, ?, ?)",
                      (bloco, arquivo.name, texto, conteudo, now))
            conn.commit()
            conn.close()
            st.success(f"Arquivo '{arquivo.name}' enviado para {bloco} com sucesso!")
            st.rerun()
    st.markdown("---")
    st.subheader("Arquivos Enviados")
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, bloco, nome_arquivo, data_upload FROM arquivos_saude ORDER BY id DESC")
    arqs = c.fetchall()
    conn.close()
    if len(arqs) == 0:
        st.info("Nenhum arquivo enviado.")
    else:
        for arq in arqs:
            st.write(f"**ID:** {arq['id']} | **Bloco:** {arq['bloco']} | **Arquivo:** {arq['nome_arquivo']} | **Data:** {arq['data_upload']}")


def pagina_trocar_senha():
    st.subheader("🔑 Trocar Senha")
    if st.button("⬅️ Voltar ao Inicio"):
        st.session_state["pagina"] = "inicio"
        st.rerun()
    st.markdown("---")
    usuario = st.session_state.get("usuario", {})
    with st.form("form_trocar_senha"):
        senha_atual = st.text_input("Senha Atual", type="password", key="ts_atual")
        nova_senha = st.text_input("Nova Senha", type="password", key="ts_nova")
        confirmar = st.text_input("Confirmar Nova Senha", type="password", key="ts_conf")
        submit = st.form_submit_button("Trocar Senha")
        if submit:
            user = verificar_login(usuario.get("username", ""), senha_atual)
            if user is None:
                st.error("Senha atual incorreta.")
            elif nova_senha != confirmar:
                st.error("As senhas nao coincidem.")
            elif len(nova_senha) LESS_THAN 6:
                st.error("A nova senha deve ter pelo menos 6 caracteres.")
            else:
                conn = get_conn()
                c = conn.cursor()
                novo_hash = hash_senha(nova_senha)
                c.execute("UPDATE users SET password_hash = ? WHERE id = ?", (novo_hash, usuario["id"]))
                conn.commit()
                conn.close()
                st.success("Senha alterada com sucesso!")


def sidebar():
    with st.sidebar:
        st.markdown("## 🏛️ MARMED")
        st.markdown("**Gestao Financeira Publica**")
        st.markdown("---")
        usuario = st.session_state.get("usuario", {})
        st.write(f"👤 **Usuario:** {usuario.get('nome', 'N/A')}")
        st.markdown("---")
        if st.button("Inicio", use_container_width=True, key="sb_inicio"):
            st.session_state["pagina"] = "inicio"
            st.rerun()
        if st.button("Cadastro de Contas", use_container_width=True, key="sb_cad"):
            st.session_state["pagina"] = "cadastro_contas"
            st.rerun()
        if st.button("Contas Cadastradas", use_container_width=True, key="sb_lista"):
            st.session_state["pagina"] = "contas_cadastradas"
            st.rerun()
        if st.button("Realizar Compras", use_container_width=True, key="sb_compras"):
            st.session_state["pagina"] = "realizar_compras"
            st.rerun()
        if st.button("Superavit", use_container_width=True, key="sb_sup"):
            st.session_state["pagina"] = "superavit"
            st.rerun()
        if st.button("Upload", use_container_width=True, key="sb_upload"):
            st.session_state["pagina"] = "upload"
            st.rerun()
        if st.button("Trocar Senha", use_container_width=True, key="sb_senha"):
            st.session_state["pagina"] = "trocar_senha"
            st.rerun()
        st.markdown("---")
        if st.button("Sair", use_container_width=True, key="sb_sair"):
            st.session_state["logado"] = False
            st.session_state["usuario"] = {}
            st.session_state["pagina"] = "inicio"
            st.rerun()


def main():
    init_db()
    if not st.session_state.get("logado", False):
        pagina_login()
        return
    sidebar()
    pagina = st.session_state.get("pagina", "inicio")
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


if __name__ == "__main__":
    main()
