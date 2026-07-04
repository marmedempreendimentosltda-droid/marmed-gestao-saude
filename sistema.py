import streamlit as st
import sqlite3
import hashlib
import re
from datetime import datetime

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
    v = str(val).replace('R$ 
