from flask import Blueprint, jsonify, request, json
import modules.tasks.relatorios.utils as utils
from application.models import db, DesempenhoAtendente, DesempenhoAtendenteVyrtos, PerformanceColaboradores
from modules.auth.utils import authenticate, authenticate_relatorio
from settings.endpoints import CREDENTIALS
from datetime import datetime, timedelta
import json

relatorio_bp = Blueprint('relatorio_bp', __name__, url_prefix='/dashboard/call')

@relatorio_bp.route('/v2/report/call_detailing', methods=['GET'])
def situacaoFila():
    
    auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
    
    if "access_token" not in auth_response:
        return jsonify({"error": "Falha na autenticação", "detalhes": auth_response}), auth_response.get("status_code", 401)
    
    access_token = auth_response["access_token"]

    # Coleta de parâmetros via query string
    class Params:
        initial_date = request.args.get('initial_date')
        initial_hour = request.args.get('initial_hour')
        final_date = request.args.get('final_date')
        final_hour = request.args.get('final_hour')
        fixed = request.args.get('fixed', '0')
        week = request.args.get('week', '')  # "1,2,3"
        options = request.args.get('options', '{}')  # precisa estar em JSON string
        queues = request.args.get('queues', '')  # "101,102"
        agents = request.args.get('agents', '')  # "1001,1002"
        transfer_display = request.args.get('transfer_display', '0')

    result = utils.get_relatorio(access_token, Params)
    return jsonify(result)

@relatorio_bp.route('/v2/report/login_logoff', methods=['GET'])
def relatorioLoginLogoff():
    # Autenticando com usuário fixo
    auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
    
    if "access_token" not in auth_response:
        return jsonify({
            "error": "Falha na autenticação",
            "detalhes": auth_response
        }), auth_response.get("status_code", 401)

    access_token = auth_response["access_token"]

    # Pega os parâmetros da query string
    class Params:
        initial_date = request.args.get('initial_date')
        initial_hour = request.args.get('initial_hour')
        final_date = request.args.get('final_date')
        final_hour = request.args.get('final_hour')
        fixed = request.args.get('fixed', '0')
        week = request.args.get('week', '')  # ex: "1,2,3,4,5"
        options = request.args.get('options', '{"sort":{"data":-1},"offset":0,"count":100}')
        agents = request.args.get('agents', '')  # ex: "1001,1002"

    response = utils.get_relatorio_login_logoff(access_token, Params)

    return jsonify(response)

@relatorio_bp.route('/v2/report/call_detailing_outgoing', methods=['GET'])
def chamadaSaida():
       # Autenticando com usuário fixo
    auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
    
    if "access_token" not in auth_response:
        return jsonify({
            "error": "Falha na autenticação",
            "detalhes": auth_response
        }), auth_response.get("status_code", 401)

    access_token = auth_response["access_token"]

    # Pega os parâmetros da query string
    class Params:
        initial_date = request.args.get('initial_date')
        initial_hour = request.args.get('initial_hour')
        final_date = request.args.get('final_date')
        final_hour = request.args.get('final_hour')
        fixed = request.args.get('fixed', '0')
        week = request.args.get('week', '')  # ex: "1,2,3,4,5"
        options = request.args.get('options', '{"sort":{"data":-1},"offset":0,"count":100}')
        conf = request.args.get('conf', '')
        agents = request.args.get('agents', '')  # ex: "1001,1002"

    response = utils.get_chamada_saida(access_token, Params)

    return jsonify(response)

'''@relatorio_bp.route('/v2/report/attendants_performance', methods=['GET'])

def performanceAtendente():
       # Autenticando com usuário fixo
    auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
    
    if "access_token" not in auth_response:
        return jsonify({
            "error": "Falha na autenticação",
            "detalhes": auth_response
        }), auth_response.get("status_code", 401)

    access_token = auth_response["access_token"]

     # Pega os parâmetros da query string
    class Params:
        initial_date = request.args.get('initial_date')
        initial_hour = request.args.get('initial_hour')
        final_date = request.args.get('final_date')
        final_hour = request.args.get('final_hour')
        week = request.args.get('week', '')

        # trata strings como listas separadas por vírgula
        agents = request.args.get('agents', '')
        if agents:
            agents = [int(x.strip()) for x in agents.split(',') if x.strip().isdigit()]
        else:
            agents = []

        queues = request.args.get('queues', '')
        if queues:
            queues = [int(x.strip()) for x in queues.split(',') if x.strip().isdigit()]
        else:
            queues = []

        # tenta carregar JSON, se falhar, cai para dicionário vazio
        try:
            options = json.loads(request.args.get('options', '{}'))
        except json.JSONDecodeError:
            options = {}

        try:
            conf = json.loads(request.args.get('conf', '{}'))
        except json.JSONDecodeError:
            conf = {}


    response = utils.atendentePerformance(access_token, Params)
    #print(response)

    return jsonify(response)'''

'''@relatorio_bp.route('/v2/report/attendants_performance', methods=['POST'])
def importar_ligacoes_atendidas():
    try:
        # 1. Autenticar com usuário fixo
        auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
        if "access_token" not in auth_response:
            return jsonify({"status": "error", "message": "Falha na autenticação", "detalhes": auth_response}), 401

        access_token = auth_response["access_token"]

        hoje = datetime.now()

        # Obtém o primeiro dia do mês atual
        primeiro_dia_mes = datetime.now().replace(day=1)
    
        # Obtém o último dia do mês atual
        ultimo_dia_mes = (primeiro_dia_mes.replace(month=primeiro_dia_mes.month % 12 + 1, day=1) - timedelta(days=1))

        # 2. Montar parâmetros
        class Params:
            initial_date = hoje.strftime('%Y-%m-%d')
            final_date = hoje.strftime('%Y-%m-%d')
            initial_hour = "00:00:00"
            final_hour = "23:59:59"
            week = ""
            fixed = 0
            agents = [2020, 2021, 2022, 2023, 2024, 2025, 2028, 2029]
            queues = [1]
            options = {
                "sort": {"data": -1},
                "offset": 0,
                "count": 1000
            }
            conf = {}

        # 3. Requisição à API utilitária
        response = utils.atendentePerformance(access_token, Params)
        #print(response)
        dados_atendentes = response.get("result", {}).get("data", [])


        if not dados_atendentes:
            return jsonify({"status": "error", "message": "Nenhum dado retornado"}), 204

        # 4. Inserir no banco (com limpeza antes)
        with db.session.begin():
            db.session.query(DesempenhoAtendente).delete()

            for item in dados_atendentes:
                nome = item.get("atendente")
                data_str = item.get("data")
                try:
                    data = datetime.strptime(data_str, "%Y-%m-%d").date()
                except Exception:
                    continue

                novo = DesempenhoAtendente(
                    nome=nome,
                    chamadas_atendidas=item.get("ch_atendidas"),
                    data=data,
                    tempo_online=item.get("tempo_online"),
                    tempo_servico=item.get("tempo_servico"),
                    tempo_totalatend=item.get("tempo_totalatend"),
                )
                db.session.add(novo)

        # 6. CONSULTA AJUSTADA - Aqui está a mudança principal
        resultados = (
            db.session.query(
                DesempenhoAtendente.nome,
                db.func.sum(DesempenhoAtendente.chamadas_atendidas).label('total')
            )
            .filter(
                DesempenhoAtendente.data.between(
                    primeiro_dia_mes.date(),
                    ultimo_dia_mes.date()
                )
            )
            .group_by(DesempenhoAtendente.nome)
            .all()
        )

        dados_grafico = [
            {"nome": nome, "total": total}
            for nome, total in resultados
        ]

        return jsonify({
            "status": "success",
            "data": dados_grafico,
            "registros_importados": len(dados_atendentes)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Erro inesperado",
            "details": str(e)
        }), 500'''

# Versão futura do attendants_performance
@relatorio_bp.route('/v2/report/attendants_performance', methods=['POST'])
def buscar_desempenho_atendentes():
    try:
        hoje = datetime.now().date()  # apenas a data
        ontem = hoje - timedelta(days=1)

        # Consulta no banco de dados PerformanceColaboradores
        resultados = (
            db.session.query(
                PerformanceColaboradores.name,
                db.func.sum(PerformanceColaboradores.ch_atendidas).label('total')
            )
            .filter(PerformanceColaboradores.data == hoje)
            .group_by(PerformanceColaboradores.name)
            .all()
        )

        dados_grafico = [
            {"nome": nome, "total": total}
            for nome, total in resultados
        ]

        return jsonify({
            "status": "success",
            "data": dados_grafico,
            "registros_encontrados": len(dados_grafico)
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Erro inesperado ao buscar desempenho de atendentes.",
            "details": str(e)
        }), 500

'''@relatorio_bp.route('/v2/report/attendants_performance_vyrtos', methods=['POST'])
def importar_ligacoes_atendidas_vyrtos():
    try:
        # 1. Autenticar com usuário fixo
        auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
        if "access_token" not in auth_response:
            return jsonify({"status": "error", "message": "Falha na autenticação", "detalhes": auth_response}), 401

        access_token = auth_response["access_token"]

        hoje = datetime.now()

        # Obtém o primeiro dia do mês atual
        primeiro_dia_mes = datetime.now().replace(day=1)
    
        # Obtém o último dia do mês atual
        ultimo_dia_mes = (primeiro_dia_mes.replace(month=primeiro_dia_mes.month % 12 + 1, day=1) - timedelta(days=1))

        # 2. Montar parâmetros
        class Params:
            initial_date = hoje.strftime('%Y-%m-%d')
            final_date = hoje.strftime('%Y-%m-%d')
            initial_hour = "00:00:00"
            final_hour = "23:59:59"
            week = ""
            fixed = 0
            agents = [2020, 2021, 2022, 2023, 2024, 2025, 2028, 2029]
            queues = [10]
            options = {
                "sort": {"data": -1},
                "offset": 0,
                "count": 1000
            }
            conf = {}

        # 3. Requisição à API utilitária
        response = utils.atendentePerformance(access_token, Params)
        #print(response)
        dados_atendentes = response.get("result", {}).get("data", [])


        if not dados_atendentes:
            return jsonify({"status": "error", "message": "Nenhum dado retornado"}), 204

        # 4. Inserir no banco (com limpeza antes)
        with db.session.begin():
            db.session.query(DesempenhoAtendenteVyrtos).delete()

            for item in dados_atendentes:
                nome = item.get("atendente")
                data_str = item.get("data")
                try:
                    data = datetime.strptime(data_str, "%Y-%m-%d").date()
                except Exception:
                    continue

                novo = DesempenhoAtendenteVyrtos(
                    nome=nome,
                    chamadas_atendidas=item.get("ch_atendidas"),
                    data=data,
                    tempo_online=item.get("tempo_online"),
                    tempo_servico=item.get("tempo_servico"),
                    tempo_totalatend=item.get("tempo_totalatend"),
                )
                db.session.add(novo)

        # 6. CONSULTA AJUSTADA - Aqui está a mudança principal
        resultados = (
            db.session.query(
                DesempenhoAtendenteVyrtos.nome,
                db.func.sum(DesempenhoAtendenteVyrtos.chamadas_atendidas).label('total')
            )
            .filter(
                DesempenhoAtendenteVyrtos.data.between(
                    primeiro_dia_mes.date(),
                    ultimo_dia_mes.date()
                )
            )
            .group_by(DesempenhoAtendenteVyrtos.nome)
            .all()
        )

        dados_grafico = [
            {"nome": nome, "total": total}
            for nome, total in resultados
        ]

        return jsonify({
            "status": "success",
            "data": dados_grafico,
            "registros_importados": len(dados_atendentes)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Erro inesperado",
            "details": str(e)
        }), 500'''

@relatorio_bp.route('/v2/report/attendants_performance_vyrtos', methods=['POST'])
def buscar_ligacoes_atendidas_vyrtos():
    try:
        hoje = datetime.now().date()

        resultados = (
            db.session.query(
                DesempenhoAtendenteVyrtos.name,
                db.func.sum(DesempenhoAtendenteVyrtos.ch_atendidas).label('total')
            )
            .filter(DesempenhoAtendenteVyrtos.data == hoje)
            .group_by(DesempenhoAtendenteVyrtos.name)
            .all()
        )

        dados_grafico = [
            {"nome": nome, "total": total}
            for nome, total in resultados
        ]

        return jsonify({
            "status": "success",
            "data": dados_grafico,
            "registros_encontrados": len(dados_grafico)
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao buscar dados locais",
            "details": str(e)
        }), 500

@relatorio_bp.route('/GetEventosAtendente', methods=['POST'])
def get_eventos_atendente():
    return
