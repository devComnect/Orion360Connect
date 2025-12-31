import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
import time

from flask import Flask, session
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_apscheduler import APScheduler
from werkzeug.security import generate_password_hash

from application.models import db, User, Guardians
from modules.home.routes import home_bp
from modules.login.routes import login_bp
from modules.deskmanager.authenticate.routes import auth_bp
from modules.filas.routes import filas_bp
from modules.dashboard.routes import dashboard_bp
from modules.operadores.routes import operadores_bp
from modules.insights.routes import insights_bp
from modules.relatorios.routes import relatorios_bp
from modules.escala.routes import escala_bp
from modules.insights.grupos.routes import grupos_bp
from modules.okrs.routes import okrs_bp
from modules.guardians.routes import guardians_bp  
from modules.register.routes import register_bp
from modules.eventos.routes import eventos_bp
from modules.operacao.routes import operacao_bp
from modules.login.session_manager import SessionManager
from modules.tasks.tasks import (
    processar_e_armazenar_performance,
    processar_e_armazenar_performance_vyrtos,
    importar_chamados,
    processar_e_armazenar_performance_incremental,
    processar_e_armazenar_performance_vyrtos_incremental,
    importar_pSatisfacao,
    importar_fcr_reabertos,
    processar_e_armazenar_eventos,
    importar_detalhes_chamadas_hoje,
    importar_registro_chamadas_incremental
)


log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')

handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

app_logger = logging.getLogger()
app_logger.setLevel(logging.DEBUG)
app_logger.addHandler(handler)

app = Flask(__name__)

@app.context_processor
def inject_global_vars():
    return dict(
        is_authenticated=session.get('is_authenticated', False),
        is_portal_admin=session.get('is_portal_admin', False),
        is_guardian_admin=session.get('is_guardian_admin', False),
        is_nivel2=int(session.get('is_nivel2', 0)),
        username=session.get('username')
    )


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:%40Slink1205@localhost/data'
app.config['SQLALCHEMY_BINDS'] = {
    'door_access': 'mysql+pymysql://sec_report:%40Comnect2025@172.16.30.50/AccessDoors',
    'delgrande': 'mysql+pymysql://delgrande:ConWsec01%21@172.16.30.40/del_grande'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'LjKbe9TBQKXExJw'

app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

class Config:
    SCHEDULER_API_ENABLED = True

app.config.from_object(Config())

# Register blueprints
app.register_blueprint(home_bp)
app.register_blueprint(login_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(filas_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(operadores_bp)
app.register_blueprint(insights_bp)
app.register_blueprint(relatorios_bp)
app.register_blueprint(escala_bp)
app.register_blueprint(grupos_bp)
app.register_blueprint(guardians_bp)
app.register_blueprint(okrs_bp)
app.register_blueprint(register_bp)
app.register_blueprint(eventos_bp)
app.register_blueprint(operacao_bp)

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login.login'  

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def tarefa_horaria_processar_performance():
    with app.app_context():
        inicio = time.time()
        logging.info("[AGENDADO][PERFORMANCE PADRÃO] Início da tarefa.")
        try:
            resultado1 = processar_e_armazenar_performance_incremental()
            logging.info(f"[AGENDADO][PERFORMANCE PADRÃO] Resultado: {resultado1}")
        except Exception:
            logging.exception("[AGENDADO][PERFORMANCE PADRÃO] Erro durante execução.")
        finally:
            duracao = time.time() - inicio
            logging.info(f"[AGENDADO][PERFORMANCE PADRÃO] Fim da tarefa. Duração: {duracao:.2f} segundos.")


def tarefa_horaria_processar_performance_vyrtos():
    with app.app_context():
        inicio = time.time()
        logging.info("[AGENDADO][VYRTOS] Início da tarefa.")
        try:
            resultado1 = processar_e_armazenar_performance_vyrtos()
            logging.info(f"[AGENDADO][VYRTOS] Resultado: {resultado1}")
        except Exception:
            logging.exception("[AGENDADO][VYRTOS] Erro durante execução.")
        finally:
            duracao = time.time() - inicio
            logging.info(f"[AGENDADO][VYRTOS] Fim da tarefa. Duração: {duracao:.2f} segundos.")

def tarefa_importar_chamados():
    with app.app_context():
        try:
            total = importar_chamados()
            logging.info(f"[AGENDADO] {total} chamados importados com sucesso.")
        except Exception as e:
            logging.error(f"[AGENDADO] Erro ao importar chamados: {e}")

def tarefa_importar_psatisfacao():
    with app.app_context():
        try:
            total = importar_pSatisfacao()
            logging.info(f"[AGENDADO] {total} chamados importados com sucesso.")
        except Exception as e:
            logging.error(f"[AGENDADO] Erro ao importar chamados: {e}")

def tarefa_importar_fcr_reabertos():
    with app.app_context():
        try:
            importar_fcr_reabertos()
            logging.info("[AGENDADO] FCR e reabertos importados com sucesso.")
        except Exception as e:
            logging.error(f"[AGENDADO] Erro ao importar FCR e reabertos: {e}")

def tarefa_importar_registro_chamadas_saida_incremental():
    with app.app_context():
        try:
            importar_registro_chamadas_incremental()
            logging.info("[AGENDADO] Registro chamadas de saída com sucesso.")
        except Exception as e:
            logging.error(f"[AGENDADO] Erro ao importar registro de chamadas de saída: {e}")

def tarefa_importar_eventos():
    with app.app_context():
        inicio = time.time()
        logging.info("[AGENDADO][EVENTOS] Início da tarefa.")
        try:
            processar_e_armazenar_eventos()
            logging.info("[AGENDADO][EVENTOS] Importação concluída.")
        except Exception:
            logging.exception("[AGENDADO][EVENTOS] Erro durante execução.")
        finally:
            duracao = time.time() - inicio
            logging.info(f"[AGENDADO][EVENTOS] Fim da tarefa. Duração: {duracao:.2f} segundos.")

def tarefa_importar_detalhes_chamadas():
    with app.app_context():
        try:
            logging.info("[AGENDADO] Iniciando coleta e armazenamento de detalhes de chamadas...")
            resultado1 = importar_detalhes_chamadas_hoje()
            logging.info(f"[AGENDADO] Resultado padrão: {resultado1}")
        except Exception as e:
            logging.error(f"[AGENDADO] Erro ao importar detalhes de chamadas: {e}")

scheduler = APScheduler()

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('admin123'), is_admin=True)
        db.session.add(admin)
        db.session.commit()
        logging.info("Usuário admin criado com sucesso.")

    scheduler.init_app(app)

    logging.info(f"Jobs agendados antes da inicialização: {scheduler.get_jobs()}")

    scheduler.add_job(
        id='job_processa_performance_horaria',
        func=tarefa_horaria_processar_performance,
        trigger='interval',
        minutes=15
    )

    scheduler.add_job(
        id='job_processa_detalhes_chamadas',
        func=tarefa_importar_detalhes_chamadas,
        trigger='interval',
        minutes=10
    )

    scheduler.add_job(
        id='job_import_eventos',
        func=tarefa_importar_eventos,
        trigger='interval',
        minutes=17
    )

    scheduler.add_job(
        id='job_processa_registro_chamadas_saida',
        func=tarefa_importar_registro_chamadas_saida_incremental,
        trigger='interval',
        minutes=18
    )

    scheduler.add_job(
        id='job_processa_performance_horaria_vyrtos',
        func=tarefa_horaria_processar_performance_vyrtos,
        trigger='interval',
        minutes=19
    )

    scheduler.add_job(
        id='job_importar_chamados',
        func=tarefa_importar_chamados,
        trigger='interval',
        minutes=5
    )

    scheduler.add_job(
        id='job_importar_psatisfacao',
        func=tarefa_importar_psatisfacao,
        trigger='interval',
        minutes=5
    )

    scheduler.add_job(
        id='job_importar_fcr_reabertos',
        func=tarefa_importar_fcr_reabertos,
        trigger='interval',
        minutes=5
    )

    scheduler.start()
    logging.info("Tarefas agendadas iniciadas.")

logging.getLogger('apscheduler').setLevel(logging.DEBUG)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=False)


