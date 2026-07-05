import streamlit as st
import sqlite3
import hashlib
import re
import base64
from datetime import datetime

def get_logo_base64():
    try:
        with open("logo.png", "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode("utf-8")
    except Exception:
        return None

LOGO_BASE64 = get_logo_base64()

st.set_page_config(page_title="MARMED - Gestao de Saude", page_icon="🏥", layout="wide", initial_sidebar_state="expanded")

DB_NAME = "marmed.db"

def get_conn():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    schema = {
        "users": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("username", "TEXT UNIQUE"),
            ("password_hash", "TEXT"),
            ("nome", "TEXT"),
        ],
        "contas_receber": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("esfera", "TEXT"),
            ("numero_conta", "TEXT"),
            ("fonte", "TEXT"),
            ("referencia_tipo", "TEXT"),
            ("referencia_numero", "TEXT"),
            ("tipo_recurso", "TEXT"),
            ("valor_pago_custeio", "REAL DEFAULT 0"),
            ("valor_pago_investimento", "REAL DEFAULT 0"),
            ("valor_total", "REAL DEFAULT 0"),
            ("data_recebimento", "TEXT"),
            ("programa_politica", "TEXT"),
            ("setor_gasto", "TEXT"),
        ],
        "superavit": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("esfera", "TEXT"),
            ("fonte_original", "TEXT"),
            ("fonte_superavit", "TEXT"),
            ("saldo_total", "REAL DEFAULT 0"),
            ("saldo_restante", "REAL DEFAULT 0"),
            ("created_at", "TEXT"),
        ],
        "ordens_compra": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("conta_receber_id", "INTEGER"),
            ("esfera", "TEXT"),
            ("numero_conta", "TEXT"),
            ("fonte", "TEXT"),
            ("ficha", "TEXT"),
            ("tipo_despesa", "TEXT"),
            ("data_compra", "TEXT"),
            ("valor_compra", "REAL DEFAULT 0"),
            ("produto_servico", "TEXT"),
            ("created_at", "TEXT"),
        ],
        "arquivos_saude": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("bloco", "TEXT"),
            ("nome_arquivo", "TEXT"),
            ("conteudo_texto", "TEXT"),
            ("dados_arquivo", "BLOB"),
            ("data_upload", "TEXT"),
        ],
        "programas_saude": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("nome", "TEXT"),
            ("descricao", "TEXT"),
            ("created_at", "TEXT"),
        ],
        "conselho": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("nome", "TEXT"),
            ("segmento", "TEXT"),
            ("cargo", "TEXT"),
            ("email", "TEXT"),
            ("telefone", "TEXT"),
            ("data_posse", "TEXT"),
        ],
    }

    for tabela, colunas in schema.items():
        colunas_sql = ", ".join(f"{nome} {definicao}" for nome, definicao in colunas)
        cur.execute(f"CREATE TABLE IF NOT EXISTS {tabela} ({colunas_sql})")

    for tabela, colunas in schema.items():
        existentes = {row[1] for row in cur.execute(f"PRAGMA table_info({tabela})").fetchall()}
        for nome_coluna, definicao in colunas:
            if nome_coluna in existentes:
                continue
            if "PRIMARY KEY" in definicao.upper():
                continue
            try:
                cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {nome_coluna} {definicao}")
            except sqlite3.OperationalError:
                pass

    admin_hash = hashlib.sha256("Diretor2025#".encode("utf-8")).hexdigest()
    try:
        cur.execute("INSERT OR IGNORE INTO users (username, password_hash, nome) VALUES (?, ?, ?)", ("admin", admin_hash, "Administrador"))
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

init_db()

def format_currency(valor):
    if valor is None:
        valor = 0.0
    v = float(valor)
    texto = f"{v:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"

def parse_valor(texto):
    if texto is None:
        return 0.0
    if isinstance(texto, (int, float)):
        return float(texto)
    limpo = str(texto).replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(limpo)
    except ValueError:
        return 0.0

def get_fonte(esfera):
    mapa = {"Federal": "1.600", "Estadual": "1.621", "Municipal": "1.500", "Transferencia": "1.700", "Transposicao": "1.800"}
    return mapa.get(esfera, "")

def get_fonte_superavit(esfera):
    mapa = {"Federal": "2.600", "Estadual": "2.621"}
    return mapa.get(esfera)

def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def verificar_login(usuario, senha):
    conn = get_conn()
    row = conn.execute("SELECT id, username, nome FROM users WHERE username=? AND password_hash=?", (usuario, hash_senha(senha))).fetchone()
    conn.close()
    return row

def extrair_texto(dados_bytes, nome_arquivo):
 
