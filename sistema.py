import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
from datetime import datetime

st.set_page_config(page_title="MARMED - Gestão em Saúde Pública de Luminárias-MG", layout="wide")

DB_PATH = "marmed.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS dotacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            categoria TEXT,
            valor_total REAL,
            valor_usado REAL DEFAULT 0,
            fonte TEXT,
            status TEXT,
            historico TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dotacao_id INTEGER,
            valor REAL,
            data TEXT,
            descricao TEXT,
            FOREIGN KEY (dotacao_id) REFERENCES dotacoes(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS tabelas_auxiliares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            dados TEXT
        )
    ''')
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
              ("admin", hashlib.sha256("admin".encode()).hexdigest()))
    conn.commit()
    conn.close()

init_db()

CATEGORIAS = {
    "REPASSE_FEDERAL": {"nome": "REPASSE FEDERAL", "cor": "#0066cc", "icone": "💰"},
    "REPASSE_ESTADUAL": {"nome": "REPASSE ESTADUAL", "cor": "#009900", "icone": "🟢"},
    "RECURSO_MUNICIPAL": {"nome": "RECURSO MUNICIPAL", "cor": "#cc6600", "icone": "🟠"},
    "TRANSFERENCIA": {"nome": "TRANSFERÊNCIA", "cor": "#6600cc", "icone": "🟣"},
    "TRANSPOSICAO": {"nome": "TRANSPOSIÇÃO", "cor": "#cc0000", "icone": "🔴"}
}

TABELAS_CORE = [
    "PPA", "LDO", "LOA", "PAS", "Plano Saúde", "Licitações", "Ordens Compra", "Contratos",
    "Fornecedores", "Prestadores", "Pacientes", "RENEN", "RENASES", "RENAME", "REMUME"
]

TABELAS_SUS = ["RENEN", "RENASES", "RENAME", "REMUME"]

CORE_SAUDE = ["Atendimento Médico", "Atendimento de Enfermagem", "Vacinação", "Saúde Bucal", "Atenção Básica"]

LINKS_UTEIS = {
    "SIA/SUS": "https://sia.saude.gov.br",
    "SIAB": "https://siab.saude.gov.br",
    "SIGTAP": "https://sigtap.saude.gov.br",
    "CNES": "http://cnes.datasus.gov.br",
    "IBGE": "https://www.ibge.gov.br"
}

ORGANOGRAMA = [
    "Secretaria Municipal de Saúde",
    "  └── Diretoria de Atenção Básica",
    "  └── Diretoria de Saúde Ambulatorial e Hospitalar",
    "  └── Diretoria de Vigilância em Saúde",
    "  └── Diretoria de Assistência Farmacêutica",
    "  └── Diretoria de Planejamento e Gestão"
]

FLUXOS = ["Entrada do Paciente", "Marcacao de Consulta", "Dispensação de Medicamentos", "Regulação", "Alta Hospitalar"]

SISTEMAS_EXTERNOS = ["e-Gestão AB", "SIA/SUS", "SIAB", "SIGTAP", "CNES", "SISVAN", "NOTIVISA"]


def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def check_login(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hash_pw(password)))
    user = c.fetchone()
    conn.close()
    return user is not None


def listar_dotacoes(filtro_categoria=None):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM dotacoes"
    params = []
    if filtro_categoria:
        query += " WHERE categoria=?"
        params.append(filtro_categoria)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def criar_dotacao(nome, categoria, valor_total, fonte, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO dotacoes (nome, categoria, valor_total, valor_usado, fonte, status, historico) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (nome, categoria, valor_total, 0, fonte, status, ""))
    conn.commit()
    conn.close()


def incluir_valor_dotacao(dotacao_id, valor, descricao):
    if valor <= 0:
        return False
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT valor_total, valor_usado, historico FROM dotacoes WHERE id=?", (dotacao_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return False
    valor_total, valor_usado, historico = row
    novo_usado = valor_usado + valor
    if novo_usado > valor_total:
        conn.close()
        return False
    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    nova_linha = f"{data_hora} - R$ {valor:,.2f} - {descricao}\n"
    c.execute("UPDATE dotacoes SET valor_usado=?, historico=? WHERE id=?",
              (novo_usado, historico + nova_linha, dotacao_id))
    c.execute("INSERT INTO movimentacoes (dotacao_id, valor, data, descricao) VALUES (?, ?, ?, ?)",
              (dotacao_id, valor, data_hora, descricao))
    conn.commit()
    conn.close()
    return True


def get_resumo_categoria(categoria):
    df = listar_dotacoes(categoria)
    total = df["valor_total"].sum() if not df.empty else 0
    usado = df["valor_usado"].sum() if not df.empty else 0
    qtd = len(df)
    perc = (usado / total * 100) if total > 0 else 0
    return total, usado, perc, qtd


# Login
if "logado" not in st.session_state:
    st.session_state.logado = False
if "filtro_categoria" not in st.session_state:
    st.session_state.filtro_categoria = None

if not st.session_state.logado:
    st.title("MARMED - Gestão em Saúde Pública de Luminárias-MG")
    st.subheader("Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if check_login(username, password):
            st.session_state.logado = True
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")
    st.stop()

# Sidebar
st.sidebar.title("MARMED - Luminárias-MG")
st.sidebar.write(f"Usuário: admin")
if st.sidebar.button("Sair"):
    st.session_state.logado = False
    st.rerun()

menu = st.sidebar.radio("Menu", [
    "INÍCIO", "PLANEJAMENTO", "LICITAÇÕES", "CADASTROS", "TABELAS SUS", "CORE SAÚDE",
    "SISTEMAS EXTERNOS", "ORGANOGRAMA", "FINANCEIRO", "RELATÓRIOS"
])

# Menu expanders
with st.sidebar.expander("INÍCIO"):
    st.write("Dashboard, resumo financeiro e contas.")
with st.sidebar.expander("PLANEJAMENTO"):
    st.write("PPA, LDO, LOA, PAS, Plano Saúde.")
with st.sidebar.expander("LICITAÇÕES"):
    st.write("Licitações, Ordens de Compra, Contratos.")
with st.sidebar.expander("CADASTROS"):
    st.write("Fornecedores, Prestadores, Pacientes.")
with st.sidebar.expander("TABELAS SUS"):
    st.write("RENEN, RENASES, RENAME, REMUME.")
with st.sidebar.expander("CORE SAÚDE"):
    st.write("Atendimentos, Atenção Básica, Vigilância.")
with st.sidebar.expander("SISTEMAS EXTERNOS"):
    for nome, url in LINKS_UTEIS.items():
        st.markdown(f"- [{nome}]({url})")
with st.sidebar.expander("ORGANOGRAMA"):
    for linha in ORGANOGRAMA:
        st.write(linha)
with st.sidebar.expander("FINANCEIRO"):
    st.write("Execução Financeira, Suplementações, Cadastrar Nova Conta.")
with st.sidebar.expander("RELATÓRIOS"):
    st.write("Exportações e relatórios consolidados.")


if menu == "INÍCIO":
    st.title("Dashboard - MARMED Luminárias-MG")
    st.markdown("### Blocos de Fontes de Recursos")

    cols = st.columns(5)
    for idx, (cat_key, cat_info) in enumerate(CATEGORIAS.items()):
        total, usado, perc, qtd = get_resumo_categoria(cat_key)
        with cols[idx]:
            st.markdown(f"""
                <div style="background-color:{cat_info['cor']};padding:15px;border-radius:12px;color:white;text-align:center;margin-bottom:10px;">
                    <div style="font-size:40px;">{cat_info['icone']}</div>
                    <h4 style="margin:5px 0;">{cat_info['nome']}</h4>
                    <h3 style="margin:5px 0;">R$ {total:,.2f}</h3>
                    <p style="margin:2px 0;">Usado: R$ {usado:,.2f} ({perc:.1f}%)</p>
                    <progress value="{perc}" max="100" style="width:100%;"></progress>
                    <p style="margin:2px 0;">{qtd} conta(s)/dotação(ões)</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Ver Contas", key=f"btn_{cat_key}"):
                st.session_state.filtro_categoria = cat_key
                st.rerun()

    st.markdown("---")
    st.markdown("### Área de Contas / Dotações")

    if st.session_state.filtro_categoria:
        cat_info = CATEGORIAS[st.session_state.filtro_categoria]
        st.markdown(f"**Filtrando por:** {cat_info['nome']} {cat_info['icone']}")
        if st.button("Limpar Filtro"):
            st.session_state.filtro_categoria = None
            st.rerun()

    df = listar_dotacoes(st.session_state.filtro_categoria)
    if df.empty:
        st.info("Nenhuma dotação cadastrada para este filtro.")
    else:
        cards_cols = st.columns(3)
        for i, row in df.iterrows():
            with cards_cols[i % 3]:
                perc = (row["valor_usado"] / row["valor_total"] * 100) if row["valor_total"] > 0 else 0
                st.markdown(f"""
                    <div style="border:1px solid #ddd;border-radius:10px;padding:15px;margin-bottom:10px;background-color:#fafafa;">
                        <h4>{row['nome']}</h4>
                        <p><strong>Categoria:</strong> {CATEGORIAS.get(row['categoria'], {}).get('nome', row['categoria'])}</p>
                        <p><strong>Valor:</strong> R$ {row['valor_total']:,.2f}</p>
                        <p><strong>Usado:</strong> R$ {row['valor_usado']:,.2f} ({perc:.1f}%)</p>
                        <progress value="{perc}" max="100" style="width:100%;"></progress>
                        <p><strong>Fonte:</strong> {row['fonte']}</p>
                        <p><strong>Status:</strong> {row['status']}</p>
                    </div>
                """, unsafe_allow_html=True)
                with st.expander("Incluir Valor", expanded=False):
                    with st.form(key=f"form_incluir_{row['id']}"):
                        valor_add = st.number_input("Valor a incluir (R$)", min_value=0.01, step=0.01, key=f"val_{row['id']}")
                        desc_add = st.text_input("Descrição", key=f"desc_{row['id']}")
                        submit_add = st.form_submit_button("Confirmar Inclusão")
                        if submit_add:
                            ok = incluir_valor_dotacao(row["id"], valor_add, desc_add)
                            if ok:
                                st.success("Valor incluído com sucesso!")
                                st.rerun()
                            else:
                                st.error("Erro: valor inválido ou execede o limite da dotação.")
                with st.expander("Histórico"):
                    st.text(row["historico"] if row["historico"] else "Sem movimentações")

elif menu == "PLANEJAMENTO":
    st.title("Planejamento")
    tabs = st.tabs(["PPA", "LDO", "LOA", "PAS", "Plano Saúde"])
    for i, nome in enumerate(["PPA", "LDO", "LOA", "PAS", "Plano Saúde"]):
        with tabs[i]:
            st.subheader(nome)
            st.write(f"Gerencie os dados de {nome} do município.")
            arquivo = st.file_uploader(f"Importar {nome}", type=["csv", "xlsx"], key=f"up_{nome}")
            if arquivo:
                st.success(f"Arquivo {nome} carregado para processamento.")
            st.text_area(f"Observações {nome}", key=f"obs_{nome}")
            if st.button(f"Salvar {nome}", key=f"save_{nome}"):
                st.success(f"{nome} salvo.")

elif menu == "LICITAÇÕES":
    st.title("Licitações e Contratos")
    tabs = st.tabs(["Licitações", "Ordens de Compra", "Contratos"])
    with tabs[0]:
        st.subheader("Licitações")
        col1, col2, col3 = st.columns(3)
        with col1:
            num = st.text_input("Número da Licitação")
        with col2:
            modalidade = st.selectbox("Modalidade", ["Pregão", "Concorrência", "Convite", "Tomada de Preços", "Dispensa"])
        with col3:
            valor = st.number_input("Valor Estimado", min_value=0.0, step=0.01)
        if st.button("Salvar Licitação"):
            st.success("Licitação salva.")
    with tabs[1]:
        st.subheader("Ordens de Compra")
        st.text_input("Número OC")
        st.selectbox("Fornecedor", ["Fornecedor A", "Fornecedor B", "Fornecedor C"])
        st.number_input("Valor OC", min_value=0.0, step=0.01)
        if st.button("Salvar OC"):
            st.success("Ordem de Compra salva.")
    with tabs[2]:
        st.subheader("Contratos")
        st.text_input("Número do Contrato")
        st.date_input("Data Início")
        st.date_input("Data Fim")
        if st.button("Salvar Contrato"):
            st.success("Contrato salvo.")

elif menu == "CADASTROS":
    st.title("Cadastros")
    tabs = st.tabs(["Fornecedores", "Prestadores", "Pacientes"])
    with tabs[0]:
        st.subheader("Fornecedores")
        st.text_input("Razão Social")
        st.text_input("CNPJ")
        if st.button("Salvar Fornecedor"):
            st.success("Fornecedor salvo.")
    with tabs[1]:
        st.subheader("Prestadores")
        st.text_input("Nome do Prestador")
        st.selectbox("Categoria Profissional", ["Médico", "Enfermeiro", "Dentista", "Farmacêutico", "Técnico"])
        if st.button("Salvar Prestador"):
            st.success("Prestador salvo.")
    with tabs[2]:
        st.subheader("Pacientes")
        st.text_input("Nome do Paciente")
        st.date_input("Data de Nascimento")
        if st.button("Salvar Paciente"):
            st.success("Paciente salvo.")

elif menu == "TABELAS SUS":
    st.title("Tabelas SUS")
    tabs = st.tabs(TABELAS_SUS)
    for i, nome in enumerate(TABELAS_SUS):
        with tabs[i]:
            st.subheader(nome)
            st.write(f"Dados e importação da tabela {nome}.")
            st.file_uploader(f"Importar {nome}", key=f"sus_up_{nome}")
            st.text_area(f"Registros {nome}", key=f"sus_txt_{nome}")
            if st.button(f"Salvar {nome}", key=f"sus_save_{nome}"):
                st.success(f"{nome} salvo.")

elif menu == "CORE SAÚDE":
    st.title("Core Saúde")
    st.subheader("Áreas de Atenção e Serviços")
    for area in CORE_SAUDE:
        with st.expander(area):
            st.write(f"Detalhamento e indicadores de {area}.")
            st.metric("Atendimentos no Mês", 0)
            st.metric("Meta", 0)
            st.progress(0)

elif menu == "SISTEMAS EXTERNOS":
    st.title("Sistemas Externos e Links Úteis")
    for nome, url in LINKS_UTEIS.items():
        st.markdown(f"- [{nome}]({url})")
    st.subheader("Outros Sistemas")
    for sis in SISTEMAS_EXTERNOS:
        st.write(f"- {sis}")

elif menu == "ORGANOGRAMA":
    st.title("Organograma e Fluxos")
    tabs = st.tabs(["Organograma", "Fluxos"])
    with tabs[0]:
        st.subheader("Organograma da Secretaria de Saúde")
        for linha in ORGANOGRAMA:
            st.write(linha)
    with tabs[1]:
        st.subheader("Fluxos de Processos")
        for fluxo in FLUXOS:
            with st.expander(fluxo):
                st.write(f"Descrição do fluxo: {fluxo}")

elif menu == "FINANCEIRO":
    st.title("Financeiro")
    tabs = st.tabs(["Execução Financeira", "Suplementações", "Cadastrar Nova Conta"])
    with tabs[0]:
        st.subheader("Execução Financeira")
        st.write("Acompanhamento de empenhos, liquidações e pagamentos.")
        st.bar_chart({"Empenhado": [100000], "Liquidado": [80000], "Pago": [70000]})
    with tabs[1]:
        st.subheader("Suplementações")
        st.selectbox("Dotação", ["Dotação 1", "Dotação 2"])
        st.number_input("Valor Suplementado", min_value=0.0, step=0.01)
        if st.button("Salvar Suplementação"):
            st.success("Suplementação salva.")
    with tabs[2]:
        st.subheader("Cadastrar Nova Conta / Dotação")
        with st.form("form_nova_conta"):
            nome = st.text_input("Nome da Conta / Dotação")
            categoria = st.selectbox("Categoria", list(CATEGORIAS.keys()), format_func=lambda x: CATEGORIAS[x]["nome"])
            valor_total = st.number_input("Valor Total (R$)", min_value=0.01, step=0.01)
            fonte = st.selectbox("Fonte", ["Federal", "Estadual", "Municipal", "Transferência", "Transposição", "Outra"])
            status = st.selectbox("Status", ["Ativa", "Inativa", "Suspensa", "Encerrada"])
            submitted = st.form_submit_button("Cadastrar Conta")
            if submitted:
                if nome and valor_total > 0:
                    criar_dotacao(nome, categoria, valor_total, fonte, status)
                    st.success("Conta cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.error("Preencha nome e valor válido.")

elif menu == "RELATÓRIOS":
    st.title("Relatórios e Exportações")
    st.subheader("Relatórios Consolidados")
    if st.button("Gerar Relatório Financeiro Consolidado"):
        df = listar_dotacoes()
        if not df.empty:
            st.dataframe(df)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Exportar CSV", data=csv, file_name="relatorio_dotacoes.csv", mime="text/csv")
        else:
            st.warning("Nenhuma dotação para exportar.")
    st.markdown("### Resumo por Categoria")
    resumo = []
    for cat_key, cat_info in CATEGORIAS.items():
        total, usado, perc, qtd = get_resumo_categoria(cat_key)
        resumo.append({
            "Categoria": cat_info["nome"],
            "Total": total,
            "Usado": usado,
            "Saldo": total - usado,
            "Quantidade": qtd
        })
    df_resumo = pd.DataFrame(resumo)
    st.dataframe(df_resumo)
    if not df_resumo.empty:
        csv_resumo = df_resumo.to_csv(index=False).encode("utf-8")
        st.download_button("Exportar Resumo CSV", data=csv_resumo, file_name="resumo_categorias.csv", mime="text/csv")
