import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import sqlite3
import hashlib
import os

DB_FILE = 'marmed.db'

# ============================================================
# CONFIGURAÇÃO INICIAL
# ============================================================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        senha_hash TEXT,
        perfil TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS exercicios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ano INTEGER UNIQUE,
        ativo INTEGER,
        orcamento_total REAL
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS orgaos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        codigo TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS programas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT,
        nome TEXT,
        exercicio_id INTEGER
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS acoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT,
        nome TEXT,
        programa_id INTEGER
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS naturezas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT,
        descricao TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS fontes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT,
        descricao TEXT,
        tipo TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS dotacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercicio_id INTEGER,
        orgao_id INTEGER,
        programa_id INTEGER,
        acao_id INTEGER,
        natureza_id INTEGER,
        fonte_id INTEGER,
        valor REAL
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS receitas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercicio_id INTEGER,
        fonte_id INTEGER,
        descricao TEXT,
        valor_previsto REAL,
        valor_arrecadado REAL
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS ppa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercicio TEXT,
        diretrizes TEXT,
        objetivos TEXT,
        metas TEXT,
        valor_previsto REAL,
        programa TEXT,
        orgao TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS ldo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercicio TEXT,
        descricao TEXT,
        metas_fiscais TEXT,
        prioridades TEXT,
        limites_programa TEXT,
        data_aprovacao TEXT,
        link_lc141 TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS pas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ano INTEGER,
        acoes TEXT,
        indicadores TEXT,
        meta TEXT,
        previsao_orcamentaria REAL,
        status TEXT,
        observacoes TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS plano_saude (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        periodo TEXT,
        diretrizes TEXT,
        objetivos TEXT,
        metas TEXT,
        populacao_estimada INTEGER,
        orcamento_previsto REAL
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS fornecedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        nome TEXT,
        cpf_cnpj TEXT,
        endereco TEXT,
        banco TEXT,
        agencia TEXT,
        conta TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS prestadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        cnes TEXT,
        tipo TEXT,
        conselho TEXT,
        validade TEXT,
        especialidade TEXT,
        situacao TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS pacientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        cpf TEXT,
        nascimento TEXT,
        sexo TEXT,
        endereco TEXT,
        telefone TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS atendimentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        paciente_id INTEGER,
        data TEXT,
        tipo TEXT,
        prestador_id INTEGER,
        descricao TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS renen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        cnes TEXT,
        tipo TEXT,
        municipio TEXT,
        gestao TEXT,
        natureza TEXT,
        situacao TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS licitacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        modalidade TEXT,
        objeto TEXT,
        dotacao_id INTEGER,
        fornecedor_id INTEGER,
        valor_total REAL,
        qtd_total REAL,
        saldo REAL,
        situacao TEXT,
        alerta_percentual REAL
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS ordens_compra (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        licitacao_id INTEGER,
        fornecedor_id INTEGER,
        numero TEXT,
        data TEXT,
        valor REAL,
        qtd REAL,
        descricao TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS contratos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        fornecedor_id INTEGER,
        objeto TEXT,
        valor_inicial REAL,
        valor_atual REAL,
        data_inicio TEXT,
        data_fim TEXT,
        situacao TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS aditivos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contrato_id INTEGER,
        tipo TEXT,
        valor REAL,
        data TEXT,
        descricao TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS empenhos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dotacao_id INTEGER,
        numero TEXT,
        data TEXT,
        valor_empenhado REAL,
        valor_liquidado REAL,
        valor_pago REAL,
        fornecedor_id INTEGER,
        descricao TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS suplementacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dotacao_id INTEGER,
        tipo TEXT,
        numero TEXT,
        data TEXT,
        valor REAL,
        descricao TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS leitos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        estabelecimento TEXT,
        tipo TEXT,
        total INTEGER,
        ocupados INTEGER,
        data TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS producao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        estabelecimento TEXT,
        quantidade INTEGER,
        data TEXT
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS alertas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        modulo TEXT,
        percentual REAL
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS configuracoes (
        chave TEXT PRIMARY KEY,
        valor TEXT
    )
    ''')

    conn.commit()
    return conn


def seed_data(conn):
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM exercicios")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO exercicios (ano, ativo, orcamento_total) VALUES (?, ?, ?)", (2026, 1, 76935000.00))

    c.execute("SELECT COUNT(*) FROM orgaos")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO orgaos (nome, codigo) VALUES (?, ?)", ("Secretaria Municipal de Saúde de Luminárias", "SMS-LUM"))

    c.execute("SELECT COUNT(*) FROM programas")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO programas (codigo, nome, exercicio_id) VALUES (?, ?, ?)", ("2010", "Saúde da Família", 1))
        c.execute("INSERT INTO programas (codigo, nome, exercicio_id) VALUES (?, ?, ?)", ("2021", "Assistência Hospitalar e Ambulatorial", 1))

    c.execute("SELECT COUNT(*) FROM acoes")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO acoes (codigo, nome, programa_id) VALUES (?, ?, ?)", ("2011", "Saúde da Família - PSF", 1))
        c.execute("INSERT INTO acoes (codigo, nome, programa_id) VALUES (?, ?, ?)", ("2022", "Atendimento Ambulatorial", 2))
        c.execute("INSERT INTO acoes (codigo, nome, programa_id) VALUES (?, ?, ?)", ("2023", "Hospital Municipal", 2))

    c.execute("SELECT COUNT(*) FROM naturezas")
    if c.fetchone()[0] == 0:
        for n in [("3.3.90.00", "Outras Despesas Correntes"), ("3.3.50.00", "Serviços de Terceiros"), ("4.4.50.00", "Investimentos")]:
            c.execute("INSERT INTO naturezas (codigo, descricao) VALUES (?, ?)", n)

    c.execute("SELECT COUNT(*) FROM fontes")
    if c.fetchone()[0] == 0:
        for f in [("10000000", "Recursos Ordinários - Receitas Federais SUS", "Federal"),
                  ("15000000", "Receitas Federais SUS - Conta 1", "Federal"),
                  ("15000001", "Receitas Federais SUS - Conta 2", "Federal"),
                  ("15000002", "Receitas Federais SUS - Conta 3", "Federal"),
                  ("15000003", "Receitas Federais SUS - Conta 4", "Federal"),
                  ("15000004", "Receitas Federais SUS - Conta 5", "Federal"),
                  ("15000005", "Receitas Federais SUS - Conta 6", "Federal"),
                  ("15000006", "Receitas Federais SUS - Conta 7", "Federal"),
                  ("16000000", "Recursos Estaduais - CIS", "Estadual")]:
            c.execute("INSERT INTO fontes (codigo, descricao, tipo) VALUES (?, ?, ?)", f)

    c.execute("SELECT COUNT(*) FROM dotacoes")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO dotacoes (exercicio_id, orgao_id, programa_id, acao_id, natureza_id, fonte_id, valor) VALUES (?,?,?,?,?,?,?)", (1, 1, 1, 1, 1, 1, 50000000.0))
        c.execute("INSERT INTO dotacoes (exercicio_id, orgao_id, programa_id, acao_id, natureza_id, fonte_id, valor) VALUES (?,?,?,?,?,?,?)", (1, 1, 2, 2, 1, 1, 15000000.0))
        c.execute("INSERT INTO dotacoes (exercicio_id, orgao_id, programa_id, acao_id, natureza_id, fonte_id, valor) VALUES (?,?,?,?,?,?,?)", (1, 1, 2, 3, 1, 9, 11935000.0))

    c.execute("SELECT COUNT(*) FROM receitas")
    if c.fetchone()[0] == 0:
        for desc, val in [("SUS Federal - Conta 1", 5000000.0), ("SUS Federal - Conta 2", 4500000.0), ("SUS Federal - Conta 3", 4200000.0),
                          ("SUS Federal - Conta 4", 4100000.0), ("SUS Federal - Conta 5", 4000000.0), ("SUS Federal - Conta 6", 3900000.0),
                          ("SUS Federal - Conta 7", 3800000.0), ("Recursos Estaduais - CIS", 11935000.0)]:
            c.execute("INSERT INTO receitas (exercicio_id, fonte_id, descricao, valor_previsto, valor_arrecadado) VALUES (?, ?, ?, ?, ?)", (1, 1, desc, val, 0.0))

    c.execute("SELECT COUNT(*) FROM renen")
    if c.fetchone()[0] == 0:
        for r in [("UBS Central", "1234567", "UBS", "Luminárias", "Municipal", "Público", "Ativo"),
                  ("Hospital Municipal", "7654321", "Hospital", "Luminárias", "Municipal", "Público", "Ativo"),
                  ("Laboratório Luminárias", "1111111", "Laboratório", "Luminárias", "Municipal", "Privado", "Ativo")]:
            c.execute("INSERT INTO renen (nome, cnes, tipo, municipio, gestao, natureza, situacao) VALUES (?, ?, ?, ?, ?, ?, ?)", r)

    c.execute("SELECT COUNT(*) FROM leitos")
    if c.fetchone()[0] == 0:
        for l in [("Hospital Municipal", "UTI", 10, 7), ("Hospital Municipal", "Clínica Médica", 30, 20), ("Hospital Municipal", "Obstetrícia", 12, 8)]:
            c.execute("INSERT INTO leitos (estabelecimento, tipo, total, ocupados, data) VALUES (?, ?, ?, ?, ?)", (l[0], l[1], l[2], l[3], date.today().isoformat()))

    c.execute("SELECT COUNT(*) FROM producao")
    if c.fetchone()[0] == 0:
        for p in [("Ambulatorial", "UBS Central", 1200), ("Hospitalar", "Hospital Municipal", 450), ("Exames", "Laboratório Luminárias", 3200)]:
            c.execute("INSERT INTO producao (tipo, estabelecimento, quantidade, data) VALUES (?, ?, ?, ?)", (p[0], p[1], p[2], date.today().isoformat()))

    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO usuarios (username, senha_hash, perfil) VALUES (?, ?, ?)", ("admin", hashlib.sha256("admin".encode()).hexdigest(), "admin"))

    c.execute("SELECT COUNT(*) FROM alertas")
    if c.fetchone()[0] == 0:
        for m in ["licitacoes", "contratos", "financeiro", "licitacao_saldo"]:
            c.execute("INSERT INTO alertas (modulo, percentual) VALUES (?, ?)", (m, 80.0))

    conn.commit()


def get_connection():
    return sqlite3.connect(DB_FILE)


def run_query(query, params=()):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def run_insert(query, params=()):
    conn = get_connection()
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    last_id = c.lastrowid
    conn.close()
    return last_id


def run_update(query, params=()):
    conn = get_connection()
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()


def run_delete(query, params=()):
    conn = get_connection()
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()


# ============================================================
# UTILITÁRIOS
# ============================================================

def format_currency(val):
    try:
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"


def format_percent(val):
    try:
        return f"{val:.1f}%"
    except:
        return "0,0%"


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def login_page():
    st.title("🔐 MARMED - Gestão em Saúde")
    st.markdown("### Sistema de Gestão Pública Municipal de Saúde")
    st.info("Use usuário **admin** e senha **admin** para acesso inicial.")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar", use_container_width=True)
            if submitted:
                conn = get_connection()
                c = conn.cursor()
                c.execute("SELECT id, username, perfil FROM usuarios WHERE username=? AND senha_hash=?", (username, hash_password(password)))
                user = c.fetchone()
                conn.close()
                if user:
                    st.session_state['authenticated'] = True
                    st.session_state['user'] = user[1]
                    st.session_state['perfil'] = user[2]
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos")


def sidebar_navigation():
    st.sidebar.markdown("# 🏥 MARMED")
    st.sidebar.markdown("### Gestão em Saúde")
    st.sidebar.divider()

    with st.sidebar.expander("🏠 Início", expanded=True):
        if st.button("Dashboard Principal", key="nav_dashboard", use_container_width=True):
            st.session_state['page'] = 'dashboard'

    with st.sidebar.expander("📋 Planejamento", expanded=True):
        for label, page in [("PPA", 'ppa'), ("LDO", 'ldo'), ("LOA", 'loa'), ("PAS", 'pas'), ("Plano de Saúde", 'plano_saude')]:
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                st.session_state['page'] = page

    with st.sidebar.expander("📑 Licitações e Contratos", expanded=True):
        for label, page in [("Licitações", 'licitacoes'), ("Ordens de Compra", 'ordens_compra'), ("Contratos", 'contratos')]:
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                st.session_state['page'] = page

    with st.sidebar.expander("👥 Cadastros", expanded=True):
        for label, page in [("Fornecedores", 'fornecedores'), ("Prestadores de Saúde", 'prestadores'), ("Pacientes", 'pacientes'), ("RENEN", 'renen')]:
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                st.session_state['page'] = page

    with st.sidebar.expander("🏥 Core Saúde", expanded=True):
        if st.button("Visão Geral Consolidada", key="nav_core", use_container_width=True):
            st.session_state['page'] = 'core_saude'

    with st.sidebar.expander("🔗 Sistemas Externos", expanded=True):
        if st.button("Links Úteis", key="nav_links", use_container_width=True):
            st.session_state['page'] = 'sistemas_externos'

    with st.sidebar.expander("📊 Organograma e Fluxos", expanded=True):
        for label, page in [("Organograma", 'organograma'), ("Fluxo Administrativo", 'fluxo_adm'), ("Fluxo da Saúde", 'fluxo_saude')]:
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                st.session_state['page'] = page

    with st.sidebar.expander("💰 Financeiro", expanded=True):
        for label, page in [("Execução Orçamentária", 'financeiro'), ("Suplementações", 'suplementacoes')]:
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                st.session_state['page'] = page

    with st.sidebar.expander("📈 Relatórios", expanded=True):
        for label, page in [("Exportação de Dados", 'exportacao'), ("Relatórios Consolidados", 'relatorios')]:
            if st.button(label, key=f"nav_{page}", use_container_width=True):
                st.session_state['page'] = page

    st.sidebar.divider()
    st.sidebar.markdown(f"👤 Usuário: **{st.session_state.get('user', '')}**")
    if st.sidebar.button("Sair", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# ============================================================
# PÁGINAS
# ============================================================

def page_dashboard():
    st.title("🏠 Dashboard Principal - MARMED")
    st.markdown("### Gestão Municipal de Saúde de Luminárias")

    col1, col2, col3, col4 = st.columns(4)

    df_dot = run_query("SELECT COALESCE(SUM(valor),0) as total FROM dotacoes")
    df_emp = run_query("SELECT COALESCE(SUM(valor_empenhado),0) as total FROM empenhos")
    df_liq = run_query("SELECT COALESCE(SUM(valor_liquidado),0) as total FROM empenhos")
    df_pag = run_query("SELECT COALESCE(SUM(valor_pago),0) as total FROM empenhos")

    orc_total = float(df_dot['total'].iloc[0])
    emp_total = float(df_emp['total'].iloc[0])
    liq_total = float(df_liq['total'].iloc[0])
    pag_total = float(df_pag['total'].iloc[0])

    with col1:
        st.metric("Orçamento Total", format_currency(orc_total))
    with col2:
        st.metric("Empenhado", format_currency(emp_total))
    with col3:
        st.metric("Liquidado", format_currency(liq_total))
    with col4:
        st.metric("Pago", format_currency(pag_total))

    c1, c2 = st.columns(2)

    with c1:
        df_rec = run_query("SELECT descricao, valor_previsto FROM receitas")
        if not df_rec.empty:
            fig = px.pie(df_rec, names='descricao', values='valor_previsto', title='Receitas Previstas por Fonte')
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        df_prog = run_query('''
            SELECT p.nome, SUM(d.valor) as total FROM dotacoes d
            JOIN programas p ON d.programa_id = p.id GROUP BY p.nome
        ''')
        if not df_prog.empty:
            fig = px.bar(df_prog, x='nome', y='total', title='Dotações por Programa', text_auto='.2s')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        df_lic = run_query("SELECT situacao, COUNT(*) as qtd FROM licitacoes GROUP BY situacao")
        if not df_lic.empty:
            fig = px.pie(df_lic, names='situacao', values='qtd', title='Situação das Licitações')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma licitação cadastrada")

    with c4:
        df_prod = run_query('''SELECT tipo, SUM(quantidade) as total FROM producao GROUP BY tipo''')
        if not df_prod.empty:
            fig = px.bar(df_prod, x='tipo', y='total', title='Produção por Tipo', text_auto=True)
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("⚠️ Alertas do Sistema")
    df_alertas = run_query("SELECT * FROM alertas")
    for _, row in df_alertas.iterrows():
        st.write(f"{row['modulo']}: alerta em {row['percentual']}%")


def page_ppa():
    st.title("📋 PPA - Plano Plurianual")
    tab1, tab2 = st.tabs(["Cadastro", "Consulta"])

    with tab1:
        with st.form("form_ppa"):
            exercicio = st.text_input("Exercício / Período")
            diretrizes = st.text_area("Diretrizes")
            objetivos = st.text_area("Objetivos")
            metas = st.text_area("Metas")
            valor = st.number_input("Valor Previsto", min_value=0.0, step=1000.0)
            programa = st.text_input("Programa")
            orgao = st.text_input("Órgão Responsável")
            if st.form_submit_button("Salvar"):
                run_insert("INSERT INTO ppa (exercicio, diretrizes, objetivos, metas, valor_previsto, programa, orgao) VALUES (?,?,?,?,?,?,?)",
                           (exercicio, diretrizes, objetivos, metas, valor, programa, orgao))
                st.success("PPA salvo")

    with tab2:
        df = run_query("SELECT * FROM ppa")
        st.dataframe(df, use_container_width=True)


def page_ldo():
    st.title("📋 LDO - Lei de Diretrizes Orçamentárias")
    tab1, tab2 = st.tabs(["Cadastro", "Consulta"])

    with tab1:
        with st.form("form_ldo"):
            exercicio = st.text_input("Exercício")
            descricao = st.text_area("Descrição")
            metas_fiscais = st.text_area("Metas Fiscais")
            prioridades = st.text_area("Prioridades")
            limites = st.text_area("Limites por Programa")
            data_aprov = st.date_input("Data Aprovação", value=date.today())
            link = st.text_input("Link LC 141")
            if st.form_submit_button("Salvar"):
                run_insert("INSERT INTO ldo (exercicio, descricao, metas_fiscais, prioridades, limites_programa, data_aprovacao, link_lc141) VALUES (?,?,?,?,?,?,?)",
                           (exercicio, descricao, metas_fiscais, prioridades, limites, data_aprov.isoformat(), link))
                st.success("LDO salva")

    with tab2:
        df = run_query("SELECT * FROM ldo")
        st.dataframe(df, use_container_width=True)


def page_loa():
    st.title("📋 LOA - Lei Orçamentária Anual")
    tab1, tab2 = st.tabs(["Cadastro", "Consulta"])

    with tab1:
        with st.form("form_loa"):
            exercicios = run_query("SELECT id, ano FROM exercicios")
            orgaos = run_query("SELECT id, nome FROM orgaos")
            programas = run_query("SELECT id, nome FROM programas")
            acoes = run_query("SELECT id, nome FROM acoes")
            naturezas = run_query("SELECT id, codigo || ' - ' || descricao as nome FROM naturezas")
            fontes = run_query("SELECT id, codigo || ' - ' || descricao as nome FROM fontes")

            ex_id = st.selectbox("Exercício", exercicios['id'], format_func=lambda x: str(exercicios[exercicios['id'] == x]['ano'].values[0]))
            org_id = st.selectbox("Órgão", orgaos['id'], format_func=lambda x: orgaos[orgaos['id'] == x]['nome'].values[0])
            prog_id = st.selectbox("Programa", programas['id'], format_func=lambda x: programas[programas['id'] == x]['nome'].values[0])
            ac_id = st.selectbox("Ação", acoes['id'], format_func=lambda x: acoes[acoes['id'] == x]['nome'].values[0])
            nat_id = st.selectbox("Natureza", naturezas['id'], format_func=lambda x: naturezas[naturezas['id'] == x]['nome'].values[0])
            fon_id = st.selectbox("Fonte", fontes['id'], format_func=lambda x: fontes[fontes['id'] == x]['nome'].values[0])
            valor = st.number_input("Valor", min_value=0.0, step=1000.0)

            if st.form_submit_button("Salvar Dotação"):
                run_insert("INSERT INTO dotacoes (exercicio_id, orgao_id, programa_id, acao_id, natureza_id, fonte_id, valor) VALUES (?,?,?,?,?,?,?)",
                           (ex_id, org_id, prog_id, ac_id, nat_id, fon_id, valor))
                st.success("Dotação salva")

            st.markdown("---")
            st.subheader("Receita Prevista")
            fon_id_rec = st.selectbox("Fonte Receita", fontes['id'], format_func=lambda x: fontes[fontes['id'] == x]['nome'].values[0], key="rec_fonte")
            desc_rec = st.text_input("Descrição Receita")
            val_rec = st.number_input("Valor Previsto", min_value=0.0, step=1000.0, key="rec_val")
            if st.form_submit_button("Salvar Receita"):
                run_insert("INSERT INTO receitas (exercicio_id, fonte_id, descricao, valor_previsto, valor_arrecadado) VALUES (?,?,?,?,?)",
                           (ex_id, fon_id_rec, desc_rec, val_rec, 0.0))
                st.success("Receita salva")

    with tab2:
        df = run_query('''
            SELECT d.id, e.ano, o.nome as orgao, p.nome as programa, a.nome as acao, n.codigo as natureza, f.descricao as fonte, d.valor
            FROM dotacoes d
            JOIN exercicios e ON d.exercicio_id = e.id
            JOIN orgaos o ON d.orgao_id = o.id
            JOIN programas p ON d.programa_id = p.id
            JOIN acoes a ON d.acao_id = a.id
            JOIN naturezas n ON d.natureza_id = n.id
            JOIN fontes f ON d.fonte_id = f.id
        ''')
        st.dataframe(df, use_container_width=True)
        st.subheader("Receitas")
        df_rec = run_query("SELECT * FROM receitas")
        st.dataframe(df_rec, use_container_width=True)


def page_pas():
    st.title("📋 PAS - Programação Anual de Saúde")
    tab1, tab2 = st.tabs(["Cadastro", "Consulta"])

    with tab1:
        with st.form("form_pas"):
            ano = st.number_input("Ano", min_value=2000, max_value=2100, value=2026)
            acoes = st.text_area("Ações Programadas")
            indicadores = st.text_area("Indicadores")
            meta = st.text_input("Meta")
            previsao = st.number_input("Previsão Orçamentária", min_value=0.0, step=1000.0)
            status = st.selectbox("Status", ["Planejado", "Em execução", "Concluído", "Suspenso"])
            obs = st.text_area("Observações")
            if st.form_submit_button("Salvar"):
                run_insert("INSERT INTO pas (ano, acoes, indicadores, meta, previsao_orcamentaria, status, observacoes) VALUES (?,?,?,?,?,?,?)",
                           (ano, acoes, indicadores, meta, previsao, status, obs))
                st.success("PAS salvo")

    with tab2:
        df = run_query("SELECT * FROM pas")
        st.dataframe(df, use_container_width=True)


def page_plano_saude():
    st.title("📋 Plano de Saúde")
    tab1, tab2 = st.tabs(["Cadastro", "Consulta"])

    with tab1:
        with st.form("form_plano_saude"):
            periodo = st.text_input("Período (ex: 2026-2029)")
            diretrizes = st.text_area("Diretrizes")
            objetivos = st.text_area("Objetivos")
            metas = st.text_area("Metas")
            populacao = st.number_input("População Estimada", min_value=0, step=100)
            orcamento = st.number_input("Orçamento Previsto", min_value=0.0, step=1000.0)
            if st.form_submit_button("Salvar"):
                run_insert("INSERT INTO plano_saude (periodo, diretrizes, objetivos, metas, populacao_estimada, orcamento_previsto) VALUES (?,?,?,?,?,?)",
                           (periodo, diretrizes, objetivos, metas, populacao, orcamento))
                st.success("Plano de Saúde salvo")

    with tab2:
        df = run_query("SELECT * FROM plano_saude")
        st.dataframe(df, use_container_width=True)


def page_licitacoes():
    st.title("📑 Licitações")
    tab1, tab2 = st.tabs(["Cadastro", "Consulta / Saldo"])

    with tab1:
        with st.form("form_licitacao"):
            numero = st.text_input("Número da Licitação")
            modalidade = st.selectbox("Modalidade", ["Pregão", "Tomada de Preços", "Concorrência", "Dispensa", "Inexigibilidade", "Concurso"])
            objeto = st.text_area("Objeto")
            dotacoes = run_query("SELECT id, valor || ' - ' || programa_id as desc FROM dotacoes")
            dotacao_id = st.selectbox("Dotação Vinculada", dotacoes['id'], format_func=lambda x: str(x)) if not dotacoes.empty else None
            fornecedores = run_query("SELECT id, nome FROM fornecedores")
            fornecedor_id = st.selectbox("Fornecedor Vencedor", fornecedores['id'], format_func=lambda x: fornecedores[fornecedores['id'] == x]['nome'].values[0]) if not fornecedores.empty else None
            valor_total = st.number_input("Valor Total", min_value=0.0, step=1000.0)
            qtd_total = st.number_input("Quantidade Total", min_value=0.0, step=1.0)
            situacao = st.selectbox("Situação", ["Planejada", "Publicada", "Homologada", "Em execução", "Concluída", "Cancelada"])
            alerta = st.slider("Alerta de Retirada (%)", 0, 100, 80)
            if st.form_submit_button("Salvar"):
                run_insert("INSERT INTO licitacoes (numero, modalidade, objeto, dotacao_id, fornecedor_id, valor_total, qtd_total, saldo, situacao, alerta_percentual) VALUES (?,?,?,?,?,?,?,?,?,?)",
                           (numero, modalidade, objeto, dotacao_id, fornecedor_id, valor_total, qtd_total, valor_total, situacao, alerta))
                st.success("Licitação salva")

    with tab2:
        df = run_query('''
            SELECT l.id, l.numero, l.modalidade, l.objeto, l.valor_total, l.qtd_total, l.saldo, l.situacao, l.alerta_percentual, f.nome as fornecedor
            FROM licitacoes l LEFT JOIN fornecedores f ON l.fornecedor_id = f.id
        ''')
        if not df.empty:
            df['perc_utilizado'] = ((df['valor_total'] - df['saldo']) / df['valor_total'] * 100).round(2)
            st.dataframe(df, use_container_width=True)

            for _, row in df.iterrows():
                if row['perc_utilizado'] >= row['alerta_percentual']:
                    st.warning(f"⚠️ Licitação {row['numero']} atingiu {row['perc_utilizado']}% de utilização (alerta: {row['alerta_percentual']}%)")

            st.subheader("Ajustar Alerta")
            lic_id = st.selectbox("Licitação", df['id'], format_func=lambda x: df[df['id'] == x]['numero'].values[0])
            novo_alerta = st.slider("Novo percentual de alerta", 0, 100, 80, key="alerta_lic")
            if st.button("Atualizar Alerta"):
                run_update("UPDATE licitacoes SET alerta_percentual=? WHERE id=?", (novo_alerta, lic_id))
                st.success("Alerta atualizado")
        else:
            st.info("Nenhuma licitação cadastrada")


def page_ordens_compra():
    st.title("📑 Ordens de Compra")
    df_lic = run_query("SELECT id, numero FROM licitacoes")
    df_forn = run_query("SELECT id, nome FROM fornecedores")

    with st.form("form_oc"):
        lic_id = st.selectbox("Licitação", df_lic['id'], format_func=lambda x: df_lic[df_lic['id'] == x]['numero'].values[0]) if not df_lic.empty else None
        forn_id = st.selectbox("Fornecedor", df_forn['id'], format_func=lambda x: df_forn[df_forn['id'] == x]['nome'].values[0]) if not df_forn.empty else None
        numero = st.text_input("Número OC")
        data = st.date_input("Data", value=date.today())
        valor = st.number_input("Valor", min_value=0.0, step=100.0)
        qtd = st.number_input("Quantidade", min_value=0.0, step=1.0)
        desc = st.text_area("Descrição")
        if st.form_submit_button("Salvar OC"):
            lic = run_query("SELECT saldo, valor_total FROM licitacoes WHERE id=?", (lic_id,))
            if not lic.empty and valor <= lic['saldo'].iloc[0]:
                run_insert("INSERT INTO ordens_compra (licitacao_id, fornecedor_id, numero, data, valor, qtd, descricao) VALUES (?,?,?,?,?,?,?)",
                           (lic_id, forn_id, numero, data.isoformat(), valor, qtd, desc))
                novo_saldo = float(lic['saldo'].iloc[0]) - valor
                run_update("UPDATE licitacoes SET saldo=? WHERE id=?", (novo_saldo, lic_id))
                st.success("Ordem de compra salva e saldo atualizado")
            else:
                st.error("Saldo insuficiente na licitação")

    st.subheader("Ordens Cadastradas")
    df = run_query('''
        SELECT oc.id, l.numero as licitacao, oc.numero, oc.data, oc.valor, oc.qtd, f.nome as fornecedor
        FROM ordens_compra oc
        JOIN licitacoes l ON oc.licitacao_id = l.id
        LEFT JOIN fornecedores f ON oc.fornecedor_id = f.id
    ''')
    st.dataframe(df, use_container_width=True)


def page_contratos():
    st.title("📑 Contratos")
    df_forn = run_query("SELECT id, nome FROM fornecedores")
    df_con = run_query('''
        SELECT c.*, f.nome as fornecedor FROM contratos c
        LEFT JOIN fornecedores f ON c.fornecedor_id = f.id
    ''')

    tab1, tab2, tab3 = st.tabs(["Cadastro", "Consulta", "Aditivos"])

    with tab1:
        with st.form("form_contrato"):
            numero = st.text_input("Número Contrato")
            forn_id = st.selectbox("Fornecedor", df_forn['id'], format_func=lambda x: df_forn[df_forn['id'] == x]['nome'].values[0]) if not df_forn.empty else None
            objeto = st.text_area("Objeto")
            valor_inicial = st.number_input("Valor Inicial", min_value=0.0, step=1000.0)
            data_inicio = st.date_input("Data Início", value=date.today())
            data_fim = st.date_input("Data Fim", value=date.today() + timedelta(days=365))
            situacao = st.selectbox("Situação", ["Ativo", "Encerrado", "Suspenso", "Vencido"])
            if st.form_submit_button("Salvar"):
                run_insert("INSERT INTO contratos (numero, fornecedor_id, objeto, valor_inicial, valor_atual, data_inicio, data_fim, situacao) VALUES (?,?,?,?,?,?,?,?)",
                           (numero, forn_id, objeto, valor_inicial, valor_inicial, data_inicio.isoformat(), data_fim.isoformat(), situacao))
                st.success("Contrato salvo")

    with tab2:
        if not df_con.empty:
            st.dataframe(df_con, use_container_width=True)
            for _, row in df_con.iterrows():
                fim = datetime.strptime(row['data_fim'], "%Y-%m-%d").date()
                dias = (fim - date.today()).days
                if dias <= 30 and dias >= 0:
                    st.warning(f"⏰ Contrato {row['numero']} vence em {dias} dias")
                elif dias < 0:
                    st.error(f"⚠️ Contrato {row['numero']} vencido há {abs(dias)} dias")
        else:
            st.info("Nenhum contrato cadastrado")

    with tab3:
        if not df_con.empty:
            con_id = st.selectbox("Contrato", df_con['id'], format_func=lambda x: df_con[df_con['id'] == x]['numero'].values[0])
            tipo = st.selectbox("Tipo Aditivo", ["Prorrogação", "Reajuste", "Acrescimo", "Supressão", "Outro"])
            valor = st.number_input("Valor do Aditivo", step=1000.0)
            data_adit = st.date_input("Data Aditivo", value=date.today())
            desc = st.text_area("Descrição")
            if st.button("Salvar Aditivo"):
                run_insert("INSERT INTO aditivos (contrato_id, tipo, valor, data, descricao) VALUES (?,?,?,?,?)",
                           (con_id, tipo, valor, data_adit.isoformat(), desc))
                contrato = run_query("SELECT valor_atual FROM contratos WHERE id=?", (con_id,))
                if not contrato.empty:
                    novo_valor = float(contrato['valor_atual'].iloc[0]) + valor
                    run_update("UPDATE contratos SET valor_atual=? WHERE id=?", (novo_valor, con_id))
                st.success("Aditivo salvo")
        else:
            st.info("Cadastre contratos primeiro")


def page_fornecedores():
    st.title("👥 Fornecedores")
    tab1, tab2 = st.tabs(["Cadastro", "Consulta"])

    with tab1:
        with st.form("form_fornecedor"):
            tipo = st.selectbox("Tipo", ["Pessoa Física", "Pessoa Jurídica"])
            nome = st.text_input("Nome / Razão Social")
            cpf_cnpj = st.text_input("CPF/CNPJ")
            endereco = st.text_area("Endereço")
            banco = st.text_input("Banco")
            agencia = st.text_input("Agência")
            conta = st.text_input("Conta")
            if st.form_submit_button("Salvar"):
                run_insert("INSERT INTO fornecedores (tipo, nome, cpf_cnpj, endereco, banco, agencia, conta) VALUES (?,?,?,?,?,?,?)",
                           (tipo, nome, cpf_cnpj, endereco, banco, agencia, conta))
                st.success("Fornecedor salvo")

    with tab2:
        df = run_query("SELECT * FROM fornecedores")
        st.dataframe(df, use_container_width=True)


def page_prestadores():
    st.title("👥 Prestadores de Saúde")
    tab1, tab2 = st.tabs(["Cadastro", "Consulta"])

    with tab1:
        with st.form("form_prestador"):
            nome = st.text_input("Nome")
            cnes = st.text_input("CNES")
            tipo = st.selectbox("Tipo", ["Médico", "Enfermeiro", "Dentista", "Laboratório", "Clínica", "Hospital", "Farmácia", "Outro"])
            conselho = st.text_input("Conselho / Registro")
            validade = st.date_input("Validade do Credenciamento", value=date.today() + timedelta(days=180))
            especialidade = st.text_input("Especialidade")
            situacao = st.selectbox("Situação", ["Ativo", "Suspenso", "Cancelado", "Vencido"])
            if st.form_submit_button("Salvar"):
                run_insert("INSERT INTO prestadores (nome, cnes, tipo, conselho, validade, especialidade, situacao) VALUES (?,?,?,?,?,?,?)",
                           (nome, cnes, tipo, conselho, validade.isoformat(), especialidade, situacao))
                st.success("Prestador salvo")

    with tab2:
        df = run_query("SELECT * FROM prestadores")
        st.dataframe(df, use_container_width=True)
        for _, row in df.iterrows():
            try:
                val = datetime.strptime(row['validade'], "%Y-%m-%d").date()
                if (val - date.today()).days <= 30:
                    st.warning(f"⚠️ Credenciamento de {row['nome']} vence em {(val - date.today()).days} dias")
            except:
                pass


def page_pacientes():
    st.title("👥 Pacientes")
    tab1, tab2, tab3 = st.tabs(["Cadastro", "Consulta", "Atendimentos"])

    with tab1:
        with st.form("form_paciente"):
            nome = st.text_input("Nome")
            cpf = st.text_input("CPF")
            nasc = st.date_input("Nascimento", value=date.today())
            sexo = st.selectbox("Sexo", ["Masculino", "Feminino", "Outro"])
            endereco = st.text_area("Endereço")
            telefone = st.text_input("Telefone")
            if st.form_submit_button("Salvar"):
                run_insert("INSERT INTO pacientes (nome, cpf, nascimento, sexo, endereco, telefone) VALUES (?,?,?,?,?,?)",
                           (nome, cpf, nasc.isoformat(), sexo, endereco, telefone))
                st.success("Paciente salvo")

    with tab2:
        df = run_query("SELECT * FROM pacientes")
        st.dataframe(df, use_container_width=True)

    with tab3:
        df_pac = run_query("SELECT id, nome FROM pacientes")
        df_prest = run_query("SELECT id, nome FROM prestadores")
        with st.form("form_atendimento"):
            pac_id = st.selectbox("Paciente", df_pac['id'], format_func=lambda x: df_pac[df_pac['id'] == x]['nome'].values[0]) if not df_pac.empty else None
            data = st.date_input("Data Atendimento", value=date.today())
            tipo = st.selectbox("Tipo", ["Consulta", "Exame", "Procedimento", "Internação", "Emergência"])
            prest_id = st.selectbox("Prestador", df_prest['id'], format_func=lambda x: df_prest[df_prest['id'] == x]['nome'].values[0]) if not df_prest.empty else None
            desc = st.text_area("Descrição")
            if st.form_submit_button("Salvar"):
                run_insert("INSERT INTO atendimentos (paciente_id, data, tipo, prestador_id, descricao) VALUES (?,?,?,?,?)",
                           (pac_id, data.isoformat(), tipo, prest_id, desc))
                st.success("Atendimento salvo")
        st.subheader("Atendimentos Cadastrados")
        df = run_query('''
            SELECT a.id, p.nome as paciente, a.data, a.tipo, pr.nome as prestador, a.descricao
            FROM atendimentos a
            JOIN pacientes p ON a.paciente_id = p.id
            LEFT JOIN prestadores pr ON a.prestador_id = pr.id
        ''')
        st.dataframe(df, use_container_width=True)


def page_renen():
    st.title("👥 RENEN - Relação Nacional de Estabelecimentos de Saúde")
    tab1, tab2 = st.tabs(["Cadastro", "Consulta"])

    with tab1:
        with st.form("form_renen"):
            nome = st.text_input("Nome")
            cnes = st.text_input("CNES")
            tipo = st.text_input("Tipo")
            municipio = st.text_input("Município")
            gestao = st.selectbox("Gestão", ["Municipal", "Estadual", "Federal", "Privada"])
            natureza = st.selectbox("Natureza", ["Público", "Privado", "Filantrópico"])
            situacao = st.selectbox("Situação", ["Ativo", "Inativo", "Suspenso"])
            if st.form_submit_button("Salvar"):
                run_insert("INSERT INTO renen (nome, cnes, tipo, municipio, gestao, natureza, situacao) VALUES (?,?,?,?,?,?,?)",
                           (nome, cnes, tipo, municipio, gestao, natureza, situacao))
                st.success("Estabelecimento salvo")

    with tab2:
        df = run_query("SELECT * FROM renen")
        st.dataframe(df, use_container_width=True)


def page_core_saude():
    st.title("🏥 Core Saúde - Visão Geral Consolidada")
    st.markdown("### Secretaria Municipal de Saúde de Luminárias")

    col1, col2, col3, col4 = st.columns(4)
    df_pacientes = run_query("SELECT COUNT(*) as total FROM pacientes")
    df_prestadores = run_query("SELECT COUNT(*) as total FROM prestadores WHERE situacao='Ativo'")
    df_atendimentos = run_query("SELECT COUNT(*) as total FROM atendimentos")
    df_leitos = run_query("SELECT SUM(total) as total, SUM(ocupados) as ocupados FROM leitos")

    with col1:
        st.metric("Pacientes Cadastrados", int(df_pacientes['total'].iloc[0]))
    with col2:
        st.metric("Prestadores Ativos", int(df_prestadores['total'].iloc[0]))
    with col3:
        st.metric("Atendimentos", int(df_atendimentos['total'].iloc[0]))
    with col4:
        total_leitos = int(df_leitos['total'].iloc[0]) if df_leitos['total'].iloc[0] else 0
        ocupados = int(df_leitos['ocupados'].iloc[0]) if df_leitos['ocupados'].iloc[0] else 0
        taxa = (ocupados / total_leitos * 100) if total_leitos else 0
        st.metric("Taxa Ocupação Leitos", f"{taxa:.1f}%")

    c1, c2 = st.columns(2)
    with c1:
        df_leitos_det = run_query("SELECT tipo, total, ocupados FROM leitos")
        if not df_leitos_det.empty:
            df_leitos_det['taxa'] = (df_leitos_det['ocupados'] / df_leitos_det['total'] * 100).round(1)
            fig = px.bar(df_leitos_det, x='tipo', y='taxa', title='Taxa de Ocupação por Tipo de Leito', text_auto=True)
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        df_prod = run_query("SELECT tipo, SUM(quantidade) as total FROM producao GROUP BY tipo")
        if not df_prod.empty:
            fig = px.pie(df_prod, names='tipo', values='total', title='Produção por Tipo')
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Gestão de Leitos")
    with st.form("form_leitos"):
        estabelecimento = st.text_input("Estabelecimento")
        tipo = st.text_input("Tipo de Leito")
        total = st.number_input("Total Leitos", min_value=0, step=1)
        ocupados = st.number_input("Ocupados", min_value=0, step=1)
        if st.form_submit_button("Salvar Leitos"):
            run_insert("INSERT INTO leitos (estabelecimento, tipo, total, ocupados, data) VALUES (?,?,?,?,?)",
                       (estabelecimento, tipo, total, ocupados, date.today().isoformat()))
            st.success("Leitos salvos")

    st.subheader("Produção Ambulatorial e Hospitalar")
    with st.form("form_producao"):
        tipo_prod = st.selectbox("Tipo", ["Ambulatorial", "Hospitalar", "Exames", "Procedimentos"])
        estab_prod = st.text_input("Estabelecimento")
        qtd = st.number_input("Quantidade", min_value=0, step=1)
        if st.form_submit_button("Salvar Produção"):
            run_insert("INSERT INTO producao (tipo, estabelecimento, quantidade, data) VALUES (?,?,?,?)",
                       (tipo_prod, estab_prod, qtd, date.today().isoformat()))
            st.success("Produção salva")


def page_sistemas_externos():
    st.title("🔗 Sistemas Externos - Links Úteis")

    links = [
        ("E-Gestor AB", "https://egestorab.saude.gov.br", "Sistema de gestão do Ministério da Saúde"),
        ("Investe SUS", "https://investesus.saude.gov.br", "Informações sobre investimentos no SUS"),
        ("DigiSUS", "https://digisus.saude.gov.br", "Plataforma digital do SUS"),
        ("SES Resolve", "#", "Portal estadual de serviços"),
        ("SIGTAP", "http://sigtap.datasus.gov.br", "Tabela de Procedimentos do SUS"),
        ("SES", "#", "Site da Secretaria Estadual de Saúde"),
        ("COSEMS", "https://cosems.org", "Conselho de Secretarias Municipais de Saúde"),
        ("CONASEMS", "https://conasems.org.br", "Conselho Nacional de Secretarias Municipais de Saúde"),
        ("Sistema CIS", "https://www.cislav.com", "Consórcio Intermunicipal de Saúde"),
        ("FNS - Fundo Nacional de Saúde", "https://www.fns.saude.gov.br", "Portal do FNS"),
        ("Consolidação PPI", "#", "Consolidação de Programas e Projetos de Investimentos"),
        ("SEI", "#", "Sistema Eletrônico de Informações"),
        ("Tabela do Consórcio CISLAV", "#", "Tabela de referência do CISLAV")
    ]

    cols = st.columns(3)
    for i, (nome, url, desc) in enumerate(links):
        with cols[i % 3]:
            st.markdown(f"""
                <div style="border:1px solid #ddd; border-radius:10px; padding:15px; margin-bottom:15px; background:#f9f9f9;">
                    <h4>{nome}</h4>
                    <p>{desc}</p>
                    <a href="{url}" target="_blank" style="text-decoration:none;">
                        <button style="background:#0066cc; color:white; border:none; padding:8px 16px; border-radius:5px; cursor:pointer;">Acessar</button>
                    </a>
                </div>
            """, unsafe_allow_html=True)


def page_organograma():
    st.title("📊 Organograma da Secretaria de Saúde")
    st.graphviz_chart('''
    digraph {
        rankdir=TB;
        node [shape=box, style="rounded,filled", color="#0066cc", fontcolor=white];
        "Secretário Municipal de Saúde" -> "Diretoria de Atenção Primária";
        "Secretário Municipal de Saúde" -> "Diretoria de Atenção Hospitalar";
        "Secretário Municipal de Saúde" -> "Diretoria de Vigilância em Saúde";
        "Secretário Municipal de Saúde" -> "Diretoria Administrativo-Financeira";
        "Diretoria de Atenção Primária" -> "Departamento de UBS";
        "Diretoria de Atenção Primária" -> "Departamento de Saúde da Família";
        "Diretoria de Atenção Hospitalar" -> "Departamento de Hospital Municipal";
        "Diretoria de Atenção Hospitalar" -> "Departamento de Regulação";
        "Diretoria de Vigilância em Saúde" -> "Departamento de Epidemiologia";
        "Diretoria de Vigilância em Saúde" -> "Departamento de Inspeção Sanitária";
        "Diretoria Administrativo-Financeira" -> "Departamento de Orçamento";
        "Diretoria Administrativo-Financeira" -> "Departamento de Licitações e Contratos";
        "Diretoria Administrativo-Financeira" -> "Departamento de Recursos Humanos";
        "Departamento de UBS" -> "Setor de Enfermagem";
        "Departamento de UBS" -> "Setor de Medicamentos";
        "Departamento de Orçamento" -> "Setor de Planejamento";
        "Departamento de Licitações e Contratos" -> "Setor de Compras";
    }
    ''')


def page_fluxo_adm():
    st.title("📊 Fluxograma de Demanda Administrativa")
    st.graphviz_chart('''
    digraph {
        rankdir=LR;
        node [shape=box, style="rounded,filled", color="#009900", fontcolor=white];
        "Solicitação" -> "Análise Técnica";
        "Análise Técnica" -> "Aprovação";
        "Aprovação" -> "Execução";
        "Execução" -> "Prestação de Contas";
        "Prestação de Contas" -> "Arquivamento";
    }
    ''')


def page_fluxo_saude():
    st.title("📊 Fluxograma da Saúde")
    st.graphviz_chart('''
    digraph {
        rankdir=LR;
        node [shape=box, style="rounded,filled", color="#cc6600", fontcolor=white];
        "Demanda do Usuário" -> "UBS / Atenção Primária";
        "UBS / Atenção Primária" -> "Referência (Especializada / Hospital)";
        "Referência (Especializada / Hospital)" -> "Contrarreferência (Retorno à UBS)";
        "Contrarreferência (Retorno à UBS)" -> "Acompanhamento na UBS";
    }
    ''')


def page_financeiro():
    st.title("💰 Execução Orçamentária")
    df_dot = run_query("SELECT id, valor || ' - Programa: ' || programa_id as desc FROM dotacoes")
    df_forn = run_query("SELECT id, nome FROM fornecedores")

    tab1, tab2, tab3 = st.tabs(["Empenho", "Liquidação/Pagamento", "Alertas"])

    with tab1:
        with st.form("form_empenho"):
            dot_id = st.selectbox("Dotação", df_dot['id'], format_func=lambda x: df_dot[df_dot['id'] == x]['desc'].values[0]) if not df_dot.empty else None
            numero = st.text_input("Número Empenho")
            data = st.date_input("Data", value=date.today())
            valor = st.number_input("Valor Empenhado", min_value=0.0, step=1000.0)
            forn_id = st.selectbox("Fornecedor", df_forn['id'], format_func=lambda x: df_forn[df_forn['id'] == x]['nome'].values[0]) if not df_forn.empty else None
            desc = st.text_area("Descrição")
            if st.form_submit_button("Salvar Empenho"):
                run_insert("INSERT INTO empenhos (dotacao_id, numero, data, valor_empenhado, valor_liquidado, valor_pago, fornecedor_id, descricao) VALUES (?,?,?,?,?,?,?,?)",
                           (dot_id, numero, data.isoformat(), valor, 0.0, 0.0, forn_id, desc))
                st.success("Empenho salvo")

    with tab2:
        df_emp = run_query("SELECT id, numero FROM empenhos")
        if not df_emp.empty:
            emp_id = st.selectbox("Empenho", df_emp['id'], format_func=lambda x: df_emp[df_emp['id'] == x]['numero'].values[0])
            emp = run_query("SELECT valor_empenhado, valor_liquidado, valor_pago FROM empenhos WHERE id=?", (emp_id,))
            val_emp = float(emp['valor_empenhado'].iloc[0])
            liq_atual = float(emp['valor_liquidado'].iloc[0])
            pag_atual = float(emp['valor_pago'].iloc[0])
            st.write(f"Empenhado: {format_currency(val_emp)} | Liquidado: {format_currency(liq_atual)} | Pago: {format_currency(pag_atual)}")
            novo_liq = st.number_input("Valor a Liquidar", min_value=0.0, max_value=val_emp - liq_atual, step=100.0)
            novo_pag = st.number_input("Valor a Pagar", min_value=0.0, max_value=val_emp - pag_atual, step=100.0)
            if st.button("Atualizar Liquidação/Pagamento"):
                run_update("UPDATE empenhos SET valor_liquidado=valor_liquidado+?, valor_pago=valor_pago+? WHERE id=?", (novo_liq, novo_pag, emp_id))
                st.success("Valores atualizados")
        else:
            st.info("Nenhum empenho cadastrado")

    with tab3:
        st.subheader("Configurar Alertas Financeiros")
        alerta = run_query("SELECT percentual FROM alertas WHERE modulo='financeiro'")
        perc = float(alerta['percentual'].iloc[0]) if not alerta.empty else 80.0
        novo = st.slider("Percentual de alerta para execução orçamentária", 0, 100, int(perc))
        if st.button("Salvar Alerta"):
            run_update("UPDATE alertas SET percentual=? WHERE modulo='financeiro'", (novo,))
            st.success("Alerta atualizado")

    st.subheader("Resumo Financeiro")
    df = run_query('''
        SELECT e.id, e.numero, e.data, e.valor_empenhado, e.valor_liquidado, e.valor_pago, d.valor as dotacao, f.nome as fornecedor
        FROM empenhos e
        JOIN dotacoes d ON e.dotacao_id = d.id
        LEFT JOIN fornecedores f ON e.fornecedor_id = f.id
    ''')
    if not df.empty:
        df['perc_exec'] = ((df['valor_empenhado'] / df['dotacao']) * 100).round(2)
        st.dataframe(df, use_container_width=True)
        alerta = run_query("SELECT percentual FROM alertas WHERE modulo='financeiro'")
        perc = float(alerta['percentual'].iloc[0]) if not alerta.empty else 80.0
        for _, row in df.iterrows():
            if row['perc_exec'] >= perc:
                st.warning(f"⚠️ Empenho {row['numero']} atingiu {row['perc_exec']}% da dotação")
    else:
        st.info("Nenhum empenho cadastrado")


def page_suplementacoes():
    st.title("💰 Suplementações")
    df_dot = run_query("SELECT id, valor || ' - Programa: ' || programa_id as desc FROM dotacoes")

    with st.form("form_suplementacao"):
        dot_id = st.selectbox("Dotação", df_dot['id'], format_func=lambda x: df_dot[df_dot['id'] == x]['desc'].values[0]) if not df_dot.empty else None
        tipo = st.selectbox("Tipo", ["Crédito Especial", "Crédito Suplementar", "Crédito Extraordinário", "Anulação"])
        numero = st.text_input("Número Decreto/Portaria")
        data = st.date_input("Data", value=date.today())
        valor = st.number_input("Valor", min_value=0.0, step=1000.0)
        desc = st.text_area("Descrição / Motivo")
        if st.form_submit_button("Salvar"):
            run_insert("INSERT INTO suplementacoes (dotacao_id, tipo, numero, data, valor, descricao) VALUES (?,?,?,?,?,?)",
                       (dot_id, tipo, numero, data.isoformat(), valor, desc))
            if tipo != "Anulação":
                run_update("UPDATE dotacoes SET valor = valor + ? WHERE id=?", (valor, dot_id))
            else:
                run_update("UPDATE dotacoes SET valor = valor - ? WHERE id=?", (valor, dot_id))
            st.success("Suplementação salva e dotação atualizada")

    st.subheader("Suplementações Cadastradas")
    df = run_query('''
        SELECT s.id, s.tipo, s.numero, s.data, s.valor, s.descricao, d.valor as dotacao
        FROM suplementacoes s
        JOIN dotacoes d ON s.dotacao_id = d.id
    ''')
    st.dataframe(df, use_container_width=True)


def page_exportacao():
    st.title("📈 Exportação de Dados")

    tabelas = ["exercicios", "orgaos", "programas", "acoes", "naturezas", "fontes", "dotacoes", "receitas", "ppa", "ldo", "loa", "pas", "plano_saude",
               "fornecedores", "prestadores", "pacientes", "renen", "licitacoes", "ordens_compra", "contratos", "aditivos", "empenhos", "suplementacoes",
               "leitos", "producao", "atendimentos"]

    tabela = st.selectbox("Selecionar tabela", tabelas)
    data_inicio = st.date_input("Data Início", value=date(2026, 1, 1))
    data_fim = st.date_input("Data Fim", value=date(2026, 12, 31))

    if tabela in ["licitacoes", "ordens_compra", "contratos", "aditivos", "empenhos", "suplementacoes", "leitos", "producao", "atendimentos"]:
        df = run_query(f"SELECT * FROM {tabela} WHERE data BETWEEN ? AND ?", (data_inicio.isoformat(), data_fim.isoformat()))
    else:
        df = run_query(f"SELECT * FROM {tabela}")

    st.dataframe(df, use_container_width=True)

    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", csv, f"{tabela}.csv", "text/csv")


def page_relatorios():
    st.title("📈 Relatórios Consolidados")

    st.subheader("Resumo Orçamentário")
    df_orc = run_query('''
        SELECT e.ano, o.nome as orgao, p.nome as programa, a.nome as acao, f.descricao as fonte, d.valor
        FROM dotacoes d
        JOIN exercicios e ON d.exercicio_id = e.id
        JOIN orgaos o ON d.orgao_id = o.id
        JOIN programas p ON d.programa_id = p.id
        JOIN acoes a ON d.acao_id = a.id
        JOIN fontes f ON d.fonte_id = f.id
    ''')
    if not df_orc.empty:
        st.dataframe(df_orc, use_container_width=True)
        fig = px.sunburst(df_orc, path=['orgao', 'programa', 'acao'], values='valor', title='Distribuição Orçamentária')
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Execução Financeira")
    df_exec = run_query('''
        SELECT p.nome as programa, SUM(e.valor_empenhado) as empenhado, SUM(e.valor_liquidado) as liquidado, SUM(e.valor_pago) as pago
        FROM empenhos e
        JOIN dotacoes d ON e.dotacao_id = d.id
        JOIN programas p ON d.programa_id = p.id
        GROUP BY p.nome
    ''')
    if not df_exec.empty:
        st.dataframe(df_exec, use_container_width=True)
        fig = go.Figure(data=[
            go.Bar(name='Empenhado', x=df_exec['programa'], y=df_exec['empenhado']),
            go.Bar(name='Liquidado', x=df_exec['programa'], y=df_exec['liquidado']),
            go.Bar(name='Pago', x=df_exec['programa'], y=df_exec['pago'])
        ])
        fig.update_layout(barmode='group', title='Execução por Programa')
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# MAIN
# ============================================================

def main():
    st.set_page_config(page_title="MARMED - Gestão em Saúde", layout="wide", initial_sidebar_state="expanded")

    if not os.path.exists(DB_FILE):
        conn = init_db()
        seed_data(conn)
        conn.close()
    else:
        conn = init_db()
        seed_data(conn)
        conn.close()

    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    if not st.session_state['authenticated']:
        login_page()
    else:
        sidebar_navigation()
        page = st.session_state.get('page', 'dashboard')

        if page == 'dashboard':
            page_dashboard()
        elif page == 'ppa':
            page_ppa()
        elif page == 'ldo':
            page_ldo()
        elif page == 'loa':
            page_loa()
        elif page == 'pas':
            page_pas()
        elif page == 'plano_saude':
            page_plano_saude()
        elif page == 'licitacoes':
            page_licitacoes()
        elif page == 'ordens_compra':
            page_ordens_compra()
        elif page == 'contratos':
            page_contratos()
        elif page == 'fornecedores':
            page_fornecedores()
        elif page == 'prestadores':
            page_prestadores()
        elif page == 'pacientes':
            page_pacientes()
        elif page == 'renen':
            page_renen()
        elif page == 'core_saude':
            page_core_saude()
        elif page == 'sistemas_externos':
            page_sistemas_externos()
        elif page == 'organograma':
            page_organograma()
        elif page == 'fluxo_adm':
            page_fluxo_adm()
        elif page == 'fluxo_saude':
            page_fluxo_saude()
        elif page == 'financeiro':
            page_financeiro()
        elif page == 'suplementacoes':
            page_suplementacoes()
        elif page == 'exportacao':
            page_exportacao()
        elif page == 'relatorios':
            page_relatorios()
        else:
            page_dashboard()


if __name__ == "__main__":
    main()
