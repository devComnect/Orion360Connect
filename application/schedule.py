import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
import time
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


def tarefa_horaria_processar_performance(app):
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


def tarefa_horaria_processar_performance_vyrtos(app):
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

def tarefa_importar_chamados(app):
    with app.app_context():
        try:
            total = importar_chamados()
            logging.info(f"[AGENDADO] {total} chamados importados com sucesso.")
        except Exception as e:
            logging.error(f"[AGENDADO] Erro ao importar chamados: {e}")

def tarefa_importar_psatisfacao(app):
    with app.app_context():
        try:
            total = importar_pSatisfacao()
            logging.info(f"[AGENDADO] {total} chamados importados com sucesso.")
        except Exception as e:
            logging.error(f"[AGENDADO] Erro ao importar chamados: {e}")

def tarefa_importar_fcr_reabertos(app):
    with app.app_context():
        try:
            importar_fcr_reabertos()
            logging.info("[AGENDADO] FCR e reabertos importados com sucesso.")
        except Exception as e:
            logging.error(f"[AGENDADO] Erro ao importar FCR e reabertos: {e}")

def tarefa_importar_registro_chamadas_saida_incremental(app):
    with app.app_context():
        try:
            importar_registro_chamadas_incremental()
            logging.info("[AGENDADO] Registro chamadas de saída com sucesso.")
        except Exception as e:
            logging.error(f"[AGENDADO] Erro ao importar registro de chamadas de saída: {e}")

def tarefa_importar_eventos(app):
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

def tarefa_importar_detalhes_chamadas(app):
    with app.app_context():
        try:
            logging.info("[AGENDADO] Iniciando coleta e armazenamento de detalhes de chamadas...")
            resultado1 = importar_detalhes_chamadas_hoje()
            logging.info(f"[AGENDADO] Resultado padrão: {resultado1}")
        except Exception as e:
            logging.error(f"[AGENDADO] Erro ao importar detalhes de chamadas: {e}")