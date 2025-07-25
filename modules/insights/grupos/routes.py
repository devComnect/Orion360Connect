from flask import Blueprint, jsonify, render_template, request, url_for
import requests
from modules.deskmanager.authenticate.routes import token_desk
from datetime import datetime, timedelta
from application.models import Chamado, db, Categoria, PesquisaSatisfacao
from collections import Counter
from sqlalchemy import func, and_, or_
import re


grupos_bp = Blueprint('grupos_bp', __name__, url_prefix='/grupos')

@grupos_bp.route('/render/grupos', methods=['POST'])
def render_grupos():
    try:
        data = request.get_json()
        grupo = data.get('grupo', '').strip()

        if not grupo:
            return jsonify({"status": "error", "message": "Grupo não especificado."}), 400

        # Redireciona com query param ou com sessão, se preferir
        redirect_url = url_for('grupos_bp.render_pagina_grupo', grupo=grupo)

        return jsonify({
            "status": "success",
            "redirect_url": redirect_url
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@grupos_bp.route('/grupos/insights')
def render_pagina_grupo():
    grupo = request.args.get('grupo', '')

    if not grupo:
        return "Grupo não informado", 400

    return render_template('insights_grupos.html', grupo=grupo)

@grupos_bp.route('/chamados/grupos', methods=['POST'])
def get_chamados_grupos():
    try:
        dias = int(request.json.get("dias", 1))  # padrão: 1 dia
        grupo = request.json.get("grupo", "").strip()  # novo campo enviado pelo JS

        hoje = datetime.now().date()
        data_inicio = hoje - timedelta(days=dias)

        # Combina datas com hora mínima e máxima do dia
        inicio = datetime.combine(data_inicio, datetime.min.time())
        fim = datetime.combine(hoje, datetime.max.time())

        # Filtro base
        query = Chamado.query.filter(
            Chamado.nome_grupo == grupo,
            Chamado.nome_status != 'Cancelado',
            Chamado.data_criacao >= inicio,
            Chamado.data_criacao <= fim
        )

        total_chamados = query.count()

        return jsonify({
            "status": "success",
            "total_chamados": total_chamados
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@grupos_bp.route('/chamados/grupos/finalizados', methods=['POST'])
def get_chamados_grupos_finalizados():
    try:
        dias = int(request.json.get("dias", 1))  # padrão: 1 dia
        grupo = request.json.get("grupo", "").strip()  # novo campo enviado pelo JS

        hoje = datetime.now().date()
        data_inicio = hoje - timedelta(days=dias)

        # Combina datas com hora mínima e máxima do dia
        inicio = datetime.combine(data_inicio, datetime.min.time())
        fim = datetime.combine(hoje, datetime.max.time())

        # Filtro base
        query = Chamado.query.filter(
            Chamado.nome_grupo == grupo,
            Chamado.nome_status != 'Cancelado',
            Chamado.nome_status == 'Resolvido',
            Chamado.data_criacao >= inicio,
            Chamado.data_criacao <= fim
        )

        total_chamados = query.count()

        return jsonify({
            "status": "success",
            "total_chamados": total_chamados
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
@grupos_bp.route('/chamados/grupos/abertos', methods=['POST'])
def get_chamados_grupos_abertos():
    try:
        dias = int(request.json.get("dias", 1))  # padrão: 1 dia
        grupo = request.json.get("grupo", "").strip()  # novo campo enviado pelo JS

        hoje = datetime.now().date()
        data_inicio = hoje - timedelta(days=dias)

        # Combina datas com hora mínima e máxima do dia
        inicio = datetime.combine(data_inicio, datetime.min.time())
        fim = datetime.combine(hoje, datetime.max.time())

        # Filtro base
        query = Chamado.query.filter(
                Chamado.nome_grupo == grupo,
                Chamado.nome_status != 'Cancelado',
                Chamado.nome_status != 'Resolvido',
                Chamado.data_criacao >= inicio,
                Chamado.data_criacao <= fim
            )

        total_chamados = query.count()
        codigos = [c.cod_chamado for c in query]

        return jsonify({
                "status": "success",
                "total_chamados": total_chamados
            })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
@grupos_bp.route('/sla/grupos', methods=['POST'])
def get_sla_grupos():
    try:
        dias = int(request.json.get("dias", 1))  # padrão: 1 dia
        grupo = request.json.get("grupo", "").strip()  # novo campo enviado pelo JS

        hoje = datetime.now().date()
        data_inicio = hoje - timedelta(days=dias)

        # Combina datas com hora mínima e máxima do dia
        inicio = datetime.combine(data_inicio, datetime.min.time())
        fim = datetime.combine(hoje, datetime.max.time())

        # Filtro: status diferente de cancelado e dentro do período
        chamados = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.nome_grupo == grupo,
            Chamado.data_criacao >= datetime.combine(data_inicio, datetime.min.time()),
            Chamado.data_criacao <= datetime.combine(hoje, datetime.max.time())
        ).all()

        # Filtra os com SLA expirado
        expirados_atendimento = sum(1 for c in chamados if c.sla_atendimento == 'S')
        expirados_resolucao = sum(1 for c in chamados if c.sla_resolucao == 'S')
        chamados_atendimento_prazo = sum(1 for c in chamados if c.sla_atendimento == 'N')
        chamados_finalizado_prazo = sum(1 for c in chamados if c.sla_resolucao == 'N')

        chamados_prazo = [
            c for c in chamados if c.sla_atendimento == 'N' or c.sla_resolucao == 'N'
        ]

        # Lista completa de expirados para retornar os códigos
        chamados_expirados = [
            c for c in chamados if c.sla_atendimento == 'S' or c.sla_resolucao == 'S'
        ]

        total_chamados = len(chamados)

        percentual_atendimento = round((expirados_atendimento / total_chamados) * 100, 2) if total_chamados else 0
        percentual_resolucao = round((expirados_resolucao / total_chamados) * 100, 2) if total_chamados else 0

        percentual_prazo_atendimento = round((chamados_atendimento_prazo/total_chamados) * 100, 2) if total_chamados else 0
        percentual_prazo_resolucao = round((chamados_finalizado_prazo/total_chamados) * 100, 2) if total_chamados else 0

        return jsonify({
            "status": "success",
            "total_chamados": total_chamados,
            "prazo_atendimento": chamados_atendimento_prazo,
            "percentual_prazo_atendimento" : percentual_prazo_atendimento,
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

@grupos_bp.route('/pSatisfacao/grupos', methods=['POST'])
def get_psatisfacao_grupos():
    try:
        dias = int(request.json.get("dias", 1))
        grupo = request.json.get("grupo", "").strip()
        data_limite = (datetime.now() - timedelta(days=dias)).date()

        filtro = [
            PesquisaSatisfacao.data_resposta >= data_limite,
            PesquisaSatisfacao.grupo.like(f"{grupo}%")
        ]

        total_pesquisas = db.session.query(func.count()).filter(*filtro).scalar()

        respondidas = db.session.query(func.count()).filter(
            *filtro,
            or_(
                and_(
                    PesquisaSatisfacao.alternativa.isnot(None),
                    func.length(PesquisaSatisfacao.alternativa) > 0
                ),
                and_(
                    PesquisaSatisfacao.resposta_dissertativa.isnot(None),
                    func.length(PesquisaSatisfacao.resposta_dissertativa) > 0
                )
            )
        ).scalar()

        nao_respondidas = total_pesquisas - respondidas

        percentual_respondidas = round((respondidas / total_pesquisas) * 100, 2) if total_pesquisas else 0
        percentual_nao_respondidas = round(100 - percentual_respondidas, 2) if total_pesquisas else 0

        return jsonify({
            "status": "success",
            "grupo": grupo,
            "total": total_pesquisas,
            "respondidas": respondidas,
            "nao_respondidas": nao_respondidas,
            "percentual_respondidas": percentual_respondidas,
            "percentual_nao_respondidas": percentual_nao_respondidas
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@grupos_bp.route('/abertos_grupos_resolvido', methods=['POST'])
def get_abertos_resolvidos():
    try:
        dias = int(request.json.get("dias", 1))
        grupo = request.json.get("grupo", "").strip()
        data_limite = datetime.now() - timedelta(days=dias)

        total_por_dia = {}
        resolvidos_por_dia = {}

        # Abertos filtrados por grupo e data
        resultados_abertos = db.session.query(
            func.date(Chamado.data_criacao).label('dia'),
            func.count(Chamado.id)
        ).filter(
            Chamado.data_criacao >= data_limite,
            Chamado.nome_grupo.like(f"{grupo}%")  # <- se tiver sufixos como -N1, -N2
        ).group_by('dia').all()

        for dia, total in resultados_abertos:
            total_por_dia[dia] = total

        # Resolvidos filtrados por grupo também
        resultados_resolvidos = db.session.query(
            func.date(Chamado.data_criacao).label('dia'),
            func.count(Chamado.id)
        ).filter(
            Chamado.data_criacao >= data_limite,
            Chamado.nome_status == 'Resolvido',
            Chamado.nome_grupo.like(f"{grupo}%")  # <- mesmo filtro
        ).group_by('dia').all()

        for dia, total in resultados_resolvidos:
            resolvidos_por_dia[dia] = total

        # Dias combinados
        todos_os_dias = sorted(set(total_por_dia.keys()).union(resolvidos_por_dia.keys()))

        # Totais
        total_abertos = sum(total_por_dia.values())
        total_resolvidos = sum(resolvidos_por_dia.values())
        diferenca = total_abertos - total_resolvidos

        return jsonify({
            'status': 'success',
            'labels': [dia.strftime('%d/%m') for dia in todos_os_dias],
            'datasets': [
                {
                    'label': 'Total de Chamados Abertos',
                    'data': [total_por_dia.get(dia, 0) for dia in todos_os_dias],
                    'borderColor': 'rgba(255, 99, 132, 0.7)',
                    'fill': False
                },
                {
                    'label': 'Chamados Resolvidos',
                    'data': [resolvidos_por_dia.get(dia, 0) for dia in todos_os_dias],
                    'borderColor': 'rgba(75, 192, 75, 0.7)',
                    'fill': False
                }
            ],
            'resumo': {
                'abertos': total_abertos,
                'resolvidos': total_resolvidos,
                'diferenca': diferenca
            }
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500