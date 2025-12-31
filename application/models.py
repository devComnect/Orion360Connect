import enum
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import UniqueConstraint, func
from enum import Enum
from sqlalchemy.types import JSON
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.ext.mutable import MutableList



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
    is_nivel2 = db.Column(db.Boolean, default=False)
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

class Guardians(db.Model):
    __tablename__ = 'guardians'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # --- NOVOS CONTADORES DE ESTATÍSTICAS (Adicionado para Conquistas) ---
    stat_patrol_count = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    stat_minigame_count = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    stat_shop_count = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    stat_quiz_count = db.Column(db.Integer, nullable=False, default=0, server_default='0')

    #Sistema de moedas
    guardian_coins = db.Column(db.Integer, nullable=False, default=0, server_default='0')

    ##Sistema de retake
    retake_tokens = db.Column(db.Integer, nullable=False, default=1, server_default='1')
    minigame_retake_tokens = db.Column(db.Integer, nullable=False, default=1, server_default='1')

    ##Personalizar perfil
    nickname = db.Column(db.String(100), nullable=True)
    is_anonymous = db.Column(db.Boolean, default=False, nullable=False) # Para anonimato no perfil
    avatar_seed = db.Column(db.String(100), default='GuardianDefault')
    
    
    #Adicao de cor no nome
    name_color = db.Column(db.String(7), nullable=True) # Para armazenar um código HEX, ex: #FFD700

    # Armazena o melhor troféu permanente: 1=Ouro, 2=Prata, 3=Bronze
    trophy_tier = db.Column(db.Integer, nullable=True)

    
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
    last_spec_change_at = db.Column(db.DateTime, nullable=True)
    tutorials_seen = db.Column(db.JSON, default=dict)
    
    #Add patrulha diaria
    last_patrol_date = db.Column(db.Date, nullable=True)
    
    # Coluna para contar a sequência de quizzes com nota máxima.
    perfect_quiz_streak = db.Column(db.Integer, nullable=False, default=0)
    perfect_quiz_cumulative_count = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    perfect_minigame_cumulative_count = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    perfect_minigame_streak = db.Column(db.Integer, default=0)


    # Controle de criação/atualização
    criado_em = db.Column(db.DateTime, default=db.func.current_timestamp())
    atualizado_em = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    #Relacionamento com a tabela de conquistas em destaque
    featured_associations = db.relationship(
        'GuardianFeatured',
        back_populates='guardian',
        cascade='all, delete-orphan' 
    )
    
    # Adicione a chave estrangeira para o nível de segurança
    nivel_id = db.Column(db.Integer, db.ForeignKey('niveis_seguranca.id'))
    nivel = db.relationship("NivelSeguranca")

    # Chave estrangeira para a nova tabela Specialization
    specialization_id = db.Column(db.Integer, db.ForeignKey('specialization.id'), nullable=True)
    specialization = db.relationship('Specialization')
    
    # Relacionamentos com as novas classes
    historico_acoes = db.relationship("HistoricoAcao", back_populates="guardian", lazy='dynamic')
    insignias_conquistadas = db.relationship("GuardianInsignia", back_populates="guardian", lazy='dynamic')
    current_streak = db.Column(db.Integer, default=0)
    last_streak_date = db.Column(db.Date, nullable=True)
    quiz_attempts = db.relationship("QuizAttempt", back_populates="guardian", cascade="all, delete-orphan", lazy='dynamic')
    weekly_quest_sets = db.relationship('WeeklyQuestSet', back_populates='guardian', cascade="all, delete-orphan", lazy='dynamic')

    @property
    def avatar_path(self):
        """
        Retorna o caminho do avatar de forma segura, com múltiplos fallbacks.
        Garante que NUNCA retorne um valor nulo.
        """
        if self.nivel and self.nivel.avatar_url:
            return self.nivel.avatar_url
        
        if self.specialization:
            primeiro_nivel = NivelSeguranca.query.filter_by(
                specialization_id=self.specialization_id,
                level_number=1
            ).first()
            if primeiro_nivel and primeiro_nivel.avatar_url:
                return primeiro_nivel.avatar_url
                
        return 'img/avatares/default.png'
    

class GuardianFeatured(db.Model):
    __tablename__ = 'guardian_featured'
    
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.id'), primary_key=True)
    insignia_id = db.Column(db.Integer, db.ForeignKey('insignias.id'), primary_key=True)
    slot_index = db.Column(db.Integer, default=0) 
    equipado_em = db.Column(db.DateTime, default=datetime.utcnow)

    insignia = db.relationship("Insignia")
    guardian = db.relationship("Guardians")

class NivelSeguranca(db.Model):
    __tablename__ = 'niveis_seguranca'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True) # Ex: Recruta, Vigilante
    score_minimo = db.Column(db.Integer, nullable=False)
    avatar_url = db.Column(db.String(255))
    level_number = db.Column(db.Integer, nullable=False)
    specialization_id = db.Column(db.Integer, db.ForeignKey('specialization.id'), nullable=False)
    specialization = db.relationship('Specialization', back_populates='levels')

class Insignia(db.Model):
    __tablename__ = 'insignias'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text, nullable=False)
    requisito_score = db.Column(db.Integer, default=0)
    caminho_imagem = db.Column(db.String(255))
    bonus_type = db.Column(db.String(50), nullable=True) 
    bonus_value = db.Column(db.Float, nullable=True)    
    
    achievement_code = db.Column(db.String(50), nullable=False, unique=True, index=True) 

    conquistas = db.relationship("GuardianInsignia", back_populates="insignia", cascade="all, delete-orphan")
    
class HistoricoAcao(db.Model):
    __tablename__ = 'historico_acoes'
    id = db.Column(db.Integer, primary_key=True)
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.id'), nullable=False)
    data_evento = db.Column(db.DateTime, default=db.func.now())
    descricao = db.Column(db.String(255), nullable=False) # Ex: "Reporte de Phishing Simulada"
    pontuacao = db.Column(db.Integer, nullable=False)
    
    # Relacionamento com a classe Guardians
    guardian = db.relationship("Guardians", back_populates="historico_acoes")
    
class GuardianInsignia(db.Model):
    __tablename__ = 'guardian_insignia'
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.id'), primary_key=True)
    insignia_id = db.Column(db.Integer, db.ForeignKey('insignias.id'), primary_key=True)
    data_conquista = db.Column(db.DateTime, default=db.func.now())
    
    # Relacionamentos com as classes principais
    guardian = db.relationship("Guardians", back_populates="insignias_conquistadas")
    insignia = db.relationship("Insignia", back_populates="conquistas")

class EventoPontuacao(db.Model):
    __tablename__ = 'eventos_pontuacao'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), unique=True, nullable=False)
    pontuacao = db.Column(db.Integer, nullable=False)
    descricao = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Evento {self.nome} | Pontos: {self.pontuacao}>' 
      
class QuizCategory(Enum):
    COMUM = 'Comum'         
    ESPECIAL = 'Especial'  
    HARDCORE = 'Hardcore'    

class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    activation_date = db.Column(db.Date, nullable=False) 
    duration_days = db.Column(db.Integer, nullable=False, default=1) 
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
    started_at = db.Column(db.DateTime, nullable=False)
    spec_bonus = db.Column(db.Integer, default=0)
    time_bonus = db.Column(db.Integer, default=0)
    perfection_bonus = db.Column(db.Integer, default=0)
    conquista_bonus = db.Column(db.Integer, default=0)
    streak_total_bonus = db.Column(db.Integer, default=0)
    streak_base_bonus = db.Column(db.Integer, default=0)
    streak_spec_bonus = db.Column(db.Integer, default=0)
    final_score = db.Column(db.Integer, default=0)
    shop_bonus = db.Column(db.Integer, default=0)

    guardian = db.relationship('Guardians')
    quiz = db.relationship('Quiz', back_populates='attempts')
    answers = db.relationship('UserAnswer', back_populates='attempt', cascade="all, delete-orphan")
   
class UserAnswer(db.Model):
    __tablename__ = 'user_answers'
    id = db.Column(db.Integer, primary_key=True)
    quiz_attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('answer_options.id'), nullable=False)
    
    attempt = db.relationship('QuizAttempt', back_populates='answers')
    question = db.relationship('Question')
    selected_option = db.relationship('AnswerOption')

class Specialization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) 
    spec_code = db.Column(db.String(50), unique=True, nullable=False) 
    description = db.Column(db.String(255), nullable=False)
    color_hex = db.Column(db.String(7), nullable=True, default='#0dcaf0') # Padrão azul 'info'
    levels = db.relationship('NivelSeguranca', back_populates='specialization', cascade="all, delete-orphan")
    perks = db.relationship('SpecializationPerkLevel', back_populates='specialization', cascade="all, delete-orphan")

class Perk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    perk_code = db.Column(db.String(50), unique=True, nullable=False) 
    name = db.Column(db.String(100), nullable=False) 
    description_template = db.Column(db.String(255)) 

class SpecializationPerkLevel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    specialization_id = db.Column(db.Integer, db.ForeignKey('specialization.id'), nullable=False)
    perk_id = db.Column(db.Integer, db.ForeignKey('perk.id'), nullable=False)
    level = db.Column(db.Integer, nullable=False, default=1)
    bonus_value = db.Column(db.Float, nullable=False) 
    
    specialization = db.relationship('Specialization', back_populates='perks')
    perk = db.relationship('Perk')
    __table_args__ = (UniqueConstraint('specialization_id', 'perk_id', 'level', name='_spec_perk_level_uc'),)

class GlobalGameSettings(db.Model):
    __tablename__ = 'global_game_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    category = db.Column(db.String(50))

    def __repr__(self):
        return f'<Setting {self.setting_key}={self.setting_value}>'
    
class TermoGame(db.Model):
    __tablename__ = 'termo_games'
    
    id = db.Column(db.Integer, primary_key=True)
    correct_word = db.Column(db.String(50), nullable=False) # A palavra a ser adivinhada
    max_attempts = db.Column(db.Integer, nullable=False, default=6)
    time_limit_seconds = db.Column(db.Integer, nullable=True) # Opcional
    points_reward = db.Column(db.Integer, nullable=False, default=10)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    activation_date = db.Column(db.Date, nullable=True) 
    duration_days = db.Column(db.Integer, nullable=False, default=1)
    hint = db.Column(db.String(255), nullable=True)

    attempts = db.relationship('TermoAttempt', back_populates='game', cascade="all, delete-orphan")

class TermoAttempt(db.Model):
    __tablename__ = 'termo_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('termo_games.id'), nullable=False)
    
    guesses = db.Column(db.JSON) 
    is_won = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    score = db.Column(db.Integer, default=0, nullable=False)
    base_points = db.Column(db.Integer, default=0, nullable=False)
    final_score = db.Column(db.Integer, nullable=False, default=0)
    time_bonus = db.Column(db.Integer, default=0, nullable=False)
    perfection_bonus = db.Column(db.Integer, default=0, nullable=False)
    conquista_bonus = db.Column(db.Integer, default=0)
    streak_total_bonus = db.Column(db.Integer, default=0, nullable=False)
    streak_base_bonus = db.Column(db.Integer, default=0, nullable=False)
    streak_spec_bonus = db.Column(db.Integer, default=0, nullable=False)
    shop_bonus = db.Column(db.Integer, default=0)
    

    guardian = db.relationship('Guardians')
    game = db.relationship('TermoGame', back_populates='attempts')

class AnagramGame(db.Model):
    __tablename__ = 'anagram_games'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(255))
    points_per_word = db.Column(db.Integer, nullable=False, default=5)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    activation_date = db.Column(db.Date, nullable=True) 
    duration_days = db.Column(db.Integer, nullable=False, default=7)
    time_limit_seconds = db.Column(db.Integer, nullable=True)

    words = db.relationship('AnagramWord', back_populates='game', cascade="all, delete-orphan")
    attempts = db.relationship('AnagramAttempt', back_populates='game', cascade="all, delete-orphan")

class AnagramWord(db.Model):
    __tablename__ = 'anagram_words'
    id = db.Column(db.Integer, primary_key=True)
    correct_word = db.Column(db.String(100), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('anagram_games.id'), nullable=False)
    game = db.relationship('AnagramGame', back_populates='words')

class AnagramAttempt(db.Model):
    __tablename__ = 'anagram_attempts'
    id = db.Column(db.Integer, primary_key=True)
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.id'), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('anagram_games.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False, default=0)
    completed_at = db.Column(db.DateTime, nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    correct_answers = db.Column(db.Integer, nullable=False, default=0)
    final_score = db.Column(db.Integer, nullable=False, default=0)
    time_bonus = db.Column(db.Integer, default=0, nullable=False)
    perfection_bonus = db.Column(db.Integer, default=0, nullable=False)
    conquista_bonus = db.Column(db.Integer, default=0)
    streak_total_bonus = db.Column(db.Integer, default=0, nullable=False)
    streak_base_bonus = db.Column(db.Integer, default=0, nullable=False)
    streak_spec_bonus = db.Column(db.Integer, default=0, nullable=False)
    shop_bonus = db.Column(db.Integer, default=0)

    guardian = db.relationship('Guardians')
    game = db.relationship('AnagramGame', back_populates='attempts')

class FeedbackReport(db.Model):
    __tablename__ = 'feedback_reports'
    id = db.Column(db.Integer, primary_key=True)
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.id'), nullable=False)
    report_type = db.Column(db.Enum('BUG', 'SUGGESTION', name='feedback_type_enum'), nullable=False) # BUG ou SUGGESTION
    description = db.Column(db.Text, nullable=False)
    attachment_path = db.Column(db.String(255), nullable=True) # Caminho relativo do arquivo salvo
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_resolved = db.Column(db.Boolean, default=False) # Para controle do admin

    guardian = db.relationship('Guardians')

    def __repr__(self):
        return f'<FeedbackReport {self.id} by Guardian {self.guardian_id} - {self.report_type}>'
    
class GameSeason(db.Model):
    __tablename__ = 'game_seasons'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False) # Indica a temporada atual
    rewards_description_html = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<GameSeason {self.name} (Ativa: {self.is_active})>'
    
class PasswordGameConfig(db.Model):
    __tablename__ = 'password_game_config'
    
    id = db.Column(db.Integer, primary_key=True) # Será sempre 1
    is_active = db.Column(db.Boolean, default=True)
    
    # Configurações de Dificuldade
    time_limit_seconds = db.Column(db.Integer, default=120) # Ex: 2 minutos
    base_reward_points = db.Column(db.Integer, default=300) # Pontos se vencer
    
    # Quantas regras sortear de cada tipo
    rules_count_easy = db.Column(db.Integer, default=1)
    rules_count_medium = db.Column(db.Integer, default=2)
    rules_count_hard = db.Column(db.Integer, default=1)
    rules_count_insane = db.Column(db.Integer, default=1)
    active_days = db.Column(db.String(20), default="0,1,2,3,4,5,6")

    def __repr__(self):
        return f'<PasswordConfig {self.time_limit_seconds}s / {self.base_reward_points}pts>'

class PasswordAttempt(db.Model):
    __tablename__ = 'password_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.id'), nullable=False)
    
    # Armazena os IDs das regras que foram sorteadas (JSON)
    rules_sequence = db.Column(db.JSON, nullable=False) 
    
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    is_won = db.Column(db.Boolean, default=False)
    
    # Pontuação e Bônus
    base_points = db.Column(db.Integer, default=0) # O valor do Config no momento do jogo
    score = db.Column(db.Integer, default=0)       # Base + Spec
    final_score = db.Column(db.Integer, default=0) # Tudo somado
    
    # Detalhamento (para o histórico e resultado unificado)
    time_bonus = db.Column(db.Integer, default=0)
    perfection_bonus = db.Column(db.Integer, default=0, nullable=False)
    spec_bonus = db.Column(db.Integer, default=0, nullable=False)
    conquista_bonus = db.Column(db.Integer, default=0)
    shop_bonus = db.Column(db.Integer, default=0)
    streak_total_bonus = db.Column(db.Integer, default=0)
    
    guardian = db.relationship('Guardians', backref='password_attempts')

class MissionCodeEnum(enum.Enum):
    PATROL_COUNT = 'Fazer Patrulha'
    QUIZ_COUNT = 'Completar Quizzes'
    QUIZ_SCORE_SUM = 'Acumular Pontos em Quizzes'
    QUIZ_PERFECT_COUNT = 'Quizzes Perfeitos'
    MINIGAME_COUNT = 'Completar Minigames (Código/Decriptar/Segredo)'
    STREAK_DAYS = 'Atingir Dias de Streak'
    ANY_CHALLENGE_COUNT = 'Completar Qualquer Desafio'
    ANY_PERFECT_COUNT = 'Qualquer Desafio Perfeito'
    QUIZ_SPEEDRUN = 'Quiz Rápido (< 60s)'
    MINIGAME_SPEEDRUN = 'Minigame Rápido (< 45s)'
    SPEND_GC_UPGRADES = 'Gastar GC em Upgrades'
    SPEND_GC_REROLL = 'Gastar GC em Reroll'

class MissionDifficultyEnum(enum.Enum):
    EASY = 'Fácil'
    MEDIUM = 'Médio'
    HARD = 'Difícil'

class MissionTypeEnum(enum.Enum):
    QUIZ = 'Quiz'
    GAME = 'Minigame'
    ACTION = 'Ação/Patrulha'
    PASSIVE = 'Passiva/Streak'
    ECONOMY = 'Economia/Loja'

class MissionTemplate(db.Model):
    __tablename__ = 'mission_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description_template = db.Column(db.String(255), nullable=False) # Ex: "Complete {target} quizzes."
    
    mission_code = db.Column(db.Enum(MissionCodeEnum), nullable=False, index=True)
    difficulty = db.Column(db.Enum(MissionDifficultyEnum), nullable=False, default=MissionDifficultyEnum.EASY)
    mission_type = db.Column(db.Enum(MissionTypeEnum), nullable=False, default=MissionTypeEnum.ACTION)
    xp_reward = db.Column(db.Integer, default=100)
    
    min_target = db.Column(db.Integer, nullable=False, default=1)
    max_target = db.Column(db.Integer, nullable=False, default=5)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    
    active_missions = db.relationship('ActiveMission', back_populates='template')

    def __repr__(self):
        return f'<Template {self.title} [{self.difficulty.name}]>'

class WeeklyQuestSet(db.Model):
    __tablename__ = 'weekly_quest_sets'
    
    id = db.Column(db.Integer, primary_key=True)
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.id'), nullable=False, index=True)
    
    week_number = db.Column(db.Integer, nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    
    bonus_reward_placeholder = db.Column(db.Integer, nullable=False, default=500)
    coin_reward = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    
    is_completed = db.Column(db.Boolean, default=False, nullable=False) 
    is_claimed = db.Column(db.Boolean, default=False, nullable=False)   
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    guardian = db.relationship('Guardians', back_populates='weekly_quest_sets')
    missions = db.relationship('ActiveMission', back_populates='quest_set', cascade="all, delete-orphan", lazy='dynamic')
    
    __table_args__ = (db.UniqueConstraint('guardian_id', 'week_number', 'year', name='_guardian_week_year_uc'),)

    def __repr__(self):
        return f'<WeeklyQuestSet Guardião {self.guardian_id} (Semana {self.week_number}/{self.year})>'

class ActiveMission(db.Model):
    __tablename__ = 'active_missions'
    
    id = db.Column(db.Integer, primary_key=True)
    quest_set_id = db.Column(db.Integer, db.ForeignKey('weekly_quest_sets.id'), nullable=False, index=True)
    
    mission_template_id = db.Column(db.Integer, db.ForeignKey('mission_templates.id'), nullable=True) 
    
    title_generated = db.Column(db.String(255), nullable=False) 
    mission_code = db.Column(db.Enum(MissionCodeEnum), nullable=False, index=True) 
    
    target_value = db.Column(db.Integer, nullable=False)    
    current_progress = db.Column(db.Integer, nullable=False, default=0)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    
    quest_set = db.relationship('WeeklyQuestSet', back_populates='missions')
    template = db.relationship('MissionTemplate', back_populates='active_missions')

    def __repr__(self):
        return f'<ActiveMission {self.id}: {self.current_progress}/{self.target_value}>'
    
class ShopItem(db.Model):
    __tablename__ = 'shop_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # Ex: "Pacote de Tokens"
    description = db.Column(db.String(255), nullable=True) # Ex: "Recupera 3 tokens de Quiz"
    category = db.Column(db.String(50), nullable=False, default='Geral') # Ex: "Consumíveis", "Bônus", "Cosméticos"
    cost = db.Column(db.Integer, nullable=False) # Preço em G-Coins
    image_path = db.Column(db.String(255), nullable=True) # Caminho da imagem ou classe de ícone (bi-star)
    bonus_type = db.Column(db.String(50), nullable=True) 
    bonus_value = db.Column(db.Float, nullable=True)
    duration_days = db.Column(db.Integer, nullable=True)
    purchase_limit = db.Column(db.Integer, nullable=True) # Quantas vezes pode comprar? (None = Infinito)
    is_active = db.Column(db.Boolean, default=True) # Para o admin esconder itens
    rarity = db.Column(db.String(20), default='COMMON', nullable=False)

    purchases = db.relationship('GuardianPurchase', back_populates='item')

    def __repr__(self):
        return f'<ShopItem {self.name} ({self.cost} GC)>'

class GuardianPurchase(db.Model):
    __tablename__ = 'guardian_purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.id'), nullable=False, index=True)
    item_id = db.Column(db.Integer, db.ForeignKey('shop_items.id'), nullable=False, index=True)
    
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)
    cost_at_purchase = db.Column(db.Integer, nullable=False) # Quanto pagou na época (para histórico)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    guardian = db.relationship('Guardians', backref=db.backref('purchases', lazy='dynamic'))
    item = db.relationship('ShopItem')

    def __repr__(self):
        return f'<Purchase {self.guardian_id} bought {self.item_id}>'
    
class GuardianShopState(db.Model):
    __tablename__ = 'guardian_shop_states'
    
    id = db.Column(db.Integer, primary_key=True)
    guardian_id = db.Column(db.Integer, db.ForeignKey('guardians.id'), unique=True, nullable=False)
    current_items_ids = db.Column(db.JSON, nullable=False) 
    reroll_count = db.Column(db.Integer, default=0)
    last_refresh_date = db.Column(db.Date, nullable=False) 
    
    guardian = db.relationship('Guardians', backref=db.backref('shop_state', uselist=False))

class AchievementCategory(db.Model):
    __tablename__ = 'achievement_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True) 
    order = db.Column(db.Integer, default=0, nullable=False)
    icon = db.Column(db.String(100))
    desc = db.Column(db.String(100))
    
    def __repr__(self):
        return f"<Category {self.name} (Order: {self.order})>"
