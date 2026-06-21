import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import datetime
from time import sleep

# ------------------ DATABASE ------------------
DB = 'marmed.db'

def get_conn():
    return sqlite3.connect(DB)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS contas_pagar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fornecedor TEXT,
        descricao TEXT,
        valor REAL,
        vencimento TEXT,
        status TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS contas_receber (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        devedor TEXT,
        descricao TEXT,
        valor REAL,
        vencimento TEXT,
        status TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS empenhos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        objeto TEXT,
        valor REAL,
        data TEXT,
        status TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS licitacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        objeto TEXT,
        modalidade TEXT,
        valor REAL,
        data TEXT,
        status TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS contratos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        contratado TEXT,
        objeto TEXT,
        valor REAL,
        inicio TEXT,
        fim TEXT,
        status TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS metricas (
        id INTEGER PRIMARY KEY,
        repasse_federal REAL,
        repasse_estadual REAL,
        recurso_municipal REAL,
        transferencia REAL,
        transposicao REAL
    )''')

    default_hash = hashlib.sha256('Diretor2025#'.encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('admin', ?)", (default_hash,))

    c.execute("INSERT OR IGNORE INTO metricas (id, repasse_federal, repasse_estadual, recurso_municipal, transferencia, transposicao) VALUES (1, 0, 0, 0, 0, 0)")

    conn.commit()
    conn.close()

init_db()

# ------------------ UTILS ------------------
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def format_currency(val):
    if val is None:
        val = 0.0
    return f'R$ {val:,.2f}'.replace(',', 'v').replace('.', ',').replace('v', '.')

def authenticated():
    return st.session_state.get('authenticated', False)

# ------------------ LOGIN PAGE ------------------
def login_page():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
        .main { background: #050b14; }
        .stApp {
            background: radial-gradient(circle at 50% 50%, #0a1f3d 0%, #02050a 100%);
        }
        .particle {
            position: fixed;
            width: 6px;
            height: 6px;
            background: rgba(0, 212, 255, 0.6);
            border-radius: 50%;
            animation: float 15s infinite linear;
            box-shadow: 0 0 10px rgba(0, 212, 255, 0.8);
        }
        @keyframes float {
            0% { transform: translateY(110vh) translateX(0); opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { transform: translateY(-10vh) translateX(100px); opacity: 0; }
        }
        .login-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 24px;
            padding: 50px 40px;
            max-width: 480px;
            margin: auto;
            box-shadow: 0 0 60px rgba(0, 212, 255, 0.15), inset 0 0 30px rgba(0, 212, 255, 0.05);
            margin-top: 5vh;
        }
        .title-3d {
            font-family: 'Orbitron', sans-serif;
            font-size: 80px;
            font-weight: 900;
            text-align: center;
            color: #00d4ff;
            text-shadow: 0 0 20px rgba(0, 212, 255, 0.8), 0 0 40px rgba(0, 212, 255, 0.5), 4px 4px 0px #003d4d, 8px 8px 0px #001a21;
            letter-spacing: 12px;
            animation: flyIn 1.8s ease-out forwards;
            margin-bottom: 10px;
        }
        .letter {
            display: inline-block;
            opacity: 0;
            transform: translateZ(-1000px) translateY(-200px) rotateX(90deg);
            animation: letterFly 0.8s ease-out forwards;
        }
        .letter:nth-child(1) { animation-delay: 0s; }
        .letter:nth-child(2) { animation-delay: 0.15s; }
        .letter:nth-child(3) { animation-delay: 0.3s; }
        .letter:nth-child(4) { animation-delay: 0.45s; }
        .letter:nth-child(5) { animation-delay: 0.6s; }
        .letter:nth-child(6) { animation-delay: 0.75s; }
        @keyframes letterFly {
            0% { opacity: 0; transform: translateZ(-1000px) translateY(-200px) rotateX(90deg); }
            60% { opacity: 1; transform: translateZ(100px) translateY(10px) rotateX(-10deg); }
            100% { opacity: 1; transform: translateZ(0) translateY(0) rotateX(0); }
        }
        .subtitle {
            font-family: 'Orbitron', sans-serif;
            font-size: 26px;
            text-align: center;
            color: #a0eaff;
            letter-spacing: 6px;
            margin-bottom: 40px;
            text-shadow: 0 0 15px rgba(0, 212, 255, 0.5);
        }
        .login-label {
            font-family: 'Orbitron', sans-serif;
            color: #00d4ff !important;
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 2px;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.6);
        }
        .acesso-text {
            text-align: center;
            color: #00d4ff;
            font-family: 'Orbitron', sans-serif;
            font-size: 14px;
            letter-spacing: 4px;
            margin-top: 25px;
            opacity: 0.8;
        }
        div.stButton > button:first-child {
            background: linear-gradient(45deg, #00d4ff, #0066cc);
            color: white;
            font-family: 'Orbitron', sans-serif;
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 3px;
            border: none;
            border-radius: 12px;
            padding: 14px 24px;
            width: 100%;
            box-shadow: 0 0 30px rgba(0, 212, 255, 0.4);
            transition: all 0.3s ease;
            margin-top: 10px;
        }
        div.stButton > button:first-child:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 50px rgba(0, 212, 255, 0.7);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    for i in range(25):
        left = (i * 4) % 100
        delay = (i * 0.7) % 15
        duration = 10 + (i % 10)
        st.markdown(f'<div class="particle" style="left:{left}%; animation-delay:-{delay}s; animation-duration:{duration}s;"></div>', unsafe_allow_html=True)

    st.markdown(
        '''
        <div class="login-card">
            <div class="title-3d">
                <span class="letter">M</span><span class="letter">A</span><span class="letter">R</span><span class="letter">M</span><span class="letter">E</span><span class="letter">D</span>
            </div>
            <div class="subtitle">SISTEMA INTEGRADO DE GESTAO</div>
        </div>
        ''',
        unsafe_allow_html=True
    )

    with st.container():
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            st.markdown('<p class="login-label">Usuario</p>', unsafe_allow_html=True)
            username = st.text_input('', key='login_user', label_visibility='collapsed')
            st.markdown('<p class="login-label">Senha</p>', unsafe_allow_html=True)
            password = st.text_input('', type='password', key='login_pass', label_visibility='collapsed')
            if st.button('ENTRAR', key='btn_login'):
                conn = get_conn()
                c = conn.cursor()
                c.execute('SELECT password FROM users WHERE username = ?', (username,))
                row = c.fetchone()
                conn.close()
                if row and row[0] == hash_password(password):
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = username
                    st.success('Login realizado com sucesso!')
                    sleep(0.5)
                    st.rerun()
                else:
                    st.error('Usuario ou senha invalidos!')
            st.markdown('<div class="acesso-text">Acesso</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ------------------ SIDEBAR ------------------
def sidebar_menu():
    st.sidebar.markdown('<h1 style="text-align:center; color:#00d4ff;">MARMED</h1>', unsafe_allow_html=True)
    st.sidebar.markdown('<hr style="border-color:#00d4ff;">', unsafe_allow_html=True)
    menu = st.sidebar.radio('Menu', [
        'Dashboard',
        'Contas a Pagar',
        'Contas a Receber',
        'Empenhos',
        'Licitacoes',
        'Contratos',
        'Trocar Senha'
    ], label_visibility='collapsed')
    st.sidebar.markdown('<hr style="border-color:#00d4ff;">', unsafe_allow_html=True)
    st.sidebar.markdown(f'<p style="color:#00d4ff; text-align:center;">Usuario: <b>{st.session_state.get("username", "")}</b></p>', unsafe_allow_html=True)
    if st.sidebar.button('Sair'):
        st.session_state['authenticated'] = False
        st.session_state.pop('username', None)
        st.rerun()
    return menu

# ------------------ DASHBOARD ------------------
def dashboard_page():
   st.markdown('<h1 style="color:#00d4ff; text-align:center;">Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<hr style="border-color:#00d4ff;">', unsafe_allow_html=True)

conn = get_conn()
c = conn.cursor()
c.execute('SELECT repasse_federal, repasse_estadual, recurso_municipal, transferencia, transposicao FROM metricas WHERE id = 1')
row = c.fetchone()
conn.close()

if row:
        labels = ['REPASSE FEDERAL', 'REPASSE ESTADUAL', 'RECURSO MUNICIPAL', 'TRANSFERENCIA', 'TRANSPOSICAO']
        values = list(row)
else:
        labels = ['REPASSE FEDERAL', 'REPASSE ESTADUAL', 'RECURSO MUNICIPAL', 'TRANSFERENCIA', 'TRANSPOSICAO']
        values = [0.0, 0.0, 0.0, 0.0, 0.0]

cols = st.columns(5)
for i, (label, val) in enumerate(zip(labels, values)):
        with cols[i]:
            st.markdown(
                f'<div style="background: rgba(0,212,255,0.08); border:1px solid #00d4ff; border-radius:16px; padding:20px; text-align:center; box-shadow:0 0 20px rgba(0,212,255,0.2);">'
                f'<p style="color:#a0eaff; font-size:12px; margin:0; letter-spacing:1px;">{label}</p>'
                f'<p style="color:#00d4ff; font-size:20px; font-weight:700; margin:10px 0 0 0;">{format_currency(val)}</p>'
                '</div>',
                unsafe_allow_html=True
            )

st.markdown('<br>', unsafe_allow_html=True)

with st.expander('Editar Metricas'):
        with st.form('form_metricas'):
            novo_federal = st.number_input('Repasse Federal', value=float(values[0]), step=0.01)
            novo_estadual = st.number_input('Repasse Estadual', value=float(values[1]), step=0.01)
            novo_municipal = st.number_input('Recurso Municipal', value=float(values[2]), step=0.01)
            novo_transferencia = st.number_input('Transferencia', value=float(values[3]), step=0.01)
            novo_transposicao = st.number_input('Transposicao', value=float(values[4]), step=0.01)
            if st.form_submit_button('Salvar Metricas'):
                conn = get_conn()
                c = conn.cursor()
                c.execute('''UPDATE metricas SET repasse_federal = ?, repasse_estadual = ?, recurso_municipal = ?, transferencia = ?, transposicao = ? WHERE id = 1''',
                          (novo_federal, novo_estadual, novo_municipal, novo_transferencia, novo_transposicao))
                conn.commit()
                conn.close()
                st.success('Metricas atualizadas!')
                st.rerun()

st.markdown('<br>', unsafe_allow_html=True)
st.markdown('<h3 style="color:#00d4ff;">Resumo Financeiro</h3>', unsafe_allow_html=True)

conn = get_conn()
df_pagar = pd.read_sql_query('SELECT COALESCE(SUM(valor),0) AS total FROM contas_pagar', conn)
df_receber = pd.read_sql_query('SELECT COALESCE(SUM(valor),0) AS total FROM contas_receber', conn)
df_empenhos = pd.read_sql_query('SELECT COALESCE(SUM(valor),0) AS total FROM empenhos', conn)
df_licitacoes = pd.read_sql_query('SELECT COALESCE(SUM(valor),0) AS total FROM licitacoes', conn)
df_contratos = pd.read_sql_query('SELECT COALESCE(SUM(valor),0) AS total FROM contratos', conn)
conn.close()

total_pagar = float(df_pagar['total'].iloc[0])
total_receber = float(df_receber['total'].iloc[0])
total_empenhos = float(df_empenhos['total'].iloc[0])
total_licitacoes = float(df_licitacoes['total'].iloc[0])
total_contratos = float(df_contratos['total'].iloc[0])

resumo_cols = st.columns(5)
resumo_labels = ['Contas a Pagar', 'Contas a Receber', 'Empenhos', 'Licitacoes', 'Contratos']
resumo_values = [total_pagar, total_receber, total_empenhos, total_licitacoes, total_contratos]
for i, (label, val) in enumerate(zip(resumo_labels, resumo_values)):
        with resumo_cols[i]:
            st.markdown(
                f'<div style="background: rgba(255,255,255,0.05); border:1px solid #a0eaff; border-radius:12px; padding:16px; text-align:center;">'
                f'<p style="color:#a0eaff; font-size:11px; margin:0;">{label}</p>'
                f'<p style="color:#00d4ff; font-size:16px; font-weight:700; margin:8px 0 0 0;">{format_currency(val)}</p>'
                '</div>',
                unsafe_allow_html=True
            )

# ------------------ GENERIC CRUD ------------------
def crud_page(title, table, columns, form_fields, id_field='id'):
    st.markdown(f'<h1 style="color:#00d4ff; text-align:center;">{title}</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:#00d4ff;">', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(['Listar', 'Adicionar', 'Editar / Excluir'])

    with tab1:
        conn = get_conn()
        df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
        conn.close()
        if df.empty:
            st.info('Nenhum registro encontrado.')
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        with st.form(f'form_add_{table}'):
            values = {}
            for field in form_fields:
                if field['type'] == 'text':
                    values[field['name']] = st.text_input(field['label'])
                elif field['type'] == 'number':
                    values[field['name']] = st.number_input(field['label'], step=0.01)
                elif field['type'] == 'date':
                    values[field['name']] = st.date_input(field['label'], datetime.today()).strftime('%Y-%m-%d')
                elif field['type'] == 'select':
                    values[field['name']] = st.selectbox(field['label'], field['options'])
            if st.form_submit_button('Salvar'):
                cols = ', '.join(values.keys())
                placeholders = ', '.join(['?' for _ in values])
                conn = get_conn()
                c = conn.cursor()
                c.execute(f'INSERT INTO {table} ({cols}) VALUES ({placeholders})', tuple(values.values()))
                conn.commit()
                conn.close()
                st.success('Registro adicionado com sucesso!')
                st.rerun()

    with tab3:
        conn = get_conn()
        c = conn.cursor()
        c.execute(f'SELECT {id_field}, {", ".join([f["name"] for f in form_fields])} FROM {table}')
        rows = c.fetchall()
        conn.close()

        if not rows:
            st.info('Nenhum registro para editar.')
            return

        options = {f'ID {r[0]} - {r[1]}': r[0] for r in rows}
        selected = st.selectbox('Selecione o registro', list(options.keys()))
        selected_id = options[selected]

        conn = get_conn()
        c = conn.cursor()
        c.execute(f'SELECT * FROM {table} WHERE {id_field} = ?', (selected_id,))
        row = c.fetchone()
        conn.close()

        if row is None:
            st.warning('Registro nao encontrado.')
            return

        with st.form(f'form_edit_{table}'):
            new_values = {}
            for i, field in enumerate(form_fields):
                current = row[i + 1]
                if field['type'] == 'text':
                    new_values[field['name']] = st.text_input(field['label'], value=current or '')
                elif field['type'] == 'number':
                    new_values[field['name']] = st.number_input(field['label'], value=float(current) if current else 0.0, step=0.01)
                elif field['type'] == 'date':
                    if current:
                        try:
                            d = datetime.strptime(current, '%Y-%m-%d').date()
                        except Exception:
                            d = datetime.today().date()
                    else:
                        d = datetime.today().date()
                    new_values[field['name']] = st.date_input(field['label'], d).strftime('%Y-%m-%d')
                elif field['type'] == 'select':
                    new_values[field['name']] = st.selectbox(field['label'], field['options'], index=field['options'].index(current) if current in field['options'] else 0)
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button('Atualizar'):
                    set_clause = ', '.join([f'{k} = ?' for k in new_values])
                    conn = get_conn()
                    c = conn.cursor()
                    c.execute(f'UPDATE {table} SET {set_clause} WHERE {id_field} = ?', tuple(new_values.values()) + (selected_id,))
                    conn.commit()
                    conn.close()
                    st.success('Registro atualizado!')
                    st.rerun()
            with col2:
                if st.form_submit_button('Excluir'):
                    conn = get_conn()
                    c = conn.cursor()
                    c.execute(f'DELETE FROM {table} WHERE {id_field} = ?', (selected_id,))
                    conn.commit()
                    conn.close()
                    st.success('Registro excluido!')
                    st.rerun()

# ------------------ CHANGE PASSWORD ------------------
def change_password_page():
    st.markdown('<h1 style="color:#00d4ff; text-align:center;">Trocar Senha</h1>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:#00d4ff;">', unsafe_allow_html=True)

    with st.form('form_trocar_senha'):
        st.markdown('<p style="color:#00d4ff; font-weight:700;">Senha Atual</p>', unsafe_allow_html=True)
        senha_atual = st.text_input('', type='password', key='senha_atual', label_visibility='collapsed')
        st.markdown('<p style="color:#00d4ff; font-weight:700;">Nova Senha</p>', unsafe_allow_html=True)
        nova_senha = st.text_input('', type='password', key='nova_senha', label_visibility='collapsed')
        st.markdown('<p style="color:#00d4ff; font-weight:700;">Confirmar Nova Senha</p>', unsafe_allow_html=True)
        confirmar_senha = st.text_input('', type='password', key='confirmar_senha', label_visibility='collapsed')
        if st.form_submit_button('Trocar Senha'):
            if nova_senha != confirmar_senha:
                st.error('Nova senha e confirmacao nao conferem!')
                return
            conn = get_conn()
            c = conn.cursor()
            c.execute('SELECT password FROM users WHERE username = ?', (st.session_state.get('username'),))
            row = c.fetchone()
            if row and row[0] == hash_password(senha_atual):
                c.execute('UPDATE users SET password = ? WHERE username = ?', (hash_password(nova_senha), st.session_state.get('username')))
                conn.commit()
                conn.close()
                st.success('Senha alterada com sucesso!')
            else:
                conn.close()
                st.error('Senha atual incorreta!')

# ------------------ MAIN ------------------
def main():
    if not authenticated():
        login_page()
    else:
        st.set_page_config(page_title='MARMED', layout='wide')
        st.markdown(
            '''
            <style>
            .main { background: #050b14; }
            .stApp { background: radial-gradient(circle at 50% 50%, #0a1f3d 0%, #02050a 100%); }
            h1, h2, h3 { color: #00d4ff; font-family: 'Orbitron', sans-serif; }
            </style>
            ''',
            unsafe_allow_html=True
        )
        menu = sidebar_menu()

        if menu == 'Dashboard':
            dashboard_page()
        elif menu == 'Contas a Pagar':
            crud_page('Contas a Pagar', 'contas_pagar', ['id', 'fornecedor', 'descricao', 'valor', 'vencimento', 'status'], [
                {'name': 'fornecedor', 'label': 'Fornecedor', 'type': 'text'},
                {'name': 'descricao', 'label': 'Descricao', 'type': 'text'},
                {'name': 'valor', 'label': 'Valor', 'type': 'number'},
                {'name': 'vencimento', 'label': 'Vencimento', 'type': 'date'},
                {'name': 'status', 'label': 'Status', 'type': 'select', 'options': ['Pendente', 'Pago', 'Atrasado']}
            ])
        elif menu == 'Contas a Receber':
            crud_page('Contas a Receber', 'contas_receber', ['id', 'devedor', 'descricao', 'valor', 'vencimento', 'status'], [
                {'name': 'devedor', 'label': 'Devedor', 'type': 'text'},
                {'name': 'descricao', 'label': 'Descricao', 'type': 'text'},
                {'name': 'valor', 'label': 'Valor', 'type': 'number'},
                {'name': 'vencimento', 'label': 'Vencimento', 'type': 'date'},
                {'name': 'status', 'label': 'Status', 'type': 'select', 'options': ['Pendente', 'Recebido', 'Atrasado']}
            ])
        elif menu == 'Empenhos':
            crud_page('Empenhos', 'empenhos', ['id', 'numero', 'objeto', 'valor', 'data', 'status'], [
                {'name': 'numero', 'label': 'Numero', 'type': 'text'},
                {'name': 'objeto', 'label': 'Objeto', 'type': 'text'},
                {'name': 'valor', 'label': 'Valor', 'type': 'number'},
                {'name': 'data', 'label': 'Data', 'type': 'date'},
                {'name': 'status', 'label': 'Status', 'type': 'select', 'options': ['Ativo', 'Anulado', 'Liquidado']}
            ])
        elif menu == 'Licitacoes':
            crud_page('Licitacoes', 'licitacoes', ['id', 'numero', 'objeto', 'modalidade', 'valor', 'data', 'status'], [
                {'name': 'numero', 'label': 'Numero', 'type': 'text'},
                {'name': 'objeto', 'label': 'Objeto', 'type': 'text'},
                {'name': 'modalidade', 'label': 'Modalidade', 'type': 'text'},
                {'name': 'valor', 'label': 'Valor', 'type': 'number'},
                {'name': 'data', 'label': 'Data', 'type': 'date'},
                {'name': 'status', 'label': 'Status', 'type': 'select', 'options': ['Aberta', 'Concluida', 'Cancelada']}
            ])
        elif menu == 'Contratos':
            crud_page('Contratos', 'contratos', ['id', 'numero', 'contratado', 'objeto', 'valor', 'inicio', 'fim', 'status'], [
                {'name': 'numero', 'label': 'Numero', 'type': 'text'},
                {'name': 'contratado', 'label': 'Contratado', 'type': 'text'},
                {'name': 'objeto', 'label': 'Objeto', 'type': 'text'},
                {'name': 'valor', 'label': 'Valor', 'type': 'number'},
                {'name': 'inicio', 'label': 'Inicio', 'type': 'date'},
                {'name': 'fim', 'label': 'Fim', 'type': 'date'},
                {'name': 'status', 'label': 'Status', 'type': 'select', 'options': ['Vigente', 'Concluido', 'Rescindido']}
            ])
        elif menu == 'Trocar Senha':
            change_password_page()

if __name__ == '__main__':
    main()
