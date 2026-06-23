def realizar_compras():
    st.markdown('<h1 style="color:#e0f2fe;">REALIZAR COMPRAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    inject_masks()
    conn = sqlite3.connect("marmed.db")
    
    # === NOVA SOLICITAÇÃO (primeiro) ===
    st.markdown('<h3 style="color:#7dd3fc;">Nova Solicitacao</h3>', unsafe_allow_html=True)
    tabs = st.tabs(["FEDERAL", "ESTADUAL", "MUNICIPAL"])
    for tab_idx, esf in enumerate(["Federal", "Estadual", "Municipal"]):
        with tabs[tab_idx]:
            # Busca contas com dados completos INCLUDINDO referencia_uso
            contas = conn.execute("""
                SELECT cr.id, cr.numero_conta, cr.fonte, cr.valor_total, 
                       cr.programa_politica, cr.setor_gasto, COALESCE(cr.referencia_uso, '') 
                FROM contas_receber cr WHERE cr.esfera=? ORDER BY cr.id DESC
            """, (esf,)).fetchall()
            
            if not contas:
                st.markdown(f'<p style="color:#94a3b8;">Nenhuma conta {esf} disponivel.</p>', unsafe_allow_html=True)
                continue
            
            for cid, num, fonte, vtotal, prog, setor, refuso in contas:
                gasto = conn.execute("SELECT COALESCE(SUM(valor_compra),0) FROM ordens_compra WHERE conta_receber_id=?", (cid,)).fetchone()[0]
                saldo = vtotal - gasto
                
                with st.expander(f"{num} - Fonte {fonte}"):
                    # DADOS DA CONTA - incluindo Setor, Programa, Ref.Uso
                    st.markdown(f'''
                    <div style="background:rgba(30,41,59,0.6);border-radius:10px;padding:12px;margin-bottom:10px;">
                        <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                            <div style="color:#94a3b8;">Valor: <span style="color:#00d4ff;">{format_currency(vtotal)}</span></div>
                            <div style="color:#94a3b8;">Saldo: <span style="color:{"#22c55e" if saldo>0 else "#ef4444"};">{format_currency(saldo)}</span></div>
                        </div>
                        <div style="border-top:1px solid rgba(34,211,238,0.15);padding-top:6px;margin-top:4px;">
                            <div style="color:#b0eaff;font-size:12px;"><strong>Programa:</strong> {prog or "--"}</div>
                            <div style="color:#b0eaff;font-size:12px;margin-top:2px;"><strong>Setor:</strong> {setor or "--"}</div>
                            <div style="color:#b0eaff;font-size:12px;margin-top:2px;"><strong>Ref.Uso:</strong> {refuso or "--"}</div>
                        </div>
                    </div>''', unsafe_allow_html=True)
                    
                    if esf != "Municipal":
                        ss = conn.execute("SELECT COALESCE(SUM(saldo_restante),0) FROM superavit WHERE esfera=? AND saldo_restante>0", (esf,)).fetchone()[0]
                        if ss > 0: st.warning(f"Superavit de {format_currency(ss)}. Utilize antes.")
                    
                    with st.form(key=f"fc_{esf}_{cid}"):
                        cA, cB = st.columns(2)
                        with cA:
                            ficha = st.text_input("Ficha")
                            td = st.selectbox("Despesa", ["", "Material de Consumo", "Servico PF", "Servico PJ", "Distribuicao Gratuita"], key=f"td_{esf}_{cid}")
                            data_c = st.text_input("Data Compra", value=datetime.now().strftime("%d/%m/%Y"), key=f"dc_{esf}_{cid}")
                        with cB:
                            valor_c_str = st.text_input("Valor", key=f"vc_{esf}_{cid}")
                            valor_c = parse_br_currency(valor_c_str)
                            if valor_c > saldo: st.markdown(f'<p style="color:#ef4444;">Excede {format_currency(saldo)}</p>', unsafe_allow_html=True)
                        prod = st.text_area("Produto/Servico", height=120)
                        if st.form_submit_button("Solicitar"):
                            erros = [x for x, v in [("Ficha", ficha), ("Tipo", td), ("Data", data_c), ("Valor", valor_c>0), ("Produto", prod), ("Saldo", valor_c<=saldo)] if not v]
                            if erros: st.error(f"Preencha: {', '.join(erros)}")
                            else:
                                conn.execute("INSERT INTO ordens_compra (conta_receber_id, esfera, numero_conta, fonte, ficha, tipo_despesa, data_compra, valor_compra, produto_servico, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)", (cid, esf, num, fonte, ficha, td, data_c, valor_c, prod, datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
                                conn.commit(); st.success("Registrada!"); st.rerun()
    
    # === EDITAR / EXCLUIR (agora na parte inferior) ===
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#7dd3fc;">Editar / Excluir Solicitacoes</h3>', unsafe_allow_html=True)
    
    ordens = conn.execute("""
        SELECT oc.id, oc.esfera, oc.numero_conta, oc.ficha, oc.valor_compra, 
               oc.produto_servico, oc.data_compra, oc.tipo_despesa,
               cr.programa_politica, cr.setor_gasto, COALESCE(cr.referencia_uso, '')
        FROM ordens_compra oc
        LEFT JOIN contas_receber cr ON oc.conta_receber_id = cr.id
        ORDER BY oc.id DESC
    """).fetchall()
    
    if ordens:
        # Mostra cada ordem com dados completos
        for o in ordens:
            oid = o[0]; esf_ord = o[1]; num_ord = o[2]; ficha = o[3] or "--"
            val_ord = o[4]; prod_ord = o[5] or ""; data_ord = o[6] or ""
            tipo_ord = o[7] or ""; prog_ord = o[8] or ""; setor_ord = o[9] or ""
            refuso_ord = o[10] or ""
            
            with st.expander(f"{esf_ord} - Conta {num_ord} - Ficha {ficha} (R$ {val_ord:.2f})"):
                st.markdown(f'''
                <div style="background:rgba(30,41,59,0.6);border-radius:10px;padding:12px;margin-bottom:8px;border-left:3px solid #22d3ee;">
                    <div style="display:flex;justify-content:space-between;flex-wrap:wrap;">
                        <div style="color:#94a3b8;font-size:11px;">Ficha: <span style="color:#e0f2fe;">{ficha}</span></div>
                        <div style="color:#94a3b8;font-size:11px;">Tipo: <span style="color:#e0f2fe;">{tipo_ord}</span></div>
                        <div style="color:#94a3b8;font-size:11px;">Data: <span style="color:#e0f2fe;">{data_ord}</span></div>
                    </div>
                    <div style="color:#00d4ff;font-size:16px;font-weight:600;margin-top:4px;">{format_currency(val_ord)}</div>
                    <div style="color:#cbd5e1;font-size:12px;margin-top:4px;">{prod_ord[:100]}{"..." if len(prod_ord)>100 else ""}</div>
                    <div style="border-top:1px solid rgba(34,211,238,0.15);padding-top:4px;margin-top:6px;">
                        <div style="color:#b0eaff;font-size:11px;"><strong>Programa:</strong> {prog_ord or "--"}</div>
                        <div style="color:#b0eaff;font-size:11px;margin-top:1px;"><strong>Setor:</strong> {setor_ord or "--"}</div>
                        <div style="color:#b0eaff;font-size:11px;margin-top:1px;"><strong>Ref.Uso:</strong> {refuso_ord or "--"}</div>
                    </div>
                </div>''', unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✏️ Editar", key=f"eo_{oid}"):
                        st.session_state["edit_ordem_id"] = oid
                        st.session_state["page"] = "EDITAR ORDEM COMPRA"
                        st.rerun()
                with c2:
                    if st.button("🗑️ Excluir", key=f"do_{oid}"):
                        conn.execute("DELETE FROM ordens_compra WHERE id=?", (oid,))
                        conn.commit()
                        st.success("Excluida!")
                        st.rerun()
    else:
        st.markdown('<p style="color:#94a3b8;">Nenhuma solicitacao.</p>', unsafe_allow_html=True)
    
    conn.close()
