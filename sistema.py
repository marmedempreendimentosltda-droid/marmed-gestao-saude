import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, date
import os

# Configuração da página
st.set_page_config(
    page_title="MARMED - Gestão em Saúde Pública",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4788;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 5px solid #1f4788;
    }
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .stButton>button {
        background-color: #1f4788;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #2d5ca3;
    }
    </style>
""", unsafe_allow_html=True)

# Banco de dados
DB_FILE = "marmed_saude.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nome TEXT NOT NULL,
            perfil TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contas_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            fornecedor TEXT NOT NULL,
            valor REAL NOT NULL,
            data_vencimento DATE NOT NULL,
            data_emissao DATE NOT NULL,
            categoria TEXT NOT NULL,
            status TEXT NOT NULL,
            observacoes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contas_receber (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            devedor TEXT NOT NULL,
            valor REAL NOT NULL,
            data_vencimento DATE NOT NULL,
            data_emissao DATE NOT NULL,
            categoria TEXT NOT NULL,
            status TEXT NOT NULL,
            observacoes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empenhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_empenho TEXT NOT NULL,
            descricao TEXT NOT NULL,
            fornecedor TEXT NOT NULL,
            valor REAL NOT NULL,
            data_empenho DATE NOT NULL,
            categoria TEXT NOT NULL,
            status TEXT NOT NULL,
            observacoes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_licitacao TEXT NOT NULL,
            objeto TEXT NOT NULL,
            modalidade TEXT NOT NULL,
            valor_estimado REAL NOT NULL,
            valor_realizado REAL,
            data_abertura DATE NOT NULL,
            status TEXT NOT NULL,
            vencedor TEXT,
            observacoes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_contrato TEXT NOT NULL,
            objeto TEXT NOT NULL,
            contratada TEXT NOT NULL,
            valor REAL NOT NULL,
            data_inicio DATE NOT NULL,
            data_fim DATE NOT NULL,
            status TEXT NOT NULL,
            observacoes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        admin_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
        cursor.execute("""
            INSERT INTO usuarios (username, password_hash, nome, perfil)
            VALUES (?, ?, ?, ?)
        """, ("admin", admin_hash, "Administrador", "admin"))

    conn.commit()
    conn.close()


def verificar_login(username, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("SELECT * FROM usuarios WHERE username=? AND password_hash=?", (username, password_hash))
    user = cursor.fetchone()
    conn.close()
    return user


def login_page():
    st.markdown('<div class="main-header">MARMED</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Gestão em Saúde Pública - Luminárias/MG</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🔐 Acesso ao Sistema")
        username = st.text_input("Usuário", key="login_username")
        password = st.text_input("Senha", type="password", key="login_password")

        if st.button("Entrar", use_container_width=True):
            if username and password:
                user = verificar_login(username, password)
                if user:
                    st.session_state["logged_in"] = True
                    st.session_state["user"] = user
                    st.session_state["pagina"] = "Dashboard"
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos")
            else:
                st.warning("Preencha usuário e senha")
        st.markdown('</div>', unsafe_allow_html=True)


def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def sidebar_menu():
    st.sidebar.markdown("## 🏥 MARMED")
    st.sidebar.markdown("*Gestão em Saúde Pública*")
    st.sidebar.markdown("*Luminárias/MG*")
    st.sidebar.markdown("---")

    if "user" in st.session_state:
        st.sidebar.markdown(f"**Usuário:** {st.session_state['user'][3]}")
        st.sidebar.markdown(f"**Perfil:** {st.session_state['user'][4].upper()}")
    st.sidebar.markdown("---")

    paginas = [
        "Dashboard",
        "Contas a Pagar",
        "Contas a Receber",
        "Empenhos",
        "Licitações",
        "Contratos",
        "Relatórios",
        "Trocar Senha",
        "Sair"
    ]

    for pagina in paginas:
        if st.sidebar.button(pagina, use_container_width=True, key=f"btn_{pagina}"):
            if pagina == "Sair":
                logout()
            else:
                st.session_state["pagina"] = pagina
                st.rerun()


def dashboard_page():
    st.markdown('<div class="main-header">Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Visão Geral da Gestão em Saúde Pública - Luminárias/MG</div>', unsafe_allow_html=True)

    conn = sqlite3.connect(DB_FILE)

    total_pagar = pd.read_sql_query("SELECT COALESCE(SUM(valor), 0) as total FROM contas_pagar", conn).iloc[0, 0]
    total_receber = pd.read_sql_query("SELECT COALESCE(SUM(valor), 0) as total FROM contas_receber", conn).iloc[0, 0]
    total_empenhos = pd.read_sql_query("SELECT COALESCE(SUM(valor), 0) as total FROM empenhos", conn).iloc[0, 0]
    total_contratos = pd.read_sql_query("SELECT COALESCE(SUM(valor), 0) as total FROM contratos", conn).iloc[0, 0]

    conn.close()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><h3>Contas a Pagar</h3><h2>R$ {total_pagar:,.2f}</h2></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><h3>Contas a Receber</h3><h2>R$ {total_receber:,.2f}</h2></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><h3>Empenhos</h3><h2>R$ {total_empenhos:,.2f}</h2></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><h3>Contratos</h3><h2>R$ {total_contratos:,.2f}</h2></div>', unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📊 Contas a Pagar por Status")
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT status, SUM(valor) as total FROM contas_pagar GROUP BY status", conn)
        conn.close()
        if not df.empty:
            st.bar_chart(df.set_index("status"))
        else:
            st.info("Nenhum dado disponível")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📈 Contas a Receber por Status")
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT status, SUM(valor) as total FROM contas_receber GROUP BY status", conn)
        conn.close()
        if not df.empty:
            st.bar_chart(df.set_index("status"))
        else:
            st.info("Nenhum dado disponível")
        st.markdown('</div>', unsafe_allow_html=True)


def contas_pagar_page():
    st.markdown('<div class="main-header">Contas a Pagar</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Gestão de Despesas e Obrigações Financeiras</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Cadastrar", "Consultar/Editar"])

    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.form("form_conta_pagar"):
            col1, col2 = st.columns(2)
            with col1:
                descricao = st.text_input("Descrição")
                fornecedor = st.text_input("Fornecedor")
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            with col2:
                data_emissao = st.date_input("Data de Emissão", value=date.today())
                data_vencimento = st.date_input("Data de Vencimento", value=date.today())
                categoria = st.selectbox("Categoria", ["Medicamentos", "Material de Consumo", "Serviços", "Obras", "Outros"])
                status = st.selectbox("Status", ["Pendente", "Pago", "Atrasado", "Cancelado"])
            observacoes = st.text_area("Observações")
            submitted = st.form_submit_button("Salvar Conta a Pagar")
            if submitted:
                if descricao and fornecedor and valor > 0:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO contas_pagar (descricao, fornecedor, valor, data_vencimento, data_emissao, categoria, status, observacoes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (descricao, fornecedor, valor, data_vencimento, data_emissao, categoria, status, observacoes))
                    conn.commit()
                    conn.close()
                    st.success("Conta a pagar cadastrada com sucesso!")
                else:
                    st.warning("Preencha todos os campos obrigatórios")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM contas_pagar ORDER BY data_vencimento", conn)
        conn.close()

        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhuma conta a pagar cadastrada")
        st.markdown('</div>', unsafe_allow_html=True)


def contas_receber_page():
    st.markdown('<div class="main-header">Contas a Receber</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Gestão de Receitas e Créditos</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Cadastrar", "Consultar/Editar"])

    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.form("form_conta_receber"):
            col1, col2 = st.columns(2)
            with col1:
                descricao = st.text_input("Descrição")
                devedor = st.text_input("Devedor")
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            with col2:
                data_emissao = st.date_input("Data de Emissão", value=date.today())
                data_vencimento = st.date_input("Data de Vencimento", value=date.today())
                categoria = st.selectbox("Categoria", ["Transferências", "Convênios", "Repasse Federal", "Repasse Estadual", "Outros"])
                status = st.selectbox("Status", ["Pendente", "Recebido", "Atrasado", "Cancelado"])
            observacoes = st.text_area("Observações")
            submitted = st.form_submit_button("Salvar Conta a Receber")
            if submitted:
                if descricao and devedor and valor > 0:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO contas_receber (descricao, devedor, valor, data_vencimento, data_emissao, categoria, status, observacoes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (descricao, devedor, valor, data_vencimento, data_emissao, categoria, status, observacoes))
                    conn.commit()
                    conn.close()
                    st.success("Conta a receber cadastrada com sucesso!")
                else:
                    st.warning("Preencha todos os campos obrigatórios")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM contas_receber ORDER BY data_vencimento", conn)
        conn.close()

        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhuma conta a receber cadastrada")
        st.markdown('</div>', unsafe_allow_html=True)


def empenhos_page():
    st.markdown('<div class="main-header">Empenhos</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Controle de Empenhos Orçamentários</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Cadastrar", "Consultar/Editar"])

    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.form("form_empenho"):
            col1, col2 = st.columns(2)
            with col1:
                numero_empenho = st.text_input("Número do Empenho")
                descricao = st.text_input("Descrição")
                fornecedor = st.text_input("Fornecedor")
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            with col2:
                data_empenho = st.date_input("Data do Empenho", value=date.today())
                categoria = st.selectbox("Categoria", ["Medicamentos", "Material de Consumo", "Serviços", "Obras", "Outros"])
                status = st.selectbox("Status", ["Ativo", "Anulado", "Liquidado", "Cancelado"])
            observacoes = st.text_area("Observações")
            submitted = st.form_submit_button("Salvar Empenho")
            if submitted:
                if numero_empenho and descricao and fornecedor and valor > 0:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO empenhos (numero_empenho, descricao, fornecedor, valor, data_empenho, categoria, status, observacoes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (numero_empenho, descricao, fornecedor, valor, data_empenho, categoria, status, observacoes))
                    conn.commit()
                    conn.close()
                    st.success("Empenho cadastrado com sucesso!")
                else:
                    st.warning("Preencha todos os campos obrigatórios")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM empenhos ORDER BY data_empenho", conn)
        conn.close()

        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhum empenho cadastrado")
        st.markdown('</div>', unsafe_allow_html=True)


def licitacoes_page():
    st.markdown('<div class="main-header">Licitações</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Gestão de Processos Licitatórios</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Cadastrar", "Consultar/Editar"])

    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.form("form_licitacao"):
            col1, col2 = st.columns(2)
            with col1:
                numero_licitacao = st.text_input("Número da Licitação")
                objeto = st.text_input("Objeto")
                modalidade = st.selectbox("Modalidade", ["Pregão", "Concorrência", "Convite", "Tomada de Preços", "Dispensa", "Inexigibilidade"])
                valor_estimado = st.number_input("Valor Estimado (R$)", min_value=0.0, format="%.2f")
                valor_realizado = st.number_input("Valor Realizado (R$)", min_value=0.0, format="%.2f")
            with col2:
                data_abertura = st.date_input("Data de Abertura", value=date.today())
                status = st.selectbox("Status", ["Em Andamento", "Concluída", "Cancelada", "Deserta", "Homologada"])
                vencedor = st.text_input("Vencedor")
            observacoes = st.text_area("Observações")
            submitted = st.form_submit_button("Salvar Licitação")
            if submitted:
                if numero_licitacao and objeto and valor_estimado >= 0:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO licitacoes (numero_licitacao, objeto, modalidade, valor_estimado, valor_realizado, data_abertura, status, vencedor, observacoes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (numero_licitacao, objeto, modalidade, valor_estimado, valor_realizado, data_abertura, status, vencedor, observacoes))
                    conn.commit()
                    conn.close()
                    st.success("Licitação cadastrada com sucesso!")
                else:
                    st.warning("Preencha todos os campos obrigatórios")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM licitacoes ORDER BY data_abertura", conn)
        conn.close()

        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhuma licitação cadastrada")
        st.markdown('</div>', unsafe_allow_html=True)


def contratos_page():
    st.markdown('<div class="main-header">Contratos</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Gestão de Contratos e Convênios</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Cadastrar", "Consultar/Editar"])

    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        with st.form("form_contrato"):
            col1, col2 = st.columns(2)
            with col1:
                numero_contrato = st.text_input("Número do Contrato")
                objeto = st.text_input("Objeto")
                contratada = st.text_input("Contratada")
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            with col2:
                data_inicio = st.date_input("Data de Início", value=date.today())
                data_fim = st.date_input("Data de Término", value=date.today())
                status = st.selectbox("Status", ["Vigente", "Concluído", "Cancelado", "Suspenso", "Rescindido"])
            observacoes = st.text_area("Observações")
            submitted = st.form_submit_button("Salvar Contrato")
            if submitted:
                if numero_contrato and objeto and contratada and valor > 0:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO contratos (numero_contrato, objeto, contratada, valor, data_inicio, data_fim, status, observacoes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (numero_contrato, objeto, contratada, valor, data_inicio, data_fim, status, observacoes))
                    conn.commit()
                    conn.close()
                    st.success("Contrato cadastrado com sucesso!")
                else:
                    st.warning("Preencha todos os campos obrigatórios")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT * FROM contratos ORDER BY data_inicio", conn)
        conn.close()

        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhum contrato cadastrado")
        st.markdown('</div>', unsafe_allow_html=True)


def relatorios_page():
    st.markdown('<div class="main-header">Relatórios</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Emissão de Relatórios Gerenciais</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    tipo_relatorio = st.selectbox("Tipo de Relatório", [
        "Contas a Pagar",
        "Contas a Receber",
        "Empenhos",
        "Licitações",
        "Contratos",
        "Resumo Geral"
    ])

    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data Início", value=date(date.today().year, 1, 1))
    with col2:
        data_fim = st.date_input("Data Fim", value=date.today())

    if st.button("Gerar Relatório"):
        conn = sqlite3.connect(DB_FILE)

        if tipo_relatorio == "Contas a Pagar":
            query = """
                SELECT * FROM contas_pagar
                WHERE data_vencimento BETWEEN ? AND ?
                ORDER BY data_vencimento
            """
            df = pd.read_sql_query(query, conn, params=(data_inicio, data_fim))
            total = df["valor"].sum() if not df.empty else 0
            st.subheader(f"Total: R$ {total:,.2f}")
            st.dataframe(df, use_container_width=True)

        elif tipo_relatorio == "Contas a Receber":
            query = """
                SELECT * FROM contas_receber
                WHERE data_vencimento BETWEEN ? AND ?
                ORDER BY data_vencimento
            """
            df = pd.read_sql_query(query, conn, params=(data_inicio, data_fim))
            total = df["valor"].sum() if not df.empty else 0
            st.subheader(f"Total: R$ {total:,.2f}")
            st.dataframe(df, use_container_width=True)

        elif tipo_relatorio == "Empenhos":
            query = """
                SELECT * FROM empenhos
                WHERE data_empenho BETWEEN ? AND ?
                ORDER BY data_empenho
            """
            df = pd.read_sql_query(query, conn, params=(data_inicio, data_fim))
            total = df["valor"].sum() if not df.empty else 0
            st.subheader(f"Total: R$ {total:,.2f}")
            st.dataframe(df, use_container_width=True)

        elif tipo_relatorio == "Licitações":
            query = """
                SELECT * FROM licitacoes
                WHERE data_abertura BETWEEN ? AND ?
                ORDER BY data_abertura
            """
            df = pd.read_sql_query(query, conn, params=(data_inicio, data_fim))
            total_estimado = df["valor_estimado"].sum() if not df.empty else 0
            total_realizado = df["valor_realizado"].sum() if not df.empty else 0
            st.subheader(f"Total Estimado: R$ {total_estimado:,.2f} | Total Realizado: R$ {total_realizado:,.2f}")
            st.dataframe(df, use_container_width=True)

        elif tipo_relatorio == "Contratos":
            query = """
                SELECT * FROM contratos
                WHERE data_inicio BETWEEN ? AND ?
                ORDER BY data_inicio
            """
            df = pd.read_sql_query(query, conn, params=(data_inicio, data_fim))
            total = df["valor"].sum() if not df.empty else 0
            st.subheader(f"Total: R$ {total:,.2f}")
            st.dataframe(df, use_container_width=True)

        elif tipo_relatorio == "Resumo Geral":
            st.subheader("Resumo Geral do Período")
            total_pagar = pd.read_sql_query("""
                SELECT COALESCE(SUM(valor), 0) as total FROM contas_pagar
                WHERE data_vencimento BETWEEN ? AND ?
            """, conn, params=(data_inicio, data_fim)).iloc[0, 0]
            total_receber = pd.read_sql_query("""
                SELECT COALESCE(SUM(valor), 0) as total FROM contas_receber
                WHERE data_vencimento BETWEEN ? AND ?
            """, conn, params=(data_inicio, data_fim)).iloc[0, 0]
            total_empenhos = pd.read_sql_query("""
                SELECT COALESCE(SUM(valor), 0) as total FROM empenhos
                WHERE data_empenho BETWEEN ? AND ?
            """, conn, params=(data_inicio, data_fim)).iloc[0, 0]
            total_contratos = pd.read_sql_query("""
                SELECT COALESCE(SUM(valor), 0) as total FROM contratos
                WHERE data_inicio BETWEEN ? AND ?
            """, conn, params=(data_inicio, data_fim)).iloc[0, 0]
            total_licitacoes = pd.read_sql_query("""
                SELECT COALESCE(SUM(valor_realizado), 0) as total FROM licitacoes
                WHERE data_abertura BETWEEN ? AND ?
            """, conn, params=(data_inicio, data_fim)).iloc[0, 0]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Contas a Pagar", f"R$ {total_pagar:,.2f}")
                st.metric("Contas a Receber", f"R$ {total_receber:,.2f}")
            with col2:
                st.metric("Empenhos", f"R$ {total_empenhos:,.2f}")
                st.metric("Contratos", f"R$ {total_contratos:,.2f}")
            with col3:
                st.metric("Licitações Realizadas", f"R$ {total_licitacoes:,.2f}")
                saldo = total_receber - total_pagar
                st.metric("Saldo Projetado", f"R$ {saldo:,.2f}")

        conn.close()
    st.markdown('</div>', unsafe_allow_html=True)


def trocar_senha_page():
    st.markdown('<div class="main-header">Trocar Senha</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Altere sua senha de acesso ao sistema</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    with st.form("form_trocar_senha"):
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
        submitted = st.form_submit_button("Alterar Senha")

        if submitted:
            if not senha_atual or not nova_senha or not confirmar_senha:
                st.error("Todos os campos são obrigatórios")
            else:
                username = st.session_state["user"][1]
                senha_atual_hash = hashlib.sha256(senha_atual.encode()).hexdigest()

                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT password_hash FROM usuarios WHERE username=?", (username,))
                resultado = cursor.fetchone()

                if not resultado or resultado[0] != senha_atual_hash:
                    conn.close()
                    st.error("Senha atual incorreta")
                elif len(nova_senha) < 6:
                    conn.close()
                    st.error("A nova senha deve ter pelo menos 6 caracteres")
                elif nova_senha != confirmar_senha:
                    conn.close()
                    st.error("A nova senha e a confirmação não coincidem")
                else:
                    nova_senha_hash = hashlib.sha256(nova_senha.encode()).hexdigest()
                    cursor.execute("UPDATE usuarios SET password_hash=? WHERE username=?", (nova_senha_hash, username))
                    conn.commit()
                    conn.close()
                    st.success("Senha alterada com sucesso!")
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def main():
    init_db()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "pagina" not in st.session_state:
        st.session_state["pagina"] = "Dashboard"

    if not st.session_state["logged_in"]:
        login_page()
    else:
        sidebar_menu()

        pagina = st.session_state.get("pagina", "Dashboard")

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
        elif pagina == "Trocar Senha":
            trocar_senha_page()


if __name__ == "__main__":
    main()
