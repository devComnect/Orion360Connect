from flask import Blueprint, jsonify, request
from settings import endpoints 
import requests, json, os
import calendar
from modules.dashboard.extensions import payload, tipos_desejados, mapeamento_tipos, cores, grupos_desejados
from modules.dashboard.utils import parse_tempo
from modules.deskmanager.authenticate.routes import token_desk
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date
from application.models import db, Chamado, PerformanceColaboradores, ChamadasDetalhes, DesempenhoAtendenteVyrtos
from sqlalchemy import extract, func

dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/ChamadosSuporte/fila', methods=['POST'])
def listar_chamados_fila():
    token_response = token_desk()
    try:
        response = requests.post(
            endpoints.LISTA_CHAMADOS_SUPORTE,
            headers={
                'Authorization': f'{token_response}',
                'Content-Type': 'application/json'
            },
            json=payload
        )
        if response.status_code == 200:
            data = response.json()
            
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

@dashboard_bp.route('/ChamadosSuporte/sla_andamento', methods=['POST'])
def listar_sla_andamento():
    try:
        hoje = datetime.now()
        chamados = (
            Chamado.query.filter(
                Chamado.nome_grupo.ilike('%SUPORTE%'),
                ~Chamado.nome_status.in_(["Resolvido", "Cancelado"])
            ).all()
        )

        sla1_expirado = sla1_urgente = sla1_quase_estourando = sla1_normal = 0
        sla2_expirado = sla2_urgente = sla2_quase_estourando = sla2_normal = 0

        codigos_sla1_expirado = []
        codigos_sla1_urgente = []
        codigos_sla1_critico = []
        codigos_sla1_normal = []

        codigos_sla2_expirado = []
        codigos_sla2_urgente = []
        codigos_sla2_critico = []
        codigos_sla2_normal = []

        for chamado in chamados:
            cod = chamado.cod_chamado
            s1 = (chamado.status_sla_atendimento or "").strip()
            s2 = (chamado.status_sla_resolucao or "").strip()

            if s1.startswith("Expirado"):
                sla1_expirado += 1
                codigos_sla1_expirado.append(cod)

            elif s1 == "Urgente":
                sla1_urgente += 1
                codigos_sla1_urgente.append(cod)

            elif s1 == "Atenção":
                sla1_quase_estourando += 1
                codigos_sla1_critico.append(cod)

            elif s1 == "Normal":
                sla1_normal += 1
                codigos_sla1_normal.append(cod)

            if s2.startswith("Expirado"):
                sla2_expirado += 1
                codigos_sla2_expirado.append(cod)

            elif s2 == "Urgente":
                sla2_urgente += 1
                codigos_sla2_urgente.append(cod)

            elif s2 == "Atenção":
                sla2_quase_estourando += 1
                codigos_sla2_critico.append(cod)

            elif s2 == "Normal":
                sla2_normal += 1
                codigos_sla2_normal.append(cod)

        return jsonify({
            "status": "success",

            "sla1_expirado": sla1_expirado,
            "sla1_urgente": sla1_urgente,
            "sla1_quase_estourando": sla1_quase_estourando,
            "sla1_nao_expirado": sla1_normal,

            "sla2_expirado": sla2_expirado,
            "sla2_urgente": sla2_urgente,
            "sla2_quase_estourando": sla2_quase_estourando,
            "sla2_nao_expirado": sla2_normal,

            "total": len(chamados),

            "codigos_sla1_expirado": codigos_sla1_expirado,
            "codigos_sla1_urgente": codigos_sla1_urgente,
            "codigos_sla1_critico": codigos_sla1_critico,
            "codigos_sla1_normal": codigos_sla1_normal,

            "codigos_sla2_expirado": codigos_sla2_expirado,
            "codigos_sla2_urgente": codigos_sla2_urgente,
            "codigos_sla2_critico": codigos_sla2_critico,
            "codigos_sla2_normal": codigos_sla2_normal,

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
        chamados_abertos = db.session.query(
            Chamado.chave, 
            Chamado.nome_status,
            Chamado.nome_grupo
        ).filter(
            Chamado.nome_status.notin_(['cancelado', 'resolvido']),
            Chamado.nome_grupo != 'SUPORTE TI'
        ).all()

        status_counts = {}
        grupos = set()
        
        for chamado in chamados_abertos:
            status = chamado.nome_status
            grupo = chamado.nome_grupo
            grupos.add(grupo)
            
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1

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
                "grupos": list(grupos) 
            },
            "chamados_abertos": [{
                "chave": chamado.chave,  
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
                    ] * len(labels)  
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

        dados_por_tipo = {
            cod: [0] * 24 for cod in tipos_desejados
        }

        for cod_tipo, hora, total in resultados:
            hora = int(hora)
            if cod_tipo in dados_por_tipo and 0 <= hora <= 23:
                dados_por_tipo[cod_tipo][hora] = total


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
                'labels': [f"{h:02d}h" for h in range(24)], 
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

        resultados_abertos = db.session.query(
            func.extract('hour', Chamado.data_criacao).label('hora'),
            func.count(Chamado.id)
        ).filter(
            Chamado.data_criacao >= inicio_dia,
            Chamado.data_criacao < fim_dia
        ).group_by('hora').all()

        for hora, total in resultados_abertos:
            total_por_hora[int(hora)] = total

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
    try:
        mes_referencia_atual = datetime.now().strftime('%Y-%m')
        chamados = Chamado.query.filter(
            Chamado.nome_status.notin_(['Resolvido', 'Cancelado']),
            Chamado.nome_prioridade.notin_(['5 - Planejada', '4 - Baixa']),
            db.or_(
                Chamado.nome_grupo.ilike('%DEV%'),
                Chamado.nome_grupo.ilike('%INFOSEC%'),
                Chamado.nome_grupo.ilike('%CSM%'),
                Chamado.nome_grupo.ilike('%NOC%')
            )
        ).all()

        sla1_expirado = sla1_urgente = sla1_quase_estourando = sla1_normal = 0
        sla2_expirado = sla2_urgente = sla2_quase_estourando = sla2_normal = 0

        codigos_sla1_expirado = []
        codigos_sla1_urgente = []
        codigos_sla1_critico = []
        codigos_sla1_normal = []

        codigos_sla2_expirado = []
        codigos_sla2_urgente = []
        codigos_sla2_critico = []
        codigos_sla2_normal = []

        for chamado in chamados:
            cod = chamado.cod_chamado
            s1 = (chamado.status_sla_atendimento or "").strip()
            s2 = (chamado.status_sla_resolucao or "").strip()

            if s1.startswith("Expirado"):
                sla1_expirado += 1
                codigos_sla1_expirado.append(cod)

            elif s1 == "Urgente":
                sla1_urgente += 1
                codigos_sla1_urgente.append(cod)

            elif s1 == "Atenção":
                sla1_quase_estourando += 1
                codigos_sla1_critico.append(cod)

            elif s1 == "Normal":
                sla1_normal += 1
                codigos_sla1_normal.append(cod)

            if s2.startswith("Expirado"):
                sla2_expirado += 1
                codigos_sla2_expirado.append(cod)

            elif s2 == "Urgente":
                sla2_urgente += 1
                codigos_sla2_urgente.append(cod)

            elif s2 == "Atenção":
                sla2_quase_estourando += 1
                codigos_sla2_critico.append(cod)

            elif s2 == "Normal":
                sla2_normal += 1
                codigos_sla2_normal.append(cod)

        return jsonify({
            "status": "success",

            "sla1_expirado": sla1_expirado,
            "sla1_urgente": sla1_urgente,
            "sla1_quase_estourando": sla1_quase_estourando,
            "sla1_nao_expirado": sla1_normal,

            "sla2_expirado": sla2_expirado,
            "sla2_urgente": sla2_urgente,
            "sla2_quase_estourando": sla2_quase_estourando,
            "sla2_nao_expirado": sla2_normal,

            "codigos_sla1_expirado": codigos_sla1_expirado,
            "codigos_sla1_urgente": codigos_sla1_urgente,
            "codigos_sla1_critico": codigos_sla1_critico,
            "codigos_sla1_normal": codigos_sla1_normal,

            "codigos_sla2_expirado": codigos_sla2_expirado,
            "codigos_sla2_urgente": codigos_sla2_urgente,
            "codigos_sla2_critico": codigos_sla2_critico,
            "codigos_sla2_normal": codigos_sla2_normal,

            "total": len(chamados),
            "grupos": grupos_desejados,
            "mes_referencia": mes_referencia_atual
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao consultar",
            "details": str(e)
        }), 500

@dashboard_bp.route('/v2/report/attendants_performance', methods=['POST'])
def buscar_desempenho_atendentes():
    try:
        hoje = datetime.now().date()  
        ontem = hoje - timedelta(days=1)

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