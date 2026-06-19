import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Configuracao da pagina
st.set_page_config(
    page_title="Sistema de Monitoramento de Gastos Publicos",
    page_icon=":money_with_wings:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cores do tema
COR_PRIMARIA = "#1f77b4"
COR_SECUNDARIA = "#ff7f0e"
COR_SUCESSO = "#2ca02c"
COR_ALERTA = "#d62728"

# Dados de exemplo (em producao, viriam de um banco de dados ou API)
DADOS_EXEMPLO = [
    {
        "id": 1,
        "orgao": "Ministerio da Educacao",
        "resolucao": "Portaria MEC n 123/2024",
        "tipo_gasto": "Obras e Reformas",
        "politica": "Educacao Basica",
        "setor": "Educacao",
        "data": "2024-01-15",
        "fonte": "Portal da Transparencia",
        "valor": 1500000.00,
        "status": "Aprovado",
        "observacoes": "Reforma de escolas em 10 municipios."
    },
    {
        "id": 2,
        "orgao": "Ministerio da Saude",
        "resolucao": "Portaria MS n 456/2024",
        "tipo_gasto": "Aquisicao de Medicamentos",
        "politica": "Saude Publica",
        "setor": "Saude",
        "data": "2024-02-20",
        "fonte": "Comprasnet",
        "valor": 3200000.50,
        "status": "Em analise",
        "observacoes": "Aquisicao emergencial de insumos hospitalares."
    },
    {
        "id": 3,
        "orgao": "Ministerio do Transporte",
        "resolucao": "Contrato MT n 789/2024",
        "tipo_gasto": "Infraestrutura Rodoviaria",
        "politica": "Mobilidade",
        "setor": "Transporte",
        "data": "2024-03-10",
        "fonte": "Sistema de Gestao de Contratos",
        "valor": 85000000.00,
        "status": "Aprovado",
        "observacoes": "Pavimentacao de rodovia federal."
    },
    {
        "id": 4,
        "orgao": "Ministerio da Fazenda",
        "resolucao": "Resolucao CGU n 101/2024",
        "tipo_gasto": "Tecnologia da Informacao",
        "politica": "Modernizacao do Estado",
        "setor": "Administracao",
        "data": "2024-04-05",
        "fonte": "Sistema de Precos de Referencia",
        "valor": 4500000.00,
        "status": "Reprovado",
        "observacoes": "Projeto de modernizacao de sistemas legados."
    },
    {
        "id": 5,
        "orgao": "Ministerio do Meio Ambiente",
        "resolucao": "Ordinacao MMA n 202/2024",
        "tipo_gasto": "Programas de Conservacao",
        "politica": "Meio Ambiente",
        "setor": "Meio Ambiente",
        "data": "2024-05-12",
        "fonte": "Sistema de Monitoramento Orcamentario",
        "valor": 2300000.75,
        "status": "Aprovado",
        "observacoes": "Financiamento de unidades de conservacao."
    }
]


@st.cache_data(ttl=3600)
def carregar_dados():
    """Carrega os dados de gastos publicos."""
    return pd.DataFrame(DADOS_EXEMPLO)


def formatar_moeda(valor):
    """Formata um valor numerico como moeda brasileira."""
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")


def pagina_inicio(df):
    """Pagina inicial com dashboard resumido."""
    st.title(":money_with_wings: Sistema de Monitoramento de Gastos Publicos")
    st.markdown("---")

    # KPIs
    total_gasto = df["valor"].sum()
    total_registros = len(df)
    media_gasto = df["valor"].mean()
    aprovados = len(df[df["status"] == "Aprovado"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Gasto", formatar_moeda(total_gasto))
    col2.metric("Total de Registros", total_registros)
    col3.metric("Gasto Medio", formatar_moeda(media_gasto))
    col4.metric("Aprovados", aprovados)

    st.markdown("---")

    # Graficos
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("Gastos por Setor")
        df_setor = df.groupby("setor")["valor"].sum().reset_index()
        fig_setor = px.pie(
            df_setor,
            values="valor",
            names="setor",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_setor.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_setor, use_container_width=True)

    with col_graf2:
        st.subheader("Gastos por Status")
        df_status = df.groupby("status")["valor"].sum().reset_index()
        fig_status = px.bar(
            df_status,
            x="status",
            y="valor",
            color="status",
            text_auto=".2s",
            color_discrete_map={
                "Aprovado": COR_SUCESSO,
                "Em analise": COR_SECUNDARIA,
                "Reprovado": COR_ALERTA
            }
        )
        fig_status.update_layout(showlegend=False)
        st.plotly_chart(fig_status, use_container_width=True)

    st.markdown("---")

    # Ultimos registros com expander
    st.subheader("Ultimos Registros Cadastrados")
    for idx, row in df.iterrows():
        with st.expander(f"{row['orgao']} - {formatar_moeda(row['valor'])} ({row['status']})"):
            c1, c2 = st.columns(2)
            c1.markdown("<<b>Resolucao:</b> " + str(row.get("resolucao", "")))
            c1.markdown("<<b>Tipo:</b> " + str(row.get("tipo_gasto", "")))
            c1.markdown("<<b>Politica:</b> " + str(row.get("politica", "")))
            c1.markdown("<<b>Setor:</b> " + str(row.get("setor", "")))
            c1.markdown("<<b>Data:</b> " + str(row.get("data", "")))
            c1.markdown("<<b>Fonte:</b> " + str(row.get("fonte", "")))
            c2.markdown("<<b>Status:</b> " + str(row.get("status", "")))
            c2.markdown("<<b>Valor:</b> " + formatar_moeda(row.get("valor", 0)))
            c2.markdown("<<b>Observacoes:</b>")
            c2.write(str(row.get("observacoes", "")))


def pagina_consulta(df):
    """Pagina de consulta detalhada."""
    st.title(":mag: Consulta de Gastos")
    st.markdown("---")

    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)

    with col_filtro1:
        setores = ["Todos"] + sorted(df["setor"].unique().tolist())
        setor_sel = st.selectbox("Setor", setores)

    with col_filtro2:
        status_opcoes = ["Todos"] + sorted(df["status"].unique().tolist())
        status_sel = st.selectbox("Status", status_opcoes)

    with col_filtro3:
        min_val, max_val = st.slider(
            "Faixa de Valor (R$)",
            min_value=float(df["valor"].min()),
            max_value=float(df["valor"].max()),
            value=(float(df["valor"].min()), float(df["valor"].max()))
        )

    # Aplicar filtros
    df_filtrado = df.copy()
    if setor_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["setor"] == setor_sel]
    if status_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["status"] == status_sel]
    df_filtrado = df_filtrado[
        (df_filtrado["valor"] >= min_val) & (df_filtrado["valor"] <= max_val)
    ]

    st.markdown(f"**Registros encontrados:** {len(df_filtrado)}")

    # Exibir tabela
    st.dataframe(
        df_filtrado.style.format({"valor": lambda x: formatar_moeda(x)}),
        use_container_width=True,
        hide_index=True
    )

    # Grafico de evolucao temporal
    if not df_filtrado.empty:
        st.markdown("---")
        st.subheader("Evolucao Temporal dos Gastos")
        df_tempo = df_filtrado.copy()
        df_tempo["data"] = pd.to_datetime(df_tempo["data"])
        df_tempo = df_tempo.sort_values("data")
        fig_tempo = px.line(
            df_tempo,
            x="data",
            y="valor",
            color="status",
            markers=True,
            title="Gastos ao longo do tempo"
        )
        st.plotly_chart(fig_tempo, use_container_width=True)


def pagina_cadastro(df):
    """Pagina de cadastro de novos gastos."""
    st.title(":heavy_plus_sign: Cadastro de Novo Gasto")
    st.markdown("---")

    with st.form("form_cadastro"):
        col1, col2 = st.columns(2)

        with col1:
            orgao = st.text_input("Orgao")
            resolucao = st.text_input("Resolucao / Documento")
            tipo_gasto = st.selectbox(
                "Tipo de Gasto",
                [
                    "Obras e Reformas",
                    "Aquisicao de Medicamentos",
                    "Infraestrutura Rodoviaria",
                    "Tecnologia da Informacao",
                    "Programas de Conservacao",
                    "Outros"
                ]
            )
            politica = st.text_input("Politica Publica")

        with col2:
            setor = st.selectbox(
                "Setor",
                ["Educacao", "Saude", "Transporte", "Administracao", "Meio Ambiente", "Outros"]
            )
            data = st.date_input("Data", datetime.now())
            fonte = st.text_input("Fonte de Informacao")
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")

        status = st.selectbox("Status", ["Aprovado", "Em analise", "Reprovado"])
        observacoes = st.text_area("Observacoes")

        submitted = st.form_submit_button("Cadastrar")

        if submitted:
            if not orgao or not resolucao or valor <= 0:
                st.error("Preencha os campos obrigatorios: Orgao, Resolucao e Valor.")
            else:
                novo_registro = {
                    "id": df["id"].max() + 1 if not df.empty else 1,
                    "orgao": orgao,
                    "resolucao": resolucao,
                    "tipo_gasto": tipo_gasto,
                    "politica": politica,
                    "setor": setor,
                    "data": data.strftime("%Y-%m-%d"),
                    "fonte": fonte,
                    "valor": valor,
                    "status": status,
                    "observacoes": observacoes
                }
                st.session_state["dados"] = pd.concat(
                    [df, pd.DataFrame([novo_registro])], ignore_index=True
                )
                st.success("Registro cadastrado com sucesso!")
                st.balloons()


def pagina_relatorios(df):
    """Pagina de relatorios."""
    st.title(":bar_chart: Relatorios")
    st.markdown("---")

    st.subheader("Resumo por Orgao")
    df_orgao = df.groupby("orgao").agg(
        total=("valor", "sum"),
        media=("valor", "mean"),
        quantidade=("valor", "count")
    ).reset_index()
    df_orgao["total"] = df_orgao["total"].apply(formatar_moeda)
    df_orgao["media"] = df_orgao["media"].apply(formatar_moeda)
    st.dataframe(df_orgao, use_container_width=True, hide_index=True)

    st.markdown("---")

    st.subheader("Resumo por Tipo de Gasto")
    df_tipo = df.groupby("tipo_gasto").agg(
        total=("valor", "sum"),
        quantidade=("valor", "count")
    ).reset_index().sort_values("total", ascending=False)
    df_tipo["total"] = df_tipo["total"].apply(formatar_moeda)
    st.dataframe(df_tipo, use_container_width=True, hide_index=True)

    st.markdown("---")

    st.subheader("Exportar Dados")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Baixar CSV",
        data=csv,
        file_name="gastos_publicos.csv",
        mime="text/csv"
    )


def main():
    """Funcao principal do sistema."""
    # Inicializa dados na session_state
    if "dados" not in st.session_state:
        st.session_state["dados"] = carregar_dados()

    df = st.session_state["dados"]

    # Menu lateral
    st.sidebar.title(":memo: Menu")
    pagina = st.sidebar.radio(
        "Selecione a pagina:",
        ["Inicio", "Consulta", "Cadastro", "Relatorios"]
    )

    st.sidebar.markdown("---")
    st.sidebar.info(
        "Sistema desenvolvido para monitoramento e transparencia de gastos publicos."
    )

    if pagina == "Inicio":
        pagina_inicio(df)
    elif pagina == "Consulta":
        pagina_consulta(df)
    elif pagina == "Cadastro":
        pagina_cadastro(df)
    elif pagina == "Relatorios":
        pagina_relatorios(df)


if __name__ == "__main__":
    main()