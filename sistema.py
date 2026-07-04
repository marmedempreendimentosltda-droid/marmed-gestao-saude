import streamlit as st
import hashlib
import sqlite3
import datetime
import pandas as pd
from datetime import date, timedelta

st.set_page_config(
    page_title="MARMED - Gestão em Saúde Pública de Luminárias-MG",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_NAME = "marmed_saude.db"
COR_PRIMARIA = "#00d4ff"
COR_GOLD = "#ffd700"
COR_BG1 = "#0a0e27"
COR_BG2 = "#0d2137"

CSS_GLOBAL = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap');

* {{
    font-family: 'Montserrat', sans-serif;
}}

.stApp {{
    background: linear-gradient(135deg, {COR_BG1} 0%, {COR_BG2} 100%);
    color: #e6f7ff;
}}

.particles {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}}

.particle {{
    position: absolute;
    width: 4px;
    height: 4px;
    background: {COR_PRIMARIA};
    border-radius: 50%;
    opacity: 0.3;
    animation: float 15s infinite linear;
}}

.particle:nth-child(1) {{ left: 10%; animation-duration: 12s; animation-delay: 0s; }}
.particle:nth-child(2) {{ left: 20%; animation-duration: 18s; animation-delay: 2s; }}
.particle:nth-child(3) {{ left: 30%; animation-duration: 14s; animation-delay: 4s; }}
.particle:nth-child(4) {{ left: 40%; animation-duration: 20s; animation-delay: 1s; }}
.particle:nth-child(5) {{ left: 50%; animation-duration: 16s; animation-delay: 3s; }}
.particle:nth-child(6) {{ left: 60%; animation-duration: 22s; animation-delay: 5s; }}
.particle:nth-child(7) {{ left: 70%; animation-duration: 13s; animation-delay: 2s; }}
.particle:nth-child(8) {{ left: 80%; animation-duration: 19s; animation-delay: 4s; }}
.particle:nth-child(9) {{ left: 90%; animation-duration: 17s; animation-delay: 6s; }}
.particle:nth-child(10) {{ left: 95%; animation-duration: 21s; animation-delay: 0s; }}

@keyframes float {{
    0% {{ transform: translateY(100vh) scale(0); opacity: 0; }}
    10% {{ opacity: 0.3; }}
    90% {{ opacity: 0.3; }}
    100% {{ transform: translateY(-10vh) scale(1); opacity: 0; }}
}}

.glass-card {{
    background: rgba(13, 33, 55, 0.7);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}}

.metric-card {{
    background: rgba(13, 33, 55, 0.8);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    transition: all 0.3s ease;
}}

.metric-card:hover {{
    transform: translateY(-5px);
    border-color: {COR_PRIMARIA};
    box-shadow: 0 12px 40px rgba(0, 212, 255, 0.15);
}}

.metric-value {{
    color: {COR_GOLD};
    font-size: 1.6rem;
    font-weight: 700;
}}

.metric-label {{
    color: {COR_PRIMARIA};
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 8px;
}}

h1, h2, h3 {{
    color: {COR_PRIMARIA} !important;
}}

.stButton button {{
    background: linear-gradient(135deg, {COR_PRIMARIA} 0%, #0099cc 100%) !important;
    color: #0a0e27 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}}

.stButton button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0, 212, 255, 0.4) !important;
}}

.stTextInput input, .stSelectbox select, .stDateInput input, .stNumberInput input, .stTextArea textarea {{
    background: rgba(10, 14, 39, 0.8) !important;
    color: #e6f7ff !important;
    border: 1px solid rgba(0, 212, 255, 0.3) !important;
    border-radius: 8px !important;
}}

.stTextInput input:focus, .stSelectbox select:focus, .stDateInput input:focus, .stNumberInput input:focus {{
    border-color: {COR_PRIMARIA} !important;
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2) !important;
}}

.css-1d391kg, .css-163ttbj, .css-1vq4p4l {{
    background: rgba(10, 14, 39, 0.9) !important;
}}

.css-1cypcdb, .css-1cypcdb .e1q9f1ca0 {{
    color: {COR_PRIMARIA} !important;
}}

[data-testid="stSidebar"] {{
    background: rgba(10, 14, 39, 0.95) !important;
    border-right: 1px solid rgba(0, 212, 255, 0.2) !important;
}}

table {{
    color: #e6f7ff !important;
}}

th {{
    color: {COR_PRIMARIA} !important;
    background: rgba(0, 212, 255, 0.1) !important;
}}

.status-pago {{
    color: #00ff88;
    font-weight: 600;
}}

.status-pendente {{
    color: #ff6b6b;
    font-weight: 600;
}}

.status-atrasado {{
    color: #ffd700;
    font-weight: 600;
}}
</style>
"""


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nome TEXT,
            cargo TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contas_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            fornecedor TEXT,
            valor REAL NOT NULL,
            data_vencimento DATE,
            status TEXT DEFAULT 'Pendente',
            categoria TEXT,
            observacao TEXT,
            data_cadastro DATE DEFAULT CURRENT_DATE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contas_receber (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            devedor TEXT,
            valor REAL NOT NULL,
            data_vencimento DATE,
            status TEXT DEFAULT 'Pendente',
            categoria TEXT,
            observacao TEXT,
            data_cadastro DATE DEFAULT CURRENT_DATE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empenhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_empenho TEXT NOT NULL,
            descricao TEXT,
            valor REAL NOT NULL,
            data_empenho DATE,
            fornecedor TEXT,
            status TEXT DEFAULT 'Ativo',
            observacao TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS licitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_processo TEXT NOT NULL,
            objeto TEXT,
            modalidade TEXT,
            valor_estimado REAL,
            data_abertura DATE,
            status TEXT DEFAULT 'Em Andamento',
            vencedor TEXT,
            observacao TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_contrato TEXT NOT NULL,
            objeto TEXT,
            contratado TEXT,
            valor_total REAL,
            data_inicio DATE,
            data_fim DATE,
            status TEXT DEFAULT 'Vigente',
            observacao TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            descricao TEXT,
            valor REAL NOT NULL,
            data_movimentacao DATE DEFAULT CURRENT_DATE,
            categoria TEXT,
            observacao TEXT
        )
    ''')

    default_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    cursor.execute('''
        INSERT OR IGNORE INTO usuarios (username, password_hash, nome, cargo)
        VALUES (?, ?, ?, ?)
    ''', ('admin', default_hash, 'Administrador', 'Diretor'))

    conn.commit()
    conn.close()


def get_db_connection():
    return sqlite3.connect(DB_NAME)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_login(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM usuarios WHERE username = ? AND password_hash = ?",
        (username, hash_password(password))
    )
    user = cursor.fetchone()
    conn.close()
    return user


def update_password(username, new_password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE usuarios SET password_hash = ? WHERE username = ?",
        (hash_password(new_password), username)
    )
    conn.commit()
    conn.close()


def add_record(table, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data])
    cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", list(data.values()))
    conn.commit()
    conn.close()


def get_all_records(table):
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT * FROM {table} ORDER BY id DESC", conn)
    conn.close()
    return df


def update_record(table, id_value, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    sets = ', '.join([f"{k} = ?" for k in data.keys()])
    values = list(data.values()) + [id_value]
    cursor.execute(f"UPDATE {table} SET {sets} WHERE id = ?", values)
    conn.commit()
    conn.close()


def delete_record(table, id_value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table} WHERE id = ?", (id_value,))
    conn.commit()
    conn.close()


def get_record_by_id(table, id_value):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (id_value,))
    record = cursor.fetchone()
    conn.close()
    return record


def format_currency(value):
    if pd.isna(value) or value is None:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def render_login():
    st.markdown("<<div class='particles'>" + "".join(["<<div class='particle'></div>" for _ in range(10)]) + "</div>", unsafe_allow_html=True)
    st.markdown("<<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<<h1 style='text-align: center;'>🏥 MARMED</h1>", unsafe_allow_html=True)
        st.markdown("<<h3 style='text-align: center; color: #e6f7ff;'>Gestão em Saúde Pública</h3>", unsafe_allow_html=True)
        st.markdown("<<p style='text-align: center; color: #00d4ff; font-weight: 600;'>Luminárias - MG</p>", unsafe_allow_html=True)
        st.markdown("<<br>", unsafe_allow_html=True)

        username = st.text_input("Usuário", key="login_user")
        password = st.text_input("Senha", type="password", key="login_pass")

        if st.button("Entrar", use_container_width=True):
            user = verify_login(username, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.nome = user[3]
                st.session_state.cargo = user[4]
                st.session_state.page = "Dashboard"
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos!")
        st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown(f"<<h2 style='color: #00d4ff;'>🏥 MARMED</h2>", unsafe_allow_html=True)
        st.markdown(f"<<p style='color: #e6f7ff;'>Bem-vindo, <b>{st.session_state.get('nome', 'Admin')}</b></p>", unsafe_allow_html=True)
        st.markdown(f"<<p style='color: #ffd700; font-size: 0.85rem;'>{st.session_state.get('cargo', 'Diretor')}</p>", unsafe_allow_html=True)
        st.markdown("<<hr style='border-color: rgba(0,212,255,0.3);'>", unsafe_allow_html=True)

        pages = [
            "Dashboard", "Contas a Pagar", "Contas a Receber", "Empenhos",
            "Licitações", "Contratos", "Relatórios", "Trocar Senha", "Sair"
        ]

        for page in pages:
            if st.button(page, use_container_width=True, key=f"nav_{page}"):
                if page == "Sair":
                    st.session_state.clear()
                    st.rerun()
                else:
                    st.session_state.page = page
                    st.rerun()


def render_dashboard():
    st.markdown("<<h1>Dashboard</h1>", unsafe_allow_html=True)

    metricas = [
        ("REPASSE FEDERAL", 1250000),
        ("REPASSE ESTADUAL", 890000),
        ("RECURSO MUNICIPAL", 450000),
        ("TRANSFERÊNCIA", 320000),
        ("TRANSPOSIÇÃO", 180000)
    ]

    cols = st.columns(5)
    for i, (label, value) in enumerate(metricas):
        with cols[i]:
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='metric-value'>{format_currency(value)}</div>
                    <div class='metric-label'>{label}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<<h3>📊 Movimentações</h3>", unsafe_allow_html=True)
        df = get_all_records("movimentacoes")
        if not df.empty:
            df['valor'] = df['valor'].apply(format_currency)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma movimentação registrada.")

        with st.expander("➕ Nova Movimentação"):
            with st.form("form_movimentacao"):
                tipo = st.selectbox("Tipo", ["Entrada", "Saída", "Transferência"])
                descricao = st.text_input("Descrição")
                valor = st.number_input("Valor", min_value=0.0, format="%.2f")
                categoria = st.text_input("Categoria")
                observacao = st.text_area("Observação")
                submitted = st.form_submit_button("Salvar Movimentação")
                if submitted:
                    add_record("movimentacoes", {
                        "tipo": tipo,
                        "descricao": descricao,
                        "valor": valor,
                        "data_movimentacao": date.today().isoformat(),
                        "categoria": categoria,
                        "observacao": observacao
                    })
                    st.success("Movimentação registrada com sucesso!")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<<h3>📅 Resumo do Mês</h3>", unsafe_allow_html=True)

        today = date.today()
        first_day = today.replace(day=1).isoformat()
        last_day = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        last_day = last_day.isoformat()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM contas_pagar WHERE status = 'Pago' AND data_vencimento BETWEEN ? AND ?", (first_day, last_day))
        total_pago = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM contas_pagar WHERE status = 'Pendente' AND data_vencimento BETWEEN ? AND ?", (first_day, last_day))
        total_pagar = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM contas_receber WHERE status = 'Recebido' AND data_vencimento BETWEEN ? AND ?", (first_day, last_day))
        total_recebido = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(valor), 0) FROM contas_receber WHERE status = 'Pendente' AND data_vencimento BETWEEN ? AND ?", (first_day, last_day))
        total_receber = cursor.fetchone()[0]

        conn.close()

        st.markdown(f"<<p style='color: #00d4ff;'>Contas Pagas</p>", unsafe_allow_html=True)
        st.markdown(f"<<p class='metric-value'>{format_currency(total_pago)}</p>", unsafe_allow_html=True)

        st.markdown(f"<<p style='color: #00d4ff;'>Contas a Pagar</p>", unsafe_allow_html=True)
        st.markdown(f"<<p class='metric-value'>{format_currency(total_pagar)}</p>", unsafe_allow_html=True)

        st.markdown(f"<<p style='color: #00d4ff;'>Contas Recebidas</p>", unsafe_allow_html=True)
        st.markdown(f"<<p class='metric-value'>{format_currency(total_recebido)}</p>", unsafe_allow_html=True)

        st.markdown(f"<<p style='color: #00d4ff;'>Contas a Receber</p>", unsafe_allow_html=True)
        st.markdown(f"<<p class='metric-value'>{format_currency(total_receber)}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


def crud_page(table_name, title, fields, date_fields=None):
    if date_fields is None:
        date_fields = []

    st.markdown(f"<<h1>{title}</h1>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 Listar", "➕ Adicionar"])

    with tab1:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        df = get_all_records(table_name)
        if not df.empty:
            for field in fields:
                if field in df.columns and field in date_fields:
                    df[field] = pd.to_datetime(df[field], errors='coerce').dt.strftime('%d/%m/%Y')
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown("<<br>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                id_edit = st.number_input("ID para editar", min_value=1, step=1, key=f"edit_{table_name}")
            with col2:
                id_delete = st.number_input("ID para excluir", min_value=1, step=1, key=f"delete_{table_name}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Edregar", key=f"btn_edit_{table_name}"):
                    record = get_record_by_id(table_name, id_edit)
                    if record:
                        st.session_state[f"edit_record_{table_name}"] = record
                        st.rerun()
                    else:
                        st.error("Registro não encontrado!")
            with col2:
                if st.button("🗑️ Excluir", key=f"btn_delete_{table_name}"):
                    delete_record(table_name, id_delete)
                    st.success("Registro excluído com sucesso!")
                    st.rerun()
        else:
            st.info("Nenhum registro encontrado.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        with st.form(f"form_add_{table_name}"):
            values = {}
            for field in fields:
                if field in date_fields:
                    values[field] = st.date_input(field.replace("_", " ").title(), key=f"add_{field}_{table_name}").isoformat()
                elif field in ["valor", "valor_estimado", "valor_total"]:
                    values[field] = st.number_input(field.replace("_", " ").title(), min_value=0.0, format="%.2f", key=f"add_{field}_{table_name}")
                elif field == "status":
                    values[field] = st.selectbox(field.replace("_", " ").title(), ["Pendente", "Pago", "Atrasado", "Recebido", "Ativo", "Inativo", "Em Andamento", "Concluído", "Cancelado", "Vigente", "Encerrado"], key=f"add_{field}_{table_name}")
                elif field == "modalidade":
                    values[field] = st.selectbox("Modalidade", ["Pregão", "Tomada de Preços", "Concorrência", "Convite", "Leilão", "Concurso", "Dispensa", "Inexigibilidade"], key=f"add_{field}_{table_name}")
                elif field == "observacao":
                    values[field] = st.text_area(field.replace("_", " ").title(), key=f"add_{field}_{table_name}")
                else:
                    values[field] = st.text_input(field.replace("_", " ").title(), key=f"add_{field}_{table_name}")

            submitted = st.form_submit_button("Salvar")
            if submitted:
                add_record(table_name, values)
                st.success("Registro salvo com sucesso!")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if f"edit_record_{table_name}" in st.session_state:
        record = st.session_state[f"edit_record_{table_name}"]
        st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<<h3>✏️ Editar Registro</h3>", unsafe_allow_html=True)
        with st.form(f"form_edit_{table_name}"):
            values = {}
            for i, field in enumerate(fields):
                if field in date_fields:
                    try:
                        default = pd.to_datetime(record[i+1]).date() if record[i+1] else date.today()
                    except:
                        default = date.today()
                    values[field] = st.date_input(field.replace("_", " ").title(), value=default, key=f"edit_{field}_{table_name}").isoformat()
                elif field in ["valor", "valor_estimado", "valor_total"]:
                    values[field] = st.number_input(field.replace("_", " ").title(), min_value=0.0, value=float(record[i+1] or 0), format="%.2f", key=f"edit_{field}_{table_name}")
                elif field == "status":
                    values[field] = st.selectbox(field.replace("_", " ").title(), ["Pendente", "Pago", "Atrasado", "Recebido", "Ativo", "Inativo", "Em Andamento", "Concluído", "Cancelado", "Vigente", "Encerrado"], index=["Pendente", "Pago", "Atrasado", "Recebido", "Ativo", "Inativo", "Em Andamento", "Concluído", "Cancelado", "Vigente", "Encerrado"].index(record[i+1]) if record[i+1] in ["Pendente", "Pago", "Atrasado", "Recebido", "Ativo", "Inativo", "Em Andamento", "Concluído", "Cancelado", "Vigente", "Encerrado"] else 0, key=f"edit_{field}_{table_name}")
                elif field == "modalidade":
                    values[field] = st.selectbox("Modalidade", ["Pregão", "Tomada de Preços", "Concorrência", "Convite", "Leilão", "Concurso", "Dispensa", "Inexigibilidade"], index=["Pregão", "Tomada de Preços", "Concorrência", "Convite", "Leilão", "Concurso", "Dispensa", "Inexigibilidade"].index(record[i+1]) if record[i+1] in ["Pregão", "Tomada de Preços", "Concorrência", "Convite", "Leilão", "Concurso", "Dispensa", "Inexigibilidade"] else 0, key=f"edit_{field}_{table_name}")
                elif field == "observacao":
                    values[field] = st.text_area(field.replace("_", " ").title(), value=record[i+1] or "", key=f"edit_{field}_{table_name}")
                else:
                    values[field] = st.text_input(field.replace("_", " ").title(), value=record[i+1] or "", key=f"edit_{field}_{table_name}")

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Atualizar"):
                    update_record(table_name, record[0], values)
                    del st.session_state[f"edit_record_{table_name}"]
                    st.success("Registro atualizado com sucesso!")
                    st.rerun()
            with col2:
                if st.form_submit_button("Cancelar"):
                    del st.session_state[f"edit_record_{table_name}"]
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


def render_contas_pagar():
    crud_page("contas_pagar", "Contas a Pagar", ["descricao", "fornecedor", "valor", "data_vencimento", "status", "categoria", "observacao"], ["data_vencimento"])


def render_contas_receber():
    crud_page("contas_receber", "Contas a Receber", ["descricao", "devedor", "valor", "data_vencimento", "status", "categoria", "observacao"], ["data_vencimento"])


def render_empenhos():
    crud_page("empenhos", "Empenhos", ["numero_empenho", "descricao", "valor", "data_empenho", "fornecedor", "status", "observacao"], ["data_empenho"])


def render_licitacoes():
    crud_page("licitacoes", "Licitações", ["numero_processo", "objeto", "modalidade", "valor_estimado", "data_abertura", "status", "vencedor", "observacao"], ["data_abertura"])


def render_contratos():
    crud_page("contratos", "Contratos", ["numero_contrato", "objeto", "contratado", "valor_total", "data_inicio", "data_fim", "status", "observacao"], ["data_inicio", "data_fim"])


def render_relatorios():
    st.markdown("<<h1>Relatórios</h1>", unsafe_allow_html=True)
    st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        relatorio = st.selectbox("Tipo de Relatório", ["Contas a Pagar", "Contas a Receber", "Empenhos", "Licitações", "Contratos", "Movimentações"])
    with col2:
        data_inicio = st.date_input("Data Início", value=date.today().replace(day=1))
    with col3:
        data_fim = st.date_input("Data Fim", value=date.today())

    if st.button("Gerar Relatório", use_container_width=True):
        tabela = relatorio.lower().replace(" ", "_")
        if tabela == "contas_a_pagar":
            tabela = "contas_pagar"
        elif tabela == "contas_a_receber":
            tabela = "contas_receber"

        conn = get_db_connection()
        if tabela == "movimentacoes":
            query = f"SELECT * FROM {tabela} WHERE data_movimentacao BETWEEN ? AND ? ORDER BY data_movimentacao DESC"
        elif tabela == "licitacoes":
            query = f"SELECT * FROM {tabela} WHERE data_abertura BETWEEN ? AND ? ORDER BY data_abertura DESC"
        elif tabela == "contratos":
            query = f"SELECT * FROM {tabela} WHERE data_inicio BETWEEN ? AND ? ORDER BY data_inicio DESC"
        else:
            query = f"SELECT * FROM {tabela} WHERE data_vencimento BETWEEN ? AND ? ORDER BY data_vencimento DESC"

        df = pd.read_sql_query(query, conn, params=(data_inicio.isoformat(), data_fim.isoformat()))
        conn.close()

        if not df.empty:
            st.markdown(f"<<h3>Relatório de {relatorio}</h3>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, hide_index=True)

            total = 0
            valor_cols = [c for c in df.columns if 'valor' in c]
            if valor_cols:
                total = df[valor_cols[0]].sum()
                st.markdown(f"<<h3 style='color: #ffd700;'>Total: {format_currency(total)}</h3>", unsafe_allow_html=True)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar CSV",
                data=csv,
                file_name=f"relatorio_{relatorio.lower().replace(' ', '_')}_{data_inicio.isoformat()}_{data_fim.isoformat()}.csv",
                mime='text/csv',
                use_container_width=True
            )
        else:
            st.info("Nenhum registro encontrado no período selecionado.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_trocar_senha():
    st.markdown("<<h1>Trocar Senha</h1>", unsafe_allow_html=True)
    st.markdown("<<div class='glass-card'>", unsafe_allow_html=True)

    with st.form("form_trocar_senha"):
        senha_atual = st.text_input("Senha Atual", type="password")
        nova_senha = st.text_input("Nova Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Nova Senha", type="password")
        submitted = st.form_submit_button("Alterar Senha")

        if submitted:
            if not verify_login(st.session_state.username, senha_atual):
                st.error("Senha atual incorreta!")
            elif nova_senha != confirmar_senha:
                st.error("As novas senhas não conferem!")
            elif len(nova_senha) < 6:
                st.error("A nova senha deve ter pelo menos 6 caracteres!")
            else:
                update_password(st.session_state.username, nova_senha)
                st.success("Senha alterada com sucesso! Faça login novamente.")
                st.session_state.clear()
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    init_db()
    st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"

    if not st.session_state.authenticated:
        render_login()
    else:
        render_sidebar()
        page = st.session_state.page

        if page == "Dashboard":
            render_dashboard()
        elif page == "Contas a Pagar":
            render_contas_pagar()
        elif page == "Contas a Receber":
            render_contas_receber()
        elif page == "Empenhos":
            render_empenhos()
        elif page == "Licitações":
            render_licitacoes()
        elif page == "Contratos":
            render_contratos()
        elif page == "Relatórios":
            render_relatorios()
        elif page == "Trocar Senha":
            render_trocar_senha()


if __name__ == "__main__":
    main()
