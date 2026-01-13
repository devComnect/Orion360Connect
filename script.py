from app import app
from modules.tasks.tasks import repopular_eventos_operador_180d,repopular_eventos_180d, importar_detalhes_chamadas_hoje,importar_registro_chamadas_incremental, processar_e_armazenar_eventos,importar_grupos, processar_e_armazenar_performance, processar_e_armazenar_performance_vyrtos, importar_categorias, importar_pSatisfacao, importar_fcr_reabertos, processar_e_armazenar_performance_incremental, processar_e_armazenar_performance_vyrtos_incremental
from modules.tasks.tasks import importar_performance_operador, importar_detalhes_chamadas, importar_chamados, importar_chamados_debug # Repovoando individualmente
from datetime import date, datetime
from sqlalchemy import func
from settings.endpoints import CREDENTIALS
from modules.auth.utils import authenticate

from flask import Blueprint, jsonify, request
from modules.filas import utils
from modules.auth.utils import authenticate 
from application.models import Fila, FilaVyrtus, db
from settings.endpoints import CREDENTIALS
from datetime import datetime, timedelta
from sqlalchemy import func

'''with app.app_context():
    print("Tarefa em execução!")
    repopular_eventos_operador_180d(operador_id=2023, nome_operador='Raysa')'''



'''with app.app_context():
    print("Tarefa em execução!")
    importar_chamados_debug()'''


'''with app.app_context():
    importar_detalhes_chamadas(
        operador_id=2021,
        nome_operador="Matheus",
        data_inicio=date(2025, 10, 1),
        data_fim=date(2025, 10, 30)
    )'''

with app.app_context():
    registros = importar_performance_operador(
        operador_id=2012,
        nome_operador="Matheus",
        data_inicio=date(2025, 12, 20),
        data_fim=date(2026, 1, 2)
    )
    print(f"Total registros importados: {registros}")





'''def grafico_status_fila_hoje():
    try:
        id = 1

        # 1. Autenticar
        username = CREDENTIALS['username']
        password = CREDENTIALS['password']
        token = authenticate(username, password)

        # 2. Buscar dados da fila
        response = utils.get_filas(token, id)
        status = response.get("result", {}).get("status", {})

        if not status:
            return jsonify({"status": "error", "message": "Nenhuma informação encontrada para a fila"}), 204

        # 3. Extrair e processar dados
        chamadas_completadas = status.get("completed", 0)
        chamadas_abandonadas = status.get("abandoned", 0)
        transbordo = status.get("exitwithkey", 0)
        chamadas_recebidas = chamadas_completadas + chamadas_abandonadas + transbordo

        # 4. Limpar e salvar no banco
        with db.session.begin():
            db.session.query(Fila).delete()
            nova_fila = Fila(
                numero=status.get("number"),
                nome=status.get("name"),
                tipo=status.get("type"),
                chamadas_completadas=chamadas_completadas,
                chamadas_abandonadas=chamadas_abandonadas,
                transbordo=transbordo,
                chamadas_recebidas=chamadas_recebidas,
                tempo_espera=status.get("holdtime"),
                tempo_fala=status.get("talktime"),
                nivel_servico=status.get("servicelevelperf"),
                data=datetime.now()
            )
            db.session.add(nova_fila)

        # 5. Preparar dados por hora
        hoje = datetime.now().date()
        inicio_dia = datetime.combine(hoje, datetime.min.time())
        fim_dia = inicio_dia + timedelta(days=1)

        horas_do_dia = list(range(24))
        completadas_por_hora = {hora: 0 for hora in horas_do_dia}
        perdidas_por_hora = {hora: 0 for hora in horas_do_dia}  # abandonadas + transbordo

        # Completadas por hora
        resultados_completadas = db.session.query(
            func.extract('hour', Fila.data).label('hora'),
            func.sum(Fila.chamadas_completadas)
        ).filter(
            Fila.data >= inicio_dia,
            Fila.data < fim_dia
        ).group_by('hora').all()

        for hora, total in resultados_completadas:
            completadas_por_hora[int(hora)] = int(total or 0)

        # Perdidas por hora (abandonadas + transbordo)
        resultados_perdidas = db.session.query(
            func.extract('hour', Fila.data).label('hora'),
            (func.sum(Fila.chamadas_abandonadas) + func.sum(Fila.transbordo)).label('total_perdidas')
        ).filter(
            Fila.data >= inicio_dia,
            Fila.data < fim_dia
        ).group_by('hora').all()

        for hora, total in resultados_perdidas:
            perdidas_por_hora[int(hora)] = int(total or 0)

        print(completadas_por_hora)
        print(perdidas_por_hora)

        # 6. Retorno JSON para o gráfico
        return jsonify({
            'status': 'success',
            'labels': [f'{h:02d}:00' for h in horas_do_dia],
            'datasets': [
                {
                    'label': 'Chamadas Completadas',
                    'data': [completadas_por_hora[h] for h in horas_do_dia],
                    'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 2,
                    'fill': False
                },
                {
                    'label': 'Chamadas Perdidas',
                    'data': [perdidas_por_hora[h] for h in horas_do_dia],
                    'backgroundColor': 'rgba(255, 99, 132, 0.6)',
                    'borderColor': 'rgba(255, 99, 132, 1)',
                    'borderWidth': 2,
                    'fill': False
                }
            ],
            'data_referencia': hoje.strftime('%d/%m/%Y')
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500'''