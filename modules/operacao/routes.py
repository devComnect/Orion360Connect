from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from application.models import Chamado, db, Categoria
from collections import Counter
from sqlalchemy import func, and_, or_,cast, Date
import re
import logging


operacao_bp = Blueprint('operacao_bp', __name__, url_prefix='/operacao')

# Rota que traz os top 5 grupos com mais chamados
@operacao_bp.route('/topGruposChamados', methods=['POST'])
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
@operacao_bp.route('/topClientesChamados', methods=['POST'])
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
@operacao_bp.route('/topStatusChamados', methods=['POST'])
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
@operacao_bp.route('/topTipoChamados', methods=['POST'])
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

@operacao_bp.route('/topSubCategoria', methods=['POST'])
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

@operacao_bp.route('/topCategoria', methods=['POST'])
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