import streamlit as st
import pandas as pd
import re
from datetime import datetime, date
from io import BytesIO
import base64

# =============================================================================
# CONFIGURAÇÃO INICIAL
# =============================================================================
st.set_page_config(page_title="MARMED", page_icon="🏥", layout="wide")

# =============================================================================
# CSS PERSONALIZADO - ESQUEMA ESCURO COM CORES VIBRANTES
# =============================================================================
def aplicar_css():
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

        .main-title {
            color: #f8fafc;
            font-weight: 900;
            font-size: 2.5rem;
            text-align: center;
            margin-bottom: 0.5rem;
        }

        .subtitle {
            color: #22d3ee;
            font-weight: 700;
            text-align: center;
            margin-bottom: 2rem;
        }

        .stDataFrame, .stTable {
            background-color: #1e293b;
            border-radius: 12px;
            padding: 1rem;
        }

        .stTextInput>div>div>input,
        .stNumberInput>div>div>input,
        .stSelectbox>div>div,
        .stDateInput>div>div>input,
        .stTextArea>div>div>textarea {
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border: 1px solid rgba(34, 211, 238, 0.4) !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
        }

        .stTextInput>div>div>input:focus,
        .stNumberInput>div>div>input:focus,
        .stSelectbox>div>div:focus,
        .stDateInput>div>div>input:focus,
        .stTextArea>div>div>textarea:focus {
            border: 1px solid #22d3ee !important;
            box-shadow: 0 0 0 2px rgba(34, 211, 238, 0.25) !important;
        }

        label, .stSlider > label, .stCheckbox > label, .stRadio > label {
            color: #22d3ee !important;
            font-weight: 700 !important;
        }

        .stButton > button {
            background: linear-gradient(135deg, #0ea5e9, #22d3ee);
            color: #0f172a;
            font-weight: 800 !important;
            border: none;
            border-radius: 10px;
            padding: 0.6rem 1.2rem;
            transition: all 0.2s ease;
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(34, 211, 238, 0.35);
        }

        .stButton > button:active {
            transform: translateY(0);
        }

        .card {
            background: linear-gradient(145deg, #1e293b, #0f172a);
            border: 1px solid rgba(34, 211, 238, 0.25);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 10px 25px rgba(2, 8, 20, 0.5);
        }

        .card-title {
            color: #22d3ee;
            font-weight: 700;
            font-size: 1.1rem;
            margin-bottom: 0.5rem;
        }

        .card-value {
            color: #f8fafc;
            font-weight: 800;
            font-size: 1.8rem;
            margin-bottom: 0.3rem;
        }

        .card-money {
            color: #38bdf8;
            font-weight: 800;
            font-size: 1.6rem;
        }

        .metric-label {
            color: #22d3ee;
            font-weight: 700;
        }

        .metric-value {
            color: #f8fafc;
            font-weight: 700;
        }

        .stTabs [data-baseweb="tab-list"] {
            border-bottom: 2px solid rgba(34, 211, 238, 0.2);
        }

        .stTabs [data-baseweb="tab"] {
            color: #94a3b8;
            font-weight: 700;
        }

        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
            color: #22d3ee;
            border-bottom: 2px solid #22d3ee;
        }

        .stSidebar {
            background-color: #0f172a;
        }

        .stSidebar .stButton > button {
            width: 100%;
            margin-bottom: 0.5rem;
        }

        .alert-success {
            background-color: rgba(34, 211, 238, 0.15);
            border: 1px solid rgba(34, 211, 238, 0.4);
            color: #22d3ee;
            padding: 1rem;
            border-radius: 10px;
            font-weight: 700;
        }

        .alert-error {
            background-color: rgba(248, 113, 113, 0.15);
            border: 1px solid rgba(248, 113, 113, 0.4);
            color: #f87171;
            padding: 1rem;
            border-radius: 10px;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# =============================================================================
# INICIALIZAÇÃO DO ESTADO
# =============================================================================
def inicializar_estado():
    defaults = {
        "autenticado": False,
        "usuario": None,
        "contas": [],
        "compras": [],
        "superavit": {"Federal": 0.0, "Estadual": 0.0, "Municipal": 0.0},
        "programas": [],
        "plano_municipal": {},
        "norte_gestao": {},
        "documentos": [],
        "menu": "Dashboard",
    }
    for chave, valor in defaults.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor

# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================
def formatar_moeda(valor):
    """Formata um float no padrão brasileiro R$ 1.234,56"""
    if valor is None:
        valor = 0.0
    sinal = "- " if valor < 0 else ""
    valor_abs = abs(valor)
    inteiro = str(int(valor_abs))
    reais = []
    while len(inteiro) > 3:
        reais.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    reais.insert(0, inteiro)
    parte_inteira = ".".join(reais)
    centavos = str(int(round((valor_abs - int(valor_abs)) * 100))).zfill(2)
    return f"R$ {sinal}{parte_inteira},{centavos}"


def mascara_moeda_input(valor_str):
    """Aplica máscara de moeda em string digitada."""
    digitos = re.sub(r"[^0-9]", "", valor_str)
    if not digitos:
        return "R$ 0,00"
    if len(digitos) == 1:
        digitos = "00" + digitos
    elif len(digitos) == 2:
        digitos = "0" + digitos
    reais = digitos[:-2]
    centavos = digitos[-2:]
    while len(reais) < 3:
        reais = "0" + reais
    partes = []
    while len(reais) > 3:
        partes.insert(0, reais[-3:])
        reais = reais[:-3]
    partes.insert(0, reais)
    parte_inteira = ".".join(partes)
    return f"R$ {parte_inteira},{centavos}"


def parse_moeda(valor_str):
    """Converte string formatada em R$ para float."""
    if not valor_str:
        return 0.0
    limpo = valor_str.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return 0.0


# =============================================================================
# AUTENTICAÇÃO
# =============================================================================
def tela_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='main-title'>🏥 MARMED</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='subtitle'>Sistema de Gestão de Recursos em Saúde</div>",
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            st.markdown("<h3 style='color:#f8fafc;'>Acesso ao Sistema</h3>", unsafe_allow_html=True)
            usuario = st.text_input("Usuário", value="")
            senha = st.text_input("Senha", type="password", value="")
            submit = st.form_submit_button("Entrar")

            if submit:
                if usuario == "admin" and senha == "Diretor2025#":
                    st.session_state["autenticado"] = True
                    st.session_state["usuario"] = usuario
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos!")


# =============================================================================
# DASHBOARD
# =============================================================================
def dashboard():
    st.markdown("<div class='main-title'>Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Visão Geral por Esfera de Gestão</div>", unsafe_allow_html=True)

    esferas = ["Federal", "Estadual", "Municipal"]

    for esfera in esferas:
        contas_esfera = [c for c in st.session_state["contas"] if c["esfera"] == esfera]
        total_contas = sum(c["saldo"] for c in contas_esfera)
        compras_esfera = [c for c in st.session_state["compras"] if c["esfera"] == esfera]
        total_compras = sum(c["valor_total"] for c in compras_esfera)
        superavit = st.session_state["superavit"].get(esfera, 0.0)
        saldo_disponivel = total_contas + superavit - total_compras

        with st.container():
            st.markdown(f"<h3 style='color:#22d3ee;'>{esfera}</h3>", unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(
                    f"""
                    <div class='card'>
                        <div class='card-title'>Contas Cadastradas</div>
                        <div class='card-value'>{len(contas_esfera)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    f"""
                    <div class='card'>
                        <div class='card-title'>Saldo em Contas</div>
                        <div class='card-money'>{formatar_moeda(total_contas)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(
                    f"""
                    <div class='card'>
                        <div class='card-title'>Compras Solicitadas</div>
                        <div class='card-money'>{formatar_moeda(total_compras)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c4:
                st.markdown(
                    f"""
                    <div class='card'>
                        <div class='card-title'>Saldo Disponível</div>
                        <div class='card-money'>{formatar_moeda(saldo_disponivel)}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.divider()

    # Resumo geral
    total_geral_contas = sum(c["saldo"] for c in st.session_state["contas"])
    total_geral_compras = sum(c["valor_total"] for c in st.session_state["compras"])
    total_geral_superavit = sum(st.session_state["superavit"].values())
    saldo_geral = total_geral_contas + total_geral_superavit - total_geral_compras

    st.markdown("<h3 style='color:#f8fafc;'>Resumo Geral</h3>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(label="Total em Contas", value=formatar_moeda(total_geral_contas))
    with c2:
        st.metric(label="Total em Compras", value=formatar_moeda(total_geral_compras))
    with c3:
        st.metric(label="Saldo Geral", value=formatar_moeda(saldo_geral))


# =============================================================================
# CADASTRO DE CONTAS
# =============================================================================
def cadastro_contas():
    st.markdown("<div class='main-title'>Cadastro de Contas</div>", unsafe_allow_html=True)

    esferas = ["Federal", "Estadual", "Municipal"]

    with st.form("form_conta"):
        col1, col2, col3 = st.columns(3)
        with col1:
            esfera = st.selectbox("Esfera", esferas)
        with col2:
            banco = st.text_input("Banco")
        with col3:
            agencia = st.text_input("Agência")

        col1, col2, col3 = st.columns(3)
        with col1:
            numero_conta = st.text_input("Número da Conta")
        with col2:
            nome_conta = st.text_input("Nome da Conta / Identificação")
        with col3:
            saldo_input = st.text_input("Saldo Inicial", value="R$ 0,00")

        submitted = st.form_submit_button("Cadastrar Conta")
        if submitted:
            saldo = parse_moeda(saldo_input)
            if not banco or not numero_conta or not nome_conta:
                st.error("Preencha todos os campos obrigatórios!")
            else:
                nova_conta = {
                    "id": len(st.session_state["contas"]) + 1,
                    "esfera": esfera,
                    "banco": banco,
                    "agencia": agencia,
                    "numero_conta": numero_conta,
                    "nome_conta": nome_conta,
                    "saldo": saldo,
                }
                st.session_state["contas"].append(nova_conta)
                st.success("Conta cadastrada com sucesso!")
                st.rerun()

    st.divider()
    st.markdown("<h3 style='color:#f8fafc;'>Contas Cadastradas</h3>", unsafe_allow_html=True)

    abas = st.tabs(esferas)
    for idx, esfera in enumerate(esferas):
        with abas[idx]:
            contas_esfera = [c for c in st.session_state["contas"] if c["esfera"] == esfera]
            if not contas_esfera:
                st.info(f"Nenhuma conta cadastrada na esfera {esfera}.")
            else:
                df = pd.DataFrame(contas_esfera)
                df["saldo_fmt"] = df["saldo"].apply(formatar_moeda)
                st.dataframe(df[["banco", "agencia", "numero_conta", "nome_conta", "saldo_fmt"]],
                             use_container_width=True, hide_index=True)

                for conta in contas_esfera:
                    with st.expander(f"Editar / Excluir - {conta['nome_conta']}"):
                        with st.form(f"editar_conta_{conta['id']}"):
                            novo_banco = st.text_input("Banco", value=conta["banco"], key=f"banco_{conta['id']}")
                            nova_agencia = st.text_input("Agência", value=conta["agencia"], key=f"agencia_{conta['id']}")
                            novo_numero = st.text_input("Número da Conta", value=conta["numero_conta"], key=f"numero_{conta['id']}")
                            novo_nome = st.text_input("Nome da Conta", value=conta["nome_conta"], key=f"nome_{conta['id']}")
                            novo_saldo = st.text_input("Saldo", value=formatar_moeda(conta["saldo"]), key=f"saldo_{conta['id']}")

                            col1, col2 = st.columns(2)
                            with col1:
                                salvar = st.form_submit_button("Salvar Alterações")
                            with col2:
                                excluir = st.form_submit_button("Excluir Conta")

                            if salvar:
                                conta["banco"] = novo_banco
                                conta["agencia"] = nova_agencia
                                conta["numero_conta"] = novo_numero
                                conta["nome_conta"] = novo_nome
                                conta["saldo"] = parse_moeda(novo_saldo)
                                st.success("Conta atualizada com sucesso!")
                                st.rerun()
                            if excluir:
                                st.session_state["contas"] = [c for c in st.session_state["contas"] if c["id"] != conta["id"]]
                                st.success("Conta excluída com sucesso!")
                                st.rerun()


# =============================================================================
# COMPRAS
# =============================================================================
def compras():
    st.markdown("<div class='main-title'>Solicitações de Compra</div>", unsafe_allow_html=True)

    esferas = ["Federal", "Estadual", "Municipal"]

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("<h3 style='color:#f8fafc;'>Nova Solicitação</h3>", unsafe_allow_html=True)
        with st.form("form_compra"):
            esfera = st.selectbox("Esfera", esferas, key="compra_esfera")
            contas_esfera = [c for c in st.session_state["contas"] if c["esfera"] == esfera]
            conta_opcoes = {f"{c['nome_conta']} - {c['numero_conta']}": c for c in contas_esfera}
            conta_selecionada = st.selectbox(
                "Conta Vinculada", options=list(conta_opcoes.keys()) if conta_opcoes else ["Nenhuma conta disponível"]
            )

            fornecedor = st.text_input("Fornecedor")
            produto = st.text_input("Produto / Serviço")
            quantidade = st.number_input("Quantidade", min_value=1, value=1, step=1)
            valor_unitario = st.text_input("Valor Unitário", value="R$ 0,00")
            data_compra = st.date_input("Data da Solicitação", value=date.today(), format="DD/MM/YYYY")
            observacao = st.text_area("Observação")

            submitted = st.form_submit_button("Solicitar")
            if submitted:
                if not conta_opcoes or conta_selecionada == "Nenhuma conta disponível":
                    st.error("Nenhuma conta disponível para a esfera selecionada.")
                elif not fornecedor or not produto:
                    st.error("Preencha fornecedor e produto.")
                else:
                    vu = parse_moeda(valor_unitario)
                    vt = vu * quantidade
                    if vt <= 0:
                        st.error("Valor total da compra deve ser maior que zero.")
                    else:
                        conta = conta_opcoes[conta_selecionada]
                        if vt > conta["saldo"]:
                            st.error("Saldo insuficiente na conta selecionada.")
                        else:
                            nova_compra = {
                                "id": len(st.session_state["compras"]) + 1,
                                "esfera": esfera,
                                "conta_id": conta["id"],
                                "conta_nome": conta["nome_conta"],
                                "fornecedor": fornecedor,
                                "produto": produto,
                                "quantidade": quantidade,
                                "valor_unitario": vu,
                                "valor_total": vt,
                                "data": data_compra.strftime("%d/%m/%Y"),
                                "observacao": observacao,
                                "status": "Solicitada",
                            }
                            conta["saldo"] -= vt
                            st.session_state["compras"].append(nova_compra)
                            st.success("Compra solicitada com sucesso!")
                            st.rerun()

    with col2:
        st.markdown("<h3 style='color:#f8fafc;'>Solicitações Realizadas</h3>", unsafe_allow_html=True)
        if not st.session_state["compras"]:
            st.info("Nenhuma solicitação de compra realizada.")
        else:
            df = pd.DataFrame(st.session_state["compras"])
            df["valor_unitario_fmt"] = df["valor_unitario"].apply(formatar_moeda)
            df["valor_total_fmt"] = df["valor_total"].apply(formatar_moeda)
            st.dataframe(
                df[["esfera", "conta_nome", "fornecedor", "produto", "quantidade", "valor_total_fmt", "data", "status"]],
                use_container_width=True,
                hide_index=True,
            )

            for compra in st.session_state["compras"]:
                with st.expander(f"Editar / Excluir - {compra['produto']} ({compra['esfera']})"):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("Editar", key=f"edit_compra_{compra['id']}"):
                            st.session_state["compra_edicao"] = compra
                            st.rerun()
                    with col_b:
                        if st.button("Excluir", key=f"del_compra_{compra['id']}"):
                            conta = next((c for c in st.session_state["contas"] if c["id"] == compra["conta_id"]), None)
                            if conta:
                                conta["saldo"] += compra["valor_total"]
                            st.session_state["compras"] = [c for c in st.session_state["compras"] if c["id"] != compra["id"]]
                            st.success("Solicitação excluída com sucesso!")
                            st.rerun()

    if "compra_edicao" in st.session_state and st.session_state["compra_edicao"]:
        compra = st.session_state["compra_edicao"]
        st.divider()
        st.markdown("<h3 style='color:#f8fafc;'>Editar Solicitação</h3>", unsafe_allow_html=True)
        with st.form("editar_compra"):
            novo_fornecedor = st.text_input("Fornecedor", value=compra["fornecedor"])
            novo_produto = st.text_input("Produto", value=compra["produto"])
            nova_quantidade = st.number_input("Quantidade", min_value=1, value=compra["quantidade"], step=1)
            novo_valor_unitario = st.text_input("Valor Unitário", value=formatar_moeda(compra["valor_unitario"]))
            nova_data = st.date_input("Data", value=datetime.strptime(compra["data"], "%d/%m/%Y").date(), format="DD/MM/YYYY")
            novo_status = st.selectbox("Status", ["Solicitada", "Aprovada", "Reprovada", "Cancelada"], index=["Solicitada", "Aprovada", "Reprovada", "Cancelada"].index(compra["status"]))

            col1, col2 = st.columns(2)
            with col1:
                salvar = st.form_submit_button("Salvar")
            with col2:
                cancelar = st.form_submit_button("Cancelar Edição")

            if salvar:
                conta = next((c for c in st.session_state["contas"] if c["id"] == compra["conta_id"]), None)
                if conta:
                    conta["saldo"] += compra["valor_total"]
                    novo_vu = parse_moeda(novo_valor_unitario)
                    novo_vt = novo_vu * nova_quantidade
                    if novo_vt <= 0:
                        st.error("Valor total deve ser maior que zero.")
                        conta["saldo"] -= compra["valor_total"]
                    elif novo_vt > conta["saldo"]:
                        st.error("Saldo insuficiente na conta.")
                        conta["saldo"] -= compra["valor_total"]
                    else:
                        compra["fornecedor"] = novo_fornecedor
                        compra["produto"] = novo_produto
                        compra["quantidade"] = nova_quantidade
                        compra["valor_unitario"] = novo_vu
                        compra["valor_total"] = novo_vt
                        compra["data"] = nova_data.strftime("%d/%m/%Y")
                        compra["status"] = novo_status
                        conta["saldo"] -= novo_vt
                        st.session_state["compra_edicao"] = None
                        st.success("Solicitação atualizada com sucesso!")
                        st.rerun()
            if cancelar:
                st.session_state["compra_edicao"] = None
                st.rerun()


# =============================================================================
# SUPERÁVIT FINANCEIRO
# =============================================================================
def superavit():
    st.markdown("<div class='main-title'>Superávit Financeiro</div>", unsafe_allow_html=True)

    esferas = ["Federal", "Estadual", "Municipal"]

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("<h3 style='color:#f8fafc;'>Lançar Superávit</h3>", unsafe_allow_html=True)
        with st.form("form_superavit"):
            esfera = st.selectbox("Esfera", esferas)
            valor = st.text_input("Valor", value="R$ 0,00")
            data_superavit = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")
            descricao = st.text_area("Descrição / Origem")
            submitted = st.form_submit_button("Lançar Superávit")
            if submitted:
                v = parse_moeda(valor)
                if v <= 0:
                    st.error("Valor deve ser maior que zero.")
                else:
                    st.session_state["superavit"][esfera] = st.session_state["superavit"].get(esfera, 0.0) + v
                    if "historico_superavit" not in st.session_state:
                        st.session_state["historico_superavit"] = []
                    st.session_state["historico_superavit"].append({
                        "esfera": esfera,
                        "valor": v,
                        "data": data_superavit.strftime("%d/%m/%Y"),
                        "descricao": descricao,
                    })
                    st.success("Superávit lançado com sucesso!")
                    st.rerun()

    with col2:
        st.markdown("<h3 style='color:#f8fafc;'>Saldo de Superávit por Esfera</h3>", unsafe_allow_html=True)
        for esfera in esferas:
            valor = st.session_state["superavit"].get(esfera, 0.0)
            st.markdown(
                f"""
                <div class='card'>
                    <div class='card-title'>{esfera}</div>
                    <div class='card-money'>{formatar_moeda(valor)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if "historico_superavit" in st.session_state and st.session_state["historico_superavit"]:
            st.markdown("<h4 style='color:#22d3ee;'>Histórico de Lançamentos</h4>", unsafe_allow_html=True)
            df = pd.DataFrame(st.session_state["historico_superavit"])
            df["valor_fmt"] = df["valor"].apply(formatar_moeda)
            st.dataframe(df[["esfera", "valor_fmt", "data", "descricao"]], use_container_width=True, hide_index=True)


# =============================================================================
# PROGRAMAS DE SAÚDE
# =============================================================================
def programas_saude():
    st.markdown("<div class='main-title'>Programas de Saúde</div>", unsafe_allow_html=True)

    esferas = ["Federal", "Estadual", "Municipal"]

    with st.form("form_programa"):
        col1, col2 = st.columns(2)
        with col1:
            esfera = st.selectbox("Esfera", esferas)
        with col2:
            nome_programa = st.text_input("Nome do Programa")
        descricao = st.text_area("Descrição do Programa")
        data_inicio = st.date_input("Data de Início", value=date.today(), format="DD/MM/YYYY")
        data_fim = st.date_input("Data de Término", value=date.today(), format="DD/MM/YYYY")
        submitted = st.form_submit_button("Cadastrar Programa")
        if submitted:
            if not nome_programa:
                st.error("Informe o nome do programa.")
            else:
                st.session_state["programas"].append({
                    "id": len(st.session_state["programas"]) + 1,
                    "esfera": esfera,
                    "nome": nome_programa,
                    "descricao": descricao,
                    "data_inicio": data_inicio.strftime("%d/%m/%Y"),
                    "data_fim": data_fim.strftime("%d/%m/%Y"),
                })
                st.success("Programa cadastrado com sucesso!")
                st.rerun()

    st.divider()
    st.markdown("<h3 style='color:#f8fafc;'>Programas Cadastrados</h3>", unsafe_allow_html=True)
    if not st.session_state["programas"]:
        st.info("Nenhum programa cadastrado.")
    else:
        filtro_esfera = st.selectbox("Filtrar por Esfera", ["Todas"] + esferas)
        programas_filtrados = st.session_state["programas"]
        if filtro_esfera != "Todas":
            programas_filtrados = [p for p in programas_filtrados if p["esfera"] == filtro_esfera]
        df = pd.DataFrame(programas_filtrados)
        st.dataframe(df[["esfera", "nome", "descricao", "data_inicio", "data_fim"]], use_container_width=True, hide_index=True)


# =============================================================================
# PLANO MUNICIPAL DE SAÚDE
# =============================================================================
def plano_municipal():
    st.markdown("<div class='main-title'>Plano Municipal de Saúde</div>", unsafe_allow_html=True)

    with st.form("form_plano"):
        titulo = st.text_input("Título do Plano")
        objetivo = st.text_area("Objetivo Geral")
        metas = st.text_area("Metas e Indicadores")
        acoes = st.text_area("Ações e Estratégias")
        vigencia_inicio = st.date_input("Início da Vigência", value=date.today(), format="DD/MM/YYYY")
        vigencia_fim = st.date_input("Fim da Vigência", value=date.today(), format="DD/MM/YYYY")
        submitted = st.form_submit_button("Salvar Plano")
        if submitted:
            st.session_state["plano_municipal"] = {
                "titulo": titulo,
                "objetivo": objetivo,
                "metas": metas,
                "acoes": acoes,
                "vigencia_inicio": vigencia_inicio.strftime("%d/%m/%Y"),
                "vigencia_fim": vigencia_fim.strftime("%d/%m/%Y"),
            }
            st.success("Plano Municipal de Saúde salvo com sucesso!")
            st.rerun()

    st.divider()
    if st.session_state["plano_municipal"]:
        plano = st.session_state["plano_municipal"]
        st.markdown(
            f"""
            <div class='card'>
                <div class='card-title'>{plano.get('titulo', 'Sem título')}</div>
                <p><strong style='color:#22d3ee;'>Objetivo:</strong> {plano.get('objetivo', '')}</p>
                <p><strong style='color:#22d3ee;'>Metas:</strong> {plano.get('metas', '')}</p>
                <p><strong style='color:#22d3ee;'>Ações:</strong> {plano.get('acoes', '')}</p>
                <p><strong style='color:#22d3ee;'>Vigência:</strong> {plano.get('vigencia_inicio', '')} a {plano.get('vigencia_fim', '')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("Nenhum Plano Municipal de Saúde cadastrado.")


# =============================================================================
# NORTE DA MINHA GESTÃO
# =============================================================================
def norte_gestao():
    st.markdown("<div class='main-title'>Norte da Minha Gestão</div>", unsafe_allow_html=True)

    with st.form("form_norte"):
        missao = st.text_area("Missão")
        visao = st.text_area("Visão")
        valores = st.text_area("Valores")
        diretrizes = st.text_area("Diretrizes Estratégicas")
        submitted = st.form_submit_button("Salvar Norte da Gestão")
        if submitted:
            st.session_state["norte_gestao"] = {
                "missao": missao,
                "visao": visao,
                "valores": valores,
                "diretrizes": diretrizes,
            }
            st.success("Norte da Gestão salvo com sucesso!")
            st.rerun()

    st.divider()
    if st.session_state["norte_gestao"]:
        norte = st.session_state["norte_gestao"]
        st.markdown(
            f"""
            <div class='card'>
                <div class='card-title'>Norte da Minha Gestão</div>
                <p><strong style='color:#22d3ee;'>Missão:</strong> {norte.get('missao', '')}</p>
                <p><strong style='color:#22d3ee;'>Visão:</strong> {norte.get('visao', '')}</p>
                <p><strong style='color:#22d3ee;'>Valores:</strong> {norte.get('valores', '')}</p>
                <p><strong style='color:#22d3ee;'>Diretrizes:</strong> {norte.get('diretrizes', '')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("Nenhum registro do Norte da Gestão cadastrado.")


# =============================================================================
# UPLOAD E BUSCA EM DOCUMENTOS
# =============================================================================
def documentos():
    st.markdown("<div class='main-title'>Upload e Busca em Documentos</div>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Envie um documento (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        st.session_state["documentos"].append({
            "nome": uploaded_file.name,
            "tipo": uploaded_file.type,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "conteudo": bytes_data,
        })
        st.success(f"Documento '{uploaded_file.name}' enviado com sucesso!")

    st.divider()
    st.markdown("<h3 style='color:#f8fafc;'>Documentos Armazenados</h3>", unsafe_allow_html=True)

    if not st.session_state["documentos"]:
        st.info("Nenhum documento armazenado.")
    else:
        termo = st.text_input("Buscar nos documentos")
        for doc in st.session_state["documentos"]:
            exibir = True
            if termo:
                if doc["tipo"] == "text/plain":
                    try:
                        texto = doc["conteudo"].decode("utf-8", errors="ignore")
                    except Exception:
                        texto = ""
                    exibir = termo.lower() in texto.lower() or termo.lower() in doc["nome"].lower()
                else:
                    exibir = termo.lower() in doc["nome"].lower()
            if exibir:
                with st.expander(f"{doc['nome']} - {doc['data']}"):
                    st.write(f"Tipo: {doc['tipo']}")
                    if doc["tipo"] == "text/plain":
                        try:
                            texto = doc["conteudo"].decode("utf-8", errors="ignore")
                            st.text_area("Conteúdo", value=texto, height=200, key=f"txt_{doc['nome']}")
                        except Exception as e:
                            st.error(f"Erro ao exibir conteúdo: {e}")
                    st.download_button(
                        label="Baixar Documento",
                        data=doc["conteudo"],
                        file_name=doc["nome"],
                        mime=doc["tipo"],
                        key=f"download_{doc['nome']}",
                    )


# =============================================================================
# MENU LATERAL
# =============================================================================
def menu_lateral():
    with st.sidebar:
        st.markdown("<div class='main-title'>🏥 MARMED</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='color:#22d3ee; font-weight:700; text-align:center;'>Usuário: {st.session_state['usuario']}</div>", unsafe_allow_html=True)
        st.divider()

        opcoes = [
            "Dashboard",
            "Cadastro de Contas",
            "Compras",
            "Superávit Financeiro",
            "Programas de Saúde",
            "Plano Municipal de Saúde",
            "Norte da Minha Gestão",
            "Documentos",
        ]
        for opcao in opcoes:
            if st.button(opcao, key=f"menu_{opcao}"):
                st.session_state["menu"] = opcao
                st.rerun()

        st.divider()
        if st.button("Sair"):
            st.session_state["autenticado"] = False
            st.session_state["usuario"] = None
            st.session_state["menu"] = "Dashboard"
            st.rerun()


# =============================================================================
# ROTEAMENTO
# =============================================================================
def main():
    aplicar_css()
    inicializar_estado()

    if not st.session_state["autenticado"]:
        tela_login()
    else:
        menu_lateral()
        opcao = st.session_state.get("menu", "Dashboard")

        if opcao == "Dashboard":
            dashboard()
        elif opcao == "Cadastro de Contas":
            cadastro_contas()
        elif opcao == "Compras":
            compras()
        elif opcao == "Superávit Financeiro":
            superavit()
        elif opcao == "Programas de Saúde":
            programas_saude()
        elif opcao == "Plano Municipal de Saúde":
            plano_municipal()
        elif opcao == "Norte da Minha Gestão":
            norte_gestao()
        elif opcao == "Documentos":
            documentos()


if __name__ == "__main__":
    main()
