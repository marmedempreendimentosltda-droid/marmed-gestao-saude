import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, date

st.set_page_config(
    page_title="MARMED - Prefeitura Municipal de Luminárias",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

CSS = """
<style>
    .stApp {
        background-color: #0a192f;
        color: #e6f1ff;
    }
    .stSidebar {
        background-color: #112240 !important;
    }
    .stSidebar .stRadio > div {
        background-color: #112240;
    }
    div[data-testid="stMetric"] {
        background-color: #112240;
        border: 1px solid #64ffda;
        border-radius: 10px;
        padding: 15px;
    }
    div[data-testid="stMetric"] > div {
        color: #e6f1ff;
    }
    div[data-testid="stMetric"] label {
        color: #64ffda !important;
    }
    .stButton>button {
        background-color: #112240;
        color: #64ffda;
        border: 1px solid #64ffda;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #64ffda;
        color: #0a192f;
    }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div, .stDateInput>div>div>input {
        background-color: #112240;
        color: #e6f1ff;
        border: 1px solid #64ffda;
        border-radius: 5px;
    }
    .stDataFrame {
        border: 1px solid #64ffda;
        border-radius: 10px;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #64ffda;
    }
    .stExpander {
        border: 1px solid #64ffda;
        border-radius: 10px;
    }
    hr {
        border-color: #64ffda;
    }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


def init_db():
    conn = sqlite3.connect("marmed.db")
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS contas_receber")
    c.execute("DROP TABLE IF EXISTS superavit")
    c.execute("DROP TABLE IF EXISTS compras")

    c.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE contas_receber (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            esfera TEXT NOT NULL,
            numero_conta TEXT NOT NULL,
            fonte TEXT NOT NULL,
            referencia_tipo TEXT,
            referencia_numero TEXT,
            tipo_recurso TEXT NOT NULL,
            valor_pago_custeio REAL DEFAULT 0,
            valor_pago_investimento REAL DEFAULT 0,
            valor_total REAL DEFAULT 0,
            data_recebimento TEXT,
            programa_politica TEXT,
            setor_gasto TEXT,
            ano TEXT DEFAULT ''
        )
    """)

    c.execute("""
        CREATE TABLE superavit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            esfera TEXT NOT NULL,
            fonte_original TEXT,
            fonte_superavit TEXT,
            saldo_total REAL DEFAULT 0,
            saldo_restante REAL DEFAULT 0,
            created_at TEXT
        )
    """)

    c.execute("""
        CREATE TABLE compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            quantidade REAL NOT NULL,
            valor_unitario REAL NOT NULL,
            valor_total REAL NOT NULL,
            data TEXT NOT NULL,
            setor TEXT,
            esfera TEXT,
            fonte TEXT
        )
    """)

    admin_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("admin", admin_hash))

    conn.commit()
    conn.close()


def get_connection():
    return sqlite3.connect("marmed.db")


def format_currency(value):
    if value is None:
        value = 0
    return "R$ {:,.2f}".format(value).replace(",", "X").replace(".", ",").replace("X", ".")


def get_fonte(esfera):
    if esfera == "Federal":
        return "1.600"
    elif esfera == "Estadual":
        return "1.621"
    elif esfera == "Municipal":
        return "1.500"
    return ""


def get_fonte_superavit(esfera):
    if esfera == "Federal":
        return "2.600"
    elif esfera == "Estadual":
        return "2.621"
    return None


init_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "INÍCIO"
if "edit_id" not in st.session_state:
    st.session_state.edit_id = None
if "edit_compra_id" not in st.session_state:
    st.session_state.edit_compra_id = None


def login_page():
    st.markdown("<<h1 style='text-align: center;'>MARMED</h1>", unsafe_allow_html=True)
    st.markdown("<<h3 style='text-align: center;'>Gestão Financeira - Prefeitura Municipal de Luminárias</h3>", unsafe_allow_html=True)

    with st.form("login_form"):
        st.markdown("<<h4>Login</h4>", unsafe_allow_html=True)
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

        if submitted:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", (username, password_hash))
            user = c.fetchone()
            conn.close()
            if user:
                st.session_state.logged_in = True
                st.session_state.page = "INÍCIO"
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")


def dashboard():
    st.markdown("<<h1>Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<<h3>Resumo Financeiro - MARMED</h3>", unsafe_allow_html=True)

    conn = get_connection()
    c = conn.cursor()

    esferas = ["Federal", "Estadual", "Municipal", "Transferência", "Transposição"]
    col1, col2, col3, col4, col5 = st.columns(5)
    columns = [col1, col2, col3, col4, col5]

    for idx, esfera in enumerate(esferas):
        c.execute("SELECT COALESCE(SUM(valor_total), 0) FROM contas_receber WHERE esfera = ?", (esfera,))
        total = c.fetchone()[0]
        columns[idx].metric(label=esfera.upper(), value=format_currency(total))

    st.markdown("<<hr>", unsafe_allow_html=True)

    c.execute("SELECT COALESCE(SUM(valor_total), 0) FROM compras")
    total_compras = c.fetchone()[0]

    c.execute("SELECT COALESCE(SUM(valor_total), 0) FROM contas_receber")
    total_receitas = c.fetchone()[0]

    saldo_geral = total_receitas - total_compras

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total Receitas", format_currency(total_receitas))
    col_b.metric("Total Compras", format_currency(total_compras))
    col_c.metric("Saldo Geral", format_currency(saldo_geral))

    c.execute("SELECT * FROM contas_receber ORDER BY data_recebimento DESC")
    contas = c.fetchall()
    df_contas = pd.DataFrame(contas, columns=["id", "Esfera", "Número da Conta", "Fonte", "Referência Tipo", "Referência Número/Ano", "Tipo de Recurso", "Valor Custeio", "Valor Investimento", "Valor Total", "Data Recebimento", "Programa/Política", "Setor de Gasto", "Ano"])
    st.markdown("<<h3>Contas a Receber</h3>", unsafe_allow_html=True)
    st.dataframe(df_contas, use_container_width=True, hide_index=True)

    c.execute("SELECT * FROM compras ORDER BY data DESC")
    compras = c.fetchall()
    df_compras = pd.DataFrame(compras, columns=["id", "Item/Produto", "Quantidade", "Valor Unitário", "Valor Total", "Data", "Setor", "Esfera", "Fonte"])
    st.markdown("<<h3>Compras Realizadas</h3>", unsafe_allow_html=True)
    st.dataframe(df_compras, use_container_width=True, hide_index=True)

    conn.close()


def cadastrar_contas():
    st.markdown("<<h1>Cadastrar Contas</h1>", unsafe_allow_html=True)

    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM contas_receber ORDER BY data_recebimento DESC")
    contas = c.fetchall()
    df_contas = pd.DataFrame(contas, columns=["id", "Esfera", "Número da Conta", "Fonte", "Referência Tipo", "Referência Número/Ano", "Tipo de Recurso", "Valor Custeio", "Valor Investimento", "Valor Total", "Data Recebimento", "Programa/Política", "Setor de Gasto", "Ano"])
    st.markdown("<<h3>Registros Existentes</h3>", unsafe_allow_html=True)
    st.dataframe(df_contas, use_container_width=True, hide_index=True)

    with st.expander("NOVO CADASTRO"):
        with st.form("form_cadastrar_conta"):
            esfera = st.selectbox("Esfera", ["Federal", "Estadual", "Municipal", "Transferência", "Transposição"])
            numero_conta = st.text_input("Número da Conta")
            fonte = st.text_input("Fonte", value=get_fonte(esfera), disabled=True)
            referencia_tipo = st.selectbox("Referência do Contrato", ["Contrato", "Convênio", "Termo de Cooperação", "Outro"])
            referencia_numero = st.text_input("Número/Ano")
            tipo_recurso = st.selectbox("Tipo de Recurso", ["Custeio", "Investimento", "Custeio/Investimento"])

            valor_custeio = 0.0
            valor_investimento = 0.0

            if tipo_recurso == "Custeio/Investimento":
                valor_custeio = st.number_input("Valor Pago - Custeio", min_value=0.0, format="%.2f")
                valor_investimento = st.number_input("Valor Pago - Investimento", min_value=0.0, format="%.2f")
            elif tipo_recurso == "Custeio":
                valor_custeio = st.number_input("Valor Pago - Custeio", min_value=0.0, format="%.2f")
            elif tipo_recurso == "Investimento":
                valor_investimento = st.number_input("Valor Pago - Investimento", min_value=0.0, format="%.2f")

            data_recebimento = st.date_input("Data de Recebimento", value=date.today())
            programa_politica = st.text_input("Programa/Política")
            setor_gasto = st.selectbox("Setor de Gasto", ["Saúde", "Educação", "Infraestrutura", "Administração", "Assistência Social", "Outros"])
            ano = st.text_input("Ano", value=str(date.today().year))

            submitted = st.form_submit_button("Salvar Conta")

            if submitted:
                valor_total = valor_custeio + valor_investimento
                c.execute("""
                    INSERT INTO contas_receber (
                        esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso,
                        valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento,
                        programa_politica, setor_gasto, ano
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso,
                    valor_custeio, valor_investimento, valor_total, data_recebimento.strftime("%Y-%m-%d"),
                    programa_politica, setor_gasto, ano
                ))
                conn.commit()
                st.success("Conta cadastrada com sucesso!")
                st.rerun()

    conn.close()


def contas_cadastradas():
    st.markdown("<<h1>Contas Cadastradas</h1>", unsafe_allow_html=True)

    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM contas_receber ORDER BY data_recebimento DESC")
    contas = c.fetchall()
    df_contas = pd.DataFrame(contas, columns=["id", "Esfera", "Número da Conta", "Fonte", "Referência Tipo", "Referência Número/Ano", "Tipo de Recurso", "Valor Custeio", "Valor Investimento", "Valor Total", "Data Recebimento", "Programa/Política", "Setor de Gasto", "Ano"])

    st.dataframe(df_contas, use_container_width=True, hide_index=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Editar Conta Selecionada"):
            if "selected_conta" in st.session_state and st.session_state.selected_conta:
                st.session_state.edit_id = st.session_state.selected_conta
                st.session_state.page = "EDITAR CONTA"
                st.rerun()
            else:
                st.warning("Selecione uma conta na tabela para editar.")

    with col2:
        if st.button("Excluir Conta Selecionada"):
            if "selected_conta" in st.session_state and st.session_state.selected_conta:
                c.execute("DELETE FROM contas_receber WHERE id = ?", (st.session_state.selected_conta,))
                conn.commit()
                st.success("Conta excluída com sucesso!")
                st.rerun()
            else:
                st.warning("Selecione uma conta na tabela para excluir.")

    if not df_contas.empty:
        selected = st.selectbox("Selecione uma conta para Editar/Excluir", df_contas["id"].tolist(), format_func=lambda x: f"ID {x} - {df_contas[df_contas['id'] == x]['Esfera'].values[0]} - {df_contas[df_contas['id'] == x]['Número da Conta'].values[0]}")
        st.session_state.selected_conta = selected

    st.markdown("<<hr>", unsafe_allow_html=True)
    st.markdown("<<h2>Recursos de Exercícios Anteriores / Superávit Financeiro</h2>", unsafe_allow_html=True)

    c.execute("SELECT * FROM superavit ORDER BY created_at DESC")
    superavit = c.fetchall()
    df_superavit = pd.DataFrame(superavit, columns=["id", "Esfera", "Fonte Original", "Fonte Superávit", "Saldo Total", "Saldo Restante", "Criado em"])
    st.dataframe(df_superavit, use_container_width=True, hide_index=True)

    if st.button("MIGRAR SALDOS PARA SUPERÁVIT"):
        for esfera in ["Federal", "Estadual"]:
            c.execute("SELECT COALESCE(SUM(valor_total), 0) FROM contas_receber WHERE esfera = ?", (esfera,))
            soma = c.fetchone()[0]
            if soma > 0:
                fonte_original = get_fonte(esfera)
                fonte_superavit = get_fonte_superavit(esfera)
                c.execute("SELECT id FROM superavit WHERE esfera = ?", (esfera,))
                existing = c.fetchone()
                if existing:
                    c.execute("""
                        UPDATE superavit
                        SET fonte_original = ?, fonte_superavit = ?, saldo_total = ?, saldo_restante = ?, created_at = ?
                        WHERE esfera = ?
                    """, (fonte_original, fonte_superavit, soma, soma, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), esfera))
                else:
                    c.execute("""
                        INSERT INTO superavit (esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (esfera, fonte_original, fonte_superavit, soma, soma, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        st.success("Saldos migrados para superávit com sucesso!")
        st.rerun()

    conn.close()


def editar_conta():
    st.markdown("<<h1>Editar Conta</h1>", unsafe_allow_html=True)

    if not st.session_state.edit_id:
        st.warning("Nenhuma conta selecionada para edição.")
        return

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM contas_receber WHERE id = ?", (st.session_state.edit_id,))
    conta = c.fetchone()

    if not conta:
        st.error("Conta não encontrada.")
        return

    (
        id_conta, esfera_old, numero_conta_old, fonte_old, referencia_tipo_old, referencia_numero_old,
        tipo_recurso_old, valor_custeio_old, valor_investimento_old, valor_total_old,
        data_recebimento_old, programa_politica_old, setor_gasto_old, ano_old
    ) = conta

    with st.form("form_editar_conta"):
        esfera = st.selectbox("Esfera", ["Federal", "Estadual", "Municipal", "Transferência", "Transposição"], index=["Federal", "Estadual", "Municipal", "Transferência", "Transposição"].index(esfera_old))
        numero_conta = st.text_input("Número da Conta", value=numero_conta_old)
        fonte = st.text_input("Fonte", value=get_fonte(esfera), disabled=True)
        referencia_tipo = st.selectbox("Referência do Contrato", ["Contrato", "Convênio", "Termo de Cooperação", "Outro"], index=["Contrato", "Convênio", "Termo de Cooperação", "Outro"].index(referencia_tipo_old) if referencia_tipo_old in ["Contrato", "Convênio", "Termo de Cooperação", "Outro"] else 0)
        referencia_numero = st.text_input("Número/Ano", value=referencia_numero_old)
        tipo_recurso = st.selectbox("Tipo de Recurso", ["Custeio", "Investimento", "Custeio/Investimento"], index=["Custeio", "Investimento", "Custeio/Investimento"].index(tipo_recurso_old))

        valor_custeio = 0.0
        valor_investimento = 0.0

        if tipo_recurso == "Custeio/Investimento":
            valor_custeio = st.number_input("Valor Pago - Custeio", min_value=0.0, value=float(valor_custeio_old), format="%.2f")
            valor_investimento = st.number_input("Valor Pago - Investimento", min_value=0.0, value=float(valor_investimento_old), format="%.2f")
        elif tipo_recurso == "Custeio":
            valor_custeio = st.number_input("Valor Pago - Custeio", min_value=0.0, value=float(valor_custeio_old), format="%.2f")
        elif tipo_recurso == "Investimento":
            valor_investimento = st.number_input("Valor Pago - Investimento", min_value=0.0, value=float(valor_investimento_old), format="%.2f")

        data_recebimento = st.date_input("Data de Recebimento", value=datetime.strptime(data_recebimento_old, "%Y-%m-%d").date() if data_recebimento_old else date.today())
        programa_politica = st.text_input("Programa/Política", value=programa_politica_old)
        setor_gasto = st.selectbox("Setor de Gasto", ["Saúde", "Educação", "Infraestrutura", "Administração", "Assistência Social", "Outros"], index=["Saúde", "Educação", "Infraestrutura", "Administração", "Assistência Social", "Outros"].index(setor_gasto_old) if setor_gasto_old in ["Saúde", "Educação", "Infraestrutura", "Administração", "Assistência Social", "Outros"] else 0)
        ano = st.text_input("Ano", value=ano_old if ano_old else str(date.today().year))

        submitted = st.form_submit_button("Salvar Alterações")

        if submitted:
            valor_total = valor_custeio + valor_investimento
            c.execute("""
                UPDATE contas_receber SET
                    esfera = ?, numero_conta = ?, fonte = ?, referencia_tipo = ?, referencia_numero = ?, tipo_recurso = ?,
                    valor_pago_custeio = ?, valor_pago_investimento = ?, valor_total = ?, data_recebimento = ?,
                    programa_politica = ?, setor_gasto = ?, ano = ?
                WHERE id = ?
            """, (
                esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso,
                valor_custeio, valor_investimento, valor_total, data_recebimento.strftime("%Y-%m-%d"),
                programa_politica, setor_gasto, ano, id_conta
            ))
            conn.commit()
            st.session_state.edit_id = None
            st.session_state.page = "CONTAS CADASTRADAS"
            st.success("Conta atualizada com sucesso!")
            st.rerun()

    conn.close()


def realizar_compras():
    st.markdown("<<h1>Realizar Compras</h1>", unsafe_allow_html=True)

    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM compras ORDER BY data DESC")
    compras = c.fetchall()
    df_compras = pd.DataFrame(compras, columns=["id", "Item/Produto", "Quantidade", "Valor Unitário", "Valor Total", "Data", "Setor", "Esfera", "Fonte"])
    st.markdown("<<h3>Compras Registradas</h3>", unsafe_allow_html=True)
    st.dataframe(df_compras, use_container_width=True, hide_index=True)

    with st.expander("NOVA COMPRA"):
        with st.form("form_nova_compra"):
            esfera = st.selectbox("Esfera", ["Federal", "Estadual", "Municipal"])
            item = st.text_input("Item/Produto")
            quantidade = st.number_input("Quantidade", min_value=0.0, format="%.2f")
            valor_unitario = st.number_input("Valor Unitário", min_value=0.0, format="%.2f")
            valor_total = quantidade * valor_unitario
            st.markdown(f"<<h4>Valor Total: {format_currency(valor_total)}</h4>", unsafe_allow_html=True)
            data_compra = st.date_input("Data", value=date.today())
            setor = st.selectbox("Setor", ["Saúde", "Educação", "Infraestrutura", "Administração", "Assistência Social", "Outros"])
            fonte = st.text_input("Fonte", value=get_fonte(esfera), disabled=True)

            submitted = st.form_submit_button("Registrar Compra")

            if submitted:
                if not item or quantidade <= 0 or valor_unitario <= 0:
                    st.error("Preencha todos os campos obrigatórios com valores válidos.")
                else:
                    if esfera != "Municipal":
                        c.execute("SELECT COALESCE(SUM(saldo_restante), 0) FROM superavit WHERE esfera = ? AND saldo_restante > 0", (esfera,))
                        saldo_superavit = c.fetchone()[0]
                        if saldo_superavit > 0:
                            st.error(f"Você ainda tem valor restante de superávit! Saldo disponível: {format_currency(saldo_superavit)}. Primeiro utilize o saldo do superávit antes de usar recursos do exercício atual.")
                        else:
                            c.execute("""
                                INSERT INTO compras (item, quantidade, valor_unitario, valor_total, data, setor, esfera, fonte)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (item, quantidade, valor_unitario, valor_total, data_compra.strftime("%Y-%m-%d"), setor, esfera, fonte))
                            conn.commit()
                            st.success("Compra registrada com sucesso!")
                            st.rerun()
                    else:
                        c.execute("""
                            INSERT INTO compras (item, quantidade, valor_unitario, valor_total, data, setor, esfera, fonte)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (item, quantidade, valor_unitario, valor_total, data_compra.strftime("%Y-%m-%d"), setor, esfera, fonte))
                        conn.commit()
                        st.success("Compra registrada com sucesso!")
                        st.rerun()

    st.markdown("<<hr>", unsafe_allow_html=True)
    st.markdown("<<h3>Editar / Excluir Compra</h3>", unsafe_allow_html=True)

    if not df_compras.empty:
        selected_compra = st.selectbox("Selecione uma compra", df_compras["id"].tolist(), format_func=lambda x: f"ID {x} - {df_compras[df_compras['id'] == x]['Item/Produto'].values[0]}")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Editar Compra"):
                st.session_state.edit_compra_id = selected_compra
                st.session_state.page = "EDITAR COMPRA"
                st.rerun()
        with col2:
            if st.button("Excluir Compra"):
                c.execute("DELETE FROM compras WHERE id = ?", (selected_compra,))
                conn.commit()
                st.success("Compra excluída com sucesso!")
                st.rerun()
    else:
        st.info("Nenhuma compra registrada para editar ou excluir.")

    conn.close()


def editar_compra():
    st.markdown("<<h1>Editar Compra</h1>", unsafe_allow_html=True)

    if not st.session_state.edit_compra_id:
        st.warning("Nenhuma compra selecionada para edição.")
        return

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM compras WHERE id = ?", (st.session_state.edit_compra_id,))
    compra = c.fetchone()

    if not compra:
        st.error("Compra não encontrada.")
        return

    id_compra, item_old, quantidade_old, valor_unitario_old, valor_total_old, data_old, setor_old, esfera_old, fonte_old = compra

    with st.form("form_editar_compra"):
        esfera = st.selectbox("Esfera", ["Federal", "Estadual", "Municipal"], index=["Federal", "Estadual", "Municipal"].index(esfera_old) if esfera_old in ["Federal", "Estadual", "Municipal"] else 0)
        item = st.text_input("Item/Produto", value=item_old)
        quantidade = st.number_input("Quantidade", min_value=0.0, value=float(quantidade_old), format="%.2f")
        valor_unitario = st.number_input("Valor Unitário", min_value=0.0, value=float(valor_unitario_old), format="%.2f")
        valor_total = quantidade * valor_unitario
        st.markdown(f"<<h4>Valor Total: {format_currency(valor_total)}</h4>", unsafe_allow_html=True)
        data_compra = st.date_input("Data", value=datetime.strptime(data_old, "%Y-%m-%d").date() if data_old else date.today())
        setor = st.selectbox("Setor", ["Saúde", "Educação", "Infraestrutura", "Administração", "Assistência Social", "Outros"], index=["Saúde", "Educação", "Infraestrutura", "Administração", "Assistência Social", "Outros"].index(setor_old) if setor_old in ["Saúde", "Educação", "Infraestrutura", "Administração", "Assistência Social", "Outros"] else 0)
        fonte = st.text_input("Fonte", value=get_fonte(esfera), disabled=True)

        submitted = st.form_submit_button("Salvar Alterações")

        if submitted:
            if not item or quantidade <= 0 or valor_unitario <= 0:
                st.error("Preencha todos os campos obrigatórios com valores válidos.")
            else:
                c.execute("""
                    UPDATE compras SET
                        item = ?, quantidade = ?, valor_unitario = ?, valor_total = ?, data = ?, setor = ?, esfera = ?, fonte = ?
                    WHERE id = ?
                """, (item, quantidade, valor_unitario, valor_total, data_compra.strftime("%Y-%m-%d"), setor, esfera, fonte, id_compra))
                conn.commit()
                st.session_state.edit_compra_id = None
                st.session_state.page = "REALIZAR COMPRAS"
                st.success("Compra atualizada com sucesso!")
                st.rerun()

    conn.close()


def change_password():
    st.markdown("<<h1>Alterar Senha</h1>", unsafe_allow_html=True)

    with st.form("form_change_password"):
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
        submitted = st.form_submit_button("Alterar Senha")

        if submitted:
            senha_atual_hash = hashlib.sha256(senha_atual.encode()).hexdigest()
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", ("admin", senha_atual_hash))
            user = c.fetchone()

            if not user:
                st.error("Senha atual incorreta.")
            elif nova_senha != confirmar_senha:
                st.error("As novas senhas não coincidem.")
            elif len(nova_senha) < 6:
                st.error("A nova senha deve ter pelo menos 6 caracteres.")
            else:
                nova_senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
                c.execute("UPDATE users SET password_hash = ? WHERE username = ?", (nova_senha_hash, "admin"))
                conn.commit()
                st.success("Senha alterada com sucesso!")

            conn.close()


def sidebar():
    with st.sidebar:
        st.markdown("<<h2 style='text-align: center;'>MARMED</h2>", unsafe_allow_html=True)
        st.markdown("<<p style='text-align: center;'>Prefeitura Municipal de Luminárias</p>", unsafe_allow_html=True)
        st.markdown("<<hr>", unsafe_allow_html=True)
        st.markdown("<<h4>ABA DE NAVEGAÇÃO</h4>", unsafe_allow_html=True)

        menu = st.radio(
            "Menu",
            ["🏠 INÍCIO", "CADASTRAR CONTAS", "CONTAS CADASTRADAS", "REALIZAR COMPRAS", "ALTERAR SENHA", "SAIR"],
            label_visibility="collapsed"
        )

        if menu == "🏠 INÍCIO":
            st.session_state.page = "INÍCIO"
        elif menu == "CADASTRAR CONTAS":
            st.session_state.page = "CADASTRAR CONTAS"
        elif menu == "CONTAS CADASTRADAS":
            st.session_state.page = "CONTAS CADASTRADAS"
        elif menu == "REALIZAR COMPRAS":
            st.session_state.page = "REALIZAR COMPRAS"
        elif menu == "ALTERAR SENHA":
            st.session_state.page = "ALTERAR SENHA"
        elif menu == "SAIR":
            st.session_state.logged_in = False
            st.session_state.page = "INÍCIO"
            st.rerun()


def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        sidebar()

        if st.session_state.page == "INÍCIO":
            dashboard()
        elif st.session_state.page == "CADASTRAR CONTAS":
            cadastrar_contas()
        elif st.session_state.page == "CONTAS CADASTRADAS":
            contas_cadastradas()
        elif st.session_state.page == "EDITAR CONTA":
            editar_conta()
        elif st.session_state.page == "REALIZAR COMPRAS":
            realizar_compras()
        elif st.session_state.page == "EDITAR COMPRA":
            editar_compra()
        elif st.session_state.page == "ALTERAR SENHA":
            change_password()


if __name__ == "__main__":
    main()
