import os
import datetime as dt
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional, List

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import (
    create_engine, Column, Integer, BigInteger, String, Text, Numeric,
    Date, DateTime, Boolean, ForeignKey, Enum, func, select, inspect, text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from sqlalchemy.exc import OperationalError, IntegrityError

# ============================================================
# CONFIGURAÇÕES INICIAIS
# ============================================================
st.set_page_config(
    page_title="MARMED Gestão em Saúde Pública",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS customizado para melhorar a aparência
st.markdown("""
<style>
    .main { background-color: #f4f6f9; }
    .stSidebar { background-color: #0a2f5c; }
    .stSidebar [data-testid="stMarkdownContainer"] p { color: #ffffff; }
    .stSidebar h1, .stSidebar h2, .stSidebar h3 { color: #ffffff; }
    .stSidebar .stSelectbox label { color: #ffffff; font-weight: 600; }
    .metric-card { background-color: #ffffff; padding: 16px; border-radius: 12px;
                   box-shadow: 0 2px 8px rgba(0,0,0,0.08); margin-bottom: 12px; }
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    h1, h2, h3 { color: #0a2f5c; }
    .stButton>button { border-radius: 8px; font-weight: 600; }
    .alert-card { background-color: #fff3cd; border-left: 5px solid #ff9800;
                  padding: 12px; border-radius: 8px; margin-bottom: 10px; }
    .danger-card { background-color: #f8d7da; border-left: 5px solid #dc3545;
                   padding: 12px; border-radius: 8px; margin-bottom: 10px; }
    .success-card { background-color: #d1e7dd; border-left: 5px solid #198754;
                    padding: 12px; border-radius: 8px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# BANCO DE DADOS (SQLAlchemy) - PostgreSQL com fallback SQLite
# ============================================================
Base = declarative_base()

DATABASE_URL = os.getenv("DATABASE_URL", None)

if DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)
        # Testa conexão
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_tipo = "PostgreSQL"
    except Exception as e:
        st.warning(f"Falha ao conectar PostgreSQL: {e}. Usando SQLite local como fallback.")
        engine = create_engine("sqlite:///marmed_local.db", echo=False, future=True)
        db_tipo = "SQLite (fallback)"
else:
    engine = create_engine("sqlite:///marmed_local.db", echo=False, future=True)
    db_tipo = "SQLite (fallback)"

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Session:
    return SessionLocal()


# ============================================================
# MODELOS
# ============================================================
class ExercicioOrcamentario(Base):
    __tablename__ = "exercicios_orcamentarios"
    id = Column(Integer, primary_key=True, index=True)
    ano = Column(Integer, unique=True, nullable=False)
    status = Column(String(20), default="Ativo")  # Ativo, Encerrado, Planejado
    loa_total = Column(Numeric(18, 2), default=Decimal("0.00"))
    created_at = Column(DateTime, default=dt.datetime.now)


class Orgao(Base):
    __tablename__ = "orgaos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    sigla = Column(String(20))
    created_at = Column(DateTime, default=dt.datetime.now)


class Programa(Base):
    __tablename__ = "programas"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), nullable=False)
    nome = Column(String(255), nullable=False)
    descricao = Column(Text)
    orgao_id = Column(Integer, ForeignKey("orgaos.id"))
    orgao = relationship("Orgao")


class Acao(Base):
    __tablename__ = "acoes"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), nullable=False)
    nome = Column(String(255), nullable=False)
    descricao = Column(Text)
    programa_id = Column(Integer, ForeignKey("programas.id"))
    programa = relationship("Programa")


class NaturezaDespesa(Base):
    __tablename__ = "naturezas_despesa"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), nullable=False)  # 3.3.90.00 etc
    categoria = Column(String(50))  # Despesas Correntes / Capital
    grupo = Column(String(100))
    elemento = Column(String(255), nullable=False)


class FonteRecurso(Base):
    __tablename__ = "fontes_recursos"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), nullable=False)
    nome = Column(String(255), nullable=False)
    tipo = Column(String(50))  # Recursos Próprios, Transferências Federais etc


class Dotacao(Base):
    __tablename__ = "dotacoes"
    id = Column(Integer, primary_key=True, index=True)
    exercicio_id = Column(Integer, ForeignKey("exercicios_orcamentarios.id"))
    orgao_id = Column(Integer, ForeignKey("orgaos.id"))
    programa_id = Column(Integer, ForeignKey("programas.id"))
    acao_id = Column(Integer, ForeignKey("acoes.id"))
    natureza_id = Column(Integer, ForeignKey("naturezas_despesa.id"))
    fonte_id = Column(Integer, ForeignKey("fontes_recursos.id"))
    valor_original = Column(Numeric(18, 2), default=Decimal("0.00"))
    valor_alteracoes = Column(Numeric(18, 2), default=Decimal("0.00"))
    valor_empenhado = Column(Numeric(18, 2), default=Decimal("0.00"))
    valor_liquidado = Column(Numeric(18, 2), default=Decimal("0.00"))
    valor_pago = Column(Numeric(18, 2), default=Decimal("0.00"))
    created_at = Column(DateTime, default=dt.datetime.now)

    exercicio = relationship("ExercicioOrcamentario")
    orgao = relationship("Orgao")
    programa = relationship("Programa")
    acao = relationship("Acao")
    natureza = relationship("NaturezaDespesa")
    fonte = relationship("FonteRecurso")

    def saldo_atual(self) -> Decimal:
        return Decimal(self.valor_original) + Decimal(self.valor_alteracoes) - Decimal(self.valor_empenhado)

    def valor_total(self) -> Decimal:
        return Decimal(self.valor_original) + Decimal(self.valor_alteracoes)


class Fornecedor(Base):
    __tablename__ = "fornecedores"
    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(2), nullable=False)  # PF ou PJ
    cpf_cnpj = Column(String(20), nullable=False, unique=True)
    nome = Column(String(255), nullable=False)
    endereco = Column(Text)
    dados_bancarios = Column(Text)
    telefone = Column(String(30))
    email = Column(String(100))
    created_at = Column(DateTime, default=dt.datetime.now)


class Licitacao(Base):
    __tablename__ = "licitacoes"
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(50), nullable=False)
    modalidade = Column(String(50), nullable=False)
    objeto = Column(Text, nullable=False)
    valor_estimado = Column(Numeric(18, 2), default=Decimal("0.00"))
    data_abertura = Column(Date)
    situacao = Column(String(30), default="Em andamento")  # Em andamento, Homologada, Fracassada, Cancelada
    dotacao_id = Column(Integer, ForeignKey("dotacoes.id"))
    created_at = Column(DateTime, default=dt.datetime.now)

    dotacao = relationship("Dotacao")


class ProdutoLicitacao(Base):
    __tablename__ = "produtos_licitacao"
    id = Column(Integer, primary_key=True, index=True)
    licitacao_id = Column(Integer, ForeignKey("licitacoes.id"))
    codigo = Column(String(30))
    descricao = Column(String(255), nullable=False)
    quantidade = Column(Numeric(18, 3), default=Decimal("0.000"))
    valor_unitario = Column(Numeric(18, 2), default=Decimal("0.00"))
    quantidade_comprada = Column(Numeric(18, 3), default=Decimal("0.000"))

    licitacao = relationship("Licitacao")

    def valor_total(self) -> Decimal:
        return Decimal(self.quantidade) * Decimal(self.valor_unitario)

    def saldo(self) -> Decimal:
        return Decimal(self.quantidade) - Decimal(self.quantidade_comprada)

    def percentual_retirada(self) -> Decimal:
        if self.quantidade == 0:
            return Decimal("0")
        return (Decimal(self.quantidade_comprada) / Decimal(self.quantidade)) * 100


class Compra(Base):
    __tablename__ = "compras"
    id = Column(Integer, primary_key=True, index=True)
    licitacao_id = Column(Integer, ForeignKey("licitacoes.id"))
    produto_id = Column(Integer, ForeignKey("produtos_licitacao.id"))
    fornecedor_id = Column(Integer, ForeignKey("fornecedores.id"))
    data = Column(Date, default=date.today)
    quantidade = Column(Numeric(18, 3), default=Decimal("0.000"))
    valor_unitario = Column(Numeric(18, 2), default=Decimal("0.00"))
    valor_total = Column(Numeric(18, 2), default=Decimal("0.00"))
    created_at = Column(DateTime, default=dt.datetime.now)

    licitacao = relationship("Licitacao")
    produto = relationship("ProdutoLicitacao")
    fornecedor = relationship("Fornecedor")


class Contrato(Base):
    __tablename__ = "contratos"
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(50), nullable=False)
    licitacao_id = Column(Integer, ForeignKey("licitacoes.id"))
    fornecedor_id = Column(Integer, ForeignKey("fornecedores.id"))
    objeto = Column(Text, nullable=False)
    data_inicio = Column(Date)
    data_fim = Column(Date)
    valor_global = Column(Numeric(18, 2), default=Decimal("0.00"))
    parcelas = Column(Integer, default=1)
    situacao = Column(String(30), default="Ativo")  # Ativo, Suspenso, Encerrado, Rescindido
    created_at = Column(DateTime, default=dt.datetime.now)

    licitacao = relationship("Licitacao")
    fornecedor = relationship("Fornecedor")


class Aditivo(Base):
    __tablename__ = "aditivos"
    id = Column(Integer, primary_key=True, index=True)
    contrato_id = Column(Integer, ForeignKey("contratos.id"))
    tipo = Column(String(50))  # Prazo, Valor, Ambos
    novo_valor_global = Column(Numeric(18, 2), nullable=True)
    nova_data_fim = Column(Date, nullable=True)
    motivo = Column(Text)
    created_at = Column(DateTime, default=dt.datetime.now)

    contrato = relationship("Contrato")


class MovimentacaoOrcamentaria(Base):
    __tablename__ = "movimentacoes_orcamentarias"
    id = Column(Integer, primary_key=True, index=True)
    dotacao_id = Column(Integer, ForeignKey("dotacoes.id"))
    tipo = Column(String(30), nullable=False)  # Empenho, Liquidacao, Pagamento, Suplementacao, Anulacao
    numero_documento = Column(String(50))
    data = Column(Date, default=date.today)
    valor = Column(Numeric(18, 2), default=Decimal("0.00"))
    historico = Column(Text)
    created_at = Column(DateTime, default=dt.datetime.now)

    dotacao = relationship("Dotacao")


# Criação das tabelas
Base.metadata.create_all(bind=engine)


# ============================================================
# DADOS INICIAIS (SEMEAR)
# ============================================================
def semear_dados():
    db = get_db()
    try:
        # Exercício
        if not db.query(ExercicioOrcamentario).filter_by(ano=2026).first():
            ex = ExercicioOrcamentario(ano=2026, status="Ativo", loa_total=Decimal("76935000.00"))
            db.add(ex)
            db.commit()
        ex = db.query(ExercicioOrcamentario).filter_by(ano=2026).first()

        # Órgãos
        orgaos_nomes = [
            ("Secretaria Municipal de Saúde", "SMS"),
            ("Secretaria Municipal de Educação", "SME"),
            ("Secretaria Municipal de Administração", "SMA"),
            ("Secretaria Municipal de Transporte", "SMT"),
            ("Secretaria Municipal de Obras", "SMO"),
            ("Secretaria Municipal de Meio Ambiente", "SMMA"),
        ]
        for nome, sigla in orgaos_nomes:
            if not db.query(Orgao).filter_by(nome=nome).first():
                db.add(Orgao(nome=nome, sigla=sigla))
        db.commit()

        # Programas e Ações
        if not db.query(Programa).first():
            db.add(Programa(codigo="1001", nome="Saúde para Todos", descricao="Ações de atenção básica e média complexidade", orgao_id=1))
            db.add(Programa(codigo="2001", nome="Educação de Qualidade", descricao="Manutenção e melhoria da rede escolar", orgao_id=2))
            db.add(Programa(codigo="3001", nome="Gestão Administrativa", descricao="Administração geral do município", orgao_id=3))
            db.add(Programa(codigo="4001", nome="Mobilidade Urbana", descricao="Transporte e mobilidade", orgao_id=4))
            db.add(Programa(codigo="5001", nome="Infraestrutura", descricao="Obras e pavimentação", orgao_id=5))
            db.add(Programa(codigo="6001", nome="Sustentabilidade", descricao="Proteção ambiental e sustentabilidade", orgao_id=6))
            db.commit()

        if not db.query(Acao).first():
            db.add(Acao(codigo="1001.01", nome="Atenção Básica", descricao="Manutenção de UBS e equipes", programa_id=1))
            db.add(Acao(codigo="1001.02", nome="Medicamentos e Insumos", descricao="Aquisição de medicamentos", programa_id=1))
            db.add(Acao(codigo="2001.01", nome="Material Escolar", descricao="Distribuição de material didático", programa_id=2))
            db.add(Acao(codigo="3001.01", nome="Serviços Contínuos", descricao="Serviços terceirizados", programa_id=3))
            db.add(Acao(codigo="5001.01", nome="Pavimentação", descricao="Obras de pavimentação", programa_id=5))
            db.commit()

        # Naturezas de Despesa
        if not db.query(NaturezaDespesa).first():
            naturezas = [
                ("3.1.90.00", "Despesas Correntes", "Pessoal e Encargos Sociais", "Vencimentos e Vantagens Fixas - Pessoal Civil"),
                ("3.3.90.00", "Despesas Correntes", "Outras Despesas Correntes", "Outras Despesas Correntes"),
                ("3.3.90.30", "Despesas Correntes", "Outras Despesas Correntes", "Material de Consumo"),
                ("3.3.90.36", "Despesas Correntes", "Outras Despesas Correntes", "Serviços de Terceiros - Pessoa Física"),
                ("3.3.90.37", "Despesas Correntes", "Outras Despesas Correntes", "Serviços de Terceiros - Pessoa Jurídica"),
                ("3.3.90.39", "Despesas Correntes", "Outras Despesas Correntes", "Outros Serviços de Terceiros"),
                ("3.3.90.52", "Despesas Correntes", "Outras Despesas Correntes", "Material de Distribuição Gratuita"),
                ("4.4.90.00", "Despesas de Capital", "Investimentos", "Outras Despesas de Capital"),
                ("4.4.90.20", "Despesas de Capital", "Investimentos", "Equipamentos e Material Permanente"),
                ("4.4.90.52", "Despesas de Capital", "Investimentos", "Obras e Instalações"),
            ]
            for codigo, categoria, grupo, elemento in naturezas:
                db.add(NaturezaDespesa(codigo=codigo, categoria=categoria, grupo=grupo, elemento=elemento))
            db.commit()

        # Fontes de Recursos
        if not db.query(FonteRecurso).first():
            fontes = [
                ("100", "Recursos Ordinários", "Recursos Próprios"),
                ("101", "Transferências do Fundo de Saúde", "Transferências Federais"),
                ("150", "Transferências do FUNDEB", "Transferências Federais"),
                ("200", "Outras Transferências Federais", "Transferências Federais"),
            ]
            for codigo, nome, tipo in fontes:
                db.add(FonteRecurso(codigo=codigo, nome=nome, tipo=tipo))
            db.commit()

        # Fornecedores
        if not db.query(Fornecedor).first():
            fornecedores = [
                ("PJ", "12.345.678/0001-90", "Distribuidora Médica Sul LTDA", "Rua A, 100, Luminárias-MG", "Banco do Brasil, Ag 1234, CC 56789-0", "(35) 3333-1001", "sul@medica.com"),
                ("PJ", "98.765.432/0001-10", "Pavimentadora Luminárias S.A.", "Av. B, 200, Luminárias-MG", "Itaú, Ag 4321, CC 98765-4", "(35) 3333-1002", "contato@pavimenta.com"),
                ("PF", "123.456.789-00", "João Medicamentos ME", "Rua C, 300, Luminárias-MG", "Caixa Econômica, Ag 0001, CC 11122-3", "(35) 3333-1003", "joao@med.com"),
                ("PJ", "11.222.333/0001-44", "Educação Material Escolar EIRELI", "Rua D, 400, Luminárias-MG", "Santander, Ag 1111, CC 22222-2", "(35) 3333-1004", "edu@material.com"),
            ]
            for tipo, cpf_cnpj, nome, end, banco, tel, email in fornecedores:
                db.add(Fornecedor(tipo=tipo, cpf_cnpj=cpf_cnpj, nome=nome, endereco=end, dados_bancarios=banco, telefone=tel, email=email))
            db.commit()

        # Dotações
        if not db.query(Dotacao).first():
            # Distribuição proporcional do orçamento por órgão (saúde recebe maior parte)
            distribuicao = [
                (1, 1, 1, 1, 3, 30000000.00),   # Saúde - Atenção Básica - Pessoal
                (1, 1, 2, 3, 1, 15000000.00),   # Saúde - Medicamentos - Material de consumo
                (1, 1, 2, 9, 1, 3500000.00),    # Saúde - Medicamentos - Outras DC
                (2, 2, 3, 7, 3, 5000000.00),    # Educação - Material escolar - Mat distribuição
                (3, 3, 4, 6, 1, 3000000.00),    # Administração - serviços - mat consumo
                (5, 5, 5, 8, 1, 12000000.00),   # Obras - pavimentação - obras
                (4, 4, 4, 4, 1, 2000000.00),    # Transporte - serviços PF
                (6, 6, 4, 6, 1, 1500000.00),    # Meio Ambiente - serviços - mat consumo
                (3, 3, 4, 7, 1, 1500000.00),    # Administração - serviços - mat distribuição
                (5, 5, 5, 10, 1, 1000000.00),   # Obras - pavimentação - equipamentos
                (1, 1, 1, 2, 1, 1500000.00),    # Saúde - Atenção básica - Outras DC
                (2, 2, 3, 6, 3, 1000000.00),    # Educação - Material escolar - mat consumo
            ]
            for orgao_id, prog_id, acao_id, nat_id, fonte_id, valor in distribuicao:
                db.add(Dotacao(
                    exercicio_id=ex.id,
                    orgao_id=orgao_id,
                    programa_id=prog_id,
                    acao_id=acao_id,
                    natureza_id=nat_id,
                    fonte_id=fonte_id,
                    valor_original=Decimal(str(valor)),
                    valor_alteracoes=Decimal("0.00"),
                    valor_empenhado=Decimal("0.00"),
                    valor_liquidado=Decimal("0.00"),
                    valor_pago=Decimal("0.00"),
                ))
            db.commit()

        # Licitações
        if not db.query(Licitacao).first():
            licitacoes = [
                ("001/2026", "Pregão", "Aquisição de medicamentos e material médico-hospitalar", 15000000.00, "2026-02-15", 2),
                ("002/2026", "Concorrência", "Pavimentação asfáltica de vias urbanas", 12000000.00, "2026-03-10", 8),
                ("003/2026", "Pregão", "Material escolar e didático", 5000000.00, "2026-02-28", 4),
                ("004/2026", "Dispensa", "Serviços de manutenção de equipamentos de saúde", 300000.00, "2026-01-20", 2),
                ("005/2026", "Tomada de Preços", "Aquisição de combustível e lubrificantes", 1500000.00, "2026-04-05", 5),
            ]
            for numero, mod, obj, valor, data, dotacao_id in licitacoes:
                db.add(Licitacao(numero=numero, modalidade=mod, objeto=obj, valor_estimado=Decimal(str(valor)),
                                 data_abertura=date.fromisoformat(data), situacao="Homologada", dotacao_id=dotacao_id))
            db.commit()

        # Produtos das Licitações
        if not db.query(ProdutoLicitacao).first():
            produtos = [
                (1, "MED-001", "Paracetamol 500mg c/ 20 cp", 500000, 2.50, 0),
                (1, "MED-002", "Dipirona Sódica 1g ampola", 100000, 3.20, 0),
                (1, "MAT-001", "Luva de procedimento cx c/ 100", 20000, 35.00, 0),
                (2, "OB-001", "Serviço de pavimentação asfáltica m²", 40000, 300.00, 0),
                (3, "ESC-001", "Kit material escolar básico", 25000, 200.00, 0),
                (4, "MAN-001", "Manutenção preventiva equipamento médico", 50, 6000.00, 0),
                (5, "COM-001", "Gasolina comum litro", 300000, 5.00, 0),
            ]
            for lic_id, cod, desc, qtd, unit, comprada in produtos:
                db.add(ProdutoLicitacao(licitacao_id=lic_id, codigo=cod, descricao=desc,
                                        quantidade=Decimal(str(qtd)), valor_unitario=Decimal(str(unit)),
                                        quantidade_comprada=Decimal(str(comprada))))
            db.commit()

        # Contratos
        if not db.query(Contrato).first():
            contratos = [
                ("001/2026", 1, 1, "Fornecimento de medicamentos", "2026-03-01", "2026-12-31", 8000000.00, 10, "Ativo"),
                ("002/2026", 2, 2, "Pavimentação asfáltica", "2026-04-01", "2026-11-30", 12000000.00, 8, "Ativo"),
                ("003/2026", 3, 4, "Fornecimento de material escolar", "2026-03-15", "2026-11-15", 4500000.00, 6, "Ativo"),
                ("004/2026", 4, 3, "Manutenção de equipamentos", "2026-02-01", "2026-12-31", 300000.00, 12, "Ativo"),
            ]
            for numero, lic_id, forn_id, obj, inicio, fim, valor, parc, situ in contratos:
                db.add(Contrato(numero=numero, licitacao_id=lic_id, fornecedor_id=forn_id, objeto=obj,
                                data_inicio=date.fromisoformat(inicio), data_fim=date.fromisoformat(fim),
                                valor_global=Decimal(str(valor)), parcelas=parc, situacao=situ))
            db.commit()

        # Empenhos iniciais (exemplo)
        if not db.query(MovimentacaoOrcamentaria).first():
            movs = [
                (2, "Empenho", "EMP-001/2026", "2026-03-05", 1500000.00, "Empenho parcial contrato 001/2026 - medicamentos"),
                (8, "Empenho", "EMP-002/2026", "2026-04-10", 3000000.00, "Empenho pavimentação contrato 002/2026"),
                (4, "Empenho", "EMP-003/2026", "2026-03-20", 1500000.00, "Empenho material escolar contrato 003/2026"),
                (2, "Liquidacao", "LIQ-001/2026", "2026-03-25", 750000.00, "Liquidação parcial medicamentos"),
                (8, "Liquidacao", "LIQ-002/2026", "2026-04-20", 1000000.00, "Liquidação parcial pavimentação"),
                (2, "Pagamento", "PAG-001/2026", "2026-03-30", 750000.00, "Pagamento medicamentos"),
                (8, "Pagamento", "PAG-002/2026", "2026-04-25", 1000000.00, "Pagamento pavimentação"),
            ]
            for dot_id, tipo, num, data, valor, hist in movs:
                db.add(MovimentacaoOrcamentaria(dotacao_id=dot_id, tipo=tipo, numero_documento=num,
                                                data=date.fromisoformat(data), valor=Decimal(str(valor)), historico=hist))
            db.commit()
            # Atualiza dotacoes
            for dot_id, tipo, num, data, valor, hist in movs:
                dot = db.query(Dotacao).get(dot_id)
                if tipo == "Empenho":
                    dot.valor_empenhado += Decimal(str(valor))
                elif tipo == "Liquidacao":
                    dot.valor_liquidado += Decimal(str(valor))
                elif tipo == "Pagamento":
                    dot.valor_pago += Decimal(str(valor))
                elif tipo == "Suplementacao":
                    dot.valor_alteracoes += Decimal(str(valor))
                elif tipo == "Anulacao":
                    dot.valor_empenhado -= Decimal(str(valor))
            db.commit()

        st.success("Dados de exemplo carregados com sucesso para Luminárias - MG / 2026!")
    except Exception as e:
        db.rollback()
        st.error(f"Erro ao semear dados: {e}")
    finally:
        db.close()


# ============================================================
# ESTADO DA SESSÃO (configurações de alertas)
# ============================================================
if "alerta_retirada" not in st.session_state:
    st.session_state["alerta_retirada"] = 20.0
if "alerta_suplementacao" not in st.session_state:
    st.session_state["alerta_suplementacao"] = 20.0
if "alerta_vencimento_dias" not in st.session_state:
    st.session_state["alerta_vencimento_dias"] = 30


# ============================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================
def format_currency(val):
    try:
        return f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def get_df_from_query(query, db):
    try:
        return pd.read_sql(query.statement, db.bind)
    except Exception:
        return pd.DataFrame()


def get_loa_total(db: Session) -> Decimal:
    ex = db.query(ExercicioOrcamentario).filter_by(ano=2026).first()
    if ex:
        return ex.loa_total
    return sum_dotacoes(db)


def sum_dotacoes(db: Session) -> Decimal:
    total = db.query(func.coalesce(func.sum(Dotacao.valor_original + Dotacao.valor_alteracoes), 0)).scalar()
    return Decimal(total or 0)


def total_empenhado(db: Session) -> Decimal:
    total = db.query(func.coalesce(func.sum(MovimentacaoOrcamentaria.valor), 0)).filter(MovimentacaoOrcamentaria.tipo == "Empenho").scalar()
    return Decimal(total or 0)


def total_pago(db: Session) -> Decimal:
    total = db.query(func.coalesce(func.sum(MovimentacaoOrcamentaria.valor), 0)).filter(MovimentacaoOrcamentaria.tipo == "Pagamento").scalar()
    return Decimal(total or 0)


def saldo_disponivel(db: Session) -> Decimal:
    return get_loa_total(db) - total_empenhado(db)


def total_licitacoes(db: Session) -> int:
    return db.query(Licitacao).count()


def total_contratos(db: Session) -> int:
    return db.query(Contrato).count()


# ============================================================
# MÓDULO: DASHBOARD
# ============================================================
def pagina_dashboard():
    st.title("🏥 MARMED Gestão em Saúde Pública")
    st.subheader("Página Inicial - Dashboard")
    st.caption(f"Banco de dados: {db_tipo}")

    db = get_db()
    try:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("<<div class='metric-card'>" +
                        f"<<h3 style='margin:0'>{format_currency(get_loa_total(db))}</h3>" +
                        "<<p style='margin:0;color:#555'>Orçamento Total LOA 2026</p></div>", unsafe_allow_html=True)
        with col2:
            st.markdown("<<div class='metric-card'>" +
                        f"<<h3 style='margin:0'>{total_licitacoes(db)}</h3>" +
                        "<<p style='margin:0;color:#555'>Total de Licitações</p></div>", unsafe_allow_html=True)
        with col3:
            st.markdown("<<div class='metric-card'>" +
                        f"<<h3 style='margin:0'>{total_contratos(db)}</h3>" +
                        "<<p style='margin:0;color:#555'>Total de Contratos</p></div>", unsafe_allow_html=True)
        with col4:
            st.markdown("<<div class='metric-card'>" +
                        f"<<h3 style='margin:0'>{format_currency(saldo_disponivel(db))}</h3>" +
                        "<<p style='margin:0;color:#555'>Saldo Disponível</p></div>", unsafe_allow_html=True)

        st.markdown("---")

        # Gastos por Secretaria
        query_gastos = db.query(Orgao.nome.label("Secretaria"),
                                func.coalesce(func.sum(MovimentacaoOrcamentaria.valor), 0).label("Total_Empenhado")). \
            outerjoin(Dotacao, Dotacao.orgao_id == Orgao.id). \
            outerjoin(MovimentacaoOrcamentaria, (MovimentacaoOrcamentaria.dotacao_id == Dotacao.id) & (MovimentacaoOrcamentaria.tipo == "Empenho")). \
            group_by(Orgao.nome)
        df_gastos = get_df_from_query(query_gastos, db)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Gastos por Secretaria")
            if not df_gastos.empty:
                fig1 = px.bar(df_gastos, x="Secretaria", y="Total_Empenhado",
                              color="Secretaria", text_auto=".2s",
                              title="Empenhos por Secretaria (R$)")
                fig1.update_layout(showlegend=False)
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("Sem dados de empenho por secretaria.")

        with col2:
            st.markdown("#### Execução Orçamentária")
            loa = float(get_loa_total(db))
            empenhado = float(total_empenhado(db))
            liquidado = float(total_liquidado := db.query(func.coalesce(func.sum(MovimentacaoOrcamentaria.valor), 0)).filter(MovimentacaoOrcamentaria.tipo == "Liquidacao").scalar() or 0)
            pago = float(total_pago(db))
            saldo = loa - empenhado

            fig2 = go.Figure()
            fig2.add_trace(go.Bar(name="Empenhado", x=["Orçamento"], y=[empenhado], marker_color="#0a2f5c"))
            fig2.add_trace(go.Bar(name="Liquidado", x=["Orçamento"], y=[liquidado], marker_color="#17a2b8"))
            fig2.add_trace(go.Bar(name="Pago", x=["Orçamento"], y=[pago], marker_color="#198754"))
            fig2.add_trace(go.Bar(name="Saldo", x=["Orçamento"], y=[saldo], marker_color="#adb5bd"))
            fig2.update_layout(barmode="group", title="Resumo da Execução Orçamentária")
            st.plotly_chart(fig2, use_container_width=True)

        # Últimas movimentações
        st.markdown("#### Últimas Movimentações")
        query_movs = db.query(MovimentacaoOrcamentaria).order_by(MovimentacaoOrcamentaria.data.desc()).limit(10)
        df_movs = get_df_from_query(query_movs, db)
        if not df_movs.empty:
            df_movs["valor"] = df_movs["valor"].apply(format_currency)
            st.dataframe(df_movs, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma movimentação registrada.")

    finally:
        db.close()


# ============================================================
# MÓDULO: LOA
# ============================================================
def pagina_loa():
    st.title("📊 Módulo LOA")
    st.subheader("Lei Orçamentária Anual")
    db = get_db()
    try:
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "Exercício", "Órgãos", "Programas/Ações", "Naturezas", "Fontes", "Dotações", "Visão Geral"
        ])

        # Exercício
        with tab1:
            st.markdown("#### Exercício Orçamentário")
            ex = db.query(ExercicioOrcamentario).filter_by(ano=2026).first()
            if ex:
                st.write(f"Ano: {ex.ano}")
                st.write(f"Status: {ex.status}")
                st.write(f"LOA Total: {format_currency(ex.loa_total)}")
            else:
                st.warning("Nenhum exercício cadastrado. Carregue dados de exemplo.")

        # Órgãos
        with tab2:
            st.markdown("#### Órgãos / Secretarias")
            with st.expander("Novo Órgão"):
                with st.form("form_orgao"):
                    nome = st.text_input("Nome")
                    sigla = st.text_input("Sigla")
                    if st.form_submit_button("Salvar"):
                        db.add(Orgao(nome=nome, sigla=sigla))
                        db.commit()
                        st.success("Órgão salvo!")
            orgaos = db.query(Orgao).all()
            st.dataframe(pd.DataFrame([{"ID": o.id, "Nome": o.nome, "Sigla": o.sigla} for o in orgaos]), use_container_width=True, hide_index=True)

        # Programas e Ações
        with tab3:
            st.markdown("#### Programas")
            progs = db.query(Programa).all()
            st.dataframe(pd.DataFrame([{"ID": p.id, "Código": p.codigo, "Nome": p.nome, "Órgão": p.orgao.nome if p.orgao else ""} for p in progs]), use_container_width=True, hide_index=True)
            st.markdown("#### Ações")
            acoes = db.query(Acao).all()
            st.dataframe(pd.DataFrame([{"ID": a.id, "Código": a.codigo, "Nome": a.nome, "Programa": a.programa.nome if a.programa else ""} for a in acoes]), use_container_width=True, hide_index=True)

        # Naturezas
        with tab4:
            st.markdown("#### Naturezas de Despesa")
            nats = db.query(NaturezaDespesa).all()
            st.dataframe(pd.DataFrame([{"ID": n.id, "Código": n.codigo, "Categoria": n.categoria, "Grupo": n.grupo, "Elemento": n.elemento} for n in nats]), use_container_width=True, hide_index=True)

        # Fontes
        with tab5:
            st.markdown("#### Fontes de Recurso")
            fontes = db.query(FonteRecurso).all()
            st.dataframe(pd.DataFrame([{"ID": f.id, "Código": f.codigo, "Nome": f.nome, "Tipo": f.tipo} for f in fontes]), use_container_width=True, hide_index=True)

        # Dotações
        with tab6:
            st.markdown("#### Dotações Orçamentárias")
            with st.expander("Nova Dotação"):
                with st.form("form_dotacao"):
                    ex = db.query(ExercicioOrcamentario).filter_by(ano=2026).first()
                    orgaos = db.query(Orgao).all()
                    progs = db.query(Programa).all()
                    acoes = db.query(Acao).all()
                    nats = db.query(NaturezaDespesa).all()
                    fontes = db.query(FonteRecurso).all()
                    org_sel = st.selectbox("Órgão", orgaos, format_func=lambda o: o.nome)
                    prog_sel = st.selectbox("Programa", progs, format_func=lambda p: f"{p.codigo} - {p.nome}")
                    acao_sel = st.selectbox("Ação", acoes, format_func=lambda a: f"{a.codigo} - {a.nome}")
                    nat_sel = st.selectbox("Natureza", nats, format_func=lambda n: f"{n.codigo} - {n.elemento}")
                    fonte_sel = st.selectbox("Fonte", fontes, format_func=lambda f: f"{f.codigo} - {f.nome}")
                    valor = st.number_input("Valor Original", min_value=0.0, step=1000.0)
                    if st.form_submit_button("Salvar Dotação"):
                        db.add(Dotacao(
                            exercicio_id=ex.id if ex else 1,
                            orgao_id=org_sel.id, programa_id=prog_sel.id, acao_id=acao_sel.id,
                            natureza_id=nat_sel.id, fonte_id=fonte_sel.id,
                            valor_original=Decimal(str(valor))
                        ))
                        db.commit()
                        st.success("Dotação salva!")

            dotacoes = db.query(Dotacao).all()
            data_dotacoes = []
            for d in dotacoes:
                data_dotacoes.append({
                    "ID": d.id,
                    "Exercício": d.exercicio.ano if d.exercicio else "",
                    "Órgão": d.orgao.nome if d.orgao else "",
                    "Programa": d.programa.nome if d.programa else "",
                    "Ação": d.acao.nome if d.acao else "",
                    "Natureza": d.natureza.codigo if d.natureza else "",
                    "Fonte": d.fonte.codigo if d.fonte else "",
                    "Valor Original": format_currency(d.valor_original),
                    "Alterações": format_currency(d.valor_alteracoes),
                    "Empenhado": format_currency(d.valor_empenhado),
                    "Saldo Atual": format_currency(d.saldo_atual()),
                })
            st.dataframe(pd.DataFrame(data_dotacoes), use_container_width=True, hide_index=True)

        # Visão Geral
        with tab7:
            st.markdown("#### Visão Geral da LOA")
            st.write(f"Total de Dotações: {len(dotacoes)}")
            st.write(f"Total Orçado: {format_currency(sum_dotacoes(db))}")
            st.write(f"Total Empenhado: {format_currency(total_empenhado(db))}")
            st.write(f"Saldo Disponível: {format_currency(saldo_disponivel(db))}")

    finally:
        db.close()


# ============================================================
# MÓDULO: LICITAÇÕES
# ============================================================
def pagina_licitacoes():
    st.title("📑 Módulo de Licitações")
    db = get_db()
    try:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("#### Cadastro de Licitação")
            with st.form("form_licitacao"):
                dotacoes = db.query(Dotacao).all()
                numero = st.text_input("Número da Licitação")
                modalidade = st.selectbox("Modalidade", ["Pregão", "Concorrência", "Tomada de Preços", "Convite", "Dispensa", "Inexigibilidade"])
                objeto = st.text_area("Objeto")
                valor_estimado = st.number_input("Valor Estimado", min_value=0.0, step=1000.0)
                data_abertura = st.date_input("Data de Abertura", value=date.today())
                situacao = st.selectbox("Situação", ["Em andamento", "Homologada", "Fracassada", "Cancelada"])
                dot_sel = st.selectbox("Dotação Orçamentária", dotacoes, format_func=lambda d: f"{d.id} - {d.orgao.nome} - {d.acao.nome} ({format_currency(d.saldo_atual())})")
                if st.form_submit_button("Salvar Licitação"):
                    db.add(Licitacao(numero=numero, modalidade=modalidade, objeto=objeto,
                                     valor_estimado=Decimal(str(valor_estimado)), data_abertura=data_abertura,
                                     situacao=situacao, dotacao_id=dot_sel.id))
                    db.commit()
                    st.success("Licitação salva!")

        with col2:
            st.markdown("#### Percentual de Alerta de Retirada")
            st.session_state["alerta_retirada"] = st.slider("Alertar quando retirada atingir (%)", 0, 100,
                                                            int(st.session_state["alerta_retirada"]))
            st.info(f"Alerta configurado para {st.session_state['alerta_retirada']}%")

        st.markdown("---")
        st.markdown("#### Licitações Cadastradas")
        licitacoes = db.query(Licitacao).all()
        data_lic = []
        for l in licitacoes:
            data_lic.append({
                "ID": l.id,
                "Número": l.numero,
                "Modalidade": l.modalidade,
                "Objeto": l.objeto,
                "Valor Estimado": format_currency(l.valor_estimado),
                "Data Abertura": l.data_abertura,
                "Situação": l.situacao,
                "Dotação": f"{l.dotacao.id}" if l.dotacao else "",
            })
        st.dataframe(pd.DataFrame(data_lic), use_container_width=True, hide_index=True)

        # Produtos
        st.markdown("#### Produtos da Licitação")
        lic_sel = st.selectbox("Selecione uma Licitação", licitacoes, format_func=lambda l: f"{l.numero} - {l.objeto[:40]}...")
        if lic_sel:
            with st.expander("Novo Produto"):
                with st.form("form_produto"):
                    cod = st.text_input("Código")
                    desc = st.text_input("Descrição")
                    qtd = st.number_input("Quantidade", min_value=0.0, step=1.0)
                    unit = st.number_input("Valor Unitário", min_value=0.0, step=0.01)
                    if st.form_submit_button("Salvar Produto"):
                        db.add(ProdutoLicitacao(licitacao_id=lic_sel.id, codigo=cod, descricao=desc,
                                                quantidade=Decimal(str(qtd)), valor_unitario=Decimal(str(unit))))
                        db.commit()
                        st.success("Produto salvo!")

            produtos = db.query(ProdutoLicitacao).filter_by(licitacao_id=lic_sel.id).all()
            data_prod = []
            for p in produtos:
                pct = p.percentual_retirada()
                alerta = "🔴" if pct >= Decimal(st.session_state["alerta_retirada"]) else "🟢"
                data_prod.append({
                    "ID": p.id,
                    "Código": p.codigo,
                    "Descrição": p.descricao,
                    "Quantidade": p.quantidade,
                    "Valor Unitário": format_currency(p.valor_unitario),
                    "Valor Total": format_currency(p.valor_total()),
                    "Comprada": p.quantidade_comprada,
                    "Saldo": p.saldo(),
                    "% Retirada": f"{pct:.2f}%",
                    "Status": alerta,
                })
            st.dataframe(pd.DataFrame(data_prod), use_container_width=True, hide_index=True)

    finally:
        db.close()


# ============================================================
# MÓDULO: COMPRAS / ORDENS DE COMPRA
# ============================================================
def pagina_compras():
    st.title("🛒 Módulo de Compras / Ordens de Compra")
    db = get_db()
    try:
        st.markdown("#### Registrar Compra")
        with st.form("form_compra"):
            licitacoes = db.query(Licitacao).filter_by(situacao="Homologada").all()
            fornecedores = db.query(Fornecedor).all()
            lic_sel = st.selectbox("Licitação", licitacoes, format_func=lambda l: f"{l.numero} - {l.objeto[:40]}...")
            produtos = []
            if lic_sel:
                produtos = db.query(ProdutoLicitacao).filter_by(licitacao_id=lic_sel.id).all()
            prod_sel = st.selectbox("Produto", produtos, format_func=lambda p: f"{p.codigo} - {p.descricao} (saldo: {p.saldo()})")
            forn_sel = st.selectbox("Fornecedor", fornecedores, format_func=lambda f: f"{f.nome} ({f.cpf_cnpj})")
            data = st.date_input("Data", value=date.today())
            qtd = st.number_input("Quantidade", min_value=0.0, step=1.0)
            unit = st.number_input("Valor Unitário", min_value=0.0, step=0.01)
            if st.form_submit_button("Registrar Compra"):
                if prod_sel and qtd <= prod_sel.saldo():
                    total = Decimal(str(qtd)) * Decimal(str(unit))
                    db.add(Compra(licitacao_id=lic_sel.id, produto_id=prod_sel.id, fornecedor_id=forn_sel.id,
                                  data=data, quantidade=Decimal(str(qtd)), valor_unitario=Decimal(str(unit)),
                                  valor_total=total))
                    prod_sel.quantidade_comprada += Decimal(str(qtd))
                    db.commit()
                    st.success("Compra registrada e saldo da licitação atualizado!")
                else:
                    st.error("Quantidade comprada excede o saldo disponível do produto.")

        st.markdown("---")
        st.markdown("#### Histórico de Compras")
        compras = db.query(Compra).order_by(Compra.data.desc()).all()
        data_comp = []
        for c in compras:
            data_comp.append({
                "ID": c.id,
                "Licitação": c.licitacao.numero if c.licitacao else "",
                "Produto": c.produto.descricao if c.produto else "",
                "Fornecedor": c.fornecedor.nome if c.fornecedor else "",
                "Data": c.data,
                "Quantidade": c.quantidade,
                "Valor Unitário": format_currency(c.valor_unitario),
                "Valor Total": format_currency(c.valor_total),
            })
        st.dataframe(pd.DataFrame(data_comp), use_container_width=True, hide_index=True)

        # Compras por produto
        st.markdown("#### Histórico por Produto")
        produtos_todos = db.query(ProdutoLicitacao).all()
        prod_filtro = st.selectbox("Produto", produtos_todos, format_func=lambda p: f"{p.codigo} - {p.descricao}")
        if prod_filtro:
            comp_prod = db.query(Compra).filter_by(produto_id=prod_filtro.id).order_by(Compra.data.desc()).all()
            st.dataframe(pd.DataFrame([{
                "ID": c.id, "Fornecedor": c.fornecedor.nome, "Data": c.data, "Quantidade": c.quantidade,
                "Valor Unitário": format_currency(c.valor_unitario), "Valor Total": format_currency(c.valor_total)
            } for c in comp_prod]), use_container_width=True, hide_index=True)

    finally:
        db.close()


# ============================================================
# MÓDULO: CONTRATOS
# ============================================================
def pagina_contratos():
    st.title("📜 Módulo de Contratos")
    db = get_db()
    try:
        st.markdown("#### Cadastro de Contrato")
        with st.form("form_contrato"):
            licitacoes = db.query(Licitacao).filter_by(situacao="Homologada").all()
            fornecedores = db.query(Fornecedor).all()
            numero = st.text_input("Número do Contrato")
            lic_sel = st.selectbox("Licitação", licitacoes, format_func=lambda l: f"{l.numero} - {l.objeto[:40]}...")
            forn_sel = st.selectbox("Fornecedor / Credor", fornecedores, format_func=lambda f: f"{f.nome} ({f.cpf_cnpj})")
            objeto = st.text_area("Objeto")
            inicio = st.date_input("Início", value=date.today())
            fim = st.date_input("Fim", value=date.today() + timedelta(days=180))
            valor_global = st.number_input("Valor Global", min_value=0.0, step=1000.0)
            parcelas = st.number_input("Parcelas", min_value=1, max_value=60, value=1)
            situacao = st.selectbox("Situação", ["Ativo", "Suspenso", "Encerrado", "Rescindido"])
            if st.form_submit_button("Salvar Contrato"):
                db.add(Contrato(numero=numero, licitacao_id=lic_sel.id, fornecedor_id=forn_sel.id, objeto=objeto,
                                data_inicio=inicio, data_fim=fim, valor_global=Decimal(str(valor_global)),
                                parcelas=parcelas, situacao=situacao))
                db.commit()
                st.success("Contrato salvo!")

        st.markdown("---")
        st.markdown("#### Contratos Cadastrados")
        contratos = db.query(Contrato).all()
        data_con = []
        for c in contratos:
            dias_para_vencer = (c.data_fim - date.today()).days if c.data_fim else None
            alerta_venc = ""
            if c.situacao == "Ativo" and dias_para_vencer is not None and dias_para_vencer <= st.session_state["alerta_vencimento_dias"]:
                alerta_venc = "🔴 Vencimento próximo"
            data_con.append({
                "ID": c.id,
                "Número": c.numero,
                "Fornecedor": c.fornecedor.nome if c.fornecedor else "",
                "Objeto": c.objeto,
                "Início": c.data_inicio,
                "Fim": c.data_fim,
                "Valor Global": format_currency(c.valor_global),
                "Parcelas": c.parcelas,
                "Situação": c.situacao,
                "Dias para Vencer": dias_para_vencer,
                "Alerta": alerta_venc,
            })
        st.dataframe(pd.DataFrame(data_con), use_container_width=True, hide_index=True)

        # Aditivos
        st.markdown("#### Aditivos")
        contr_sel = st.selectbox("Contrato", contratos, format_func=lambda c: f"{c.numero} - {c.fornecedor.nome}")
        if contr_sel:
            with st.expander("Novo Aditivo"):
                with st.form("form_aditivo"):
                    tipo = st.selectbox("Tipo", ["Prazo", "Valor", "Ambos"])
                    novo_valor = st.number_input("Novo Valor Global (opcional)", min_value=0.0, step=1000.0, value=0.0)
                    nova_data = st.date_input("Nova Data Fim (opcional)", value=contr_sel.data_fim if contr_sel.data_fim else date.today())
                    motivo = st.text_area("Motivo")
                    if st.form_submit_button("Salvar Aditivo"):
                        db.add(Aditivo(contrato_id=contr_sel.id, tipo=tipo,
                                       novo_valor_global=Decimal(str(novo_valor)) if novo_valor > 0 else None,
                                       nova_data_fim=nova_data if nova_data else None, motivo=motivo))
                        if tipo in ["Valor", "Ambos"] and novo_valor > 0:
                            contr_sel.valor_global = Decimal(str(novo_valor))
                        if tipo in ["Prazo", "Ambos"] and nova_data:
                            contr_sel.data_fim = nova_data
                        db.commit()
                        st.success("Aditivo salvo!")
            aditivos = db.query(Aditivo).filter_by(contrato_id=contr_sel.id).all()
            st.dataframe(pd.DataFrame([{"ID": a.id, "Tipo": a.tipo, "Novo Valor": format_currency(a.novo_valor_global) if a.novo_valor_global else "",
                                        "Nova Data Fim": a.nova_data_fim, "Motivo": a.motivo} for a in aditivos]),
                         use_container_width=True, hide_index=True)

    finally:
        db.close()


# ============================================================
# MÓDULO: FORNECEDORES
# ============================================================
def pagina_fornecedores():
    st.title("🏢 Módulo de Fornecedores / Credenciados")
    db = get_db()
    try:
        st.markdown("#### Cadastro de Fornecedor")
        with st.form("form_fornecedor"):
            tipo = st.selectbox("Tipo", ["PJ", "PF"])
            cpf_cnpj = st.text_input("CPF/CNPJ")
            nome = st.text_input("Nome/Razão Social")
            endereco = st.text_area("Endereço")
            banco = st.text_area("Dados Bancários")
            telefone = st.text_input("Telefone")
            email = st.text_input("E-mail")
            if st.form_submit_button("Salvar Fornecedor"):
                try:
                    db.add(Fornecedor(tipo=tipo, cpf_cnpj=cpf_cnpj, nome=nome, endereco=endereco,
                                      dados_bancarios=banco, telefone=telefone, email=email))
                    db.commit()
                    st.success("Fornecedor salvo!")
                except IntegrityError:
                    db.rollback()
                    st.error("CPF/CNPJ já cadastrado.")

        st.markdown("---")
        fornecedores = db.query(Fornecedor).all()
        forn_sel = st.selectbox("Fornecedores", fornecedores, format_func=lambda f: f"{f.nome} ({f.cpf_cnpj})")
        if forn_sel:
            st.markdown(f"#### Histórico de {forn_sel.nome}")
            contratos = db.query(Contrato).filter_by(fornecedor_id=forn_sel.id).all()
            licitacoes = db.query(Licitacao).join(Compra).filter(Compra.fornecedor_id == forn_sel.id).distinct().all()
            st.write(f"**Contratos:** {len(contratos)}")
            st.write(f"**Licitações com compras:** {len(licitacoes)}")
            st.markdown("**Contratos**")
            st.dataframe(pd.DataFrame([{"Número": c.numero, "Objeto": c.objeto, "Valor": format_currency(c.valor_global),
                                        "Situação": c.situacao} for c in contratos]), use_container_width=True, hide_index=True)

    finally:
        db.close()


# ============================================================
# MÓDULO: FINANCEIRO
# ============================================================
def pagina_financeiro():
    st.title("💰 Módulo Financeiro")
    db = get_db()
    try:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("#### Movimentação Orçamentária")
            with st.form("form_financeiro"):
                dotacoes = db.query(Dotacao).all()
                dot_sel = st.selectbox("Dotação", dotacoes, format_func=lambda d: f"{d.id} - {d.orgao.nome} - {d.acao.nome} (saldo: {format_currency(d.saldo_atual())})")
                tipo = st.selectbox("Tipo", ["Empenho", "Liquidacao", "Pagamento", "Suplementacao", "Anulacao"])
                numero = st.text_input("Número do Documento")
                data_mov = st.date_input("Data", value=date.today())
                valor = st.number_input("Valor", min_value=0.0, step=100.0)
                historico = st.text_area("Histórico")
                if st.form_submit_button("Salvar Movimentação"):
                    if tipo == "Anulacao" and Decimal(str(valor)) > dot_sel.valor_empenhado:
                        st.error("Valor de anulação excede o valor empenhado.")
                    else:
                        db.add(MovimentacaoOrcamentaria(dotacao_id=dot_sel.id, tipo=tipo, numero_documento=numero,
                                                        data=data_mov, valor=Decimal(str(valor)), historico=historico))
                        if tipo == "Empenho":
                            dot_sel.valor_empenhado += Decimal(str(valor))
                        elif tipo == "Liquidacao":
                            dot_sel.valor_liquidado += Decimal(str(valor))
                        elif tipo == "Pagamento":
                            dot_sel.valor_pago += Decimal(str(valor))
                        elif tipo == "Suplementacao":
                            dot_sel.valor_alteracoes += Decimal(str(valor))
                        elif tipo == "Anulacao":
                            dot_sel.valor_empenhado -= Decimal(str(valor))
                        db.commit()
                        st.success("Movimentação salva!")

        with col2:
            st.markdown("#### Alerta de Suplementação")
            st.session_state["alerta_suplementacao"] = st.slider("Alertar quando execução atingir (%)", 0, 100,
                                                                 int(st.session_state["alerta_suplementacao"]))
            st.info(f"Alerta configurado para {st.session_state['alerta_suplementacao']}%")

        st.markdown("---")
        st.markdown("#### Extrato da Dotação")
        dot_ext = st.selectbox("Selecione a Dotação", dotacoes, format_func=lambda d: f"{d.id} - {d.orgao.nome} - {d.acao.nome}")
        if dot_ext:
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("Original", format_currency(dot_ext.valor_original))
            col2.metric("Alterações", format_currency(dot_ext.valor_alteracoes))
            col3.metric("Empenhado", format_currency(dot_ext.valor_empenhado))
            col4.metric("Liquidado", format_currency(dot_ext.valor_liquidado))
            col5.metric("Pago", format_currency(dot_ext.valor_pago))
            st.metric("Saldo Disponível", format_currency(dot_ext.saldo_atual()))

            total_dot = dot_ext.valor_total()
            perc_exec = (dot_ext.valor_empenhado / total_dot * 100) if total_dot > 0 else Decimal("0")
            if perc_exec >= Decimal(st.session_state["alerta_suplementacao"]):
                st.markdown(f"<<div class='danger-card'>⚠️ A execução desta dotação atingiu {perc_exec:.2f}% - considere suplementação de crédito.</div>", unsafe_allow_html=True)

            st.markdown("#### Histórico de Movimentações")
            movs = db.query(MovimentacaoOrcamentaria).filter_by(dotacao_id=dot_ext.id).order_by(MovimentacaoOrcamentaria.data.desc()).all()
            st.dataframe(pd.DataFrame([{"Tipo": m.tipo, "Documento": m.numero_documento, "Data": m.data,
                                        "Valor": format_currency(m.valor), "Histórico": m.historico} for m in movs]),
                         use_container_width=True, hide_index=True)

    finally:
        db.close()


# ============================================================
# MÓDULO: ALERTAS / CONFIGURAÇÕES
# ============================================================
def pagina_alertas():
    st.title("⚠️ Módulo de Alertas / Configurações")
    st.markdown("#### Configurações de Alerta")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state["alerta_retirada"] = st.slider("% Retirada de Licitação", 0, 100,
                                                        int(st.session_state["alerta_retirada"]))
    with col2:
        st.session_state["alerta_suplementacao"] = st.slider("% Execução para Suplementação", 0, 100,
                                                              int(st.session_state["alerta_suplementacao"]))
    with col3:
        st.session_state["alerta_vencimento_dias"] = st.slider("Dias para Vencimento de Contrato", 0, 365,
                                                                int(st.session_state["alerta_vencimento_dias"]))

    st.markdown("---")
    st.markdown("#### Painel de Alertas Ativos")

    db = get_db()
    try:
        # Alertas de retirada de licitação
        prods = db.query(ProdutoLicitacao).all()
        alertas_retirada = []
        for p in prods:
            pct = p.percentual_retirada()
            if pct >= Decimal(st.session_state["alerta_retirada"]):
                alertas_retirada.append({
                    "Tipo": "Retirada de Licitação",
                    "Licitação": p.licitacao.numero,
                    "Produto": p.descricao,
                    "Mensagem": f"Retirada atingiu {pct:.2f}% (limite {st.session_state['alerta_retirada']}%)",
                })

        # Alertas de suplementação
        alertas_sup = []
        for d in db.query(Dotacao).all():
            total = d.valor_total()
            if total > 0:
                pct = (d.valor_empenhado / total) * 100
                if pct >= Decimal(st.session_state["alerta_suplementacao"]):
                    alertas_sup.append({
                        "Tipo": "Suplementação Orçamentária",
                        "Dotação": f"{d.id} - {d.orgao.nome}",
                        "Mensagem": f"Execução atingiu {pct:.2f}% (limite {st.session_state['alerta_suplementacao']}%)",
                    })

        # Alertas de vencimento
        alertas_venc = []
        for c in db.query(Contrato).filter_by(situacao="Ativo").all():
            if c.data_fim:
                dias = (c.data_fim - date.today()).days
                if dias <= st.session_state["alerta_vencimento_dias"]:
                    alertas_venc.append({
                        "Tipo": "Vencimento de Contrato",
                        "Contrato": c.numero,
                        "Mensagem": f"Vence em {dias} dias ({c.data_fim})",
                    })

        todos_alertas = alertas_retirada + alertas_sup + alertas_venc
        if not todos_alertas:
            st.markdown("<<div class='success-card'>✅ Nenhum alerta ativo no momento.</div>", unsafe_allow_html=True)
        else:
            df_alertas = pd.DataFrame(todos_alertas)
            st.dataframe(df_alertas, use_container_width=True, hide_index=True)

    finally:
        db.close()


# ============================================================
# MÓDULO: RELATÓRIOS
# ============================================================
def pagina_relatorios():
    st.title("📈 Módulo de Relatórios")
    db = get_db()
    try:
        tab1, tab2, tab3 = st.tabs(["Execução Orçamentária", "Licitações por Período", "Compras por Fornecedor"])

        with tab1:
            st.markdown("#### Relatório de Execução Orçamentária")
            dotacoes = db.query(Dotacao).all()
            data = []
            for d in dotacoes:
                total = d.valor_total()
                exec_pct = (d.valor_empenhado / total * 100) if total > 0 else Decimal("0")
                data.append({
                    "Exercício": d.exercicio.ano if d.exercicio else "",
                    "Órgão": d.orgao.nome if d.orgao else "",
                    "Programa": d.programa.nome if d.programa else "",
                    "Ação": d.acao.nome if d.acao else "",
                    "Natureza": d.natureza.codigo if d.natureza else "",
                    "Fonte": d.fonte.codigo if d.fonte else "",
                    "Valor Original": float(d.valor_original),
                    "Alterações": float(d.valor_alteracoes),
                    "Empenhado": float(d.valor_empenhado),
                    "Liquidado": float(d.valor_liquidado),
                    "Pago": float(d.valor_pago),
                    "Saldo": float(d.saldo_atual()),
                    "% Execução": float(exec_pct),
                })
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("Exportar CSV", df.to_csv(index=False).encode("utf-8"), "execucao_orcamentaria.csv", "text/csv")

        with tab2:
            st.markdown("#### Relatório de Licitações por Período")
            c1, c2 = st.columns(2)
            inicio = c1.date_input("Início", value=date(2026, 1, 1))
            fim = c2.date_input("Fim", value=date(2026, 12, 31))
            licitacoes = db.query(Licitacao).filter(Licitacao.data_abertura >= inicio, Licitacao.data_abertura <= fim).all()
            data = []
            for l in licitacoes:
                data.append({
                    "Número": l.numero,
                    "Modalidade": l.modalidade,
                    "Objeto": l.objeto,
                    "Valor Estimado": float(l.valor_estimado),
                    "Data Abertura": l.data_abertura,
                    "Situação": l.situacao,
                    "Dotação": l.dotacao.id if l.dotacao else "",
                })
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("Exportar CSV", df.to_csv(index=False).encode("utf-8"), "licitacoes_periodo.csv", "text/csv")

        with tab3:
            st.markdown("#### Relatório de Compras por Fornecedor")
            fornecedores = db.query(Fornecedor).all()
            forn_sel = st.selectbox("Fornecedor", fornecedores, format_func=lambda f: f"{f.nome} ({f.cpf_cnpj})")
            if forn_sel:
                compras = db.query(Compra).filter_by(fornecedor_id=forn_sel.id).all()
                data = []
                for c in compras:
                    data.append({
                        "Licitação": c.licitacao.numero if c.licitacao else "",
                        "Produto": c.produto.descricao if c.produto else "",
                        "Data": c.data,
                        "Quantidade": float(c.quantidade),
                        "Valor Unitário": float(c.valor_unitario),
                        "Valor Total": float(c.valor_total),
                    })
                df = pd.DataFrame(data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.download_button("Exportar CSV", df.to_csv(index=False).encode("utf-8"), "compras_fornecedor.csv", "text/csv")

    finally:
        db.close()


# ============================================================
# NAVEGAÇÃO PRINCIPAL
# ============================================================
def main():
    # Sidebar estilosa com ícones
    st.sidebar.markdown("<<h1 style='color:#ffffff; text-align:center;'>🏥 MARMED</h1>", unsafe_allow_html=True)
    st.sidebar.markdown("<<p style='color:#ffffff; text-align:center;'>Gestão em Saúde Pública<br>Luminárias - MG</p>", unsafe_allow_html=True)
    st.sidebar.markdown("---")

    if st.sidebar.button("🌱 Carregar Dados de Exemplo"):
        semear_dados()

    st.sidebar.markdown("---")

    paginas = {
        "🏠 Dashboard": pagina_dashboard,
        "📊 LOA": pagina_loa,
        "📑 Licitações": pagina_licitacoes,
        "🛒 Compras": pagina_compras,
        "📜 Contratos": pagina_contratos,
        "🏢 Fornecedores": pagina_fornecedores,
        "💰 Financeiro": pagina_financeiro,
        "⚠️ Alertas": pagina_alertas,
        "📈 Relatórios": pagina_relatorios,
    }

    opcao = st.sidebar.selectbox("Navegação", list(paginas.keys()))
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"<<p style='color:#b0c4de; font-size:0.8em;'>Banco: {db_tipo}</p>", unsafe_allow_html=True)

    paginas[opcao]()


if __name__ == "__main__":
    main()
