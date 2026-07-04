import streamlit as st
import sqlite3
import os
import re
import hashlib
import pandas as pd
from datetime import datetime
from io import BytesIO

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

DB_NAME = "marmed.db"

ADMIN_USER = "admin"
ADMIN_PASS = "Diretor2025#"

DARK_CSS = """
<style>
    .stApp {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #0d0d1a 100%);
        color: #e0e0ff;
    }
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #4ecdc4;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 0 0 10px rgba(78, 205, 196, 0.3);
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #6a93ff;
        margin-bottom: 0.8rem;
    }
    .card {
        background: rgba(20, 20, 40, 0.7);
        border: 1px solid rgba(100, 100, 180, 0.3);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #4ecdc4;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #a0a0cc;
    }
    .stButton>button {
        background: linear-gradient(135deg, #2a3f8a 0%, #1e2a5e 100%);
        color: #e0e0ff;
        border: 1px solid #4ecdc4;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #3a5fd8 0%, #2a3f8a 100%);
        box-shadow: 0 0 12px rgba(78, 205, 196, 0.4);
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div {
        background-color: rgba(15, 15, 30, 0.8);
        color: #e0e0ff;
        border: 1px solid rgba(100, 100, 180, 0.4);
        border-radius: 8px;
    }
    .stSidebar {
        background: linear-gradient(180deg, #0d0d1a 0%, #1a1a2e 100%);
    }
    .stSidebar .stRadio label {
        color: #c0c0ff;
        font-weight: 500;
    }
    .stExpander {
        background: rgba(20, 20, 40, 0.5);
        border-radius: 10px;
        border: 1px solid rgba(100, 100, 180, 0.2);
    }
    .info-box {
        background: rgba(30, 42, 94, 0.4);
        border-left: 4px solid #4ecdc4;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    .warning-box {
        background: rgba(94, 70, 30, 0.4);
        border-left: 4px solid #ff9f43;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
</style>
"""


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS contas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            esfera TEXT,
            nome TEXT,
            valor REAL,
            data TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            esfera TEXT,
            descricao TEXT,
            valor REAL,
            data TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS arquivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT,
            nome TEXT,
            tipo TEXT,
            texto TEXT,
            dados BLOB,
            data_upload TEXT
        )
    """)
    c.execute("SELECT COUNT(*) FROM usuarios WHERE username = ?", (ADMIN_USER,))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)", (ADMIN_USER, ADMIN_PASS))
    conn.commit()
    conn.close()


def get_conn():
    return sqlite3.connect(DB_NAME)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def login_user(username, password):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT password FROM usuarios WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row and row[0] == password:
        return True
    return False


def change_password(username, new_password):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE usuarios SET password = ? WHERE username = ?", (new_password, username))
    conn.commit()
    conn.close()


def format_currency(value):
    if value is None:
        return "R$ 0,00"
    return "R$ {:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")


def parse_currency(value_str):
    if not value_str:
        return 0.0
    cleaned = re.sub(r"[^\d,]", "", value_str)
    cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def extract_text(file, ext):
    texto = ""
    try:
        if ext == "pdf" and PDF_AVAILABLE:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    texto += page_text + "\n"
        elif ext == "docx" and DOCX_AVAILABLE:
            doc = docx.Document(file)
            for para in doc.paragraphs:
                texto += para.text + "\n"
        elif ext in ["txt", "csv"]:
            texto = file.read().decode("utf-8", errors="ignore")
    except Exception as e:
        texto = "Erro na leitura: " + str(e)
    return texto


def save_uploaded_file(categoria, uploaded_file):
    if uploaded_file is None:
        return
    ext = uploaded_file.name.split(".")[-1].lower()
    dados = uploaded_file.getvalue()
    texto = extract_text(BytesIO(dados), ext)
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO arquivos (categoria, nome, tipo, texto, dados, data_upload) VALUES (?, ?, ?, ?, ?, ?)",
        (categoria, uploaded_file.name, ext, texto, dados, datetime.now().strftime("%d/%m/%Y %H:%M"))
    )
    conn.commit()
    conn.close()


def get_files(categoria):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, nome, tipo, texto, data_upload FROM arquivos WHERE categoria = ? ORDER BY id DESC", (categoria,))
    rows = c.fetchall()
    conn.close()
    return rows


def delete_file(file_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM arquivos WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()


def search_files(categoria, termo):
    files = get_files(categoria)
    if not termo:
        return files
    termo_lower = termo.lower()
    result = []
    for f in files:
        if termo_lower in f[1].lower() or (f[3] and termo_lower in f[3].lower()):
            result.append(f)
    return result


def login_page():
    st.markdown(DARK_CSS, unsafe_allow_html=True)
    st.markdown("<div class='main-header'>MARMED - Gestão em Saúde</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center; color: #6a93ff;'>Acesso ao Sistema</h3>", unsafe_allow_html=True)
        username = st.text_input("Usuário", key="login_user")
        password = st.text_input("Senha", type="password", key="login_pass")
        if st.button("Entrar", use_container_width=True):
            if login_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")
        st.markdown("</div>", unsafe_allow_html=True)


def dashboard():
    st.markdown("<div class='main-header'>Dashboard MARMED</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Visão Geral por Esfera de Gestão</div>", unsafe_allow_html=True)
    esferas = ["Federal", "Estadual", "Municipal", "Transferência", "Transposição"]
    cols = st.columns(5)
    conn = get_conn()
    c = conn.cursor()
    for idx, esfera in enumerate(esferas):
        c.execute("SELECT COALESCE(SUM(valor), 0) FROM contas WHERE esfera = ?", (esfera,))
        total = c.fetchone()[0]
        c.execute("SELECT COALESCE(SUM(valor), 0) FROM compras WHERE esfera = ?", (esfera,))
        gasto = c.fetchone()[0]
        saldo = total - gasto
        with cols[idx]:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<div class='metric-label'>" + esfera + "</div>", unsafe_allow_html=True)
            st.markdown("<div class='metric-value'>" + format_currency(saldo) + "</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    conn.close()

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Resumo Financeiro</div>", unsafe_allow_html=True)
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(valor), 0) FROM contas")
    total_contas = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(valor), 0) FROM compras")
    total_compras = c.fetchone()[0]
    superavit = total_contas - total_compras
    conn.close()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='metric-label'>Total em Contas</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-value'>" + format_currency(total_contas) + "</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='metric-label'>Total em Compras</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-value'>" + format_currency(total_compras) + "</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='metric-label'>Superávit Financeiro</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-value'>" + format_currency(superavit) + "</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def cadastro_contas():
    st.markdown("<div class='main-header'>Cadastro de Contas</div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    esferas = ["Federal", "Estadual", "Municipal", "Transferência", "Transposição"]
    esfera = st.selectbox("Esfera", esferas, key="conta_esfera")
    nome = st.text_input("Nome da Conta / Fonte", key="conta_nome")
    valor_str = st.text_input("Valor (R$)", value="R$ 0,00", key="conta_valor")
    data = st.date_input("Data", key="conta_data")
    if st.button("Salvar Conta", key="btn_salvar_conta"):
        valor = parse_currency(valor_str)
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO contas (esfera, nome, valor, data) VALUES (?, ?, ?, ?)",
            (esfera, nome, valor, data.strftime("%d/%m/%Y"))
        )
        conn.commit()
        conn.close()
        st.success("Conta cadastrada com sucesso!")
    st.markdown("</div>", unsafe_allow_html=True)


def contas_cadastradas():
    st.markdown("<div class='main-header'>Contas Cadastradas</div>", unsafe_allow_html=True)
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, esfera, nome, valor, data FROM contas ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    if not rows:
        st.info("Nenhuma conta cadastrada.")
        return
    for row in rows:
        conta_id, esfera, nome, valor, data = row
        with st.expander(esfera + " - " + nome + " - " + format_currency(valor)):
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            edit = st.checkbox("Editar", key="edit_conta_" + str(conta_id))
            if edit:
                novo_esfera = st.selectbox("Esfera", ["Federal", "Estadual", "Municipal", "Transferência", "Transposição"], index=["Federal", "Estadual", "Municipal", "Transferência", "Transposição"].index(esfera), key="select_conta_" + str(conta_id))
                novo_nome = st.text_input("Nome", value=nome, key="nome_conta_" + str(conta_id))
                novo_valor_str = st.text_input("Valor", value=format_currency(valor), key="valor_conta_" + str(conta_id))
                novo_data = st.date_input("Data", value=datetime.strptime(data, "%d/%m/%Y"), key="data_conta_" + str(conta_id))
                if st.button("Atualizar", key="update_conta_" + str(conta_id)):
                    novo_valor = parse_currency(novo_valor_str)
                    conn = get_conn()
                    c = conn.cursor()
                    c.execute(
                        "UPDATE contas SET esfera = ?, nome = ?, valor = ?, data = ? WHERE id = ?",
                        (novo_esfera, novo_nome, novo_valor, novo_data.strftime("%d/%m/%Y"), conta_id)
                    )
                    conn.commit()
                    conn.close()
                    st.success("Conta atualizada!")
                    st.rerun()
            if st.button("Excluir", key="delete_conta_" + str(conta_id)):
                conn = get_conn()
                c = conn.cursor()
                c.execute("DELETE FROM contas WHERE id = ?", (conta_id,))
                conn.commit()
                conn.close()
                st.success("Conta excluída!")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


def realizar_compras():
    st.markdown("<div class='main-header'>Realizar Compras</div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    esferas = ["Federal", "Estadual", "Municipal", "Transferência", "Transposição"]
    esfera = st.selectbox("Esfera", esferas, key="compra_esfera")
    descricao = st.text_input("Descrição da Compra", key="compra_descricao")
    valor_str = st.text_input("Valor (R$)", value="R$ 0,00", key="compra_valor")
    data = st.date_input("Data", key="compra_data")
    if st.button("Registrar Compra", key="btn_salvar_compra"):
        valor = parse_currency(valor_str)
        conn = get_conn()
        c = conn.cursor()
        c.execute(
            "INSERT INTO compras (esfera, descricao, valor, data) VALUES (?, ?, ?, ?)",
            (esfera, descricao, valor, data.strftime("%d/%m/%Y"))
        )
        conn.commit()
        conn.close()
        st.success("Compra registrada com sucesso!")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='sub-header'>Compras Registradas</div>", unsafe_allow_html=True)
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, esfera, descricao, valor, data FROM compras ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    for row in rows:
        compra_id, esfera, descricao, valor, data = row
        with st.expander(esfera + " - " + descricao + " - " + format_currency(valor)):
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            edit = st.checkbox("Editar", key="edit_compra_" + str(compra_id))
            if edit:
                novo_esfera = st.selectbox("Esfera", esferas, index=esferas.index(esfera), key="select_compra_" + str(compra_id))
                novo_descricao = st.text_input("Descrição", value=descricao, key="desc_compra_" + str(compra_id))
                novo_valor_str = st.text_input("Valor", value=format_currency(valor), key="valor_compra_" + str(compra_id))
                novo_data = st.date_input("Data", value=datetime.strptime(data, "%d/%m/%Y"), key="data_compra_" + str(compra_id))
                if st.button("Atualizar", key="update_compra_" + str(compra_id)):
                    novo_valor = parse_currency(novo_valor_str)
                    conn = get_conn()
                    c = conn.cursor()
                    c.execute(
                        "UPDATE compras SET esfera = ?, descricao = ?, valor = ?, data = ? WHERE id = ?",
                        (novo_esfera, novo_descricao, novo_valor, novo_data.strftime("%d/%m/%Y"), compra_id)
                    )
                    conn.commit()
                    conn.close()
                    st.success("Compra atualizada!")
                    st.rerun()
            if st.button("Excluir", key="delete_compra_" + str(compra_id)):
                conn = get_conn()
                c = conn.cursor()
                c.execute("DELETE FROM compras WHERE id = ?", (compra_id,))
                conn.commit()
                conn.close()
                st.success("Compra excluída!")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)


def superavit_financeiro():
    st.markdown("<div class='main-header'>Superávit Financeiro</div>", unsafe_allow_html=True)
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(valor), 0) FROM contas")
    total_contas = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(valor), 0) FROM compras")
    total_compras = c.fetchone()[0]
    superavit = total_contas - total_compras
    conn.close()

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='metric-label'>Total em Contas</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-value'>" + format_currency(total_contas) + "</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='metric-label'>Total em Compras</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-value'>" + format_currency(total_compras) + "</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='metric-label'>Superávit</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-value'>" + format_currency(superavit) + "</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if superavit > 0:
        st.markdown("<div class='info-box'>Situação financeira: SUPERÁVIT POSITIVO</div>", unsafe_allow_html=True)
    elif superavit < 0:
        st.markdown("<div class='warning-box'>Situação financeira: DÉFICIT - atenção aos gastos</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='info-box'>Situação financeira: EQUILÍBRIO</div>", unsafe_allow_html=True)

    st.markdown("<div class='sub-header'>Distribuição por Esfera</div>", unsafe_allow_html=True)
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT esfera, COALESCE(SUM(valor), 0) FROM contas GROUP BY esfera")
    contas_por_esfera = c.fetchall()
    c.execute("SELECT esfera, COALESCE(SUM(valor), 0) FROM compras GROUP BY esfera")
    compras_por_esfera = c.fetchall()
    conn.close()
    saldos = {}
    for esfera, valor in contas_por_esfera:
        saldos[esfera] = valor
    for esfera, valor in compras_por_esfera:
        saldos[esfera] = saldos.get(esfera, 0) - valor
    if saldos:
        df = pd.DataFrame([{"Esfera": k, "Saldo": v} for k, v in saldos.items()])
        st.bar_chart(df.set_index("Esfera"))


def programas_saude():
    st.markdown("<div class='main-header'>Programas de Saúde</div>", unsafe_allow_html=True)
    aba1, aba2 = st.tabs(["MEDICAMENTOS", "PROGRAMAS DE SAÚDE"])

    with aba1:
        st.markdown("<div class='sub-header'>Medicamentos</div>", unsafe_allow_html=True)
        medicamentos = ["RENAME", "REMUME", "RENEM", "RENASES"]
        for med in medicamentos:
            with st.expander(med):
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                uploaded = st.file_uploader("Upload de arquivo - " + med, type=["pdf", "docx", "txt", "csv"], key="upload_med_" + med)
                if st.button("Enviar arquivo - " + med, key="btn_med_" + med):
                    save_uploaded_file("MEDICAMENTOS_" + med, uploaded)
                    st.success("Arquivo enviado!")
                busca = st.text_input("Buscar em documentos - " + med, key="busca_med_" + med)
                arquivos = search_files("MEDICAMENTOS_" + med, busca)
                if arquivos:
                    for arq in arquivos:
                        arq_id, nome, tipo, texto, data_upload = arq
                        st.write("- " + nome + " (" + data_upload + ")")
                        st.download_button("Download", data=BytesIO(texto.encode()) if texto else b"", file_name=nome, key="down_med_" + med + "_" + str(arq_id))
                        if st.button("Excluir", key="del_med_" + med + "_" + str(arq_id)):
                            delete_file(arq_id)
                            st.rerun()
                else:
                    st.info("Nenhum documento encontrado.")
                st.markdown("</div>", unsafe_allow_html=True)

    with aba2:
        st.markdown("<div class='sub-header'>Programas de Saúde</div>", unsafe_allow_html=True)
        programas = ["PAS", "RDQA", "RAG"]
        for prog in programas:
            with st.expander(prog):
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                uploaded = st.file_uploader("Upload de arquivo - " + prog, type=["pdf", "docx", "txt", "csv"], key="upload_prog_" + prog)
                if st.button("Enviar arquivo - " + prog, key="btn_prog_" + prog):
                    save_uploaded_file("PROGRAMAS_" + prog, uploaded)
                    st.success("Arquivo enviado!")
                busca = st.text_input("Buscar em documentos - " + prog, key="busca_prog_" + prog)
                arquivos = search_files("PROGRAMAS_" + prog, busca)
                if arquivos:
                    for arq in arquivos:
                        arq_id, nome, tipo, texto, data_upload = arq
                        st.write("- " + nome + " (" + data_upload + ")")
                        st.download_button("Download", data=BytesIO(texto.encode()) if texto else b"", file_name=nome, key="down_prog_" + prog + "_" + str(arq_id))
                        if st.button("Excluir", key="del_prog_" + prog + "_" + str(arq_id)):
                            delete_file(arq_id)
                            st.rerun()
                else:
                    st.info("Nenhum documento encontrado.")
                st.markdown("</div>", unsafe_allow_html=True)


def upload_arquivos():
    st.markdown("<div class='main-header'>Upload de Arquivos</div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    categoria = st.text_input("Categoria do Documento", key="upload_categoria")
    uploaded = st.file_uploader("Selecione o arquivo", type=["pdf", "docx", "txt", "csv", "xlsx"], key="upload_geral")
    if st.button("Enviar", key="btn_upload_geral"):
        cat = categoria if categoria else "GERAL"
        save_uploaded_file(cat, uploaded)
        st.success("Arquivo enviado com sucesso!")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='sub-header'>Buscar Documentos</div>", unsafe_allow_html=True)
    busca = st.text_input("Termo de busca", key="busca_geral")
    if busca:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT id, categoria, nome, tipo, data_upload FROM arquivos WHERE LOWER(nome) LIKE ? OR LOWER(texto) LIKE ?", ("%" + busca.lower() + "%", "%" + busca.lower() + "%"))
        rows = c.fetchall()
        conn.close()
        if rows:
            for row in rows:
                arq_id, cat, nome, tipo, data_upload = row
                st.write("[" + cat + "] " + nome + " - " + data_upload)
                if st.button("Excluir", key="del_geral_" + str(arq_id)):
                    delete_file(arq_id)
                    st.rerun()
        else:
            st.info("Nenhum documento encontrado.")


def plano_municipal_saude():
    st.markdown("<div class='main-header'>Plano Municipal de Saúde</div>", unsafe_allow_html=True)
    st.markdown("<div class='info-box'>Gerencie os documentos, metas e ações do Plano Municipal de Saúde.</div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload de documento do PMS", type=["pdf", "docx", "txt", "csv"], key="upload_pms")
    if st.button("Enviar documento PMS", key="btn_pms"):
        save_uploaded_file("PLANO_MUNICIPAL_SAUDE", uploaded)
        st.success("Documento enviado!")
    busca = st.text_input("Buscar no PMS", key="busca_pms")
    arquivos = search_files("PLANO_MUNICIPAL_SAUDE", busca)
    if arquivos:
        for arq in arquivos:
            arq_id, nome, tipo, texto, data_upload = arq
            st.write("- " + nome + " (" + data_upload + ")")
            if st.button("Excluir", key="del_pms_" + str(arq_id)):
                delete_file(arq_id)
                st.rerun()
    else:
        st.info("Nenhum documento encontrado.")
    st.markdown("</div>", unsafe_allow_html=True)


def norte_gestao():
    st.markdown("<div class='main-header'>Norte da Minha Gestão</div>", unsafe_allow_html=True)
    st.markdown("<div class='info-box'>Diretrizes estratégicas, indicadores e prioridades da gestão em saúde.</div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload de documento", type=["pdf", "docx", "txt", "csv"], key="upload_norte")
    if st.button("Enviar documento", key="btn_norte"):
        save_uploaded_file("NORTE_GESTAO", uploaded)
        st.success("Documento enviado!")
    busca = st.text_input("Buscar documentos", key="busca_norte")
    arquivos = search_files("NORTE_GESTAO", busca)
    if arquivos:
        for arq in arquivos:
            arq_id, nome, tipo, texto, data_upload = arq
            st.write("- " + nome + " (" + data_upload + ")")
            if st.button("Excluir", key="del_norte_" + str(arq_id)):
                delete_file(arq_id)
                st.rerun()
    else:
        st.info("Nenhum documento encontrado.")
    st.markdown("</div>", unsafe_allow_html=True)


def conselho_municipal_saude():
    st.markdown("<div class='main-header'>CONSELHO MUNICIPAL DE SAÚDE</div>", unsafe_allow_html=True)
    st.markdown("<div class='info-box'>O Conselho Municipal de Saúde (CMS) é um órgão colegiado de composição paritária entre usuários, trabalhadores e gestor do SUS, responsável por fiscalizar, acompanhar e contribuir na elaboração de políticas públicas de saúde no município. Aqui são armazenados atas, resoluções, pareceres e demais documentos do CMS.</div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload de documento do CMS", type=["pdf", "docx", "txt", "csv"], key="upload_cms")
    if st.button("Enviar documento CMS", key="btn_cms"):
        save_uploaded_file("CONSELHO_MUNICIPAL_SAUDE", uploaded)
        st.success("Documento enviado!")
    busca = st.text_input("Buscar nos documentos do CMS", key="busca_cms")
    arquivos = search_files("CONSELHO_MUNICIPAL_SAUDE", busca)
    if arquivos:
        for arq in arquivos:
            arq_id, nome, tipo, texto, data_upload = arq
            st.write("- " + nome + " (" + data_upload + ")")
            if st.button("Excluir", key="del_cms_" + str(arq_id)):
                delete_file(arq_id)
                st.rerun()
    else:
        st.info("Nenhum documento encontrado.")
    st.markdown("</div>", unsafe_allow_html=True)


def trocar_senha():
    st.markdown("<div class='main-header'>Trocar Senha</div>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    atual = st.text_input("Senha atual", type="password", key="senha_atual")
    nova = st.text_input("Nova senha", type="password", key="senha_nova")
    confirma = st.text_input("Confirmar nova senha", type="password", key="senha_confirma")
    if st.button("Alterar Senha", key="btn_trocar_senha"):
        if not login_user(st.session_state.username, atual):
            st.error("Senha atual incorreta.")
        elif nova != confirma:
            st.error("As senhas não conferem.")
        elif len(nova) < 6:
            st.error("A nova senha deve ter pelo menos 6 caracteres.")
        else:
            change_password(st.session_state.username, nova)
            st.success("Senha alterada com sucesso!")
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="MARMED - Gestão em Saúde", page_icon="🏥", layout="wide")
    st.markdown(DARK_CSS, unsafe_allow_html=True)
    init_db()

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "menu" not in st.session_state:
        st.session_state.menu = "DASHBOARD"

    if not st.session_state.logged_in:
        login_page()
        return

    with st.sidebar:
        st.markdown("<div class='main-header' style='font-size:1.5rem;'>MARMED</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center; color:#a0a0cc;'>Usuário: " + st.session_state.username + "</div>", unsafe_allow_html=True)
        st.markdown("<hr>", unsafe_allow_html=True)
        menu_options = [
            "DASHBOARD",
            "CADASTRO DE CONTAS",
            "CONTAS CADASTRADAS",
            "REALIZAR COMPRAS",
            "SUPERÁVIT FINANCEIRO",
            "PROGRAMAS DE SAÚDE",
            "UPLOAD DE ARQUIVOS",
            "PLANO MUNICIPAL DE SAÚDE",
            "NORTE DA MINHA GESTAO",
            "CONSELHO MUNICIPAL SAÚDE",
            "TROCAR SENHA",
            "SAIR"
        ]
        menu = st.radio("Menu", menu_options, label_visibility="collapsed")

    if menu == "DASHBOARD":
        dashboard()
    elif menu == "CADASTRO DE CONTAS":
        cadastro_contas()
    elif menu == "CONTAS CADASTRADAS":
        contas_cadastradas()
    elif menu == "REALIZAR COMPRAS":
        realizar_compras()
    elif menu == "SUPERÁVIT FINANCEIRO":
        superavit_financeiro()
    elif menu == "PROGRAMAS DE SAÚDE":
        programas_saude()
    elif menu == "UPLOAD DE ARQUIVOS":
        upload_arquivos()
    elif menu == "PLANO MUNICIPAL DE SAÚDE":
        plano_municipal_saude()
    elif menu == "NORTE DA MINHA GESTAO":
        norte_gestao()
    elif menu == "CONSELHO MUNICIPAL SAÚDE":
        conselho_municipal_saude()
    elif menu == "TROCAR SENHA":
        trocar_senha()
    elif menu == "SAIR":
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()


if __name__ == "__main__":
    main()
