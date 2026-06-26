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

def menor_que(a, b):
    return a < b

def menor_ou_igual(a, b):
    return a <= b

def maior_que(a, b):
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
        }
        aplicarMascaras();
        setInterval(aplicarMascaras, 2000);
    })();
    </script>
    """, unsafe_allow_html=True)

def init_db():
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nome TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  senha TEXT NOT NULL,
                  tipo TEXT DEFAULT 'usuario',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS empenhos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  orgao TEXT,
                  esfera TEXT,
                  fonte TEXT,
                  programa TEXT,
                  acao TEXT,
                  natureza_despesa TEXT,
                  modalidade TEXT,
                  valor_total REAL,
                  valor_empenhado REAL,
                  valor_liquidado REAL,
                  valor_pago REAL,
                  data_empenho DATE,
                  data_liquidacao DATE,
                  data_pagamento DATE,
                  credor TEXT,
                  cpf_cnpj TEXT,
                  processo TEXT,
                  status TEXT DEFAULT 'ativo',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS contratos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  orgao TEXT,
                  esfera TEXT,
                  numero TEXT,
                  objeto TEXT,
                  credor TEXT,
                  cpf_cnpj TEXT,
                  valor_global REAL,
                  valor_empenhado REAL,
                  valor_liquidado REAL,
                  valor_pago REAL,
                  data_inicio DATE,
                  data_fim DATE,
                  prazo_meses INTEGER,
                  fiscal TEXT,
                  modalidade TEXT,
                  status TEXT DEFAULT 'ativo',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS prestacao_contas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  orgao TEXT,
                  esfera TEXT,
                  ano INTEGER,
                  tipo TEXT,
                  status TEXT DEFAULT 'pendente',
                  data_entrega DATE,
                  observacoes TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS obras
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  orgao TEXT,
                  esfera TEXT,
                  numero_contrato TEXT,
                  objeto TEXT,
                  empresa TEXT,
                  cnpj TEXT,
                  valor_contrato REAL,
                  valor_empenhado REAL,
                  valor_liquidado REAL,
                  valor_pago REAL,
                  data_inicio DATE,
                  data_fim DATE,
                  prazo_meses INTEGER,
                  fiscal TEXT,
                  status TEXT DEFAULT 'ativo',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS almoxarifado
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  orgao TEXT,
                  esfera TEXT,
                  item TEXT,
                  descricao TEXT,
                  quantidade INTEGER,
                  unidade TEXT,
                  valor_unitario REAL,
                  valor_total REAL,
                  categoria TEXT,
                  localizacao TEXT,
                  data_aquisicao DATE,
                  status TEXT DEFAULT 'ativo',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS frota
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  orgao TEXT,
                  esfera TEXT,
                  veiculo TEXT,
                  placa TEXT,
                  marca TEXT,
                  modelo TEXT,
                  ano INTEGER,
                  combustivel TEXT,
                  km_atual INTEGER,
                  valor_aquisicao REAL,
                  data_aquisicao DATE,
                  status TEXT DEFAULT 'ativo',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS rh
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  orgao TEXT,
                  esfera TEXT,
                  servidor TEXT,
                  cpf TEXT,
                  cargo TEXT,
                  lotacao TEXT,
                  tipo_vinculo TEXT,
                  data_admissao DATE,
                  data_demissao DATE,
                  salario_base REAL,
                  status TEXT DEFAULT 'ativo',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS diarias
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  orgao TEXT,
                  esfera TEXT,
                  servidor TEXT,
                  cpf TEXT,
                  destino TEXT,
                  data_inicio DATE,
                  data_fim DATE,
                  diarias INTEGER,
                  valor_unitario REAL,
                  valor_total REAL,
                  objeto TEXT,
                  status TEXT DEFAULT 'ativo',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS licitacoes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  orgao TEXT,
                  esfera TEXT,
                  modalidade TEXT,
                  numero TEXT,
                  objeto TEXT,
                  data_abertura DATE,
                  data_homologacao DATE,
                  valor_estimado REAL,
                  valor_homologado REAL,
                  vencedor TEXT,
                  cnpj_vencedor TEXT,
                  status TEXT DEFAULT 'ativo',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS convenios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  orgao TEXT,
                  esfera TEXT,
                  numero TEXT,
                  concedente TEXT,
                  objeto TEXT,
                  valor_global REAL,
                  valor_repasse REAL,
                  valor_contrapartida REAL,
                  valor_empenhado REAL,
                  valor_liquidado REAL,
                  valor_pago REAL,
                  data_assinatura DATE,
                  data_inicio DATE,
                  data_fim DATE,
                  situacao TEXT,
                  status TEXT DEFAULT 'ativo',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    conn.commit()
    conn.close()

def criar_usuario(nome, email, senha):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    try:
        c.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                  (nome, email, senha_hash))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def verificar_login(email, senha):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    c.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha_hash))
    usuario = c.fetchone()
    conn.close()
    return usuario

def get_orgaos(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT orgao FROM empenhos WHERE usuario_id = ? AND orgao IS NOT NULL", (usuario_id,))
    orgaos = [row[0] for row in c.fetchall()]
    conn.close()
    return orgaos

def get_esferas(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT esfera FROM empenhos WHERE usuario_id = ? AND esfera IS NOT NULL", (usuario_id,))
    esferas = [row[0] for row in c.fetchall()]
    conn.close()
    return esferas

def get_fontes(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT fonte FROM empenhos WHERE usuario_id = ? AND fonte IS NOT NULL", (usuario_id,))
    fontes = [row[0] for row in c.fetchall()]
    conn.close()
    return fontes

def get_programas(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT programa FROM empenhos WHERE usuario_id = ? AND programa IS NOT NULL", (usuario_id,))
    programas = [row[0] for row in c.fetchall()]
    conn.close()
    return programas

def get_credores(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT credor FROM empenhos WHERE usuario_id = ? AND credor IS NOT NULL", (usuario_id,))
    credores = [row[0] for row in c.fetchall()]
    conn.close()
    return credores

def get_contratos_credores(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT credor FROM contratos WHERE usuario_id = ? AND credor IS NOT NULL", (usuario_id,))
    credores = [row[0] for row in c.fetchall()]
    conn.close()
    return credores

def get_obras_empresas(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT empresa FROM obras WHERE usuario_id = ? AND empresa IS NOT NULL", (usuario_id,))
    empresas = [row[0] for row in c.fetchall()]
    conn.close()
    return empresas

def get_almoxarifado_itens(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT item FROM almoxarifado WHERE usuario_id = ? AND item IS NOT NULL", (usuario_id,))
    itens = [row[0] for row in c.fetchall()]
    conn.close()
    return itens

def get_frota_veiculos(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT veiculo FROM frota WHERE usuario_id = ? AND veiculo IS NOT NULL", (usuario_id,))
    veiculos = [row[0] for row in c.fetchall()]
    conn.close()
    return veiculos

def get_rh_servidores(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT servidor FROM rh WHERE usuario_id = ? AND servidor IS NOT NULL", (usuario_id,))
    servidores = [row[0] for row in c.fetchall()]
    conn.close()
    return servidores

def get_diarias_servidores(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT servidor FROM diarias WHERE usuario_id = ? AND servidor IS NOT NULL", (usuario_id,))
    servidores = [row[0] for row in c.fetchall()]
    conn.close()
    return servidores

def get_licitacoes_vencedores(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT vencedor FROM licitacoes WHERE usuario_id = ? AND vencedor IS NOT NULL", (usuario_id,))
    vencedores = [row[0] for row in c.fetchall()]
    conn.close()
    return vencedores

def get_convenios_concedentes(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT concedente FROM convenios WHERE usuario_id = ? AND concedente IS NOT NULL", (usuario_id,))
    concedentes = [row[0] for row in c.fetchall()]
    conn.close()
    return concedentes

def get_orgaos_contratos(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT orgao FROM contratos WHERE usuario_id = ? AND orgao IS NOT NULL", (usuario_id,))
    orgaos = [row[0] for row in c.fetchall()]
    conn.close()
    return orgaos

def get_orgaos_obras(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT orgao FROM obras WHERE usuario_id = ? AND orgao IS NOT NULL", (usuario_id,))
    orgaos = [row[0] for row in c.fetchall()]
    conn.close()
    return orgaos

def get_orgaos_almoxarifado(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT orgao FROM almoxarifado WHERE usuario_id = ? AND orgao IS NOT NULL", (usuario_id,))
    orgaos = [row[0] for row in c.fetchall()]
    conn.close()
    return orgaos

def get_orgaos_frota(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT orgao FROM frota WHERE usuario_id = ? AND orgao IS NOT NULL", (usuario_id,))
    orgaos = [row[0] for row in c.fetchall()]
    conn.close()
    return orgaos

def get_orgaos_rh(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT orgao FROM rh WHERE usuario_id = ? AND orgao IS NOT NULL", (usuario_id,))
    orgaos = [row[0] for row in c.fetchall()]
    conn.close()
    return orgaos

def get_orgaos_diarias(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT orgao FROM diarias WHERE usuario_id = ? AND orgao IS NOT NULL", (usuario_id,))
    orgaos = [row[0] for row in c.fetchall()]
    conn.close()
    return orgaos

def get_orgaos_licitacoes(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT orgao FROM licitacoes WHERE usuario_id = ? AND orgao IS NOT NULL", (usuario_id,))
    orgaos = [row[0] for row in c.fetchall()]
    conn.close()
    return orgaos

def get_orgaos_convenios(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT orgao FROM convenios WHERE usuario_id = ? AND orgao IS NOT NULL", (usuario_id,))
    orgaos = [row[0] for row in c.fetchall()]
    conn.close()
    return orgaos

def get_esferas_contratos(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT esfera FROM contratos WHERE usuario_id = ? AND esfera IS NOT NULL", (usuario_id,))
    esferas = [row[0] for row in c.fetchall()]
    conn.close()
    return esferas

def get_esferas_obras(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT esfera FROM obras WHERE usuario_id = ? AND esfera IS NOT NULL", (usuario_id,))
    esferas = [row[0] for row in c.fetchall()]
    conn.close()
    return esferas

def get_esferas_almoxarifado(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT esfera FROM almoxarifado WHERE usuario_id = ? AND esfera IS NOT NULL", (usuario_id,))
    esferas = [row[0] for row in c.fetchall()]
    conn.close()
    return esferas

def get_esferas_frota(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT esfera FROM frota WHERE usuario_id = ? AND esfera IS NOT NULL", (usuario_id,))
    esferas = [row[0] for row in c.fetchall()]
    conn.close()
    return esferas

def get_esferas_rh(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT esfera FROM rh WHERE usuario_id = ? AND esfera IS NOT NULL", (usuario_id,))
    esferas = [row[0] for row in c.fetchall()]
    conn.close()
    return esferas

def get_esferas_diarias(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT esfera FROM diarias WHERE usuario_id = ? AND esfera IS NOT NULL", (usuario_id,))
    esferas = [row[0] for row in c.fetchall()]
    conn.close()
    return esferas

def get_esferas_licitacoes(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT esfera FROM licitacoes WHERE usuario_id = ? AND esfera IS NOT NULL", (usuario_id,))
    esferas = [row[0] for row in c.fetchall()]
    conn.close()
    return esferas

def get_esferas_convenios(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT esfera FROM convenios WHERE usuario_id = ? AND esfera IS NOT NULL", (usuario_id,))
    esferas = [row[0] for row in c.fetchall()]
    conn.close()
    return esferas

def get_modalidades(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT modalidade FROM empenhos WHERE usuario_id = ? AND modalidade IS NOT NULL", (usuario_id,))
    modalidades = [row[0] for row in c.fetchall()]
    conn.close()
    return modalidades

def get_modalidades_contratos(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT modalidade FROM contratos WHERE usuario_id = ? AND modalidade IS NOT NULL", (usuario_id,))
    modalidades = [row[0] for row in c.fetchall()]
    conn.close()
    return modalidades

def get_modalidades_licitacoes(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT modalidade FROM licitacoes WHERE usuario_id = ? AND modalidade IS NOT NULL", (usuario_id,))
    modalidades = [row[0] for row in c.fetchall()]
    conn.close()
    return modalidades

def get_naturezas(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT natureza_despesa FROM empenhos WHERE usuario_id = ? AND natureza_despesa IS NOT NULL", (usuario_id,))
    naturezas = [row[0] for row in c.fetchall()]
    conn.close()
    return naturezas

def get_acoes(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT acao FROM empenhos WHERE usuario_id = ? AND acao IS NOT NULL", (usuario_id,))
    acoes = [row[0] for row in c.fetchall()]
    conn.close()
    return acoes

def get_categorias_almoxarifado(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT categoria FROM almoxarifado WHERE usuario_id = ? AND categoria IS NOT NULL", (usuario_id,))
    categorias = [row[0] for row in c.fetchall()]
    conn.close()
    return categorias

def get_localizacoes_almoxarifado(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT localizacao FROM almoxarifado WHERE usuario_id = ? AND localizacao IS NOT NULL", (usuario_id,))
    localizacoes = [row[0] for row in c.fetchall()]
    conn.close()
    return localizacoes

def get_cargos_rh(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT cargo FROM rh WHERE usuario_id = ? AND cargo IS NOT NULL", (usuario_id,))
    cargos = [row[0] for row in c.fetchall()]
    conn.close()
    return cargos

def get_lotacoes_rh(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT lotacao FROM rh WHERE usuario_id = ? AND lotacao IS NOT NULL", (usuario_id,))
    lotacoes = [row[0] for row in c.fetchall()]
    conn.close()
    return lotacoes

def get_vinculos_rh(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT tipo_vinculo FROM rh WHERE usuario_id = ? AND tipo_vinculo IS NOT NULL", (usuario_id,))
    vinculos = [row[0] for row in c.fetchall()]
    conn.close()
    return vinculos

def get_situacoes_convenios(usuario_id):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT situacao FROM convenios WHERE usuario_id = ? AND situacao IS NOT NULL", (usuario_id,))
    situacoes = [row[0] for row in c.fetchall()]
    conn.close()
    return situacoes

init_db()

if 'usuario_id' not in st.session_state:
    st.session_state.usuario_id = None
if 'usuario_nome' not in st.session_state:
    st.session_state.usuario_nome = None
if 'usuario_tipo' not in st.session_state:
    st.session_state.usuario_tipo = None
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'login'

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .login-container {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        max-width: 400px;
        margin: 100px auto;
    }
    .login-title {
        text-align: center;
        color: #667eea;
        font-size: 2rem;
        margin-bottom: 1.5rem;
    }
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        font-weight: bold;
        width: 100%;
    }
    .stButton button:hover {
        opacity: 0.9;
    }
    .success-msg {
        color: #28a745;
        text-align: center;
        padding: 0.5rem;
    }
    .error-msg {
        color: #dc3545;
        text-align: center;
        padding: 0.5rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #667eea;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
    }
    .section-title {
        color: #667eea;
        font-size: 1.3rem;
        font-weight: bold;
        margin: 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #667eea;
    }
    .status-ativo {
        color: #28a745;
        font-weight: bold;
    }
    .status-pendente {
        color: #ffc107;
        font-weight: bold;
    }
    .status-concluido {
        color: #17a2b8;
        font-weight: bold;
    }
    .status-inativo {
        color: #dc3545;
        font-weight: bold;
    }
    .info-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .info-label {
        font-weight: bold;
        color: #495057;
    }
    .info-value {
        color: #212529;
    }
</style>
""", unsafe_allow_html=True)

if st.session_state.pagina == 'login':
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">MARMED</div>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center;color:#666;">Sistema de Gestao Publica</p>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Entrar", "Cadastrar"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                senha = st.text_input("Senha", type="password")
                submit = st.form_submit_button("Entrar")
                if submit:
                    usuario = verificar_login(email, senha)
                    if usuario:
                        st.session_state.usuario_id = usuario[0]
                        st.session_state.usuario_nome = usuario[1]
                        st.session_state.usuario_tipo = usuario[4]
                        st.session_state.pagina = 'dashboard'
                        st.rerun()
                    else:
                        st.error("Email ou senha incorretos!")

        with tab2:
            with st.form("cadastro_form"):
                nome = st.text_input("Nome completo")
                email = st.text_input("Email")
                senha = st.text_input("Senha", 
