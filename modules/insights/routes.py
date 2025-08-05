from flask import Blueprint, jsonify, render_template, request, url_for
import requests
from modules.deskmanager.authenticate.routes import token_desk
from modules.insights.utils import formatar_tempo
from datetime import datetime, timedelta
from application.models import Chamado, db, Categoria, PesquisaSatisfacao, RelatorioColaboradores
from collections import Counter
from sqlalchemy import func, and_, or_
import numpy as np
import re


insights_bp = Blueprint('insights_bp', __name__, url_prefix='/insights')

# Rota que traz os chamados criados no grupo do Suporte  
@insights_bp.route('/ChamadosSuporte', methods=['POST'])
def listar_chamados_criados():
    try:
        dias = int(request.json.get("dias", 1))  # padrão: 1 dia
        hoje = datetime.now().date()
        data_inicio = hoje - timedelta(days=dias)

        # Combina datas com hora mínima e máxima do dia
        inicio = datetime.combine(data_inicio, datetime.min.time())
        fim = datetime.combine(hoje, datetime.max.time())

        total_chamados = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.data_criacao >= inicio,
            Chamado.data_criacao <= fim
        ).count()

        return jsonify({
            "status": "success",
            "total_chamados": total_chamados
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Rota que traz os chamados finalizados no grupo do Suporte
@insights_bp.route('/ChamadosSuporte/finalizado', methods=['POST'])
def listar_chamados_finalizado():
    try:
        dias = int(request.json.get("dias", 1))  # padrão: 1 dia
        hoje = datetime.now().date()
        data_inicio = hoje - timedelta(days=dias)

        inicio = datetime.combine(data_inicio, datetime.min.time())
        fim = datetime.combine(hoje, datetime.max.time())

        total_chamados = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.nome_status == 'Resolvido',
            Chamado.data_finalizacao != None,
            Chamado.data_finalizacao >= inicio,
            Chamado.data_finalizacao <= fim
        ).count()

        return jsonify({
            "status": "success",
            "total_chamados": total_chamados
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Rota que traz os SLAs globais
@insights_bp.route('/sla', methods=['POST'])
def sla_insights():
    try:
        data = request.get_json()
        dias = int(data.get('dias', 1)) 
        hoje = datetime.now()
        data_inicio = hoje - timedelta(days=dias)

        # Filtro: status diferente de cancelado e dentro do período
        chamados = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.data_criacao >= datetime.combine(data_inicio.date(), datetime.min.time()),
            Chamado.data_criacao <= datetime.combine(hoje.date(), datetime.max.time())
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

# Rota que traz os top 5 grupos com mais chamados
@insights_bp.route('/topGruposChamados', methods=['POST'])
def top_grupos_chamados():
    dias = request.json.get('dias', 1)
    data_inicio = datetime.now() - timedelta(days=int(dias))
    data_fim = datetime.now()

    resultados = db.session.query(
        Chamado.nome_grupo,
        db.func.count(Chamado.id).label('total')
    ).filter(
        Chamado.data_criacao >= data_inicio,
        Chamado.data_criacao <= data_fim,
        Chamado.nome_status != 'Cancelado',
    ).group_by(Chamado.nome_grupo).order_by(db.desc('total')).limit(5).all()

    dados = [{"grupo": grupo or "Não informado", "total": total} for grupo, total in resultados]
    return jsonify(dados)

# Rota que traz os top 5 clientes com mais chamados
@insights_bp.route('/topClientesChamados', methods=['POST'])
def top_clientes_chamados():
    data = request.get_json()
    dias = int(data.get('dias', 1))

    data_limite = datetime.now() - timedelta(days=dias)

    # Domínios comuns a serem ignorados
    dominios_ignorados = {
        "gmail", "outlook", "hotmail", "yahoo", "icloud", "bol", "uol", "live", "aol", "msn", "foradeescopo", "foradoescopo"
    }

    # Consulta os chamados no período
    chamados = Chamado.query.with_entities(Chamado.solicitante_email)\
        .filter(Chamado.data_criacao >= data_limite)\
        .all()

    # Extrai domínios dos e-mails
    dominios = []
    for c in chamados:
        email = c[0]
        if email and "@" in email:
            dominio = re.sub(r"^.*@", "", email).split('.')[0].lower()  # pega só o nome principal
            if dominio not in dominios_ignorados:
                dominios.append(dominio.upper())  # padroniza visualmente para maiúsculo

    contagem = Counter(dominios).most_common(5)

    resultado = [{"cliente": cliente, "total": total} for cliente, total in contagem]

    return jsonify(resultado)

# Rota que traz os top 5 status com mais chamados
@insights_bp.route('/topStatusChamados', methods=['POST'])
def top_status_chamados():
    data = request.get_json()
    dias = int(data.get('dias', 1))
    data_limite = datetime.now() - timedelta(days=dias)

    # Consulta os status dos chamados no período
    chamados = Chamado.query.with_entities(Chamado.nome_status)\
        .filter(Chamado.data_criacao >= data_limite)\
        .all()

    # Contagem dos status
    status_list = [c[0] for c in chamados if c[0]]  # Remove Nones
    contagem = Counter(status_list).most_common(5)

    # Formata para JSON
    resultado = [{"status": status, "total": total} for status, total in contagem]
    return jsonify(resultado)

# Rota que traz os top 5 tipos com mais chamados 
@insights_bp.route('/topTipoChamados', methods=['POST'])
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
    data_limite = datetime.now() - timedelta(days=dias)

    # Consulta agrupada por tipo de ocorrência
    resultados = (
        db.session.query(
            Chamado.cod_tipo_ocorrencia,
            db.func.count().label('quantidade')
        )
        .filter(Chamado.data_criacao >= data_limite)
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

@insights_bp.route('/topSubCategoria', methods=['POST'])
def top_sub_categoria():
    data = request.get_json()
    dias = int(data.get('dias', 1))
    data_limite = datetime.now() - timedelta(days=dias)

    # Join entre Chamado e Categoria pela subcategoria
    resultados = db.session.query(
        Chamado.cod_sub_categoria.label('codigo'),
        Categoria.sub_categoria.label('nome'),
        func.count(Chamado.id).label('quantidade')
    ).join(
        Categoria, Chamado.cod_sub_categoria == Categoria.sequencia
    ).filter(
        Chamado.data_criacao >= data_limite
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

@insights_bp.route('/topCategoria', methods=['POST'])
def top_categoria():
    data = request.get_json()
    dias = int(data.get('dias', 1))
    data_limite = datetime.now() - timedelta(days=dias)

    # Join entre Chamado e Categoria pela subcategoria
    resultados = db.session.query(
        Chamado.cod_sub_categoria.label('codigo'),
        Categoria.categoria.label('nome'),
        func.count(Chamado.id).label('quantidade')
    ).join(
        Categoria, Chamado.cod_sub_categoria == Categoria.sequencia
    ).filter(
        Chamado.data_criacao >= data_limite
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

@insights_bp.route('/ChamadosEmAbertoSuporte', methods=['POST'])
def listar_chamados_aberto():
    dias = int(request.json.get("dias", 1))  # padrão: 1 dia
    hoje = datetime.now().date()
    data_inicio = hoje - timedelta(days=dias)

    # Combina datas com hora mínima e máxima do dia
    inicio = datetime.combine(data_inicio, datetime.min.time())
    fim = datetime.combine(hoje, datetime.max.time())

    chamados = Chamado.query.filter(
        Chamado.nome_status != 'Cancelado',
        Chamado.nome_status != 'Resolvido',
        Chamado.data_criacao >= inicio,
        Chamado.data_criacao <= fim
    ).all()

    total_chamados = len(chamados)
    codigos = [c.cod_chamado for c in chamados]

    return jsonify({
        "status": "success",
        "total_chamados": total_chamados,
        "cod_chamados": codigos
    })

# Rota que   
@insights_bp.route('/get/operadores', methods=['GET'])
def get_operadores():
    try:
        # Consulta apenas operadores do grupo 'SUPORTE B2B - COMNECT'
        operadores = db.session.query(
            Chamado.operador
        ).filter(
            Chamado.operador.isnot(None),
            Chamado.operador != '',
            Chamado.operador != 'Fabio',
            Chamado.operador != 'API',
            Chamado.operador != 'Caio',
            Chamado.operador != 'Paulo',
            Chamado.operador != 'Maria Luiza',
            Chamado.operador != 'Alexandre',
            Chamado.operador != 'Suporte',
            #Chamado.nome_grupo.like('SUPORTE COMNEcT%')
        ).distinct().order_by(
            Chamado.operador
        ).all()

        # Extrai apenas os nomes dos operadores
        lista_operadores = [op[0] for op in operadores if op[0]]

        return jsonify({
            "status": "success",
            "operadores": lista_operadores,
            "total": len(lista_operadores)
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
    # Rota que   

@insights_bp.route('/get/grupos', methods=['GET'])
def get_grupos():
    try:
        # Consulta grupos distintos, excluindo aqueles que contenham 'n1' ou 'n2'
        grupos = db.session.query(Chamado.nome_grupo)\
            .filter(
                Chamado.nome_grupo.isnot(None),
                ~Chamado.nome_grupo.ilike('%n1%'),
                ~Chamado.nome_grupo.ilike('%n2%'),
                ~Chamado.nome_grupo.ilike('%CSM%'),
            )\
            .distinct()\
            .all()

        lista_grupos = [gr[0] for gr in grupos]

        return jsonify({
            "status": "success",
            "grupos": lista_grupos,
            "total": len(lista_grupos)
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@insights_bp.route('/pSatisfacao', methods=['POST'])
def listar_p_satisfacao():
    data = request.get_json()
    dias = int(data.get('dias', 1))
    data_limite = (datetime.now() - timedelta(days=dias)).date()  # só data, sem hora

    # Total de pesquisas no período
    total_pesquisas = db.session.query(func.count()).filter(
        PesquisaSatisfacao.data_resposta >= data_limite
    ).scalar()

    # Total de pesquisas respondidas (com alternativa OU dissertativa preenchida)
    respondidas = db.session.query(func.count()).filter(
        and_(
            PesquisaSatisfacao.data_resposta >= data_limite,
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
        )
    ).scalar()

    # Total não respondidas
    nao_respondidas = total_pesquisas - respondidas

    # Cálculo dos percentuais
    percentual_respondidas = round((respondidas / total_pesquisas) * 100, 2) if total_pesquisas else 0
    percentual_nao_respondidas = round(100 - percentual_respondidas, 2) if total_pesquisas else 0

    return jsonify({
        "status": "success",
        "total": total_pesquisas,
        "respondidas": respondidas,
        "nao_respondidas": nao_respondidas,
        "percentual_respondidas": percentual_respondidas,
        "percentual_nao_respondidas": percentual_nao_respondidas
    })

@insights_bp.route('/abertos_vs_admin_resolvido_periodo', methods=['POST'])
def relacao_admin_abertos_vs_resolvido_periodo():
    try:
        dados = request.get_json(force=True)
        dias = int(dados.get("dias", 1))
        data_limite = datetime.now() - timedelta(days=dias)

        total_por_dia = {}
        resolvidos_por_dia = {}

        resultados_abertos = db.session.query(
            func.date(Chamado.data_criacao).label('dia'),
            func.count(Chamado.id)
        ).filter(
            Chamado.data_criacao >= data_limite
        ).group_by('dia').all()

        for dia, total in resultados_abertos:
            total_por_dia[dia] = total

        resultados_resolvidos = db.session.query(
            func.date(Chamado.data_criacao).label('dia'),
            func.count(Chamado.id)
        ).filter(
            Chamado.data_criacao >= data_limite,
            Chamado.nome_status == 'Resolvido'
        ).group_by('dia').all()

        for dia, total in resultados_resolvidos:
            resolvidos_por_dia[dia] = total

        todos_os_dias = sorted(set(total_por_dia.keys()).union(resolvidos_por_dia.keys()))

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

# Rota que traz os tickets por canal pelos períodos de 7, 15, 30 e 90 dias  
@insights_bp.route('/ticketsCanal', methods=['POST'])
def chamados_tickets_canal():
    try:
        dias = int(request.json.get("dias", 1))  # valor padrão: últimos 30 dias
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

@insights_bp.route('/tma_tms', methods=['GET'])
def tma_e_tms():
    try:
        dias = request.args.get('dias', default=1, type=int)  # padrão 30 dias
        data_limite = datetime.utcnow() - timedelta(days=dias)

        chamados_validos = db.session.query(Chamado).filter(
            Chamado.data_criacao >= data_limite,
            Chamado.data_criacao.isnot(None),
            Chamado.restante_p_atendimento.isnot(None),
            Chamado.restante_s_atendimento.isnot(None),
            Chamado.nome_status.ilike('%Resolvido%')
        ).all()

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

@insights_bp.route('/reabertos', methods=['POST'])
def reabertos():
    try:
        data = request.get_json()
        dias = int(data.get('dias', 1))

        hoje = datetime.utcnow()
        data_limite = hoje - timedelta(days=dias)

        # Todos os chamados do operador no período
        total_registros = RelatorioColaboradores.query.filter(
            func.date(RelatorioColaboradores.data_criacao) >= data_limite
        ).all()

        total_chamados = len(total_registros)

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

@insights_bp.route('/fcr', methods=['POST'])
def fcr():
    try:
        data = request.get_json()
        dias = int(data.get('dias', 1))

        hoje = datetime.utcnow()
        data_limite = hoje - timedelta(days=dias)

        # Todos os chamados do operador
        total_registros = RelatorioColaboradores.query.filter(
            RelatorioColaboradores.data_criacao >= data_limite
        ).all()

        # Chamados com FCR
        fcr_registros = [r for r in total_registros if r.first_call == 'S']
        codigos_fcr = [r.cod_chamado for r in fcr_registros if r.cod_chamado]

        return jsonify({
            "status": "success",
            "total_fcr": len(codigos_fcr),
            "percentual_fcr": round((len(codigos_fcr) / len(total_registros)) * 100, 2) if total_registros else 0,
            "cod_chamados": codigos_fcr
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@insights_bp.route('/abertos/status', methods=['POST'])
def estatisticas_chamados_periodos():
    try:
        dados = request.get_json(force=True)
        dias = int(dados.get("dias", 1))  
        data_limite = datetime.now() - timedelta(days=dias)

        chamados_abertos = db.session.query(
            Chamado.chave, 
            Chamado.nome_status,
            Chamado.nome_grupo,
            Chamado.data_criacao
        ).filter(
            Chamado.data_criacao >= data_limite,
            ~Chamado.nome_status.in_(["Cancelado"])
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
            "chamados_abertos": [
                {
                    "chave": chamado.chave,
                    "nome_status": chamado.nome_status,
                    "nome_grupo": chamado.nome_grupo
                } for chamado in chamados_abertos
            ]
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500