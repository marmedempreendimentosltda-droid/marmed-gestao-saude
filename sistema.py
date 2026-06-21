import streamlit as st
import sqlite3
import hashlib
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

def init_db():
    conn = sqlite3.connect("marmed.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT)")
    c.execute("DROP TABLE IF EXISTS contas_receber")
    c.execute("""
        CREATE TABLE contas_receber (
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
    c.execute("DROP TABLE IF EXISTS superavit")
    c.execute("""
        CREATE TABLE superavit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            esfera TEXT,
            fonte_original TEXT,
            fonte_superavit TEXT,
            saldo_total REAL DEFAULT 0,
            saldo_restante REAL DEFAULT 0,
            created_at TEXT
        )
    """)
    c.execute("DROP TABLE IF EXISTS compras")
    c.execute("""
        CREATE TABLE compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT,
            quantidade REAL,
            valor_unitario REAL,
            valor_total REAL,
            data TEXT,
            setor TEXT,
            esfera TEXT,
            fonte TEXT
        )
    """)
    default_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)", ("admin", default_hash))
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
        .stSelectbox label { color: #22d3ee !important; font-weight: 600; font-size: 13px; letter-spacing: 1px; }
        .stNumberInput label { color: #22d3ee !important; font-weight: 600; font-size: 13px; letter-spacing: 1px; }
        .stTextInput > div > div > input { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; color: #e0f2fe !important; border-radius: 10px !important; }
        .stButton > button { background: linear-gradient(90deg, #06b6d4, #3b82f6) !important; color: #fff !important; font-weight: 700 !important; border-radius: 10px !important; border: none !important; width: 100%; padding: 12px !important; letter-spacing: 2px; }
        .stSelectbox > div > div { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; border-radius: 10px !important; color: #e0f2fe !important; }
        .stNumberInput > div > div > input { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; color: #e0f2fe !important; border-radius: 10px !important; }
        .stDataFrame { background: rgba(15, 23, 42, 0.6) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; border-radius: 10px !important; }
        .stDataFrame td { color: #e0f2fe !important; }
        .stDataFrame th { color: #22d3ee !important; }
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
    c.execute("SELECT COALESCE(SUM(valor_total),0) FROM contas_receber WHERE esfera='Federal'")
    total_federal = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(valor_total),0) FROM contas_receber WHERE esfera='Estadual'")
    total_estadual = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(valor_total),0) FROM contas_receber WHERE esfera='Municipal'")
    total_municipal = c.fetchone()[0]
    c.execute("SELECT COALESCE(COUNT(*),0) FROM contas_receber")
    total_contas = c.fetchone()[0]
    c.execute("SELECT COALESCE(COUNT(*),0) FROM compras")
    total_compras = c.fetchone()[0]
    conn.close()
    cols = st.columns(5)
    dados = [
        ("REPASSE FEDERAL", total_federal, "#3b82f6"),
        ("REPASSE ESTADUAL", total_estadual, "#22c55e"),
        ("RECURSO MUNICIPAL", total_municipal, "#eab308"),
        ("TRANSFERÊNCIA", 0, "#a855f7"),
        ("TRANSPOSIÇÃO", 0, "#ef4444")
    ]
    for i, (tit, val, cor) in enumerate(dados):
        with cols[i]:
            st.markdown(f'<div style="background:linear-gradient(135deg,#1a2a3a,#0f2027);border-radius:15px;padding:20px;text-align:center;border-left:4px solid {cor};border:1px solid rgba(34,211,238,0.3);min-height:130px;display:flex;flex-direction:column;justify-content:center;"><div style="color:#b0eaff;font-size:11px;letter-spacing:1px;font-weight:600;margin-bottom:8px;">{tit}</div><div style="color:#00d4ff;font-size:20px;font-weight:700;">{format_currency(val)}</div></div>', unsafe_allow_html=True)
    st.markdown(f'<p style="text-align:center;color:#64748b;font-size:12px;margin-top:20px;">{total_contas} conta(s) cadastrada(s) | {total_compras} compra(s) - Painel gerencial MARMED - {datetime.now().strftime("%d/%m/%Y")}</p>', unsafe_allow_html=True)

def cadastrar_contas():
    st.markdown('<h1 style="color:#e0f2fe;">CADASTRAR CONTAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    df = conn.execute("SELECT id, esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso, valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento, programa_politica, setor_gasto FROM contas_receber ORDER BY id DESC").fetchall()
    cols = ["ID", "Esfera", "Nº Conta", "Fonte", "Referência", "Nº/Ano", "Tipo Recurso", "Valor Custeio", "Valor Investimento", "Valor Total", "Data Receb.", "Programa/Política", "Setor Gasto"]
    conn.close()
    if df:
        import pandas as pd
        pdf = pd.DataFrame(df, columns=cols)
        for c in ["Valor Custeio", "Valor Investimento", "Valor Total"]:
            pdf[c] = pdf[c].apply(lambda x: format_currency(x))
        st.dataframe(pdf, use_container_width=True, hide_index=True)
    with st.expander("NOVO CADASTRO", expanded=False):
        st.markdown('<p style="color:#fbbf24;font-size:12px;margin-bottom:10px;">* Campos obrigatórios</p>', unsafe_allow_html=True)
        esfera = st.selectbox("* Esfera", ["", "Federal", "Estadual", "Municipal"], key="esfera_cad")
        fonte_auto = get_fonte(esfera)
        num_conta = st.text_input("* Número da Conta (aceita letras e números)")
        if esfera:
            st.markdown(f'<p style="color:#22d3ee;font-weight:600;">Fonte: {fonte_auto}</p>', unsafe_allow_html=True)
        else:
            st.markdown(f'<p style="color:#94a3b8;">Selecione a Esfera para definir a Fonte automaticamente</p>', unsafe_allow_html=True)
        # Opcionais abaixo
        ref_contrato = st.selectbox("Referência do Contrato (opcional)", ["", "Resolução", "Deliberação", "Portaria"])
        num_ano_ref = st.text_input("Número/Ano (opcional)")
        tipo_recurso = st.selectbox("* Tipo de Recurso", ["", "Custeio", "Investimento", "Custeio/Investimento"], key="tipo_recurso_cad")
        if tipo_recurso == "Custeio/Investimento":
            val_custeio = st.number_input("* Valor Pago Custeio", min_value=0.0, step=0.01, format="%.2f")
            val_invest = st.number_input("* Valor Pago Investimento", min_value=0.0, step=0.01, format="%.2f")
            val_total = val_custeio + val_invest
        elif tipo_recurso == "Custeio":
            val_pago = st.number_input("* Valor Pago", min_value=0.0, step=0.01, format="%.2f")
            val_custeio = val_pago
            val_invest = 0.0
            val_total = val_pago
        elif tipo_recurso == "Investimento":
            val_pago = st.number_input("* Valor Pago", min_value=0.0, step=0.01, format="%.2f")
            val_custeio = 0.0
            val_invest = val_pago
            val_total = val_pago
        else:
            val_custeio = 0.0
            val_invest = 0.0
            val_total = 0.0
        data_receb = st.text_input("* Data de Recebimento", value=datetime.now().strftime("%d/%m/%Y"))
        # Opcionais
        programa_politica = st.text_input("Programa/Política (opcional)")
        setor_gasto = st.text_input("Setor de Referência de Gasto (opcional)")
        if st.button("Salvar Conta", key="salvar_conta"):
            if not esfera or not num_conta or not tipo_recurso or not data_receb or val_total <= 0:
                st.error("Preencha todos os campos obrigatórios: Esfera, Número da Conta, Tipo de Recurso, Valor Pago e Data de Recebimento")
            else:
                conn = sqlite3.connect("marmed.db")
                c = conn.cursor()
                c.execute("""
                    INSERT INTO contas_receber 
                    (esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso, 
                     valor_pago_custeio, valor_pago_investimento, valor_total, 
                     data_recebimento, programa_politica, setor_gasto)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (esfera, num_conta, fonte_auto, ref_contrato, num_ano_ref, tipo_recurso, 
                      val_custeio, val_invest, val_total,
                      data_receb, programa_politica, setor_gasto))
                conn.commit()
                conn.close()
                st.success("Conta cadastrada com sucesso!")
                st.rerun()

def contas_cadastradas():
    st.markdown('<h1 style="color:#e0f2fe;">CONTAS CADASTRADAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    df = conn.execute("SELECT id, esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso, valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento, programa_politica, setor_gasto FROM contas_receber ORDER BY id DESC").fetchall()
    cols = ["ID", "Esfera", "Nº Conta", "Fonte", "Referência", "Nº/Ano", "Tipo Recurso", "Valor Custeio", "Valor Investimento", "Valor Total", "Data Receb.", "Programa/Política", "Setor Gasto"]
    if df:
        import pandas as pd
        pdf = pd.DataFrame(df, columns=cols)
        for c in ["Valor Custeio", "Valor Investimento", "Valor Total"]:
            pdf[c] = pdf[c].apply(lambda x: format_currency(x))
        st.dataframe(pdf, use_container_width=True, hide_index=True)
        st.markdown(f'<p style="color:#64748b;font-size:12px;text-align:center;">Total de registros: {len(df)}</p>', unsafe_allow_html=True)
        st.markdown('<h3 style="color:#7dd3fc;">Editar / Excluir Conta</h3>', unsafe_allow_html=True)
        opcoes = {f"{r[1]} - {r[2]} (ID {r[0]})": r[0] for r in df}
        opcoes["Selecione..."] = None
        escolha = st.selectbox("Selecione uma conta", list(opcoes.keys()))
        if escolha and opcoes[escolha]:
            rid = opcoes[escolha]
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Editar", key=f"edit_conta_{rid}"):
                    st.session_state["edit_conta_id"] = rid
                    st.session_state["page"] = "EDITAR CONTA"
                    st.rerun()
            with c2:
                if st.button("Excluir", key=f"del_conta_{rid}"):
                    conn.execute("DELETE FROM contas_receber WHERE id=?", (rid,))
                    conn.commit()
                    st.success("Conta excluída com sucesso!")
                    st.rerun()
    else:
        st.info("Nenhuma conta cadastrada ainda.")
    
    # Bloco de Superávit
    st.markdown('<hr style="border-color:rgba(34,211,238,0.5);margin-top:30px;">', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#fbbf24;text-align:center;letter-spacing:2px;font-size:22px;">RECURSOS DE EXERCÍCIOS ANTERIORES / SUPERÁVIT FINANCEIRO</h2>', unsafe_allow_html=True)
    
    sup_df = conn.execute("SELECT id, esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, created_at FROM superavit ORDER BY id DESC").fetchall()
    sup_cols = ["ID", "Esfera", "Fonte Original", "Fonte Superávit", "Saldo Total", "Saldo Restante", "Criado em"]
    if sup_df:
        import pandas as pd
        spdf = pd.DataFrame(sup_df, columns=sup_cols)
        spdf["Saldo Total"] = spdf["Saldo Total"].apply(lambda x: format_currency(x))
        spdf["Saldo Restante"] = spdf["Saldo Restante"].apply(lambda x: format_currency(x))
        st.dataframe(spdf, use_container_width=True, hide_index=True)
    else:
        st.markdown('<p style="color:#94a3b8;text-align:center;">Nenhum superávit registrado ainda.</p>', unsafe_allow_html=True)
    
    if st.button("MIGRAR SALDOS PARA SUPERÁVIT", key="migrar_superavit"):
        for esfera in ["Federal", "Estadual"]:
            total = conn.execute("SELECT COALESCE(SUM(valor_total),0) FROM contas_receber WHERE esfera=?", (esfera,)).fetchone()[0]
            if total > 0:
                fonte_orig = get_fonte(esfera)
                fonte_sup = get_fonte_superavit(esfera)
                exist = conn.execute("SELECT id FROM superavit WHERE esfera=?", (esfera,)).fetchone()
                agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                if exist:
                    conn.execute("UPDATE superavit SET fonte_original=?, fonte_superavit=?, saldo_total=saldo_total+?, saldo_restante=saldo_restante+?, created_at=? WHERE esfera=?", (fonte_orig, fonte_sup, total, total, agora, esfera))
                else:
                    conn.execute("INSERT INTO superavit (esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, created_at) VALUES (?,?,?,?,?,?)", (esfera, fonte_orig, fonte_sup, total, total, agora))
        conn.commit()
        st.success("Saldos migrados para Superávit com sucesso! Fonte 1.500 (Municipal) não foi migrada.")
        st.rerun()
    
    conn.close()

def editar_conta():
    st.markdown('<h1 style="color:#e0f2fe;">EDITAR CONTA</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    rid = st.session_state.get("edit_conta_id")
    if not rid:
        st.error("Nenhuma conta selecionada para edição.")
        if st.button("Voltar"):
            st.session_state["page"] = "CONTAS CADASTRADAS"
            st.rerun()
        return
    conn = sqlite3.connect("marmed.db")
    row = conn.execute("SELECT * FROM contas_receber WHERE id=?", (rid,)).fetchone()
    conn.close()
    if not row:
        st.error("Conta não encontrada.")
        return
    esfera = st.selectbox("* Esfera", ["", "Federal", "Estadual", "Municipal"], index=["", "Federal", "Estadual", "Municipal"].index(row[1]) if row[1] in ["", "Federal", "Estadual", "Municipal"] else 0, key="esfera_edit")
    fonte_auto = get_fonte(esfera)
    num_conta = st.text_input("* Número da Conta (aceita letras e números)", value=row[2] or "")
    if esfera:
        st.markdown(f'<p style="color:#22d3ee;font-weight:600;">Fonte: {fonte_auto}</p>', unsafe_allow_html=True)
    ref_contrato = st.selectbox("Referência do Contrato (opcional)", ["", "Resolução", "Deliberação", "Portaria"], index=["", "Resolução", "Deliberação", "Portaria"].index(row[4]) if row[4] in ["", "Resolução", "Deliberação", "Portaria"] else 0)
    num_ano_ref = st.text_input("Número/Ano (opcional)", value=row[5] or "")
    tipo_recurso = st.selectbox("* Tipo de Recurso", ["", "Custeio", "Investimento", "Custeio/Investimento"], index=["", "Custeio", "Investimento", "Custeio/Investimento"].index(row[6]) if row[6] in ["", "Custeio", "Investimento", "Custeio/Investimento"] else 0, key="tipo_recurso_edit")
    if tipo_recurso == "Custeio/Investimento":
        val_custeio = st.number_input("* Valor Pago Custeio", min_value=0.0, step=0.01, format="%.2f", value=float(row[7] or 0))
        val_invest = st.number_input("* Valor Pago Investimento", min_value=0.0, step=0.01, format="%.2f", value=float(row[8] or 0))
        val_total = val_custeio + val_invest
    elif tipo_recurso == "Custeio":
        val_pago = st.number_input("* Valor Pago", min_value=0.0, step=0.01, format="%.2f", value=float(row[7] or 0))
        val_custeio = val_pago
        val_invest = 0.0
    elif tipo_recurso == "Investimento":
        val_pago = st.number_input("* Valor Pago", min_value=0.0, step=0.01, format="%.2f", value=float(row[8] or 0))
        val_custeio = 0.0
        val_invest = val_pago
    else:
        val_custeio = 0.0
        val_invest = 0.0
    val_total = val_custeio + val_invest
    data_receb = st.text_input("* Data de Recebimento", value=row[10] or datetime.now().strftime("%d/%m/%Y"))
    programa_politica = st.text_input("Programa/Política (opcional)", value=row[11] or "")
    setor_gasto = st.text_input("Setor de Referência de Gasto (opcional)", value=row[12] or "")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Salvar Alterações"):
            if not esfera or not num_conta or not tipo_recurso or not data_receb:
                st.error("Preencha os campos obrigatórios: Esfera, Número da Conta, Tipo de Recurso e Data de Recebimento")
            else:
                conn = sqlite3.connect("marmed.db")
                conn.execute("""
                    UPDATE contas_receber SET esfera=?, numero_conta=?, fonte=?, referencia_tipo=?, referencia_numero=?, tipo_recurso=?,
                    valor_pago_custeio=?, valor_pago_investimento=?, valor_total=?, data_recebimento=?, programa_politica=?, setor_gasto=?
                    WHERE id=?
                """, (esfera, num_conta, fonte_auto, ref_contrato, num_ano_ref, tipo_recurso, val_custeio, val_invest, val_total, data_receb, programa_politica, setor_gasto, rid))
                conn.commit()
                conn.close()
                st.success("Conta atualizada com sucesso!")
                st.session_state["page"] = "CONTAS CADASTRADAS"
                st.rerun()
    with c2:
        if st.button("Voltar"):
            st.session_state["page"] = "CONTAS CADASTRADAS"
            st.rerun()

def realizar_compras():
    st.markdown('<h1 style="color:#e0f2fe;">REALIZAR COMPRAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    df = conn.execute("SELECT id, item, quantidade, valor_unitario, valor_total, data, setor, esfera, fonte FROM compras ORDER BY id DESC").fetchall()
    cols = ["ID", "Item", "Qtd", "Valor Unit.", "Valor Total", "Data", "Setor", "Esfera", "Fonte"]
    if df:
        import pandas as pd
        pdf = pd.DataFrame(df, columns=cols)
        pdf["Valor Unit."] = pdf["Valor Unit."].apply(lambda x: format_currency(x))
        pdf["Valor Total"] = pdf["Valor Total"].apply(lambda x: format_currency(x))
        st.dataframe(pdf, use_container_width=True, hide_index=True)
        st.markdown('<h3 style="color:#7dd3fc;">Editar / Excluir Compra</h3>', unsafe_allow_html=True)
        opcoes = {f"{r[1]} - {r[5]} (ID {r[0]})": r[0] for r in df}
        opcoes["Selecione..."] = None
        escolha = st.selectbox("Selecione uma compra", list(opcoes.keys()))
        if escolha and opcoes[escolha]:
            rid = opcoes[escolha]
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Editar", key=f"edit_compra_{rid}"):
                    st.session_state["edit_compra_id"] = rid
                    st.session_state["page"] = "EDITAR COMPRA"
                    st.rerun()
            with c2:
                if st.button("Excluir", key=f"del_compra_{rid}"):
                    conn.execute("DELETE FROM compras WHERE id=?", (rid,))
                    conn.commit()
                    st.success("Compra excluída com sucesso!")
                    st.rerun()
    with st.expander("NOVA COMPRA", expanded=False):
        esfera = st.selectbox("Esfera", ["", "Federal", "Estadual", "Municipal"], key="esfera_compra")
        if esfera:
            st.markdown(f'<p style="color:#22d3ee;font-weight:600;">Fonte: {get_fonte(esfera)}</p>', unsafe_allow_html=True)
        item = st.text_input("Item/Produto")
        qtd = st.number_input("Quantidade", min_value=0.01, step=0.01, format="%.2f")
        val_unit = st.number_input("Valor Unitário", min_value=0.0, step=0.01, format="%.2f")
        val_total_compra = qtd * val_unit
        st.markdown(f'<p style="color:#00d4ff;font-size:18px;font-weight:700;">Valor Total: {format_currency(val_total_compra)}</p>', unsafe_allow_html=True)
        data_compra = st.text_input("Data da Compra", value=datetime.now().strftime("%d/%m/%Y"))
        setor_compra = st.text_input("Setor")
        if st.button("Registrar Compra", key="salvar_compra"):
            if not item or not esfera:
                st.error("Preencha os campos obrigatórios: Esfera e Item")
            else:
                if esfera != "Municipal":
                    saldo_sup = conn.execute("SELECT COALESCE(SUM(saldo_restante),0) FROM superavit WHERE esfera=? AND saldo_restante>0", (esfera,)).fetchone()[0]
                    if saldo_sup > 0:
                        st.error(f"Você ainda tem valor restante de superávit! Saldo disponível: {format_currency(saldo_sup)}. Primeiro utilize o saldo do superávit antes de usar recursos do exercício atual.")
                    else:
                        conn.execute("INSERT INTO compras (item, quantidade, valor_unitario, valor_total, data, setor, esfera, fonte) VALUES (?,?,?,?,?,?,?,?)", (item, qtd, val_unit, val_total_compra, data_compra, setor_compra, esfera, get_fonte(esfera)))
                        conn.commit()
                        st.success("Compra registrada com sucesso!")
                        st.rerun()
                else:
                    conn.execute("INSERT INTO compras (item, quantidade, valor_unitario, valor_total, data, setor, esfera, fonte) VALUES (?,?,?,?,?,?,?,?)", (item, qtd, val_unit, val_total_compra, data_compra, setor_compra, esfera, get_fonte(esfera)))
                    conn.commit()
                    st.success("Compra registrada com sucesso!")
                    st.rerun()
    conn.close()

def editar_compra():
    st.markdown('<h1 style="color:#e0f2fe;">EDITAR COMPRA</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    rid = st.session_state.get("edit_compra_id")
    if not rid:
        st.error("Nenhuma compra selecionada para edição.")
        if st.button("Voltar"):
            st.session_state["page"] = "REALIZAR COMPRAS"
            st.rerun()
        return
    conn = sqlite3.connect("marmed.db")
    row = conn.execute("SELECT * FROM compras WHERE id=?", (rid,)).fetchone()
    conn.close()
    if not row:
        st.error("Compra não encontrada.")
        return
    esfera = st.selectbox("Esfera", ["", "Federal", "Estadual", "Municipal"], index=["", "Federal", "Estadual", "Municipal"].index(row[7]) if row[7] in ["", "Federal", "Estadual", "Municipal"] else 0, key="esfera_edit_compra")
    if esfera:
        st.markdown(f'<p style="color:#22d3ee;font-weight:600;">Fonte: {get_fonte(esfera)}</p>', unsafe_allow_html=True)
    item = st.text_input("Item/Produto", value=row[1] or "")
    qtd = st.number_input("Quantidade", min_value=0.01, step=0.01, format="%.2f", value=float(row[2] or 1))
    val_unit = st.number_input("Valor Unitário", min_value=0.0, step=0.01, format="%.2f", value=float(row[3] or 0))
    val_total_compra = qtd * val_unit
    st.markdown(f'<p style="color:#00d4ff;font-size:18px;font-weight:700;">Valor Total: {format_currency(val_total_compra)}</p>', unsafe_allow_html=True)
    data_compra = st.text_input("Data da Compra", value=row[5] or datetime.now().strftime("%d/%m/%Y"))
    setor_compra = st.text_input("Setor", value=row[6] or "")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Salvar Alterações"):
            conn = sqlite3.connect("marmed.db")
            conn.execute("UPDATE compras SET item=?, quantidade=?, valor_unitario=?, valor_total=?, data=?, setor=?, esfera=?, fonte=? WHERE id=?", (item, qtd, val_unit, val_total_compra, data_compra, setor_compra, esfera, get_fonte(esfera), rid))
            conn.commit()
            conn.close()
            st.success("Compra atualizada com sucesso!")
            st.session_state["page"] = "REALIZAR COMPRAS"
            st.rerun()
    with c2:
        if st.button("Voltar"):
            st.session_state["page"] = "REALIZAR COMPRAS"
            st.rerun()

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

def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "page" not in st.session_state:
        st.session_state["page"] = "Dashboard"
    if not st.session_state["logged_in"]:
        login_page()
    else:
        st.sidebar.markdown('<h3 style="color:#22d3ee;text-align:center;letter-spacing:2px;">ABA DE NAVEGAÇÃO</h3>', unsafe_allow_html=True)
        st.sidebar.markdown('<hr>', unsafe_allow_html=True)
        if st.sidebar.button("INÍCIO", key="nav_inicio", use_container_width=True):
            st.session_state["page"] = "Dashboard"
            st.rerun()
        if st.sidebar.button("CADASTRAR CONTAS", key="nav_cadastrar", use_container_width=True):
            st.session_state["page"] = "CADASTRAR CONTAS"
            st.rerun()
        if st.sidebar.button("CONTAS CADASTRADAS", key="nav_cadastradas", use_container_width=True):
            st.session_state["page"] = "CONTAS CADASTRADAS"
            st.rerun()
        if st.sidebar.button("REALIZAR COMPRAS", key="nav_compras", use_container_width=True):
            st.session_state["page"] = "REALIZAR COMPRAS"
            st.rerun()
        st.sidebar.markdown('<hr>', unsafe_allow_html=True)
        if st.sidebar.button("Sair", key="logout", use_container_width=True):
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
        elif page == "EDITAR COMPRA":
            editar_compra()
        elif page == "Trocar Senha":
            change_password()

if __name__ == "__main__":
    main()
