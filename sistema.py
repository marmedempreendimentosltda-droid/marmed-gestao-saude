import streamlit as st
import datetime
import re
import pandas as pd
import io

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="MARMED - Sistema de Gestão",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CSS CUSTOMIZADO - CORES FORTES E VIBRANTES
# =============================================================================
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: #0f172a;
            color: #cbd5e1;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #f8fafc !important;
            font-weight: 800 !important;
        }

        p, li, span, div, label {
            color: #cbd5e1;
        }

        .stMetric {
            background-color: rgba(30, 41, 59, 0.85);
            border: 1px solid rgba(34, 211, 238, 0.25);
            border-radius: 12px;
            padding: 16px;
        }

        .stMetric > div:nth-child(1) {
            color: #22d3ee !important;
            font-weight: 700 !important;
        }

        .stMetric > div:nth-child(2) {
            color: #f8fafc !important;
            font-weight: 800 !important;
        }

        .stDataFrame {
            border: 1px solid rgba(34, 211, 238, 0.25);
            border-radius: 10px;
        }

        .stButton > button {
            background: linear-gradient(135deg, #0ea5e9 0%, #22d3ee 100%);
            color: #0f172a;
            font-weight: 800 !important;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            transition: all 0.2s ease-in-out;
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(34, 211, 238, 0.35);
        }

        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > div,
        .stNumberInput > div > div > input,
        .stDateInput > div > div > input {
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border: 1px solid rgba(34, 211, 238, 0.4) !important;
            border-radius: 8px !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            background-color: #1e293b;
            color: #22d3ee;
            border-radius: 8px 8px 0 0;
            font-weight: 700;
            border: 1px solid rgba(34, 211, 238, 0.25);
        }

        .stTabs [aria-selected="true"] {
            background-color: #0ea5e9 !important;
            color: #0f172a !important;
        }

        .css-1d39120, .css-1avcm0n, .css-12oz5g7 {
            background-color: #0f172a;
        }

        .info-card {
            background-color: rgba(30, 41, 59, 0.9);
            border: 1px solid rgba(34, 211, 238, 0.25);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
        }

        .label-destaque {
            color: #22d3ee;
            font-weight: 700;
        }

        .valor-destaque {
            color: #38bdf8;
            font-weight: 800;
        }

        .dado-destaque {
            color: #f8fafc;
            font-weight: 700;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# =============================================================================
# ESTADO INICIAL
# =============================================================================
def inicializar_estado():
    defaults = {
        "authenticated": False,
        "usuario": None,
        "contas": [],
        "compras": [],
        "programas": [],
        "planos": [],
        "nortes": [],
        "documentos": [],
        "id_conta": 1,
        "id_compra": 1,
        "id_programa": 1,
        "id_plano": 1,
        "id_norte": 1,
        "id_documento": 1,
        "compra_submetida": False,
    }
    for chave, valor in defaults.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor

inicializar_estado()

ESFERAS = ["Federal", "Estadual", "Municipal"]
STATUS_COMPRA = ["Solicitada", "Aprovada", "Reprovada", "Paga", "Recebida"]

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================
def formatar_moeda(valor: float) -> str:
    """Formata um número float como moeda brasileira."""
    if valor is None:
        valor = 0.0
    texto = f"R$ {valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def parse_moeda(texto: str) -> float:
    """Converte texto em formato moeda brasileiro para float."""
    if not texto:
        return 0.0
    limpo = texto.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return 0.0


def mascara_moeda_input(label: str, chave: str, valor_inicial: str = "") -> str:
    """Input de texto com formatação ao digitar (ativa em on_change)."""
    def _on_change():
        raw = st.session_state.get(chave, "")
        numerico = re.sub(r"[^\d,]", "", raw.replace(".", ","))
        if numerico.count(",") > 1:
            partes = numerico.split(",")
            numerico = partes[0] + "," + "".join(partes[1:])
        try:
            if numerico:
                # Força duas casas decimais caso o usuário tenha digitado centavos
                if "," in numerico:
                    inteiros, decimais = numerico.split(",")
                    decimais = (decimais + "00")[:2]
                else:
                    inteiros = numerico
                    decimais = "00"
                valor = float(f"{inteiros}.{decimais}")
                st.session_state[chave] = formatar_moeda(valor)
            else:
                st.session_state[chave] = ""
        except ValueError:
            pass

    return st.text_input(label, value=valor_inicial, key=chave, on_change=_on_change)


def novo_id(tipo: str) -> int:
    chave = f"id_{tipo}"
    st.session_state[chave] += 1
    return st.session_state[chave] - 1


def contas_por_esfera(esfera: str) -> list:
    return [c for c in st.session_state.contas if c["esfera"] == esfera]


def compras_por_esfera(esfera: str) -> list:
    return [c for c in st.session_state.compras if c["esfera"] == esfera]


def total_contas(esfera: str) -> float:
    return sum(c["valor"] for c in contas_por_esfera(esfera))


def total_compras(esfera: str) -> float:
    return sum(c["valor"] for c in compras_por_esfera(esfera))


def superavit(esfera: str) -> float:
    return total_contas(esfera) - total_compras(esfera)


def conta_por_id(identificador: int) -> dict:
    for c in st.session_state.contas:
        if c["id"] == identificador:
            return c
    return None


def compra_por_id(identificador: int) -> dict:
    for c in st.session_state.compras:
        if c["id"] == identificador:
            return c
    return None


# =============================================================================
# LOGIN
# =============================================================================
def tela_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>🏥 MARMED</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #22d3ee; font-weight: 700;'>Sistema de Gestão para Saúde</p>", unsafe_allow_html=True)
        with st.form("login_form"):
            usuario = st.text_input("Usuário", key="login_user")
            senha = st.text_input("Senha", type="password", key="login_pass")
            submitted = st.form_submit_button("Entrar", use_container_width=True)
            if submitted:
                if usuario == "admin" and senha == "Diretor2025#":
                    st.session_state.authenticated = True
                    st.session_state.usuario = usuario
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")


# =============================================================================
# DASHBOARD
# =============================================================================
def dashboard():
    st.markdown("<h1>Dashboard</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #22d3ee; font-weight: 700;'>Bem-vindo, {st.session_state.usuario}!</p>", unsafe_allow_html=True)

    cols = st.columns(3)
    for i, esfera in enumerate(ESFERAS):
        with cols[i]:
            st.markdown(f"<h3 style='text-align: center; color: #22d3ee;'>{esfera}</h3>", unsafe_allow_html=True)
            tc = total_contas(esfera)
            tcm = total_compras(esfera)
            sup = superavit(esfera)
            st.metric(label="Total em Contas", value=formatar_moeda(tc))
            st.metric(label="Total em Compras", value=formatar_moeda(tcm))
            cor_sup = "#38bdf8" if sup >= 0 else "#f87171"
            st.markdown(
                f"<div style='text-align: center;'><span class='label-destaque'>Superávit:</span> "
                f"<span style='color: {cor_sup}; font-weight: 800;'>{formatar_moeda(sup)}</span></div>",
                unsafe_allow_html=True
            )

    st.divider()

    st.markdown("<h2>Resumo Geral</h2>", unsafe_allow_html=True)
    total_geral_contas = sum(total_contas(e) for e in ESFERAS)
    total_geral_compras = sum(total_compras(e) for e in ESFERAS)
    total_geral_superavit = total_geral_contas - total_geral_compras

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Geral em Contas", formatar_moeda(total_geral_contas))
    c2.metric("Total Geral em Compras", formatar_moeda(total_geral_compras))
    c3.metric("Superávit Geral", formatar_moeda(total_geral_superavit))

    st.divider()

    st.markdown("<h2>Últimas Compras Solicitadas</h2>", unsafe_allow_html=True)
    if st.session_state.compras:
        df = pd.DataFrame(st.session_state.compras[-10:])
        df["valor"] = df["valor"].apply(formatar_moeda)
        df = df[["id", "esfera", "conta", "descricao", "fornecedor", "valor", "data", "status"]]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma compra solicitada até o momento.")


# =============================================================================
# CONTAS
# =============================================================================
def aba_cadastrar_contas():
    st.markdown("<h2>Cadastrar Conta</h2>", unsafe_allow_html=True)
    with st.form("form_conta", clear_on_submit=True):
        esfera = st.selectbox("Esfera *", ESFERAS, key="conta_esfera")
        nome = st.text_input("Nome da Conta / Fonte de Recurso *", key="conta_nome")
        valor = mascara_moeda_input("Valor Total *", "conta_valor")
        data_recebimento = st.date_input("Data de Recebimento / Vigência *", value=datetime.date.today(), format="DD/MM/YYYY", key="conta_data")
        responsavel = st.text_input("Responsável", key="conta_responsavel")
        observacao = st.text_area("Observação", key="conta_obs")
        submitted = st.form_submit_button("Salvar Conta", use_container_width=True)

        if submitted:
            if not nome.strip():
                st.error("O nome da conta é obrigatório.")
            else:
                v = parse_moeda(valor)
                nova_conta = {
                    "id": novo_id("conta"),
                    "esfera": esfera,
                    "nome": nome.strip(),
                    "valor": v,
                    "data": data_recebimento.strftime("%d/%m/%Y"),
                    "responsavel": responsavel.strip(),
                    "observacao": observacao.strip()
                }
                st.session_state.contas.append(nova_conta)
                st.success("Conta cadastrada com sucesso!")
                st.rerun()


def aba_listar_contas():
    st.markdown("<h2>Contas Cadastradas</h2>", unsafe_allow_html=True)
    tabs = st.tabs(ESFERAS)
    for idx, esfera in enumerate(ESFERAS):
        with tabs[idx]:
            contas = contas_por_esfera(esfera)
            if not contas:
                st.info(f"Nenhuma conta cadastrada na esfera {esfera}.")
            else:
                total = total_contas(esfera)
                st.markdown(
                    f"<p><span class='label-destaque'>Total {esfera}:</span> "
                    f"<span class='valor-destaque'>{formatar_moeda(total)}</span></p>",
                    unsafe_allow_html=True
                )
                for conta in contas:
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(
                                f"<p><span class='label-destaque'>ID:</span> <span class='dado-destaque'>{conta['id']}</span> | "
                                f"<span class='label-destaque'>Conta:</span> <span class='dado-destaque'>{conta['nome']}</span></p>"
                                f"<p><span class='label-destaque'>Valor:</span> <span class='valor-destaque'>{formatar_moeda(conta['valor'])}</span> | "
                                f"<span class='label-destaque'>Data:</span> <span class='dado-destaque'>{conta['data']}</span></p>"
                                f"<p><span class='label-destaque'>Responsável:</span> <span class='dado-destaque'>{conta['responsavel']}</span></p>",
                                unsafe_allow_html=True
                            )
                            if conta["observacao"]:
                                st.markdown(f"<p><span class='label-destaque'>Obs:</span> {conta['observacao']}</p>", unsafe_allow_html=True)
                        with c2:
                            if st.button("Editar", key=f"edit_conta_{conta['id']}", use_container_width=True):
                                st.session_state.edit_conta_id = conta["id"]
                                st.rerun()
                            if st.button("Excluir", key=f"del_conta_{conta['id']}", use_container_width=True):
                                st.session_state.contas = [c for c in st.session_state.contas if c["id"] != conta["id"]]
                                st.session_state.compras = [c for c in st.session_state.compras if c["conta_id"] != conta["id"]]
                                st.success("Conta excluída.")
                                st.rerun()


def aba_editar_contas():
    if "edit_conta_id" not in st.session_state or st.session_state.edit_conta_id is None:
        st.info("Selecione uma conta para editar na aba 'Contas Cadastradas'.")
        return

    conta = conta_por_id(st.session_state.edit_conta_id)
    if not conta:
        st.error("Conta não encontrada.")
        st.session_state.edit_conta_id = None
        return

    st.markdown("<h2>Editar Conta</h2>", unsafe_allow_html=True)
    with st.form("form_editar_conta"):
        esfera = st.selectbox("Esfera *", ESFERAS, index=ESFERAS.index(conta["esfera"]), key="edit_conta_esfera")
        nome = st.text_input("Nome da Conta / Fonte de Recurso *", value=conta["nome"], key="edit_conta_nome")
        valor_str = mascara_moeda_input("Valor Total *", "edit_conta_valor", valor_inicial=formatar_moeda(conta["valor"]))
        data_obj = datetime.datetime.strptime(conta["data"], "%d/%m/%Y").date()
        data_recebimento = st.date_input("Data de Recebimento / Vigência *", value=data_obj, format="DD/MM/YYYY", key="edit_conta_data")
        responsavel = st.text_input("Responsável", value=conta["responsavel"], key="edit_conta_responsavel")
        observacao = st.text_area("Observação", value=conta["observacao"], key="edit_conta_obs")

        c1, c2 = st.columns(2)
        with c1:
            salvar = st.form_submit_button("Salvar Alterações", use_container_width=True)
        with c2:
            cancelar = st.form_submit_button("Cancelar", use_container_width=True)

        if salvar:
            if not nome.strip():
                st.error("O nome da conta é obrigatório.")
            else:
                conta["esfera"] = esfera
                conta["nome"] = nome.strip()
                conta["valor"] = parse_moeda(valor_str)
                conta["data"] = data_recebimento.strftime("%d/%m/%Y")
                conta["responsavel"] = responsavel.strip()
                conta["observacao"] = observacao.strip()
                st.session_state.edit_conta_id = None
                st.success("Conta atualizada com sucesso!")
                st.rerun()
        if cancelar:
            st.session_state.edit_conta_id = None
            st.rerun()


def tela_contas():
    st.markdown("<h1>Gestão de Contas</h1>", unsafe_allow_html=True)
    aba_cad, aba_list, aba_edit = st.tabs(["Cadastrar Conta", "Contas Cadastradas", "Editar Conta"])
    with aba_cad:
        aba_cadastrar_contas()
    with aba_list:
        aba_listar_contas()
    with aba_edit:
        aba_editar_contas()


# =============================================================================
# COMPRAS
# =============================================================================
def tela_compras():
    st.markdown("<h1>Solicitação de Compras</h1>", unsafe_allow_html=True)

    aba_solicitar, aba_solicitacoes = st.tabs(["Solicitar Compra", "Solicitações Cadastradas"])

    with aba_solicitar:
        st.markdown("<h2>Nova Solicitação de Compra</h2>", unsafe_allow_html=True)
        with st.form("form_compra", clear_on_submit=True):
            esfera = st.selectbox("Esfera *", ESFERAS, key="compra_esfera")
            contas_disponiveis = contas_por_esfera(esfera)
            conta_nomes = [c["nome"] for c in contas_disponiveis]
            conta_selecionada = st.selectbox(
                "Conta Vinculada *",
                conta_nomes if conta_nomes else ["Nenhuma conta disponível"],
                key="compra_conta"
            )
            descricao = st.text_area("Descrição do Item / Serviço *", key="compra_descricao")
            fornecedor = st.text_input("Fornecedor", key="compra_fornecedor")
            valor = mascara_moeda_input("Valor Estimado *", "compra_valor")
            data_compra = st.date_input("Data da Solicitação *", value=datetime.date.today(), format="DD/MM/YYYY", key="compra_data")
            solicitante = st.text_input("Solicitante *", key="compra_solicitante")

            submitted = st.form_submit_button("Solicitar", use_container_width=True)
            if submitted:
                if not contas_disponiveis:
                    st.error("Não há contas cadastradas para esta esfera. Cadastre uma conta primeiro.")
                elif not descricao.strip() or not solicitante.strip():
                    st.error("Descrição e solicitante são obrigatórios.")
                else:
                    conta_id = next((c["id"] for c in contas_disponiveis if c["nome"] == conta_selecionada), None)
                    nova_compra = {
                        "id": novo_id("compra"),
                        "esfera": esfera,
                        "conta_id": conta_id,
                        "conta": conta_selecionada,
                        "descricao": descricao.strip(),
                        "fornecedor": fornecedor.strip(),
                        "valor": parse_moeda(valor),
                        "data": data_compra.strftime("%d/%m/%Y"),
                        "solicitante": solicitante.strip(),
                        "status": "Solicitada"
                    }
                    st.session_state.compras.append(nova_compra)
                    st.success("Compra solicitada com sucesso!")
                    st.rerun()

    with aba_solicitacoes:
        st.markdown("<h2>Solicitações Cadastradas</h2>", unsafe_allow_html=True)
        esfera_filtro = st.selectbox("Filtrar por Esfera", ["Todas"] + ESFERAS, key="filtro_compras_esfera")
        compras = st.session_state.compras
        if esfera_filtro != "Todas":
            compras = [c for c in compras if c["esfera"] == esfera_filtro]

        if not compras:
            st.info("Nenhuma solicitação encontrada.")
        else:
            for compra in compras:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(
                            f"<p><span class='label-destaque'>ID:</span> <span class='dado-destaque'>{compra['id']}</span> | "
                            f"<span class='label-destaque'>Esfera:</span> <span class='dado-destaque'>{compra['esfera']}</span> | "
                            f"<span class='label-destaque'>Conta:</span> <span class='dado-destaque'>{compra['conta']}</span></p>"
                            f"<p><span class='label-destaque'>Descrição:</span> <span class='dado-destaque'>{compra['descricao']}</span></p>"
                            f"<p><span class='label-destaque'>Fornecedor:</span> <span class='dado-destaque'>{compra['fornecedor']}</span> | "
                            f"<span class='label-destaque'>Valor:</span> <span class='valor-destaque'>{formatar_moeda(compra['valor'])}</span></p>"
                            f"<p><span class='label-destaque'>Data:</span> <span class='dado-destaque'>{compra['data']}</span> | "
                            f"<span class='label-destaque'>Solicitante:</span> <span class='dado-destaque'>{compra['solicitante']}</span> | "
                            f"<span class='label-destaque'>Status:</span> <span class='dado-destaque'>{compra['status']}</span></p>",
                            unsafe_allow_html=True
                        )
                    with c2:
                        if st.button("Editar", key=f"edit_compra_{compra['id']}", use_container_width=True):
                            st.session_state.edit_compra_id = compra["id"]
                            st.rerun()
                        if st.button("Excluir", key=f"del_compra_{compra['id']}", use_container_width=True):
                            st.session_state.compras = [c for c in st.session_state.compras if c["id"] != compra["id"]]
                            st.success("Solicitação excluída.")
                            st.rerun()

    if "edit_compra_id" in st.session_state and st.session_state.edit_compra_id is not None:
        st.divider()
        editar_compra()


def editar_compra():
    compra = compra_por_id(st.session_state.edit_compra_id)
    if not compra:
        st.error("Compra não encontrada.")
        st.session_state.edit_compra_id = None
        return

    st.markdown("<h2>Editar Solicitação de Compra</h2>", unsafe_allow_html=True)
    with st.form("form_editar_compra"):
        esfera = st.selectbox("Esfera *", ESFERAS, index=ESFERAS.index(compra["esfera"]), key="edit_compra_esfera")
        contas_disponiveis = contas_por_esfera(esfera)
        conta_nomes = [c["nome"] for c in contas_disponiveis]
        conta_sel = compra["conta"] if compra["conta"] in conta_nomes else (conta_nomes[0] if conta_nomes else "")
        conta_selecionada = st.selectbox(
            "Conta Vinculada *",
            conta_nomes,
            index=conta_nomes.index(conta_sel) if conta_sel in conta_nomes else 0,
            key="edit_compra_conta"
        )
        descricao = st.text_area("Descrição *", value=compra["descricao"], key="edit_compra_descricao")
        fornecedor = st.text_input("Fornecedor", value=compra["fornecedor"], key="edit_compra_fornecedor")
        valor_str = mascara_moeda_input("Valor Estimado *", "edit_compra_valor", valor_inicial=formatar_moeda(compra["valor"]))
        data_obj = datetime.datetime.strptime(compra["data"], "%d/%m/%Y").date()
        data_compra = st.date_input("Data *", value=data_obj, format="DD/MM/YYYY", key="edit_compra_data")
        solicitante = st.text_input("Solicitante *", value=compra["solicitante"], key="edit_compra_solicitante")
        status = st.selectbox("Status", STATUS_COMPRA, index=STATUS_COMPRA.index(compra["status"]), key="edit_compra_status")

        c1, c2 = st.columns(2)
        with c1:
            salvar = st.form_submit_button("Salvar Alterações", use_container_width=True)
        with c2:
            cancelar = st.form_submit_button("Cancelar", use_container_width=True)

        if salvar:
            if not descricao.strip() or not solicitante.strip():
                st.error("Descrição e solicitante são obrigatórios.")
            else:
                conta_id = next((c["id"] for c in contas_disponiveis if c["nome"] == conta_selecionada), None)
                compra["esfera"] = esfera
                compra["conta_id"] = conta_id
                compra["conta"] = conta_selecionada
                compra["descricao"] = descricao.strip()
                compra["fornecedor"] = fornecedor.strip()
                compra["valor"] = parse_moeda(valor_str)
                compra["data"] = data_compra.strftime("%d/%m/%Y")
                compra["solicitante"] = solicitante.strip()
                compra["status"] = status
                st.session_state.edit_compra_id = None
                st.success("Solicitação atualizada com sucesso!")
                st.rerun()
        if cancelar:
            st.session_state.edit_compra_id = None
            st.rerun()


# =============================================================================
# SUPERÁVIT
# =============================================================================
def tela_superavit():
    st.markdown("<h1>Superávit Financeiro</h1>", unsafe_allow_html=True)
    st.markdown("<p>Análise de saldo entre contas cadastradas e compras solicitadas por esfera.</p>", unsafe_allow_html=True)

    dados = []
    for esfera in ESFERAS:
        tc = total_contas(esfera)
        tcm = total_compras(esfera)
        sup = superavit(esfera)
        dados.append({
            "Esfera": esfera,
            "Total em Contas": formatar_moeda(tc),
            "Total em Compras": formatar_moeda(tcm),
            "Superávit": formatar_moeda(sup)
        })

    total_c = sum(total_contas(e) for e in ESFERAS)
    total_cm = sum(total_compras(e) for e in ESFERAS)
    total_s = total_c - total_cm
    dados.append({
        "Esfera": "TOTAL GERAL",
        "Total em Contas": formatar_moeda(total_c),
        "Total em Compras": formatar_moeda(total_cm),
        "Superávit": formatar_moeda(total_s)
    })

    df = pd.DataFrame(dados)
    st.dataframe(df, use_container_width=True, hide_index=True)

    cols = st.columns(3)
    for i, esfera in enumerate(ESFERAS):
        with cols[i]:
            sup = superavit(esfera)
            cor = "#38bdf8" if sup >= 0 else "#f87171"
            st.markdown(
                f"<div class='info-card'>"
                f"<h3 style='color: #22d3ee;'>{esfera}</h3>"
                f"<p><span class='label-destaque'>Contas:</span> <span class='valor-destaque'>{formatar_moeda(total_contas(esfera))}</span></p>"
                f"<p><span class='label-destaque'>Compras:</span> <span class='valor-destaque'>{formatar_moeda(total_compras(esfera))}</span></p>"
                f"<p><span class='label-destaque'>Superávit:</span> <span style='color: {cor}; font-weight: 800;'>{formatar_moeda(sup)}</span></p>"
                f"</div>",
                unsafe_allow_html=True
            )


# =============================================================================
# PROGRAMAS DE SAÚDE
# =============================================================================
def tela_programas():
    st.markdown("<h1>Programas de Saúde</h1>", unsafe_allow_html=True)

    aba_cad, aba_list = st.tabs(["Cadastrar Programa", "Programas Cadastrados"])

    with aba_cad:
        with st.form("form_programa", clear_on_submit=True):
            esfera = st.selectbox("Esfera *", ESFERAS, key="prog_esfera")
            nome = st.text_input("Nome do Programa *", key="prog_nome")
            objetivo = st.text_area("Objetivo", key="prog_objetivo")
            meta = st.text_area("Meta / Público-alvo", key="prog_meta")
            data_inicio = st.date_input("Data de Início *", value=datetime.date.today(), format="DD/MM/YYYY", key="prog_inicio")
            data_fim = st.date_input("Data de Término", value=datetime.date.today(), format="DD/MM/YYYY", key="prog_fim")
            responsavel = st.text_input("Responsável", key="prog_responsavel")
            submitted = st.form_submit_button("Salvar Programa", use_container_width=True)
            if submitted:
                if not nome.strip():
                    st.error("O nome do programa é obrigatório.")
                else:
                    st.session_state.programas.append({
                        "id": novo_id("programa"),
                        "esfera": esfera,
                        "nome": nome.strip(),
                        "objetivo": objetivo.strip(),
                        "meta": meta.strip(),
                        "data_inicio": data_inicio.strftime("%d/%m/%Y"),
                        "data_fim": data_fim.strftime("%d/%m/%Y"),
                        "responsavel": responsavel.strip()
                    })
                    st.success("Programa cadastrado com sucesso!")
                    st.rerun()

    with aba_list:
        esfera_filtro = st.selectbox("Filtrar por Esfera", ["Todas"] + ESFERAS, key="filtro_prog_esfera")
        programas = st.session_state.programas
        if esfera_filtro != "Todas":
            programas = [p for p in programas if p["esfera"] == esfera_filtro]

        if not programas:
            st.info("Nenhum programa cadastrado.")
        else:
            for prog in programas:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(
                            f"<p><span class='label-destaque'>ID:</span> <span class='dado-destaque'>{prog['id']}</span> | "
                            f"<span class='label-destaque'>Esfera:</span> <span class='dado-destaque'>{prog['esfera']}</span></p>"
                            f"<p><span class='label-destaque'>Programa:</span> <span class='dado-destaque'>{prog['nome']}</span></p>"
                            f"<p><span class='label-destaque'>Objetivo:</span> {prog['objetivo']}</p>"
                            f"<p><span class='label-destaque'>Meta:</span> {prog['meta']}</p>"
                            f"<p><span class='label-destaque'>Início:</span> <span class='dado-destaque'>{prog['data_inicio']}</span> | "
                            f"<span class='label-destaque'>Término:</span> <span class='dado-destaque'>{prog['data_fim']}</span></p>"
                            f"<p><span class='label-destaque'>Responsável:</span> <span class='dado-destaque'>{prog['responsavel']}</span></p>",
                            unsafe_allow_html=True
                        )
                    with c2:
                        if st.button("Excluir", key=f"del_prog_{prog['id']}", use_container_width=True):
                            st.session_state.programas = [p for p in st.session_state.programas if p["id"] != prog["id"]]
                            st.success("Programa excluído.")
                            st.rerun()


# =============================================================================
# PLANO MUNICIPAL DE SAÚDE
# =============================================================================
def tela_plano_municipal():
    st.markdown("<h1>Plano Municipal de Saúde</h1>", unsafe_allow_html=True)

    aba_cad, aba_list = st.tabs(["Cadastrar Ação", "Ações Cadastradas"])

    with aba_cad:
        with st.form("form_plano", clear_on_submit=True):
            eixo = st.text_input("Eixo / Estratégia *", key="plano_eixo")
            acao = st.text_area("Ação / Intervenção *", key="plano_acao")
            indicador = st.text_input("Indicador", key="plano_indicador")
            meta = st.text_input("Meta", key="plano_meta")
            prazo = st.date_input("Prazo", value=datetime.date.today(), format="DD/MM/YYYY", key="plano_prazo")
            responsavel = st.text_input("Responsável", key="plano_responsavel")
            submitted = st.form_submit_button("Salvar Ação", use_container_width=True)
            if submitted:
                if not eixo.strip() or not acao.strip():
                    st.error("Eixo e ação são obrigatórios.")
                else:
                    st.session_state.planos.append({
                        "id": novo_id("plano"),
                        "eixo": eixo.strip(),
                        "acao": acao.strip(),
                        "indicador": indicador.strip(),
                        "meta": meta.strip(),
                        "prazo": prazo.strftime("%d/%m/%Y"),
                        "responsavel": responsavel.strip()
                    })
                    st.success("Ação cadastrada com sucesso!")
                    st.rerun()

    with aba_list:
        if not st.session_state.planos:
            st.info("Nenhuma ação cadastrada no Plano Municipal de Saúde.")
        else:
            for plano in st.session_state.planos:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(
                            f"<p><span class='label-destaque'>ID:</span> <span class='dado-destaque'>{plano['id']}</span></p>"
                            f"<p><span class='label-destaque'>Eixo:</span> <span class='dado-destaque'>{plano['eixo']}</span></p>"
                            f"<p><span class='label-destaque'>Ação:</span> {plano['acao']}</p>"
                            f"<p><span class='label-destaque'>Indicador:</span> {plano['indicador']} | "
                            f"<span class='label-destaque'>Meta:</span> {plano['meta']}</p>"
                            f"<p><span class='label-destaque'>Prazo:</span> <span class='dado-destaque'>{plano['prazo']}</span> | "
                            f"<span class='label-destaque'>Responsável:</span> <span class='dado-destaque'>{plano['responsavel']}</span></p>",
                            unsafe_allow_html=True
                        )
                    with c2:
                        if st.button("Excluir", key=f"del_plano_{plano['id']}", use_container_width=True):
                            st.session_state.planos = [p for p in st.session_state.planos if p["id"] != plano["id"]]
                            st.success("Ação excluída.")
                            st.rerun()


# =============================================================================
# NORTE DA MINHA GESTÃO
# =============================================================================
def tela_norte_gestao():
    st.markdown("<h1>Norte da Minha Gestão</h1>", unsafe_allow_html=True)

    aba_cad, aba_list = st.tabs(["Cadastrar Diretriz", "Diretrizes Cadastradas"])

    with aba_cad:
        with st.form("form_norte", clear_on_submit=True):
            esfera = st.selectbox("Esfera *", ESFERAS, key="norte_esfera")
            titulo = st.text_input("Título da Diretriz *", key="norte_titulo")
            descricao = st.text_area("Descrição", key="norte_descricao")
            prioridade = st.selectbox("Prioridade", ["Alta", "Média", "Baixa"], key="norte_prioridade")
            responsavel = st.text_input("Responsável", key="norte_responsavel")
            prazo = st.date_input("Prazo", value=datetime.date.today(), format="DD/MM/YYYY", key="norte_prazo")
            submitted = st.form_submit_button("Salvar Diretriz", use_container_width=True)
            if submitted:
                if not titulo.strip():
                    st.error("O título da diretriz é obrigatório.")
                else:
                    st.session_state.nortes.append({
                        "id": novo_id("norte"),
                        "esfera": esfera,
                        "titulo": titulo.strip(),
                        "descricao": descricao.strip(),
                        "prioridade": prioridade,
                        "responsavel": responsavel.strip(),
                        "prazo": prazo.strftime("%d/%m/%Y")
                    })
                    st.success("Diretriz cadastrada com sucesso!")
                    st.rerun()

    with aba_list:
        esfera_filtro = st.selectbox("Filtrar por Esfera", ["Todas"] + ESFERAS, key="filtro_norte_esfera")
        nortes = st.session_state.nortes
        if esfera_filtro != "Todas":
            nortes = [n for n in nortes if n["esfera"] == esfera_filtro]

        if not nortes:
            st.info("Nenhuma diretriz cadastrada.")
        else:
            for norte in nortes:
                cor_prioridade = {"Alta": "#f87171", "Média": "#fbbf24", "Baixa": "#38bdf8"}
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(
                            f"<p><span class='label-destaque'>ID:</span> <span class='dado-destaque'>{norte['id']}</span> | "
                            f"<span class='label-destaque'>Esfera:</span> <span class='dado-destaque'>{norte['esfera']}</span></p>"
                            f"<p><span class='label-destaque'>Título:</span> <span class='dado-destaque'>{norte['titulo']}</span></p>"
                            f"<p><span class='label-destaque'>Descrição:</span> {norte['descricao']}</p>"
                            f"<p><span class='label-destaque'>Prioridade:</span> "
                            f"<span style='color: {cor_prioridade.get(norte['prioridade'], '#cbd5e1')}; font-weight: 800;'>{norte['prioridade']}</span> | "
                            f"<span class='label-destaque'>Prazo:</span> <span class='dado-destaque'>{norte['prazo']}</span></p>"
                            f"<p><span class='label-destaque'>Responsável:</span> <span class='dado-destaque'>{norte['responsavel']}</span></p>",
                            unsafe_allow_html=True
                        )
                    with c2:
                        if st.button("Excluir", key=f"del_norte_{norte['id']}", use_container_width=True):
                            st.session_state.nortes = [n for n in st.session_state.nortes if n["id"] != norte["id"]]
                            st.success("Diretriz excluída.")
                            st.rerun()


# =============================================================================
# UPLOAD E BUSCA DE DOCUMENTOS
# =============================================================================
def tela_documentos():
    st.markdown("<h1>Upload e Busca de Documentos</h1>", unsafe_allow_html=True)

    aba_upload, aba_busca = st.tabs(["Upload de Documentos", "Buscar Documentos"])

    with aba_upload:
        with st.form("form_documento", clear_on_submit=True):
            esfera = st.selectbox("Esfera *", ESFERAS, key="doc_esfera")
            titulo = st.text_input("Título do Documento *", key="doc_titulo")
            tipo = st.selectbox("Tipo", ["Ofício", "Relatório", "Portaria", "Lei", "Plano", "Outro"], key="doc_tipo")
            data_doc = st.date_input("Data do Documento", value=datetime.date.today(), format="DD/MM/YYYY", key="doc_data")
            arquivo = st.file_uploader("Selecione o arquivo", type=["pdf", "docx", "txt", "png", "jpg", "jpeg"], key="doc_arquivo")
            submitted = st.form_submit_button("Salvar Documento", use_container_width=True)
            if submitted:
                if not titulo.strip():
                    st.error("O título do documento é obrigatório.")
                elif arquivo is None:
                    st.error("Selecione um arquivo para upload.")
                else:
                    conteudo = ""
                    if arquivo.type == "text/plain":
                        try:
                            conteudo = arquivo.read().decode("utf-8", errors="ignore")
                        except Exception:
                            conteudo = ""
                    else:
                        conteudo = "[Arquivo binário - visualização indisponível para busca textual]"

                    st.session_state.documentos.append({
                        "id": novo_id("documento"),
                        "esfera": esfera,
                        "titulo": titulo.strip(),
                        "tipo": tipo,
                        "data": data_doc.strftime("%d/%m/%Y"),
                        "nome_arquivo": arquivo.name,
                        "tipo_arquivo": arquivo.type,
                        "bytes": arquivo.getvalue(),
                        "conteudo_texto": conteudo
                    })
                    st.success("Documento salvo com sucesso!")
                    st.rerun()

    with aba_busca:
        termo = st.text_input("Buscar por palavra-chave no título ou conteúdo", key="doc_busca")
        esfera_filtro = st.selectbox("Filtrar por Esfera", ["Todas"] + ESFERAS, key="doc_filtro_esfera")
        documentos = st.session_state.documentos
        if esfera_filtro != "Todas":
            documentos = [d for d in documentos if d["esfera"] == esfera_filtro]
        if termo:
            termo_lower = termo.lower()
            documentos = [
                d for d in documentos
                if termo_lower in d["titulo"].lower() or termo_lower in d["conteudo_texto"].lower()
            ]

        if not documentos:
            st.info("Nenhum documento encontrado.")
        else:
            st.markdown(f"<p><span class='label-destaque'>Resultados encontrados:</span> <span class='dado-destaque'>{len(documentos)}</span></p>", unsafe_allow_html=True)
            for doc in documentos:
                with st.container(border=True):
                    st.markdown(
                        f"<p><span class='label-destaque'>ID:</span> <span class='dado-destaque'>{doc['id']}</span> | "
                        f"<span class='label-destaque'>Esfera:</span> <span class='dado-destaque'>{doc['esfera']}</span> | "
                        f"<span class='label-destaque'>Tipo:</span> <span class='dado-destaque'>{doc['tipo']}</span></p>"
                        f"<p><span class='label-destaque'>Título:</span> <span class='dado-destaque'>{doc['titulo']}</span></p>"
                        f"<p><span class='label-destaque'>Arquivo:</span> <span class='dado-destaque'>{doc['nome_arquivo']}</span> | "
                        f"<span class='label-destaque'>Data:</span> <span class='dado-destaque'>{doc['data']}</span></p>",
                        unsafe_allow_html=True
                    )
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        st.download_button(
                            label="Download",
                            data=doc["bytes"],
                            file_name=doc["nome_arquivo"],
                            mime=doc["tipo_arquivo"],
                            key=f"download_doc_{doc['id']}"
                        )
                    with col2:
                        if st.button("Excluir", key=f"del_doc_{doc['id']}"):
                            st.session_state.documentos = [d for d in st.session_state.documentos if d["id"] != doc["id"]]
                            st.success("Documento excluído.")
                            st.rerun()


# =============================================================================
# MENU LATERAL E NAVEGAÇÃO
# =============================================================================
def menu_principal():
    st.sidebar.markdown("<h2 style='color: #22d3ee;'>MARMED</h2>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<p style='color: #cbd5e1;'>Usuário: <span style='color: #f8fafc; font-weight: 700;'>{st.session_state.usuario}</span></p>", unsafe_allow_html=True)
    st.sidebar.divider()

    opcoes = [
        "Dashboard",
        "Contas",
        "Compras",
        "Superávit",
        "Programas de Saúde",
        "Plano Municipal de Saúde",
        "Norte da Minha Gestão",
        "Documentos"
    ]

    opcao = st.sidebar.radio("Menu", opcoes, label_visibility="collapsed")

    if st.sidebar.button("Sair", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.usuario = None
        st.session_state.edit_conta_id = None
        st.session_state.edit_compra_id = None
        st.rerun()

    if opcao == "Dashboard":
        dashboard()
    elif opcao == "Contas":
        tela_contas()
    elif opcao == "Compras":
        tela_compras()
    elif opcao == "Superávit":
        tela_superavit()
    elif opcao == "Programas de Saúde":
        tela_programas()
    elif opcao == "Plano Municipal de Saúde":
        tela_plano_municipal()
    elif opcao == "Norte da Minha Gestão":
        tela_norte_gestao()
    elif opcao == "Documentos":
        tela_documentos()


# =============================================================================
# PONTO DE ENTRADA
# =============================================================================
def main():
    if not st.session_state.authenticated:
        tela_login()
    else:
        menu_principal()


if __name__ == "__main__":
    main()
