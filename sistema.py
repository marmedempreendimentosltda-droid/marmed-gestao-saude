def pagina_cadastro_contas():
    st.markdown('<p class="mm-title">Cadastro de Contas</p>', unsafe_allow_html=True)
    st.markdown('<p class="mm-subtitle">Registre as contas a receber por esfera de gestao</p>', unsafe_allow_html=True)

    # ESFERA E FONTE FORA DO FORM - atualizam instantaneamente
    esfera = st.selectbox("Esfera", ["Federal", "Estadual", "Municipal", "Transferencia", "Transposicao"], key="esfera_cad_fora")

    fonte_vinculada = get_fonte(esfera)
    st.markdown(
        f'<div class="mm-card" style="text-align:left;margin-bottom:16px;padding:14px 18px;">'
        f'<div class="mm-card-label">Fonte Vinculada</div>'
        f'<div class="mm-card-value" style="font-size:20px;">{fonte_vinculada}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    with st.form("form_cadastro_conta"):
        col1, col2 = st.columns(2)
        with col1:
            numero_conta = st.text_input("Numero da Conta")
            referencia_tipo = st.text_input("Tipo de Referencia")
            referencia_numero = st.text_input("Numero de Referencia")
        with col2:
            tipo_recurso = st.selectbox("Tipo de Recurso", ["Custeio", "Investimento", "Custeio e Investimento"])
            valor_custeio = st.text_input("Valor Custeio", value="R$ 0,00")
            valor_investimento = st.text_input("Valor Investimento", value="R$ 0,00")
            data_recebimento = st.date_input("Data de Recebimento", value=datetime.now())

        programa_politica = st.text_input("Programa / Politica")
        setor_gasto = st.text_input("Setor de Gasto")

        salvar = st.form_submit_button("Salvar Conta", use_container_width=True)

        if salvar:
            vc = parse_valor(valor_custeio)
            vi = parse_valor(valor_investimento)
            vt = vc + vi
            if vt <= 0:
                st.error("Informe pelo menos um valor de custeio ou investimento.")
            else:
                conn = get_conn()
                conn.execute(
                    "INSERT INTO contas_receber (esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso, valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento, programa_politica, setor_gasto) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (esfera, numero_conta, get_fonte(esfera), referencia_tipo, referencia_numero, tipo_recurso, vc, vi, vt, data_recebimento.strftime("%d/%m/%Y"), programa_politica, setor_gasto),
                )
                conn.commit()
                conn.close()
                st.success("Conta cadastrada com sucesso!")
                st.rerun()
