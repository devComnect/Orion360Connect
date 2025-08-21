from flask import Blueprint, jsonify, request
from settings import endpoints
import requests, json, os
import calendar
from modules.deskmanager.authenticate.routes import token_desk
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date
from application.models import db, Chamado, PerformanceColaboradores, ChamadasDetalhes, DesempenhoAtendenteVyrtos
from sqlalchemy import extract, func


dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/ChamadosSuporte/fila', methods=['POST'])
def listar_chamados_fila():
    token_response = token_desk()

    payload = {
        "Pesquisa": "",
        "Tatual": "",
        "Ativo": "NaFila",
        "StatusSLA": "S",
        "Colunas": {
            "Chave": "on",
            "CodChamado": "on",
            "NomePrioridade": "on",
            "DataCriacao": "on",
            "HoraCriacao": "on",
            "DataFinalizacao": "on",
            "HoraFinalizacao": "on",
            "DataAlteracao": "on",
            "HoraAlteracao": "on",
            "NomeStatus": "on",
            "Assunto": "on",
            "Descricao": "on",
            "ChaveUsuario": "on",
            "NomeUsuario": "on",
            "SobrenomeUsuario": "on",
            "NomeCompletoSolicitante": "on",
            "SolicitanteEmail": "on",
            "NomeOperador": "on",
            "SobrenomeOperador": "on",
            "TotalAcoes": "on",
            "TotalAnexos": "on",
            "Sla": "on",
            "CodGrupo": "on",
            "NomeGrupo": "on",
            "CodSolicitacao": "off",
            "CodSubCategoria": "off",
            "CodTipoOcorrencia": "off",
            "CodCategoriaTipo": "off",
            "CodPrioridadeAtual": "off",
            "CodStatusAtual": "off"
        },
        "Ordem": [{
            "Coluna": "Chave",
            "Direcao": "true"
        }]
    }

    try:
        response = requests.post(
            'https://api.desk.ms/ChamadosSuporte/lista',
            headers={
                'Authorization': f'{token_response}',
                'Content-Type': 'application/json'
            },
            json=payload
        )
        # Verifica se a requisição foi bem sucedida
        if response.status_code == 200:
            data = response.json()
            
            # Captura apenas o total do retorno
            total_chamados = data.get("total", "0")
            
            return jsonify({
                "status": "success",
                "total_chamados": total_chamados
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Erro na requisição",
                "status_code": response.status_code
            }), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao conectar com o servidor",
            "details": str(e)
        }), 500

def parse_tempo(s):
    try:
        negativo = s.startswith('-')
        h, m, s = map(int, s.replace('-', '').split(':'))
        delta = timedelta(hours=h, minutes=m, seconds=s)
        return -delta if negativo else delta
    except:
        return None

@dashboard_bp.route('/ChamadosSuporte/sla_andamento', methods=['POST'])
def listar_sla_andamento():
    try:
        hoje = datetime.now()

        chamados = Chamado.query.filter(
            Chamado.nome_grupo.ilike('%SUPORTE%'),
            ~Chamado.nome_status.in_(["Resolvido", "Cancelado"])
        ).all()

        sla1_expirado = 0
        sla1_nao_expirado = 0
        sla2_expirado = 0
        sla2_nao_expirado = 0
        sla1_quase_estourando = 0
        sla2_quase_estourando = 0

        codigos_sla1 = []
        codigos_sla2 = []
        codigos_sla1_critico = []
        codigos_sla2_critico = []

        for chamado in chamados:
            sla1 = (chamado.sla_atendimento or "").strip().upper()
            sla2 = (chamado.sla_resolucao or "").strip().upper()
            restante1_raw = (chamado.restante_p_atendimento or "").strip()
            restante2_raw = (chamado.restante_s_atendimento or "").strip()
            restante1 = parse_tempo(restante1_raw)
            restante2 = parse_tempo(restante2_raw)
            cod = chamado.cod_chamado

            # SLA 1 - Atendimento
            if sla1 == "S" or (restante1 is not None and restante1 <= timedelta(minutes=0)):
                sla1_expirado += 1
                codigos_sla1.append(cod)
            elif restante1 is not None and restante1 <= timedelta(minutes=5):
                sla1_quase_estourando += 1
                codigos_sla1_critico.append(cod)
            elif restante1 is not None:
                sla1_nao_expirado += 1

            # SLA 2 - Resolução
            if sla2 == "S" or (restante2 is not None and restante2 <= timedelta(minutes=0)):
                sla2_expirado += 1
                codigos_sla2.append(cod)
            elif restante2 is not None and restante2 <= timedelta(minutes=5):
                sla2_quase_estourando += 1
                codigos_sla2_critico.append(cod)
            elif restante2 is not None:
                sla2_nao_expirado += 1

        return jsonify({
            "status": "success",
            "sla1_expirado": sla1_expirado,
            "sla1_nao_expirado": sla1_nao_expirado,
            "sla1_quase_estourando": sla1_quase_estourando,
            "sla2_expirado": sla2_expirado,
            "sla2_nao_expirado": sla2_nao_expirado,
            "sla2_quase_estourando": sla2_quase_estourando,
            "total": len(chamados),
            "codigos_sla1": codigos_sla1,
            "codigos_sla2": codigos_sla2,
            "codigos_sla1_critico": codigos_sla1_critico,
            "codigos_sla2_critico": codigos_sla2_critico,
            "grupo_filtrado": "SUPORTE",
            "mes_referencia": hoje.strftime("%Y-%m")
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao consultar os dados",
            "details": str(e)
        }), 500

@dashboard_bp.route('/ChamadosSuporte/estatisticas_mensais', methods=['GET'])
def estatisticas_chamados():
    try:
        # Obter todos os chamados abertos (não resolvidos ou cancelados)
        chamados_abertos = db.session.query(
            Chamado.chave, 
            Chamado.nome_status,
            Chamado.nome_grupo
        ).filter(
            Chamado.nome_status.notin_(['cancelado', 'resolvido'])
        ).all()

        # Processar os resultados
        status_counts = {}
        grupos = set()
        
        for chamado in chamados_abertos:
            status = chamado.nome_status
            grupo = chamado.nome_grupo
            grupos.add(grupo)
            
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1

        # Formatar resposta para o gráfico
        labels = list(status_counts.keys())
        dados = list(status_counts.values())
        
        return jsonify({
            "status": "success",
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": dados,
                    "backgroundColor": [
                        '#FF6384', '#36A2EB', '#FFCE56',
                        '#4BC0C0', '#9966FF', '#FF9F40'
                    ]
                }],
                "total": sum(dados),
                "grupos": list(grupos)  # Lista de grupos associados
            },
            "chamados_abertos": [{
                "chave": chamado.chave,  # Retornando chave em vez de id
                "nome_status": chamado.nome_status,
                "nome_grupo": chamado.nome_grupo
            } for chamado in chamados_abertos]
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500
    
@dashboard_bp.route('/ChamadosSuporte/por_grupo_mes_atual', methods=['GET'])
def chamados_por_grupo_mes():

    try:
        hoje = datetime.now()

        # Consulta agrupando por grupo
        resultados = db.session.query(
            Chamado.nome_grupo,
            func.count(Chamado.id).label('total')
        ).filter(
            extract('month', Chamado.data_criacao) == hoje.month,
            extract('year', Chamado.data_criacao) == hoje.year
        ).group_by(
            Chamado.nome_grupo
        ).order_by(
            func.count(Chamado.id).desc()
        ).all()

        labels = [r[0] or "Sem Grupo" for r in resultados]
        dados = [r[1] for r in resultados]

        return jsonify({
            "status": "success",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": "Chamados por Grupo",
                    "data": dados,
                    "backgroundColor": [
                        '#007bff', '#6610f2', '#6f42c1',
                        '#e83e8c', '#fd7e14', '#20c997',
                        '#17a2b8', '#6c757d', '#343a40'
                    ] * len(labels)  # repete as cores se precisar
                }]
            },
            "mes_referencia": f"{hoje.month}/{hoje.year}"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao buscar dados por grupo",
            "details": str(e)
        }), 500
    
@dashboard_bp.route('/ChamadosSuporte/por_tipo_solicitacao_mes_atual', methods=['POST'])
def chamados_por_tipo_solicitacao_hoje():
    try:
        hoje = datetime.now().date()
        inicio_dia = datetime.combine(hoje, datetime.min.time())
        fim_dia = inicio_dia + timedelta(days=1)

        tipos_desejados = ['000003', '000101', '000004', '000060', '000001', '000071']
        mapeamento_tipos = {
            '000101': 'Portal Comnect',
            '000071': 'Interno',
            '000003': 'E-mail',
            '000004': 'Telefone',
            '000001': 'Portal Solicitante',
            '000060': 'WhatsApp'
        }

        # Consulta agrupando por tipo e hora
        resultados = db.session.query(
            Chamado.cod_solicitacao,
            func.extract('hour', Chamado.data_criacao).label('hora'),
            func.count(Chamado.id)
        ).filter(
            Chamado.cod_solicitacao.in_(tipos_desejados),
            Chamado.data_criacao >= inicio_dia,
            Chamado.data_criacao < fim_dia
        ).group_by(
            Chamado.cod_solicitacao,
            'hora'
        ).all()

        # Inicializar estrutura: {tipo: [0, 0, ..., 0] para cada hora}
        dados_por_tipo = {
            cod: [0] * 24 for cod in tipos_desejados
        }

        # Preencher os dados
        for cod_tipo, hora, total in resultados:
            hora = int(hora)
            if cod_tipo in dados_por_tipo and 0 <= hora <= 23:
                dados_por_tipo[cod_tipo][hora] = total

        cores = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']

        # Construir os datasets
        datasets = []
        for i, cod in enumerate(tipos_desejados):
            datasets.append({
                'label': mapeamento_tipos.get(cod, cod),
                'data': dados_por_tipo[cod],
                'backgroundColor': cores[i],
                'borderColor': cores[i],
                'fill': False,
                'tension': 0.3,
                'borderWidth': 2
            })

        return jsonify({
            'status': 'success',
            'data': {
                'labels': [f"{h:02d}h" for h in range(24)],  # Eixo X: horas
                'datasets': datasets
            },
            'data_referencia': hoje.strftime('%d/%m/%Y')
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@dashboard_bp.route('/ChamadosSuporte/abertos_vs_resolvidos', methods=['POST'])
def chamados_abertos_vs_resolvidos():
    try:
        hoje = datetime.now().date()
        inicio_dia = datetime.combine(hoje, datetime.min.time())
        fim_dia = inicio_dia + timedelta(days=1)

        horas_do_dia = list(range(0, 24))
        total_por_hora = {hora: 0 for hora in horas_do_dia}
        resolvidos_por_hora = {hora: 0 for hora in horas_do_dia}

        # Chamados abertos no dia atual (por hora da criação)
        resultados_abertos = db.session.query(
            func.extract('hour', Chamado.data_criacao).label('hora'),
            func.count(Chamado.id)
        ).filter(
            Chamado.data_criacao >= inicio_dia,
            Chamado.data_criacao < fim_dia
        ).group_by('hora').all()

        for hora, total in resultados_abertos:
            total_por_hora[int(hora)] = total

        # Chamados resolvidos no dia atual (por hora da finalização)
        resultados_resolvidos = db.session.query(
            func.extract('hour', Chamado.data_finalizacao).label('hora'),
            func.count(Chamado.id)
        ).filter(
            Chamado.data_finalizacao >= inicio_dia,
            Chamado.data_finalizacao < fim_dia,
            Chamado.nome_status == 'Resolvido'
        ).group_by('hora').all()

        for hora, total in resultados_resolvidos:
            resolvidos_por_hora[int(hora)] = total

        return jsonify({
            'status': 'success',
            'labels': [f'{h:02d}:00' for h in horas_do_dia],
            'datasets': [
                {
                    'label': 'Chamados Abertos',
                    'data': [total_por_hora[h] for h in horas_do_dia],
                    'backgroundColor': 'rgba(255, 99, 132, 0.7)',
                    'borderColor': 'rgba(255, 99, 132, 1)',
                    'borderWidth': 2
                },
                {
                    'label': 'Chamados Resolvidos',
                    'data': [resolvidos_por_hora[h] for h in horas_do_dia],
                    'backgroundColor': 'rgba(75, 192, 75, 0.7)',
                    'borderColor': 'rgba(75, 192, 192, 1)',
                    'borderWidth': 2
                }
            ],
            'resumo': {
                'total_abertos': sum(total_por_hora.values()),
                'total_resolvidos': sum(resolvidos_por_hora.values()),
                'diferenca': sum(total_por_hora.values()) - sum(resolvidos_por_hora.values())
            },
            'data_referencia': hoje.strftime('%d/%m/%Y')
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@dashboard_bp.route('/ChamadosSuporte/sla_andamento_grupos', methods=['POST'])
def listar_sla_andamento_grupos():
    grupos_desejados = ['INFOSEC', 'DEV', 'NOC', 'CSM']
    mes_referencia_atual = datetime.now().strftime('%Y-%m')

    chamados = Chamado.query.filter(
        Chamado.nome_status.notin_(['Resolvido', 'Cancelado']),
        Chamado.nome_prioridade.notin_(['5 - Planejada', '4 - Baixa']),
        db.or_(
            Chamado.nome_grupo.ilike('%DEV%'),
            Chamado.nome_grupo.ilike('%INFOSEC%'),
            Chamado.nome_grupo.ilike('%CSM%'),
            Chamado.nome_grupo.ilike('%NOC%')
        ),
        Chamado.sla_atendimento.in_(['S', 'N']),
        Chamado.sla_resolucao.in_(['S', 'N']),
    ).all()

    # Contadores
    sla1_expirado = sla1_nao_expirado = sla1_quase_estourando = 0
    sla2_expirado = sla2_nao_expirado = sla2_quase_estourando = 0

    # Listas de códigos
    codigos_sla1 = []
    codigos_sla2 = []
    codigos_sla1_critico = []
    codigos_sla2_critico = []

    for chamado in chamados:
        restante1_raw = (chamado.restante_p_atendimento or "").strip()
        restante2_raw = (chamado.restante_s_atendimento or "").strip()
        restante1 = parse_tempo(restante1_raw)
        restante2 = parse_tempo(restante2_raw)
        cod = chamado.cod_chamado

        # SLA Atendimento
        if chamado.sla_atendimento == "S":
            sla1_expirado += 1
            codigos_sla1.append(cod)
        elif chamado.sla_atendimento == "N" and restante1 is not None:
            if timedelta(minutes=0) < restante1 <= timedelta(minutes=5):
                sla1_quase_estourando += 1
                codigos_sla1_critico.append(cod)
            elif restante1 > timedelta(minutes=10):
                sla1_nao_expirado += 1
            else:
                sla1_expirado += 1
                codigos_sla1.append(cod)

        # SLA Resolução
        if chamado.sla_resolucao == "S":
            sla2_expirado += 1
            codigos_sla2.append(cod)
        elif chamado.sla_resolucao == "N" and restante2 is not None:
            if timedelta(minutes=0) < restante2 <= timedelta(minutes=5):
                sla2_quase_estourando += 1
                codigos_sla2_critico.append(cod)
            elif restante2 > timedelta(minutes=10):
                sla2_nao_expirado += 1
            else:
                sla2_expirado += 1
                codigos_sla2.append(cod)

    return jsonify({
        "status": "success",
        "sla1_expirado": sla1_expirado,
        "sla1_nao_expirado": sla1_nao_expirado,
        "sla1_quase_estourando": sla1_quase_estourando,
        "sla2_expirado": sla2_expirado,
        "sla2_nao_expirado": sla2_nao_expirado,
        "sla2_quase_estourando": sla2_quase_estourando,
        "codigos_sla1": codigos_sla1,
        "codigos_sla2": codigos_sla2,
        "codigos_sla1_critico": codigos_sla1_critico,
        "codigos_sla2_critico": codigos_sla2_critico,
        "total": len(chamados),
        "grupos": grupos_desejados,
        "mes_referencia": mes_referencia_atual
    })

@dashboard_bp.route('/v2/report/attendants_performance', methods=['POST'])
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


@dashboard_bp.route('/v2/report/attendants_performance_vyrtos', methods=['POST'])
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