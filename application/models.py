from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import UniqueConstraint
from enum import Enum

# Inicializa o db, que será importado no app.py
db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)  # Nova coluna email
    name = db.Column(db.String(100), nullable=True)  # Nova coluna name (opcional)
    is_admin = db.Column(db.Boolean, default=False)
    is_nivel2 = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.now())

    @property
    def is_nivel2_user(self):
        return int(self.is_nivel2 or 0) == 1

    def __repr__(self):
        return f'<Usuario {self.username}>'
    
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
    data_importacao = db.Column(db.DateTime, default=datetime.utcnow)

class Fila(db.Model):
    __tablename__ = 'fila_suporte'

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
    pimprod_Lanche_5 = db.Column(db.Integer, default=0)
    pimprod_Pessoal_6 = db.Column(db.Integer, default=0)
    pimprod_Toalete_1 = db.Column(db.Integer, default=0)

    data_importacao = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('operador_id', 'data', name='uq_operador_data'),
    )

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
    data_criacao = db.Column(db.Date)  # ou db.Date se quiser como data
    data_finalizacao = db.Column(db.String(20))  # ou db.Date se quiser como data
    possui_ps = db.Column(db.String(1))
    ps_expirou = db.Column(db.String(1))

class Guardians(db.Model):
    __tablename__ = 'guardians'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    ##Personalizar perfil
    nickname = db.Column(db.String(100), nullable=True)
    is_anonymous = db.Column(db.Boolean, default=False, nullable=False) # Para anonimato no perfil
    
    #Conquista ao lado do nome
    featured_insignia_id = db.Column(db.Integer, db.ForeignKey('insignias.id'), nullable=True)
    featured_insignia = db.relationship('Insignia')
    
    #Adicao de cor no nome
    name_color = db.Column(db.String(7), nullable=True) # Para armazenar um código HEX, ex: #FFD700

    
    # Chave estrangeira para classe user
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), unique=True, nullable=False)

    # Informações pessoais
    nome = db.Column(db.String(100)) 
    email = db.Column(db.String(255), unique=True)
    grupo = db.Column(db.String(100))  # Equivale a department_name
    
    # Permissao de admin
    is_admin = db.Column(db.Boolean, default=False)

    # Pontuação , ranking e anonimato
    score_atual = db.Column(db.Integer, default=0)
    opt_in_real_name_ranking = db.Column(db.Boolean, default=False)
    is_anonymous = db.Column(db.Boolean, nullable=False, default=False)


    # Dados do departamento (embutidos)
    departamento_id = db.Column(db.Integer)  # Departments.department_id
    departamento_nome = db.Column(db.String(100))  # Departments.department_name
    departamento_score = db.Column(db.Integer, default=0)

    # Últimas atividades
    ultima_atividade = db.Column(db.DateTime)

    # Dados adicionais
    avatar_url = db.Column(db.String(255))  # Imagem/avatar do colaborador
    
    #Add patrulha diaria
    last_patrol_date = db.Column(db.Date, nullable=True)
    
    # Coluna para contar a sequência de quizzes com nota máxima.
    perfect_quiz_streak = db.Column(db.Integer, nullable=False, default=0)


    # Controle de criação/atualização
    criado_em = db.Column(db.DateTime, default=db.func.current_timestamp())
    atualizado_em = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Adicione a chave estrangeira para o nível de segurança
    nivel_id = db.Column(db.Integer, db.ForeignKey('niveis_seguranca.id'))
    nivel = db.relationship("NivelSeguranca")
    
    # Relacionamentos com as novas classes
    historico_acoes = db.relationship("HistoricoAcao", back_populates="guardian", lazy='dynamic')
    insignias_conquistadas = db.relationship("GuardianInsignia", back_populates="guardian", lazy='dynamic')
    current_streak = db.Column(db.Integer, default=0)
    last_streak_date = db.Column(db.Date, nullable=True)
    quiz_attempts = db.relationship("QuizAttempt", back_populates="guardian", cascade="all, delete-orphan", lazy='dynamic')


class Grupos(db.Model):
    __tablename__ = 'grupos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    chave = db.Column(db.String(10), unique=True, nullable=False)  # Ex: "000005"
    nome = db.Column(db.String(100), nullable=False)               # Ex: "CSM"
    email = db.Column(db.String(255), nullable=False)              # Ex: "csm@dominio.com.br"
    opcoes = db.Column(db.Text)                                    # HTML com os ícones e tooltips
    bloqueado = db.Column(db.String(20))               # Campo pode vir vazio, tratado como False
    qtd_operadores = db.Column(db.Integer, default=0)              # Ex: 1
    smtp_ativo = db.Column(db.String(10))              # "N" ou "S" convertido em Boolean

    criado_em = db.Column(db.DateTime, default=db.func.current_timestamp())
    atualizado_em = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class EventosAtendentes(db.Model):
    __tablename__ = 'eventos_atendente'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data = db.Column(db.Date, nullable=False, index=True)  # "2025/08/08"
    atendente = db.Column(db.Integer, nullable=True, index=True)  # ID do atendente (NULL se inválido)
    nome_atendente = db.Column(db.String(100), nullable=True)  # Nome pode ser NULL
    evento = db.Column(db.String(50), nullable=True)  # Tipo de evento
    parametro = db.Column(db.String(10), nullable=True)  # "1" ou "-"
    nome_pausa = db.Column(db.String(50), nullable=True)  # "Toalete" ou NULL
    data_inicio = db.Column(db.DateTime, nullable=True)  # Pode ser NULL se horário inválido
    data_fim = db.Column(db.DateTime, nullable=True)  # Pode ser NULL se horário inválido
    sinaliza_duracao = db.Column(db.Boolean, nullable=False, default=False)
    duracao = db.Column(db.Interval, nullable=True)  # "00:03:29"
    complemento = db.Column(db.String(255), nullable=True)
    data_importacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Evento {self.evento} - {self.nome_atendente} ({self.data})>"

class RegistroChamadas(db.Model):
    __tablename__= 'registro_chamadas_saida'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    data_hora = db.Column(db.DateTime)
    unique_id = db.Column(db.String(100))
    status = db.Column(db.String(20))
    numero = db.Column(db.String(20))
    tempo_espera = db.Column(db.String(20))
    tempo_atendimento = db.Column(db.String(20))
    nome_atendente = db.Column(db.String(50))
    motivo = db.Column(db.String(20))
    sub_motivo = db.Column(db.String(20))
    desconexao_local = db.Column(db.String(20))
    data_importacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Metas(db.Model):
    __tablename__ = 'metas'
    
    id = db.Column(db.Integer, primary_key=True)

    # Campos numéricos de metas
    reabertos = db.Column(db.Float, nullable=True)
    fcr = db.Column(db.Float, nullable=True)
    tma = db.Column(db.Float, nullable=True)
    tms = db.Column(db.Float, nullable=True)
    tmin = db.Column(db.Float, nullable=True)
    tmax = db.Column(db.Float, nullable=True)
    sla_atendimento_prazo = db.Column(db.Float, nullable=True)
    sla_resolucao_prazo = db.Column(db.Float, nullable=True)
    csat = db.Column(db.Float, nullable=True)

    # Opcional: Data de criação e modificação
    criado_em = db.Column(db.DateTime, server_default=db.func.now())
    atualizado_em = db.Column(db.DateTime, onupdate=db.func.now())

    def __repr__(self):
        return f'<Metas {self.id}>'

class ChamadasDetalhes(db.Model):
    __tablename__ = 'detalhes_chamadas'

    id = db.Column(db.Integer, primary_key=True)
    idFila = db.Column(db.String(50))
    nomeFila = db.Column(db.String(255))
    uniqueID = db.Column(db.String(100))
    data = db.Column(db.String(50))
    tipo = db.Column(db.String(50))
    numero = db.Column(db.String(50))
    origem = db.Column(db.String(50))
    tipoOrigem = db.Column(db.String(100))
    filaOrigem = db.Column(db.String(255))
    horaEntradaPos = db.Column(db.String(50))
    horaAtendimento = db.Column(db.String(50))
    horaTerminoPos = db.Column(db.String(50))
    tempoEspera = db.Column(db.String(50))
    tempoAtendimento = db.Column(db.String(50))
    numeroAtendente = db.Column(db.String(50))
    nomeAtendente = db.Column(db.String(255))
    desconexaoLocal = db.Column(db.String(50))
    transferencia = db.Column(db.String(255))
    motivo = db.Column(db.String(255))
    rotuloSubMotivo = db.Column(db.String(255))
    subMotivo = db.Column(db.String(255))
    isAtendida = db.Column(db.String(10))
    isAbandonada = db.Column(db.String(10))
    isTransbordoPorTempo = db.Column(db.String(10))
    isTransbordoPorTecla = db.Column(db.String(10))
    isIncompleta = db.Column(db.String(10))
    numeroSemFormato = db.Column(db.String(50))
    tipoAbandonada = db.Column(db.String(50))
    Nome = db.Column(db.String(255))
    protocolo = db.Column(db.String(100))
    retentativaSucesso = db.Column(db.String(50))
    dataImportacao = db.Column(db.String(50))  # NOVA COLUNA
    
class DoorAccessLogs(db.Model):
    __bind_key__ = 'door_access'
    __tablename__ = 'door_access_logs'

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer)
    time = db.Column(db.Integer)
    event = db.Column(db.Integer)
    hw_device_id = db.Column(db.BigInteger)
    identifier_id = db.Column(db.BigInteger)
    user_id = db.Column(db.Integer)
    portal_id = db.Column(db.Integer)
    identification_rule_id = db.Column(db.Integer)
    card_value = db.Column(db.String(50))
    qrcode_value = db.Column(db.String(50))
    log_type_id = db.Column(db.Integer)
    updated_at = db.Column(db.DateTime)

# Modelo parcial da tabela 'users' do banco 'door_access'
class UserAccess(db.Model):
    __bind_key__ = 'door_access'
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))

# Modelo parcial da tabela 'devices' do banco 'door_access'
class DeviceAccess(db.Model):
    __bind_key__ = 'door_access'
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))

## COMNECT GUARDIANS ##    
    
class NivelSeguranca(db.Model):
    __tablename__ = 'niveis_seguranca'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True) # Ex: Recruta, Vigilante
    score_minimo = db.Column(db.Integer, nullable=False)
    badge_icon_url = db.Column(db.String(255))

class Insignia(db.Model):
    __tablename__ = 'insignias'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text, nullable=False)
    requisito_score = db.Column(db.Integer, default=0) # Pontuação mínima para obter a insígnia
    caminho_imagem = db.Column(db.String(255))
    
    achievement_code = db.Column(db.String(50), nullable=False, unique=True, index=True)  #id para conquistas automaticas

    
    # Relacionamento com a tabela de junção
    conquistas = db.relationship("GuardianInsignia", back_populates="insignia")
    
class HistoricoAcao(db.Model):
    __tablename__ = 'historico_acoes'
    id = db.Column(db.Integer, primary_key=True)
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.id'), nullable=False)
    data_evento = db.Column(db.DateTime, default=db.func.now())
    descricao = db.Column(db.String(255), nullable=False) # Ex: "Reporte de Phishing Simulada"
    pontuacao = db.Column(db.Integer, nullable=False)
    
    # Relacionamento com a classe Guardians
    guardian = db.relationship("Guardians", back_populates="historico_acoes")
    
# Tabela de junção para insígnias (quem ganhou qual insígnia)
class GuardianInsignia(db.Model):
    __tablename__ = 'guardian_insignia'
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.id'), primary_key=True)
    insignia_id = db.Column(db.Integer, db.ForeignKey('insignias.id'), primary_key=True)
    data_conquista = db.Column(db.DateTime, default=db.func.now())
    
    
    # Relacionamentos com as classes principais
    guardian = db.relationship("Guardians", back_populates="insignias_conquistadas")
    insignia = db.relationship("Insignia", back_populates="conquistas")

# Eventos e Pontuacoes

class EventoPontuacao(db.Model):
    __tablename__ = 'eventos_pontuacao'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), unique=True, nullable=False)
    pontuacao = db.Column(db.Integer, nullable=False)
    descricao = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Evento {self.nome} | Pontos: {self.pontuacao}>' 
      
## QUIZ DE SEGURANCA ##

class QuizCategory(Enum):
    COMUM = 'Comum'         
    ESPECIAL = 'Especial'  
    HARDCORE = 'Hardcore'    

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # NOVOS CAMPOS PARA AGENDAMENTO
    activation_date = db.Column(db.Date, nullable=False) # Dia em que o quiz "vai ao ar"
    duration_days = db.Column(db.Integer, nullable=False, default=1) # Por quantos dias fica disponível
    time_limit_seconds = db.Column(db.Integer, nullable=True)

    
    category = db.Column(db.Enum(QuizCategory), nullable=False, default=QuizCategory.COMUM)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    questions = db.relationship('Question', back_populates='quiz', cascade="all, delete-orphan")
    attempts = db.relationship('QuizAttempt', back_populates='quiz')

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id', ondelete='SET NULL'), nullable=True)
    question_text = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer, nullable=False, default=10)
    quiz = db.relationship('Quiz', back_populates='questions')
    options = db.relationship('AnswerOption', back_populates='question', cascade="all, delete-orphan")

class AnswerOption(db.Model):
    __tablename__ = 'answer_options'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    option_text = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    question = db.relationship('Question', back_populates='options')

class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'
    id = db.Column(db.Integer, primary_key=True)
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    guardian = db.relationship('Guardians')
    quiz = db.relationship('Quiz', back_populates='attempts')
    answers = db.relationship('UserAnswer', back_populates='attempt', cascade="all, delete-orphan")
    started_at = db.Column(db.DateTime, nullable=False)

    
class UserAnswer(db.Model):
    __tablename__ = 'user_answers'
    id = db.Column(db.Integer, primary_key=True)
    quiz_attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('answer_options.id'), nullable=False)
    
    attempt = db.relationship('QuizAttempt', back_populates='answers')
    question = db.relationship('Question')
    selected_option = db.relationship('AnswerOption')
