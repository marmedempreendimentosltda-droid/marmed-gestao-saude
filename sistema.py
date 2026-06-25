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

def eh_menor_ou_igual(a, b):
    return a <= b

def eh_maior_que(a, b):
    return a > b

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
                st.markdown(f'<div style="background:rgba(30,41,59,0.8);border-radius:10px;padding:12px;margin-bottom:8px;border-left:3px solid #22d3ee;"><div style="color:#cbd5e1;font-size:12px;">Ficha: <strong style="color:#f8fafc;">{o[0] or "--"}</strong> | <strong 
