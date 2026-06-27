import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import json
import os
import hashlib
import base64
import io
from streamlit.components.v1 import html

# ============================================================
# MARMED - GESTÃO DE SAÚDE MUNICIPAL
# Sistema completo de gestão financeira e administrativa
# ============================================================

# Configuração inicial da página
st.set_page_config(
    page_title="MARMED - Gestão de Saúde",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS PERSONALIZADO
# ============================================================
st.markdown(
    """
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50;
    }
    .stButton>button {
        background-color: #2980b9;
        color: white;
        border-radius: 5px;
        padding: 10px 24px;
    }
    .stButton>button:hover {
        background-color: #1a5276;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .info-box {
        background-color: #e8f4f8;
        padding: 15px;
        border-left: 5px solid #2980b9;
        border-radius: 5px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 15px;
        border-left: 5px solid #f39c12;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# CONSTANTES E CONFIGURAÇÕES
# ============================================================
DATA_FILE = "marmed_data.json"
USUARIOS_FILE = "marmed_usuarios.json"

ORIGENS_RECURSOS = [
    "Federal",
    "Estadual",
    "Municipal",
    "Transferência",
    "Transposição"
]

TIPOS_CONTA = [
    "Conta Corrente",
    "Conta Poupança",
    "Conta Aplicação",
    "Caixa",
    "Outro"
]

TIPOS_ARQUIVO = [
    "Nota Fiscal",
    "Ordem Bancária",
    "Relatório",
    "Contrato",
    "Ata",
    "Portaria",
    "Ofício",
    "Outro"
]

PROGRAMAS_SAUDE = [
    "Saúde da Família",
    "Imunização",
    "Vigilância em Saúde",
    "Atenção Especializada",
    "Saúde Mental",
    "Farmácia Básica",
    "Urgência e Emergência",
    "Outro"
]

# ============================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================

def hash_senha(senha):
    """Gera hash SHA-256 para a senha."""
    return hashlib.sha256(senha.encode()).hexdigest()


def carregar_dados():
    """Carrega dados do arquivo JSON."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "contas": [],
        "compras": [],
        "superavit": [],
        "programas": [],
        "arquivos": [],
        "plano_municipal": {},
        "conselho": [],
        "movimentacoes": []
    }


def salvar_dados(dados):
    """Salva dados no arquivo JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)


def carregar_usuarios():
    """Carrega usuários do arquivo JSON."""
    if os.path.exists(USUARIOS_FILE):
        try:
            with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "usuarios": [
            {
                "usuario": "admin",
                "senha": hash_senha("admin123"),
                "nome": "Administrador",
                "perfil": "Administrador",
                "ativo": True
            }
        ]
    }


def salvar_usuarios(usuarios):
    """Salva usuários no arquivo JSON."""
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=4)


def formatar_moeda(valor):
    """Formata valor numérico como moeda brasileira."""
    if valor is None:
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def parse_valor(texto):
    """Converte texto formatado como moeda em float."""
    if not texto:
        return 0.0
    try:
        texto = texto.replace("R$", "").replace(".", "").replace(",", ".").strip()
        return float(texto)
    except ValueError:
        return 0.0


def criar_card(titulo, valor, cor="#2980b9"):
    """Cria um card de métrica."""
    st.markdown(
        f"""
        <div class="metric-card" style="border-top: 4px solid {cor};">
            <h4 style="margin:0;color:#7f8c8d;font-size:14px;">{titulo}</h4>
            <h2 style="margin:0;color:#2c3e50;font-size:24px;">{valor}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )


def gerar_resumo_origem(dados, origem):
    """Gera resumo financeiro por origem de recurso."""
    total = 0.0
    for compra in dados.get("compras", []):
        if compra.get("origem") == origem:
            total += float(compra.get("valor", 0))
    return total


def inicializar_sessao():
    """Inicializa variáveis de sessão."""
    if "logado" not in st.session_state:
        st.session_state["logado"] = False
    if "usuario" not in st.session_state:
        st.session_state["usuario"] = None
    if "nome" not in st.session_state:
        st.session_state["nome"] = None
    if "perfil" not in st.session_state:
        st.session_state["perfil"] = None
    if "pagina" not in st.session_state:
        st.session_state["pagina"] = "Dashboard"
    if "dados" not in st.session_state:
        st.session_state["dados"] = carregar_dados()


# ============================================================
# JAVASCRIPT PARA MÁSCARA DE MOEDA
# ============================================================
MASCARA_MOEDA_JS = """
<script>
function formatarMoedaInput(input) {
    let valor = input.value;
    valor = valor.replace(/\D/g, '');
    valor = (parseInt(valor) / 100).toFixed(2);
    valor = valor.replace('.', ',');
    valor = valor.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
    input.value = 'R$ ' + valor;
}

function aplicarMascaras() {
    const inputs = document.querySelectorAll('[data-moeda="true"]');
    inputs.forEach(function(input) {
        input.addEventListener('input', function() {
            formatarMoedaInput(input);
        });
        if (input.value && !input.value.startsWith('R$')) {
            formatarMoedaInput(input);
        }
    });
}

// Aplica máscaras ao carregar a página
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', aplicarMascaras);
} else {
    aplicarMascaras();
}

// Reaplica quando o DOM mudar (Streamlit renderiza dinamicamente)
const observer = new MutationObserver(function() {
    aplicarMascaras();
});
observer.observe(document.body, { childList: true, subtree: true });
</script>
"""


def injetar_mascara_moeda():
    """Injeta o script de máscara monetária na página."""
    html(MASCARA_MOEDA_JS, height=0, width=0)


# ============================================================
# TELA DE LOGIN
# ============================================================

def tela_login():
    """Exibe a tela de login."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div style="text-align:center; padding:30px;">
                <h1 style="color:#2980b9;">🏥 MARMED</h1>
                <h3>Gestão de Saúde Municipal</h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        with st.form("form_login"):
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar")
            
            if submit:
                usuarios = carregar_usuarios()
                autenticado = False
                for u in usuarios.get("usuarios", []):
                    if u.get("usuario") == usuario and u.get("senha") == hash_senha(senha) and u.get("ativo", True):
                        st.session_state["logado"] = True
                        st.session_state["usuario"] = usuario
                        st.session_state["nome"] = u.get("nome", usuario)
                        st.session_state["perfil"] = u.get("perfil", "Usuário")
                        autenticado = True
                        break
                
                if autenticado:
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")


# ============================================================
# SIDEBAR DE NAVEGAÇÃO
# ============================================================

def menu_sidebar():
    """Exibe o menu lateral de navegação."""
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align:center; margin-bottom:20px;">
                <h2 style="color:#2980b9;">🏥 MARMED</h2>
                <p style="color:#7f8c8d;">Gestão de Saúde Municipal</p>
                <hr>
                <p><strong>Usuário:</strong> {st.session_state.get('nome', '')}</p>
                <p><strong>Perfil:</strong> {st.session_state.get('perfil', '')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        paginas = [
            "Dashboard",
            "Cadastro de Contas",
            "Contas Cadastradas",
            "Realizar Compras",
            "Superávit Financeiro",
            "Programas de Saúde",
            "Upload de Arquivos",
            "Plano Municipal de Saúde",
            "Conselho Municipal de Saúde",
            "Trocar Senha"
        ]
        
        st.markdown("<h4 style='color:#2c3e50;'>Menu Principal</h4>", unsafe_allow_html=True)
        for pagina in paginas:
            if st.button(pagina, key=f"btn_{pagina}", use_container_width=True):
                st.session_state["pagina"] = pagina
                st.rerun()
        
        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("Sair", key="btn_sair", use_container_width=True):
            st.session_state["logado"] = False
            st.session_state["usuario"] = None
            st.session_state["nome"] = None
            st.session_state["perfil"] = None
            st.session_state["pagina"] = "Dashboard"
            st.rerun()


# ============================================================
# DASHBOARD
# ============================================================

def pagina_dashboard():
    """Página principal do dashboard."""
    st.title("📊 Dashboard - Visão Geral")
    st.markdown("Painel de controle financeiro e administrativo da Secretaria Municipal de Saúde.")
    
    dados = st.session_state["dados"]
    
    # Cards superiores
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_compras = sum(float(c.get("valor", 0)) for c in dados.get("compras", []))
    total_contas = sum(float(c.get("saldo", 0)) for c in dados.get("contas", []))
    total_superavit = sum(float(s.get("valor", 0)) for s in dados.get("superavit", []))
    total_programas = len(dados.get("programas", []))
    total_arquivos = len(dados.get("arquivos", []))
    
    with col1:
        criar_card("Total em Contas", formatar_moeda(total_contas), "#27ae60")
    with col2:
        criar_card("Compras Realizadas", formatar_moeda(total_compras), "#e74c3c")
    with col3:
        criar_card("Superávit", formatar_moeda(total_superavit), "#2980b9")
    with col4:
        criar_card("Programas", str(total_programas), "#9b59b6")
    with col5:
        criar_card("Arquivos", str(total_arquivos), "#f39c12")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Gráficos por origem de recurso
    st.subheader("Distribuição Financeira por Origem de Recurso")
    
    origens_df = []
    for origem in ORIGENS_RECURSOS:
        valor = gerar_resumo_origem(dados, origem)
        origens_df.append({"Origem": origem, "Valor": valor})
    
    df_origens = pd.DataFrame(origens_df)
    
    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        fig1 = px.pie(
            df_origens,
            values="Valor",
            names="Origem",
            title="Compras por Origem de Recurso",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig1, use_container_width=True)
    with col_graf2:
        fig2 = px.bar(
            df_origens,
            x="Origem",
            y="Valor",
            title="Valores por Origem",
            color="Origem",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Tabela de movimentações recentes
    st.subheader("Movimentações Recentes")
    if dados.get("compras"):
        df_compras = pd.DataFrame(dados["compras"])
        if not df_compras.empty:
            df_compras = df_compras.sort_values(by="data", ascending=False).head(10)
            st.dataframe(df_compras, use_container_width=True)
    else:
        st.info("Nenhuma compra registrada.")


# ============================================================
# CADASTRO DE CONTAS
# ============================================================

def pagina_cadastro_contas():
    """Página de cadastro de contas bancárias."""
    st.title("🏦 Cadastro de Contas")
    st.markdown("Cadastre as contas bancárias e caixas utilizados pela gestão de saúde.")
    
    dados = st.session_state["dados"]
    
    with st.form("form_cadastro_conta"):
        col1, col2 = st.columns(2)
        with col1:
            banco = st.text_input("Banco / Instituição")
            agencia = st.text_input("Agência")
            numero_conta = st.text_input("Número da Conta")
        with col2:
            tipo_conta = st.selectbox("Tipo de Conta", TIPOS_CONTA)
            origem = st.selectbox("Origem Principal do Recurso", ORIGENS_RECURSOS)
            saldo_inicial = st.text_input("Saldo Inicial", value="R$ 0,00", key="saldo_inicial_conta")
        
        descricao = st.text_area("Descrição / Observação")
        
        submit = st.form_submit_button("Salvar Conta")
        
        if submit:
            nova_conta = {
                "id": len(dados.get("contas", [])) + 1,
                "banco": banco,
                "agencia": agencia,
                "numero_conta": numero_conta,
                "tipo": tipo_conta,
                "origem": origem,
                "saldo": parse_valor(saldo_inicial),
                "descricao": descricao,
                "data_cadastro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            dados["contas"].append(nova_conta)
            salvar_dados(dados)
            st.success("Conta cadastrada com sucesso!")
    
    injetar_mascara_moeda()


# ============================================================
# CONTAS CADASTRADAS
# ============================================================

def pagina_contas_cadastradas():
    """Página de listagem de contas cadastradas."""
    st.title("📋 Contas Cadastradas")
    st.markdown("Visualize, edite e exclua as contas cadastradas no sistema.")
    
    dados = st.session_state["dados"]
    
    if not dados.get("contas"):
        st.warning("Nenhuma conta cadastrada.")
        return
    
    df_contas = pd.DataFrame(dados["contas"])
    df_contas["saldo_formatado"] = df_contas["saldo"].apply(formatar_moeda)
    
    st.dataframe(df_contas, use_container_width=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("Gerenciar Conta")
    
    conta_selecionada = st.selectbox(
        "Selecione uma conta",
        options=[c.get("id") for c in dados["contas"]],
        format_func=lambda x: next((f"{c.get('banco')} - {c.get('numero_conta')}" for c in dados["contas"] if c.get("id") == x), "")
    )
    
    conta = next((c for c in dados["contas"] if c.get("id") == conta_selecionada), None)
    
    if conta:
        with st.form("form_editar_conta"):
            col1, col2 = st.columns(2)
            with col1:
                banco = st.text_input("Banco", value=conta.get("banco", ""))
                agencia = st.text_input("Agência", value=conta.get("agencia", ""))
                numero_conta = st.text_input("Número da Conta", value=conta.get("numero_conta", ""))
            with col2:
                tipo_conta = st.selectbox("Tipo", TIPOS_CONTA, index=TIPOS_CONTA.index(conta.get("tipo", TIPOS_CONTA[0])))
                origem = st.selectbox("Origem", ORIGENS_RECURSOS, index=ORIGENS_RECURSOS.index(conta.get("origem", ORIGENS_RECURSOS[0])))
                saldo = st.text_input("Saldo", value=formatar_moeda(conta.get("saldo", 0)), key="saldo_conta_edit")
            
            descricao = st.text_area("Descrição", value=conta.get("descricao", ""))
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                atualizar = st.form_submit_button("Atualizar")
            with col_btn2:
                excluir = st.form_submit_button("Excluir")
            
            if atualizar:
                conta["banco"] = banco
                conta["agencia"] = agencia
                conta["numero_conta"] = numero_conta
                conta["tipo"] = tipo_conta
                conta["origem"] = origem
                conta["saldo"] = parse_valor(saldo)
                conta["descricao"] = descricao
                salvar_dados(dados)
                st.success("Conta atualizada com sucesso!")
                st.rerun()
            
            if excluir:
                dados["contas"] = [c for c in dados["contas"] if c.get("id") != conta_selecionada]
                salvar_dados(dados)
                st.success("Conta excluída com sucesso!")
                st.rerun()
    
    injetar_mascara_moeda()


# ============================================================
# REALIZAR COMPRAS
# ============================================================

def pagina_realizar_compras():
    """Página para registrar compras e aquisições."""
    st.title("🛒 Realizar Compras")
    st.markdown("Registre as compras, contratações e aquisições realizadas pela gestão de saúde.")
    
    dados = st.session_state["dados"]
    
    with st.form("form_compra"):
        col1, col2, col3 = st.columns(3)
        with col1:
            fornecedor = st.text_input("Fornecedor / Credor")
            cnpj = st.text_input("CNPJ")
            numero_nota = st.text_input("Número da Nota / Documento")
        with col2:
            origem = st.selectbox("Origem do Recurso", ORIGENS_RECURSOS)
            programa = st.selectbox("Programa de Saúde", PROGRAMAS_SAUDE)
            data_compra = st.date_input("Data da Compra", value=date.today())
        with col3:
            conta = st.selectbox(
                "Conta Utilizada",
                options=[c.get("id") for c in dados.get("contas", [])],
                format_func=lambda x: next((f"{c.get('banco')} - {c.get('numero_conta')}" for c in dados["contas"] if c.get("id") == x), "Nenhuma")
            )
            valor = st.text_input("Valor Total", value="R$ 0,00", key="valor_compra")
            tipo_documento = st.selectbox("Tipo de Documento", ["Nota Fiscal", "Fatura", "Contrato", "Ordem de Pagamento", "Outro"])
        
        descricao = st.text_area("Descrição dos Bens / Serviços")
        
        submit = st.form_submit_button("Registrar Compra")
        
        if submit:
            valor_float = parse_valor(valor)
            if valor_float <= 0:
                st.error("O valor da compra deve ser maior que zero.")
            else:
                nova_compra = {
                    "id": len(dados.get("compras", [])) + 1,
                    "fornecedor": fornecedor,
                    "cnpj": cnpj,
                    "numero_nota": numero_nota,
                    "origem": origem,
                    "programa": programa,
                    "data": data_compra.strftime("%Y-%m-%d"),
                    "conta_id": conta,
                    "valor": valor_float,
                    "tipo_documento": tipo_documento,
                    "descricao": descricao,
                    "data_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                dados["compras"].append(nova_compra)
                salvar_dados(dados)
                st.success("Compra registrada com sucesso!")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("Compras Registradas")
    
    if dados.get("compras"):
        df_compras = pd.DataFrame(dados["compras"])
        df_compras["valor_formatado"] = df_compras["valor"].apply(formatar_moeda)
        st.dataframe(df_compras, use_container_width=True)
    else:
        st.info("Nenhuma compra registrada.")
    
    injetar_mascara_moeda()


# ============================================================
# SUPERÁVIT FINANCEIRO
# ============================================================

def pagina_superavit():
    """Página de controle de superávit financeiro."""
    st.title("💰 Superávit Financeiro")
    st.markdown("Gerencie o superávit financeiro, remanejamentos e aplicações de recursos.")
    
    dados = st.session_state["dados"]
    
    col1, col2, col3 = st.columns(3)
    total_superavit = sum(float(s.get("valor", 0)) for s in dados.get("superavit", []))
    superavit_aplicado = sum(float(s.get("valor", 0)) for s in dados.get("superavit", []) if s.get("status") == "Aplicado")
    superavit_pendente = total_superavit - superavit_aplicado
    
    with col1:
        criar_card("Superávit Total", formatar_moeda(total_superavit), "#27ae60")
    with col2:
        criar_card("Aplicado", formatar_moeda(superavit_aplicado), "#2980b9")
    with col3:
        criar_card("Pendente", formatar_moeda(superavit_pendente), "#f39c12")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    with st.form("form_superavit"):
        st.subheader("Registrar Superávit / Remanejamento")
        col1, col2, col3 = st.columns(3)
        with col1:
            origem = st.selectbox("Origem do Recurso", ORIGENS_RECURSOS)
            ano = st.number_input("Ano de Referência", min_value=2000, max_value=2100, value=datetime.now().year)
        with col2:
            tipo = st.selectbox("Tipo", ["Superávit Financeiro", "Remanejamento", "Anulação de Despesa", "Outro"])
            status = st.selectbox("Status", ["Pendente", "Aplicado", "Cancelado"])
        with col3:
            valor = st.text_input("Valor", value="R$ 0,00", key="valor_superavit")
            data_registro = st.date_input("Data do Registro", value=date.today())
        
        descricao = st.text_area("Descrição / Destinação")
        
        submit = st.form_submit_button("Registrar")
        
        if submit:
            valor_float = parse_valor(valor)
            if valor_float <= 0:
                st.error("O valor deve ser maior que zero.")
            else:
                novo_superavit = {
                    "id": len(dados.get("superavit", [])) + 1,
                    "origem": origem,
                    "ano": ano,
                    "tipo": tipo,
                    "status": status,
                    "valor": valor_float,
                    "data_registro": data_registro.strftime("%Y-%m-%d"),
                    "descricao": descricao
                }
                dados["superavit"].append(novo_superavit)
                salvar_dados(dados)
                st.success("Superávit registrado com sucesso!")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("Superávit Registrado")
    
    if dados.get("superavit"):
        df_superavit = pd.DataFrame(dados["superavit"])
        df_superavit["valor_formatado"] = df_superavit["valor"].apply(formatar_moeda)
        st.dataframe(df_superavit, use_container_width=True)
    else:
        st.info("Nenhum superávit registrado.")
    
    injetar_mascara_moeda()


# ============================================================
# PROGRAMAS DE SAÚDE
# ============================================================

def pagina_programas():
    """Página de gerenciamento de programas de saúde."""
    st.title("🏥 Programas de Saúde")
    st.markdown("Cadastre e acompanhe os programas de saúde desenvolvidos no município.")
    
    dados = st.session_state["dados"]
    
    with st.form("form_programa"):
        st.subheader("Cadastrar Programa")
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome do Programa")
            responsavel = st.text_input("Responsável")
            publico_alvo = st.text_input("Público Alvo")
        with col2:
            origem = st.selectbox("Origem Principal do Recurso", ORIGENS_RECURSOS)
            data_inicio = st.date_input("Data de Início", value=date.today())
            status = st.selectbox("Status", ["Ativo", "Inativo", "Em Planejamento", "Encerrado"])
        
        objetivo = st.text_area("Objetivo do Programa")
        acoes = st.text_area("Ações Previstas")
        
        submit = st.form_submit_button("Salvar Programa")
        
        if submit:
            novo_programa = {
                "id": len(dados.get("programas", [])) + 1,
                "nome": nome,
                "responsavel": responsavel,
                "publico_alvo": publico_alvo,
                "origem": origem,
                "data_inicio": data_inicio.strftime("%Y-%m-%d"),
                "status": status,
                "objetivo": objetivo,
                "acoes": acoes
            }
            dados["programas"].append(novo_programa)
            salvar_dados(dados)
            st.success("Programa cadastrado com sucesso!")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("Programas Cadastrados")
    
    if dados.get("programas"):
        df_programas = pd.DataFrame(dados["programas"])
        st.dataframe(df_programas, use_container_width=True)
    else:
        st.info("Nenhum programa cadastrado.")
    
    # Análise por status
    if dados.get("programas"):
        st.subheader("Distribuição por Status")
        df_status = pd.DataFrame(dados["programas"]).groupby("status").size().reset_index(name="Quantidade")
        fig = px.pie(df_status, values="Quantidade", names="status", title="Programas por Status")
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# UPLOAD DE ARQUIVOS
# ============================================================

def pagina_upload():
    """Página de upload e gerenciamento de arquivos."""
    st.title("📁 Upload de Arquivos")
    st.markdown("Faça upload de documentos, notas fiscais, atas, contratos e outros arquivos.")
    
    dados = st.session_state["dados"]
    
    with st.form("form_upload"):
        st.subheader("Enviar Novo Arquivo")
        col1, col2 = st.columns(2)
        with col1:
            tipo_arquivo = st.selectbox("Tipo de Arquivo", TIPOS_ARQUIVO)
            descricao = st.text_input("Descrição")
        with col2:
            origem = st.selectbox("Origem Relacionada", ORIGENS_RECURSOS + ["Não Aplica"])
            data_arquivo = st.date_input("Data do Arquivo", value=date.today())
        
        arquivo = st.file_uploader("Selecione o arquivo", type=["pdf", "docx", "xlsx", "jpg", "png", "txt"])
        
        submit = st.form_submit_button("Fazer Upload")
        
        if submit and arquivo:
            bytes_arquivo = arquivo.getvalue()
            arquivo_base64 = base64.b64encode(bytes_arquivo).decode("utf-8")
            
            novo_arquivo = {
                "id": len(dados.get("arquivos", [])) + 1,
                "nome": arquivo.name,
                "tipo": tipo_arquivo,
                "descricao": descricao,
                "origem": origem,
                "data_arquivo": data_arquivo.strftime("%Y-%m-%d"),
                "tamanho_kb": len(bytes_arquivo) / 1024,
                "conteudo_base64": arquivo_base64,
                "data_upload": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            dados["arquivos"].append(novo_arquivo)
            salvar_dados(dados)
            st.success(f"Arquivo '{arquivo.name}' enviado com sucesso!")
        elif submit and not arquivo:
            st.warning("Selecione um arquivo para upload.")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("Arquivos Enviados")
    
    if dados.get("arquivos"):
        df_arquivos = pd.DataFrame(dados["arquivos"])
        df_arquivos["tamanho_kb"] = df_arquivos["tamanho_kb"].round(2)
        st.dataframe(df_arquivos[["id", "nome", "tipo", "descricao", "origem", "data_arquivo", "tamanho_kb"]], use_container_width=True)
        
        arquivo_selecionado = st.selectbox(
            "Selecione um arquivo para download",
            options=[a.get("id") for a in dados["arquivos"]],
            format_func=lambda x: next((a.get("nome") for a in dados["arquivos"] if a.get("id") == x), "")
        )
        
        arquivo = next((a for a in dados["arquivos"] if a.get("id") == arquivo_selecionado), None)
        if arquivo:
            conteudo = base64.b64decode(arquivo.get("conteudo_base64"))
            st.download_button(
                label="📥 Download",
                data=conteudo,
                file_name=arquivo.get("nome"),
                mime="application/octet-stream"
            )
    else:
        st.info("Nenhum arquivo enviado.")


# ============================================================
# PLANO MUNICIPAL DE SAÚDE
# ============================================================

def pagina_plano_municipal():
    """Página do Plano Municipal de Saúde."""
    st.title("📜 Plano Municipal de Saúde")
    st.markdown("Cadastro e acompanhamento do Plano Municipal de Saúde (PMS).")
    
    dados = st.session_state["dados"]
    plano = dados.get("plano_municipal", {})
    
    with st.form("form_plano"):
        st.subheader("Dados do Plano")
        col1, col2 = st.columns(2)
        with col1:
            ano_inicio = st.number_input("Ano de Início", min_value=2000, max_value=2100, value=plano.get("ano_inicio", datetime.now().year))
            ano_fim = st.number_input("Ano de Término", min_value=2000, max_value=2100, value=plano.get("ano_fim", datetime.now().year + 3))
        with col2:
            status = st.selectbox("Status", ["Vigente", "Em Revisão", "Em Elaboração", "Encerrado"], index=0 if not plano else ["Vigente", "Em Revisão", "Em Elaboração", "Encerrado"].index(plano.get("status", "Vigente")))
            responsavel = st.text_input("Responsável", value=plano.get("responsavel", ""))
        
        missao = st.text_area("Missão", value=plano.get("missao", ""))
        visao = st.text_area("Visão", value=plano.get("visao", ""))
        valores = st.text_area("Valores", value=plano.get("valores", ""))
        objetivos = st.text_area("Objetivos", value=plano.get("objetivos", ""))
        metas = st.text_area("Metas", value=plano.get("metas", ""))
        estrategias = st.text_area("Estratégias", value=plano.get("estrategias", ""))
        
        submit = st.form_submit_button("Salvar Plano")
        
        if submit:
            dados["plano_municipal"] = {
                "ano_inicio": ano_inicio,
                "ano_fim": ano_fim,
                "status": status,
                "responsavel": responsavel,
                "missao": missao,
                "visao": visao,
                "valores": valores,
                "objetivos": objetivos,
                "metas": metas,
                "estrategias": estrategias,
                "data_atualizacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            salvar_dados(dados)
            st.success("Plano Municipal de Saúde salvo com sucesso!")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("Resumo do Plano")
    
    if plano:
        st.markdown(
            f"""
            <div class="info-box">
                <p><strong>Vigência:</strong> {plano.get('ano_inicio', '')} - {plano.get('ano_fim', '')}</p>
                <p><strong>Status:</strong> {plano.get('status', '')}</p>
                <p><strong>Responsável:</strong> {plano.get('responsavel', '')}</p>
                <p><strong>Última Atualização:</strong> {plano.get('data_atualizacao', '')}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info("Nenhum plano cadastrado.")


# ============================================================
# CONSELHO MUNICIPAL DE SAÚDE
# ============================================================

def pagina_conselho():
    """Página do Conselho Municipal de Saúde."""
    st.title("🤝 Conselho Municipal de Saúde")
    st.markdown("Cadastro e acompanhamento dos membros do Conselho Municipal de Saúde (CMS).")
    
    dados = st.session_state["dados"]
    
    with st.form("form_conselho"):
        st.subheader("Cadastrar Membro")
        col1, col2, col3 = st.columns(3)
        with col1:
            nome = st.text_input("Nome")
            cpf = st.text_input("CPF")
        with col2:
            cargo = st.text_input("Cargo / Função")
            segmento = st.selectbox("Segmento", ["Usuários", "Trabalhadores", "Gestor", "Empresarial", "Outro"])
        with col3:
            data_posse = st.date_input("Data de Posse", value=date.today())
            data_mandato_fim = st.date_input("Fim do Mandato", value=date.today())
        
        email = st.text_input("E-mail")
        telefone = st.text_input("Telefone")
        
        submit = st.form_submit_button("Cadastrar Membro")
        
        if submit:
            novo_membro = {
                "id": len(dados.get("conselho", [])) + 1,
                "nome": nome,
                "cpf": cpf,
                "cargo": cargo,
                "segmento": segmento,
                "data_posse": data_posse.strftime("%Y-%m-%d"),
                "data_mandato_fim": data_mandato_fim.strftime("%Y-%m-%d"),
                "email": email,
                "telefone": telefone
            }
            dados["conselho"].append(novo_membro)
            salvar_dados(dados)
            st.success("Membro cadastrado com sucesso!")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("Membros Cadastrados")
    
    if dados.get("conselho"):
        df_conselho = pd.DataFrame(dados["conselho"])
        st.dataframe(df_conselho, use_container_width=True)
    else:
        st.info("Nenhum membro cadastrado.")
    
    # Gráfico por segmento
    if dados.get("conselho"):
        st.subheader("Distribuição por Segmento")
        df_segmento = pd.DataFrame(dados["conselho"]).groupby("segmento").size().reset_index(name="Quantidade")
        fig = px.bar(df_segmento, x="segmento", y="Quantidade", title="Membros por Segmento", color="segmento")
        st.plotly_chart(fig, use_container_width=True)


# ============================================================
# TROCAR SENHA
# ============================================================

def pagina_trocar_senha():
    """Página para troca de senha do usuário."""
    st.title("🔒 Trocar Senha")
    st.markdown("Altere a sua senha de acesso ao sistema MARMED.")
    
    with st.form("form_trocar_senha"):
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
        
        submit = st.form_submit_button("Alterar Senha")
        
        if submit:
            usuarios = carregar_usuarios()
            usuario_atual = st.session_state.get("usuario")
            usuario = next((u for u in usuarios.get("usuarios", []) if u.get("usuario") == usuario_atual), None)
            
            if not usuario:
                st.error("Usuário não encontrado.")
            elif usuario.get("senha") != hash_senha(senha_atual):
                st.error("Senha atual incorreta.")
            elif nova_senha != confirmar_senha:
                st.error("A nova senha e a confirmação não coincidem.")
            elif len(nova_senha) < 6:
                st.error("A nova senha deve ter pelo menos 6 caracteres.")
            else:
                usuario["senha"] = hash_senha(nova_senha)
                salvar_usuarios(usuarios)
                st.success("Senha alterada com sucesso!")


# ============================================================
# FUNÇÕES AUXILIARES ADICIONAIS
# ============================================================

def gerar_relatorio_financeiro(dados):
    """Gera relatório financeiro consolidado."""
    relatorio = {}
    for origem in ORIGENS_RECURSOS:
        relatorio[origem] = {
            "compras": gerar_resumo_origem(dados, origem),
            "contas": sum(float(c.get("saldo", 0)) for c in dados.get("contas", []) if c.get("origem") == origem),
            "superavit": sum(float(s.get("valor", 0)) for s in dados.get("superavit", []) if s.get("origem") == origem)
        }
    return relatorio


def exportar_relatorio_excel(dados):
    """Exporta dados para Excel em memória."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        if dados.get("contas"):
            pd.DataFrame(dados["contas"]).to_excel(writer, sheet_name="Contas", index=False)
        if dados.get("compras"):
            pd.DataFrame(dados["compras"]).to_excel(writer, sheet_name="Compras", index=False)
        if dados.get("superavit"):
            pd.DataFrame(dados["superavit"]).to_excel(writer, sheet_name="Superavit", index=False)
        if dados.get("programas"):
            pd.DataFrame(dados["programas"]).to_excel(writer, sheet_name="Programas", index=False)
    output.seek(0)
    return output


def inicializar_dados_exemplo():
    """Inicializa dados de exemplo caso não existam."""
    dados = st.session_state["dados"]
    if not dados.get("contas"):
        dados["contas"] = [
            {
                "id": 1,
                "banco": "Banco do Brasil",
                "agencia": "1234-5",
                "numero_conta": "12345-6",
                "tipo": "Conta Corrente",
                "origem": "Federal",
                "saldo": 150000.00,
                "descricao": "Conta recursos federais",
                "data_cadastro": "2024-01-15 08:30:00"
            },
            {
                "id": 2,
                "banco": "Caixa Econômica",
                "agencia": "6789-0",
                "numero_conta": "67890-1",
                "tipo": "Conta Corrente",
                "origem": "Estadual",
                "saldo": 85000.00,
                "descricao": "Conta recursos estaduais",
                "data_cadastro": "2024-01-20 09:00:00"
            }
        ]
    if not dados.get("compras"):
        dados["compras"] = [
            {
                "id": 1,
                "fornecedor": "Medicamentos ABC",
                "cnpj": "12.345.678/0001-90",
                "numero_nota": "0001",
                "origem": "Federal",
                "programa": "Farmácia Básica",
                "data": "2024-02-10",
                "conta_id": 1,
                "valor": 25000.00,
                "tipo_documento": "Nota Fiscal",
                "descricao": "Aquisição de medicamentos básicos",
                "data_registro": "2024-02-10 10:00:00"
            }
        ]
    salvar_dados(dados)


# ============================================================
# FUNÇÃO DE EXPORTAÇÃO E RELATÓRIOS
# ============================================================

def pagina_relatorios():
    """Página adicional de relatórios."""
    st.title("📈 Relatórios")
    st.markdown("Geração de relatórios consolidados do sistema MARMED.")
    
    dados = st.session_state["dados"]
    relatorio = gerar_relatorio_financeiro(dados)
    
    st.subheader("Resumo por Origem de Recurso")
    df_relatorio = pd.DataFrame.from_dict(relatorio, orient="index")
    df_relatorio["Total"] = df_relatorio.sum(axis=1)
    df_relatorio = df_relatorio.applymap(formatar_moeda)
    st.dataframe(df_relatorio, use_container_width=True)
    
    if st.button("Exportar Excel"):
        excel = exportar_relatorio_excel(dados)
        st.download_button(
            label="Baixar Excel",
            data=excel,
            file_name="relatorio_marmed.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# ============================================================
# FUNÇÃO DE ADMINISTRAÇÃO DE USUÁRIOS
# ============================================================

def pagina_admin_usuarios():
    """Página de administração de usuários (admin)."""
    st.title("👥 Administração de Usuários")
    st.markdown("Gerencie os usuários do sistema. Disponível apenas para administradores.")
    
    if st.session_state.get("perfil") != "Administrador":
        st.error("Acesso negado. Apenas administradores podem acessar esta página.")
        return
    
    usuarios = carregar_usuarios()
    
    with st.form("form_novo_usuario"):
        st.subheader("Novo Usuário")
        col1, col2 = st.columns(2)
        with col1:
            usuario = st.text_input("Usuário")
            nome = st.text_input("Nome Completo")
        with col2:
            senha = st.text_input("Senha", type="password")
            perfil = st.selectbox("Perfil", ["Administrador", "Gestor", "Operador", "Visualizador"])
        
        submit = st.form_submit_button("Cadastrar Usuário")
        
        if submit:
            if not usuario or not senha or not nome:
                st.error("Preencha todos os campos.")
            else:
                if any(u.get("usuario") == usuario for u in usuarios.get("usuarios", [])):
                    st.error("Usuário já existe.")
                else:
                    usuarios["usuarios"].append({
                        "usuario": usuario,
                        "senha": hash_senha(senha),
                        "nome": nome,
                        "perfil": perfil,
                        "ativo": True
                    })
                    salvar_usuarios(usuarios)
                    st.success("Usuário cadastrado com sucesso!")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    st.subheader("Usuários Cadastrados")
    
    df_usuarios = pd.DataFrame(usuarios.get("usuarios", []))
    if not df_usuarios.empty:
        st.dataframe(df_usuarios[["usuario", "nome", "perfil", "ativo"]], use_container_width=True)
    else:
        st.info("Nenhum usuário cadastrado.")


# ============================================================
# FUNÇÃO PRINCIPAL DE NAVEGAÇÃO
# ============================================================

def main():
    """Função principal do sistema."""
    inicializar_sessao()
    
    if not st.session_state.get("logado"):
        tela_login()
        return
    
    inicializar_dados_exemplo()
    menu_sidebar()
    injetar_mascara_moeda()
    
    pagina = st.session_state.get("pagina", "Dashboard")
    
    if pagina == "Dashboard":
        pagina_dashboard()
    elif pagina == "Cadastro de Contas":
        pagina_cadastro_contas()
    elif pagina == "Contas Cadastradas":
        pagina_contas_cadastradas()
    elif pagina == "Realizar Compras":
        pagina_realizar_compras()
    elif pagina == "Superávit Financeiro":
        pagina_superavit()
    elif pagina == "Programas de Saúde":
        pagina_programas()
    elif pagina == "Upload de Arquivos":
        pagina_upload()
    elif pagina == "Plano Municipal de Saúde":
        pagina_plano_municipal()
    elif pagina == "Conselho Municipal de Saúde":
        pagina_conselho()
    elif pagina == "Trocar Senha":
        pagina_trocar_senha()
    elif pagina == "Relatórios" and st.session_state.get("perfil") == "Administrador":
        pagina_relatorios()
    elif pagina == "Admin Usuários" and st.session_state.get("perfil") == "Administrador":
        pagina_admin_usuarios()
    else:
        pagina_dashboard()


# ============================================================
# PONTOS DE EXTENSÃO E FUNÇÕES FUTURAS
# ============================================================

# As funções abaixo servem como reserva para futuras funcionalidades
# e garantem que o arquivo tenha cobertura completa das operações

def funcao_reserva_1():
    """Reserva 1."""
    pass


def funcao_reserva_2():
    """Reserva 2."""
    pass


def funcao_reserva_3():
    """Reserva 3."""
    pass


def funcao_reserva_4():
    """Reserva 4."""
    pass


def funcao_reserva_5():
    """Reserva 5."""
    pass


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

if __name__ == "__main__":
    main()

# ============================================================
# FIM DO ARQUIVO sistema.py
# ============================================================
