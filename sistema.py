def contas_cadastradas():
    st.markdown('<h1 style="color:#e0f2fe;">CONTAS CADASTRADAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    
    conn = sqlite3.connect("marmed.db")
    tabs = st.tabs(["FEDERAL", "ESTADUAL", "MUNICIPAL"])
    
    for tab_idx, esf in enumerate(["Federal", "Estadual", "Municipal"]):
        with tabs[tab_idx]:
            r = conn.execute("SELECT id, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso, valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento, programa_politica, setor_gasto, COALESCE(referencia_uso, '') FROM contas_receber WHERE esfera=? ORDER BY id DESC", (esf,)).fetchall()
            if r:
                # Inicializa a selecao para esta aba
                sel_key = f"selected_id_{tab_idx}"
                if sel_key not in st.session_state:
                    st.session_state[sel_key] = None
                
                # CABECALHO DA TABELA
                col_h1, col_h2, col_h3, col_h4, col_h5, col_h6 = st.columns([1, 2, 2, 2, 2, 1])
                with col_h1: st.markdown('<p style="color:#22d3ee;font-size:10px;font-weight:600;">ID</p>', unsafe_allow_html=True)
                with col_h2: st.markdown('<p style="color:#22d3ee;font-size:10px;font-weight:600;">CONTA / FONTE</p>', unsafe_allow_html=True)
                with col_h3: st.markdown('<p style="color:#22d3ee;font-size:10px;font-weight:600;">VALOR</p>', unsafe_allow_html=True)
                with col_h4: st.markdown('<p style="color:#22d3ee;font-size:10px;font-weight:600;">DATA</p>', unsafe_allow_html=True)
                with col_h5: st.markdown('<p style="color:#22d3ee;font-size:10px;font-weight:600;">PROGRAMA</p>', unsafe_allow_html=True)
                with col_h6: st.markdown('<p style="color:#22d3ee;font-size:10px;font-weight:600;">SEL.</p>', unsafe_allow_html=True)
                
                st.markdown('<hr style="margin:2px 0;border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
                
                # LINHAS DA TABELA - cada linha com botao SELECIONAR
                for x in r:
                    rid = x[0]; num = x[1]; fonte = x[2]; val = format_currency(x[8])
                    data = x[9] or ""; prog = (x[10] or "")[:20]; setor = (x[11] or "")[:15]
                    
                    is_selected = st.session_state[sel_key] == rid
                    border_color = "#22d3ee" if is_selected else "rgba(34,211,238,0.1)"
                    bg_color = "rgba(34,211,238,0.08)" if is_selected else "transparent"
                    
                    cols = st.columns([1, 2, 2, 2, 2, 1])
                    with cols[0]:
                        st.markdown(f'<p style="color:#64748b;font-size:12px;margin:6px 0;">{rid}</p>', unsafe_allow_html=True)
                    with cols[1]:
                        st.markdown(f'<p style="color:#e0f2fe;font-weight:600;margin:6px 0;">{num} <span style="color:#22d3ee;">Fonte {fonte}</span></p>', unsafe_allow_html=True)
                    with cols[2]:
                        st.markdown(f'<p style="color:#00d4ff;font-weight:600;margin:6px 0;">{val}</p>', unsafe_allow_html=True)
                    with cols[3]:
                        st.markdown(f'<p style="color:#94a3b8;font-size:13px;margin:6px 0;">{data}</p>', unsafe_allow_html=True)
                    with cols[4]:
                        cor_texto = "#e0f2fe" if prog else "#64748b"
                        st.markdown(f'<p style="color:{cor_texto};font-size:11px;margin:6px 0;">{prog if prog else "--"}</p>', unsafe_allow_html=True)
                    with cols[5]:
                        if st.button("👉", key=f"sel_{tab_idx}_{rid}", help=f"Selecionar {num}"):
                            st.session_state[sel_key] = rid
                            st.rerun()
                
                st.markdown(f'<p style="color:#64748b;margin-top:10px;">Total: {len(r)} conta(s) {esf}</p>', unsafe_allow_html=True)
                
                # AREA EDITAR/EXCLUIR NA PARTE INFERIOR
                st.markdown('<hr>', unsafe_allow_html=True)
                st.markdown(f'<h4 style="color:#7dd3fc;">Editar / Excluir - {esf}</h4>', unsafe_allow_html=True)
                
                # Se uma conta foi selecionada, destaca no dropdown
                selected_id = st.session_state.get(sel_key)
                opts = {}
                for x in r:
                    opts[f"{x[1]} - Fonte {x[2]} (ID {x[0]})"] = x[0]
                opts["Selecione..."] = None
                
                # Define o valor default do dropdown baseado na selecao
                default_idx = 0  # "Selecione..."
                if selected_id:
                    for i, (k, v) in enumerate(opts.items()):
                        if v == selected_id:
                            default_idx = i
                            break
                
                opt_list = list(opts.keys())
                esc = st.selectbox(f"Selecione a conta", opt_list, index=default_idx, key=f"sel_{tab_idx}")
                
                if esc and opts[esc]:
                    rid = opts[esc]
                    st.session_state[sel_key] = rid
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✏️ Editar", key=f"e_{tab_idx}_{rid}"): st.session_state["edit_conta_id"] = rid; st.session_state["page"] = "EDITAR CONTA"; st.rerun()
                    with c2:
                        if st.button("🗑️ Excluir", key=f"d_{tab_idx}_{rid}"): conn.execute("DELETE FROM contas_receber WHERE id=?", (rid,)); conn.commit(); st.success("Excluida!"); st.rerun()
                else:
                    st.session_state[sel_key] = None
                    st.markdown('<p style="color:#94a3b8;font-size:13px;">Nenhuma conta selecionada. Clique em 👉 na linha desejada.</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p style="color:#94a3b8;">Nenhuma conta {esf}.</p>', unsafe_allow_html=True)
    
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#fbbf24;text-align:center;font-size:22px;">RECURSOS DE EXERCICIOS ANTERIORES / SUPERAVIT FINANCEIRO</h2>', unsafe_allow_html=True)
    sup = conn.execute("SELECT id, esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, created_at FROM superavit ORDER BY id DESC").fetchall()
    if sup:
        import pandas as pd
        spd = pd.DataFrame(sup, columns=["ID", "Esfera", "F. Original", "F. Superavit", "Saldo Total", "Saldo Restante", "Criado em"])
        spd["Saldo Total"] = spd["Saldo Total"].apply(lambda x: format_currency(x))
        spd["Saldo Restante"] = spd["Saldo Restante"].apply(lambda x: format_currency(x))
        st.dataframe(spd, use_container_width=True, hide_index=True)
    else: st.markdown('<p style="color:#94a3b8;">Nenhum superavit registrado.</p>', unsafe_allow_html=True)
    if st.button("MIGRAR SALDOS PARA SUPERAVIT"):
        for esf in ["Federal", "Estadual"]:
            total = conn.execute("SELECT COALESCE(SUM(valor_total),0) FROM contas_receber WHERE esfera=?", (esf,)).fetchone()[0]
            if total > 0:
                fo = get_fonte(esf); fs = get_fonte_superavit(esf)
                exist = conn.execute("SELECT id FROM superavit WHERE esfera=?", (esf,)).fetchone()
                agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                if exist: conn.execute("UPDATE superavit SET saldo_total=saldo_total+?, saldo_restante=saldo_restante+?, created_at=? WHERE esfera=?", (total, total, agora, esf))
                else: conn.execute("INSERT INTO superavit (esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, created_at) VALUES (?,?,?,?,?,?)", (esf, fo, fs, total, total, agora))
        conn.commit(); st.success("Saldos migrados!"); st.rerun()
    conn.close()
