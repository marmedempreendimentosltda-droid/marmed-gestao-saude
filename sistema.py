import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, date, timedelta
import pandas as pd
import os

# ===================== CONFIGURAÇÃO =====================
DB_PATH = "marmed.db"

# ===================== BANCO DE DADOS =====================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS contas_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fornecedor TEXT NOT NULL,
            descricao TEXT,
            valor REAL NOT NULL,
            vencimento DATE NOT NULL,
            status TEXT DEFAULT 'Pendente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS contas_receber (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            descricao TEXT,
            valor REAL NOT NULL,
            vencimento DATE NOT NULL,
            status TEXT DEFAULT 'Pendente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS empenhos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            descricao TEXT,
            valor REAL NOT NULL,
            data DATE NOT NULL,
            status TEXT DEFAULT 'Ativo',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS licitacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            objeto TEXT,
            status TEXT DEFAULT 'Em Andamento',
            data_abertura DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS contratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            contratada TEXT NOT NULL,
            objeto TEXT,
            valor REAL NOT NULL,
            inicio DATE NOT NULL,
            fim DATE NOT NULL,
            status TEXT DEFAULT 'Ativo',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    admin_hash = hashlib.sha256("Diretor2025#".encode()).hexdigest()
    c.execute('''
        INSERT OR IGNORE INTO usuarios (username, password_hash, role)
        VALUES (?, ?, ?)
    ''', ("admin", admin_hash, "admin"))

    conn.commit()
    conn.close()

# ===================== FUNÇÕES AUXILIARES =====================
def get_db_connection():
    return sqlite3.connect(DB_PATH)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def login_user(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT id, username, role FROM usuarios
        WHERE username = ? AND password_hash = ?
    ''', (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user


def load_data(table_name):
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df


def insert_record(table_name, columns, values):
    conn = get_db_connection()
    c = conn.cursor()
    placeholders = ", ".join(["?"] * len(values))
    c.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
    conn.commit()
    conn.close()


def update_record(table_name, record_id, columns, values):
    conn = get_db_connection()
    c = conn.cursor()
    set_clause = ", ".join([f"{col} = ?" for col in columns])
    c.execute(f"UPDATE {table_name} SET {set_clause} WHERE id = ?", values + [record_id])
    conn.commit()
    conn.close()


def delete_record(table_name, record_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()


# ===================== PÁGINAS =====================
def login_page():
    st.title("MARMED - Sistema de Gestão")
    st.markdown("### Login")

    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")

    if submitted:
        user = login_user(username, password)
        if user:
            st.session_state["authenticated"] = True
            st.session_state["user"] = {"id": user[0], "username": user[1], "role": user[2]}
            st.session_state["page"] = "Dashboard"
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")


def dashboard():
    st.title("Dashboard")
    st.markdown("Visão geral do sistema MARMED")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        df_pagar = load_data("contas_pagar")
        st.metric(label="Contas a Pagar", value=len(df_pagar))

    with col2:
        df_receber = load_data("contas_receber")
        st.metric(label="Contas a Receber", value=len(df_receber))

    with col3:
        df_empenhos = load_data("empenhos")
        st.metric(label="Empenhos", value=len(df_empenhos))

    with col4:
        df_licitacoes = load_data("licitacoes")
        st.metric(label="Licitações", value=len(df_licitacoes))

    with col5:
        df_contratos = load_data("contratos")
        st.metric(label="Contratos", value=len(df_contratos))


    st.subheader("Contas a Pagar - Próximos Vencimentos")
    if not df_pagar.empty:
        df_pagar["vencimento"] = pd.to_datetime(df_pagar["vencimento"]).dt.strftime("%d/%m/%Y")
        st.dataframe(df_pagar[["id", "fornecedor", "descricao", "valor", "vencimento", "status"]], use_container_width=True)
    else:
        st.info("Nenhuma conta a pagar cadastrada.")


    st.subheader("Contas a Receber - Próximos Vencimentos")
    if not df_receber.empty:
        df_receber["vencimento"] = pd.to_datetime(df_receber["vencimento"]).dt.strftime("%d/%m/%Y")
        st.dataframe(df_receber[["id", "cliente", "descricao", "valor", "vencimento", "status"]], use_container_width=True)
    else:
        st.info("Nenhuma conta a receber cadastrada.")


def crud_page(title, table_name, columns_config, default_values=None):
    st.title(title)

    df = load_data(table_name)

    tab1, tab2 = st.tabs(["Listar", "Adicionar / Editar"])

    with tab1:
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro encontrado.")

    with tab2:
        records = []
        if not df.empty:
            records = df.to_dict("records")
            record_options = {f"{r['id']} - {str(r.get(list(columns_config.keys())[0], ''))}": r["id"] for r in records}
            record_options["Novo"] = None
        else:
            record_options = {"Novo": None}

        selected = st.selectbox("Selecionar registro", list(record_options.keys()))
        selected_id = record_options[selected]

        record_data = None
        if selected_id:
            record_data = df[df["id"] == selected_id].iloc[0].to_dict()

        with st.form("crud_form"):
            values = []
            form_columns = []
            for col, config in columns_config.items():
                if config["type"] == "text":
                    val = st.text_input(config["label"], value=record_data.get(col, default_values.get(col, "")) if record_data else default_values.get(col, ""))
                elif config["type"] == "textarea":
                    val = st.text_area(config["label"], value=record_data.get(col, default_values.get(col, "")) if record_data else default_values.get(col, ""))
                elif config["type"] == "number":
                    val = st.number_input(config["label"], value=float(record_data.get(col, default_values.get(col, 0))) if record_data else float(default_values.get(col, 0)))
                elif config["type"] == "date":
                    default_date = record_data.get(col, default_values.get(col, date.today())) if record_data else default_values.get(col, date.today())
                    if isinstance(default_date, str):
                        default_date = datetime.strptime(default_date, "%Y-%m-%d").date()
                    val = st.date_input(config["label"], value=default_date)
                elif config["type"] == "select":
                    options = config["options"]
                    default_val = record_data.get(col, default_values.get(col, options[0])) if record_data else default_values.get(col, options[0])
                    val = st.selectbox(config["label"], options=options, index=options.index(default_val) if default_val in options else 0)
                else:
                    val = None

                values.append(val)
                form_columns.append(col)

            submitted = st.form_submit_button("Salvar")

        if submitted:
            if selected_id:
                update_record(table_name, selected_id, form_columns, values)
                st.success("Registro atualizado com sucesso!")
            else:
                insert_record(table_name, ", ".join(form_columns), values)
                st.success("Registro inserido com sucesso!")
            st.rerun()

        if selected_id:
            if st.button("Excluir", type="primary"):
                delete_record(table_name, selected_id)
                st.warning("Registro excluído!")
                st.rerun()


def change_password():
    st.title("Alterar Senha")
    with st.form("change_password_form"):
        current = st.text_input("Senha atual", type="password")
        new_pass = st.text_input("Nova senha", type="password")
        confirm = st.text_input("Confirmar nova senha", type="password")
        submitted = st.form_submit_button("Alterar")

    if submitted:
        user = st.session_state.get("user")
        if not user:
            st.error("Usuário não autenticado.")
            return

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT password_hash FROM usuarios WHERE id = ?", (user["id"],))
        row = c.fetchone()
        conn.close()

        if row and row[0] == hash_password(current):
            if new_pass == confirm:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("UPDATE usuarios SET password_hash = ? WHERE id = ?", (hash_password(new_pass), user["id"]))
                conn.commit()
                conn.close()
                st.success("Senha alterada com sucesso!")
            else:
                st.error("As novas senhas não conferem.")
        else:
            st.error("Senha atual incorreta.")


# ===================== MAIN =====================
def main():
    st.set_page_config(page_title="MARMED", layout="wide")
    init_db()

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "page" not in st.session_state:
        st.session_state["page"] = "Dashboard"

    if not st.session_state["authenticated"]:
        login_page()
        return

    with st.sidebar:
        st.markdown("## MARMED")
        st.markdown(f"Usuário: **{st.session_state['user']['username']}**")
        st.markdown("---")

        if st.button("Dashboard"):
            st.session_state["page"] = "Dashboard"
            st.rerun()

        if st.button("Registrar Conta"):
            st.session_state["page"] = "Registrar Conta"
            st.rerun()

        if st.button("Contas Ativas"):
            st.session_state["page"] = "Contas Ativas"
            st.rerun()

        st.markdown("---")

        if st.button("Alterar Senha"):
            st.session_state["page"] = "Alterar Senha"
            st.rerun()

        if st.button("Sair"):
            st.session_state["authenticated"] = False
            st.session_state["page"] = "Dashboard"
            st.session_state.pop("user", None)
            st.rerun()

    page = st.session_state.get("page", "Dashboard")

    if page == "Dashboard":
        dashboard()
    elif page == "Registrar Conta":
        crud_page(
            "Registrar Conta",
            "contas_receber",
            {
                "cliente": {"label": "Cliente", "type": "text"},
                "descricao": {"label": "Descrição", "type": "textarea"},
                "valor": {"label": "Valor", "type": "number"},
                "vencimento": {"label": "Vencimento", "type": "date"},
                "status": {"label": "Status", "type": "select", "options": ["Pendente", "Recebido", "Atrasado", "Cancelado"]}
            },
            default_values={"status": "Pendente"}
        )
    elif page == "Contas Ativas":
        crud_page(
            "Contas Ativas",
            "contas_pagar",
            {
                "fornecedor": {"label": "Fornecedor", "type": "text"},
                "descricao": {"label": "Descrição", "type": "textarea"},
                "valor": {"label": "Valor", "type": "number"},
                "vencimento": {"label": "Vencimento", "type": "date"},
                "status": {"label": "Status", "type": "select", "options": ["Pendente", "Pago", "Atrasado", "Cancelado"]}
            },
            default_values={"status": "Pendente"}
        )
    elif page == "Alterar Senha":
        change_password()


if __name__ == "__main__":
    main()
