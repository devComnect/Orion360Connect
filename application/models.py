from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Inicializa o db, que será importado no app.py
db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    #name = db.Column(db.String(50))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())

    def __repr__(self):
        return f'<Usuario {self.username}>'
    
class DesempenhoAtendente(db.Model):
    __tablename__ = 'desempenho_atendente'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255))
    chamadas_atendidas = db.Column(db.Integer)
    data = db.Column(db.Date)
    tempo_online = db.Column(db.Integer)
    tempo_servico = db.Column(db.Integer)
    tempo_totalatend = db.Column(db.Integer)
    data_importacao = db.Column(db.DateTime, default=datetime.utcnow)

class DesempenhoAtendenteVyrtos(db.Model):
    __tablename__ = 'desempenho_atendente_vyrtos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20))
    operador_id = db.Column(db.Integer, nullable=False, index=True)
    data = db.Column(db.Date, nullable=False, index=True)
    ch_atendidas = db.Column(db.Integer, default=0)
    ch_naoatendidas = db.Column(db.Integer, default=0)
    tempo_online = db.Column(db.Integer, default=0)
    tempo_livre = db.Column(db.Integer, default=0)
    tempo_servico = db.Column(db.Integer, default=0)
    pimprod_refeicao = db.Column(db.Integer, default=0)
    tempo_minatend = db.Column(db.Integer, nullable=True)
    tempo_medatend = db.Column(db.Float, nullable=True)
    tempo_maxatend = db.Column(db.Integer, nullable=True)

class Fila(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer)
    nome = db.Column(db.String(50))
    tipo = db.Column(db.String(10))  # <-- ADICIONE ESTA LINHA
    chamadas_completadas = db.Column(db.Integer)
    chamadas_abandonadas = db.Column(db.Integer)
    transbordo = db.Column(db.Integer)
    chamadas_recebidas = db.Column(db.Integer)
    tempo_espera = db.Column(db.Integer)
    tempo_fala = db.Column(db.Integer)
    nivel_servico = db.Column(db.Float)
    data = db.Column(db.DateTime)

class FilaVyrtus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer)
    nome = db.Column(db.String(50))
    tipo = db.Column(db.String(10))  # <-- ADICIONE ESTA LINHA
    chamadas_completadas = db.Column(db.Integer)
    chamadas_abandonadas = db.Column(db.Integer)
    transbordo = db.Column(db.Integer)
    chamadas_recebidas = db.Column(db.Integer)
    tempo_espera = db.Column(db.Integer)
    tempo_fala = db.Column(db.Integer)
    nivel_servico = db.Column(db.Float)
    data = db.Column(db.DateTime)

class PerformanceColaboradores(db.Model):
    __tablename__ = 'performance_colaboradores'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20))
    operador_id = db.Column(db.Integer, nullable=False, index=True)
    data = db.Column(db.Date, nullable=False, index=True)
    ch_atendidas = db.Column(db.Integer, default=0)
    ch_naoatendidas = db.Column(db.Integer, default=0)
    tempo_online = db.Column(db.Integer, default=0)
    tempo_livre = db.Column(db.Integer, default=0)
    tempo_servico = db.Column(db.Integer, default=0)
    pimprod_refeicao = db.Column(db.Integer, default=0)
    tempo_minatend = db.Column(db.Integer, nullable=True)
    tempo_medatend = db.Column(db.Float, nullable=True)
    tempo_maxatend = db.Column(db.Integer, nullable=True)
    data_importacao = db.Column(db.DateTime)


class Chamado(db.Model):
    __tablename__ = 'chamados'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chave = db.Column(db.Integer, nullable=False)
    cod_chamado = db.Column(db.String(20), nullable=False)
    nome_prioridade = db.Column(db.String(100))
    data_criacao = db.Column(db.DateTime, nullable=False)
    hora_criacao = db.Column(db.String(10))
    data_finalizacao = db.Column(db.DateTime)
    hora_finalizacao = db.Column(db.String(10))
    data_alteracao = db.Column(db.Date)
    hora_alteracao = db.Column(db.String(10))
    nome_status = db.Column(db.String(50))
    assunto = db.Column(db.Text)
    descricao = db.Column(db.Text)
    chave_usuario = db.Column(db.String(50))
    nome_usuario = db.Column(db.String(100))
    sobrenome_usuario = db.Column(db.String(100))
    nome_completo_solicitante = db.Column(db.String(200))
    solicitante_email = db.Column(db.String(200))
    operador = db.Column(db.String(100))
    sobrenome_operador = db.Column(db.String(100))
    total_acoes = db.Column(db.Integer)
    total_anexos = db.Column(db.Integer)
    sla_atendimento = db.Column(db.String(100))
    sla_resolucao = db.Column(db.String(100))
    cod_grupo = db.Column(db.String(10))
    nome_grupo = db.Column(db.String(100))
    cod_solicitacao = db.Column(db.String(10))
    cod_sub_categoria = db.Column(db.String(10))
    cod_tipo_ocorrencia = db.Column(db.String(10))
    cod_categoria_tipo = db.Column(db.String(10))
    cod_prioridade_atual = db.Column(db.String(10))
    cod_status_atual = db.Column(db.String(10))
    mes_referencia = db.Column(db.String(7), nullable=False)
    data_importacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    restante_p_atendimento = db.Column(db.String(10))
    restante_s_atendimento = db.Column(db.String(10))
    tipo_vinculo = db.Column(db.String(10))  # Valores: 'pai', 'filho', None


    __table_args__ = (
        db.UniqueConstraint('chave', 'mes_referencia', name='uq_chave_mes'),
    )

    # Relacionamento com PerformanceColaboradores (somente leitura)
    performance = db.relationship(
        "PerformanceColaboradores",
        primaryjoin="Chamado.operador == foreign(PerformanceColaboradores.name)",
        viewonly=True,
        uselist=False
    )

    def to_dict(self):
        return {
            "cod_chamado": self.cod_chamado,
            "nome_status": self.nome_status,
            "nome_grupo": self.nome_grupo,
            "operador": self.operador,
            "sla_atendimento": self.sla_atendimento,
            "sla_resolucao": self.sla_resolucao,
            "data_criacao": self.data_criacao.isoformat() if self.data_criacao else None
        }

    def __repr__(self):
        return f'<Chamado {self.cod_chamado}>'

class Categoria(db.Model):
    __tablename__ = 'categoria'

    chave = db.Column(db.Integer, primary_key=True)
    sequencia = db.Column(db.String(20))
    sub_categoria = db.Column(db.String(100))
    categoria = db.Column(db.String(100))
    data_importacao = db.Column(db.DateTime)

class PesquisaSatisfacao(db.Model):
    __tablename__ = 'pesquisa_satisfacao'

    id = db.Column(db.Integer, primary_key=True)
    referencia_chamado = db.Column(db.String(50), nullable=False)
    assunto = db.Column(db.String(255))
    data_resposta = db.Column(db.Date)
    data_finalizacao = db.Column(db.Date)
    empresa = db.Column(db.String(255))
    solicitante = db.Column(db.String(255))
    operador = db.Column(db.String(255))
    grupo = db.Column(db.String(255))
    questionario = db.Column(db.String(255))
    questao = db.Column(db.Text)
    alternativa = db.Column(db.String(255))
    resposta_dissertativa = db.Column(db.Text)

class RelatorioColaboradores(db.Model):
    __tablename__ = 'relatorio_colaboradores'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)


    chave = db.Column(db.String(20))
    nome_status = db.Column(db.String(50))
    operador = db.Column(db.String(20))
    grupo = db.Column(db.String(20))
    reaberto = db.Column(db.String(50))
    first_call = db.Column(db.String(1))
    tempo_sem_interacao = db.Column(db.String(50))
    sla1_expirado = db.Column(db.String(20))
    nome_sla1_status = db.Column(db.String(50))
    sla2_expirado = db.Column(db.String(20))
    nome_sla2_status = db.Column(db.String(50))
    pesquisa_satisfacao_respondido = db.Column(db.String(1))
    nome_solicitacao = db.Column(db.String(100))
    fantasia = db.Column(db.String(100))
    nome_completo_solicitante = db.Column(db.String(100))
    cod_chamado = db.Column(db.String(20))
    data_criacao = db.Column(db.String(20))  # ou db.Date se quiser como data
    data_finalizacao = db.Column(db.String(20))  # ou db.Date se quiser como data
    possui_ps = db.Column(db.String(1))
    ps_expirou = db.Column(db.String(1))
