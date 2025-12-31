from flask import Blueprint, jsonify, request
from modules.filas import utils
from modules.auth.utils import authenticate 
from application.models import Fila, FilaVyrtus, db
from settings.endpoints import CREDENTIALS
from datetime import datetime, timedelta
from sqlalchemy import func


filas_bp = Blueprint('filas_bp', __name__, url_prefix='/dashboard/call')

@filas_bp.route('/v2/report/queue_status', methods=['POST'])
def grafico_status_fila_hoje():
    try:
        id = 1

        username = CREDENTIALS['username']
        password = CREDENTIALS['password']
        token = authenticate(username, password)

        response = utils.get_filas(token, id)
        status = response.get("result", {}).get("status", {})

        if not status:
            return jsonify({"status": "error", "message": "Nenhuma informação encontrada para a fila"}), 204

        chamadas_completadas = status.get("completed", 0)
        chamadas_abandonadas = status.get("abandoned", 0)
        transbordo = status.get("exitwithkey", 0)
        chamadas_recebidas = chamadas_completadas + chamadas_abandonadas + transbordo

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
        perdidas_por_hora = {hora: 0 for hora in horas_do_dia}  

        resultados_completadas = db.session.query(
            func.extract('hour', Fila.data).label('hora'),
            func.sum(Fila.chamadas_completadas)
        ).filter(
            Fila.data >= inicio_dia,
            Fila.data < fim_dia
        ).group_by('hora').all()

        for hora, total in resultados_completadas:
            completadas_por_hora[int(hora)] = int(total or 0)

        resultados_perdidas = db.session.query(
            func.extract('hour', Fila.data).label('hora'),
            (func.sum(Fila.chamadas_abandonadas) + func.sum(Fila.transbordo)).label('total_perdidas')
        ).filter(
            Fila.data >= inicio_dia,
            Fila.data < fim_dia
        ).group_by('hora').all()

        for hora, total in resultados_perdidas:
            perdidas_por_hora[int(hora)] = int(total or 0)

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
        return jsonify({'status': 'error', 'message': str(e)}), 500

@filas_bp.route('/v2/report/queue_status_vyrtus', methods=['POST'])
def queue_status_vyrtus_hourly():
    id = 10
    try:
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
            db.session.query(FilaVyrtus).delete()
            nova_fila = FilaVyrtus(
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
        completadas_por_hora = {h: 0 for h in horas_do_dia}
        perdidas_por_hora = {h: 0 for h in horas_do_dia}  # perdidas = abandonadas + transbordo

        # Chamadas completadas por hora
        resultados_completadas = db.session.query(
            func.extract('hour', FilaVyrtus.data).label('hora'),
            func.sum(FilaVyrtus.chamadas_completadas)
        ).filter(
            FilaVyrtus.data >= inicio_dia,
            FilaVyrtus.data < fim_dia
        ).group_by('hora').all()

        for hora, total in resultados_completadas:
            completadas_por_hora[int(hora)] = int(total or 0)

        # Chamadas perdidas (abandonadas + transbordo) por hora
        resultados_perdidas = db.session.query(
            func.extract('hour', FilaVyrtus.data).label('hora'),
            (func.sum(FilaVyrtus.transbordo) + func.sum(FilaVyrtus.chamadas_abandonadas)).label("total_perdidas")
        ).filter(
            FilaVyrtus.data >= inicio_dia,
            FilaVyrtus.data < fim_dia
        ).group_by('hora').all()

        for hora, total in resultados_perdidas:
            perdidas_por_hora[int(hora)] = int(total or 0)

        # 6. Retorno JSON para o gráfico
        return jsonify({
            "status": "success",
            "data_referencia": hoje.strftime('%d/%m/%Y'),
            "labels": [f"{h:02d}:00" for h in horas_do_dia],
            "datasets": [
                {
                    "label": "Chamadas Completadas",
                    "data": [completadas_por_hora[h] for h in horas_do_dia],
                    "backgroundColor": "rgba(54, 162, 235, 0.5)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "borderWidth": 2,
                    "fill": False
                },
                {
                    "label": "Chamadas Perdidas",
                    "data": [perdidas_por_hora[h] for h in horas_do_dia],
                    "backgroundColor": "rgba(255, 99, 132, 0.6)",
                    "borderColor": "rgba(255, 99, 132, 1)",
                    "borderWidth": 2,
                    "fill": False
                }
            ]
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao gerar dados por hora.",
            "details": str(e)
        }), 500

@filas_bp.route('/v2/report/agents_status', methods=['POST'])
def agentes_online_status():
    id = 1  
    try:
        username = CREDENTIALS['username']
        password = CREDENTIALS['password']
        token = authenticate(username, password)

        response = utils.get_filas(token, id)
        status = response.get("result", {}).get("status", {})

        if not status:
            return jsonify({"status": "error", "message": "Nenhuma informação encontrada para a fila"}), 204

        members = status.get("members", [])
        if not members:
            return jsonify({"status": "success", "members": [], "message": "Nenhum agente online encontrado."})

        agentes = []
        now_timestamp = int(datetime.now().timestamp())

        for m in members:
            tempo_online_segundos = now_timestamp - m.get("entryTime", now_timestamp)

            em_pausa = m.get("penalty", 0) > 0
            
            motivo_pausa = m.get("pause_reason", "Indefinido") if em_pausa else None

            agente = {
                "agentNumber": m.get("agentNumber"),
                "tempo_online": tempo_online_segundos,
                "em_pausa": em_pausa,
                "motivo_pausa": motivo_pausa
            }
            agentes.append(agente)

        return jsonify({
            "status": "success",
            "members": agentes
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao obter status dos agentes.",
            "details": str(e)
        }), 500
