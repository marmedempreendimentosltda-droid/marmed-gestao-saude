def cadastrar_contas():
    st.markdown('<h1 style="color:#e0f2fe;">CADASTRAR CONTAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    inject_masks()
    
    with st.expander("NOVO CADASTRO", expanded=True):
        st.markdown('<p style="color:#fbbf24;font-size:12px;">* Campos obrigatorios</p>', unsafe_allow_html=True)
        
        # PASSO 1: ESCOLHER ESFERA - MOSTRA A FONTE AUTOMATICAMENTE
        esfera = st.selectbox("* 1. Selecione a Esfera", ["", "Federal", "Estadual", "Municipal"], key="esfera_cad")
        
        # MOSTRA A FONTE AUTOMATICAMENTE AO SELECIONAR A ESFERA
        if esfera:
            fonte_mostrada = get_fonte(esfera)
            cor_fonte = {"Federal": "#3b82f6", "Estadual": "#22c55e", "Municipal": "#eab308"}
            st.markdown(f'''
            <div style="background:rgba(30,41,59,0.8);border-radius:10px;padding:15px;margin-bottom:15px;border-left:4px solid {cor_fonte.get(esfera, "#22d3ee")};">
                <div style="display:flex;align-items:center;justify-content:space-between;">
                    <div>
                        <span style="color:#94a3b8;font-size:13px;">Fonte vinculada automaticamente:</span>
                        <span style="color:#22d3ee;font-size:28px;font-weight:800;margin-left:10px;">{fonte_mostrada}</span>
                    </div>
                    <div>
                        <span style="background:{"#3b82f6" if esfera=="Federal" else "#22c55e" if esfera=="Estadual" else "#eab308"};color:#fff;padding:6px 14px;border-radius:6px;font-size:13px;font-weight:700;">{esfera.upper()}</span>
                    </div>
                </div>
            </div>''', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#64748b;font-size:13px;">Selecione uma Esfera para ver a Fonte vinculada automaticamente</p>', unsafe_allow_html=True)
        
        # PASSO 2: DADOS DA CONTA
        num_conta = st.text_input("* 2. Numero da Conta", key="num_conta_cad")
        ref_contrato = st.selectbox("Referencia (opcional)", ["", "Resolucao", "Deliberacao", "Portaria"])
        num_ano_ref = st.text_input("Numero/Ano (opcional)")
        
        # PASSO 3: TIPO DE RECURSO
        st.markdown('<p style="color:#7dd3fc;font-size:13px;font-weight:600;margin-top:10px;">3. Selecione o Tipo de Recurso</p>', unsafe_allow_html=True)
        tipo_recurso = st.selectbox("* Tipo de Recurso", ["", "Custeio", "Investimento", "Custeio/Investimento"], key="tipo_recurso_cad")
        
        # PASSO 4: CAMPOS DE VALOR
        val_custeio_str = ""
        val_invest_str = ""
        vt = 0.0
        
        if tipo_recurso:
            st.markdown(f'<p style="color:#7dd3fc;font-size:13px;font-weight:600;margin-top:10px;">4. Informe o(s) Valor(es)</p>', unsafe_allow_html=True)
            
            if tipo_recurso in ["Custeio", "Custeio/Investimento"]:
                c1, c2 = st.columns([1, 3])
                with c1:
                    st.markdown('<p style="color:#22d3ee;font-weight:700;margin-top:8px;">R$ CUSTEIO</p>', unsafe_allow_html=True)
                with c2:
                    val_custeio_str = st.text_input("", key="val_custeio_cad", label_visibility="collapsed")
            
            if tipo_recurso in ["Investimento", "Custeio/Investimento"]:
                c1, c2 = st.columns([1, 3])
                with c1:
                    st.markdown('<p style="color:#22d3ee;font-weight:700;margin-top:8px;">R$ INVESTIMENTO</p>', unsafe_allow_html=True)
                with c2:
                    val_invest_str = st.text_input("", key="val_invest_cad", label_visibility="collapsed")
            
            vc = parse_br_currency(val_custeio_str)
            vi = parse_br_currency(val_invest_str)
            vt = vc + vi
            
            if vt > 0:
                st.markdown(f'<p style="color:#00d4ff;font-size:18px;font-weight:700;margin-top:10px;">Total: {format_currency(vt)}</p>', unsafe_allow_html=True)
        
        # PASSO 5: DATA DE RECEBIMENTO
        st.markdown(f'<p style="color:#7dd3fc;font-size:13px;font-weight:600;margin-top:10px;">5. Data de Recebimento</p>', unsafe_allow_html=True)
        st.markdown('<p style="color:#94a3b8;font-size:11px;margin-bottom:5px;">Digite apenas numeros que o sistema coloca as barras automaticamente</p>', unsafe_allow_html=True)
        data_receb = st.text_input("* Data Recebimento", key="data_receb_cad")
        if not data_receb:
            data_receb = datetime.now().strftime("%d/%m/%Y")
        
        # PASSO 6: INFORMACOES ADICIONAIS
        st.markdown(f'<p style="color:#7dd3fc;font-size:13px;font-weight:600;margin-top:10px;">6. Informacoes Adicionais</p>', unsafe_allow_html=True)
        prog = st.text_input("Programa/Politica (opcional)")
        setor = st.text_input("Setor (opcional)")
        
        # BOTAO SALVAR
        if st.button("Salvar Conta"):
            erros = []
            if not esfera: erros.append("Esfera")
            if not num_conta: erros.append("Numero da Conta")
            if not tipo_recurso: erros.append("Tipo de Recurso")
            if vt <= 0: erros.append("Valor (preencha Custeio ou Investimento)")
            if not data_receb: erros.append("Data de Recebimento")
            if erros:
                st.error(f"Preencha: {', '.join(erros)}")
            else:
                conn = sqlite3.connect("marmed.db")
                conn.execute("INSERT INTO contas_receber (esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso, valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento, programa_politica, setor_gasto) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (esfera, num_conta, get_fonte(esfera), ref_contrato, num_ano_ref, tipo_recurso, parse_br_currency(val_custeio_str), parse_br_currency(val_invest_str), vt, data_receb, prog, setor))
                conn.commit(); conn.close()
                st.session_state["page"] = "CONTAS CADASTRADAS"; st.rerun()
