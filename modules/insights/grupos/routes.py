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

@grupos_bp.route('/ticketsOperador', methods=['POST'])
def get_tickets_grupo_operador():
    try:
        dias = int(request.json.get("dias"))  
        grupo = request.json.get("grupo", "").strip()
        data_limite = datetime.now() - timedelta(days=dias)

        # Consulta todos os chamados criados no período, finalizados ou não
        resultados = db.session.query(
            Chamado.operador,
            func.count(Chamado.id).label('total')
        ).filter(
            Chamado.data_criacao >= data_limite,
            Chamado.nome_grupo == grupo,
        ).group_by(
            Chamado.operador
        ).order_by(
            func.count(Chamado.id).desc()
        ).all()

        # Organiza os dados para o gráfico
        labels = [r[0] if r[0] else 'Sem operador' for r in resultados]
        dados = [r[1] for r in resultados]

        # Gera cores aleatórias distintas
        def gerar_cores_hex(n):
            import random
            random.seed(42)
            return [f'#{random.randint(0, 0xFFFFFF):06x}' for _ in range(n)]

        backgroundColor = gerar_cores_hex(len(labels))

        return jsonify({
            'status': 'success',
            'data': {
                'labels': labels,
                'datasets': [{
                    'data': dados,
                    'backgroundColor': backgroundColor
                }]
            },
            'data_referencia': f'Últimos {dias} dias'
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@grupos_bp.route('/tickets_grupos_canal', methods=['POST'])
def get_tickets_grupos_canal():
    try:
        dias = int(request.json.get("dias"))
        grupo = request.json.get("grupo", "").strip()
        data_limite = datetime.now() - timedelta(days=dias)

        tipos_desejados = ['000003', '000101', '000004', '000060', '000001', '000071']
        mapeamento_tipos = {
            '000101': 'Portal Comnect',
            '000071': 'Interno',
            '000003': 'E-mail',
            '000004': 'Telefone',
            '000001': 'Portal Solicitante',
            '000060': 'WhatsApp'
        }

        # Consulta agrupando por tipo e dia
        resultados = db.session.query(
            Chamado.cod_solicitacao,
            func.date(Chamado.data_criacao).label('dia'),
            func.count(Chamado.id)
        ).filter(
            Chamado.cod_solicitacao.in_(tipos_desejados),
            Chamado.data_criacao >= data_limite,
            Chamado.nome_grupo == grupo,
            #Chamado.data_finalizacao.is_(None),
            Chamado.nome_status.notin_(['Cancelado'])  # caso queira filtrar
        ).group_by(
            Chamado.cod_solicitacao,
            func.date(Chamado.data_criacao)
        ).order_by(func.date(Chamado.data_criacao)).all()

        # Gerar lista contínua de dias
        hoje = datetime.now().date()
        lista_dias = [data_limite.date() + timedelta(days=i) for i in range((hoje - data_limite.date()).days + 1)]
        labels = [dia.strftime('%d/%m') for dia in lista_dias]

        # Organizar dados por tipo
        dados_agrupados = {cod: {} for cod in tipos_desejados}
        for cod, dia, total in resultados:
            dados_agrupados[cod][dia] = total

        cores = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']

        datasets = []
        for i, cod in enumerate(tipos_desejados):
            dados = [dados_agrupados[cod].get(d, 0) for d in lista_dias]
            datasets.append({
                'label': mapeamento_tipos.get(cod, cod),
                'data': dados,
                'backgroundColor': cores[i],
                'borderColor': cores[i],
                'fill': False,
                'tension': 0.3,
                'borderWidth': 2
            })

        return jsonify({
            'status': 'success',
            'data': {
                'labels': labels,
                'datasets': datasets
            },
            'data_referencia': f"Últimos {dias} dias"
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
# Rota que traz os top 5 tipos com mais chamados 
@grupos_bp.route('/topTipoChamadosGrupos', methods=['POST'])
def top_tipo_chamados():
    tipo_ocorrencia = {
        "000150": "GMUD",
        "000010": "Incidente",
        "000004": "Problema",
        "000002": "Dúvida",
        "000008": "Evento",
        "000009": "Requisição",
    }

    data = request.get_json()
    dias = int(data.get('dias', 1))
    grupo = request.json.get("grupo", "").strip()
    data_limite = datetime.now() - timedelta(days=dias)

    # Consulta agrupada por tipo de ocorrência
    resultados = (
        db.session.query(
            Chamado.cod_tipo_ocorrencia,
            db.func.count().label('quantidade')
        )
        .filter(Chamado.data_criacao >= data_limite,
                Chamado.nome_grupo == grupo,
                )
        .group_by(Chamado.cod_tipo_ocorrencia)
        .order_by(db.desc('quantidade'))
        .all()
    )

    top_resultado = []
    for row in resultados:
        nome_tipo = tipo_ocorrencia.get(row.cod_tipo_ocorrencia)
        if nome_tipo:  # Só inclui se estiver mapeado
            top_resultado.append({
                "tipo": nome_tipo,
                "codigo": row.cod_tipo_ocorrencia,
                "quantidade": row.quantidade
            })

    # Pega só os 5 mais frequentes
    top_resultado = top_resultado[:5]

    return jsonify({
        "status": "success",
        "dados": top_resultado
    })

@grupos_bp.route('/topCategoriaGrupos', methods=['POST'])
def top_categoria():
    data = request.get_json()
    dias = int(data.get('dias', 1))
    grupo = request.json.get("grupo", "").strip()
    data_limite = datetime.now() - timedelta(days=dias)

    # Join entre Chamado e Categoria pela subcategoria
    resultados = db.session.query(
        Chamado.cod_sub_categoria.label('codigo'),
        Categoria.categoria.label('nome'),
        func.count(Chamado.id).label('quantidade')
    ).join(
        Categoria, Chamado.cod_sub_categoria == Categoria.sequencia
    ).filter(
        Chamado.data_criacao >= data_limite,
        Chamado.nome_grupo == grupo,
    ).group_by(
        Chamado.cod_sub_categoria,
        Categoria.categoria
    ).order_by(
        func.count(Chamado.id).desc()
    ).limit(5).all()

    # Montar a resposta
    dados = [
        {
            "codigo": r.codigo,
            "nome": r.nome,
            "quantidade": r.quantidade
        }
        for r in resultados
    ]

    return jsonify({"status": "success", "dados": dados})

def parse_tempo(s):
    try:
        negativo = s.startswith('-')
        h, m, s = map(int, s.replace('-', '').split(':'))
        delta = timedelta(hours=h, minutes=m, seconds=s)
        return -delta if negativo else delta
    except:
        return None

@grupos_bp.route('/slaAndamentoGrupos', methods=['POST'])
def listar_sla_andamento_grupos():
    grupo = request.json.get("grupo", "").strip()
    mes_referencia_atual = datetime.now().strftime('%Y-%m')

    chamados = Chamado.query.filter(
    Chamado.nome_status.notin_(['Resolvido', 'Cancelado']),
    Chamado.nome_prioridade.notin_(['5 - Planejada', '4 - Baixa']),
    Chamado.nome_grupo.ilike(f"%{grupo}%"),
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
            if timedelta(minutes=0) < restante1 <= timedelta(minutes=10):
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
            if timedelta(minutes=0) < restante2 <= timedelta(minutes=10):
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
        "grupos": grupo,
        "mes_referencia": mes_referencia_atual
    })

@grupos_bp.route('/topSubCategoriaGrupos', methods=['POST'])
def top_sub_categoria():
    data = request.get_json()
    dias = int(data.get('dias', 1))
    grupo = request.json.get("grupo", "").strip()
    data_limite = datetime.now() - timedelta(days=dias)

    # Join entre Chamado e Categoria pela subcategoria
    resultados = db.session.query(
        Chamado.cod_sub_categoria.label('codigo'),
        Categoria.sub_categoria.label('nome'),
        func.count(Chamado.id).label('quantidade')
    ).join(
        Categoria, Chamado.cod_sub_categoria == Categoria.sequencia
    ).filter(
        Chamado.data_criacao >= data_limite,
        Chamado.nome_grupo == grupo,
    ).group_by(
        Chamado.cod_sub_categoria,
        Categoria.sub_categoria
    ).order_by(
        func.count(Chamado.id).desc()
    ).limit(5).all()

    # Montar a resposta
    dados = [
        {
            "codigo": r.codigo,
            "nome": r.nome,
            "quantidade": r.quantidade
        }
        for r in resultados
    ]

    return jsonify({"status": "success", "dados": dados})