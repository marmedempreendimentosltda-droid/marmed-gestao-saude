import streamlit as st
import sqlite3
import hashlib
import re
from datetime import datetime, date

st.set_page_config(page_title="MARMED", layout="wide")

def format_currency(value):
    if value is None: value = 0.0
    v = float(value)
    inteiro, centavos = f"{v:.2f}".split(".")
    if len(inteiro) > 3:
        partes = []
        while len(inteiro) > 3:
            partes.insert(0, inteiro[-3:])
            inteiro = inteiro[:-3]
        if inteiro:
            partes.insert(0, inteiro)
        inteiro = ".".join(partes)
    return f"R$ {inteiro},{centavos}"

def get_fonte(esfera):
    if esfera == "Federal": return "1.600"
    elif esfera == "Estadual": return "1.621"
    elif esfera == "Municipal": return "1.500"
    return ""

def get_fonte_superavit(esfera):
    if esfera == "Federal": return "2.600"
    elif esfera == "Estadual": return "2.621"
    return None

def extract_text_from_bytes(file_bytes, filename):
    text = ""
    try:
        if filename.lower().endswith(('.txt', '.csv')):
            text = file_bytes.decode('utf-8', errors='replace')
        else:
            text = f"[Arquivo: {filename}]"
    except:
        text = f"[Nao foi possivel extrair texto]"
    return text

def parse_br_currency(val):
    if val is None: return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    if not val or str(val).strip() == '':
        return 0.0
    v = str(val).replace('R$ ', '').replace('R$', '').replace('.', '').replace(',', '.')
    try:
        return float(v)
    except:
        return 0.0

def is_zero_or_negative(val):
    """Retorna True se o valor for menor ou igual a zero"""
    return val <= 0.0

def is_greater_than(val, limit):
    """Retorna True se o valor for maior que o limite"""
    return val > limit

def inject_masks():
    st.markdown("""
    <script>
    (function() {
        function aplicarMascaras() {
            document.querySelectorAll('[data-testid="stTextInput"]').forEach(function(el) {
                var label = el.querySelector('label');
                var input = el.querySelector('input');
                if (label && input && !input.dataset.maskMoney && /custeio|investimento|valor|compra/i.test(label.textContent)) {
                    input.dataset.maskMoney = '1';
                    input.inputMode = 'numeric';
                    input.setAttribute('autocomplete', 'off');
                    input.addEventListener('input', function() {
                        var v = this.value.replace(/\D/g, '');
                        if (v.length === 0) { this.value = ''; return; }
                        while (v.length < 3) v = '0' + v;
                        var cents = v.substring(v.length - 2);
                        var reais = v.substring(0, v.length - 2);
                        reais = reais.replace(/^0+/, '');
                        if (reais === '') reais = '0';
                        var partes = [];
                        while (reais.length > 3) {
                            partes.unshift(reais.substring(reais.length - 3));
                            reais = reais.substring(0, reais.length - 3);
                        }
                        if (reais.length > 0) partes.unshift(reais);
                        this.value = partes.join('.') + ',' + cents;
                    });
                    if (input.value) { input.dispatchEvent(new Event('input')); }
                }
            });
            document.querySelectorAll('input:not([type="hidden"])').forEach(function(input) {
                if (input.dataset.maskMoney) return;
                var parentText = (input.parentElement ? input.parentElement.textContent : '') + ' ' + (input.placeholder || '');
                if (!input.dataset.maskMoney && /custeio|investimento|valor|compra/i.test(parentText)) {
                    input.dataset.maskMoney = '1';
                    input.inputMode = 'numeric';
                    input.addEventListener('input', function() {
                        var v = this.value.replace(/\D/g, '');
                        if (v.length === 0) { this.value = ''; return; }
                        while (v.length < 3) v = '0' + v;
                        var cents = v.substring(v.length - 2);
                        var reais = v.substring(0, v.length - 2);
                        reais = reais.replace(/^0+/, '');
                        if (reais === '') reais = '0';
                        var partes = [];
                        while (reais.length > 3) {
                            partes.unshift(reais.substring(reais.length - 3));
                            reais = reais.substring(0, reais.length - 3);
                        }
                        if (reais.length > 0) partes.unshift(reais);
                        this.value = partes.join('.') + ',' + cents;
                    });
                    if (input.value) { input.dispatchEvent(new Event('input')); }
                }
            });
        }
        aplicarMascaras();
        var obs = new MutationObserver(aplicarMascaras);
        obs.observe(document.body, { childList: true, subtree: true });
        setTimeout(aplicarMascaras, 500);
        setTimeout(aplicarMascaras, 1500);
        setTimeout(aplicarMascaras, 3000);
    })();
    </script>
    """, unsafe_allow_html=True)

def init_db():
    conn = sqlite3.connect("marmed.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT)")
    c.execute("""CREATE TABLE IF NOT EXISTS contas_receber (
        id INTEGER PRIMARY KEY AUTOINCREMENT, esfera TEXT, numero_conta TEXT, fonte TEXT,
        referencia_tipo TEXT, referencia_numero TEXT, tipo_recurso TEXT,
        valor_pago_custeio REAL DEFAULT 0, valor_pago_investimento REAL DEFAULT 0,
        valor_total REAL DEFAULT 0, data_recebimento TEXT, programa_politica TEXT, setor_gasto TEXT,
        referencia_uso TEXT DEFAULT ''
    )""")
    try:
        c.execute("ALTER TABLE contas_receber ADD COLUMN referencia_uso TEXT DEFAULT ''")
    except:
        pass
    c.execute("""CREATE TABLE IF NOT EXISTS superavit (
        id INTEGER PRIMARY KEY AUTOINCREMENT, esfera TEXT, fonte_original TEXT, fonte_superavit TEXT,
        saldo_total REAL DEFAULT 0, saldo_restante REAL DEFAULT 0, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS ordens_compra (
        id INTEGER PRIMARY KEY AUTOINCREMENT, conta_receber_id INTEGER, esfera TEXT, numero_conta TEXT, fonte TEXT,
        ficha TEXT, tipo_despesa TEXT, data_compra TEXT, valor_compra REAL DEFAULT 0, produto_servico TEXT, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS arquivos_saude (
        id INTEGER PRIMARY KEY AUTOINCREMENT, bloco TEXT, nome_arquivo TEXT, conteudo_texto TEXT,
        dados_arquivo BLOB, data_upload TEXT
    )""")
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
        .stApp { background: linear-gradient(135deg, #0f172a, #1e3a8a, #0f172a); }
        div[data-testid="column"]:nth-child(2) {
            background: rgba(15, 23, 42, 0.85) !important;
            backdrop-filter: blur(16px) !important;
            border: 2px solid rgba(14, 165, 233, 0.5) !important;
            border-radius: 24px !important;
            padding: 48px 40px !important;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5) !important;
            margin-top: 80px !important; max-width: 420px !important;
            margin-left: auto !important; margin-right: auto !important;
        }
        .marmed-title { font-size: 52px; font-weight: 800; text-align: center; color: #e0f2fe; letter-spacing: 6px; margin-bottom: 8px; }
        .subtitle { text-align: center; color: #22d3ee; font-size: 14px; letter-spacing: 4px; margin-bottom: 36px; text-transform: uppercase; font-weight: 700; }
        .stTextInput label { color: #22d3ee !important; font-weight: 700 !important; font-size: 14px !important; }
        .stTextInput > div > div > input { background: rgba(30, 41, 59, 0.9) !important; border: 1px solid rgba(34, 211, 238, 0.4) !important; color: #f8fafc !important; border-radius: 10px !important; font-size: 16px !important; }
        .stButton > button { background: linear-gradient(90deg, #06b6d4, #3b82f6) !important; color: #fff !important; font-weight: 800 !important; border-radius: 10px !important; border: none !important; width: 100%; padding: 14px !important; font-size: 16px !important; }
        .stSelectbox > div > div { background: rgba(30, 41, 59, 0.9) !important; border: 1px solid rgba(34, 211, 238, 0.4) !important; border-radius: 10px !important; color: #f8fafc !important; }
        .stDateInput > div > div > input { background: rgba(30, 41, 59, 0.9) !important; border: 1px solid rgba(34, 211, 238, 0.4) !important; color: #f8fafc !important; border-radius: 10px !important; }
        .stDateInput label { color: #22d3ee !important; font-weight: 700 !important; }
        .stNumberInput > div > div > input { background: rgba(30, 41, 59, 0.9) !important; border: 1px solid rgba(34, 211, 238, 0.4) !important; color: #f8fafc !important; border-radius: 10px !important; }
        .stDataFrame { background: rgba(15, 23, 42, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.4) !important; border-radius: 10px !important; }
        .stDataFrame td { color: #f8fafc !important; font-weight: 500 !important; }
        .stDataFrame th { color: #22d3ee !important; font-weight: 700 !important; }
        .stFileUploader > div { background: rgba(30, 41, 59, 0.9) !important; border: 1px dashed rgba(34, 211, 238, 0.5) !important; border-radius: 10px !important; color: #f8fafc !important; }
        .stTextArea > div > textarea { background: rgba(30, 41, 59, 0.9) !important; border: 1px solid rgba(34, 211, 238, 0.4) !important; color: #f8fafc !important; border-radius: 10px !important; }
        .stExpander { background: rgba(15, 23, 42, 0.7) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; border-radius: 12px !important; margin-bottom: 8px !important; }
        .stTabs [data-baseweb="tab"] { color: #f8fafc !important; font-weight: 700 !important; }
        </style>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="marmed-title">MARMED</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">SISTEMA INTEGRADO DE GESTAO</div>', unsafe_allow_html=True)
        username = st.text_input("USUARIO", key="login_user")
        password = st.text_input("SENHA", type="password", key="login_pass")
        if st.button("Acessar"):
            pw_hash = hashlib.sha256(password.encode()).hexdigest()
            conn = sqlite3.connect("marmed.db")
            user = conn.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (username, pw_hash)).fetchone()
            conn.close()
            if user:
                st.session_state["logged_in"] = True
                st.session_state["page"] = "Dashboard"
                st.rerun()
            else:
                st.error("Usuario ou senha invalidos")

def dashboard():
    st.markdown('<h1 style="color:#f8fafc;text-align:center;font-size:48px;font-weight:800;letter-spacing:6px;">MARMED</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#22d3ee;text-align:center;letter-spacing:4px;margin-bottom:4px;font-weight:700;">SISTEMA INTEGRADO DE GESTAO</h3>', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#3b82f6;text-align:center;letter-spacing:3px;font-size:20px;font-weight:700;margin-bottom:16px;">PREFEITURA MUNICIPAL DE LUMINARIAS</h2>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.4);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    cols = st.columns(5)
    for i, (tit, esf, cor) in enumerate(zip(
        ["REPASSE FEDERAL", "REPASSE ESTADUAL", "RECURSO MUNICIPAL", "TRANSFERENCIA", "TRANSPOSICAO"],
        ["Federal", "Estadual", "Municipal", "Transferencia", "Transposicao"],
        ["#3b82f6", "#22c55e", "#eab308", "#a855f7", "#ef4444"]
    )):
        tc = conn.execute("SELECT COALESCE(SUM(valor_total),0) FROM contas_receber WHERE esfera=?", (esf,)).fetchone()[0]
        tg = conn.execute("SELECT COALESCE(SUM(valor_compra),0) FROM ordens_compra WHERE esfera=?", (esf,)).fetchone()[0]
        saldo = tc - tg
        with cols[i]:
            st.markdown(f'<div style="background:linear-gradient(135deg,#1a2a3a,#0f2027);border-radius:15px;padding:15px;text-align:center;border-left:5px solid {cor};border:1px solid rgba(34,211,238,0.4);margin-bottom:8px;"><div style="color:#38bdf8;font-size:12px;font-weight:700;">{tit}</div><div style="color:#f8fafc;font-size:20px;font-weight:800;">{format_currency(tc)}</div><div style="color:#cbd5e1;font-size:11px;">Saldo: <span style="color:{cor};font-weight:700;">{format_currency(saldo)}</span></div></div>', unsafe_allow_html=True)
            if st.button(f"Ver {esf}", key=f"b_{esf}"):
                st.session_state["esfera_view"] = esf
                st.session_state["page"] = "ESFERA DETALHE"; st.rerun()
    tc = conn.execute("SELECT COUNT(*) FROM contas_receber").fetchone()[0]
    tco = conn.execute("SELECT COUNT(*) FROM ordens_compra").fetchone()[0]
    conn.close()
    st.markdown(f'<p style="text-align:center;color:#cbd5e1;font-size:13px;margin-top:10px;">{tc} conta(s) | {tco} ordem(ns) de compra - {datetime.now().strftime("%d/%m/%Y")}</p>', unsafe_allow_html=True)

def esfera_detalhe():
    esf = st.session_state.get("esfera_view", "Federal")
    st.markdown(f'<h1 style="color:#f8fafc;">{esf.upper()}</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    for cid, num, fonte, vtotal in conn.execute("SELECT id, numero_conta, fonte, valor_total FROM contas_receber WHERE esfera=? ORDER BY id DESC", (esf,)).fetchall():
        gasto = conn.execute("SELECT COALESCE(SUM(valor_compra),0) FROM ordens_compra WHERE conta_receber_id=?", (cid,)).fetchone()[0]
        saldo = vtotal - gasto
        with st.expander(f"{num} - Fonte {fonte}"):
            st.markdown(f'<p style="color:#cbd5e1;">N: <strong style="color:#f8fafc;">{num}</strong> | Fonte: <strong style="color:#22d3ee;">{fonte}</strong> | Original: <strong style="color:#38bdf8;">{format_currency(vtotal)}</strong> | Saldo: <strong style="color:{"#22c55e" if saldo>0 else "#ef4444"}">{format_currency(saldo)}</strong></p>', unsafe_allow_html=True)
            for o in conn.execute("SELECT ficha, tipo_despesa, data_compra, valor_compra, produto_servico FROM ordens_compra WHERE conta_receber_id=? ORDER BY id DESC", (cid,)).fetchall():
                st.markdown(f'<div style="background:rgba(30,41,59,0.8);border-radius:10px;padding:12px;margin-bottom:8px;border-left:3px solid #22d3ee;"><div style="color:#cbd5e1;font-size:12px;">Ficha: <strong style="color:#f8fafc;">{o[0] or "--"}</strong> | <strong style="color:#22d3ee;">{o[1] or "--"}</strong> | {o[2] or "--"}</div><div style="color:#38bdf8;font-size:16px;font-weight:700;">{format_currency(o[3])}</div><div style="color:#cbd5e1;font-size:13px;">{o[4][:80]}{"..." if o[4] and len(o[4])>80 else ""}</div></div>', unsafe_allow_html=True)
    conn.close()
    if st.button("Voltar ao Inicio"):
        st.session_state["page"] = "Dashboard"; st.rerun()

def cadastrar_contas():
    st.markdown('<h1 style="color:#f8fafc;">CADASTRAR CONTAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    inject_masks()
    with st.expander("NOVO CADASTRO", expanded=True):
        st.markdown('<p style="color:#fbbf24;font-size:13px;font-weight:700;">* Campos obrigatorios</p>', unsafe_allow_html=True)
        esfera = st.selectbox("* 1. Selecione a Esfera", ["", "Federal", "Estadual", "Municipal"], key="esfera_cad")
        if esfera:
            fonte_mostrada = get_fonte(esfera)
            cor_fonte = {"Federal": "#3b82f6", "Estadual": "#22c55e", "Municipal": "#eab308"}
            st.markdown(f'''
            <div style="background:rgba(30,41,59,0.9);border-radius:10px;padding:15px;margin-bottom:15px;border-left:5px solid {cor_fonte.get(esfera, "#22d3ee")};">
                <div style="display:flex;align-items:center;justify-content:space-between;">
                    <div><span style="color:#cbd5e1;font-size:14px;">Fonte vinculada:</span><span style="color:#22d3ee;font-size:30px;font-weight:800;margin-left:10px;">{fonte_mostrada}</span></div>
                    <div><span style="background:{"#3b82f6" if esfera=="Federal" else "#22c55e" if esfera=="Estadual" else "#eab308"};color:#fff;padding:6px 14px;border-radius:6px;font-size:14px;font-weight:700;">{esfera.upper()}</span></div>
                </div>
            </div>''', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#cbd5e1;font-size:14px;">Selecione a Esfera para ver a Fonte</p>', unsafe_allow_html=True)
        num_conta = st.text_input("* 2. Numero da Conta", key="num_conta_cad")
        ref_contrato = st.selectbox("Referencia (opcional)", ["", "Resolucao", "Deliberacao", "Portaria"])
        num_ano_ref = st.text_input("Numero/Ano (opcional)")
        st.markdown('<p style="color:#22d3ee;font-size:15px;font-weight:700;margin-top:12px;">3. Selecione o Tipo de Recurso</p>', unsafe_allow_html=True)
        tipo_recurso = st.selectbox("* Tipo de Recurso", ["", "Custeio", "Investimento", "Custeio/Investimento"], key="tipo_recurso_cad")
        val_custeio_str = ""
        val_invest_str = ""
        vt = 0.0
        if tipo_recurso:
            st.markdown('<p style="color:#22d3ee;font-size:15px;font-weight:700;margin-top:12px;">4. Informe o(s) Valor(es) - Digite apenas numeros</p>', unsafe_allow_html=True)
            st.markdown('<p style="color:#cbd5e1;font-size:12px;margin-bottom:5px;">O sistema coloca ponto e virgula automaticamente</p>', unsafe_allow_html=True)
            if tipo_recurso in ["Custeio", "Custeio/Investimento"]:
                c1, c2 = st.columns([1, 3])
                with c1:
                    st.markdown('<p style="color:#06b6d4;font-weight:800;margin-top:8px;font-size:16px;">R$ CUSTEIO</p>', unsafe_allow_html=True)
                with c2:
                    val_custeio_str = st.text_input("", key="val_custeio_cad", label_visibility="collapsed")
            if tipo_recurso in ["Investimento", "Custeio/Investimento"]:
                c1, c2 = st.columns([1, 3])
                with c1:
                    st.markdown('<p style="color:#06b6d4;font-weight:800;margin-top:8px;font-size:16px;">R$ INVESTIMENTO</p>', unsafe_allow_html=True)
                with c2:
                    val_invest_str = st.text_input("", key="val_invest_cad", label_visibility="collapsed")
            vc = parse_br_currency(val_custeio_str)
            vi = parse_br_currency(val_invest_str)
            vt = vc + vi
            if vt > 0:
                st.markdown(f'<p style="color:#38bdf8;font-size:20px;font-weight:800;margin-top:10px;">Total: {format_currency(vt)}</p>', unsafe_allow_html=True)
        st.markdown('<p style="color:#22d3ee;font-size:15px;font-weight:700;margin-top:12px;">5. Data de Recebimento</p>', unsafe_allow_html=True)
        st.markdown('<p style="color:#cbd5e1;font-size:12px;margin-bottom:5px;">Clique no campo para abrir o calendario</p>', unsafe_allow_html=True)
        data_receb = st.date_input("* Data Recebimento", value=datetime.now(), format="DD/MM/YYYY", key="data_receb_cad")
        st.markdown('<p style="color:#22d3ee;font-size:15px;font-weight:700;margin-top:12px;">6. Informacoes Adicionais</p>', unsafe_allow_html=True)
        prog = st.text_input("Programa/Politica (opcional)")
        setor = st.text_input("Setor (opcional)")
        ref_uso = st.text_input("Referencia para Uso - Material/Servico")
        if st.button("Salvar Conta"):
            erros = []
            if not esfera: erros.append("Esfera")
            if not num_conta: erros.append("Numero da Conta")
            if not tipo_recurso: erros.append("Tipo de Recurso")
            if is_zero_or_negative(vt): erros.append("Valor (preencha Custeio ou Investimento)")
            if erros:
                st.error(f"Preencha: {', '.join(erros)}")
            else:
                conn = sqlite3.connect("marmed.db")
                conn.execute("INSERT INTO contas_receber (esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso, valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento, programa_politica, setor_gasto, referencia_uso) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (esfera, num_conta, get_fonte(esfera), ref_contrato, num_ano_ref, tipo_recurso, parse_br_currency(val_custeio_str), parse_br_currency(val_invest_str), vt, data_receb.strftime("%d/%m/%Y"), prog, setor, ref_uso))
                conn.commit(); conn.close()
                st.session_state["page"] = "CONTAS CADASTRADAS"; st.rerun()

def contas_cadastradas():
    st.markdown('<h1 style="color:#f8fafc;">CONTAS CADASTRADAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    tabs = st.tabs(["FEDERAL", "ESTADUAL", "MUNICIPAL"])
    for tab_idx, esf in enumerate(["Federal", "Estadual", "Municipal"]):
        with tabs[tab_idx]:
            r = conn.execute("SELECT id, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso, valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento, programa_politica, setor_gasto, COALESCE(referencia_uso, '') FROM contas_receber WHERE esfera=? ORDER BY id DESC", (esf,)).fetchall()
            if r:
                import pandas as pd
                d = [(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11], x[12]) for x in r]
                pdf = pd.DataFrame(d, columns=["ID", "Conta", "Fonte", "Ref.", "N/Ano", "Tipo", "Custeio", "Invest.", "Total", "Data", "Programa", "Setor", "Ref.Uso"])
                for c in ["Custeio", "Invest.", "Total"]: pdf[c] = pdf[c].apply(lambda x: format_currency(x))
                st.dataframe(pdf, use_container_width=True, hide_index=True)
                st.markdown(f'<p style="color:#cbd5e1;">Total: <strong style="color:#f8fafc;">{len(r)}</strong> conta(s) {esf}</p>', unsafe_allow_html=True)
                st.markdown(f'<h4 style="color:#22d3ee;">Editar / Excluir - {esf}</h4>', unsafe_allow_html=True)
                opts = {f"{x[1]} - Fonte {x[2]} (ID {x[0]})": x[0] for x in r}
                opts["Selecione..."] = None
                esc = st.selectbox(f"Selecione a conta", list(opts.keys()), key=f"sel_{tab_idx}")
                if esc and opts[esc]:
                    rid = opts[esc]
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Editar", key=f"e_{tab_idx}_{rid}"): st.session_state["edit_conta_id"] = rid; st.session_state["page"] = "EDITAR CONTA"; st.rerun()
                    with c2:
                        if st.button("Excluir", key=f"d_{tab_idx}_{rid}"): conn.execute("DELETE FROM contas_receber WHERE id=?", (rid,)); conn.commit(); st.success("Excluida!"); st.rerun()
            else: st.markdown(f'<p style="color:#cbd5e1;">Nenhuma conta {esf}.</p>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#fbbf24;text-align:center;font-size:22px;font-weight:800;">RECURSOS DE EXERCICIOS ANTERIORES / SUPERAVIT FINANCEIRO</h2>', unsafe_allow_html=True)
    sup = conn.execute("SELECT id, esfera, fonte_original, fonte_superavit, saldo_total, saldo_restante, created_at FROM superavit ORDER BY id DESC").fetchall()
    if sup:
        import pandas as pd
        spd = pd.DataFrame(sup, columns=["ID", "Esfera", "F. Original", "F. Superavit", "Saldo Total", "Saldo Restante", "Criado em"])
        spd["Saldo Total"] = spd["Saldo Total"].apply(lambda x: format_currency(x))
        spd["Saldo Restante"] = spd["Saldo Restante"].apply(lambda x: format_currency(x))
        st.dataframe(spd, use_container_width=True, hide_index=True)
    else: st.markdown('<p style="color:#cbd5e1;">Nenhum superavit registrado.</p>', unsafe_allow_html=True)
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

def editar_conta():
    st.markdown('<h1 style="color:#f8fafc;">EDITAR CONTA</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    inject_masks()
    rid = st.session_state.get("edit_conta_id")
    if not rid: st.error("Nenhuma conta."); return
    conn = sqlite3.connect("marmed.db")
    row = conn.execute("SELECT * FROM contas_receber WHERE id=?", (rid,)).fetchone()
    if not row: conn.close(); st.error("Nao encontrada."); return
    esfera = st.selectbox("* Esfera", ["", "Federal", "Estadual", "Municipal"], index=["", "Federal", "Estadual", "Municipal"].index(row[1]) if row[1] in ["", "Federal", "Estadual", "Municipal"] else 0, key="esf_edit")
    if esfera: st.markdown(f'<p style="color:#22d3ee;font-weight:800;font-size:18px;">Fonte: {get_fonte(esfera)}</p>', unsafe_allow_html=True)
    num_conta = st.text_input("* NConta", value=row[2] or "")
    ref_contrato = st.selectbox("Ref", ["", "Resolucao", "Deliberacao", "Portaria"], index=["", "Resolucao", "Deliberacao", "Portaria"].index(row[4]) if row[4] in ["", "Resolucao", "Deliberacao", "Portaria"] else 0)
    num_ano_ref = st.text_input("N/Ano", value=row[5] or "")
    tipo_recurso = st.selectbox("* Tipo", ["", "Custeio", "Investimento", "Custeio/Investimento"], index=["", "Custeio", "Investimento", "Custeio/Investimento"].index(row[6]) if row[6] in ["", "Custeio", "Investimento", "Custeio/Investimento"] else 0, key="tipo_edit")
    vc_str = st.text_input("Custeio", value=format_currency(row[7] or 0).replace("R$ ", ""), key="val_custeio_edit")
    vi_str = st.text_input("Investimento", value=format_currency(row[8] or 0).replace("R$ ", ""), key="val_invest_edit")
    vc = parse_br_currency(vc_str); vi = parse_br_currency(vi_str)
    try:
        data_receb = st.date_input("Data", value=datetime.strptime(row[10], "%d/%m/%Y") if row[10] else datetime.now(), format="DD/MM/YYYY", key="data_edit")
    except:
        data_receb = st.date_input("Data", value=datetime.now(), format="DD/MM/YYYY", key="data_edit")
    prog = st.text_input("Programa", value=row[11] or "")
    setor = st.text_input("Setor", value=row[12] or "")
    ref_uso = st.text_input("Ref.Uso - Material/Servico", value=row[13] if len(row) > 13 and row[13] else "")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Salvar"):
            try:
                conn.execute("UPDATE contas_receber SET esfera=?, numero_conta=?, fonte=?, referencia_tipo=?, referencia_numero=?, tipo_recurso=?, valor_pago_custeio=?, valor_pago_investimento=?, valor_total=?, data_recebimento=?, programa_politica=?, setor_gasto=?, referencia_uso=? WHERE id=?", (esfera, num_conta, get_fonte(esfera), ref_contrato, num_ano_ref, tipo_recurso, vc, vi, vc+vi, data_receb.strftime("%d/%m/%Y"), prog, setor, ref_uso, rid))
            except:
                conn.execute("UPDATE contas_receber SET esfera=?, numero_conta=?, fonte=?, referencia_tipo=?, referencia_numero=?, tipo_recurso=?, valor_pago_custeio=?, valor_pago_investimento=?, valor_total=?, data_recebimento=?, programa_politica=?, setor_gasto=? WHERE id=?", (esfera, num_conta, get_fonte(esfera), ref_contrato, num_ano_ref, tipo_recurso, vc, vi, vc+vi, data_receb.strftime("%d/%m/%Y"), prog, setor, rid))
            conn.commit(); conn.close(); st.success("Atualizada!"); st.session_state["page"] = "CONTAS CADASTRADAS"; st.rerun()
    with c2:
        if st.button("Voltar"): st.session_state["page"] = "CONTAS CADASTRADAS"; st.rerun()
    conn.close()

def realizar_compras():
    st.markdown('<h1 style="color:#f8fafc;">REALIZAR COMPRAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    inject_masks()
    conn = sqlite3.connect("marmed.db")
    
    st.markdown('<h3 style="color:#22d3ee;font-weight:800;">Nova Solicitacao</h3>', unsafe_allow_html=True)
    tabs = st.tabs(["FEDERAL", "ESTADUAL", 
