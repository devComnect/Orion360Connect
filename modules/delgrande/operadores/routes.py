from flask import Blueprint, jsonify, request, render_template, url_for, session
import modules.delgrande.relatorios.utils as utils
from application.models import db, DesempenhoAtendente, DesempenhoAtendenteVyrtos, PerformanceColaboradores, PesquisaSatisfacao, RelatorioColaboradores 
from modules.delgrande.auth.utils import authenticate, authenticate_relatorio
from application.models import Chamado
from settings.endpoints import CREDENTIALS
from datetime import datetime, timedelta, date
from sqlalchemy import func, cast, Date, and_, or_


operadores_bp = Blueprint('operadores_bp', __name__, url_prefix='/operadores')


'''@operadores_bp.route('/performanceColaboradores', methods=['POST'])
def get_performance_colaboradores():
    OPERADORES_IDS = {
        "Matheus": 2021,
        "Renato": 2020,
        "Gustavo": 2022,
        "Raysa": 2023,
        "Danilo": 2025
    }

    data = request.get_json()
    nome = data.get('nome')
    dias_str = str(data.get('dias', '1'))

    operador_id = OPERADORES_IDS.get(nome)

    # Autenticação
    auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
    if "access_token" not in auth_response:
        return jsonify({"status": "error", "message": "Falha na autenticação"}), 401

    access_token = auth_response["access_token"]

    hoje = datetime.now()
    ontem = hoje - timedelta(days=1)

    # Ajuste no cálculo das datas
    periodos = {
        "1": (ontem).strftime('%Y-%m-%d'),  # Ontem
        "7": (hoje - timedelta(days=6)).strftime('%Y-%m-%d'),  # Inclui 7 dias (ontem + hoje)
        "15": (hoje - timedelta(days=14)).strftime('%Y-%m-%d'),  # Últimos 15 dias
        "30": (hoje - timedelta(days=29)).strftime('%Y-%m-%d'),  # Últimos 30 dias
        "90": (hoje - timedelta(days=89)).strftime('%Y-%m-%d')  # Últimos 90 dias
    }

    # Pega a data inicial com base no parâmetro "dias" ou o valor padrão "1"
    data_inicial = periodos.get(dias_str, periodos["1"])
    data_final = (hoje - timedelta(days=1)).strftime('%Y-%m-%d')  # Ontem

    # Parâmetros para a consulta
    class Params:
        initial_date = data_inicial
        final_date = data_final
        initial_hour = "00:00:00"
        final_hour = "23:59:59"
        fixed = 0
        week = ""
        agents = [operador_id]
        queues = [1]
        options = {"sort": {"data": -1}, "offset": 0, "count": 1000}
        conf = {}

    # Chama a função de performance
    response = utils.atendentePerformance(access_token, Params)
    print(response)

    # Processa os dados de atendentes
    dados_atendentes = response.get("result", {}).get("data", [])
    print(dados_atendentes)

    acumulado = {
        "ch_atendidas": 0,
        "ch_naoatendidas": 0,
        "tempo_online": 0,
        "tempo_livre": 0,
        "tempo_servico": 0,
        "pimprod_Refeicao": 0,
        "tempo_minatend": None,
        "tempo_medatend": [],
        "tempo_maxatend": None
    }

    # Itera sobre os dados recebidos e acumula os valores
    for item in dados_atendentes:
        acumulado["ch_atendidas"] += int(item.get("ch_atendidas") or 0)
        acumulado["ch_naoatendidas"] += int(item.get("ch_naoatendidas") or 0)
        acumulado["tempo_online"] += int(item.get("tempo_online") or 0)
        acumulado["tempo_livre"] += int(item.get("tempo_livre") or 0)
        acumulado["tempo_servico"] += int(item.get("tempo_servico") or 0)
        acumulado["pimprod_Refeicao"] += int(item.get("pimprod_Refeicao") or 0)

        if item.get("tempo_minatend") is not None:
            acumulado["tempo_minatend"] = (
                item["tempo_minatend"]
                if acumulado["tempo_minatend"] is None
                else min(acumulado["tempo_minatend"], item["tempo_minatend"])
            )

        if item.get("tempo_maxatend") is not None:
            acumulado["tempo_maxatend"] = (
                item["tempo_maxatend"]
                if acumulado["tempo_maxatend"] is None
                else max(acumulado["tempo_maxatend"], item["tempo_maxatend"])
            )

        if item.get("tempo_medatend") is not None:
            acumulado["tempo_medatend"].append(item["tempo_medatend"])

    # Calcula a média do tempo de atendimento
    media_geral = (
        sum(acumulado["tempo_medatend"]) / len(acumulado["tempo_medatend"])
        if acumulado["tempo_medatend"] else 0
    )

    # Organiza os dados para o retorno
    dados = {
        "periodo": dias_str,
        "ch_atendidas": acumulado["ch_atendidas"],
        "ch_naoatendidas": acumulado["ch_naoatendidas"],
        "tempo_online": acumulado["tempo_online"],
        "tempo_livre": acumulado["tempo_livre"],
        "tempo_servico": acumulado["tempo_servico"],
        "pimprod_Refeicao": acumulado["pimprod_Refeicao"],
        "tempo_minatend": acumulado["tempo_minatend"] or 0,
        "tempo_medatend": round(media_geral, 2),
        "tempo_maxatend": acumulado["tempo_maxatend"] or 0
    }

    return jsonify({"status": "success", "dados": dados})'''

@operadores_bp.route('/performanceColaboradoresRender', methods=['POST'])
def performance_colaboradores_render():
    session.pop('dados', None)
    session.pop('nome', None)
    data = request.get_json()
    nome = data.get('nome')

    if not nome:
        return jsonify({"status": "error", "message": "Nome do operador não fornecido"}), 400

    ontem = date.today() - timedelta(days=1)

    registros = PerformanceColaboradores.query.filter(
        PerformanceColaboradores.name == nome,
        PerformanceColaboradores.data == ontem
    )

    acumulado = {
        "ch_atendidas": 0,
        "ch_naoatendidas": 0,
        "tempo_online": 0,
        "tempo_livre": 0,
        "tempo_servico": 0,
        "pimprod_Refeicao": 0,
        "tempo_minatend": None,
        "tempo_medatend": [],
        "tempo_maxatend": None
    }

    for item in registros:
        acumulado["ch_atendidas"] = item.ch_atendidas
        acumulado["ch_naoatendidas"] += item.ch_naoatendidas
        acumulado["tempo_online"] += item.tempo_online
        acumulado["tempo_livre"] += item.tempo_livre
        acumulado["tempo_servico"] += item.tempo_servico
        acumulado["pimprod_Refeicao"] += item.pimprod_refeicao

        if item.tempo_minatend is not None:
            acumulado["tempo_minatend"] = (
                item.tempo_minatend
                if acumulado["tempo_minatend"] is None
                else min(acumulado["tempo_minatend"], item.tempo_minatend)
            )

        if item.tempo_maxatend is not None:
            acumulado["tempo_maxatend"] = (
                item.tempo_maxatend
                if acumulado["tempo_maxatend"] is None
                else max(acumulado["tempo_maxatend"], item.tempo_maxatend)
            )

        if item.tempo_medatend is not None:
            acumulado["tempo_medatend"].append(item.tempo_medatend)

    media_geral = (
        sum(acumulado["tempo_medatend"]) / len(acumulado["tempo_medatend"])
        if acumulado["tempo_medatend"] else 0
    )

    dados = {
        "ch_atendidas": acumulado["ch_atendidas"],
        "ch_naoatendidas": acumulado["ch_naoatendidas"],
        "tempo_online": acumulado["tempo_online"],
        "tempo_livre": acumulado["tempo_livre"],
        "tempo_servico": acumulado["tempo_servico"],
        "pimprod_Refeicao": acumulado["pimprod_Refeicao"],
        "tempo_minatend": acumulado["tempo_minatend"] or 0,
        "tempo_medatend": round(media_geral, 2),
        "tempo_maxatend": acumulado["tempo_maxatend"] or 0
    }

    session['nome'] = nome
    session['dados'] = dados

    return jsonify({"redirect_url": url_for('operadores_bp.render_operadores')})

@operadores_bp.route('/colaboradores', methods=['GET'])
def render_operadores():
    nome = session.get('nome')
    dados = session.get('dados')

    if not nome or not dados:
        return "Dados não encontrados na sessão", 400

    return render_template('colaboradores.html', nome=nome, dados=dados)

@operadores_bp.route('/performanceColaboradores', methods=['POST'])
def get_performance_colaboradores():
    data = request.get_json()
    nome = data.get('nome', '').strip().title()  # normaliza o nome
    dias_str = str(data.get('dias', '1'))

    if not nome:
        return jsonify({"status": "error", "message": "Nome do operador não fornecido"}), 400

    # Busca o operador_id diretamente no banco usando o nome
    operador = PerformanceColaboradores.query.filter_by(name=nome).first()

    if not operador:
        return jsonify({"status": "error", "message": f"Operador '{nome}' não encontrado"}), 404

    operador_id = operador.operador_id

    hoje = datetime.now().date()
    ontem = hoje - timedelta(days=1)

    try:
        dias = int(dias_str)
    except ValueError:
        return jsonify({"status": "error", "message": "O valor de 'dias' deve ser um número inteiro"}), 400

    data_inicial = hoje - timedelta(days=dias)

    registros = PerformanceColaboradores.query.filter(
        PerformanceColaboradores.operador_id == operador_id,
        PerformanceColaboradores.data >= data_inicial,
        PerformanceColaboradores.data <= hoje
    ).all()


    # Inicializa os acumuladores
    acumulado = {
        "ch_atendidas": 0,
        "ch_naoatendidas": 0,
        "tempo_online": 0,
        "tempo_livre": 0,
        "tempo_servico": 0,
        "pimprod_Refeicao": 0,
        "tempo_minatend": None,
        "tempo_medatend": [],
        "tempo_maxatend": None
    }

    for r in registros:
        acumulado["ch_atendidas"] += r.ch_atendidas
        acumulado["ch_naoatendidas"] += r.ch_naoatendidas
        acumulado["tempo_online"] += r.tempo_online
        acumulado["tempo_livre"] += r.tempo_livre
        acumulado["tempo_servico"] += r.tempo_servico
        acumulado["pimprod_Refeicao"] += r.pimprod_refeicao

        if r.tempo_minatend is not None:
            acumulado["tempo_minatend"] = r.tempo_minatend if acumulado["tempo_minatend"] is None else min(acumulado["tempo_minatend"], r.tempo_minatend)

        if r.tempo_maxatend is not None:
            acumulado["tempo_maxatend"] = r.tempo_maxatend if acumulado["tempo_maxatend"] is None else max(acumulado["tempo_maxatend"], r.tempo_maxatend)

        if r.tempo_medatend is not None:
            acumulado["tempo_medatend"].append(r.tempo_medatend)

    media_geral = (
        sum(acumulado["tempo_medatend"]) / len(acumulado["tempo_medatend"])
        if acumulado["tempo_medatend"] else 0
    )

    dados = {
        "periodo": dias_str,
        "ch_atendidas": acumulado["ch_atendidas"],
        "ch_naoatendidas": acumulado["ch_naoatendidas"],
        "tempo_online": acumulado["tempo_online"],
        "tempo_livre": acumulado["tempo_livre"],
        "tempo_servico": acumulado["tempo_servico"],
        "pimprod_Refeicao": acumulado["pimprod_Refeicao"],
        "tempo_minatend": acumulado["tempo_minatend"] or 0,
        "tempo_medatend": round(media_geral, 2),
        "tempo_maxatend": acumulado["tempo_maxatend"] or 0
    }

    return jsonify({"status": "success", "dados": dados})

@operadores_bp.route('/ChamadosSuporte/ticketsOperador', methods=['POST'])
def chamados_por_operador_periodo():
    try:
        data = request.json
        nome_operador = data.get("nome")
        dias = int(data.get("dias"))

        if not nome_operador:
            return jsonify({"status": "error", "message": "Nome do operador não fornecido."}), 400

        hoje = datetime.now().date()

        if dias == 1:
            data_inicio = hoje - timedelta(days=1)  # apenas ontem
            data_fim = data_inicio
        else:
            data_inicio = hoje - timedelta(days=dias)
            data_fim = hoje  # até hoje

        chamados = db.session.query(
            Chamado.cod_chamado,
            Chamado.cod_solicitacao,
            Chamado.data_criacao,
            Chamado.data_finalizacao,
            Chamado.nome_grupo,
            Chamado.nome_status
        ).filter(
            cast(Chamado.data_criacao, Date) >= data_inicio,
            cast(Chamado.data_criacao, Date) <= data_fim,
            Chamado.operador == nome_operador
        ).all()

        lista_chamados = [{
            "cod_chamado": c.cod_chamado,
            "cod_solicitacao": c.cod_solicitacao,
            "data_criacao": c.data_criacao.strftime("%Y-%m-%d %H:%M:%S") if c.data_criacao else None,
            "data_finalizacao": c.data_finalizacao.strftime("%Y-%m-%d %H:%M:%S") if c.data_finalizacao else None,
            "nome_grupo": c.nome_grupo,
            "nome_status": c.nome_status
        } for c in chamados]

        return jsonify({
            "status": "success",
            "total_chamados": len(lista_chamados),
            "data_referencia": f"{data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}",
            "chamados": lista_chamados
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@operadores_bp.route('/ChamadosSuporte/ticketsTelefoneVsAtendidas', methods=['POST'])
def chamados_telefone_vs_atendidas():
    try:
        dias_str = str(request.json.get("dias"))
        nome_operador = request.json.get("nome", "").strip().title()

        if not nome_operador:
            return jsonify({'status': 'error', 'message': 'Nome do operador não fornecido'}), 400

        operador = PerformanceColaboradores.query.filter_by(name=nome_operador).first()
        #if not operador:
        #    return jsonify({'status': 'error', 'message': f"Operador '{nome_operador}' não encontrado"}), 404

        operador_id = operador.operador_id

        hoje = datetime.now().date()
        ontem = hoje - timedelta(days=1)

        periodos = {
            "1": hoje,
            "7": hoje - timedelta(days=7),
            "15": hoje - timedelta(days=15),
            "30": hoje - timedelta(days=30),
            "90": hoje - timedelta(days=90),
            "180": hoje - timedelta(days=180)
        }

        data_inicial = periodos.get(dias_str)
        data_final = hoje

        lista_dias = [
            data_inicial + timedelta(days=i)
            for i in range((data_final - data_inicial).days + 1)
        ]
        labels = [dia.strftime('%d/%m') for dia in lista_dias]

        # === TICKETS (com filtro para remover cancelados)
        chamados_result = db.session.query(
            func.date(Chamado.data_criacao).label('dia'),
            func.count(Chamado.id)
        ).filter(
            Chamado.cod_solicitacao == '000004',
            Chamado.operador == nome_operador,
            func.date(Chamado.data_criacao).in_(lista_dias)
        ).group_by(
            func.date(Chamado.data_criacao)
        ).all()

        chamados_por_dia = {dia: total for dia, total in chamados_result}
        dados_chamados = [chamados_por_dia.get(dia, 0) for dia in lista_dias]

        # === LIGAÇÕES
        atendimentos_result = db.session.query(
            PerformanceColaboradores.data,
            func.sum(PerformanceColaboradores.ch_atendidas)
        ).filter(
            PerformanceColaboradores.operador_id == operador_id,
            PerformanceColaboradores.data >= data_inicial,
            PerformanceColaboradores.data <= data_final
        ).group_by(
            PerformanceColaboradores.data
        ).all()

        atendimentos_por_dia_map = {data: total for data, total in atendimentos_result}
        atendimentos_por_dia = [atendimentos_por_dia_map.get(dia, 0) for dia in lista_dias]

        # === TOTALIZAÇÃO E DIFERENÇA
        total_tickets = sum(dados_chamados)
        total_ligacoes = sum(atendimentos_por_dia)
        diferenca = total_tickets - total_ligacoes

        return jsonify({
            'status': 'success',
            'data': {
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Tickets',
                        'data': dados_chamados,
                        'backgroundColor': 'rgba(255, 99, 132, 0.5)',
                        'borderColor': 'rgba(255, 99, 132, 1)',
                        'fill': False,
                        'tension': 0.3
                    },
                    {
                        'label': 'Ligações',
                        'data': atendimentos_por_dia,
                        'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                        'borderColor': 'rgba(54, 162, 235, 1)',
                        'fill': False,
                        'tension': 0.3
                    }
                ],
                'resumo': {
                    'total_tickets': total_tickets,
                    'total_ligacoes': total_ligacoes,
                    'diferenca': diferenca
                }
            }
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@operadores_bp.route('/GetSlaOperador', methods=['POST'])
def get_sla_operador():
    data = request.get_json()
    nome = data.get('nome')

    dias = int(data.get('dias', 1))

    data_inicio = datetime.now() - timedelta(days=dias)

    # Filtro com operador, período e grupo de suporte
    chamados = Chamado.query.filter(
        #Chamado.nome_grupo.ilike('%SUPORTE%'),
        Chamado.nome_status != 'Cancelado',
        Chamado.operador == nome,
        Chamado.data_criacao >= data_inicio
    ).all()

    # Filtra apenas os expirados
    chamados_expirados = [
        c for c in chamados if c.sla_atendimento == 'S' or c.sla_resolucao == 'S'
    ]

    expirados_atendimento = sum(1 for c in chamados if c.sla_atendimento == 'S')
    expirados_resolucao = sum(1 for c in chamados if c.sla_resolucao == 'S')
    


    return jsonify({
        "chamados": [c.to_dict() for c in chamados_expirados],
        "expirados_atendimento": expirados_atendimento,
        "expirados_resolucao": expirados_resolucao,
        "codigos_atendimento": [c.cod_chamado for c in chamados_expirados if c.sla_atendimento == 'S'],
        "codigos_resolucao": [c.cod_chamado for c in chamados_expirados if c.sla_resolucao == 'S']
    })

@operadores_bp.route('/pSatisfacaoOperador', methods=['POST'])
def listar_p_satisfacao():
    data = request.get_json()
    dias = int(data.get('dias'))
    nome = data.get('nome')

    data_limite = (datetime.now() - timedelta(days=dias)).date()

    CSAT_MAP = {
        'Péssimo': 1,
        'Discordo Totalmente': 2,
        'Discordo Parcialmente': 3,
        'Neutro': 4,
        'Concordo Parcialmente': 5,
        'Regular': 6,
        'Bom': 7,
        'Concordo': 8,
        'Concordo Plenamente': 9,
        'Ótimo': 10
    }

    # Buscar todas as alternativas preenchidas no período
    alternativas_brutas = db.session.query(PesquisaSatisfacao.alternativa).filter(
        and_(
            PesquisaSatisfacao.data_resposta >= data_limite,
            PesquisaSatisfacao.alternativa.isnot(None),
            func.length(PesquisaSatisfacao.alternativa) > 0,
            PesquisaSatisfacao.operador.ilike(f"{nome}%")
            )
    ).all()

    respostas_convertidas = []

    for alt in alternativas_brutas:
        valor = alt[0].strip()
        # Se for número direto (ex: '8', '10')
        if valor.isdigit():
            numero = int(valor)
            if 0 <= numero <= 10:
                respostas_convertidas.append(numero)
        # Se for texto mapeado (ex: 'Concordo')
        elif valor in CSAT_MAP:
            respostas_convertidas.append(CSAT_MAP[valor])

    total_respondidas = len(respostas_convertidas)

    # Considerar como satisfatórias as notas 8 a 10
    respostas_satisfatorias = sum(1 for nota in respostas_convertidas if nota >= 7)

    # Cálculo do CSAT
    csat = round((respostas_satisfatorias / total_respondidas) * 100, 2) if total_respondidas else 0

    return jsonify({
        "status": "success",
        "total_respondidas": total_respondidas,
        "respostas_satisfatorias": respostas_satisfatorias,
        "csat": csat
    })

@operadores_bp.route('/performanceColaboradoresRender/n2', methods=['POST'])
def performance_colaboradores_render_n2():
    session.pop('dados', None)
    session.pop('nome', None)

    data = request.get_json()
    nome = data.get('nome')

    session['nome'] = nome

    return jsonify({"redirect_url": url_for('operadores_bp.render_operadores_n2')})

@operadores_bp.route('/getChamadosAbertos', methods=['POST'])
def get_chamados_abertos():
    try:
        data = request.get_json()
        nome = data.get('nome')
        dias = int(data.get('dias', 1))  # padrão 1 dia

        if not nome:
            return jsonify({"status": "error", "message": "Nome do operador não fornecido."}), 400

        hoje = datetime.now().date()
        data_inicio = hoje - timedelta(days=dias)

        # Limites de data com horário completo
        inicio = datetime.combine(data_inicio, datetime.min.time())
        fim = datetime.combine(hoje, datetime.max.time())

        # Filtra chamados abertos para o operador
        chamados = Chamado.query.filter(
            Chamado.nome_status.notin_(['Cancelado', 'Resolvido']),
            Chamado.data_criacao >= inicio,
            Chamado.data_criacao <= fim,
            Chamado.operador == nome
        ).all()

        total_chamados = len(chamados)
        codigos = [c.cod_chamado for c in chamados]

        return jsonify({
            "status": "success",
            "total_chamados": total_chamados,
            "cod_chamados": codigos
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@operadores_bp.route('/tma_tms/colaboradores', methods=['POST'])
def tma_e_tms_colaboradores():
    try:
        data = request.get_json()
        dias = int(data.get("dias", 1))
        nome = data.get("nome", "").strip()

        data_limite = datetime.utcnow() - timedelta(days=dias)

        query = db.session.query(Chamado).filter(
            Chamado.data_criacao >= data_limite,
            Chamado.data_criacao.isnot(None),
            Chamado.restante_p_atendimento.isnot(None),
            Chamado.restante_s_atendimento.isnot(None),
            Chamado.nome_status.ilike('%Resolvido%')
        )

        if nome:
            query = query.filter(Chamado.operador.ilike(f'%{nome}%'))

        chamados_validos = query.all()

        tma_list = []
        tms_list = []
        erros = []

        for chamado in chamados_validos:
            try:
                tempo_p = chamado.restante_p_atendimento.strip()
                sinal_p = -1 if tempo_p.startswith("-") else 1
                partes_p = tempo_p.replace("-", "").split(":")
                h, m, s = (list(map(int, partes_p)) + [0, 0, 0])[:3]
                restante_p = timedelta(hours=h, minutes=m, seconds=s) * sinal_p

                tempo_s = chamado.restante_s_atendimento.strip()
                sinal_s = -1 if tempo_s.startswith("-") else 1
                partes_s = tempo_s.replace("-", "").split(":")
                hs, ms, ss = (list(map(int, partes_s)) + [0, 0, 0])[:3]
                restante_s = timedelta(hours=hs, minutes=ms, seconds=ss) * sinal_s

                if restante_p.total_seconds() < 0 or restante_s.total_seconds() < 0:
                    continue

                tms_individual = restante_s - restante_p
                if tms_individual.total_seconds() < 0 or tms_individual > timedelta(days=30):
                    continue

                tma_list.append(restante_p.total_seconds())
                tms_list.append(tms_individual.total_seconds())

            except Exception as e:
                erros.append({
                    "cod_chamado": chamado.cod_chamado,
                    "restante_p_atendimento": chamado.restante_p_atendimento,
                    "restante_s_atendimento": chamado.restante_s_atendimento,
                    "erro": str(e)
                })
                continue

        if not tma_list or not tms_list:
            return jsonify({
                "status": "success",
                "media_tma": "Sem dados",
                "mediana_tma": "Sem dados",
                "media_tms": "Sem dados",
                "mediana_tms": "Sem dados",
                "chamados_processados": 0,
                "erros_amostragem": erros[:10]
            })

        import numpy as np

        media_tma = np.mean(tma_list) / 60
        mediana_tma = np.median(tma_list) / 60
        media_tms = np.mean(tms_list) / 60
        mediana_tms = np.median(tms_list) / 60

        def formatar_tempo(minutos: float) -> str:
            if minutos < 60:
                return f"{round(minutos)} min"
            elif minutos < 1440:
                return f"{minutos / 60:.1f} h"
            else:
                return f"{minutos / 1440:.2f} dias"

        return jsonify({
            "status": "success",
            "media_tma": formatar_tempo(media_tma),
            "mediana_tma": formatar_tempo(mediana_tma),
            "media_tms": formatar_tempo(media_tms),
            "mediana_tms": formatar_tempo(mediana_tms),
            "chamados_processados": len(tma_list),
            "erros_amostragem": erros[:10]
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@operadores_bp.route('/slaColaboradores', methods=['POST'])
def sla_colaboradores():
    try:
        data = request.get_json()
        dias = int(data.get('dias', 1))
        nome = data.get('nome', '').strip().lower()

        hoje = datetime.now()
        data_inicio = hoje - timedelta(days=dias)

        # Consulta base
        query = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.data_criacao >= datetime.combine(data_inicio.date(), datetime.min.time()),
            Chamado.data_criacao <= datetime.combine(hoje.date(), datetime.max.time())
        )

        # Aplica filtro de nome, se fornecido
        if nome:
            query = query.filter(Chamado.operador.ilike(f"%{nome}%"))  # 👈 filtro aplicado

        chamados = query.all()

        expirados_atendimento = sum(1 for c in chamados if c.sla_atendimento == 'S')
        expirados_resolucao = sum(1 for c in chamados if c.sla_resolucao == 'S')
        chamados_atendimento_prazo = sum(1 for c in chamados if c.sla_atendimento == 'N')
        chamados_finalizado_prazo = sum(1 for c in chamados if c.sla_resolucao == 'N')

        chamados_expirados = [
            c for c in chamados if c.sla_atendimento == 'S' or c.sla_resolucao == 'S'
        ]

        total_chamados = len(chamados)

        percentual_atendimento = round((expirados_atendimento / total_chamados) * 100, 2) if total_chamados else 0
        percentual_resolucao = round((expirados_resolucao / total_chamados) * 100, 2) if total_chamados else 0
        percentual_prazo_atendimento = round((chamados_atendimento_prazo / total_chamados) * 100, 2) if total_chamados else 0
        percentual_prazo_resolucao = round((chamados_finalizado_prazo / total_chamados) * 100, 2) if total_chamados else 0

        return jsonify({
            "status": "success",
            "total_chamados": total_chamados,
            "prazo_atendimento": chamados_atendimento_prazo,
            "percentual_prazo_atendimento": percentual_prazo_atendimento,
            "percentual_prazo_resolucao": percentual_prazo_resolucao,
            "expirados_atendimento": expirados_atendimento,
            "prazos_resolucao": chamados_finalizado_prazo,
            "expirados_resolucao": expirados_resolucao,
            "percentual_atendimento": percentual_atendimento,
            "percentual_resolucao": percentual_resolucao,
            "codigos_atendimento": [c.cod_chamado for c in chamados_expirados if c.sla_atendimento == 'S'],
            "codigos_resolucao": [c.cod_chamado for c in chamados_expirados if c.sla_resolucao == 'S'],
            "codigos_prazo_atendimento": [c.cod_chamado for c in chamados if c.sla_atendimento == 'N'],
            "codigos_prazo_resolucao": [c.cod_chamado for c in chamados if c.sla_resolucao == 'N']
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@operadores_bp.route('/fcrColaboradores', methods=['POST'])
def fcr_colaboradores():
    try:
        data = request.get_json()
        dias = int(data.get('dias'))
        nome = data.get('nome', '').strip().lower()

        hoje = datetime.utcnow().date()
        data_limite = hoje - timedelta(days=dias)

        # Todos os chamados do operador
        total_registros = RelatorioColaboradores.query.filter(
            func.lower(RelatorioColaboradores.operador) == nome,
            RelatorioColaboradores.data_criacao >= data_limite,
            RelatorioColaboradores.nome_status == 'Resolvido',
        ).all()

        data_inicio = hoje - timedelta(days=dias)

        inicio = datetime.combine(data_inicio, datetime.min.time())
        fim = datetime.combine(hoje, datetime.max.time())

        total_chamados = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.nome_status == 'Resolvido',
            Chamado.data_finalizacao != None,
            Chamado.data_finalizacao >= inicio,
            Chamado.data_finalizacao <= fim,
            Chamado.operador == nome
        ).count()

        # Chamados com FCR
        fcr_registros = [r for r in total_registros if r.first_call == 'S']
        codigos_fcr = [r.cod_chamado for r in fcr_registros if r.cod_chamado]

        return jsonify({
            "status": "success",
            "total_fcr": len(codigos_fcr),
            "percentual_fcr": round((len(fcr_registros) / total_chamados) * 100, 2) if total_registros else 0,
            "cod_chamados": codigos_fcr,
            "total_chamados": total_chamados
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@operadores_bp.route('/reabertosColaboradores', methods=['POST'])
def reabertos_colaboradores():
    try:
        data = request.get_json()
        dias = int(data.get('dias'))
        nome = data.get('nome', '').strip().lower()

        hoje = datetime.utcnow()
        data_limite = hoje - timedelta(days=dias)


        # Todos os chamados do operador no período
        total_registros = RelatorioColaboradores.query.filter(
            RelatorioColaboradores.operador.ilike(nome),
            func.date(RelatorioColaboradores.data_criacao) >= data_limite
        ).all()

        data_inicio = hoje - timedelta(days=dias)

        inicio = datetime.combine(data_inicio, datetime.min.time())
        fim = datetime.combine(hoje, datetime.max.time())

        total_chamados = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.nome_status == 'Resolvido',
            Chamado.data_finalizacao != None,
            Chamado.data_finalizacao >= inicio,
            Chamado.data_finalizacao <= fim,
            Chamado.operador == nome
        ).count()

        # Apenas os reabertos
        reabertos = [r for r in total_registros if r.reaberto == 'Reaberto']
        codigos = [r.cod_chamado for r in reabertos if r.cod_chamado]

        return jsonify({
            "status": "success",
            "total_reabertos": len(codigos),
            "cod_chamados": codigos,
            "total_chamados": total_chamados
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@operadores_bp.route('/colaboradores/n2', methods=['GET'])
def render_operadores_n2():
    nome = session.get('nome')

    return render_template('colaboradores_nivel2.html', nome=nome)