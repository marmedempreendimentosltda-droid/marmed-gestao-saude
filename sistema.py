import streamlit as st
import sqlite3
import hashlib
import re
from datetime import datetime

st.set_page_config(page_title="MARMED", layout="wide")

def format_currency(value):
    if value is None:
        value = 0.0
    return f"R$ {float(value):,.2f}"

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
        text = f"[Nao foi possivel extrair texto de {filename}]"
    return text

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
        .stApp { background: linear-gradient(135deg, #0f172a, #1e3a8a, #0f172a); overflow: hidden; }
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
        .stTextInput label { color: #22d3ee !important; font-weight: 600; font-size: 13px; }
        .stTextInput > div > div > input { background: rgba(30, 41, 59, 0.8) !important; border: 1px solid rgba(34, 211, 238, 0.3) !important; color: #e0f2fe !important; border-radius: 10px !important; }
        .stButton > button { background: linear-gradient(90deg, #06b6d4, #3b82f6) !important; color: #fff !important; font-weight: 700 !important; border-radius: 10px !important; border: none !important; width: 100%; padding: 12px !important; letter-spacing: 2px; }
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
                st.error("Usuario ou senha invalidos")
        st.markdown('<p style="text-align:center;color:#94a3b8;font-size:12px;margin-top:28px;">Acesso restrito a usuarios autorizados</p>', unsafe_allow_html=True)

def dashboard():
    st.markdown('<h1 style="color:#e0f2fe;text-align:center;font-size:48px;font-weight:800;letter-spacing:6px;">MARMED</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#7dd3fc;text-align:center;letter-spacing:4px;margin-bottom:4px;">SISTEMA INTEGRADO DE GESTAO</h3>', unsafe_allow_html=True)
    st.markdown('<h2 style="color:#1e40af;text-align:center;letter-spacing:3px;font-size:20px;font-weight:700;margin-bottom:16px;">PREFEITURA MUNICIPAL DE LUMINARIAS</h2>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    c = conn.cursor()
    for i, (tit, esf, cor) in enumerate(zip(
        ["REPASSE FEDERAL", "REPASSE ESTADUAL", "RECURSO MUNICIPAL", "TRANSFERENCIA", "TRANSPOSICAO"],
        ["Federal", "Estadual", "Municipal", "Transferencia", "Transposicao"],
        ["#3b82f6", "#22c55e", "#eab308", "#a855f7", "#ef4444"]
    )):
        total_contas = c.execute("SELECT COALESCE(SUM(valor_total),0) FROM contas_receber WHERE esfera=?", (esf,)).fetchone()[0]
        total_gasto = c.execute("SELECT COALESCE(SUM(valor_compra),0) FROM ordens_compra WHERE esfera=?", (esf,)).fetchone()[0]
        saldo = total_contas - total_gasto
        with st.columns(5)[i]:
            st.markdown(f'<div style="background:linear-gradient(135deg,#1a2a3a,#0f2027);border-radius:15px;padding:15px;text-align:center;border-left:4px solid {cor};border:1px solid rgba(34,211,238,0.3);margin-bottom:8px;"><div style="color:#b0eaff;font-size:11px;letter-spacing:1px;font-weight:600;">{tit}</div><div style="color:#00d4ff;font-size:18px;font-weight:700;">{format_currency(total_contas)}</div><div style="color:#94a3b8;font-size:10px;margin-top:4px;">Saldo: {format_currency(saldo)}</div></div>', unsafe_allow_html=True)
            if st.button(f"Ver {esf}", key=f"btn_{esf}"):
                st.session_state["esfera_view"] = esf
                st.session_state["page"] = "ESFERA DETALHE"
                st.rerun()
    tc = c.execute("SELECT COUNT(*) FROM contas_receber").fetchone()[0]
    tco = c.execute("SELECT COUNT(*) FROM ordens_compra").fetchone()[0]
    conn.close()
    st.markdown(f'<p style="text-align:center;color:#64748b;font-size:12px;margin-top:10px;">{tc} conta(s) | {tco} ordem(ns) de compra - {datetime.now().strftime("%d/%m/%Y")}</p>', unsafe_allow_html=True)

def esfera_detalhe():
    esf = st.session_state.get("esfera_view", "Federal")
    st.markdown(f'<h1 style="color:#e0f2fe;">{esf.upper()}</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    for cid, num, fonte, vtotal in conn.execute("SELECT id, numero_conta, fonte, valor_total FROM contas_receber WHERE esfera=? ORDER BY id DESC", (esf,)).fetchall():
        gasto = conn.execute("SELECT COALESCE(SUM(valor_compra),0) FROM ordens_compra WHERE conta_receber_id=?", (cid,)).fetchone()[0]
        saldo = vtotal - gasto
        with st.expander(f"{num} - Fonte {fonte}"):
            st.markdown(f'<p style="color:#b0eaff;">N: <strong>{num}</strong> | Fonte: <strong>{fonte}</strong> | Original: <strong>{format_currency(vtotal)}</strong> | Saldo: <strong style="color:{"#22c55e" if saldo>0 else "#ef4444"}">{format_currency(saldo)}</strong></p>', unsafe_allow_html=True)
            for o in conn.execute("SELECT id, ficha, tipo_despesa, data_compra, valor_compra, produto_servico FROM ordens_compra WHERE conta_receber_id=? ORDER BY id DESC", (cid,)).fetchall():
                st.markdown(f'<div style="background:rgba(30,41,59,0.6);border-radius:10px;padding:12px;margin-bottom:8px;border-left:3px solid #22d3ee;"><div style="color:#94a3b8;font-size:11px;">Ficha: {o[1] or "--"} | {o[2] or "--"} | {o[3] or "--"}</div><div style="color:#e0f2fe;font-size:14px;font-weight:600;">{format_currency(o[4])}</div><div style="color:#94a3b8;font-size:12px;">{o[5][:80]}{"..." if o[5] and len(o[5])>80 else ""}</div></div>', unsafe_allow_html=True)
    conn.close()
    if st.button("Voltar ao Inicio"):
        st.session_state["page"] = "Dashboard"
        st.rerun()

def cadastrar_contas():
    st.markdown('<h1 style="color:#e0f2fe;">CADASTRAR CONTAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    for k in ["esfera_cad", "val_custeio_cad", "val_invest_cad", "tipo_recurso_cad"]:
        st.session_state.pop(k, None)
    with st.expander("NOVO CADASTRO", expanded=True):
        st.markdown('<p style="color:#fbbf24;font-size:12px;margin-bottom:10px;">* Campos obrigatorios</p>', unsafe_allow_html=True)
        esfera = st.selectbox("* Esfera", ["", "Federal", "Estadual", "Municipal"], key="esfera_cad")
        num_conta = st.text_input("* Numero da Conta")
        if esfera: st.markdown(f'<p style="color:#22d3ee;font-weight:600;">Fonte: {get_fonte(esfera)}</p>', unsafe_allow_html=True)
        ref_contrato = st.selectbox("Referencia (opcional)", ["", "Resolucao", "Deliberacao", "Portaria"])
        num_ano_ref = st.text_input("Numero/Ano (opcional)")
        tipo_recurso = st.selectbox("* Tipo de Recurso", ["", "Custeio", "Investimento", "Custeio/Investimento"], key="tipo_recurso_cad")
        vc = st.number_input("* Custeio", min_value=0.0, step=0.01, format="%.2f", key="val_custeio_cad")
        vi = st.number_input("* Investimento", min_value=0.0, step=0.01, format="%.2f", key="val_invest_cad")
        vt = vc + vi
        if vt > 0: st.markdown(f'<p style="color:#00d4ff;font-size:16px;font-weight:700;">Total: {format_currency(vt)}</p>', unsafe_allow_html=True)
        data_receb = st.text_input("* Data Recebimento", value=datetime.now().strftime("%d/%m/%Y"))
        prog = st.text_input("Programa/Politica (opcional)")
        setor = st.text_input("Setor (opcional)")
        if st.button("Salvar Conta", key="salvar_conta"):
            erros = [x for x, v in [("Esfera", esfera), ("Conta", num_conta), ("Recurso", tipo_recurso), ("Valor", vt>0), ("Data", data_receb)] if not v]
            if erros: st.error(f"Preencha: {', '.join(erros)}")
            else:
                conn = sqlite3.connect("marmed.db")
                conn.execute("INSERT INTO contas_receber (esfera, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso, valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento, programa_politica, setor_gasto) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (esfera, num_conta, get_fonte(esfera), ref_contrato, num_ano_ref, tipo_recurso, vc, vi, vt, data_receb, prog, setor))
                conn.commit()
                conn.close()
                st.success("Conta cadastrada!")
                st.rerun()

def contas_cadastradas():
    st.markdown('<h1 style="color:#e0f2fe;">CONTAS CADASTRADAS</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    conn = sqlite3.connect("marmed.db")
    for tab, esf in [(st.tabs(["FEDERAL", "ESTADUAL", "MUNICIPAL"])[0], "Federal"), (st.tabs(["FEDERAL", "ESTADUAL", "MUNICIPAL"])[1], "Estadual"), (st.tabs(["FEDERAL", "ESTADUAL", "MUNICIPAL"])[2], "Municipal")]:
        with tab:
            r = conn.execute("SELECT id, numero_conta, fonte, referencia_tipo, referencia_numero, tipo_recurso, valor_pago_custeio, valor_pago_investimento, valor_total, data_recebimento, programa_politica, setor_gasto FROM contas_receber WHERE esfera=? ORDER BY id DESC", (esf,)).fetchall()
            if r:
                import pandas as pd
                cols = ["ID", "Conta", "Fonte", "Ref.", "N/Ano", "Tipo", "Custeio", "Invest.", "Total", "Data", "Programa", "Setor"]
                d = [(x[0], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11], x[12]) for x in r]
                pdf = pd.DataFrame(d, columns=cols)
                for c in ["Custeio", "Invest.", "Total"]: pdf[c] = pdf[c].apply(lambda x: format_currency(x))
                st.dataframe(pdf, use_container_width=True, hide_index=True)
            else: st.markdown(f'<p style="color:#94a3b8;">Nenhuma conta {esf}.</p>', unsafe_allow_html=True)
    # ... superavit ...
    conn.close()

# [Funcoes editar_conta, realizar_compras, editar_ordem_compra, change_password mantidas]
# Pular para o bloco principal - PROGRAMAS DE SAUDE

def bloco_saude(titulo, sigla, explicacao, site_url, cor_topo="#1e40af"):
    with st.expander(f"{sigla} - {titulo}", expanded=False):
        st.markdown(f'<div style="background:linear-gradient(135deg,{cor_topo},#0f172a);border-radius:12px;padding:20px;margin-bottom:15px;border-left:6px solid #22d3ee;">', unsafe_allow_html=True)
        st.markdown(f'<h2 style="color:#ffffff;margin:0 0 4px 0;font-size:28px;font-weight:800;letter-spacing:2px;">{sigla}</h2>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:#e0f2fe;font-size:16px;margin-bottom:12px;font-weight:700;">{titulo}</p>', unsafe_allow_html=True)
        st.markdown(f'<div style="background:rgba(15,23,42,0.7);border-radius:10px;padding:18px;color:#e0f2fe;font-size:15px;line-height:1.7;">{explicacao}</div>', unsafe_allow_html=True)
        if site_url:
            st.markdown(f'<a href="{site_url}" target="_blank" style="display:inline-block;margin-top:12px;padding:10px 20px;background:#22d3ee;color:#0f172a;border-radius:8px;text-decoration:none;font-weight:700;font-size:14px;">Acessar Site Oficial</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        conn = sqlite3.connect("marmed.db")
        up = st.file_uploader("Enviar arquivo (PDF, Word, TXT, CSV)", type=["pdf", "docx", "doc", "txt", "csv"], key=f"upload_{sigla}")
        if up:
            db = up.read()
            tx = extract_text_from_bytes(db, up.name)
            conn.execute("INSERT INTO arquivos_saude (bloco, nome_arquivo, conteudo_texto, dados_arquivo, data_upload) VALUES (?,?,?,?,?)", (sigla, up.name, tx, db, datetime.now().strftime("%d/%m/%Y %H:%M")))
            conn.commit()
            st.success(f"Arquivo '{up.name}' anexado!")
            st.rerun()
        arqs = conn.execute("SELECT id, nome_arquivo, data_upload, conteudo_texto FROM arquivos_saude WHERE bloco=? ORDER BY id DESC", (sigla,)).fetchall()
        if arqs:
            st.markdown(f'<p style="color:#94a3b8;">{len(arqs)} arquivo(s) anexado(s)</p>', unsafe_allow_html=True)
            for a in arqs:
                st.markdown(f'<div style="background:rgba(30,41,59,0.6);border-radius:6px;padding:8px;margin-bottom:5px;border-left:2px solid #22d3ee;"><span style="color:#e0f2fe;">{a[1]}</span> <span style="color:#64748b;font-size:11px;">{a[2]}</span></div>', unsafe_allow_html=True)
            termo = st.text_input("Buscar palavra/frase", key=f"busca_{sigla}")
            if termo:
                achou = False
                for a in arqs:
                    txt = a[3] or ""
                    matches = list(re.finditer(re.escape(termo), txt, re.IGNORECASE))
                    if matches:
                        achou = True
                        st.markdown(f'<p style="color:#22d3ee;font-weight:600;margin-top:8px;">{a[1]}</p>', unsafe_allow_html=True)
                        for m in matches[:5]:
                            s = max(0, m.start() - 80)
                            e = min(len(txt), m.end() + 80)
                            trecho = txt[s:e]
                            dest = re.sub(re.escape(termo), f'<span style="background:#fbbf24;color:#000;padding:2px 4px;border-radius:3px;font-weight:700;">{termo}</span>', trecho, flags=re.IGNORECASE)
                            st.markdown(f'<div style="background:rgba(15,23,42,0.5);border-radius:6px;padding:10px;margin-bottom:6px;color:#cbd5e1;font-size:13px;font-family:monospace;line-height:1.5;">...{dest}...</div>', unsafe_allow_html=True)
                if not achou: st.markdown(f'<p style="color:#94a3b8;">Nenhuma ocorrencia de "{termo}".</p>', unsafe_allow_html=True)
        else: st.markdown('<p style="color:#64748b;">Nenhum documento anexado.</p>', unsafe_allow_html=True)
        conn.close()

def programas_saude():
    st.markdown('<h1 style="color:#e0f2fe;font-size:38px;">PROGRAMAS DE SAUDE</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#94a3b8;margin-bottom:20px;">Clique em cada bloco para expandir, anexar documentos e pesquisar.</p>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(34,211,238,0.3);">', unsafe_allow_html=True)
    
    t1, t2, t3, t4, t5 = st.tabs(["MEDICAMENTOS", "GESTAO", "FINANCIAMENTO", "REGULACAO", "CONSORCIOS"])
    
    with t1:
        bloco_saude("Relacao Nacional de Medicamentos Essenciais", "RENAME",
            'A <strong>RENAME</strong> (Relacao Nacional de Medicamentos Essenciais) e a lista oficial do Ministerio da Saude que define quais medicamentos e insumos sao oferecidos gratuitamente pelo SUS. Ela serve para orientar o tratamento, garantir o acesso da populacao e organizar o financiamento entre Uniao, estados e municipios.<br><br>'
            'Alem de servir de guia para medicos e pacientes, a RENAME e a base utilizada pelo SUS para compras publicas, incentivando o uso racional de remedios padronizados para as doencas mais recorrentes no pais.',
            "https://www.gov.br/saude/pt-br/assuntos/assistencia-farmaceutica-no-sus/rename", "#0e7490")
        
        bloco_saude("Relacao Municipal de Medicamentos Essenciais", "REMUME",
            'A <strong>REMUME</strong> (Relacao Municipal de Medicamentos Essenciais) e a lista oficial de medicamentos disponibilizados gratuitamente pelo SUS na rede publica de cada municipio.<br><br>'
            '<strong>Componentes:</strong><br>'
            'Componente Basico: Medicamentos para atencao primaria (postos de saude).<br>'
            'Componente Estrategico: Farmacos para doencas de controle prioritario.<br>'
            'Componente Especializado: Medicamentos de alto custo.',
            "https://bvsms.saude.gov.br/bvs/publicacoes/rename_2022.pdf", "#0891b2")
        
        bloco_saude("Relacao Nacional de Equipamentos e Materiais Permanentes", "RENEM",
            'A <strong>RENEM</strong> padroniza e determina quais equipamentos e materiais medico-hospitalares podem ser financiados pelo SUS.<br><br>'
            '<strong>Caracteristicas:</strong><br>'
            'Inclui desde itens simples (macas) ate equipamentos de alta complexidade.<br>'
            'Estabelece valores base que orientam o repasse de verbas federais.<br>'
            'Atualizacao periodica em parceria com o PROCOT.',
            "https://portalfns.saude.gov.br/", "#155e75")
        
        bloco_saude("Relacao Nacional de Acoes e Servicos de Saude", "RENASES",
            'A <strong>RENASES</strong> garante o direito a integralidade da assistencia, assegurando que o paciente tenha acesso a todo o ciclo de cuidado.<br><br>'
            '<strong>O que compoe:</strong><br>'
            'Atencao Primaria: Postos de saude, consultas basicas, vacinacao.<br>'
            'Urgencia e Emergencia: UPAs e pronto-socorros.<br>'
            'Atencao Especializada: Consultas com especialistas, exames, internacoes.<br>'
            'Atencao Psicossocial: CAPS.<br>'
            'Vigilancia em Saude: Controle de epidemias e saneamento.',
            "https://www.gov.br/saude/pt-br/acesso-a-informacao/acoes-e-programas/renases", "#164e63")
    
    with t2:
        bloco_saude("Plataforma de Gestao da Atencao Primaria a Saude", "E-GESTOR APS",
            'O <strong>e-Gestor APS</strong> e a plataforma oficial do Governo Federal/Ministerio da Saude voltada para o SUS.<br><br>'
            '<strong>O que faz:</strong> Centraliza os acessos a sistemas da Atencao Basica, como cobertura, equipes de saude da familia, Mais Medicos e dados de financiamento.',
            "https://egestorab.saude.gov.br/", "#0369a1")
        
        bloco_saude("Nova Plataforma de Regulacao de Leitos - SES/MG", "CORE SAUDE MG",
            'O <strong>Core Saude MG</strong> e a nova plataforma digital da SES-MG que substituiu o SUSfacil para gerenciar a fila unica de leitos, cirurgias, consultas e exames.<br><br>'
            '<strong>Objetivos:</strong><br>'
            'Fila unica e criterios tecnicos estaduais.<br>'
            'Decisoes baseadas em dados com monitoramento em tempo real.<br>'
            'Regulacao 4.0 padronizando fluxos assistenciais em MG.',
            "https://www.saude.mg.gov.br/", "#075985")
    
    with t3:
        bloco_saude("Fundo Nacional de Saude - Gestor Financeiro do SUS", "FNS",
            'O <strong>FNS</strong> e o gestor financeiro dos recursos do Ministerio da Saude na esfera federal.<br><br>'
            '<strong>Custeio:</strong> Manutencao de hospitais, postos, compra de medicamentos, pagamento de profissionais.<br>'
            '<strong>Investimentos:</strong> Construcao de unidades de saude, reformas, compra de equipamentos.<br><br>'
            '<strong>Repasses:</strong> Fundo a Fundo (automatico) e Convenios (projetos especificos).',
            "https://portalfns.saude.gov.br/", "#1d4ed8")
        
        bloco_saude("Sistema de Gerenciamento da Tabela de Procedimentos", "SIGTAP",
            'O <strong>SIGTAP</strong> e a tabela oficial que padroniza procedimentos, medicamentos e OPM do SUS.<br><br>'
            'Codigos e valores de cada exame, cirurgia ou consulta.<br>'
            'Regras de compatibilidade entre procedimentos.<br>'
            'Instrumentos de registro (AIH, BPA).<br>'
            'Niveis: Atencao Basica, Media e Alta Complexidade.',
            "http://sigtap.datasus.gov.br/tabela-unificada/app/sec/inicio.jsp", "#1e3a8a")
        
        bloco_saude("Programacao Pactuada e Integrada", "PPI",
            'A <strong>PPI</strong> e o instrumento que organiza a rede de servicos do SUS, definindo o fluxo de pacientes entre municipios.<br><br>'
            'A consolidacao da PPI unifica metas fisicas e orcamentarias (exames, consultas) para controle e distribuicao centralizada dos recursos financeiros.',
            "http://datasus.saude.gov.br/informacoes-de-saude/tabnet", "#1e40af")
    
    with t4:
        bloco_saude("Conselho Nacional de Secretarias Municipais de Saude", "CONASEMS",
            'O <strong>CONASEMS</strong> representa as Secretarias Municipais de Saude de todo o Brasil.<br><br>'
            '<strong>Funcoes:</strong> Representa os municipios na Comissao Intergestora Tripartite, oferece suporte tecnico e promove capacitacao.<br><br>'
            '<strong>Diferenca:</strong> CONASEMS (nacional) / COSEMS (estadual) / CONASS (estados)',
            "https://conasems.org.br/", "#4338ca")
        
        bloco_saude("Conselho de Secretarias Municipais de Saude de MG", "COSEMS MG",
            'O <strong>COSEMS MG</strong> representa os 853 municipios mineiros. Atua como elo entre Secretarios de Saude e as esferas estadual/federal.<br><br>'
            '<strong>Funcoes:</strong> Representacao politica, participacao na CIB, apoio tecnico e capacitacao para gestores das 28 regionais de saude.',
            "https://www.cosemsmg.org.br/", "#3730a3")
    
    with t5:
        bloco_saude("Consorcio Intermunicipal de Saude da Microrregiao de Lavras", "CISLAV",
            'O <strong>CISLAV</strong> une prefeituras da regiao para otimizar recursos e melhorar o atendimento pelo SUS.<br><br>'
            'Compartilhamento de custos de consultas, exames e transporte (Transporta SUS).<br>'
            'Fortalecimento da vigilancia sanitaria regional.<br>'
            'Aquisicao conjunta de medicamentos e insumos.',
            "https://www.cislav.com/", "#312e81")

def main():
    if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
    if "page" not in st.session_state: st.session_state["page"] = "Dashboard"
    if not st.session_state["logged_in"]: login_page()
    else:
        st.sidebar.markdown('<h3 style="color:#22d3ee;text-align:center;letter-spacing:2px;">MENU PRINCIPAL</h3>', unsafe_allow_html=True)
        st.sidebar.markdown('<hr>', unsafe_allow_html=True)
        st.sidebar.markdown('<p style="color:#7dd3fc;font-size:12px;letter-spacing:1px;margin-bottom:5px;">GESTAO FINANCEIRA</p>', unsafe_allow_html=True)
        if st.sidebar.button("INICIO", key="nav_inicio", use_container_width=True): st.session_state["page"] = "Dashboard"; st.rerun()
        if st.sidebar.button("CADASTRAR CONTAS", key="nav_cadastrar", use_container_width=True): st.session_state["page"] = "CADASTRAR CONTAS"; st.rerun()
        if st.sidebar.button("CONTAS CADASTRADAS", key="nav_cadastradas", use_container_width=True): st.session_state["page"] = "CONTAS CADASTRADAS"; st.rerun()
        if st.sidebar.button("REALIZAR COMPRAS", key="nav_compras", use_container_width=True): st.session_state["page"] = "REALIZAR COMPRAS"; st.rerun()
        st.sidebar.markdown('<hr>', unsafe_allow_html=True)
        st.sidebar.markdown('<p style="color:#7dd3fc;font-size:12px;letter-spacing:1px;margin-bottom:5px;">SAUDE PUBLICA</p>', unsafe_allow_html=True)
        if st.sidebar.button("PROGRAMAS DE SAUDE", key="nav_saude", use_container_width=True): st.session_state["page"] = "PROGRAMAS SAUDE"; st.rerun()
        st.sidebar.markdown('<hr>', unsafe_allow_html=True)
        if st.sidebar.button("Sair", key="logout", use_container_width=True):
            st.session_state["logged_in"] = False; st.session_state.pop("username", None); st.rerun()
        page = st.session_state["page"]
        if page == "Dashboard": dashboard()
        elif page == "CADASTRAR CONTAS": cadastrar_contas()
        elif page == "CONTAS CADASTRADAS": contas_cadastradas()
        elif page == "EDITAR CONTA": pass
        elif page == "REALIZAR COMPRAS": pass
        elif page == "EDITAR ORDEM COMPRA": pass
        elif page == "ESFERA DETALHE": esfera_detalhe()
        elif page == "PROGRAMAS SAUDE": programas_saude()

if __name__ == "__main__":
    main()
