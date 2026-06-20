import streamlit as st
import sqlite3
import datetime
import pandas as pd
import hashlib

st.set_page_config(page_title="MARMED - Gestão em Saúde Pública", layout="wide")

DB_NAME = "marmed.db"


def init_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contas_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fornecedor TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            vencimento DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pendente',
            data_pagamento DATE,
            observacao TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contas_receber (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            vencimento DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pendente',
            data_recebimento DATE,
            observacao TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empenhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_empenho TEXT NOT NULL UNIQUE,
            fornecedor TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            data_empenho DATE NOT NULL,
            data_cancelamento DATE,
            status TEXT NOT NULL DEFAULT 'Ativo'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS licitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modalidade TEXT NOT NULL,
            objeto TEXT NOT NULL,
            valor_estimado REAL NOT NULL,
            data_abertura DATE NOT NULL,
            data_homologacao DATE,
            situacao TEXT NOT NULL DEFAULT 'Em andamento'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_contrato TEXT NOT NULL UNIQUE,
            fornecedor TEXT NOT NULL,
            objeto TEXT NOT NULL,
            valor REAL NOT NULL,
            data_inicio DATE NOT NULL,
            data_fim DATE NOT NULL,
            situacao TEXT NOT NULL DEFAULT 'Vigente'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    ''')

    admin_hash = hashlib.sha256("admin".encode()).hexdigest()
    cursor.execute('''
        INSERT OR IGNORE INTO usuarios (username, password_hash) VALUES (?, ?)
    ''', ("admin", admin_hash))

    conn.commit()
    conn.close()


@st.cache_resource
def get_db_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


conn = get_db_connection()


def verificar_login(username, password):
    cursor = conn.cursor()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute(
        "SELECT id FROM usuarios WHERE username=? AND password_hash=?",
        (username, password_hash)
    )
    result = cursor.fetchone()
    return result is not None


def formatar_moeda(valor):
    try:
        if valor is None:
            return "R$ 0,00"
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def parse_valor(valor_str):
    try:
        if isinstance(valor_str, (int, float)):
            return float(valor_str)
        valor_str = str(valor_str).replace("R$", "").replace(".", "").replace(",", ".").strip()
        return float(valor_str) if valor_str else 0.0
    except Exception:
        return 0.0


def login_page():
    st.markdown("<<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div style='text-align: center; padding: 20px; border-radius: 10px; background-color: #f0f2f6;'>
                <h1 style='color: #1f4e79;'>MARMED</h1>
                <h3 style='color: #333;'>Gestão em Saúde Pública de Luminárias-MG</h3>
                <p style='color: #555;'>Sistema de Gestão Financeira e Administrativa</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("<<br>", unsafe_allow_html=True)
        with st.form("login_form"):
            st.subheader("Login")
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)
            if submitted:
                if not username or not password:
                    st.error("Preencha usuário e senha.")
                else:
                    if verificar_login(username, password):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.page = "Dashboard"
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas.")


def sidebar_navigation():
    with st.sidebar:
        st.markdown(f"### Bem-vindo, {st.session_state.get('username', 'admin')}")
        st.divider()

        paginas = [
            "Dashboard",
            "Contas a Pagar",
            "Contas a Receber",
            "Empenhos",
            "Licitações",
            "Contratos",
            "Relatórios"
        ]

        for pagina in paginas:
            if st.button(pagina, use_container_width=True, key=f"nav_{pagina}"):
                st.session_state.page = pagina
                st.session_state.edit_mode = False
                st.session_state.selected_record = None
                st.rerun()

        st.divider()
        if st.button("Sair", use_container_width=True, key="logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.page = "Login"
            st.session_state.edit_mode = False
            st.session_state.selected_record = None
            st.rerun()


def dashboard_page():
    st.title("Dashboard")
    st.markdown("Visão geral dos recursos financeiros da saúde pública")
    st.divider()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(
            """
            <div style='background-color: #1f77b4; padding: 15px; border-radius: 10px; color: white; text-align: center;'>
                <h5>REPASSE FEDERAL</h5>
                <h3>R$ 1.250.000,00</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            """
            <div style='background-color: #2ca02c; padding: 15px; border-radius: 10px; color: white; text-align: center;'>
                <h5>REPASSE ESTADUAL</h5>
                <h3>R$ 890.000,00</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            """
            <div style='background-color: #ff7f0e; padding: 15px; border-radius: 10px; color: white; text-align: center;'>
                <h5>RECURSO MUNICIPAL</h5>
                <h3>R$ 450.000,00</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            """
            <div style='background-color: #9467bd; padding: 15px; border-radius: 10px; color: white; text-align: center;'>
                <h5>TRANSFERÊNCIA</h5>
                <h3>R$ 320.000,00</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col5:
        st.markdown(
            """
            <div style='background-color: #d62728; padding: 15px; border-radius: 10px; color: white; text-align: center;'>
                <h5>TRANSPOSIÇÃO</h5>
                <h3>R$ 180.000,00</h3>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("Últimas Movimentações")
        dados = [
            {"Data": "2024-01-15", "Descrição": "Repasse Federal Janeiro", "Valor": 125000.00, "Tipo": "Entrada"},
            {"Data": "2024-01-18", "Descrição": "Pagamento Fornecedor XYZ", "Valor": 45000.00, "Tipo": "Saída"},
            {"Data": "2024-01-22", "Descrição": "Repasse Estadual", "Valor": 89000.00, "Tipo": "Entrada"},
            {"Data": "2024-01-25", "Descrição": "Empenho Material Médico", "Valor": 23000.00, "Tipo": "Saída"},
            {"Data": "2024-01-28", "Descrição": "Receita de Convênio", "Valor": 15000.00, "Tipo": "Entrada"},
        ]
        df = pd.DataFrame(dados)
        df["Valor"] = df["Valor"].apply(formatar_moeda)
        st.dataframe(df, use_container_width=True, hide_index=True)

    with col_right:
        st.subheader("Resumo do Mês")
        cursor = conn.cursor()

        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM contas_pagar WHERE status='Pago'")
        total_pago = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM contas_pagar WHERE status='Pendente'")
        total_pagar_pendente = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM contas_receber WHERE status='Recebido'")
        total_recebido = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM contas_receber WHERE status='Pendente'")
        total_receber_pendente = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM empenhos WHERE status='Ativo'")
        total_empenhos = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(valor_estimado), 0) FROM licitacoes WHERE situacao='Em andamento'")
        total_licitacoes = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM contratos WHERE situacao='Vigente'")
        total_contratos = cursor.fetchone()[0]

        resumo = pd.DataFrame({
            "Métrica": [
                "Total Pago (Contas a Pagar)",
                "Total Pendente (Contas a Pagar)",
                "Total Recebido (Contas a Receber)",
                "Total Pendente (Contas a Receber)",
                "Empenhos Ativos",
                "Licitações em Andamento",
                "Contratos Vigentes"
            ],
            "Valor": [
                formatar_moeda(total_pago),
                formatar_moeda(total_pagar_pendente),
                formatar_moeda(total_recebido),
                formatar_moeda(total_receber_pendente),
                formatar_moeda(total_empenhos),
                formatar_moeda(total_licitacoes),
                formatar_moeda(total_contratos)
            ]
        })
        st.dataframe(resumo, use_container_width=True, hide_index=True)


def contas_pagar_page():
    st.title("Contas a Pagar")
    st.markdown("Cadastro e gerenciamento de contas a pagar")
    st.divider()

    cursor = conn.cursor()

    with st.expander("Adicionar Nova Conta a Pagar", expanded=False):
        with st.form("form_add_pagar"):
            col1, col2 = st.columns(2)
            with col1:
                fornecedor = st.text_input("Fornecedor", key="add_fornecedor_pagar")
                descricao = st.text_input("Descrição", key="add_descricao_pagar")
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f", key="add_valor_pagar")
            with col2:
                vencimento = st.date_input("Data de Vencimento", key="add_vencimento_pagar")
                status = st.selectbox("Status", ["Pendente", "Pago", "Atrasado"], key="add_status_pagar")
                data_pagamento = st.date_input("Data de Pagamento", value=None, key="add_data_pagamento_pagar")
            observacao = st.text_area("Observação", key="add_observacao_pagar")
            submitted = st.form_submit_button("Salvar", use_container_width=True)
            if submitted:
                if not fornecedor or not descricao or valor <= 0:
                    st.error("Preencha todos os campos obrigatórios com valores válidos.")
                else:
                    try:
                        dp = data_pagamento if status == "Pago" else None
                        cursor.execute('''
                            INSERT INTO contas_pagar (fornecedor, descricao, valor, vencimento, status, data_pagamento, observacao)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (fornecedor, descricao, valor, vencimento, status, dp, observacao))
                        conn.commit()
                        st.success("Conta a pagar registrada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    cursor.execute("SELECT * FROM contas_pagar ORDER BY vencimento DESC")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(rows, columns=columns)

    if not df.empty:
        df["valor"] = df["valor"].apply(formatar_moeda)

    st.subheader("Contas Cadastradas")
    edited_df = st.data_editor(
        df if not df.empty else pd.DataFrame(columns=columns),
        num_rows="dynamic",
        use_container_width=True,
        key="editor_pagar",
        hide_index=True,
        column_config={
            "valor": st.column_config.TextColumn("Valor (R$)")
        }
    )

    if not df.empty and not edited_df.equals(df):
        try:
            for _, row in edited_df.iterrows():
                row_id = row["id"]
                valor_numerico = parse_valor(row["valor"])
                cursor.execute('''
                    UPDATE contas_pagar
                    SET fornecedor=?, descricao=?, valor=?, vencimento=?, status=?, data_pagamento=?, observacao=?
                    WHERE id=?
                ''', (
                    row["fornecedor"], row["descricao"], valor_numerico, row["vencimento"],
                    row["status"], row.get("data_pagamento"), row.get("observacao"), row_id
                ))
            conn.commit()
            st.success("Alterações salvas!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar: {e}")

    if not df.empty:
        st.subheader("Excluir Registro")
        ids = df["id"].tolist()
        id_excluir = st.selectbox("Selecione o ID para excluir", ids, key="delete_pagar")
        if st.button("Excluir", key="btn_delete_pagar"):
            try:
                cursor.execute("DELETE FROM contas_pagar WHERE id=?", (id_excluir,))
                conn.commit()
                st.success("Registro excluído!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")

    st.divider()
    st.subheader("Totais")
    cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM contas_pagar WHERE status='Pago'")
    total_pago = cursor.fetchone()[0]
    cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM contas_pagar WHERE status='Pendente'")
    total_pendente = cursor.fetchone()[0]
    cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM contas_pagar WHERE status='Atrasado'")
    total_atrasado = cursor.fetchone()[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Pago", formatar_moeda(total_pago))
    col2.metric("Total Pendente", formatar_moeda(total_pendente))
    col3.metric("Total Atrasado", formatar_moeda(total_atrasado))


def contas_receber_page():
    st.title("Contas a Receber")
    st.markdown("Cadastro e gerenciamento de contas a receber")
    st.divider()

    cursor = conn.cursor()

    with st.expander("Adicionar Nova Conta a Receber", expanded=False):
        with st.form("form_add_receber"):
            col1, col2 = st.columns(2)
            with col1:
                cliente = st.text_input("Cliente", key="add_cliente_receber")
                descricao = st.text_input("Descrição", key="add_descricao_receber")
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f", key="add_valor_receber")
            with col2:
                vencimento = st.date_input("Data de Vencimento", key="add_vencimento_receber")
                status = st.selectbox("Status", ["Pendente", "Recebido", "Atrasado"], key="add_status_receber")
                data_recebimento = st.date_input("Data de Recebimento", value=None, key="add_data_recebimento_receber")
            observacao = st.text_area("Observação", key="add_observacao_receber")
            submitted = st.form_submit_button("Salvar", use_container_width=True)
            if submitted:
                if not cliente or not descricao or valor <= 0:
                    st.error("Preencha todos os campos obrigatórios com valores válidos.")
                else:
                    try:
                        dr = data_recebimento if status == "Recebido" else None
                        cursor.execute('''
                            INSERT INTO contas_receber (cliente, descricao, valor, vencimento, status, data_recebimento, observacao)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (cliente, descricao, valor, vencimento, status, dr, observacao))
                        conn.commit()
                        st.success("Conta a receber registrada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    cursor.execute("SELECT * FROM contas_receber ORDER BY vencimento DESC")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(rows, columns=columns)

    if not df.empty:
        df["valor"] = df["valor"].apply(formatar_moeda)

    st.subheader("Contas Cadastradas")
    edited_df = st.data_editor(
        df if not df.empty else pd.DataFrame(columns=columns),
        num_rows="dynamic",
        use_container_width=True,
        key="editor_receber",
        hide_index=True,
        column_config={
            "valor": st.column_config.TextColumn("Valor (R$)")
        }
    )

    if not df.empty and not edited_df.equals(df):
        try:
            for _, row in edited_df.iterrows():
                row_id = row["id"]
                valor_numerico = parse_valor(row["valor"])
                cursor.execute('''
                    UPDATE contas_receber
                    SET cliente=?, descricao=?, valor=?, vencimento=?, status=?, data_recebimento=?, observacao=?
                    WHERE id=?
                ''', (
                    row["cliente"], row["descricao"], valor_numerico, row["vencimento"],
                    row["status"], row.get("data_recebimento"), row.get("observacao"), row_id
                ))
            conn.commit()
            st.success("Alterações salvas!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar: {e}")

    if not df.empty:
        st.subheader("Excluir Registro")
        ids = df["id"].tolist()
        id_excluir = st.selectbox("Selecione o ID para excluir", ids, key="delete_receber")
        if st.button("Excluir", key="btn_delete_receber"):
            try:
                cursor.execute("DELETE FROM contas_receber WHERE id=?", (id_excluir,))
                conn.commit()
                st.success("Registro excluído!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")

    st.divider()
    st.subheader("Totais")
    cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM contas_receber WHERE status='Recebido'")
    total_recebido = cursor.fetchone()[0]
    cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM contas_receber WHERE status='Pendente'")
    total_pendente = cursor.fetchone()[0]
    cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM contas_receber WHERE status='Atrasado'")
    total_atrasado = cursor.fetchone()[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Recebido", formatar_moeda(total_recebido))
    col2.metric("Total Pendente", formatar_moeda(total_pendente))
    col3.metric("Total Atrasado", formatar_moeda(total_atrasado))


def empenhos_page():
    st.title("Empenhos")
    st.markdown("Cadastro e gerenciamento de empenhos")
    st.divider()

    cursor = conn.cursor()

    with st.expander("Adicionar Novo Empenho", expanded=False):
        with st.form("form_add_empenho"):
            col1, col2 = st.columns(2)
            with col1:
                numero_empenho = st.text_input("Número do Empenho", key="add_numero_empenho")
                fornecedor = st.text_input("Fornecedor", key="add_fornecedor_empenho")
                descricao = st.text_input("Descrição", key="add_descricao_empenho")
            with col2:
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f", key="add_valor_empenho")
                data_empenho = st.date_input("Data do Empenho", key="add_data_empenho")
                status = st.selectbox("Status", ["Ativo", "Cancelado"], key="add_status_empenho")
                data_cancelamento = st.date_input("Data de Cancelamento", value=None, key="add_data_cancelamento_empenho")
            submitted = st.form_submit_button("Salvar", use_container_width=True)
            if submitted:
                if not numero_empenho or not fornecedor or not descricao or valor <= 0:
                    st.error("Preencha todos os campos obrigatórios com valores válidos.")
                else:
                    try:
                        dc = data_cancelamento if status == "Cancelado" else None
                        cursor.execute('''
                            INSERT INTO empenhos (numero_empenho, fornecedor, descricao, valor, data_empenho, data_cancelamento, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (numero_empenho, fornecedor, descricao, valor, data_empenho, dc, status))
                        conn.commit()
                        st.success("Empenho registrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    cursor.execute("SELECT * FROM empenhos ORDER BY data_empenho DESC")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(rows, columns=columns)

    if not df.empty:
        df["valor"] = df["valor"].apply(formatar_moeda)

    st.subheader("Empenhos Cadastrados")
    edited_df = st.data_editor(
        df if not df.empty else pd.DataFrame(columns=columns),
        num_rows="dynamic",
        use_container_width=True,
        key="editor_empenhos",
        hide_index=True,
        column_config={
            "valor": st.column_config.TextColumn("Valor (R$)")
        }
    )

    if not df.empty and not edited_df.equals(df):
        try:
            for _, row in edited_df.iterrows():
                row_id = row["id"]
                valor_numerico = parse_valor(row["valor"])
                cursor.execute('''
                    UPDATE empenhos
                    SET numero_empenho=?, fornecedor=?, descricao=?, valor=?, data_empenho=?, data_cancelamento=?, status=?
                    WHERE id=?
                ''', (
                    row["numero_empenho"], row["fornecedor"], row["descricao"], valor_numerico,
                    row["data_empenho"], row.get("data_cancelamento"), row["status"], row_id
                ))
            conn.commit()
            st.success("Alterações salvas!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar: {e}")

    if not df.empty:
        st.subheader("Excluir Registro")
        ids = df["id"].tolist()
        id_excluir = st.selectbox("Selecione o ID para excluir", ids, key="delete_empenho")
        if st.button("Excluir", key="btn_delete_empenho"):
            try:
                cursor.execute("DELETE FROM empenhos WHERE id=?", (id_excluir,))
                conn.commit()
                st.success("Registro excluído!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")


def licitacoes_page():
    st.title("Licitações")
    st.markdown("Cadastro e gerenciamento de licitações")
    st.divider()

    cursor = conn.cursor()

    with st.expander("Adicionar Nova Licitação", expanded=False):
        with st.form("form_add_licitacao"):
            col1, col2 = st.columns(2)
            with col1:
                modalidade = st.text_input("Modalidade", key="add_modalidade_licitacao")
                objeto = st.text_input("Objeto", key="add_objeto_licitacao")
                valor_estimado = st.number_input("Valor Estimado (R$)", min_value=0.0, format="%.2f", key="add_valor_estimado_licitacao")
            with col2:
                data_abertura = st.date_input("Data de Abertura", key="add_data_abertura_licitacao")
                situacao = st.selectbox("Situação", ["Em andamento", "Homologada", "Cancelada"], key="add_situacao_licitacao")
                data_homologacao = st.date_input("Data de Homologação", value=None, key="add_data_homologacao_licitacao")
            submitted = st.form_submit_button("Salvar", use_container_width=True)
            if submitted:
                if not modalidade or not objeto or valor_estimado <= 0:
                    st.error("Preencha todos os campos obrigatórios com valores válidos.")
                else:
                    try:
                        dh = data_homologacao if situacao == "Homologada" else None
                        cursor.execute('''
                            INSERT INTO licitacoes (modalidade, objeto, valor_estimado, data_abertura, data_homologacao, situacao)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (modalidade, objeto, valor_estimado, data_abertura, dh, situacao))
                        conn.commit()
                        st.success("Licitação registrada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    cursor.execute("SELECT * FROM licitacoes ORDER BY data_abertura DESC")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(rows, columns=columns)

    if not df.empty:
        df["valor_estimado"] = df["valor_estimado"].apply(formatar_moeda)

    st.subheader("Licitações Cadastradas")
    edited_df = st.data_editor(
        df if not df.empty else pd.DataFrame(columns=columns),
        num_rows="dynamic",
        use_container_width=True,
        key="editor_licitacoes",
        hide_index=True,
        column_config={
            "valor_estimado": st.column_config.TextColumn("Valor Estimado (R$)")
        }
    )

    if not df.empty and not edited_df.equals(df):
        try:
            for _, row in edited_df.iterrows():
                row_id = row["id"]
                valor_numerico = parse_valor(row["valor_estimado"])
                cursor.execute('''
                    UPDATE licitacoes
                    SET modalidade=?, objeto=?, valor_estimado=?, data_abertura=?, data_homologacao=?, situacao=?
                    WHERE id=?
                ''', (
                    row["modalidade"], row["objeto"], valor_numerico, row["data_abertura"],
                    row.get("data_homologacao"), row["situacao"], row_id
                ))
            conn.commit()
            st.success("Alterações salvas!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar: {e}")

    if not df.empty:
        st.subheader("Excluir Registro")
        ids = df["id"].tolist()
        id_excluir = st.selectbox("Selecione o ID para excluir", ids, key="delete_licitacao")
        if st.button("Excluir", key="btn_delete_licitacao"):
            try:
                cursor.execute("DELETE FROM licitacoes WHERE id=?", (id_excluir,))
                conn.commit()
                st.success("Registro excluído!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")


def contratos_page():
    st.title("Contratos")
    st.markdown("Cadastro e gerenciamento de contratos")
    st.divider()

    cursor = conn.cursor()

    with st.expander("Adicionar Novo Contrato", expanded=False):
        with st.form("form_add_contrato"):
            col1, col2 = st.columns(2)
            with col1:
                numero_contrato = st.text_input("Número do Contrato", key="add_numero_contrato")
                fornecedor = st.text_input("Fornecedor", key="add_fornecedor_contrato")
                objeto = st.text_input("Objeto", key="add_objeto_contrato")
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f", key="add_valor_contrato")
            with col2:
                data_inicio = st.date_input("Data de Início", key="add_data_inicio_contrato")
                data_fim = st.date_input("Data de Fim", key="add_data_fim_contrato")
                situacao = st.selectbox("Situação", ["Vigente", "Encerrado", "Suspenso"], key="add_situacao_contrato")
            submitted = st.form_submit_button("Salvar", use_container_width=True)
            if submitted:
                if not numero_contrato or not fornecedor or not objeto or valor <= 0:
                    st.error("Preencha todos os campos obrigatórios com valores válidos.")
                elif data_fim < data_inicio:
                    st.error("A data de fim não pode ser anterior à data de início.")
                else:
                    try:
                        cursor.execute('''
                            INSERT INTO contratos (numero_contrato, fornecedor, objeto, valor, data_inicio, data_fim, situacao)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (numero_contrato, fornecedor, objeto, valor, data_inicio, data_fim, situacao))
                        conn.commit()
                        st.success("Contrato registrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    cursor.execute("SELECT * FROM contratos ORDER BY data_inicio DESC")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(rows, columns=columns)

    if not df.empty:
        df["valor"] = df["valor"].apply(formatar_moeda)

    st.subheader("Contratos Cadastrados")
    edited_df = st.data_editor(
        df if not df.empty else pd.DataFrame(columns=columns),
        num_rows="dynamic",
        use_container_width=True,
        key="editor_contratos",
        hide_index=True,
        column_config={
            "valor": st.column_config.TextColumn("Valor (R$)")
        }
    )

    if not df.empty and not edited_df.equals(df):
        try:
            for _, row in edited_df.iterrows():
                row_id = row["id"]
                valor_numerico = parse_valor(row["valor"])
                cursor.execute('''
                    UPDATE contratos
                    SET numero_contrato=?, fornecedor=?, objeto=?, valor=?, data_inicio=?, data_fim=?, situacao=?
                    WHERE id=?
                ''', (
                    row["numero_contrato"], row["fornecedor"], row["objeto"], valor_numerico,
                    row["data_inicio"], row["data_fim"], row["situacao"], row_id
                ))
            conn.commit()
            st.success("Alterações salvas!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar: {e}")

    if not df.empty:
        st.subheader("Excluir Registro")
        ids = df["id"].tolist()
        id_excluir = st.selectbox("Selecione o ID para excluir", ids, key="delete_contrato")
        if st.button("Excluir", key="btn_delete_contrato"):
            try:
                cursor.execute("DELETE FROM contratos WHERE id=?", (id_excluir,))
                conn.commit()
                st.success("Registro excluído!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao excluir: {e}")


def relatorios_page():
    st.title("Relatórios")
    st.markdown("Visualize e exporte resumos de todas as áreas")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data Inicial", value=datetime.date.today().replace(day=1), key="rel_inicio")
    with col2:
        data_fim = st.date_input("Data Final", value=datetime.date.today(), key="rel_fim")

    if data_fim < data_inicio:
        st.error("A data final não pode ser anterior à data inicial.")
        return

    cursor = conn.cursor()

    st.subheader("Contas a Pagar")
    cursor.execute('''
        SELECT id, fornecedor, descricao, valor, vencimento, status, data_pagamento, observacao
        FROM contas_pagar
        WHERE vencimento BETWEEN ? AND ?
        ORDER BY vencimento
    ''', (data_inicio, data_fim))
    rows = cursor.fetchall()
    if rows:
        df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])
        df["valor"] = df["valor"].apply(formatar_moeda)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma conta a pagar no período selecionado.")

    st.subheader("Contas a Receber")
    cursor.execute('''
        SELECT id, cliente, descricao, valor, vencimento, status, data_recebimento, observacao
        FROM contas_receber
        WHERE vencimento BETWEEN ? AND ?
        ORDER BY vencimento
    ''', (data_inicio, data_fim))
    rows = cursor.fetchall()
    if rows:
        df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])
        df["valor"] = df["valor"].apply(formatar_moeda)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma conta a receber no período selecionado.")

    st.subheader("Empenhos")
    cursor.execute('''
        SELECT id, numero_empenho, fornecedor, descricao, valor, data_empenho, data_cancelamento, status
        FROM empenhos
        WHERE data_empenho BETWEEN ? AND ?
        ORDER BY data_empenho
    ''', (data_inicio, data_fim))
    rows = cursor.fetchall()
    if rows:
        df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])
        df["valor"] = df["valor"].apply(formatar_moeda)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum empenho no período selecionado.")

    st.subheader("Licitações")
    cursor.execute('''
        SELECT id, modalidade, objeto, valor_estimado, data_abertura, data_homologacao, situacao
        FROM licitacoes
        WHERE data_abertura BETWEEN ? AND ?
        ORDER BY data_abertura
    ''', (data_inicio, data_fim))
    rows = cursor.fetchall()
    if rows:
        df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])
        df["valor_estimado"] = df["valor_estimado"].apply(formatar_moeda)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma licitação no período selecionado.")

    st.subheader("Contratos")
    cursor.execute('''
        SELECT id, numero_contrato, fornecedor, objeto, valor, data_inicio, data_fim, situacao
        FROM contratos
        WHERE data_inicio BETWEEN ? AND ?
        ORDER BY data_inicio
    ''', (data_inicio, data_fim))
    rows = cursor.fetchall()
    if rows:
        df = pd.DataFrame(rows, columns=[desc[0] for desc in cursor.description])
        df["valor"] = df["valor"].apply(formatar_moeda)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum contrato no período selecionado.")


def main():
    init_db()

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "page" not in st.session_state:
        st.session_state.page = "Login"
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False
    if "selected_record" not in st.session_state:
        st.session_state.selected_record = None

    if not st.session_state.authenticated:
        login_page()
    else:
        sidebar_navigation()
        pagina = st.session_state.page

        if pagina == "Dashboard":
            dashboard_page()
        elif pagina == "Contas a Pagar":
            contas_pagar_page()
        elif pagina == "Contas a Receber":
            contas_receber_page()
        elif pagina == "Empenhos":
            empenhos_page()
        elif pagina == "Licitações":
            licitacoes_page()
        elif pagina == "Contratos":
            contratos_page()
        elif pagina == "Relatórios":
            relatorios_page()
        else:
            dashboard_page()


if __name__ == "__main__":
    main()
