import streamlit as st
import hashlib
import sqlite3
import pandas as pd
from datetime import datetime, date

st.set_page_config(
    page_title="MARMED - Gestão em Saúde Pública",
    page_icon=":hospital:",
    layout="wide",
    initial_sidebar_state="expanded"
)

DEFAULT_USER = "admin"
DEFAULT_PASS = "Diretor2025#"
DEFAULT_HASH = hashlib.sha256(DEFAULT_PASS.encode()).hexdigest()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

def init_db():
    conn = sqlite3.connect("marmed.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS contas_pagar (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, credor TEXT, valor REAL, vencimento TEXT, status TEXT, categoria TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS contas_receber (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, devedor TEXT, valor REAL, vencimento TEXT, status TEXT, categoria TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS empenhos (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, descricao TEXT, valor REAL, data TEXT, fonte TEXT, status TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS licitacoes (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, objeto TEXT, modalidade TEXT, valor REAL, data_abertura TEXT, status TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS contratos (id INTEGER PRIMARY KEY AUTOINCREMENT, numero TEXT, contratado TEXT, objeto TEXT, valor REAL, inicio TEXT, fim TEXT, status TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS repasses_federal (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, valor REAL, data TEXT, programa TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS repasses_estadual (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, valor REAL, data TEXT, programa TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS recursos_municipal (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, valor REAL, data TEXT, origem TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS transferencias (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, origem TEXT, destino TEXT, valor REAL, data TEXT, tipo TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS transposicoes (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, origem TEXT, destino TEXT, valor REAL, data TEXT, tipo TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT UNIQUE, senha_hash TEXT)""")
    c.execute("""INSERT OR IGNORE INTO usuarios (usuario, senha_hash) VALUES (?, ?)""", (DEFAULT_USER, DEFAULT_HASH))
    conn.commit()
    return conn

conn = init_db()

def format_currency(val):<br/>
    try:<br/>
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")<br/>
    except:
        return "R$ 0,00"

LOGIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');<br/>
.stApp { background: linear-gradient(135deg, #050510 0%, #0a0a20 50%, #02020a 100%); }<br/>
.login-container { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }<br/>
.title-3d { font-family: 'Orbitron', sans-serif; font-size: 5rem; font-weight: 900; color: #00d4ff; text-align: center; perspective: 1000px; margin-bottom: 10px; text-shadow: 0 0 10px #00d4ff, 0 0 30px #00d4ff, 0 0 60px #008cff; }<br/>
.title-3d span { display: inline-block; opacity: 0; transform-style: preserve-3d; }<br/>
.title-3d .m1 { --tx: -500px; --ty: -300px; --tz: 800px; --rx: 120deg; --ry: -80deg; }<br/>
.title-3d .a1 { --tx: 400px; --ty: -250px; --tz: -600px; --rx: -100deg; --ry: 90deg; }<br/>
.title-3d .r1 { --tx: -300px; --ty: 350px; --tz: 500px; --rx: 80deg; --ry: -120deg; }<br/>
.title-3d .m2 { --tx: 500px; --ty: 300px; --tz: -400px; --rx: -70deg; --ry: 100deg; }<br/>
.title-3d .e1 { --tx: -400px; --ty: -200px; --tz: 700px; --rx: 110deg; --ry: -90deg; }<br/>
.title-3d .d1 { --tx: 300px; --ty: 250px; --tz: -800px; --rx: -130deg; --ry: 70deg; }<br/>
@keyframes flyIn { 0% { opacity: 0; transform: translate3d(var(--tx), var(--ty), var(--tz)) rotateX(var(--rx)) rotateY(var(--ry)); } 60% { opacity: 1; } 100% { opacity: 1; transform: translate3d(0, 0, 0) rotateX(0deg) rotateY(0deg); } }<br/>
@keyframes glowPulse { 0%, 100% { text-shadow: 0 0 10px #00d4ff, 0 0 30px #00d4ff, 0 0 60px #008cff; } 50% { text-shadow: 0 0 20px #00d4ff, 0 0 50px #00d4ff, 0 0 100px #008cff, 0 0 150px #ffffff; } }<br/>
@keyframes flash { 0% { text-shadow: 0 0 5px #fff, 0 0 20px #ffd700; color: #ffffff; } 50% { text-shadow: 0 0 50px #ffd700, 0 0 100px #ffffff; color: #ffd700; } 100% { text-shadow: 0 0 10px #00d4ff, 0 0 30px #00d4ff; color: #00d4ff; } }<br/>
.title-3d span { animation: flyIn 3s ease-out forwards, glowPulse 2s ease-in-out infinite 3s, flash 0.4s ease-out 3s; }<br/>
.title-3d .m1 { animation-delay: 0s, 3s, 3s; }<br/>
.title-3d .a1 { animation-delay: 0.18s, 3.18s, 3.18s; }<br/>
.title-3d .r1 { animation-delay: 0.36s, 3.36s, 3.36s; }<br/>
.title-3d .m2 { animation-delay: 0.54s, 3.54s, 3.54s; }<br/>
.title-3d .e1 { animation-delay: 0.72s, 3.72s, 3.72s; }<br/>
.title-3d .d1 { animation-delay: 0.90s, 3.90s, 3.90s; }<br/>
.subtitle-cyan { color: #00d4ff; font-size: 1.5rem; text-align: center; font-family: 'Orbitron', sans-serif; margin-top: 0; }<br/>
.subtitle-blue { color: #87cefa; font-size: 1.2rem; text-align: center; margin-top: 5px; }<br/>
.glass-card { background: rgba(255, 255, 255, 0.08); backdrop-filter: blur(16px); border: 1px solid rgba(0, 212, 255, 0.3); border-radius: 20px; padding: 40px; width: 100%; max-width: 420px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5); margin-top: 30px; }<br/>
.field-label { color: #e0f7ff; font-weight: 600; margin-bottom: 5px; display: block; }<br/>
.stTextInput > div > div > input { background: rgba(255, 255, 255, 0.15) !important; border: 2px solid #00d4ff !important; color: #ffffff !important; border-radius: 10px !important; padding: 12px !important; }<br/>
.stTextInput > div > div > input:focus { border-color: #ffd700 !important; box-shadow: 0 0 15px #ffd700 !important; }<br/>
.stButton > button { width: 100%; background: linear-gradient(90deg, #00d4ff, #008cff) !important; color: #ffffff !important; border: none !important; border-radius: 10px !important; padding: 12px !important; font-weight: 700 !important; }<br/>
.stButton > button:hover { box-shadow: 0 0 25px #00d4ff !important; transform: translateY(-2px) !important; }<br/>
#particles-canvas { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; pointer-events: none; }
</style>
<canvas id="particles-canvas"></canvas>
<script>
(function(){ const canvas = document.getElementById('particles-canvas'); if (!canvas) return; const ctx = canvas.getContext('2d'); let particles = []; function resize(){ canvas.width = window.innerWidth; canvas.height = window.innerHeight; } window.addEventListener('resize', resize); resize(); for (let i = 0; i < 80; i++) { particles.push({ x: Math.random() * canvas.width, y: Math.random() * canvas.height, r: Math.random() * 2 + 1, dx: (Math.random() - 0.5) * 0.5, dy: (Math.random() - 0.5) * 0.5, alpha: Math.random() * 0.5 + 0.2 }); } function animate(){ ctx.clearRect(0, 0, canvas.width, canvas.height); particles.forEach(p => { p.x += p.dx; p.y += p.dy; if (p.x < 0 || p.x > canvas.width) p.dx *= -1; if (p.y < 0 || p.y > canvas.height) p.dy *= -1; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fillStyle = 'rgba(0, 212, 255, ' + p.alpha + ')'; ctx.fill(); }); requestAnimationFrame(animate); } animate(); })();
</script>
"""

def login_page():
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div class="login-container">
        <div class="title-3d">
            <span class="m1">M</span><span class="a1">A</span><span class="r1">R</span><span class="m2">M</span><span class="e1">E</span><span class="d1">D</span>
        </div>
        <div class="subtitle-cyan">Gestão em Saúde Pública</div>
        <div class="subtitle-blue">Luminárias - MG</div>
    </div>
    """, unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<span class='field-label'>Usuário</span>", unsafe_allow_html=True)
        usuario = st.text_input("", key="user_login", label_visibility="collapsed")
        st.markdown("<span class='field-label'>Senha</span>", unsafe_allow_html=True)
        senha = st.text_input("", type="password", key="pass_login", label_visibility="collapsed")
        if st.button("Entrar", key="btn_login"):
            h = hashlib.sha256(senha.encode()).hexdigest()
            c = conn.cursor()
            c.execute("SELECT * FROM usuarios WHERE usuario=? AND senha_hash=?", (usuario, h))
            if c.fetchone():
                st.session_state.logged_in = True
                st.session_state.page = "Dashboard"
                st.success("Login realizado!")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
        st.markdown("</div>", unsafe_allow_html=True)

APP_CSS = """
<style>
.stApp { background: linear-gradient(135deg, #050510 0%, #0a0a20 50%, #02020a 100%); }<br/>
h1, h2, h3 { color: #00d4ff; }<br/>
.metric-card { background: rgba(255, 255, 255, 0.08); backdrop-filter: blur(12px); border: 1px solid rgba(0, 212, 255, 0.3); border-radius: 15px; padding: 20px; text-align: center; }<br/>
.metric-card h3 { margin: 0; font-size: 0.95rem; color: #87cefa; }<br/>
.metric-card p { margin: 10px 0 0; font-size: 1.5rem; font-weight: 700; color: #00d4ff; }<br/>
.glass-card { background: rgba(255, 255, 255, 0.08); backdrop-filter: blur(12px); border: 1px solid rgba(0, 212, 255, 0.3); border-radius: 15px; padding: 20px; margin-bottom: 20px; }<br/>
.stButton > button { background: linear-gradient(90deg, #00d4ff, #008cff) !important; color: #fff !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; }<br/>
.stButton > button:hover { box-shadow: 0 0 20px #00d4ff !important; }<br/>
.stTextInput > div > div > input, .stNumberInput > div > div > input, .stDateInput > div > div > input, .stSelectbox > div > div > div { background: rgba(255, 255, 255, 0.12) !important; border: 1px solid rgba(0, 212, 255, 0.5) !important; color: #fff !important; border-radius: 8px !important; }
</style>
"""

def totals():
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(valor),0) FROM repasses_federal")
    f = c.fetchone()[0] or 1250000
    c.execute("SELECT COALESCE(SUM(valor),0) FROM repasses_estadual")
    e = c.fetchone()[0] or 890000
    c.execute("SELECT COALESCE(SUM(valor),0) FROM recursos_municipal")
    m = c.fetchone()[0] or 450000
    c.execute("SELECT COALESCE(SUM(valor),0) FROM transferencias")
    t = c.fetchone()[0] or 320000
    c.execute("SELECT COALESCE(SUM(valor),0) FROM transposicoes")
    tp = c.fetchone()[0] or 180000
    return {"REPASSE FEDERAL": f, "REPASSE ESTADUAL": e, "RECURSO MUNICIPAL": m, "TRANSFERÊNCIA": t, "TRANSPOSIÇÃO": tp}

def dashboard_page():
    st.title("Dashboard")
    values = totals()
    cols = st.columns(5)
    for col, (label, value) in zip(cols, values.items()):<br/>
        col.markdown(f'<div class="metric-card"><h3>{label}</h3><p>R$ {value:,.2f}</p></div>', unsafe_allow_html=True)

def sidebar():
    menu = ["Dashboard", "Contas a Pagar", "Contas a Receber", "Empenhos", "Licita\u00e7\u00f5es", "Contratos", "Relat\u00f3rios", "Trocar Senha", "Sair"]
    st.sidebar.markdown('<h1 style="text-align:center; color:#00d4ff;">MARMED</h1>', unsafe_allow_html=True)<br/>
    st.sidebar.markdown('<p style="text-align:center; color:#87cefa;">Luminárias - MG</p>', unsafe_allow_html=True)<br/>
    for item in menu:<br/>
        if st.sidebar.button(item, key=f"menu_{item}", use_container_width=True):<br/>
            if item == "Sair":
                st.session_state.logged_in = False
                st.rerun()
            else:
                st.session_state.page = item
                st.rerun()

def crud_page(table, cols, labels, title, status_ops=None):
    st.title(title)
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table}")
    rows = c.fetchall()
    df = pd.DataFrame(rows, columns=["id"] + cols) if rows else pd.DataFrame()
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.subheader("Cadastrar")
    with st.form(f"form_{table}"):
        inputs = {}
        for col, label in zip(cols, labels):
            st.markdown(f"<span class='field-label'>{label}</span>", unsafe_allow_html=True)
            if col == "valor":
                inputs[col] = st.number_input("", value=0.0, step=0.01, key=f"{table}_{col}", label_visibility="collapsed")
            elif col in ["vencimento", "data", "data_abertura", "inicio", "fim"]:
                inputs[col] = st.date_input("", value=date.today(), key=f"{table}_{col}", label_visibility="collapsed").isoformat()
            elif col == "status" and status_ops:
                inputs[col] = st.selectbox("", status_ops, key=f"{table}_{col}", label_visibility="collapsed")
            else:
                inputs[col] = st.text_input("", key=f"{table}_{col}", label_visibility="collapsed")
        if st.form_submit_button("Salvar"):
            placeholders = ", ".join(["?"] * len(cols))
            c.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})", list(inputs.values()))
            conn.commit()
            st.success("Salvo!")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    if not df.empty:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Registros")
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

def trocar_senha_page():
    st.title("Trocar Senha")
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<span class='field-label'>Senha Atual</span>", unsafe_allow_html=True)
    atual = st.text_input("", type="password", key="senha_atual", label_visibility="collapsed")
    st.markdown("<span class='field-label'>Nova Senha</span>", unsafe_allow_html=True)
    nova = st.text_input("", type="password", key="senha_nova", label_visibility="collapsed")
    st.markdown("<span class='field-label'>Confirmar Nova Senha</span>", unsafe_allow_html=True)
    confirma = st.text_input("", type="password", key="senha_confirma", label_visibility="collapsed")
    if st.button("Alterar Senha"):<br/>
        if nova != confirma:
            st.error("As senhas não conferem.")
        else:
            c = conn.cursor()
            h_atual = hashlib.sha256(atual.encode()).hexdigest()
            c.execute("SELECT * FROM usuarios WHERE usuario=? AND senha_hash=?", (DEFAULT_USER, h_atual))
            if not c.fetchone():
                st.error("Senha atual incorreta.")
            else:
                h_nova = hashlib.sha256(nova.encode()).hexdigest()
                c.execute("UPDATE usuarios SET senha_hash=? WHERE usuario=?", (h_nova, DEFAULT_USER))
                conn.commit()
                st.success("Senha alterada!")
    st.markdown("</div>", unsafe_allow_html=True)

def main():<br/>
    if not st.session_state.logged_in:
        login_page()
    else:
        st.markdown(APP_CSS, unsafe_allow_html=True)
        sidebar()
        p = st.session_state.page
        if p == "Dashboard":
            dashboard_page()
        elif p == "Contas a Pagar":
            crud_page("contas_pagar", ["descricao","credor","valor","vencimento","status","categoria"], ["Descrição","Credor","Valor","Vencimento","Status","Categoria"], "Contas a Pagar", ["Pendente","Pago","Vencido"])
        elif p == "Contas a Receber":
            crud_page("contas_receber", ["descricao","devedor","valor","vencimento","status","categoria"], ["Descrição","Devedor","Valor","Vencimento","Status","Categoria"], "Contas a Receber", ["Pendente","Recebido","Vencido"])
        elif p == "Empenhos":
            crud_page("empenhos", ["numero","descricao","valor","data","fonte","status"], ["Número","Descrição","Valor","Data","Fonte","Status"], "Empenhos", ["Ativo","Liquidado","Anulado"])
        elif p == "Licita\u00e7\u00f5es":
            crud_page("licitacoes", ["numero","objeto","modalidade","valor","data_abertura","status"], ["Número","Objeto","Modalidade","Valor","Data Abertura","Status"], "Licitações", ["Em Andamento","Concluída","Cancelada"])
        elif p == "Contratos":
            crud_page("contratos", ["numero","contratado","objeto","valor","inicio","fim","status"], ["Número","Contratado","Objeto","Valor","Início","Fim","Status"], "Contratos", ["Vigente","Encerrado","Cancelado"])
        elif p == "Relat\u00f3rios":
            st.title("Relatórios")
            st.info("Selecione um módulo para ver os dados.")
        elif p == "Trocar Senha":
            trocar_senha_page()

if __name__ == "__main__":
    main()
