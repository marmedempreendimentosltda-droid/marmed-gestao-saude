import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, date

st.set_page_config(page_title="MARMED", layout="wide", initial_sidebar_state="expanded")

# 
# BANCO DE DADOS
# 
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
    
    c.execute('''CREATE TABLE IF NOT EXISTS contas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  esfera TEXT,
                  tipo TEXT,
                  fonte TEXT,
                  valor REAL,
                  descricao TEXT,
                  data DATE,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS compras
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  esfera TEXT,
                  descricao TEXT,
                  valor REAL,
                  data DATE,
                  status TEXT DEFAULT 'pendente',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS superavit
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  esfera TEXT,
                  valor REAL,
                  data DATE,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS programas_saude
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  nome TEXT,
                  descricao TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS uploads
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  usuario_id INTEGER,
                  categoria TEXT,
                  nome_arquivo TEXT,
                  conteudo TEXT,
                  data DATE,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(usuario_id) REFERENCES usuarios(id))''')
    
    # Criar usuario admin padrao
    senha_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    try:
        c.execute("INSERT OR IGNORE INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                  ("Administrador", "admin", senha_hash, "admin"))
    except:
        pass
    
    conn.commit()
    conn.close()

def verificar_login(email, senha):
    conn = sqlite3.connect('marmed.db')
    c = conn.cursor()
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    c.execute("SELECT * FROM usuarios WHERE email = ? AND senha = ?", (email, senha_hash))
    usuario = c.fetchone()
    conn.close()
    return usuario

def format_currency(valor):
    if valor is None:
        return "R$ 0,00"
    v = float(valor)
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

def parse_br_currency(val):
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    v = str(val).replace('R$ ', '').replace('R$', '').replace('.', '').replace(',', '.')
    try:
        return float(v)
    except:
        return 0.0

init_db()

# 
# SESSION STATE
# 
if 'usuario_id' not in st.session_state:
    st.session_state.usuario_id = None
if 'usuario_nome' not in st.session_state:
    st.session_state.usuario_nome = None
if 'usuario_tipo' not in st.session_state:
    st.session_state.usuario_tipo = None
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'login'
