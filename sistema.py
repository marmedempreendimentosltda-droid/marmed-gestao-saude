import os
import datetime
import sqlite3
import json
import hashlib
from typing import List, Optional, Dict, Any

# ---------------------- DATABASE ----------------------

DB_FILE = "marmed_orcamento.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS exercicios_orcamentarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ano INTEGER NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK(status IN ('elaboracao','aprovado','execucao','encerrado')),
    data_inicio DATE,
    data_fim DATE
);

CREATE TABLE IF NOT EXISTS orgaos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL,
    nome TEXT NOT NULL,
    sigla TEXT NOT NULL,
    ativo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS programas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL,
    nome TEXT NOT NULL,
    objetivo TEXT,
    orgao_responsavel_id INTEGER,
    FOREIGN KEY (orgao_responsavel_id) REFERENCES orgaos(id)
);

CREATE TABLE IF NOT EXISTS acoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('projeto','atividade','operacao_especial')),
    nome TEXT NOT NULL,
    produto TEXT,
    unidade_medida TEXT,
    programa_id INTEGER,
    orgao_id INTEGER,
    FOREIGN KEY (programa_id) REFERENCES programas(id),
    FOREIGN KEY (orgao_id) REFERENCES orgaos(id)
);

CREATE TABLE IF NOT EXISTS naturezas_despesa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL,
    categoria TEXT NOT NULL,
    grupo TEXT NOT NULL,
    modalidade TEXT,
    elemento TEXT,
    descricao TEXT
);

CREATE TABLE IF NOT EXISTS fontes_recurso (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL,
    descricao TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('tesouro','vinculado','convenio'))
);

CREATE TABLE IF NOT EXISTS dotacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercicio_id INTEGER,
    orgao_id INTEGER,
    programa_id INTEGER,
    acao_id INTEGER,
    natureza_id INTEGER,
    fonte_recurso_id INTEGER,
    valor_original DECIMAL(15,2) DEFAULT 0,
    valor_atual DECIMAL(15,2) DEFAULT 0,
    valor_empenhado DECIMAL(15,2) DEFAULT 0,
    valor_liquidado DECIMAL(15,2) DEFAULT 0,
    valor_pago DECIMAL(15,2) DEFAULT 0,
    FOREIGN KEY (exercicio_id) REFERENCES exercicios_orcamentarios(id),
    FOREIGN KEY (orgao_id) REFERENCES orgaos(id),
    FOREIGN KEY (programa_id) REFERENCES programas(id),
    FOREIGN KEY (acao_id) REFERENCES acoes(id),
    FOREIGN KEY (natureza_id) REFERENCES naturezas_despesa(id),
    FOREIGN KEY (fonte_recurso_id) REFERENCES fontes_recurso(id)
);

CREATE TABLE IF NOT EXISTS previsao_receitas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercicio_id INTEGER,
    fonte_recurso_id INTEGER,
    descricao TEXT,
    valor_previsto DECIMAL(15,2) DEFAULT 0,
    valor_realizado DECIMAL(15,2) DEFAULT 0,
    mes_competencia INTEGER,
    FOREIGN KEY (exercicio_id) REFERENCES exercicios_orcamentarios(id),
    FOREIGN KEY (fonte_recurso_id) REFERENCES fontes_recurso(id)
);

CREATE TABLE IF NOT EXISTS credores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL CHECK(tipo IN ('pf','pj')),
    cpf_cnpj TEXT NOT NULL,
    nome TEXT NOT NULL,
    endereco TEXT,
    dados_bancarios TEXT,
    ativo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS licitacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT NOT NULL,
    modalidade TEXT NOT NULL CHECK(modalidade IN ('pregao','concorrencia','tomada_precos','convite','dispensa','inexigibilidade')),
    objeto TEXT,
    data_abertura DATE,
    valor_estimado DECIMAL(15,2) DEFAULT 0,
    situacao TEXT NOT NULL CHECK(situacao IN ('em_andamento','homologada','fracassada','cancelada')),
    orgao_id INTEGER,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    percentual_alerta_retirada DECIMAL(5,2) DEFAULT 20.00,
    FOREIGN KEY (orgao_id) REFERENCES orgaos(id)
);

CREATE TABLE IF NOT EXISTS itens_licitacao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    licitacao_id INTEGER,
    produto_nome TEXT,
    descricao TEXT,
    quantidade_total DECIMAL(15,2) DEFAULT 0,
    unidade_medida TEXT,
    valor_unitario DECIMAL(15,2) DEFAULT 0,
    quantidade_retirada DECIMAL(15,2) DEFAULT 0,
    saldo DECIMAL(15,2) DEFAULT 0,
    FOREIGN KEY (licitacao_id) REFERENCES licitacoes(id)
);

CREATE TABLE IF NOT EXISTS ordens_compra (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    licitacao_id INTEGER,
    item_licitacao_id INTEGER,
    numero TEXT,
    data DATE,
    quantidade DECIMAL(15,2) DEFAULT 0,
    valor_unitario DECIMAL(15,2) DEFAULT 0,
    valor_total DECIMAL(15,2) DEFAULT 0,
    situacao TEXT NOT NULL CHECK(situacao IN ('pendente','entregue','cancelada')),
    observacao TEXT,
    FOREIGN KEY (licitacao_id) REFERENCES licitacoes(id),
    FOREIGN KEY (item_licitacao_id) REFERENCES itens_licitacao(id)
);

CREATE TABLE IF NOT EXISTS contratos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT,
    licitacao_id INTEGER,
    credor_id INTEGER,
    objeto TEXT,
    valor_global DECIMAL(15,2) DEFAULT 0,
    vigencia_inicio DATE,
    vigencia_fim DATE,
    dotacao_id INTEGER,
    situacao TEXT NOT NULL CHECK(situacao IN ('ativo','suspenso','encerrado','rescindido')),
    FOREIGN KEY (licitacao_id) REFERENCES licitacoes(id),
    FOREIGN KEY (credor_id) REFERENCES credores(id),
    FOREIGN KEY (dotacao_id) REFERENCES dotacoes(id)
);

CREATE TABLE IF NOT EXISTS aditivos_contrato (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contrato_id INTEGER,
    numero TEXT,
    tipo TEXT NOT NULL CHECK(tipo IN ('prazo','valor','objeto')),
    valor DECIMAL(15,2) DEFAULT 0,
    novo_vencimento DATE,
    data DATE,
    descricao TEXT,
    FOREIGN KEY (contrato_id) REFERENCES contratos(id)
);

CREATE TABLE IF NOT EXISTS empenhos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT,
    data DATE,
    tipo TEXT NOT NULL CHECK(tipo IN ('ordinario','estimativo','global')),
    dotacao_id INTEGER,
    credor_id INTEGER,
    valor DECIMAL(15,2) DEFAULT 0,
    saldo DECIMAL(15,2) DEFAULT 0,
    status TEXT NOT NULL CHECK(status IN ('ativo','cancelado','liquidado_total')),
    historico TEXT,
    FOREIGN KEY (dotacao_id) REFERENCES dotacoes(id),
    FOREIGN KEY (credor_id) REFERENCES credores(id)
);

CREATE TABLE IF NOT EXISTS liquidacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empenho_id INTEGER,
    numero TEXT,
    data DATE,
    valor DECIMAL(15,2) DEFAULT 0,
    documento_fiscal TEXT,
    historico TEXT,
    FOREIGN KEY (empenho_id) REFERENCES empenhos(id)
);

CREATE TABLE IF NOT EXISTS pagamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    liquidacao_id INTEGER,
    data DATE,
    valor DECIMAL(15,2) DEFAULT 0,
    forma_pagamento TEXT,
    ordem_bancaria TEXT,
    FOREIGN KEY (liquidacao_id) REFERENCES liquidacoes(id)
);

CREATE TABLE IF NOT EXISTS alteracoes_orcamentarias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL CHECK(tipo IN ('suplementacao','reducao','remanejamento','credito_especial','credito_extraordinario')),
    numero_decreto TEXT,
    data DATE,
    justificativa TEXT,
    valor_total DECIMAL(15,2) DEFAULT 0,
    percentual_alerta_suplementacao DECIMAL(5,2) DEFAULT 20.00
);

CREATE TABLE IF NOT EXISTS itens_alteracao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alteracao_id INTEGER,
    dotacao_origem_id INTEGER,
    dotacao_destino_id INTEGER,
    tipo_movimento TEXT NOT NULL CHECK(tipo_movimento IN ('credito','reducao')),
    valor DECIMAL(15,2) DEFAULT 0,
    FOREIGN KEY (alteracao_id) REFERENCES alteracoes_orcamentarias(id),
    FOREIGN KEY (dotacao_origem_id) REFERENCES dotacoes(id),
    FOREIGN KEY (dotacao_destino_id) REFERENCES dotacoes(id)
);

CREATE TABLE IF NOT EXISTS prestadores_saude (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    credor_id INTEGER,
    especialidade TEXT,
    registro_conselho TEXT,
    data_credenciamento DATE,
    data_validade DATE,
    situacao TEXT NOT NULL CHECK(situacao IN ('ativo','suspenso','cancelado')),
    FOREIGN KEY (credor_id) REFERENCES credores(id)
);

CREATE TABLE IF NOT EXISTS pacientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cpf TEXT,
    data_nascimento DATE,
    sexo TEXT,
    endereco TEXT,
    telefone TEXT,
    email TEXT,
    convenio TEXT,
    observacoes TEXT,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS atendimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paciente_id INTEGER,
    prestador_id INTEGER,
    data_atendimento DATE,
    tipo TEXT NOT NULL CHECK(tipo IN ('consulta','exame','procedimento','internacao')),
    descricao TEXT,
    valor DECIMAL(15,2) DEFAULT 0,
    status TEXT NOT NULL CHECK(status IN ('agendado','realizado','cancelado')),
    FOREIGN KEY (paciente_id) REFERENCES pacientes(id),
    FOREIGN KEY (prestador_id) REFERENCES prestadores_saude(id)
);

CREATE TABLE IF NOT EXISTS parametros_alerta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_alerta TEXT NOT NULL UNIQUE,
    valor_padrao DECIMAL(5,2) DEFAULT 0,
    descricao TEXT,
    ativo INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    perfil TEXT NOT NULL CHECK(perfil IN ('admin','orcamentario','financeiro','gestor','consulta')),
    orgao_id INTEGER,
    ativo INTEGER DEFAULT 1,
    FOREIGN KEY (orgao_id) REFERENCES orgaos(id)
);

CREATE TABLE IF NOT EXISTS logs_auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    tabela TEXT,
    registro_id INTEGER,
    operacao TEXT NOT NULL CHECK(operacao IN ('insert','update','delete')),
    dados_anteriores TEXT,
    dados_novos TEXT,
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
"""


def get_connection():
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript(SCHEMA)
    conn.commit()

    # Dados iniciais
    c.execute("SELECT COUNT(*) FROM exercicios_orcamentarios")
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO exercicios_orcamentarios (ano, status, data_inicio, data_fim) VALUES (?, ?, ?, ?)",
            (2026, "execucao", "2026-01-01", "2026-12-31"),
        )
        exercicio_id = c.lastrowid

        c.execute(
            "INSERT INTO orgaos (codigo, nome, sigla, ativo) VALUES (?, ?, ?, ?)",
            ("02.01", "Secretaria Municipal de Saúde", "SMS", 1),
        )
        orgao_id = c.lastrowid

        c.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, perfil, orgao_id, ativo) VALUES (?, ?, ?, ?, ?, ?)",
            ("Administrador", "admin", hashlib.sha256("admin123".encode()).hexdigest(), "admin", orgao_id, 1),
        )

        fontes = [
            ("FUNDEB", "FUNDEB", "vinculado"),
            ("SUS-CUST", "SUS - Custeio", "vinculado"),
            ("SUS-INVEST", "SUS - Investimento", "vinculado"),
            ("RO", "Recursos Ordinários", "tesouro"),
            ("EMENDAS", "Emendas Parlamentares", "vinculado"),
        ]
        fonte_ids = {}
        for cod, desc, tipo in fontes:
            c.execute(
                "INSERT INTO fontes_recurso (codigo, descricao, tipo) VALUES (?, ?, ?)",
                (cod, desc, tipo),
            )
            fonte_ids[desc] = c.lastrowid

        # Receitas reais de Luminárias (federal / estadual)
        receitas_luminarias = [
            ("00277 - PM LUMI INCREMENTO AT PRIM EMENDA COMISSAO - CUSTEIO", fonte_ids["SUS - Custeio"], 2094575.37),
            ("00272 - PM LUMI INCREMENTO TEMP CUSTEIO AT.PRIM. - CUSTEIO", fonte_ids["SUS - Custeio"], 4189150.74),
            ("00270 - PM LUMI INCREMENTO TEMP CUSTEIO AT PRIMARIA - CUSTEIO", fonte_ids["SUS - Custeio"], 6283726.11),
            ("00273 - PM LUMI INCREMENTO TEMPORARIO CUSTEIO MAC - CUSTEIO", fonte_ids["SUS - Custeio"], 8378301.48),
            ("00271 - PM LUMI INCREMENTO TEMP CUSTEIO AT.PRIM. - CUSTEIO", fonte_ids["SUS - Custeio"], 10472875.85),
            ("00247 - PM LUMI BLOCO SUS-CUSTEIO - FMS CT - CUSTEIO", fonte_ids["SUS - Custeio"], 12567450.82),
            ("00220 - PM LUMINARIAS-FOLHA PAGTO - CUSTEIO", fonte_ids["Recursos Ordinários"], 8378301.48),
            ("00065 - ICMS SAÚDE ESTADUAL - LUMINÁRIAS", fonte_ids["Recursos Ordinários"], 5000000.00),
            ("00287 - FUNDO A FUNDEB SAÚDE - LUMINÁRIAS", fonte_ids["FUNDEB"], 2094575.37),
        ]
        for desc, fonte_id, valor in receitas_luminarias:
            c.execute(
                "INSERT INTO previsao_receitas (exercicio_id, fonte_recurso_id, descricao, valor_previsto, valor_realizado, mes_competencia) VALUES (?, ?, ?, ?, ?, ?)",
                (exercicio_id, fonte_id, desc, valor, 0.0, 1),
            )

        # Naturezas de despesa padrão
        naturezas = [
            ("3.1.90.11.00", "3 - Corrente", "1 - Pessoal", "90", "11", "Vencimentos e Vantagens Fixas - Pessoal Civil"),
            ("3.1.90.91.00", "3 - Corrente", "3 - Outras Correntes", "90", "91", "Sentenças Judiciais"),
            ("3.3.90.30.00", "3 - Corrente", "3 - Outras Correntes", "90", "30", "Material de Consumo"),
            ("3.3.90.36.00", "3 - Corrente", "3 - Outras Correntes", "90", "36", "Outras Despesas Gerais"),
            ("3.3.90.39.00", "3 - Corrente", "3 - Outras Correntes", "90", "39", "Outros Serviços de Terceiros - Pessoa Jurídica"),
            ("4.4.90.51.00", "4 - Capital", "4 - Investimentos", "90", "51", "Obras e Instalações"),
            ("4.4.90.52.00", "4 - Capital", "4 - Investimentos", "90", "52", "Equipamentos e Material Permanente"),
        ]
        natureza_ids = {}
        for i, (cod, cat, grupo, mod, elem, desc) in enumerate(naturezas):
            c.execute(
                "INSERT INTO naturezas_despesa (codigo, categoria, grupo, modalidade, elemento, descricao) VALUES (?, ?, ?, ?, ?, ?)",
                (cod, cat, grupo, mod, elem, desc),
            )
            natureza_ids[i] = c.lastrowid

        # Programa e ação para SMS
        c.execute(
            "INSERT INTO programas (codigo, nome, objetivo, orgao_responsavel_id) VALUES (?, ?, ?, ?)",
            ("0001", "Saúde para Todos", "Garantir atenção integral à saúde da população", orgao_id),
        )
        programa_id = c.lastrowid

        c.execute(
            "INSERT INTO acoes (codigo, tipo, nome, produto, unidade_medida, programa_id, orgao_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("0001", "atividade", "Atendimento Ambulatorial", "Consultas médicas", "Atendimento", programa_id, orgao_id),
        )
        acao_id = c.lastrowid

        # Dotações iniciais para totalizar R$ 76.935.000,00
        dotacoes_valores = [
            (natureza_ids[0], fonte_ids["Recursos Ordinários"], 12500000.00),
            (natureza_ids[1], fonte_ids["Recursos Ordinários"], 2000000.00),
            (natureza_ids[2], fonte_ids["SUS - Custeio"], 18000000.00),
            (natureza_ids[3], fonte_ids["SUS - Custeio"], 12000000.00),
            (natureza_ids[4], fonte_ids["FUNDEB"], 15000000.00),
            (natureza_ids[5], fonte_ids["SUS - Investimento"], 10000000.00),
            (natureza_ids[6], fonte_ids["Emendas Parlamentares"], 7435000.00),
        ]
        for nat_id, fonte_id, valor in dotacoes_valores:
            c.execute(
                "INSERT INTO dotacoes (exercicio_id, orgao_id, programa_id, acao_id, natureza_id, fonte_recurso_id, valor_original, valor_atual) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (exercicio_id, orgao_id, programa_id, acao_id, nat_id, fonte_id, valor, valor),
            )

        # Parametros de alerta
        parametros = [
            ("licitacao_retirada", 20, "Alerta de retirada de licitação (%)", 1),
            ("dotacao_suplementacao", 20, "Alerta de suplementação de dotação (%)", 1),
            ("vencimento_contrato", 60, "Alerta de vencimento de contrato (dias)", 1),
            ("estoque_minimo", 10, "Alerta de estoque mínimo (%)", 1),
        ]
        for tipo, val, desc, ativo in parametros:
            c.execute(
                "INSERT INTO parametros_alerta (tipo_alerta, valor_padrao, descricao, ativo) VALUES (?, ?, ?, ?)",
                (tipo, val, desc, ativo),
            )

        conn.commit()
    conn.close()


# Generic helpers


def list_tables():
    return [
        "exercicios_orcamentarios",
        "orgaos",
        "programas",
        "acoes",
        "naturezas_despesa",
        "fontes_recurso",
        "dotacoes",
        "previsao_receitas",
        "credores",
        "licitacoes",
        "itens_licitacao",
        "ordens_compra",
        "contratos",
        "aditivos_contrato",
        "empenhos",
        "liquidacoes",
        "pagamentos",
        "alteracoes_orcamentarias",
        "itens_alteracao",
        "prestadores_saude",
        "pacientes",
        "atendimentos",
        "parametros_alerta",
        "usuarios",
        "logs_auditoria",
    ]


def dict_from_row(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def _insert(table: str, data: Dict[str, Any]) -> int:
    conn = get_connection()
    c = conn.cursor()
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
    c.execute(sql, tuple(data.values()))
    conn.commit()
    rowid = c.lastrowid
    conn.close()
    return rowid


def _get_all(table: str, order_by: str = "id") -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table} ORDER BY {order_by}")
    rows = c.fetchall()
    conn.close()
    return [dict_from_row(c, row) for row in rows]


def _get_by_id(table: str, id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table} WHERE id = ?", (id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        return None
    return dict_from_row(c, row)


def _update(table: str, id: int, data: Dict[str, Any]) -> bool:
    conn = get_connection()
    c = conn.cursor()
    sets = ", ".join([f"{k} = ?" for k in data.keys()])
    sql = f"UPDATE {table} SET {sets} WHERE id = ?"
    c.execute(sql, tuple(data.values()) + (id,))
    conn.commit()
    changed = c.rowcount
    conn.close()
    return changed > 0


def _delete(table: str, id: int) -> bool:
    conn = get_connection()
    c = conn.cursor()
    c.execute(f"DELETE FROM {table} WHERE id = ?", (id,))
    conn.commit()
    changed = c.rowcount
    conn.close()
    return changed > 0


# Exercicios
insert_exercicio = lambda d: _insert("exercicios_orcamentarios", d)
get_all_exercicios = lambda: _get_all("exercicios_orcamentarios", "ano")
get_exercicio_by_id = lambda id: _get_by_id("exercicios_orcamentarios", id)
update_exercicio = lambda id, d: _update("exercicios_orcamentarios", id, d)
delete_exercicio = lambda id: _delete("exercicios_orcamentarios", id)

# Orgaos
insert_orgao = lambda d: _insert("orgaos", d)
get_all_orgaos = lambda: _get_all("orgaos", "nome")
get_orgao_by_id = lambda id: _get_by_id("orgaos", id)
update_orgao = lambda id, d: _update("orgaos", id, d)
delete_orgao = lambda id: _delete("orgaos", id)

# Programas
insert_programa = lambda d: _insert("programas", d)
get_all_programas = lambda: _get_all("programas", "nome")
get_programa_by_id = lambda id: _get_by_id("programas", id)
update_programa = lambda id, d: _update("programas", id, d)
delete_programa = lambda id: _delete("programas", id)

# Acoes
insert_acao = lambda d: _insert("acoes", d)
get_all_acoes = lambda: _get_all("acoes", "nome")
get_acao_by_id = lambda id: _get_by_id("acoes", id)
update_acao = lambda id, d: _update("acoes", id, d)
delete_acao = lambda id: _delete("acoes", id)

# Naturezas
insert_natureza = lambda d: _insert("naturezas_despesa", d)
get_all_naturezas = lambda: _get_all("naturezas_despesa", "codigo")
get_natureza_by_id = lambda id: _get_by_id("naturezas_despesa", id)
update_natureza = lambda id, d: _update("naturezas_despesa", id, d)
delete_natureza = lambda id: _delete("naturezas_despesa", id)

# Fontes
insert_fonte = lambda d: _insert("fontes_recurso", d)
get_all_fontes = lambda: _get_all("fontes_recurso", "descricao")
get_fonte_by_id = lambda id: _get_by_id("fontes_recurso", id)
update_fonte = lambda id, d: _update("fontes_recurso", id, d)
delete_fonte = lambda id: _delete("fontes_recurso", id)

# Dotacoes
insert_dotacao = lambda d: _insert("dotacoes", d)
get_all_dotacoes = lambda: _get_all("dotacoes", "id")
get_dotacao_by_id = lambda id: _get_by_id("dotacoes", id)
update_dotacao = lambda id, d: _update("dotacoes", id, d)
delete_dotacao = lambda id: _delete("dotacoes", id)

# Previsao Receitas
insert_receita = lambda d: _insert("previsao_receitas", d)
get_all_receitas = lambda: _get_all("previsao_receitas", "id")
get_receita_by_id = lambda id: _get_by_id("previsao_receitas", id)
update_receita = lambda id, d: _update("previsao_receitas", id, d)
delete_receita = lambda id: _delete("previsao_receitas", id)

# Credores
insert_credor = lambda d: _insert("credores", d)
get_all_credores = lambda: _get_all("credores", "nome")
get_credor_by_id = lambda id: _get_by_id("credores", id)
update_credor = lambda id, d: _update("credores", id, d)
delete_credor = lambda id: _delete("credores", id)

# Licitacoes
insert_licitacao = lambda d: _insert("licitacoes", d)
get_all_licitacoes = lambda: _get_all("licitacoes", "data_criacao DESC")
get_licitacao_by_id = lambda id: _get_by_id("licitacoes", id)
update_licitacao = lambda id, d: _update("licitacoes", id, d)
delete_licitacao = lambda id: _delete("licitacoes", id)

# Itens Licitacao
insert_item_licitacao = lambda d: _insert("itens_licitacao", d)
get_all_itens_licitacao = lambda: _get_all("itens_licitacao", "id")
get_item_licitacao_by_id = lambda id: _get_by_id("itens_licitacao", id)
update_item_licitacao = lambda id, d: _update("itens_licitacao", id, d)
delete_item_licitacao = lambda id: _delete("itens_licitacao", id)

# Ordens Compra
insert_ordem_compra = lambda d: _insert("ordens_compra", d)
get_all_ordens_compra = lambda: _get_all("ordens_compra", "data DESC")
get_ordem_compra_by_id = lambda id: _get_by_id("ordens_compra", id)
update_ordem_compra = lambda id, d: _update("ordens_compra", id, d)
delete_ordem_compra = lambda id: _delete("ordens_compra", id)

# Contratos
insert_contrato = lambda d: _insert("contratos", d)
get_all_contratos = lambda: _get_all("contratos", "vigencia_fim")
get_contrato_by_id = lambda id: _get_by_id("contratos", id)
update_contrato = lambda id, d: _update("contratos", id, d)
delete_contrato = lambda id: _delete("contratos", id)

# Aditivos
insert_aditivo = lambda d: _insert("aditivos_contrato", d)
get_all_aditivos = lambda: _get_all("aditivos_contrato", "id")
get_aditivo_by_id = lambda id: _get_by_id("aditivos_contrato", id)
update_aditivo = lambda id, d: _update("aditivos_contrato", id, d)
delete_aditivo = lambda id: _delete("aditivos_contrato", id)

# Empenhos
insert_empenho = lambda d: _insert("empenhos", d)
get_all_empenhos = lambda: _get_all("empenhos", "data DESC")
get_empenho_by_id = lambda id: _get_by_id("empenhos", id)
update_empenho = lambda id, d: _update("empenhos", id, d)
delete_empenho = lambda id: _delete("empenhos", id)

# Liquidacoes
insert_liquidacao = lambda d: _insert("liquidacoes", d)
get_all_liquidacoes = lambda: _get_all("liquidacoes", "data DESC")
get_liquidacao_by_id = lambda id: _get_by_id("liquidacoes", id)
update_liquidacao = lambda id, d: _update("liquidacoes", id, d)
delete_liquidacao = lambda id: _delete("liquidacoes", id)

# Pagamentos
insert_pagamento = lambda d: _insert("pagamentos", d)
get_all_pagamentos = lambda: _get_all("pagamentos", "data DESC")
get_pagamento_by_id = lambda id: _get_by_id("pagamentos", id)
update_pagamento = lambda id, d: _update("pagamentos", id, d)
delete_pagamento = lambda id: _delete("pagamentos", id)

# Alteracoes
insert_alteracao = lambda d: _insert("alteracoes_orcamentarias", d)
get_all_alteracoes = lambda: _get_all("alteracoes_orcamentarias", "data DESC")
get_alteracao_by_id = lambda id: _get_by_id("alteracoes_orcamentarias", id)
update_alteracao = lambda id, d: _update("alteracoes_orcamentarias", id, d)
delete_alteracao = lambda id: _delete("alteracoes_orcamentarias", id)

# Itens Alteracao
insert_item_alteracao = lambda d: _insert("itens_alteracao", d)
get_all_itens_alteracao = lambda: _get_all("itens_alteracao", "id")
get_item_alteracao_by_id = lambda id: _get_by_id("itens_alteracao", id)
update_item_alteracao = lambda id, d: _update("itens_alteracao", id, d)
delete_item_alteracao = lambda id: _delete("itens_alteracao", id)

# Prestadores
insert_prestador = lambda d: _insert("prestadores_saude", d)
get_all_prestadores = lambda: _get_all("prestadores_saude", "especialidade")
get_prestador_by_id = lambda id: _get_by_id("prestadores_saude", id)
update_prestador = lambda id, d: _update("prestadores_saude", id, d)
delete_prestador = lambda id: _delete("prestadores_saude", id)

# Pacientes
insert_paciente = lambda d: _insert("pacientes", d)
get_all_pacientes = lambda: _get_all("pacientes", "nome")
get_paciente_by_id = lambda id: _get_by_id("pacientes", id)
update_paciente = lambda id, d: _update("pacientes", id, d)
delete_paciente = lambda id: _delete("pacientes", id)

# Atendimentos
insert_atendimento = lambda d: _insert("atendimentos", d)
get_all_atendimentos = lambda: _get_all("atendimentos", "data_atendimento DESC")
get_atendimento_by_id = lambda id: _get_by_id("atendimentos", id)
update_atendimento = lambda id, d: _update("atendimentos", id, d)
delete_atendimento = lambda id: _delete("atendimentos", id)

# Parametros
insert_parametro = lambda d: _insert("parametros_alerta", d)
get_all_parametros = lambda: _get_all("parametros_alerta", "tipo_alerta")
get_parametro_by_id = lambda id: _get_by_id("parametros_alerta", id)
update_parametro = lambda id, d: _update("parametros_alerta", id, d)
delete_parametro = lambda id: _delete("parametros_alerta", id)

# Usuarios
insert_usuario = lambda d: _insert("usuarios", d)
get_all_usuarios = lambda: _get_all("usuarios", "nome")
get_usuario_by_id = lambda id: _get_by_id("usuarios", id)
update_usuario = lambda id, d: _update("usuarios", id, d)
delete_usuario = lambda id: _delete("usuarios", id)


def login_usuario(email: str, senha: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM usuarios WHERE email = ? AND senha_hash = ? AND ativo = 1",
        (email, hashlib.sha256(senha.encode()).hexdigest()),
    )
    row = c.fetchone()
    conn.close()
    if row is None:
        return None
    return dict_from_row(c, row)


# Relatorios


def get_saldo_dotacao(exercicio_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT d.id, d.valor_original, d.valor_atual, d.valor_empenhado, d.valor_liquidado, d.valor_pago,
               (d.valor_atual - d.valor_empenhado) as saldo_empenho,
               (d.valor_atual - d.valor_pago) as saldo_pagar,
               o.nome as orgao, o.sigla, f.descricao as fonte, n.codigo as natureza
        FROM dotacoes d
        JOIN orgaos o ON d.orgao_id = o.id
        JOIN fontes_recurso f ON d.fonte_recurso_id = f.id
        JOIN naturezas_despesa n ON d.natureza_id = n.id
        WHERE d.exercicio_id = ?
        """,
        (exercicio_id,),
    )
    rows = c.fetchall()
    conn.close()
    return [dict_from_row(c, row) for row in rows]


def get_execucao_por_orgao(exercicio_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT o.nome as orgao, o.sigla,
               SUM(d.valor_atual) as total_dotacao,
               SUM(d.valor_empenhado) as total_empenhado,
               SUM(d.valor_liquidado) as total_liquidado,
               SUM(d.valor_pago) as total_pago
        FROM dotacoes d
        JOIN orgaos o ON d.orgao_id = o.id
        WHERE d.exercicio_id = ?
        GROUP BY o.id, o.nome, o.sigla
        """,
        (exercicio_id,),
    )
    rows = c.fetchall()
    conn.close()
    return [dict_from_row(c, row) for row in rows]


def get_ranking_despesas(exercicio_id: int, top: int = 10) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT n.codigo as natureza, n.descricao,
               SUM(d.valor_pago) as total_pago,
               SUM(d.valor_empenhado) as total_empenhado
        FROM dotacoes d
        JOIN naturezas_despesa n ON d.natureza_id = n.id
        WHERE d.exercicio_id = ?
        GROUP BY n.id, n.codigo, n.descricao
        ORDER BY total_pago DESC
        LIMIT ?
        """,
        (exercicio_id, top),
    )
    rows = c.fetchall()
    conn.close()
    return [dict_from_row(c, row) for row in rows]


def get_alerta_licitacao() -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT l.id, l.numero, l.modalidade, l.situacao, l.percentual_alerta_retirada,
               i.id as item_id, i.produto_nome, i.quantidade_total, i.quantidade_retirada, i.saldo,
               (i.quantidade_retirada / NULLIF(i.quantidade_total, 0) * 100) as percentual_retirado,
               o.nome as orgao
        FROM licitacoes l
        JOIN itens_licitacao i ON l.id = i.licitacao_id
        LEFT JOIN orgaos o ON l.orgao_id = o.id
        WHERE l.situacao IN ('em_andamento', 'homologada')
        """
    )
    rows = c.fetchall()
    conn.close()
    itens = [dict_from_row(c, row) for row in rows]
    alertas = []
    for item in itens:
        perc = item.get("percentual_retirado") or 0
        if perc >= item.get("percentual_alerta_retirada", 20):
            alertas.append(item)
    return alertas


def get_alerta_dotacao() -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT valor_padrao FROM parametros_alerta WHERE tipo_alerta = 'dotacao_suplementacao'")
    row = c.fetchone()
    perc_alerta = row[0] if row else 20

    c.execute(
        """
        SELECT d.*, o.nome as orgao, o.sigla, n.codigo as natureza
        FROM dotacoes d
        JOIN orgaos o ON d.orgao_id = o.id
        JOIN naturezas_despesa n ON d.natureza_id = n.id
        """
    )
    rows = c.fetchall()
    conn.close()
    dotacoes = [dict_from_row(c, row) for row in rows]
    alertas = []
    for d in dotacoes:
        if d.get("valor_atual", 0) > 0:
            percentual_utilizado = (d.get("valor_empenhado", 0) / d.get("valor_atual", 1)) * 100
            if percentual_utilizado >= (100 - perc_alerta):
                d["percentual_utilizado"] = percentual_utilizado
                alertas.append(d)
    return alertas


def get_visao_geral_loa(exercicio_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT d.id, e.ano, o.nome as orgao, o.sigla, p.nome as programa, a.nome as acao,
               n.codigo as natureza, n.descricao as natureza_descricao, f.descricao as fonte,
               d.valor_original, d.valor_atual, d.valor_empenhado, d.valor_liquidado, d.valor_pago,
               (d.valor_atual - d.valor_empenhado) as saldo
        FROM dotacoes d
        JOIN exercicios_orcamentarios e ON d.exercicio_id = e.id
        JOIN orgaos o ON d.orgao_id = o.id
        JOIN programas p ON d.programa_id = p.id
        JOIN acoes a ON d.acao_id = a.id
        JOIN naturezas_despesa n ON d.natureza_id = n.id
        JOIN fontes_recurso f ON d.fonte_recurso_id = f.id
        WHERE d.exercicio_id = ?
        ORDER BY d.id
        """,
        (exercicio_id,),
    )
    rows = c.fetchall()
    conn.close()
    return [dict_from_row(c, row) for row in rows]


def get_execucao_mensal(exercicio_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT strftime('%m', data) as mes, SUM(valor) as total_pago
        FROM pagamentos p
        JOIN liquidacoes l ON p.liquidacao_id = l.id
        JOIN empenhos e ON l.empenho_id = e.id
        JOIN dotacoes d ON e.dotacao_id = d.id
        WHERE d.exercicio_id = ?
        GROUP BY mes
        ORDER BY mes
        """,
        (exercicio_id,),
    )
    rows = c.fetchall()
    conn.close()
    return [dict_from_row(c, row) for row in rows]


def get_itens_por_licitacao(licitacao_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM itens_licitacao WHERE licitacao_id = ?", (licitacao_id,))
    rows = c.fetchall()
    conn.close()
    return [dict_from_row(c, row) for row in rows]


def get_ordens_por_licitacao(licitacao_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM ordens_compra WHERE licitacao_id = ?", (licitacao_id,))
    rows = c.fetchall()
    conn.close()
    return [dict_from_row(c, row) for row in rows]


def get_contratos_por_credor(credor_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM contratos WHERE credor_id = ?", (credor_id,))
    rows = c.fetchall()
    conn.close()
    return [dict_from_row(c, row) for row in rows]


def get_empenhos_por_credor(credor_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM empenhos WHERE credor_id = ?", (credor_id,))
    rows = c.fetchall()
    conn.close()
    return [dict_from_row(c, row) for row in rows]


def get_atendimentos_por_paciente(paciente_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM atendimentos WHERE paciente_id = ?", (paciente_id,))
    rows = c.fetchall()
    conn.close()
    return [dict_from_row(c, row) for row in rows]


def get_extrato_dotacao(dotacao_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        SELECT d.*, o.nome as orgao, p.nome as programa, a.nome as acao,
               n.codigo as natureza, f.descricao as fonte
        FROM dotacoes d
        JOIN orgaos o ON d.orgao_id = o.id
        JOIN programas p ON d.programa_id = p.id
        JOIN acoes a ON d.acao_id = a.id
        JOIN naturezas_despesa n ON d.natureza_id = n.id
        JOIN fontes_recurso f ON d.fonte_recurso_id = f.id
        WHERE d.id = ?
        """,
        (dotacao_id,),
    )
    row = c.fetchone()
    conn.close()
    if row is None:
        return None
    return dict_from_row(c, row)


def get_liquidacoes_por_empenho(empenho_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM liquidacoes WHERE empenho_id = ?", (empenho_id,))
    rows = c.fetchall()
    conn.close()
    return [dict_from_row(c, row) for row in rows]


def get_pagamentos_por_liquidacao(liquidacao_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM pagamentos WHERE liquidacao_id = ?", (liquidacao_id,))
    rows = c.fetchall()
    conn.close()
    return [dict_from_row(c, row) for row in rows]


def get_parametro_valor(tipo_alerta: str) -> float:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT valor_padrao FROM parametros_alerta WHERE tipo_alerta = ?", (tipo_alerta,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0


def recalcular_saldo_item_licitacao(item_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT COALESCE(SUM(quantidade), 0) FROM ordens_compra WHERE item_licitacao_id = ? AND situacao != 'cancelada'",
        (item_id,),
    )
    total = c.fetchone()[0] or 0
    c.execute("SELECT quantidade_total FROM itens_licitacao WHERE id = ?", (item_id,))
    row = c.fetchone()
    if row:
        qtd_total = row[0]
        c.execute(
            "UPDATE itens_licitacao SET quantidade_retirada = ?, saldo = ? WHERE id = ?",
            (total, qtd_total - total, item_id),
        )
        conn.commit()
    conn.close()


def recalcular_dotacao_por_empenho(dotacao_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT COALESCE(SUM(valor), 0) FROM empenhos WHERE dotacao_id = ? AND status != 'cancelado'",
        (dotacao_id,),
    )
    empenhado = c.fetchone()[0] or 0
    c.execute(
        """
        SELECT COALESCE(SUM(li.valor), 0)
        FROM liquidacoes li
        JOIN empenhos e ON li.empenho_id = e.id
        WHERE e.dotacao_id = ? AND e.status != 'cancelado'
        """,
        (dotacao_id,),
    )
    liquidado = c.fetchone()[0] or 0
    c.execute(
        """
        SELECT COALESCE(SUM(p.valor), 0)
        FROM pagamentos p
        JOIN liquidacoes li ON p.liquidacao_id = li.id
        JOIN empenhos e ON li.empenho_id = e.id
        WHERE e.dotacao_id = ? AND e.status != 'cancelado'
        """,
        (dotacao_id,),
    )
    pago = c.fetchone()[0] or 0
    c.execute(
        "UPDATE dotacoes SET valor_empenhado = ?, valor_liquidado = ?, valor_pago = ? WHERE id = ?",
        (empenhado, liquidado, pago, dotacao_id),
    )
    conn.commit()
    conn.close()


def inserir_log(usuario_id, tabela, registro_id, operacao, dados_anteriores=None, dados_novos=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO logs_auditoria (usuario_id, tabela, registro_id, operacao, dados_anteriores, dados_novos) VALUES (?, ?, ?, ?, ?, ?)",
        (
            usuario_id,
            tabela,
            registro_id,
            operacao,
            json.dumps(dados_anteriores, default=str) if dados_anteriores else None,
            json.dumps(dados_novos, default=str) if dados_novos else None,
        ),
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Banco de dados inicializado com sucesso.")
