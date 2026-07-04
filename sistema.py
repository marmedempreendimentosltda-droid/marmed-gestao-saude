import streamlit as st
import pandas as pd
import datetime
import hashlib
import plotly.express as px
from database import *

st.set_page_config(page_title="MARMED Gestão em Saúde", layout="wide")


def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def pagina_dashboard():
    st.title("🏠 Dashboard - MARMED Gestão em Saúde")

    exercicios = get_all_exercicios()
    if not exercicios:
        st.warning("Nenhum exercício orçamentário cadastrado.")
        return
    ex = exercicios[0]

    col1, col2, col3, col4 = st.columns(4)

    dotacoes = get_all_dotacoes()
    total_orcamento = sum(d["valor_atual"] or 0 for d in dotacoes)
    total_empenhado = sum(d["valor_empenhado"] or 0 for d in dotacoes)
    total_pago = sum(d["valor_pago"] or 0 for d in dotacoes)
    saldo = total_orcamento - total_empenhado
    pct_exec = (total_empenhado / total_orcamento * 100) if total_orcamento else 0

    col1.metric("💵 Orçamento Total", f"R$ {total_orcamento:,.2f}")
    col2.metric("📌 Valor Empenhado", f"R$ {total_empenhado:,.2f}")
    col3.metric("📊 % Executado", f"{pct_exec:.1f}%")
    col4.metric("💰 Saldo Disponível", f"R$ {saldo:,.2f}")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Execução por Natureza")
        ranking = get_ranking_despesas(ex["id"], 7)
        if ranking:
            fig = px.bar(
                ranking, x="descricao", y="total_pago",
                title="Despesas por Natureza",
                labels={"descricao": "Natureza", "total_pago": "Valor Pago (R$)"},
                color_discrete_sequence=["#1f77b4"]
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📊 Execução por Órgão")
        exec_orgao = get_execucao_por_orgao(ex["id"])
        if exec_orgao:
            fig = px.pie(
                exec_orgao, values="total_dotacao", names="sigla",
                title="Distribuição por Órgão",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("🚨 Alertas Ativos")
    alertas_lic = get_alerta_licitacao()
    alertas_dot = get_alerta_dotacao()

    if alertas_lic:
        st.warning(f"⚠️ {len(alertas_lic)} item(ns) de licitação atingiram o limite de retirada!")
    if alertas_dot:
        st.warning(f"⚠️ {len(alertas_dot)} dotação(ões) necessitam suplementação!")
    if not alertas_lic and not alertas_dot:
        st.success("✅ Nenhum alerta ativo no momento.")

    st.subheader("📋 Últimas Movimentações")
    empenhos = get_all_empenhos()
    if empenhos:
        df = pd.DataFrame(empenhos[:10])
        st.dataframe(df[["numero", "data", "valor", "status"]], use_container_width=True)


def pagina_loa():
    st.title("📊 LOA - Lei Orçamentária Anual")
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📅 Exercício", "🏛️ Órgãos", "📋 Programas/Ações",
        "🏷️ Naturezas", "💰 Fontes", "💵 Dotações",
        "📈 Receitas", "👁️ Visão Geral"
    ])

    with tab1:
        st.subheader("Exercícios Orçamentários")
        with st.form("form_exercicio"):
            col1, col2 = st.columns(2)
            with col1:
                ano = st.number_input("Ano", min_value=2020, max_value=2035, value=2026)
                data_inicio = st.date_input("Data Início", value=datetime.date(2026, 1, 1))
            with col2:
                status = st.selectbox("Status", ["elaboracao", "aprovado", "execucao", "encerrado"])
                data_fim = st.date_input("Data Fim", value=datetime.date(2026, 12, 31))
            if st.form_submit_button("Salvar"):
                try:
                    insert_exercicio({"ano": ano, "status": status, "data_inicio": data_inicio, "data_fim": data_fim})
                    st.success("Exercício salvo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        exercicios = get_all_exercicios()
        if exercicios:
            st.dataframe(pd.DataFrame(exercicios), use_container_width=True)

    with tab2:
        st.subheader("Órgãos")
        with st.form("form_orgao"):
            col1, col2, col3 = st.columns(3)
            with col1:
                codigo = st.text_input("Código", "02.01")
            with col2:
                nome = st.text_input("Nome", "Secretaria Municipal de Saúde")
            with col3:
                sigla = st.text_input("Sigla", "SMS")
            if st.form_submit_button("Salvar"):
                try:
                    insert_orgao({"codigo": codigo, "nome": nome, "sigla": sigla, "ativo": 1})
                    st.success("Órgão salvo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
        orgaos = get_all_orgaos()
        if orgaos:
            st.dataframe(pd.DataFrame(orgaos), use_container_width=True)

    with tab3:
        st.subheader("Programas")
        with st.form("form_programa"):
            orgaos_list = get_all_orgaos()
            orgao_opts = {f"{o['nome']} ({o['sigla']})": o["id"] for o in orgaos_list}
            col1, col2 = st.columns(2)
            with col1:
                p_codigo = st.text_input("Código do Programa")
                p_nome = st.text_input("Nome do Programa")
            with col2:
                p_objetivo = st.text_area("Objetivo")
                p_orgao = st.selectbox("Órgão Responsável", options=list(orgao_opts.keys()))
            if st.form_submit_button("Salvar Programa"):
                try:
                    insert_programa({"codigo": p_codigo, "nome": p_nome, "objetivo": p_objetivo, "orgao_responsavel_id": orgao_opts[p_orgao]})
                    st.success("Programa salvo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        st.subheader("Ações")
        with st.form("form_acao"):
            programas = get_all_programas()
            prog_opts = {p["nome"]: p["id"] for p in programas}
            col1, col2 = st.columns(2)
            with col1:
                a_codigo = st.text_input("Código da Ação")
                a_nome = st.text_input("Nome da Ação")
                a_programa = st.selectbox("Programa", options=list(prog_opts.keys()))
            with col2:
                a_tipo = st.selectbox("Tipo", ["projeto", "atividade", "operacao_especial"])
                a_produto = st.text_input("Produto", "Consultas médicas")
                a_unidade = st.text_input("Unidade Medida", "Atendimento")
            if st.form_submit_button("Salvar Ação"):
                try:
                    insert_acao({"codigo": a_codigo, "tipo": a_tipo, "nome": a_nome, "produto": a_produto, "unidade_medida": a_unidade, "programa_id": prog_opts[a_programa], "orgao_id": 1})
                    st.success("Ação salva!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    with tab4:
        st.subheader("Naturezas de Despesa")
        with st.form("form_natureza"):
            col1, col2 = st.columns(2)
            with col1:
                n_codigo = st.text_input("Código", "3.1.90.11.00")
                n_grupo = st.selectbox("Grupo", ["1 - Pessoal", "2 - Juros", "3 - Outras Correntes", "4 - Investimentos"])
                n_elemento = st.text_input("Elemento", "11")
            with col2:
                n_categoria = st.selectbox("Categoria", ["3 - Corrente", "4 - Capital"])
                n_modalidade = st.text_input("Modalidade", "90")
                n_descricao = st.text_input("Descrição", "Vencimentos e Vantagens Fixas")
            if st.form_submit_button("Salvar"):
                try:
                    insert_natureza({"codigo": n_codigo, "categoria": n_categoria, "grupo": n_grupo, "modalidade": n_modalidade, "elemento": n_elemento, "descricao": n_descricao})
                    st.success("Natureza salva!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
        naturezas = get_all_naturezas()
        if naturezas:
            st.dataframe(pd.DataFrame(naturezas), use_container_width=True)

    with tab5:
        st.subheader("Fontes de Recurso")
        with st.form("form_fonte"):
            col1, col2 = st.columns(2)
            with col1:
                f_codigo = st.text_input("Código", "RO")
                f_descricao = st.text_input("Descrição", "Recursos Ordinários")
            with col2:
                f_tipo = st.selectbox("Tipo", ["tesouro", "vinculado", "convenio"])
            if st.form_submit_button("Salvar"):
                try:
                    insert_fonte({"codigo": f_codigo, "descricao": f_descricao, "tipo": f_tipo})
                    st.success("Fonte salva!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
        fontes = get_all_fontes()
        if fontes:
            st.dataframe(pd.DataFrame(fontes), use_container_width=True)

    with tab6:
        st.subheader("Dotações Orçamentárias")
        with st.form("form_dotacao"):
            exercicios_list = get_all_exercicios()
            ex_opts = {str(e["ano"]): e["id"] for e in exercicios_list}
            orgaos_list = get_all_orgaos()
            og_opts = {f"{o['nome']} ({o['sigla']})": o["id"] for o in orgaos_list}
            programas = get_all_programas()
            pr_opts = {p["nome"]: p["id"] for p in programas}
            acoes = get_all_acoes()
            ac_opts = {a["nome"]: a["id"] for a in acoes}
            naturezas = get_all_naturezas()
            nt_opts = {n["descricao"]: n["id"] for n in naturezas}
            fontes_list = get_all_fontes()
            ft_opts = {f["descricao"]: f["id"] for f in fontes_list}

            col1, col2, col3 = st.columns(3)
            with col1:
                d_exercicio = st.selectbox("Exercício", options=list(ex_opts.keys()))
                d_orgao = st.selectbox("Órgão", options=list(og_opts.keys()))
                d_programa = st.selectbox("Programa", options=list(pr_opts.keys()))
            with col2:
                d_acao = st.selectbox("Ação", options=list(ac_opts.keys()))
                d_natureza = st.selectbox("Natureza", options=list(nt_opts.keys()))
                d_fonte = st.selectbox("Fonte", options=list(ft_opts.keys()))
            with col3:
                d_valor_original = st.number_input("Valor Original (R$)", min_value=0.0, step=1000.0, format="%.2f")
                d_valor_atual = st.number_input("Valor Atual (R$)", min_value=0.0, step=1000.0, format="%.2f")

            if st.form_submit_button("Salvar Dotação"):
                try:
                    insert_dotacao({
                        "exercicio_id": ex_opts[d_exercicio], "orgao_id": og_opts[d_orgao],
                        "programa_id": pr_opts[d_programa], "acao_id": ac_opts[d_acao],
                        "natureza_id": nt_opts[d_natureza], "fonte_recurso_id": ft_opts[d_fonte],
                        "valor_original": d_valor_original, "valor_atual": d_valor_atual
                    })
                    st.success("Dotação salva!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        dotacoes = get_all_dotacoes()
        if dotacoes:
            st.dataframe(pd.DataFrame(dotacoes), use_container_width=True)

    with tab7:
        st.subheader("Previsão de Receitas")
        with st.form("form_receita"):
            receitas_fontes = get_all_fontes()
            rf_opts = {f["descricao"]: f["id"] for f in receitas_fontes}
            col1, col2 = st.columns(2)
            with col1:
                r_descricao = st.text_input("Descrição")
                r_valor_previsto = st.number_input("Valor Previsto (R$)", min_value=0.0, format="%.2f")
            with col2:
                r_fonte = st.selectbox("Fonte de Recurso", options=list(rf_opts.keys()))
                r_mes = st.number_input("Mês", min_value=1, max_value=12, value=1)
            if st.form_submit_button("Salvar"):
                try:
                    ex_id = ex_opts[list(ex_opts.keys())[0]] if ex_opts else 1
                    insert_receita({"exercicio_id": ex_id, "fonte_recurso_id": rf_opts[r_fonte], "descricao": r_descricao, "valor_previsto": r_valor_previsto, "valor_realizado": 0, "mes_competencia": r_mes})
                    st.success("Receita salva!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        receitas = get_all_receitas()
        if receitas:
            df = pd.DataFrame(receitas)
            st.dataframe(df, use_container_width=True)
            total_prev = df["valor_previsto"].sum()
            st.metric("Total Previsto", f"R$ {total_prev:,.2f}")

    with tab8:
        st.subheader("Visão Geral da LOA")
        exercicios_list = get_all_exercicios()
        if exercicios_list:
            ex_id = exercicios_list[0]["id"]
            dados = get_visao_geral_loa(ex_id)
            if dados:
                df = pd.DataFrame(dados)
                st.dataframe(df, use_container_width=True, height=400)
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download CSV", csv, "loa_completa.csv", "text/csv")

                col1, col2, col3 = st.columns(3)
                col1.metric("💰 Orçamento Original", f"R$ {df['valor_original'].sum():,.2f}")
                col2.metric("💵 Orçamento Atual", f"R$ {df['valor_atual'].sum():,.2f}")
                col3.metric("📌 Saldo Disponível", f"R$ {df['saldo'].sum():,.2f}")


def pagina_licitacoes():
    st.title("📑 Licitações")

    tab_lic, tab_itens = st.tabs(["Cadastro de Licitações", "Itens da Licitação"])

    with tab_lic:
        orgaos_list = get_all_orgaos()
        og_opts = {f"{o['nome']} ({o['sigla']})": o["id"] for o in orgaos_list}
        with st.form("form_licitacao"):
            col1, col2, col3 = st.columns(3)
            with col1:
                numero = st.text_input("Número da Licitação")
                modalidade = st.selectbox("Modalidade", ["pregao_eletronico", "tomada_preco", "convite", "concorrencia", "dispensa", "inexigibilidade"])
            with col2:
                objeto = st.text_area("Objeto")
                valor_estimado = st.number_input("Valor Estimado (R$)", min_value=0.0, format="%.2f")
            with col3:
                orgao = st.selectbox("Órgão", options=list(og_opts.keys()))
                alerta = st.slider("Percentual de alerta (%)", 0, 100, 20, 1)
            if st.form_submit_button("Salvar Licitação"):
                try:
                    insert_licitacao({"numero": numero, "modalidade": modalidade, "objeto": objeto, "valor_estimado": valor_estimado, "orgao_id": og_opts[orgao], "alerta_percentual": alerta})
                    st.success("Licitação salva!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        licitacoes = get_all_licitacoes()
        if licitacoes:
            df = pd.DataFrame(licitacoes)
            st.dataframe(df, use_container_width=True)
            st.subheader("Detalhes da Licitação")
            lic_opt = {f"{l['numero']} - {l.get('objeto', '')}": l["id"] for l in licitacoes}
            sel = st.selectbox("Selecionar licitação", options=list(lic_opt.keys()))
            itens = get_itens_licitacao(lic_opt[sel])
            if itens:
                st.dataframe(pd.DataFrame(itens), use_container_width=True)

    with tab_itens:
        licitacoes = get_all_licitacoes()
        lic_opts = {f"{l['numero']} - {l.get('objeto', '')}": l["id"] for l in licitacoes}
        if not licitacoes:
            st.warning("Cadastre uma licitação primeiro.")
            return
        with st.form("form_item_licitacao"):
            col1, col2, col3 = st.columns(3)
            with col1:
                lic_sel = st.selectbox("Licitação", options=list(lic_opts.keys()))
                produto = st.text_input("Produto")
            with col2:
                quantidade = st.number_input("Quantidade", min_value=1, value=1)
                valor_unitario = st.number_input("Valor Unitário (R$)", min_value=0.0, format="%.2f")
            with col3:
                unidade = st.text_input("Unidade de Medida", "un")
            if st.form_submit_button("Salvar Item"):
                try:
                    insert_item_licitacao({"licitacao_id": lic_opts[lic_sel], "produto": produto, "quantidade": quantidade, "valor_unitario": valor_unitario, "unidade_medida": unidade, "quantidade_retirada": 0})
                    st.success("Item salvo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        if licitacoes:
            lic_det = st.selectbox("Ver itens de", options=list(lic_opts.keys()), key="det_itens")
            itens = get_itens_licitacao(lic_opts[lic_det])
            if itens:
                for item in itens:
                    total = item.get("quantidade", 0)
                    retirada = item.get("quantidade_retirada", 0)
                    pct = (retirada / total * 100) if total else 0
                    col_a, col_b = st.columns([1, 3])
                    col_a.write(f"{item.get('produto', '')}")
                    col_b.progress(min(pct / 100, 1.0), text=f"{retirada}/{total} ({pct:.1f}%)")
                st.dataframe(pd.DataFrame(itens), use_container_width=True)


def pagina_compras():
    st.title("🛒 Compras - Ordens de Compra")

    licitacoes = get_all_licitacoes()
    lic_opts = {f"{l['numero']} - {l.get('objeto', '')}": l["id"] for l in licitacoes}
    if not licitacoes:
        st.warning("Nenhuma licitação cadastrada.")
        return

    lic_sel = st.selectbox("Licitação", options=list(lic_opts.keys()))
    itens = get_itens_licitacao(lic_opts[lic_sel])
    item_opts = {f"{i['produto']} (disp: {i.get('quantidade', 0) - i.get('quantidade_retirada', 0)})": i["id"] for i in itens}

    with st.form("form_compra"):
        col1, col2, col3 = st.columns(3)
        with col1:
            item_sel = st.selectbox("Item", options=list(item_opts.keys()))
            quantidade = st.number_input("Quantidade", min_value=1, value=1)
        with col2:
            valor_unitario = st.number_input("Valor Unitário (R$)", min_value=0.0, format="%.2f")
            situacao = st.selectbox("Situação", ["pendente", "autorizada", "entregue", "cancelada"])
        with col3:
            data_oc = st.date_input("Data", value=datetime.date.today())
            numero = st.text_input("Número OC")
        if st.form_submit_button("Salvar Ordem de Compra"):
            try:
                insert_ordem_compra({"licitacao_id": lic_opts[lic_sel], "item_licitacao_id": item_opts[item_sel], "numero": numero, "data": data_oc, "quantidade": quantidade, "valor_unitario": valor_unitario, "situacao": situacao})
                recalcular_saldo_item_licitacao(item_opts[item_sel])
                st.success("Ordem de compra salva!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

    st.subheader("Histórico de Ordens de Compra")
    ordens = get_all_ordens_compra()
    if ordens:
        st.dataframe(pd.DataFrame(ordens), use_container_width=True)


def pagina_contratos():
    st.title("📜 Contratos")

    tab_con, tab_adit = st.tabs(["Contratos", "Aditivos"])

    with tab_con:
        licitacoes = get_all_licitacoes()
        lic_opts = {f"{l['numero']} - {l.get('objeto', '')}": l["id"] for l in licitacoes}
        fornecedores = get_all_fornecedores()
        forn_opts = {f"{f['nome']} ({f.get('cpf_cnpj', '')})": f["id"] for f in fornecedores}
        with st.form("form_contrato"):
            col1, col2, col3 = st.columns(3)
            with col1:
                numero = st.text_input("Número do Contrato")
                licitacao = st.selectbox("Licitação", options=list(lic_opts.keys()))
            with col2:
                credor = st.selectbox("Credor", options=list(forn_opts.keys()))
                valor_global = st.number_input("Valor Global (R$)", min_value=0.0, format="%.2f")
            with col3:
                vigencia = st.date_input("Vigência", value=datetime.date.today())
                situacao = st.selectbox("Situação", ["ativo", "suspenso", "rescindido", "encerrado"])
            if st.form_submit_button("Salvar Contrato"):
                try:
                    insert_contrato({"numero": numero, "licitacao_id": lic_opts[licitacao], "fornecedor_id": forn_opts[credor], "valor_global": valor_global, "vigencia": vigencia, "situacao": situacao})
                    st.success("Contrato salvo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        contratos = get_all_contratos()
        if contratos:
            df = pd.DataFrame(contratos)
            hoje = datetime.date.today()
            def colorir_vencimento(row):
                vig = row.get("vigencia")
                if not vig:
                    return [""] * len(row)
                try:
                    vig_dt = pd.to_datetime(vig).date()
                except Exception:
                    return [""] * len(row)
                dias = (vig_dt - hoje).days
                if dias > 60:
                    cor = "background-color: #d4edda"
                elif dias > 30:
                    cor = "background-color: #fff3cd"
                else:
                    cor = "background-color: #f8d7da"
                return [cor] * len(row)

            st.dataframe(df.style.apply(colorir_vencimento, axis=1), use_container_width=True)

    with tab_adit:
        contratos = get_all_contratos()
        cont_opts = {f"{c['numero']}": c["id"] for c in contratos}
        if not contratos:
            st.warning("Cadastre um contrato primeiro.")
            return
        with st.form("form_aditivo"):
            col1, col2, col3 = st.columns(3)
            with col1:
                contrato = st.selectbox("Contrato", options=list(cont_opts.keys()))
                tipo = st.selectbox("Tipo", ["prazo", "valor", "prazo_e_valor", "outros"])
            with col2:
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
                novo_vencimento = st.date_input("Novo Vencimento", value=datetime.date.today())
            with col3:
                justificativa = st.text_area("Justificativa")
            if st.form_submit_button("Salvar Aditivo"):
                try:
                    insert_aditivo({"contrato_id": cont_opts[contrato], "tipo": tipo, "valor": valor, "novo_vencimento": novo_vencimento, "justificativa": justificativa})
                    st.success("Aditivo salvo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        aditivos = get_all_aditivos()
        if aditivos:
            st.dataframe(pd.DataFrame(aditivos), use_container_width=True)


def pagina_fornecedores():
    st.title("🏢 Fornecedores")

    with st.form("form_fornecedor"):
        col1, col2, col3 = st.columns(3)
        with col1:
            tipo = st.selectbox("Tipo", ["pf", "pj"])
            cpf_cnpj = st.text_input("CPF/CNPJ")
        with col2:
            nome = st.text_input("Nome / Razão Social")
            endereco = st.text_input("Endereço")
        with col3:
            dados_bancarios = st.text_input("Dados Bancários")
            ativo = st.selectbox("Ativo", [1, 0])
        if st.form_submit_button("Salvar Fornecedor"):
            try:
                insert_fornecedor({"tipo": tipo, "cpf_cnpj": cpf_cnpj, "nome": nome, "endereco": endereco, "dados_bancarios": dados_bancarios, "ativo": ativo})
                st.success("Fornecedor salvo!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

    fornecedores = get_all_fornecedores()
    if fornecedores:
        df = pd.DataFrame(fornecedores)
        st.dataframe(df, use_container_width=True)

        st.subheader("Histórico do Fornecedor")
        forn_opts = {f"{f['nome']} ({f.get('cpf_cnpj', '')})": f["id"] for f in fornecedores}
        forn_sel = st.selectbox("Selecionar fornecedor", options=list(forn_opts.keys()))
        contratos = get_contratos_por_fornecedor(forn_opts[forn_sel])
        empenhos = get_empenhos_por_fornecedor(forn_opts[forn_sel])
        if contratos:
            st.markdown("**Contratos**")
            st.dataframe(pd.DataFrame(contratos), use_container_width=True)
        if empenhos:
            st.markdown("**Empenhos**")
            st.dataframe(pd.DataFrame(empenhos), use_container_width=True)


def pagina_prestadores():
    st.title("🏥 Prestadores de Saúde")

    fornecedores = get_all_fornecedores()
    forn_opts = {f"{f['nome']} ({f.get('cpf_cnpj', '')})": f["id"] for f in fornecedores}
    with st.form("form_prestador"):
        col1, col2, col3 = st.columns(3)
        with col1:
            credor = st.selectbox("Credor", options=list(forn_opts.keys()))
            especialidade = st.text_input("Especialidade")
        with col2:
            registro_conselho = st.text_input("Registro no Conselho")
            data_credenciamento = st.date_input("Data Credenciamento", value=datetime.date.today())
        with col3:
            data_validade = st.date_input("Data Validade", value=datetime.date.today())
            situacao = st.selectbox("Situação", ["ativo", "suspenso", "cancelado"])
        if st.form_submit_button("Salvar Prestador"):
            try:
                insert_prestador({"fornecedor_id": forn_opts[credor], "especialidade": especialidade, "registro_conselho": registro_conselho, "data_credenciamento": data_credenciamento, "data_validade": data_validade, "situacao": situacao})
                st.success("Prestador salvo!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

    prestadores = get_all_prestadores()
    if prestadores:
        st.dataframe(pd.DataFrame(prestadores), use_container_width=True)


def pagina_pacientes():
    st.title("👤 Pacientes")

    tab_cad, tab_atend = st.tabs(["Cadastro", "Atendimentos"])

    with tab_cad:
        with st.form("form_paciente"):
            col1, col2, col3 = st.columns(3)
            with col1:
                nome = st.text_input("Nome")
                cpf = st.text_input("CPF")
                data_nascimento = st.date_input("Data Nascimento", value=datetime.date.today())
            with col2:
                sexo = st.selectbox("Sexo", ["M", "F", "Outro"])
                endereco = st.text_input("Endereço")
            with col3:
                telefone = st.text_input("Telefone")
                email = st.text_input("Email")
                convenio = st.text_input("Convênio")
            if st.form_submit_button("Salvar Paciente"):
                try:
                    insert_paciente({"nome": nome, "cpf": cpf, "data_nascimento": data_nascimento, "sexo": sexo, "endereco": endereco, "telefone": telefone, "email": email, "convenio": convenio})
                    st.success("Paciente salvo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        pacientes = get_all_pacientes()
        if pacientes:
            st.dataframe(pd.DataFrame(pacientes), use_container_width=True)

    with tab_atend:
        pacientes = get_all_pacientes()
        if not pacientes:
            st.warning("Cadastre um paciente primeiro.")
            return
        pac_opts = {f"{p['nome']} ({p.get('cpf', '')})": p["id"] for p in pacientes}
        pac_sel = st.selectbox("Paciente", options=list(pac_opts.keys()), key="pac_atend")

        with st.form("form_atendimento"):
            col1, col2, col3 = st.columns(3)
            with col1:
                data_atend = st.date_input("Data Atendimento", value=datetime.date.today())
                tipo = st.selectbox("Tipo", ["consulta", "exame", "procedimento", "internacao"])
            with col2:
                prestadores = get_all_prestadores()
                prest_opts = {f"{p.get('especialidade', '')} - {p.get('registro_conselho', '')}": p["id"] for p in prestadores}
                prestador = st.selectbox("Prestador", options=list(prest_opts.keys()))
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            with col3:
                procedimento = st.text_input("Procedimento")
                situacao = st.selectbox("Situação", ["agendado", "realizado", "cancelado"])
            if st.form_submit_button("Salvar Atendimento"):
                try:
                    insert_atendimento({"paciente_id": pac_opts[pac_sel], "prestador_id": prest_opts[prestador], "data": data_atend, "tipo": tipo, "procedimento": procedimento, "valor": valor, "situacao": situacao})
                    st.success("Atendimento salvo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        atendimentos = get_atendimentos_por_paciente(pac_opts[pac_sel])
        if atendimentos:
            st.dataframe(pd.DataFrame(atendimentos), use_container_width=True)


def pagina_financeiro():
    st.title("💰 Financeiro")

    tab_emp, tab_liq, tab_pag, tab_sup, tab_ext = st.tabs([
        "Empenhos", "Liquidações", "Pagamentos", "Suplementações", "Extrato"
    ])

    with tab_emp:
        dotacoes = get_all_dotacoes()
        dot_opts = {f"Dotação #{d['id']}": d["id"] for d in dotacoes}
        fornecedores = get_all_fornecedores()
        forn_opts = {f"{f['nome']} ({f.get('cpf_cnpj', '')})": f["id"] for f in fornecedores}
        with st.form("form_empenho"):
            col1, col2, col3 = st.columns(3)
            with col1:
                numero = st.text_input("Número Empenho")
                data = st.date_input("Data", value=datetime.date.today())
                tipo = st.selectbox("Tipo", ["ordinario", "estimativo", "global"])
            with col2:
                dotacao = st.selectbox("Dotação", options=list(dot_opts.keys()))
                credor = st.selectbox("Credor", options=list(forn_opts.keys()))
            with col3:
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
                historico = st.text_area("Histórico")
            if st.form_submit_button("Salvar Empenho"):
                try:
                    insert_empenho({"numero": numero, "data": data, "tipo": tipo, "dotacao_id": dot_opts[dotacao], "fornecedor_id": forn_opts[credor], "valor": valor, "historico": historico, "status": "ativo"})
                    recalcular_dotacao_por_empenho(dot_opts[dotacao])
                    st.success("Empenho salvo!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        empenhos = get_all_empenhos()
        if empenhos:
            st.dataframe(pd.DataFrame(empenhos), use_container_width=True)

    with tab_liq:
        empenhos = get_all_empenhos()
        emp_opts = {f"{e['numero']} - R$ {e.get('valor', 0):,.2f}": e["id"] for e in empenhos}
        if not empenhos:
            st.warning("Cadastre um empenho primeiro.")
        else:
            with st.form("form_liquidacao"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    empenho = st.selectbox("Empenho", options=list(emp_opts.keys()))
                    numero = st.text_input("Número Liquidação")
                with col2:
                    data = st.date_input("Data", value=datetime.date.today())
                    valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
                with col3:
                    documento_fiscal = st.text_input("Documento Fiscal")
                if st.form_submit_button("Salvar Liquidação"):
                    try:
                        insert_liquidacao({"empenho_id": emp_opts[empenho], "numero": numero, "data": data, "valor": valor, "documento_fiscal": documento_fiscal})
                        dot_id = next((e["dotacao_id"] for e in empenhos if e["id"] == emp_opts[empenho]), None)
                        if dot_id:
                            recalcular_dotacao_por_empenho(dot_id)
                        st.success("Liquidação salva!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

        liquidacoes = get_all_liquidacoes()
        if liquidacoes:
            st.dataframe(pd.DataFrame(liquidacoes), use_container_width=True)

    with tab_pag:
        liquidacoes = get_all_liquidacoes()
        liq_opts = {f"{l['numero']} - R$ {l.get('valor', 0):,.2f}": l["id"] for l in liquidacoes}
        if not liquidacoes:
            st.warning("Cadastre uma liquidação primeiro.")
        else:
            with st.form("form_pagamento"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    liquidacao = st.selectbox("Liquidação", options=list(liq_opts.keys()))
                    data = st.date_input("Data", value=datetime.date.today())
                with col2:
                    valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
                    forma_pagamento = st.selectbox("Forma Pagamento", ["transferencia", "cheque", "dinheiro", "pix"])
                with col3:
                    st.text_input("Observação", "", key="obs_pag")
                if st.form_submit_button("Salvar Pagamento"):
                    try:
                        insert_pagamento({"liquidacao_id": liq_opts[liquidacao], "data": data, "valor": valor, "forma_pagamento": forma_pagamento})
                        st.success("Pagamento salvo!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

        pagamentos = get_all_pagamentos()
        if pagamentos:
            st.dataframe(pd.DataFrame(pagamentos), use_container_width=True)

    with tab_sup:
        st.subheader("Suplementações / Alterações Orçamentárias")
        alerta_sup = st.slider("Percentual de alerta (%)", 0, 100, 20, 1, key="alerta_sup")
        with st.form("form_suplementacao"):
            col1, col2, col3 = st.columns(3)
            with col1:
                tipo = st.selectbox("Tipo", ["suplementacao", "anulacao", "remanejamento"])
                numero_decreto = st.text_input("Número Decreto/Portaria")
            with col2:
                data = st.date_input("Data", value=datetime.date.today())
                dotacao = st.selectbox("Dotação", options=[f"Dotação #{d['id']}" for d in get_all_dotacoes()])
            with col3:
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
                justificativa = st.text_area("Justificativa")
            if st.form_submit_button("Salvar Alteração"):
                try:
                    dot_id = int(dotacao.replace("Dotação #", ""))
                    insert_alteracao_orcamentaria({"tipo": tipo, "numero_decreto": numero_decreto, "data": data, "dotacao_id": dot_id, "valor": valor, "justificativa": justificativa})
                    st.success("Alteração salva!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

        alteracoes = get_all_alteracoes_orcamentarias()
        if alteracoes:
            df = pd.DataFrame(alteracoes)
            st.dataframe(df, use_container_width=True)
            total_sup = df[df["tipo"] == "suplementacao"]["valor"].sum() if "tipo" in df.columns else 0
            st.metric("Total de Suplementações", f"R$ {total_sup:,.2f}")

    with tab_ext:
        st.subheader("Extrato da Dotação")
        dotacoes = get_all_dotacoes()
        dot_opts = {f"Dotação #{d['id']}": d["id"] for d in dotacoes}
        if not dotacoes:
            st.warning("Nenhuma dotação cadastrada.")
        else:
            dot_sel = st.selectbox("Dotação", options=list(dot_opts.keys()), key="ext_dot")
            extrato = get_extrato_dotacao(dot_opts[dot_sel])
            if extrato:
                st.dataframe(pd.DataFrame(extrato), use_container_width=True, height=500)


def pagina_alertas():
    st.title("⚠️ Alertas e Parâmetros")

    parametros = get_all_parametros()
    if parametros:
        for p in parametros:
            novo_valor = st.slider(f"{p.get('nome', p['id'])} (atual: {p.get('valor', 0)})", 0, 100, int(p.get("valor", 0) or 0), 1)
            if st.button(f"Salvar {p.get('nome', p['id'])}", key=f"btn_p_{p['id']}"):
                try:
                    update_parametro({"id": p["id"], "valor": novo_valor})
                    st.success("Parâmetro atualizado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
    else:
        st.info("Nenhum parâmetro cadastrado.")

    st.subheader("Preview dos Alertas Ativos")
    alertas_lic = get_alerta_licitacao()
    alertas_dot = get_alerta_dotacao()

    if alertas_lic:
        st.warning("Alertas de licitação")
        st.dataframe(pd.DataFrame(alertas_lic), use_container_width=True)
    if alertas_dot:
        st.warning("Alertas de dotação")
        st.dataframe(pd.DataFrame(alertas_dot), use_container_width=True)
    if not alertas_lic and not alertas_dot:
        st.success("✅ Nenhum alerta ativo no momento.")


def pagina_relatorios():
    st.title("📈 Relatórios")

    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data Início", value=datetime.date(datetime.date.today().year, 1, 1))
    with col2:
        data_fim = st.date_input("Data Fim", value=datetime.date.today())

    tipo_rel = st.selectbox("Tipo de Relatório", [
        "Execução Orçamentária", "Licitações", "Fornecedores"
    ])

    if st.button("Gerar Relatório"):
        try:
            if tipo_rel == "Execução Orçamentária":
                dados = get_relatorio_execucao_orcamentaria(data_inicio, data_fim)
            elif tipo_rel == "Licitações":
                dados = get_relatorio_licitacoes(data_inicio, data_fim)
            elif tipo_rel == "Fornecedores":
                dados = get_relatorio_fornecedores(data_inicio, data_fim)
            else:
                dados = []

            if dados:
                df = pd.DataFrame(dados)
                st.dataframe(df, use_container_width=True, height=500)
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download CSV", csv, f"relatorio_{tipo_rel.lower().replace(' ', '_')}.csv", "text/csv")
            else:
                st.info("Nenhum dado encontrado para o período/tipo selecionado.")
        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")


def main():
    if "usuario" not in st.session_state:
        st.session_state.usuario = None

    init_db()

    if st.session_state.usuario is None:
        st.title("🔐 MARMED Gestão em Saúde")
        st.image("https://via.placeholder.com/200x80?text=MARMED", width=200)
        email = st.text_input("Email", value="admin")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            try:
                user = login_usuario(email, hash_senha(senha))
                if user:
                    st.session_state.usuario = user
                    st.rerun()
                else:
                    st.error("Email ou senha inválidos.")
            except Exception as e:
                st.error(f"Erro no login: {e}")
        return

    with st.sidebar:
        st.title("🏥 MARMED")
        st.caption(f"👤 {st.session_state.usuario['nome']}")
        st.divider()

        pagina = st.radio("Navegação", [
            "🏠 Dashboard", "📊 LOA", "📑 Licitações", "🛒 Compras",
            "📜 Contratos", "🏢 Fornecedores", "🏥 Prestadores Saúde",
            "👤 Pacientes", "💰 Financeiro", "⚠️ Alertas", "📈 Relatórios"
        ])

        st.divider()
        if st.button("🚪 Sair"):
            st.session_state.usuario = None
            st.rerun()

    if pagina == "🏠 Dashboard":
        pagina_dashboard()
    elif pagina == "📊 LOA":
        pagina_loa()
    elif pagina == "📑 Licitações":
        pagina_licitacoes()
    elif pagina == "🛒 Compras":
        pagina_compras()
    elif pagina == "📜 Contratos":
        pagina_contratos()
    elif pagina == "🏢 Fornecedores":
        pagina_fornecedores()
    elif pagina == "🏥 Prestadores Saúde":
        pagina_prestadores()
    elif pagina == "👤 Pacientes":
        pagina_pacientes()
    elif pagina == "💰 Financeiro":
        pagina_financeiro()
    elif pagina == "⚠️ Alertas":
        pagina_alertas()
    elif pagina == "📈 Relatórios":
        pagina_relatorios()


if __name__ == "__main__":
    main()
