import streamlit as st
import sqlite3
import hashlib
import re
from datetime import datetime

st.set_page_config(page_title="MARMED", layout="wide")

def format_currency(value):
    """Formata valor no padrao brasileiro: R$ 7.677,35 (ponto no milhar, virgula no decimal)"""
    if value is None: value = 0.0
    v = float(value)
    inteiro, centavos = f"{v:.2f}".split(".")
    # Adiciona separador de milhar com ponto
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
    """Converte valor formatado BR (7.677,35) para float (7677.35)"""
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

def inject_masks():
    """Injeta JavaScript para mascaras de data e moeda"""
    st.markdown("""
    <script>
    (function() {
        function aplicarMascaras() {
            // Mascara de DATA (dd/mm/aaaa)
            document.querySelectorAll('[data-testid="stTextInput"]').forEach(function(el) {
                var label = el.querySelector('label');
                var input = el.querySelector('input');
                if (label && input && !input.dataset.maskDate && /data|recebimento/i.test(label.textContent)) {
                    input.dataset.maskDate = '1';
                    input.inputMode = 'numeric';
                    input.setAttribute('autocomplete', 'off');
                    input.addEventListener('input', function() {
                        var v = this.value.replace(/\D/g, '').substring(0, 8);
                        if (v.length > 4) v = v.substring(0,2) + '/' + v.substring(2,4) + '/' + v.substring(4);
                        else if (v.length > 2) v = v.substring(0,2) + '/' + v.substring(2);
                        this.value = v;
                    });
                    // Dispara evento para formatar valor inicial se existir
                    if (input.value) { input.dispatchEvent(new Event('input')); }
                }
            });
            // Mascara de VALOR MONETARIO BR (1.234,56)
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
                    // Dispara evento para formatar valor inicial se existir
                    if (input.value) { input.dispatchEvent(new Event('input')); }
                }
            });
            // Mascara também para inputs dentro do Streamlit (campos com label oculta)
            document.querySelectorAll('input:not([type="hidden"])').forEach(function(input) {
                if (input.dataset.maskMoney || input.dataset.maskDate) return;
                var parentText = (input.parentElement ? input.parentElement.textContent : '') + ' ' + (input.placeholder || '');
                if (!input.dataset.maskDate && /data|recebimento/i.test(parentText)) {
                    input.dataset.maskDate = '1';
                    input.inputMode = 'numeric';
                    input.addEventListener('input', function() {
                        var v = this.value.replace(/\D/g, '').substring(0, 8);
                        if (v.length > 4) v = v.substring(0,2) + '/' + v.substring(2,4) + '/' + v.substring(4);
                        else if (v.length > 2) v = v.substring(0,2) + '/' + v.substring(2);
                        this.value = v;
                    });
                    if (input.value) { input.dispatchEvent(new Event('input')); }
                }
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
        valor_total REAL DEFAULT 0, data_recebimento TEXT, programa_politica TEXT, setor_gasto TEXT
    )""")
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
            background: rgba(15, 23, 42, 0.75) !important;
            backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(14, 165, 233, 0.3) !important;
            border-radius: 24px !important;
            padding: 48px 40px !important;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5) !important;
            margin-top: 80px !important; max-width: 420px !important;
            margin-left: auto !important; margin-right: auto !important;
        }
        .marmed-title { font-size: 52px; font-weight: 800; text-align: center; color: #e0f2fe; letter-spacing: 6px; margin-bottom: 8px; }
        .subtitle { text-align: center; color: #7dd3fc; font-size: 14px; letter-spacing: 4px; margin-bottom: 36px; text-transform: uppercase; }
        .stTextInput label { color: #22d3ee !important; font-weight: 600; }
        .stTextInput > div > div > input { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; color: #e0f2fe !important; border-radius: 10px !important; }
        .stButton > button { background: linear-gradient(90deg, #06b6d4, #3b82f6) !important; color: #fff !important; font-weight: 700 !important; border-radius: 10px !important; border: none !important; width: 100%; padding: 12px !important; }
        .stSelectbox > div > div { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; border-radius: 10px !important; color: #e0f2fe !important; }
        .stNumberInput > div > div > input { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; color: #e0f2fe !important; border-radius: 10px !important; }
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
    st.markdown('<h1 style="color:#e0f2fe;text-align:center;font-size:48px;font-weight:800;letter-spacing:6px;">MARMED</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#7dd3fc;text-align:center;letter-spacing:4px;margin-bottom:4px;">SISTEMA INTEGRADO DE GESTAO</h3>', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#1e40af;text-align:center;letter-spacing:3px;font-size:20px;font-weight:700;margin-bottom:16px;">PREFEITURA MUNICIPAL DE LUMINARIAS</h2>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
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
            st.markdown(f'<div style="background:linear-gradient(135deg,#1a2a3a,#0f2027);border-radius:15px;padding:15px;text-align:center;border-left:4px solid {cor};border:1px solid rgba(34,211,238,0.3);margin-bottom:8px;"><div style="color:#b0eaff;font-size:11px;font-weight:600;">{tit}</div><div style="color:#00d4ff;font-size:18px;font-weight:700;">{format_currency(tc)}</div><div style="color:#94a3b8;font-size:10px;">Saldo: {format_currency(saldo)}</div></div>', unsafe_allow_html=True)
            if st.button(f"Ver {esf}", key=f"b_{esf}"):
                st.session_state["esfera_view"] = esf
                st.session_state["page"] = "ESFERA DETALHE"; st.rerun()
    tc = conn.execute("SELECT COUNT(*) FROM contas_receber").fetchone()[0]
    tco = conn.execute("SELECT COUNT(*) FROM ordens_compra").fetchone()[0]
    conn.close()
    st.markdown(f'<p style="text-align:center;color:#64748b;font-size:12px;margin-top:10px;">{tc} conta(s) | {tco} ordem(ns) de compra - {datetime.now().strftime("%d/%m/%Y")}</p>', unsafe_allow_html=True)

def esfera_detalhe():
    esf = st.session_state.get("esfera_view", "Federal")
    st.markdown(f'<h1 style="color:#e0f2fe;">{esf.upper()}</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    for cid, num, fonte, vtotal in conn.execute("SELECT id, numero_conta, fonte, valor_total FROM contas_receber WHERE esfera=? ORDER BY id DESC", (esf,)).fetchall():
        gasto = conn.execute("SELECT COALESCE(SUM(valor_compra),0) FROM ordens_compra WHERE conta_receber_id=?", (cid,)).fetchone()[0]
        saldo = vtotal - gasto
        with st.expander(f"{num} - Fonte {fonte}"):
            st.markdown(f'<p style="color:#b0eaff;">N: <strong>{num}</strong> | Fonte: <strong>{fonte}</strong> | Original: <strong>{format_currency(vtotal)}</strong> | Saldo: <strong style="color:{"#22c55e" if saldo>0 else "#ef4444"}">{format_currency(saldo)}</strong></p>', unsafe_allow_html=True)
            for o in conn.execute("SELECT ficha, tipo_despesa, data_compra, valor_compra, produto_servico FROM ordens_compra WHERE conta_receber_id=? ORDER BY id DESC", (cid,)).fetchall():
                st.markdown(f'<div style="background:rgba(30,41,59,0.6);border-radius:10px;padding:12px;margin-bottom:8px;border-left:3px solid #22d3ee;"><div style="color:#94a3b8;font-size:11px;">Ficha: {o[0] or "--"} | {o[1] or "--"} | {o[2] or "--"}</div><div style="color:#e0f2fe;font-size:14px;font-weight:600;">{format_currency(o[3])}</div><div style="color:#94a3b8;font-size:12px;">{o[4][:80]}{"..." if o[4] and len(o[4])>80 else ""}</div></div>', unsafe_allow_html=True)
    conn.close()
    if st.button("Voltar ao Inicio"):
        st.session_state["page"] = "Dashboard"; st.rerun()

def cadastrar_contas():
    st.markdown('<h1 style="color:#e0f2fe;">CADASTRAR CONTAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    inject_masks()
    with st.expander("NOVO CADASTRO", expanded=True):
        st.markdown('<p style="color:#fbbf24;font-size:12px;">* Campos obrigatorios</p>', unsafe_allow_html=True)
        esfera = st.selectbox("* 1. Selecione a Esfera", ["", "Federal", "Estadual", "Municipal"], key="esfera_cad")
        if esfera:
            fonte_mostrada = get_fonte(esfera)
            cor_fonte = {"Federal": "#3b82f6", "Estadual": "#22c55e", "Municipal": "#eab308"}
            st.markdown(f'''
            <div style="background:rgba(30,41,59,0.8);border-radius:10px;padding:15px;margin-bottom:15px;border-left:4px solid {cor_fonte.get(esfera, "#22d3ee")};">
                <div style="display:flex;align-items:center;justify-content:space-between;">
                    <div><span style="color:#94a3b8;font-size:13px;">Fonte vinculada:</span><span style="color:#22d3ee;font-size:28px;font-weight:800;margin-left:10px;">{fonte_mostrada}</span></div>
                    <div><span style="background:{"#3b82f6" if esfera=="Federal" else "#22c55e" if esfera=="Estadual" else "#eab308"};color:#fff;padding:6px 14px;border-radius:6px;font-size:13px;font-weight:700;">{esfera.upper()}</span></div>
                </div>
            </div>''', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#64748b;font-size:13px;">Selecione a Esfera para ver a Fonte</p>', unsafe_allow_html=True)
        num_conta = st.text_input("* 2. Numero da Conta", key="num_conta_cad")
        ref_contrato = st.selectbox("Referencia (opcional)", ["", "Resolucao", "Deliberacao", "Portaria"])
        num_ano_ref = st.text_input("Numero/Ano (opcional)")
        st.markdown('<p style="color:#7dd3fc;font-size:13px;font-weight:600;margin-top:10px;">3. Selecione o Tipo de Recurso</p>', unsafe_allow_html=True)
        tipo_recurso = st.selectbox("* Tipo de Recurso", ["", "Custeio", "Investimento", "Custeio/Investimento"], key="tipo_recurso_cad")
        val_custeio_str = ""
        val_invest_str = ""
        vt = 0.0
        if tipo_recurso:
            st.markdown('<p style="color:#7dd3fc;font-size:13px;font-weight:600;margin-top:10px;">4. Informe o(s) Valor(es) - Digite apenas numeros</p>', unsafe_allow_html=True)
            st.markdown('<p style="color:#94a3b8;font-size:11px;margin-bottom:5px;">O sistema coloca ponto e virgula automaticamente</p>', unsafe_allow_html=True)
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
        st.markdown('<p style="color:#7dd3fc;font-size:13px;font-weight:600;margin-top:10px;">5. Data de Recebimento - Digite apenas numeros</p>', unsafe_allow_html=True)
        st.markdown('<p style="color:#94a3b8;font-size:11px;margin-bottom:5px;">O sistema coloca as barras automaticamente</p>', unsafe_allow_html=True)
        data_receb = st.text_input("* Data Recebimento", key="data_receb_cad")
        if not data_receb:
            data_receb = datetime.now().strftime("%d/%m/%Y")
        st.markdown('<p style="color:#7dd3fc;font-size:13px;font-weight:600;margin-top:10px;">6. Informacoes Adicionais</p>', unsafe_allow_html=True)
        prog = st.text_input("Programa/Politica (opcional)")
        setor = st.text_input("Setor (opcional)")
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

def contas_cadastradas():
    st.markdown('<h1 style="color:#e0f2fe;">CONTAS CADASTRADAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    tabs = st.tabs(["FEDERAL", "ESTADUAL", "MUNICIPAL"])
    for tab_idx, esf in enumerate(["Federal", "Estadual", "Municipal"]):
        with tabs[tab_idx]:
            r = conn.execute("SELECT id, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso, valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento, programa_politica, setor_gasto FROM contas_receber WHERE esfera=? ORDER BY id DESC", (esf,)).fetchall()
            if r:
                import pandas as pd
                d = [(x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11]) for x in r]
                pdf = pd.DataFrame(d, columns=["ID", "Conta", "Fonte", "Ref.", "N/Ano", "Tipo", "Custeio", "Invest.", "Total", "Data", "Programa", "Setor"])
                for c in ["Custeio", "Invest.", "Total"]: pdf[c] = pdf[c].apply(lambda x: format_currency(x))
                st.dataframe(pdf, use_container_width=True, hide_index=True)
                st.markdown(f'<p style="color:#64748b;">Total: {len(r)} conta(s) {esf}</p>', unsafe_allow_html=True)
                st.markdown(f'<h4 style="color:#7dd3fc;">Editar / Excluir - {esf}</h4>', unsafe_allow_html=True)
                opts = {f"{x[1]} - Fonte {x[2]} (ID {x[0]})": x[0] for x in r}
                opts["Selecione..."] = None
                esc = st.selectbox(f"Selecione", list(opts.keys()), key=f"sel_{tab_idx}")
                if esc and opts[esc]:
                    rid = opts[esc]
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Editar", key=f"e_{tab_idx}_{rid}"): st.session_state["edit_conta_id"] = rid; st.session_state["page"] = "EDITAR CONTA"; st.rerun()
                    with c2:
                        if st.button("Excluir", key=f"d_{tab_idx}_{rid}"): conn.execute("DELETE FROM contas_receber WHERE id=?", (rid,)); conn.commit(); st.success("Excluida!"); st.rerun()
            else: st.markdown(f'<p style="color:#94a3b8;">Nenhuma conta {esf}.</p>', unsafe_allow_html=True)
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

def editar_conta():
    st.markdown('<h1 style="color:#e0f2fe;">EDITAR CONTA</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    inject_masks()
    rid = st.session_state.get("edit_conta_id")
    if not rid: st.error("Nenhuma conta."); return
    conn = sqlite3.connect("marmed.db")
    row = conn.execute("SELECT * FROM contas_receber WHERE id=?", (rid,)).fetchone()
    if not row: conn.close(); st.error("Nao encontrada."); return
    esfera = st.selectbox("* Esfera", ["", "Federal", "Estadual", "Municipal"], index=["", "Federal", "Estadual", "Municipal"].index(row[1]) if row[1] in ["", "Federal", "Estadual", "Municipal"] else 0, key="esf_edit")
    if esfera: st.markdown(f'<p style="color:#22d3ee;font-weight:600;font-size:18px;">Fonte: {get_fonte(esfera)}</p>', unsafe_allow_html=True)
    num_conta = st.text_input("* NConta", value=row[2] or "")
    ref_contrato = st.selectbox("Ref", ["", "Resolucao", "Deliberacao", "Portaria"], index=["", "Resolucao", "Deliberacao", "Portaria"].index(row[4]) if row[4] in ["", "Resolucao", "Deliberacao", "Portaria"] else 0)
    num_ano_ref = st.text_input("N/Ano", value=row[5] or "")
    tipo_recurso = st.selectbox("* Tipo", ["", "Custeio", "Investimento", "Custeio/Investimento"], index=["", "Custeio", "Investimento", "Custeio/Investimento"].index(row[6]) if row[6] in ["", "Custeio", "Investimento", "Custeio/Investimento"] else 0, key="tipo_edit")
    vc_str = st.text_input("Custeio", value=format_currency(row[7] or 0).replace("R$ ", ""), key="val_custeio_edit")
    vi_str = st.text_input("Investimento", value=format_currency(row[8] or 0).replace("R$ ", ""), key="val_invest_edit")
    vc = parse_br_currency(vc_str); vi = parse_br_currency(vi_str)
    data_receb = st.text_input("Data", value=row[10] or datetime.now().strftime("%d/%m/%Y"), key="data_edit")
    prog = st.text_input("Programa", value=row[11] or "")
    setor = st.text_input("Setor", value=row[12] or "")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Salvar"):
            conn.execute("UPDATE contas_receber SET esfera=?, numero_conta=?, fonte=?, referencia_tipo=?, referencia_numero=?, tipo_recurso=?, valor_pago_custeio=?, valor_pago_investimento=?, valor_total=?, data_recebimento=?, programa_politica=?, setor_gasto=? WHERE id=?", (esfera, num_conta, get_fonte(esfera), ref_contrato, num_ano_ref, tipo_recurso, vc, vi, vc+vi, data_receb, prog, setor, rid))
            conn.commit(); conn.close(); st.success("Atualizada!"); st.session_state["page"] = "CONTAS CADASTRADAS"; st.rerun()
    with c2:
        if st.button("Voltar"): st.session_state["page"] = "CONTAS CADASTRADAS"; st.rerun()
    conn.close()

def realizar_compras():
    st.markdown('<h1 style="color:#e0f2fe;">REALIZAR COMPRAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    inject_masks()
    conn = sqlite3.connect("marmed.db")
    st.markdown('<h3 style="color:#7dd3fc;">Editar / Excluir Solicitacoes</h3>', unsafe_allow_html=True)
    ordens = conn.execute("SELECT oc.id, oc.esfera, oc.numero_conta, oc.ficha, oc.valor_compra FROM ordens_compra oc ORDER BY oc.id DESC").fetchall()
    if ordens:
        opts = {f"{o[1]} - Conta {o[2]} - Ficha {o[3] or '--'} (R$ {o[4]:.2f}) - ID {o[0]}": o[0] for o in ordens}
        opts["Selecione..."] = None
        esc = st.selectbox("Selecione", list(opts.keys()), key="sel_ordem")
        if esc and opts[esc]:
            oid = opts[esc]
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Editar", key=f"eo_{oid}"): st.session_state["edit_ordem_id"] = oid; st.session_state["page"] = "EDITAR ORDEM COMPRA"; st.rerun()
            with c2:
                if st.button("Excluir", key=f"do_{oid}"): conn.execute("DELETE FROM ordens_compra WHERE id=?", (oid,)); conn.commit(); st.success("Excluida!"); st.rerun()
    else: st.markdown('<p style="color:#94a3b8;">Nenhuma solicitacao.</p>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#7dd3fc;">Nova Solicitacao</h3>', unsafe_allow_html=True)
    tabs = st.tabs(["FEDERAL", "ESTADUAL", "MUNICIPAL"])
    for tab_idx, esf in enumerate(["Federal", "Estadual", "Municipal"]):
        with tabs[tab_idx]:
            for cid, num, fonte, vtotal in conn.execute("SELECT id, numero_conta, fonte, valor_total FROM contas_receber WHERE esfera=? ORDER BY id DESC", (esf,)).fetchall():
                gasto = conn.execute("SELECT COALESCE(SUM(valor_compra),0) FROM ordens_compra WHERE conta_receber_id=?", (cid,)).fetchone()[0]
                saldo = vtotal - gasto
                with st.expander(f"{num} - Fonte {fonte}"):
                    st.markdown(f'<div style="background:rgba(30,41,59,0.6);border-radius:10px;padding:12px;"><div style="display:flex;justify-content:space-between;"><div style="color:#94a3b8;">Valor: <span style="color:#00d4ff;">{format_currency(vtotal)}</span></div><div style="color:#94a3b8;">Saldo: <span style="color:{"#22c55e" if saldo>0 else "#ef4444"};">{format_currency(saldo)}</span></div></div></div>', unsafe_allow_html=True)
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
    conn.close()

def editar_ordem_compra():
    st.markdown('<h1 style="color:#e0f2fe;">EDITAR SOLICITACAO</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    inject_masks()
    oid = st.session_state.get("edit_ordem_id")
    if not oid: st.error("Nenhuma."); return
    conn = sqlite3.connect("marmed.db")
    row = conn.execute("SELECT * FROM ordens_compra WHERE id=?", (oid,)).fetchone()
    if not row: conn.close(); st.error("Nao encontrada."); return
    ficha = st.text_input("Ficha", value=row[5] or "")
    td = st.selectbox("Despesa", ["", "Material de Consumo", "Servico PF", "Servico PJ", "Distribuicao Gratuita"], index=["", "Material de Consumo", "Servico PF", "Servico PJ", "Distribuicao Gratuita"].index(row[6]) if row[6] in ["", "Material de Consumo", "Servico PF", "Servico PJ", "Distribuicao Gratuita"] else 0, key="td_edit")
    data_c = st.text_input("Data", value=row[7] or datetime.now().strftime("%d/%m/%Y"), key="data_ordem_edit")
    valor_c_str = st.text_input("Valor", value=format_currency(row[8] or 0).replace("R$ ", ""), key="valor_ordem_edit")
    valor_c = parse_br_currency(valor_c_str)
    prod = st.text_area("Produto/Servico", height=120, value=row[9] or "")
    st.markdown(f'<p style="color:#94a3b8;">Conta: {row[3]} | Esfera: {row[2]} | Fonte: {row[4]}</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Salvar"):
            conn.execute("UPDATE ordens_compra SET ficha=?, tipo_despesa=?, data_compra=?, valor_compra=?, produto_servico=? WHERE id=?", (ficha, td, data_c, valor_c, prod, oid))
            conn.commit(); conn.close(); st.success("Atualizada!"); st.session_state["page"] = "REALIZAR COMPRAS"; st.rerun()
    with c2:
        if st.button("Voltar"): st.session_state["page"] = "REALIZAR COMPRAS"; st.rerun()
    conn.close()

def change_password():
    st.markdown('<h1 style="color:#e0f2fe;">Trocar Senha</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    cur = st.text_input("Senha atual", type="password")
    new = st.text_input("Nova senha", type="password")
    conf = st.text_input("Confirmar", type="password")
    if st.button("Salvar"):
        if new != conf: st.error("Nao conferem")
        else:
            ch = hashlib.sha256(cur.encode()).hexdigest()
            conn = sqlite3.connect("marmed.db")
            row = conn.execute("SELECT id FROM users WHERE username=? AND password_hash=?", (st.session_state["username"], ch)).fetchone()
            if row:
                nh = hashlib.sha256(new.encode()).hexdigest()
                conn.execute("UPDATE users SET password_hash=? WHERE id=?", (nh, row[0]))
                conn.commit(); conn.close(); st.success("Senha alterada!")
            else: conn.close(); st.error("Senha atual incorreta")

def bloco_saude(tit, sig, exp, url, cor="#1e40af"):
    with st.expander(f"{sig} - {tit}", expanded=False):
        st.markdown(f'<div style="background:linear-gradient(135deg,{cor},#0f172a);border-radius:12px;padding:20px;margin-bottom:15px;border-left:6px solid #22d3ee;">', unsafe_allow_html=True)
        st.markdown(f'<h2 style="color:#fff;margin:0;font-size:28px;font-weight:800;">{sig}</h2>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#e0f2fe;font-size:16px;font-weight:700;">{tit}</p>', unsafe_allow_html=True)
        st.markdown(f'<div style="background:rgba(15,23,42,0.7);border-radius:10px;padding:18px;color:#e0f2fe;font-size:15px;line-height:1.7;">{exp}</div>', unsafe_allow_html=True)
        if url: st.markdown(f'<a href="{url}" target="_blank" style="display:inline-block;margin-top:12px;padding:10px 20px;background:#22d3ee;color:#0f172a;border-radius:8px;text-decoration:none;font-weight:700;">Acessar Site Oficial</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        conn = sqlite3.connect("marmed.db")
        up = st.file_uploader("Enviar arquivo", type=["pdf", "docx", "doc", "txt", "csv"], key=f"up_{sig}")
        if up:
            db = up.read(); tx = extract_text_from_bytes(db, up.name)
            conn.execute("INSERT INTO arquivos_saude (bloco, nome_arquivo, conteudo_texto, dados_arquivo, data_upload) VALUES (?,?,?,?,?)", (sig, up.name, tx, db, datetime.now().strftime("%d/%m/%Y %H:%M")))
            conn.commit(); st.success("Arquivo anexado!"); st.rerun()
        arqs = conn.execute("SELECT nome_arquivo, data_upload, conteudo_texto FROM arquivos_saude WHERE bloco=? ORDER BY id DESC", (sig,)).fetchall()
        if arqs:
            for a in arqs: st.markdown(f'<div style="background:rgba(30,41,59,0.6);border-radius:6px;padding:8px;margin-bottom:5px;border-left:2px solid #22d3ee;"><span style="color:#e0f2fe;">{a[0]}</span> <span style="color:#64748b;">{a[1]}</span></div>', unsafe_allow_html=True)
            termo = st.text_input("Buscar", key=f"busca_{sig}")
            if termo:
                achou = False
                for a in arqs:
                    txt = a[2] or ""
                    matches = list(re.finditer(re.escape(termo), txt, re.IGNORECASE))
                    if matches:
                        achou = True; st.markdown(f'<p style="color:#22d3ee;font-weight:600;">{a[0]}</p>', unsafe_allow_html=True)
                        for m in matches[:5]:
                            s = max(0, m.start()-80); e = min(len(txt), m.end()+80)
                            trecho = txt[s:e]
                            dest = re.sub(re.escape(termo), f'<span style="background:#fbbf24;color:#000;padding:2px 4px;border-radius:3px;font-weight:700;">{termo}</span>', trecho, flags=re.IGNORECASE)
                            st.markdown(f'<div style="background:rgba(15,23,42,0.5);border-radius:6px;padding:10px;margin-bottom:6px;color:#cbd5e1;font-size:13px;font-family:monospace;">...{dest}...</div>', unsafe_allow_html=True)
                if not achou: st.markdown(f'<p style="color:#94a3b8;">Nada encontrado.</p>', unsafe_allow_html=True)
        else: st.markdown('<p style="color:#64748b;">Nenhum documento.</p>', unsafe_allow_html=True)
        conn.close()

def programas_saude():
    st.markdown('<h1 style="color:#e0f2fe;font-size:38px;">PROGRAMAS DE SAUDE</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    t1, t2, t3, t4, t5 = st.tabs(["MEDICAMENTOS", "GESTAO", "FINANCIAMENTO", "REGULACAO", "CONSORCIOS"])
    with t1:
        bloco_saude("Relacao Nacional de Medicamentos", "RENAME", 'A <strong>RENAME</strong> e a lista oficial do Ministerio da Saude.', "https://www.gov.br/saude/rename", "#0e7490")
        bloco_saude("Relacao Municipal de Medicamentos", "REMUME", 'A <strong>REMUME</strong> e a lista oficial de medicamentos do SUS.', "", "#0891b2")
        bloco_saude("Relacao Nacional de Equipamentos", "RENEM", 'A <strong>RENEM</strong> padroniza equipamentos.', "https://portalfns.saude.gov.br/", "#155e75")
        bloco_saude("Relacao Nacional de Acoes de Saude", "RENASES", 'A <strong>RENASES</strong> garante integralidade no SUS.', "", "#164e63")
    with t2:
        bloco_saude("e-Gestor APS", "E-GESTOR", 'O <strong>e-Gestor APS</strong> centraliza atencao basica.', "https://egestorab.saude.gov.br/", "#0369a1")
        bloco_saude("Core Saude MG", "CORE", 'O <strong>Core Saude MG</strong> gerencia leitos em MG.', "https://www.saude.mg.gov.br/", "#075985")
    with t3:
        bloco_saude("Fundo Nacional de Saude", "FNS", 'O <strong>FNS</strong> e o gestor financeiro.', "https://portalfns.saude.gov.br/", "#1d4ed8")
        bloco_saude("SIGTAP", "SIGTAP", 'O <strong>SIGTAP</strong> padroniza procedimentos.', "http://sigtap.datasus.gov.br/", "#1e3a8a")
        bloco_saude("PPI", "PPI", 'A <strong>PPI</strong> organiza fluxo de pacientes.', "", "#1e40af")
    with t4:
        bloco_saude("CONASEMS", "CONASEMS", 'O <strong>CONASEMS</strong> representa municipios.', "https://conasems.org.br/", "#4338ca")
        bloco_saude("COSEMS MG", "COSEMS", 'O <strong>COSEMS MG</strong> representa 853 municipios.', "https://www.cosemsmg.org.br/", "#3730a3")
    with t5:
        bloco_saude("CISLAV", "CISLAV", 'O <strong>CISLAV</strong> une prefeituras de Lavras.', "https://www.cislav.com/", "#312e81")

def plano_municipal_saude():
    st.markdown('<h1 style="color:#e0f2fe;font-size:38px;">PLANO MUNICIPAL DE SAUDE</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('''<div style="background:linear-gradient(135deg,#0e7490,#0f172a);border-radius:12px;padding:20px;margin-bottom:15px;border-left:6px solid #22d3ee;"><h2 style="color:#fff;margin:0;font-size:24px;font-weight:800;">PMS</h2><p style="color:#e0f2fe;font-size:16px;font-weight:700;">Plano Municipal de Saude</p><div style="background:rgba(15,23,42,0.7);border-radius:10px;padding:18px;color:#e0f2fe;font-size:15px;line-height:1.7;">O <strong>Plano Municipal de Saude (PMS)</strong> e o instrumento basico de planejamento do SUS no municipio.</div></div>''', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#7dd3fc;">Documentos do PMS</h3>', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    up = st.file_uploader("Enviar arquivo", type=["pdf", "docx", "doc", "txt", "csv"], key="up_pms")
    if up:
        db = up.read(); tx = extract_text_from_bytes(db, up.name)
        conn.execute("INSERT INTO arquivos_saude (bloco, nome_arquivo, conteudo_texto, dados_arquivo, data_upload) VALUES (?,?,?,?,?)", ("PMS", up.name, tx, db, datetime.now().strftime("%d/%m/%Y %H:%M")))
        conn.commit(); st.success("Arquivo anexado!"); st.rerun()
    arqs = conn.execute("SELECT nome_arquivo, data_upload, conteudo_texto FROM arquivos_saude WHERE bloco='PMS' ORDER BY id DESC").fetchall()
    if arqs:
        for a in arqs: st.markdown(f'<div style="background:rgba(30,41,59,0.6);border-radius:6px;padding:8px;margin-bottom:5px;border-left:2px solid #22d3ee;"><span style="color:#e0f2fe;">{a[0]}</span> <span style="color:#64748b;">{a[1]}</span></div>', unsafe_allow_html=True)
        termo = st.text_input("Buscar", key="busca_pms")
        if termo:
            achou = False
            for a in arqs:
                txt = a[2] or ""
                matches = list(re.finditer(re.escape(termo), txt, re.IGNORECASE))
                if matches:
                    achou = True; st.markdown(f'<p style="color:#22d3ee;">{a[0]}</p>', unsafe_allow_html=True)
                    for m in matches[:5]:
                        s = max(0, m.start()-80); e = min(len(txt), m.end()+80)
                        dest = re.sub(re.escape(termo), f'<span style="background:#fbbf24;color:#000;padding:2px 4px;border-radius:3px;font-weight:700;">{termo}</span>', txt[s:e], flags=re.IGNORECASE)
                        st.markdown(f'<div style="background:rgba(15,23,42,0.5);border-radius:6px;padding:10px;margin-bottom:6px;color:#cbd5e1;font-size:13px;font-family:monospace;">...{dest}...</div>', unsafe_allow_html=True)
            if not achou: st.markdown(f'<p style="color:#94a3b8;">Nada encontrado.</p>', unsafe_allow_html=True)
    else: st.markdown('<p style="color:#64748b;">Nenhum documento anexado.</p>', unsafe_allow_html=True)
    conn.close()

def norte_minha_gestao():
    st.markdown('<h1 style="color:#e0f2fe;font-size:38px;">NORTE DA MINHA GESTAO</h1>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('''<div style="background:linear-gradient(135deg,#7c3aed,#0f172a);border-radius:12px;padding:20px;margin-bottom:15px;border-left:6px solid #a78bfa;"><h2 style="color:#fff;margin:0;font-size:24px;font-weight:800;">DIRETRIZES</h2><p style="color:#e0f2fe;font-size:16px;font-weight:700;">Norte da Minha Gestao</p></div>''', unsafe_allow_html=True)
    for titulo, descricao, cor in [("Atencao Primaria","Ampliar cobertura ESF.","#7c3aed"),("Eficiencia Financeira","Otimizar recursos.","#2563eb"),("Valorizacao","Capacitacao continua.","#059669"),("Integracao Regional","Fortalecer CISLAV.","#d97706"),("Controle Social","Participacao no Conselho.","#dc2626")]:
        st.markdown(f'<div style="background:rgba(30,41,59,0.7);border-radius:10px;padding:15px;margin-bottom:10px;border-left:4px solid {cor};"><p style="color:{cor};font-size:16px;font-weight:700;margin:0;">{titulo}</p><p style="color:#cbd5e1;font-size:14px;margin:5px 0 0;">{descricao}</p></div>', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    up = st.file_uploader("Enviar arquivo", type=["pdf", "docx", "doc", "txt", "csv"], key="up_norte")
    if up:
        db = up.read(); tx = extract_text_from_bytes(db, up.name)
        conn.execute("INSERT INTO arquivos_saude (bloco, nome_arquivo, conteudo_texto, dados_arquivo, data_upload) VALUES (?,?,?,?,?)", ("NORTE_GESTAO", up.name, tx, db, datetime.now().strftime("%d/%m/%Y %H:%M")))
        conn.commit(); st.success("Documento anexado!"); st.rerun()
    arqs = conn.execute("SELECT nome_arquivo, data_upload, conteudo_texto FROM arquivos_saude WHERE bloco='NORTE_GESTAO' ORDER BY id DESC").fetchall()
    if arqs:
        for a in arqs: st.markdown(f'<div style="background:rgba(30,41,59,0.6);border-radius:6px;padding:8px;margin-bottom:5px;border-left:2px solid #a78bfa;"><span style="color:#e0f2fe;">{a[0]}</span> <span style="color:#64748b;">{a[1]}</span></div>', unsafe_allow_html=True)
    else: st.markdown('<p style="color:#64748b;">Nenhum documento anexado.</p>', unsafe_allow_html=True)
    conn.close()

def main():
    if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
    if "page" not in st.session_state: st.session_state["page"] = "Dashboard"
    if not st.session_state["logged_in"]: login_page()
    else:
        st.sidebar.markdown('<h3 style="color:#22d3ee;text-align:center;">MENU PRINCIPAL</h3>', unsafe_allow_html=True)
        st.sidebar.markdown('<hr>', unsafe_allow_html=True)
        st.sidebar.markdown('<p style="color:#7dd3fc;font-size:11px;">GESTAO FINANCEIRA</p>', unsafe_allow_html=True)
        if st.sidebar.button("INICIO", use_container_width=True): st.session_state["page"] = "Dashboard"; st.rerun()
        if st.sidebar.button("CADASTRAR CONTAS", use_container_width=True): st.session_state["page"] = "CADASTRAR CONTAS"; st.rerun()
        if st.sidebar.button("CONTAS CADASTRADAS", use_container_width=True): st.session_state["page"] = "CONTAS CADASTRADAS"; st.rerun()
        if st.sidebar.button("REALIZAR COMPRAS", use_container_width=True): st.session_state["page"] = "REALIZAR COMPRAS"; st.rerun()
        st.sidebar.markdown('<hr>', unsafe_allow_html=True)
        st.sidebar.markdown('<p style="color:#7dd3fc;font-size:11px;">SAUDE PUBLICA</p>', unsafe_allow_html=True)
        if st.sidebar.button("PROGRAMAS DE SAUDE", use_container_width=True): st.session_state["page"] = "PROGRAMAS SAUDE"; st.rerun()
        if st.sidebar.button("PLANO MUNICIPAL DE SAUDE", use_container_width=True): st.session_state["page"] = "PLANO MUNICIPAL"; st.rerun()
        if st.sidebar.button("NORTE DA MINHA GESTAO", use_container_width=True): st.session_state["page"] = "NORTE GESTAO"; st.rerun()
        st.sidebar.markdown('<hr>', unsafe_allow_html=True)
        if st.sidebar.button("Sair", use_container_width=True):
            st.session_state["logged_in"] = False; st.session_state.pop("username", None); st.rerun()
        p = st.session_state["page"]
        if p == "Dashboard": dashboard()
        elif p == "CADASTRAR CONTAS": cadastrar_contas()
        elif p == "CONTAS CADASTRADAS": contas_cadastradas()
        elif p == "EDITAR CONTA": editar_conta()
        elif p == "REALIZAR COMPRAS": realizar_compras()
        elif p == "EDITAR ORDEM COMPRA": editar_ordem_compra()
        elif p == "ESFERA DETALHE": esfera_detalhe()
        elif p == "PROGRAMAS SAUDE": programas_saude()
        elif p == "PLANO MUNICIPAL": plano_municipal_saude()
        elif p == "NORTE GESTAO": norte_minha_gestao()
        elif p == "Trocar Senha": change_password()

if __name__ == "__main__":
    main()
