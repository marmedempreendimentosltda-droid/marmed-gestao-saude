import sqlite3
import hashlib
from datetime import datetime


def init_db():
    """
    Inicializa o banco marmed.db de forma defensiva:
    - Cria as tabelas se não existirem (CREATE TABLE IF NOT EXISTS)
    - Verifica colunas existentes via PRAGMA table_info
    - Adiciona colunas faltantes via ALTER TABLE (envolto em try/except)
    - Não apaga tabelas nem dados existentes
    - Garante o usuário admin padrão (admin / Diretor2025#)
    """
    conn = sqlite3.connect("marmed.db")
    cur = conn.cursor()

    # ------------------------------------------------------------------
    # 1) Definição completa do schema esperado de cada tabela.
    #    Estrutura: { tabela: [(nome_coluna, definicao_sql), ...] }
    #    A definição_sql é usada tanto no CREATE quanto no ALTER TABLE.
    # ------------------------------------------------------------------
    schema = {
        "users": [
            ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
            ("username", "TEXT UNIQUE"),
            ("password_hash", "TEXT"),
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
    }

    # ------------------------------------------------------------------
    # 2) Criação das tabelas (se não existirem).
    #    CREATE TABLE IF NOT EXISTS não altera tabelas já existentes,
    #    por isso a etapa de migração defensiva abaixo é necessária.
    # ------------------------------------------------------------------
    for tabela, colunas in schema.items():
        colunas_sql = ", ".join(f"{nome} {definicao}" for nome, definicao in colunas)
        cur.execute(f"CREATE TABLE IF NOT EXISTS {tabela} ({colunas_sql})")

    # ------------------------------------------------------------------
    # 3) Migração defensiva: para cada tabela, verifica as colunas
    #    existentes com PRAGMA table_info e adiciona as faltantes.
    #    ALTER TABLE ADD COLUMN é envolvido em try/except porque o
    #    SQLite não suporta "ADD COLUMN IF NOT EXISTS" nativamente.
    # ------------------------------------------------------------------
    for tabela, colunas in schema.items():
        # PRAGMA table_info retorna uma linha por coluna:
        # (cid, name, type, notnull, dflt_value, pk)
        colunas_existentes = {
            row[1] for row in cur.execute(f"PRAGMA table_info({tabela})").fetchall()
        }

        for nome_coluna, definicao in colunas:
            if nome_coluna in colunas_existentes:
                continue

            # Colunas PRIMARY KEY não podem ser adicionadas via ALTER TABLE.
            # Elas só existem em tabelas recém-criadas; se faltarem em uma
            # tabela antiga, não há migração segura sem recriar a tabela,
            # então pulamos silenciosamente para não apagar dados.
            if "PRIMARY KEY" in definicao.upper():
                continue

            try:
                cur.execute(
                    f"ALTER TABLE {tabela} ADD COLUMN {nome_coluna} {definicao}"
                )
            except sqlite3.OperationalError:
                # Coluna já existe ou restrição inviabilizou o ALTER:
                # ignoramos para não quebrar a inicialização.
                pass

    # ------------------------------------------------------------------
    # 4) Criação do usuário admin padrão, se ainda não existir.
    #    Senha padrão: Diretor2025#
    # ------------------------------------------------------------------
    admin_hash = hashlib.sha256("Diretor2025#".encode("utf-8")).hexdigest()
    try:
        cur.execute(
            "INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)",
            ("admin", admin_hash),
        )
    except sqlite3.OperationalError:
        # Se a tabela users estiver em estado inesperado, não derruba o app.
        pass

    conn.commit()
    conn.close()
