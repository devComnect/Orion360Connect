from flask import Blueprint, jsonify, render_template, request, url_for
import requests
from modules.deskmanager.authenticate.routes import token_desk
from datetime import datetime, timedelta
from application.models import Chamado, db, Categoria, PesquisaSatisfacao
from collections import Counter
from sqlalchemy import func, and_, or_
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
        Chamado.data_criacao <= data_fim
    ).group_by(Chamado.nome_grupo).order_by(db.desc('total')).limit(5).all()

    dados = [{"grupo": grupo or "Não informado", "total": total} for grupo, total in resultados]
    return jsonify(dados)

# Rota que traz os top 5 clientes com mais chamados
@insights_bp.route('/topClientesChamados', methods=['POST'])
def top_clientes_chamados():
    data = request.get_json()
    dias = int(data.get('dias', 1))

    data_limite = datetime.now() - timedelta(days=dias)

    # Consulta os chamados no período
    chamados = Chamado.query.with_entities(Chamado.solicitante_email)\
        .filter(Chamado.data_criacao >= data_limite)\
        .all()

    # Extrai domínios dos e-mails
    dominios = []
    for c in chamados:
        email = c[0]
        if email and "@" in email:
            dominio = re.sub(r"^.*@", "", email).split('.')[0].upper()  # exemplo: fiserv.com → fiserv
            dominios.append(dominio)

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

@insights_bp.route('/pSatisfacao', methods=['POST'])
def listar_p_satisfacao():
    data = request.get_json()
    print(data)
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

# Rota traz os chamados abertos atualmente
'''@insights_bp.route('/ChamadosEmAbertoSuporte', methods=['POST'])
def listar_chamados_aberto():
    token_response = token_desk()
    
    try:
        # Faz a requisição para a API de chamados
        response = requests.post(
            'https://api.desk.ms/ChamadosSuporte/lista',
            headers={
                'Authorization': f'{token_response}',
                'Content-Type': 'application/json'
            },
            json={
                "Pesquisa":"", 	#Pesquisa por Assunto,Código,Descrição,Solicitante,Status,Operador ou Dados do Cliente
            "Tatual":"", 	#Opcional para uso com mais de 3000 registros, define a partir de qual registro exibir
            "Ativo":"EmAberto",	#Pode usar um texto pré definido ou o código do Status*
            "StatusSLA":"S", #S: Apenas com SLA, A: Apenas sem SLA, N: Com e Sem SLA (todos)
            "Colunas": 	#Colunas a serem exibidas, Caso não seja enviado trará todas
            {
                "Chave":"on",		#Chave do chamado
                "CodChamado":"on",	#Código de referência do chamado (mmaa-000000)
                "NomePrioridade":"on",	#Prioridade do chamado
                "DataCriacao":"on",	#Data da criação
                "HoraCriacao":"on",	#Hora da criação
                "DataFinalizacao":"on",	#Data da finalização
                "HoraFinalizacao":"on", #Hora da finalização
                "DataAlteracao":"on", 	#Data da Ultima Alteração
                "HoraAlteracao":"on", 	#Hora da Ultima Alteração
                "NomeStatus":"on",	#Nome do Status atual do chamado
                "Assunto":"on",	
                "Descricao":"on",
                "ChaveUsuario":"on",	#Código do Solicitante	
                "NomeUsuario":"on",		#Primeiro nome do Solicitante
                "SobrenomeUsuario":"on",	#Sobrenome do Solicitante
                "NomeCompletoSolicitante":"on", #Nome Completo do Solicitante
                "SolicitanteEmail":"on",	#Email do Solicitante
                "NomeOperador":"on",		#Primeiro nome do Operador
                "SobrenomeOperador":"on",	#Sobrenome do Operador
                "TotalAcoes":"on",		#Quantidade de ações realizadas no chamado
                "TotalAnexos":"on",
                "Sla":"on",			#Exibe as informações sobre o SLA (várias colunas serão exibidas)
                "CodGrupo":"on",		#Código do grupo de atendimento do chamado
                "NomeGrupo":"on",		#Nome do grupo de atendimento do chamado
                "CodSolicitacao":"on", 		#Código de Solicitação
                "CodSubCategoria":"on", 	#Código de Sub Categoria
                "CodTipoOcorrencia":"on", 	#Código do Tipo de Ocorrência
                "CodCategoriaTipo":"on", 	#Código do Tipo de Categoria
                "CodPrioridadeAtual":"on", 	#Código da Prioridade
                "CodStatusAtual":"on"	#Código do Status Atual
            },
            "Ordem": [	#Colunas para ordenação
                {
                "Coluna": "Chave",
                "Direcao": "true"	#true:ASC e false:DESC	
                }
            ]
            }
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
        }), 500'''