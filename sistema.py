import streamlit as st
import sqlite3
import hashlib
import io
import re
from datetime import datetime

st.set_page_config(page_title="MARMED", layout="wide")

def format_currency(value):
    if value is None:
        value = 0.0
    return f"R$ {float(value):,.2f}"

def get_fonte(esfera):
    if esfera == "Federal":
        return "1.600"
    elif esfera == "Estadual":
        return "1.621"
    elif esfera == "Municipal":
        return "1.500"
    return ""

def get_fonte_superavit(esfera):
    if esfera == "Federal":
        return "2.600"
    elif esfera == "Estadual":
        return "2.621"
    return None

def extract_text_from_bytes(file_bytes, filename):
    """Tenta extrair texto de arquivos enviados."""
    text = ""
    try:
        if filename.lower().endswith('.txt'):
            text = file_bytes.decode('utf-8', errors='replace')
        elif filename.lower().endswith('.csv'):
            text = file_bytes.decode('utf-8', errors='replace')
        else:
            text = f"[Arquivo: {filename} - visualização de texto não disponível para este formato]"
    except:
        text = f"[Não foi possível extrair texto de {filename}]"
    return text

def init_db():
    conn = sqlite3.connect("marmed.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT)")
    c.execute("""
        CREATE TABLE IF NOT EXISTS contas_receber (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            esfera TEXT,
            numero_conta TEXT,
            fonte TEXT,
            referencia_tipo TEXT,
            referencia_numero TEXT,
            tipo_recurso TEXT,
            valor_pago_custeio REAL DEFAULT 0,
            valor_pago_investimento REAL DEFAULT 0,
            valor_total REAL DEFAULT 0,
            data_recebimento TEXT,
            programa_politica TEXT,
            setor_gasto TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS superavit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            esfera TEXT,
            fonte_original TEXT,
            fonte_superavit TEXT,
            saldo_total REAL DEFAULT 0,
            saldo_restante REAL DEFAULT 0,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS ordens_compra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conta_receber_id INTEGER,
            esfera TEXT,
            numero_conta TEXT,
            fonte TEXT,
            ficha TEXT,
            tipo_despesa TEXT,
            data_compra TEXT,
            valor_compra REAL DEFAULT 0,
            produto_servico TEXT,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS arquivos_saude (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bloco TEXT,
            nome_arquivo TEXT,
            conteudo_texto TEXT,
            dados_arquivo BLOB,
            data_upload TEXT
        )
    """)
    default_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("admin", default_hash))
    except:
        pass
    conn.commit()
    conn.close()

init_db()

def login_page():
    st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #0f172a, #1e3a8a, #0f172a); overflow: hidden; }
        div[data-testid="column"]:nth-child(2) {
            background: rgba(15, 23, 42, 0.75) !important;
            backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(14, 165, 233, 0.3) !important;
            border-radius: 24px !important;
            padding: 48px 40px !important;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5) !important;
            margin-top: 80px !important;
            max-width: 420px !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
        .marmed-title { font-size: 52px; font-weight: 800; text-align: center; color: #e0f2fe; letter-spacing: 6px; margin-bottom: 8px; }
        .subtitle { text-align: center; color: #7dd3fc; font-size: 14px; letter-spacing: 4px; margin-bottom: 36px; text-transform: uppercase; }
        .stTextInput label { color: #22d3ee !important; font-weight: 600; font-size: 13px; letter-spacing: 1px; }
        .stTextInput > div > div > input { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; color: #e0f2fe !important; border-radius: 10px !important; }
        .stButton > button { background: linear-gradient(90deg, #06b6d4, #3b82f6) !important; color: #fff !important; font-weight: 700 !important; border-radius: 10px !important; border: none !important; width: 100%; padding: 12px !important; letter-spacing: 2px; }
        .stSelectbox > div > div { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; border-radius: 10px !important; color: #e0f2fe !important; }
        .stDataFrame { background: rgba(15, 23, 42, 0.6) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; border-radius: 10px !important; }
        .stDataFrame td { color: #e0f2fe !important; }
        .stDataFrame th { color: #22d3ee !important; }
        .stFileUploader > div { background: rgba(30, 41, 59, 0.8) !important; border: 1px dashed rgba(34, 211, 238, 0.4) !important; border-radius: 10px !important; color: #e0f2fe !important; }
        .stTextArea > div > textarea { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; color: #e0f2fe !important; border-radius: 10px !important; }
        </style>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="marmed-title">MARMED</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">SISTEMA INTEGRADO DE GESTÃO</div>', unsafe_allow_html=True)
        username = st.text_input("USUÁRIO", key="login_user")
        password = st.text_input("SENHA", type="password", key="login_pass")
        if st.button("Acessar", key="login_btn"):
            pw_hash = hashlib.sha256(password.encode()).hexdigest()
            conn = sqlite3.connect("marmed.db")
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (username, pw_hash))
            user = c.fetchone()
            conn.close()
            if user:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["page"] = "Dashboard"
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")
        st.markdown('<p style="text-align:center;color:#94a3b8;font-size:12px;margin-top:28px;">Acesso restrito a usuários autorizados</p>', unsafe_allow_html=True)

def dashboard():
    st.markdown('<h1 style="color:#e0f2fe;text-align:center;font-size:48px;font-weight:800;letter-spacing:6px;">MARMED</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#7dd3fc;text-align:center;letter-spacing:4px;margin-bottom:4px;">SISTEMA INTEGRADO DE GESTÃO</h3>', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#1e40af;text-align:center;letter-spacing:3px;font-size:20px;font-weight:700;margin-bottom:16px;">PREFEITURA MUNICIPAL DE LUMINÁRIAS</h2>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    c = conn.cursor()
    esferas = ["REPASSE FEDERAL", "REPASSE ESTADUAL", "RECURSO MUNICIPAL", "TRANSFERÊNCIA", "TRANSPOSIÇÃO"]
    esf_keys = ["Federal", "Estadual", "Municipal", "Transferência", "Transposição"]
    cores = ["#3b82f6", "#22c55e", "#eab308", "#a855f7", "#ef4444"]
    cols = st.columns(5)
    for i, (tit, esf, cor) in enumerate(zip(esferas, esf_keys, cores)):
        total_contas = c.execute("SELECT COALESCE(SUM(valor_total),0) FROM contas_receber WHERE esfera=?", (esf,)).fetchone()[0]
        total_gasto = c.execute("SELECT COALESCE(SUM(valor_compra),0) FROM ordens_compra WHERE esfera=?", (esf,)).fetchone()[0]
        saldo = total_contas - total_gasto
        with cols[i]:
            st.markdown(f'<div style="background:linear-gradient(135deg,#1a2a3a,#0f2027);border-radius:15px;padding:15px;text-align:center;border-left:4px solid {cor};border:1px solid rgba(34,211,238,0.3);margin-bottom:8px;"><div style="color:#b0eaff;font-size:11px;letter-spacing:1px;font-weight:600;">{tit}</div><div style="color:#00d4ff;font-size:18px;font-weight:700;">{format_currency(total_contas)}</div><div style="color:#94a3b8;font-size:10px;margin-top:4px;">Saldo: {format_currency(saldo)}</div></div>', unsafe_allow_html=True)
            if st.button(f"Ver {esf}", key=f"btn_{esf}"):
                st.session_state["esfera_view"] = esf
                st.session_state["page"] = "ESFERA DETALHE"
                st.rerun()
    c.execute("SELECT COUNT(*) FROM contas_receber")
    tc = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ordens_compra")
    tco = c.fetchone()[0]
    conn.close()
    st.markdown(f'<p style="text-align:center;color:#64748b;font-size:12px;margin-top:10px;">{tc} conta(s) | {tco} ordem(ns) de compra - {datetime.now().strftime("%d/%m/%Y")}</p>', unsafe_allow_html=True)

def esfera_detalhe():
    esf = st.session_state.get("esfera_view", "Federal")
    st.markdown(f'<h1 style="color:#e0f2fe;">{esf.upper()}</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    contas = conn.execute("SELECT id, numero_conta, fonte, valor_total FROM contas_receber WHERE esfera=? ORDER BY id DESC", (esf,)).fetchall()
    if not contas:
        st.info(f"Nenhuma conta cadastrada para {esf}.")
    for cid, num, fonte, vtotal in contas:
        total_gasto = conn.execute("SELECT COALESCE(SUM(valor_compra),0) FROM ordens_compra WHERE conta_receber_id=?", (cid,)).fetchone()[0]
        saldo = vtotal - total_gasto
        with st.expander(f"{num} - Fonte {fonte}"):
            st.markdown(f'<p style="color:#b0eaff;">Nº: <strong>{num}</strong> | Fonte: <strong>{fonte}</strong> | Original: <strong>{format_currency(vtotal)}</strong> | Saldo: <strong style="color:{"#22c55e" if saldo>0 else "#ef4444"}">{format_currency(saldo)}</strong></p>', unsafe_allow_html=True)
            ordens = conn.execute("SELECT id, ficha, tipo_despesa, data_compra, valor_compra, produto_servico FROM ordens_compra WHERE conta_receber_id=? ORDER BY id DESC", (cid,)).fetchall()
            if ordens:
                for o in ordens:
                    st.markdown(f'<div style="background:rgba(30,41,59,0.6);border-radius:10px;padding:12px;margin-bottom:8px;border-left:3px solid #22d3ee;"><div style="color:#94a3b8;font-size:11px;">Ficha: {o[1] or "—"} | {o[2] or "—"} | {o[3] or "—"}</div><div style="color:#e0f2fe;font-size:14px;font-weight:600;">{format_currency(o[4])}</div><div style="color:#94a3b8;font-size:12px;">{o[5][:80]}{"..." if o[5] and len(o[5])>80 else ""}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#64748b;">Nenhuma ordem de compra.</p>', unsafe_allow_html=True)
    conn.close()
    if st.button("Voltar ao Início"):
        st.session_state["page"] = "Dashboard"
        st.rerun()

def cadastrar_contas():
    st.markdown('<h1 style="color:#e0f2fe;">CADASTRAR CONTAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    for k in ["esfera_cad", "val_custeio_cad", "val_invest_cad", "tipo_recurso_cad"]:
        st.session_state.pop(k, None)
    with st.expander("NOVO CADASTRO", expanded=True):
        st.markdown('<p style="color:#fbbf24;font-size:12px;margin-bottom:10px;">* Campos obrigatórios</p>', unsafe_allow_html=True)
        esfera = st.selectbox("* Esfera", ["", "Federal", "Estadual", "Municipal"], key="esfera_cad")
        fonte_auto = get_fonte(esfera)
        num_conta = st.text_input("* Número da Conta")
        if esfera:
            st.markdown(f'<p style="color:#22d3ee;font-weight:600;">Fonte: {fonte_auto}</p>', unsafe_allow_html=True)
        ref_contrato = st.selectbox("Referência do Contrato (opcional)", ["", "Resolução", "Deliberação", "Portaria"])
        num_ano_ref = st.text_input("Número/Ano (opcional)")
        tipo_recurso = st.selectbox("* Tipo de Recurso", ["", "Custeio", "Investimento", "Custeio/Investimento"], key="tipo_recurso_cad")
        val_custeio = st.number_input("* Valor Pago - Custeio", min_value=0.0, step=0.01, format="%.2f", key="val_custeio_cad")
        val_invest = st.number_input("* Valor Pago - Investimento", min_value=0.0, step=0.01, format="%.2f", key="val_invest_cad")
        val_total_calc = val_custeio + val_invest
        if val_total_calc > 0:
            st.markdown(f'<p style="color:#00d4ff;font-size:16px;font-weight:700;">Valor Total: {format_currency(val_total_calc)}</p>', unsafe_allow_html=True)
        data_receb = st.text_input("* Data de Recebimento", value=datetime.now().strftime("%d/%m/%Y"))
        programa_politica = st.text_input("Programa/Política (opcional)")
        setor_gasto = st.text_input("Setor de Referência de Gasto (opcional)")
        if st.button("Salvar Conta", key="salvar_conta"):
            erros = [x for x, v in [("Esfera", esfera), ("Nº Conta", num_conta), ("Tipo Recurso", tipo_recurso), ("Valor", val_total_calc>0), ("Data", data_receb)] if not v]
            if erros: st.error(f"Preencha: {', '.join(erros)}")
            else:
                conn = sqlite3.connect("marmed.db")
                conn.execute("INSERT INTO contas_receber (esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso, valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento, programa_politica, setor_gasto) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (esfera, num_conta, fonte_auto, ref_contrato, num_ano_ref, tipo_recurso, val_custeio, val_invest, val_total_calc, data_receb, programa_politica, setor_gasto))
                conn.commit()
                conn.close()
                st.success("Conta cadastrada! Campos limpos.")
                st.rerun()

def contas_cadastradas():
    st.markdown('<h1 style="color:#e0f2fe;">CONTAS CADASTRADAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    tab1, tab2, tab3 = st.tabs(["🔵 FEDERAL", "🟢 ESTADUAL", "🟡 MUNICIPAL"])
    for tab, esf in [(tab1, "Federal"), (tab2, "Estadual"), (tab3, "Municipal")]:
        with tab:
            registros = conn.execute("SELECT id, esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso, valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento, programa_politica, setor_gasto FROM contas_receber WHERE esfera=? ORDER BY id DESC", (esf,)).fetchall()
            if registros:
                import pandas as pd
                cols = ["ID", "Nº Conta", "Fonte", "Ref.", "Nº/Ano", "Tipo", "V. Custeio", "V. Invest.", "V. Total", "Data", "Programa", "Setor"]
                dados = [(r[0], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12]) for r in registros]
                pdf = pd.DataFrame(dados, columns=cols)
                for c in ["V. Custeio", "V. Invest.", "V. Total"]:
                    pdf[c] = pdf[c].apply(lambda x: format_currency(x))
                st.dataframe(pdf, use_container_width=True, hide_index=True)
                st.markdown(f'<p style="color:#64748b;font-size:12px;">Total: {len(registros)} conta(s) {esf}</p>', unsafe_allow_html=True)
                st.markdown(f'<h4 style="color:#7dd3fc;margin-top:15px;">Editar / Excluir - {esf}</h4>', unsafe_allow_html=True)
                opcoes = {f"{r[2]} - Fonte {r[3]} (ID {r[0]})": r[0] for r in registros}
                opcoes["Selecione..."] = None
                escolha = st.selectbox(f"Selecione uma conta {esf}", list(opcoes.keys()), key=f"sel_{esf}")
                if escolha and opcoes[escolha]:
                    rid = opcoes[escolha]
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Editar", key=f"edit_{esf}_{rid}"):
                            st.session_state["edit_conta_id"] = rid
                            st.session_state["page"] = "EDITAR CONTA"
                            st.rerun()
                    with c2:
                        if st.button("Excluir", key=f"del_{esf}_{rid}"):
                            conn.execute("DELETE FROM contas_receber WHERE id=?", (rid,))
                            conn.commit()
                            st.success("Conta excluída!")
                            st.rerun()
            else:
                st.markdown(f'<p style="color:#94a3b8;">Nenhuma conta {esf} cadastrada.</p>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.5);margin-top:30px;">', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#fbbf24;text-align:center;letter-spacing:2px;font-size:22px;">RECURSOS DE EXERCÍCIOS ANTERIORES / SUPERÁVIT FINANCEIRO</h2>', unsafe_allow_html=True)
    sup_df = conn.execute("SELECT id, esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, created_at FROM superavit ORDER BY id DESC").fetchall()
    if sup_df:
        import pandas as pd
        spdf = pd.DataFrame(sup_df, columns=["ID", "Esfera", "F. Original", "F. Superávit", "Saldo Total", "Saldo Restante", "Criado em"])
        spdf["Saldo Total"] = spdf["Saldo Total"].apply(lambda x: format_currency(x))
        spdf["Saldo Restante"] = spdf["Saldo Restante"].apply(lambda x: format_currency(x))
        st.dataframe(spdf, use_container_width=True, hide_index=True)
    else:
        st.markdown('<p style="color:#94a3b8;text-align:center;">Nenhum superávit registrado.</p>', unsafe_allow_html=True)
    if st.button("MIGRAR SALDOS PARA SUPERÁVIT", key="migrar_superavit"):
        for esf in ["Federal", "Estadual"]:
            total = conn.execute("SELECT COALESCE(SUM(valor_total),0) FROM contas_receber WHERE esfera=?", (esf,)).fetchone()[0]
            if total > 0:
                fonte_orig = get_fonte(esf)
                fonte_sup = get_fonte_superavit(esf)
                exist = conn.execute("SELECT id FROM superavit WHERE esfera=?", (esf,)).fetchone()
                agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                if exist:
                    conn.execute("UPDATE superavit SET saldo_total=saldo_total+?, saldo_restante=saldo_restante+?, created_at=? WHERE esfera=?", (total, total, agora, esf))
                else:
                    conn.execute("INSERT INTO superavit (esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, created_at) VALUES (?,?,?,?,?,?)", (esf, fonte_orig, fonte_sup, total, total, agora))
        conn.commit()
        st.success("Saldos migrados!")
        st.rerun()
    conn.close()

def editar_conta():
    st.markdown('<h1 style="color:#e0f2fe;">EDITAR CONTA</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    rid = st.session_state.get("edit_conta_id")
    if not rid:
        st.error("Nenhuma conta selecionada.")
        if st.button("Voltar"):
            st.session_state["page"] = "CONTAS CADASTRADAS"
            st.rerun()
        return
    conn = sqlite3.connect("marmed.db")
    row = conn.execute("SELECT * FROM contas_receber WHERE id=?", (rid,)).fetchone()
    if not row:
        conn.close()
        st.error("Conta não encontrada.")
        return
    esfera = st.selectbox("* Esfera", ["", "Federal", "Estadual", "Municipal"], index=["", "Federal", "Estadual", "Municipal"].index(row[1]) if row[1] in ["", "Federal", "Estadual", "Municipal"] else 0, key="esfera_edit")
    fonte_auto = get_fonte(esfera)
    num_conta = st.text_input("* Número da Conta", value=row[2] or "")
    if esfera:
        st.markdown(f'<p style="color:#22d3ee;font-weight:600;">Fonte: {fonte_auto}</p>', unsafe_allow_html=True)
    ref_contrato = st.selectbox("Referência do Contrato (opcional)", ["", "Resolução", "Deliberação", "Portaria"], index=["", "Resolução", "Deliberação", "Portaria"].index(row[4]) if row[4] in ["", "Resolução", "Deliberação", "Portaria"] else 0)
    num_ano_ref = st.text_input("Número/Ano (opcional)", value=row[5] or "")
    tipo_recurso = st.selectbox("* Tipo de Recurso", ["", "Custeio", "Investimento", "Custeio/Investimento"], index=["", "Custeio", "Investimento", "Custeio/Investimento"].index(row[6]) if row[6] in ["", "Custeio", "Investimento", "Custeio/Investimento"] else 0, key="tipo_recurso_edit")
    val_custeio = st.number_input("* Valor Pago - Custeio", min_value=0.0, step=0.01, format="%.2f", value=float(row[7] or 0))
    val_invest = st.number_input("* Valor Pago - Investimento", min_value=0.0, step=0.01, format="%.2f", value=float(row[8] or 0))
    val_total_calc = val_custeio + val_invest
    data_receb = st.text_input("* Data de Recebimento", value=row[10] or datetime.now().strftime("%d/%m/%Y"))
    programa_politica = st.text_input("Programa/Política (opcional)", value=row[11] or "")
    setor_gasto = st.text_input("Setor de Referência de Gasto (opcional)", value=row[12] or "")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Salvar Alterações"):
            conn.execute("UPDATE contas_receber SET esfera=?, numero_conta=?, fonte=?, referencia_tipo=?, referencia_numero=?, tipo_recurso=?, valor_pago_custeio=?, valor_pago_investimento=?, valor_total=?, data_recebimento=?, programa_politica=?, setor_gasto=? WHERE id=?", (esfera, num_conta, fonte_auto, ref_contrato, num_ano_ref, tipo_recurso, val_custeio, val_invest, val_total_calc, data_receb, programa_politica, setor_gasto, rid))
            conn.commit()
            conn.close()
            st.success("Conta atualizada!")
            st.session_state["page"] = "CONTAS CADASTRADAS"
            st.rerun()
    with c2:
        if st.button("Voltar"):
            st.session_state["page"] = "CONTAS CADASTRADAS"
            st.rerun()
    conn.close()

def realizar_compras():
    st.markdown('<h1 style="color:#e0f2fe;">REALIZAR COMPRAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    st.markdown('<h3 style="color:#7dd3fc;">Editar / Excluir Solicitações</h3>', unsafe_allow_html=True)
    ordens = conn.execute("SELECT oc.id, oc.esfera, oc.numero_conta, oc.fonte, oc.ficha, oc.tipo_despesa, oc.data_compra, oc.valor_compra, oc.produto_servico FROM ordens_compra oc ORDER BY oc.id DESC").fetchall()
    if ordens:
        opcoes_ordem = {f"{o[1]} - Conta {o[2]} - Ficha {o[4] or '—'} (R$ {o[7]:.2f}) - ID {o[0]}": o[0] for o in ordens}
        opcoes_ordem["Selecione..."] = None
        escolha_ordem = st.selectbox("Selecione uma solicitação", list(opcoes_ordem.keys()), key="sel_ordem")
        if escolha_ordem and opcoes_ordem[escolha_ordem]:
            oid = opcoes_ordem[escolha_ordem]
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Editar", key=f"edit_ordem_{oid}"):
                    st.session_state["edit_ordem_id"] = oid
                    st.session_state["page"] = "EDITAR ORDEM COMPRA"
                    st.rerun()
            with c2:
                if st.button("Excluir", key=f"del_ordem_{oid}"):
                    conn.execute("DELETE FROM ordens_compra WHERE id=?", (oid,))
                    conn.commit()
                    st.success("Solicitação excluída!")
                    st.rerun()
    else:
        st.markdown('<p style="color:#94a3b8;">Nenhuma solicitação registrada.</p>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);margin-top:20px;">', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#7dd3fc;">Nova Solicitação</h3>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["🔵 FEDERAL", "🟢 ESTADUAL", "🟡 MUNICIPAL"])
    for tab, esf in [(tab1, "Federal"), (tab2, "Estadual"), (tab3, "Municipal")]:
        with tab:
            contas = conn.execute("SELECT id, esfera, numero_conta, fonte, tipo_recurso, valor_total FROM contas_receber WHERE esfera=? ORDER BY id DESC", (esf,)).fetchall()
            if not contas:
                st.markdown(f'<p style="color:#94a3b8;">Nenhuma conta {esf} disponível.</p>', unsafe_allow_html=True)
            else:
                for cid, esfera, num, fonte, trecurso, vtotal in contas:
                    total_gasto = conn.execute("SELECT COALESCE(SUM(valor_compra),0) FROM ordens_compra WHERE conta_receber_id=?", (cid,)).fetchone()[0]
                    saldo = vtotal - total_gasto
                    with st.expander(f"{num} - Fonte {fonte}"):
                        st.markdown(f'<div style="background:rgba(30,41,59,0.6);border-radius:10px;padding:12px;margin-bottom:10px;"><div style="display:flex;justify-content:space-between;"><div style="color:#94a3b8;">Conta: <span style="color:#e0f2fe;">{num}</span></div><div style="color:#94a3b8;">Fonte: <span style="color:#22d3ee;">{fonte}</span></div><div style="color:#94a3b8;">Valor: <span style="color:#00d4ff;">{format_currency(vtotal)}</span></div><div style="color:#94a3b8;">Saldo: <span style="color:{"#22c55e" if saldo>0 else "#ef4444"};">{format_currency(saldo)}</span></div></div></div>', unsafe_allow_html=True)
                        if esf != "Municipal":
                            saldo_sup = conn.execute("SELECT COALESCE(SUM(saldo_restante),0) FROM superavit WHERE esfera=? AND saldo_restante>0", (esf,)).fetchone()[0]
                            if saldo_sup > 0:
                                st.warning(f"Superávit de {format_currency(saldo_sup)} para {esf}. Utilize-o antes.")
                        with st.form(key=f"form_compra_{esf}_{cid}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                ficha = st.text_input("Ficha")
                                tipo_desp = st.selectbox("Tipo de Despesa", ["", "Material de Consumo", "Serviço de Terceiro Pessoa Física", "Serviço de Terceiro Pessoa Jurídica", "Distribuição Gratuita"], key=f"td_{esf}_{cid}")
                                data_compra = st.text_input("Data da Compra", value=datetime.now().strftime("%d/%m/%Y"))
                            with col2:
                                valor_compra = st.number_input("Valor da Compra", min_value=0.0, step=0.01, format="%.2f")
                                if valor_compra > saldo:
                                    st.markdown(f'<p style="color:#ef4444;font-size:12px;">Excede saldo de {format_currency(saldo)}</p>', unsafe_allow_html=True)
                            produto_servico = st.text_area("Produto/Serviço", height=120)
                            if st.form_submit_button(f"Solicitar Compra - {num}"):
                                erros = [x for x, v in [("Ficha", ficha), ("Tipo", tipo_desp), ("Data", data_compra), ("Valor", valor_compra>0), ("Produto/Serviço", produto_servico), ("Saldo", valor_compra<=saldo)] if not v]
                                if erros: st.error(f"Preencha: {', '.join(erros)}")
                                else:
                                    conn.execute("INSERT INTO ordens_compra (conta_receber_id, esfera, numero_conta, fonte, ficha, tipo_despesa, data_compra, valor_compra, produto_servico, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)", (cid, esf, num, fonte, ficha, tipo_desp, data_compra, valor_compra, produto_servico, datetime.now().strftime("%d/%m/%Y %H:%M:%S")))
                                    conn.commit()
                                    st.success(f"Solicitação registrada!")
                                    st.rerun()
    conn.close()

def editar_ordem_compra():
    st.markdown('<h1 style="color:#e0f2fe;">EDITAR SOLICITAÇÃO</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    oid = st.session_state.get("edit_ordem_id")
    if not oid:
        st.error("Nenhuma selecionada.")
        if st.button("Voltar"):
            st.session_state["page"] = "REALIZAR COMPRAS"
            st.rerun()
        return
    conn = sqlite3.connect("marmed.db")
    row = conn.execute("SELECT * FROM ordens_compra WHERE id=?", (oid,)).fetchone()
    if not row:
        conn.close()
        st.error("Não encontrada.")
        return
    ficha = st.text_input("Ficha", value=row[5] or "")
    tipo_desp = st.selectbox("Tipo de Despesa", ["", "Material de Consumo", "Serviço de Terceiro Pessoa Física", "Serviço de Terceiro Pessoa Jurídica", "Distribuição Gratuita"], index=["", "Material de Consumo", "Serviço de Terceiro Pessoa Física", "Serviço de Terceiro Pessoa Jurídica", "Distribuição Gratuita"].index(row[6]) if row[6] in ["", "Material de Consumo", "Serviço de Terceiro Pessoa Física", "Serviço de Terceiro Pessoa Jurídica", "Distribuição Gratuita"] else 0, key="td_edit")
    data_compra = st.text_input("Data", value=row[7] or datetime.now().strftime("%d/%m/%Y"))
    valor_compra = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f", value=float(row[8] or 0))
    produto_servico = st.text_area("Produto/Serviço", height=120, value=row[9] or "")
    st.markdown(f'<p style="color:#94a3b8;">Conta: {row[3]} | Esfera: {row[2]} | Fonte: {row[4]}</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Salvar"):
            conn.execute("UPDATE ordens_compra SET ficha=?, tipo_despesa=?, data_compra=?, valor_compra=?, produto_servico=? WHERE id=?", (ficha, tipo_desp, data_compra, valor_compra, produto_servico, oid))
            conn.commit()
            conn.close()
            st.success("Atualizada!")
            st.session_state["page"] = "REALIZAR COMPRAS"
            st.rerun()
    with c2:
        if st.button("Voltar"):
            st.session_state["page"] = "REALIZAR COMPRAS"
            st.rerun()
    conn.close()

def change_password():
    st.markdown('<h1 style="color:#e0f2fe;">Trocar Senha</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    current = st.text_input("Senha atual", type="password")
    new_pass = st.text_input("Nova senha", type="password")
    confirm = st.text_input("Confirmar nova senha", type="password")
    if st.button("Salvar nova senha"):
        if new_pass != confirm:
            st.error("As senhas não conferem")
        else:
            ch = hashlib.sha256(current.encode()).hexdigest()
            conn = sqlite3.connect("marmed.db")
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE username=? AND password_hash=?", (st.session_state["username"], ch))
            row = c.fetchone()
            if row:
                nh = hashlib.sha256(new_pass.encode()).hexdigest()
                c.execute("UPDATE users SET password_hash=? WHERE id=?", (nh, row[0]))
                conn.commit()
                conn.close()
                st.success("Senha alterada com sucesso")
            else:
                conn.close()
                st.error("Senha atual incorreta")

# ============================================================
# PROGRAMAS DE SAÚDE
# ============================================================

def bloco_saude(titulo, sigla, explicacao, site_url, cor_topo="#1e40af"):
    """Renderiza um bloco de saúde com explicação, link, upload e busca."""
    st.markdown(f'<div style="background:linear-gradient(135deg,{cor_topo},{"#0f172a"});border-radius:12px;padding:15px;margin-bottom:15px;border-left:4px solid #22d3ee;">', unsafe_allow_html=True)
    st.markdown(f'<h3 style="color:#22d3ee;margin:0;">{sigla}</h3>', unsafe_allow_html=True)
    st.markdown(f'<p style="color:#b0eaff;font-size:13px;margin-bottom:10px;">{titulo}</p>', unsafe_allow_html=True)
    st.markdown(f'<div style="background:rgba(15,23,42,0.5);border-radius:8px;padding:12px;color:#e0f2fe;font-size:13px;line-height:1.5;">{explicacao}</div>', unsafe_allow_html=True)
    
    if site_url:
        st.markdown(f'<a href="{site_url}" target="_blank" style="display:inline-block;margin-top:10px;padding:8px 16px;background:#22d3ee;color:#0f172a;border-radius:8px;text-decoration:none;font-weight:700;font-size:13px;">🔗 Acessar Site Oficial</a>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.expander(f"📁 Documentos anexados - {sigla}", expanded=False):
        conn = sqlite3.connect("marmed.db")
        
        uploaded = st.file_uploader(f"Enviar arquivo (PDF, Word, TXT, CSV)", type=["pdf", "docx", "doc", "txt", "csv"], key=f"upload_{sigla}")
        if uploaded:
            dados_bytes = uploaded.read()
            texto_extraido = extract_text_from_bytes(dados_bytes, uploaded.name)
            conn.execute("INSERT INTO arquivos_saude (bloco, nome_arquivo, conteudo_texto, dados_arquivo, data_upload) VALUES (?,?,?,?,?)", (sigla, uploaded.name, texto_extraido, dados_bytes, datetime.now().strftime("%d/%m/%Y %H:%M")))
            conn.commit()
            st.success(f"Arquivo '{uploaded.name}' anexado com sucesso!")
            st.rerun()
        
        arquivos = conn.execute("SELECT id, nome_arquivo, data_upload, conteudo_texto FROM arquivos_saude WHERE bloco=? ORDER BY id DESC", (sigla,)).fetchall()
        if arquivos:
            st.markdown(f'<p style="color:#94a3b8;font-size:12px;">{len(arquivos)} arquivo(s) anexado(s)</p>', unsafe_allow_html=True)
            for arq in arquivos:
                st.markdown(f'<div style="background:rgba(30,41,59,0.6);border-radius:6px;padding:8px;margin-bottom:5px;border-left:2px solid #22d3ee;"><span style="color:#e0f2fe;">📄 {arq[1]}</span> <span style="color:#64748b;font-size:11px;">— {arq[2]}</span></div>', unsafe_allow_html=True)
            
            # Pesquisa nos documentos
            st.markdown(f'<p style="color:#7dd3fc;font-size:13px;margin-top:10px;">🔍 Pesquisar nos documentos anexados</p>', unsafe_allow_html=True)
            termo = st.text_input("Digite a palavra ou frase para buscar", key=f"busca_{sigla}")
            if termo:
                encontrou = False
                for arq in arquivos:
                    texto = arq[3] or ""
                    matches = list(re.finditer(re.escape(termo), texto, re.IGNORECASE))
                    if matches:
                        encontrou = True
                        st.markdown(f'<p style="color:#22d3ee;font-weight:600;margin-top:8px;">📄 {arq[1]}</p>', unsafe_allow_html=True)
                        for m in matches[:5]:  # Mostra até 5 ocorrências
                            start = max(0, m.start() - 80)
                            end = min(len(texto), m.end() + 80)
                            trecho = texto[start:end]
                            # Destaca o termo encontrado
                            trecho_destacado = re.sub(re.escape(termo), f'<span style="background:#fbbf24;color:#000;padding:1px 3px;border-radius:3px;font-weight:700;">{termo}</span>', trecho, flags=re.IGNORECASE)
                            st.markdown(f'<div style="background:rgba(15,23,42,0.5);border-radius:6px;padding:8px;margin-bottom:4px;color:#94a3b8;font-size:12px;font-family:monospace;">...{trecho_destacado}...</div>', unsafe_allow_html=True)
                if not encontrou:
                    st.markdown(f'<p style="color:#94a3b8;">Nenhuma ocorrência de "{termo}" encontrada nos documentos.</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#64748b;">Nenhum documento anexado ainda. Faça o upload acima.</p>', unsafe_allow_html=True)
        
        conn.close()

def programas_saude():
    st.markdown('<h1 style="color:#e0f2fe;">PROGRAMAS DE SAÚDE</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    
    # Agrupa em tabs grandes
    tab_med, tab_gestao, tab_fin, tab_reg, tab_cons = st.tabs([
        "💊 MEDICAMENTOS", "🏛️ GESTÃO", "💰 FINANCIAMENTO", "📋 REGULAÇÃO", "🤝 CONSÓRCIOS"
    ])
    
    with tab_med:
        bloco_saude(
            "Relação Nacional de Medicamentos Essenciais",
            "RENAME",
            """A <strong>RENAME</strong> (Relação Nacional de Medicamentos Essenciais) é a lista oficial do Ministério da Saúde que define quais medicamentos e insumos são oferecidos gratuitamente pelo SUS. Ela serve para orientar o tratamento, garantir o acesso da população e organizar o financiamento entre União, estados e municípios.<br><br>
Além de servir de guia para médicos e pacientes, a RENAME é a base utilizada pelo SUS para compras públicas, incentivando o uso racional de remédios padronizados para as doenças mais recorrentes no país. Cada estado e município pode criar a sua própria lista, mas ela deve ser baseada nesta relação nacional.""",
            "https://www.gov.br/saude/pt-br/assuntos/assistencia-farmaceutica-no-sus/rename",
            "#0891b2"
        )
        
        bloco_saude(
            "Relação Municipal de Medicamentos Essenciais",
            "REMUME",
            """A <strong>REMUME</strong> (Relação Municipal de Medicamentos Essenciais) é a lista oficial de medicamentos disponibilizados gratuitamente pelo SUS na rede pública de cada município. Ela orienta a prescrição médica e garante que a população tenha acesso aos remédios essenciais para as principais necessidades de saúde.<br><br>
<strong>Componentes:</strong><br>
• <strong>Componente Básico:</strong> Medicamentos para atenção primária (postos de saúde).<br>
• <strong>Componente Estratégico:</strong> Fármacos para doenças de controle prioritário ou endemias.<br>
• <strong>Componente Especializado:</strong> Medicamentos de alto custo fornecidos pelo Estado/Município.""",
            "https://bvsms.saude.gov.br/bvs/publicacoes/rename_2022.pdf",
            "#0e7490"
        )
        
        bloco_saude(
            "Relação Nacional de Equipamentos e Materiais Permanentes",
            "RENEM",
            """A <strong>RENEM</strong> (Relação Nacional de Equipamentos e Materiais Permanentes) é a lista oficial do Ministério da Saúde que padroniza e determina quais equipamentos e materiais médico-hospitalares podem ser financiados pelo SUS. Ela é usada para guiar investimentos e compras de entidades públicas e privadas sem fins lucrativos.<br><br>
<strong>Principais características:</strong><br>
• <strong>Lista de Itens:</strong> Inclui desde itens simples (como macas e adipômetros) até equipamentos de alta complexidade (como aceleradores lineares).<br>
• <strong>Valores de Referência:</strong> A lista estabelece valores base que orientam o repasse de verbas federais.<br>
• <strong>Atualização:</strong> O Ministério da Saúde realiza atualizações periódicas em parceria com o PROCOT.""",
            "https://portalfns.saude.gov.br/",
            "#155e75"
        )
        
        bloco_saude(
            "Relação Nacional de Ações e Serviços de Saúde",
            "RENASES",
            """A <strong>RENASES</strong> foi instituída para assegurar o direito à integralidade da assistência, ou seja, garante que o paciente não tenha acesso apenas a um remédio, mas a todo o ciclo de cuidado necessário para tratar sua saúde.<br><br>
<strong>O que compõe a RENASES?</strong><br>
• <strong>Atenção Primária:</strong> Postos de saúde, consultas médicas básicas e vacinação.<br>
• <strong>Urgência e Emergência:</strong> Atendimento em UPAs e pronto-socorros.<br>
• <strong>Atenção Especializada e Hospitalar:</strong> Consultas com especialistas, exames de alta complexidade e internações.<br>
• <strong>Atenção Psicossocial:</strong> Tratamentos em CAPS (Centros de Atenção Psicossocial).<br>
• <strong>Vigilância em Saúde:</strong> Ações de controle de epidemias e saneamento.""",
            "https://www.gov.br/saude/pt-br/acesso-a-informacao/acoes-e-programas/renases",
            "#164e63"
        )
    
    with tab_gestao:
        bloco_saude(
            "Plataforma de Gestão da Atenção Primária à Saúde",
            "E-GESTOR APS",
            """O <strong>e-Gestor APS</strong> (Atenção Primária à Saúde) é a plataforma oficial do Governo Federal/Ministério da Saúde voltada para o Sistema Único de Saúde (SUS).<br><br>
<strong>O que faz:</strong> Centraliza os acessos a diversos sistemas da Atenção Básica, como histórico de cobertura, acompanhamento de equipes de saúde da família, programas como o Mais Médicos e dados de financiamento.<br><br>
<strong>Acesso:</strong> Possui uma área de Acesso Público (com relatórios e dados abertos para a população) e uma Área Restrita (para gestores municipais e estaduais administrarem recursos e enviarem informações).""",
            "https://egestorab.saude.gov.br/",
            "#0369a1"
        )
        
        bloco_saude(
            "Nova Plataforma de Regulação de Leitos - SES/MG",
            "CORE SAÚDE MG",
            """O <strong>Core Saúde MG</strong> é a nova plataforma digital da Secretaria de Estado de Saúde de Minas Gerais (SES-MG). Ele substituiu o antigo sistema SUSfácil para gerenciar e organizar a fila única de leitos hospitalares, cirurgias, consultas e exames do SUS.<br><br>
<strong>Objetivos:</strong><br>
• <strong>Mais Transparência:</strong> Utiliza fila única e critérios técnicos estaduais, evitando interferências na ordem de atendimento.<br>
• <strong>Decisões Baseadas em Dados:</strong> O paciente é direcionado pelo médico regulador do Estado de forma ágil, com monitoramento em tempo real.<br>
• <strong>Regulação 4.0:</strong> Padroniza fluxos assistenciais em todo o território mineiro.""",
            "https://www.saude.mg.gov.br/",
            "#075985"
        )
    
    with tab_fin:
        bloco_saude(
            "Fundo Nacional de Saúde - Gestor Financeiro do SUS",
            "FNS",
            """O <strong>Fundo Nacional de Saúde (FNS)</strong> é o gestor financeiro dos recursos do Ministério da Saúde na esfera federal.<br><br>
<strong>Como Funciona e o que Financia:</strong> O FNS centraliza o orçamento federal da saúde e distribui esses montantes para estados, municípios, Distrito Federal e entidades parceiras do SUS. Esses repasses são utilizados para:<br><br>
<strong>Custeio:</strong> Manutenção de hospitais, postos de saúde, compra de medicamentos e pagamento de profissionais.<br>
<strong>Investimentos:</strong> Construção de novas unidades de saúde, reformas e compra de equipamentos.<br><br>
<strong>Modalidades de Repasse:</strong><br>
• <strong>Fundo a Fundo:</strong> Transferência direta e automática do Fundo Nacional para os fundos estaduais e municipais de saúde.<br>
• <strong>Convênios e Termos de Cooperação:</strong> Transferências condicionadas a projetos específicos.""",
            "https://portalfns.saude.gov.br/",
            "#1d4ed8"
        )
        
        bloco_saude(
            "Sistema de Gerenciamento da Tabela de Procedimentos",
            "SIGTAP",
            """O <strong>SIGTAP</strong> (Sistema de Gerenciamento da Tabela de Procedimentos, Medicamentos e OPM do SUS) é a tabela oficial do Ministério da Saúde que padroniza todos os procedimentos, medicamentos e Órteses, Próteses e Materiais Especiais (OPM) utilizados no Sistema Único de Saúde (SUS).<br><br>
<strong>O que você encontra na tabela:</strong><br>
• <strong>Códigos e Valores:</strong> Identificação numérica de cada exame, cirurgia ou consulta, junto com o valor repassado pelo SUS.<br>
• <strong>Regras e Compatibilidades:</strong> Define quais procedimentos podem ser feitos juntos.<br>
• <strong>Instrumentos de Registro:</strong> Indica qual documento deve ser preenchido (AIH para internações ou BPA para ambulatório).<br>
• <strong>Nível de Complexidade:</strong> Classifica a ação em Atenção Básica, Média ou Alta Complexidade.""",
            "http://sigtap.datasus.gov.br/tabela-unificada/app/sec/inicio.jsp",
            "#1e3a8a"
        )
        
        bloco_saude(
            "Consolidação da Programação Pactuada Integrada",
            "PPI / CONSOLIDAÇÃO",
            """A <strong>consolidação da PPI</strong> refere-se à etapa final do planejamento de saúde, onde os dados da Programação Pactuada Integrada (PPI) são unificados. No Sistema Único de Saúde (SUS), esse processo unifica metas físicas e orçamentárias (como exames e consultas) para que os municípios e estados controlem e distribuam os recursos financeiros de forma centralizada.<br><br>
A PPI é o instrumento que organiza a rede de serviços do SUS, definindo o fluxo de pacientes entre municípios e garantindo que cada gestor saiba exatamente quanto destinar para cada tipo de procedimento.""",
            "http://datasus.saude.gov.br/informacoes-de-saude/tabnet",
            "#1e40af"
        )
    
    with tab_reg:
        bloco_saude(
            "Conselho Nacional de Secretarias Municipais de Saúde",
            "CONASEMS",
            """O <strong>CONASEMS</strong> (Conselho Nacional de Secretarias Municipais de Saúde) é uma associação civil sem fins lucrativos que representa e congrega as Secretarias Municipais de Saúde de todo o Brasil.<br><br>
<strong>Principais funções:</strong><br>
• <strong>Representatividade:</strong> Representa os interesses de todos os municípios brasileiros nas instâncias de negociação e decisão do SUS (Comissão Intergestora Tripartite).<br>
• <strong>Apoio aos Gestores:</strong> Oferece suporte técnico, jurídico e político aos secretários municipais de saúde.<br>
• <strong>Capacitação:</strong> Atua fortemente na área de educação continuada para trabalhadores e gestores do SUS.<br>
• <strong>Eventos:</strong> Promove o maior congresso de saúde pública do mundo.<br><br>
<strong>Diferença entre CONASEMS, COSEMS e CONASS:</strong><br>
• <strong>CONASEMS:</strong> Municípios em âmbito nacional.<br>
• <strong>COSEMS:</strong> Municípios em âmbito estadual.<br>
• <strong>CONASS:</strong> Representa as Secretarias de Estado da Saúde.""",
            "https://conasems.org.br/",
            "#4338ca"
        )
        
        bloco_saude(
            "Conselho de Secretarias Municipais de Saúde de MG",
            "COSEMS MG",
            """O <strong>COSEMS MG</strong> (Conselho de Secretarias Municipais de Saúde de Minas Gerais) é uma entidade sem fins lucrativos que representa os gestores municipais de saúde dos 853 municípios mineiros. Ele atua como o principal elo entre os Secretários de Saúde e as esferas estadual e federal.<br><br>
<strong>Principais Funções:</strong><br>
• <strong>Representação Política:</strong> Defende os interesses dos municípios na formulação, implantação e avaliação de políticas públicas de saúde.<br>
• <strong>Articulação Institucional:</strong> Participa ativamente de instâncias decisórias, como a Comissão Intergestores Bipartite (CIB).<br>
• <strong>Apoio Técnico:</strong> Oferece suporte, capacitação e intercâmbio de experiências para os gestores e equipes de saúde em todo o estado.<br><br>
O COSEMS MG se divide em representações regionais, que acompanham de perto a realidade das 28 regionais de saúde de Minas Gerais.""",
            "https://www.cosemsmg.org.br/",
            "#3730a3"
        )
    
    with tab_cons:
        bloco_saude(
            "Consórcio Intermunicipal de Saúde da Microrregião de Lavras",
            "CISLAV",
            """O <strong>CISLAV</strong> é o Consórcio Intermunicipal de Saúde dos Municípios da Microrregião de Lavras. Trata-se de uma associação pública que une prefeituras da região para otimizar recursos e melhorar o atendimento médico pelo SUS.<br><br>
<strong>O que oferece:</strong><br>
• Permite que cidades menores compartilhem custos de consultas especializadas, exames e transporte de pacientes (como o Transporta SUS).<br>
• Fortalece ações regionais de vigilância sanitária.<br>
• Viabiliza a aquisição conjunta de medicamentos e insumos.<br>
• Promove a regionalização da saúde, garantindo atendimento mais próximo à população.""",
            "https://www.cislav.com/",
            "#312e81"
        )

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "page" not in st.session_state:
        st.session_state["page"] = "Dashboard"
    if not st.session_state["logged_in"]:
        login_page()
    else:
        st.sidebar.markdown('<h3 style="color:#22d3ee;text-align:center;letter-spacing:2px;">MENU PRINCIPAL</h3>', unsafe_allow_html=True)
        st.sidebar.markdown('<hr>', unsafe_allow_html=True)
        st.sidebar.markdown('<p style="color:#7dd3fc;font-size:12px;letter-spacing:1px;margin-bottom:5px;">GESTÃO FINANCEIRA</p>', unsafe_allow_html=True)
        if st.sidebar.button("📊 INÍCIO", key="nav_inicio", use_container_width=True):
            st.session_state["page"] = "Dashboard"
            st.rerun()
        if st.sidebar.button("📝 CADASTRAR CONTAS", key="nav_cadastrar", use_container_width=True):
            st.session_state["page"] = "CADASTRAR CONTAS"
            st.rerun()
        if st.sidebar.button("📋 CONTAS CADASTRADAS", key="nav_cadastradas", use_container_width=True):
            st.session_state["page"] = "CONTAS CADASTRADAS"
            st.rerun()
        if st.sidebar.button("🛒 REALIZAR COMPRAS", key="nav_compras", use_container_width=True):
            st.session_state["page"] = "REALIZAR COMPRAS"
            st.rerun()
        st.sidebar.markdown('<hr>', unsafe_allow_html=True)
        st.sidebar.markdown('<p style="color:#7dd3fc;font-size:12px;letter-spacing:1px;margin-bottom:5px;">SAÚDE PÚBLICA</p>', unsafe_allow_html=True)
        if st.sidebar.button("🏥 PROGRAMAS DE SAÚDE", key="nav_saude", use_container_width=True):
            st.session_state["page"] = "PROGRAMAS SAUDE"
            st.rerun()
        st.sidebar.markdown('<hr>', unsafe_allow_html=True)
        if st.sidebar.button("🚪 Sair", key="logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state.pop("username", None)
            st.rerun()
        page = st.session_state["page"]
        if page == "Dashboard":
            dashboard()
        elif page == "CADASTRAR CONTAS":
            cadastrar_contas()
        elif page == "CONTAS CADASTRADAS":
            contas_cadastradas()
        elif page == "EDITAR CONTA":
            editar_conta()
        elif page == "REALIZAR COMPRAS":
            realizar_compras()
        elif page == "EDITAR ORDEM COMPRA":
            editar_ordem_compra()
        elif page == "ESFERA DETALHE":
            esfera_detalhe()
        elif page == "PROGRAMAS SAUDE":
            programas_saude()
        elif page == "Trocar Senha":
            change_password()

if __name__ == "__main__":
    main()
