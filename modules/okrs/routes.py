from flask import Blueprint, jsonify, render_template, request, url_for
import requests
from modules.deskmanager.authenticate.routes import token_desk
from modules.insights.utils import formatar_tempo
from datetime import datetime, timedelta
from application.models import Chamado, db, PesquisaSatisfacao, RelatorioColaboradores, PerformanceColaboradores, Metas
from collections import Counter
from sqlalchemy import func, and_, or_, extract, text
import numpy as np
from collections import defaultdict
import re

okrs_bp = Blueprint('okrs_bp', __name__, url_prefix='/okrs')

@okrs_bp.route('/reabertosOkrs', methods=['POST'])
def reabertos_okrs():
    try:
        data = request.get_json()
        dias = int(data.get('dias', 1))

        hoje = datetime.utcnow()
        data_limite = hoje - timedelta(days=dias)

        # Todos os chamados do operador no período
        total_registros = RelatorioColaboradores.query.filter(
            func.date(RelatorioColaboradores.data_criacao) >= data_limite
        ).all()

        #total_chamados = len(total_registros)

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
    
@okrs_bp.route('/tmaTmsOkrs', methods=['GET'])
def tma_e_tms_okrs():
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

@okrs_bp.route('/tmaTmsMensal', methods=['GET'])
def tma_tms_mensal():
    try:
        dias = request.args.get('dias', default=365, type=int)
        data_limite = datetime.utcnow() - timedelta(days=dias)

        chamados_validos = db.session.query(Chamado).filter(
            Chamado.data_criacao >= data_limite,
            Chamado.data_criacao.isnot(None),
            Chamado.restante_p_atendimento.isnot(None),
            Chamado.restante_s_atendimento.isnot(None),
            Chamado.nome_status.ilike('%Resolvido%')
        ).all()

        # Dicionários para armazenar listas de valores por (ano, mes)
        tma_por_mes = defaultdict(list)
        tms_por_mes = defaultdict(list)
        erros = []

        for chamado in chamados_validos:
            try:
                # Extrair ano e mês da data_criacao
                ano = chamado.data_criacao.year
                mes = chamado.data_criacao.month

                # Processar restante_p_atendimento
                tempo_p = chamado.restante_p_atendimento.strip()
                sinal_p = -1 if tempo_p.startswith("-") else 1
                partes_p = tempo_p.replace("-", "").split(":")
                h, m, s = (list(map(int, partes_p)) + [0, 0, 0])[:3]
                restante_p = timedelta(hours=h, minutes=m, seconds=s) * sinal_p

                # Processar restante_s_atendimento
                tempo_s = chamado.restante_s_atendimento.strip()
                sinal_s = -1 if tempo_s.startswith("-") else 1
                partes_s = tempo_s.replace("-", "").split(":")
                hs, ms, ss = (list(map(int, partes_s)) + [0, 0, 0])[:3]
                restante_s = timedelta(hours=hs, minutes=ms, seconds=ss) * sinal_s

                # Ignorar se tempos negativos
                if restante_p.total_seconds() < 0 or restante_s.total_seconds() < 0:
                    continue

                tms_individual = restante_s - restante_p
                # Ignorar se TMS negativo ou maior que 30 dias
                if tms_individual.total_seconds() < 0 or tms_individual > timedelta(days=30):
                    continue

                # Guardar os valores em segundos por mês
                tma_por_mes[(ano, mes)].append(restante_p.total_seconds())
                tms_por_mes[(ano, mes)].append(tms_individual.total_seconds())

            except Exception as e:
                erros.append({
                    "cod_chamado": chamado.cod_chamado,
                    "restante_p_atendimento": chamado.restante_p_atendimento,
                    "restante_s_atendimento": chamado.restante_s_atendimento,
                    "erro": str(e)
                })
                continue

        # Ordenar as chaves (ano, mes) para construir resultado ordenado
        meses_ordenados = sorted(tma_por_mes.keys())

        labels = []
        medias_tma = []
        medias_tms = []

        for ano, mes in meses_ordenados:
            tma_lista = tma_por_mes.get((ano, mes), [])
            tms_lista = tms_por_mes.get((ano, mes), [])

            if not tma_lista or not tms_lista:
                continue

            media_tma = np.mean(tma_lista) / 60  # minutos
            media_tms = np.mean(tms_lista) / 60  # minutos

            # Formatando label "MMM/yy"
            labels.append(datetime(ano, mes, 1).strftime('%b/%y'))
            medias_tma.append(round(media_tma, 2))
            medias_tms.append(round(media_tms, 2))

        def formatar_tempo(minutos: float) -> str:
            if minutos < 60:
                return f"{round(minutos)} min"
            elif minutos < 1440:
                return f"{minutos / 60:.1f} h"
            else:
                return f"{minutos / 1440:.2f} dias"

        return jsonify({
            "status": "success",
            "labels": labels,
            "media_tma_min": medias_tma,
            "media_tms_min": medias_tms,
            "chamados_processados": sum(len(v) for v in tma_por_mes.values()),
            "erros_amostragem": erros[:10]
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@okrs_bp.route('/tminTmaxOkrs', methods=['POST'])
def get_tmin_tmax_okrs():
    try:
        dias = int(request.json.get("dias", 1))  # padrão: 1 dia
        hoje = datetime.now().date()
        data_inicio = hoje - timedelta(days=dias)

        # Contagem de registros válidos
        count_min = db.session.query(func.count(PerformanceColaboradores.id)).filter(
            PerformanceColaboradores.tempo_minatend != 0,
            PerformanceColaboradores.data >= data_inicio,
            PerformanceColaboradores.data <= hoje
        ).scalar() or 0

        count_max = db.session.query(func.count(PerformanceColaboradores.id)).filter(
            PerformanceColaboradores.tempo_maxatend != 0,
            PerformanceColaboradores.data >= data_inicio,
            PerformanceColaboradores.data <= hoje
        ).scalar() or 0

        # Totais (em segundos → converte p/ minutos)
        total_ligacoes_minatend = db.session.query(
            func.sum(PerformanceColaboradores.tempo_minatend)
        ).filter(
            PerformanceColaboradores.tempo_minatend != 0,
            PerformanceColaboradores.data >= data_inicio,
            PerformanceColaboradores.data <= hoje
        ).scalar() or 0

        total_ligacoes_maxatend = db.session.query(
            func.sum(PerformanceColaboradores.tempo_maxatend)
        ).filter(
            PerformanceColaboradores.tempo_maxatend != 0,
            PerformanceColaboradores.data >= data_inicio,
            PerformanceColaboradores.data <= hoje
        ).scalar() or 0

        # Converte para minutos
        total_ligacoes_minatend = total_ligacoes_minatend / 60
        total_ligacoes_maxatend = total_ligacoes_maxatend / 60

        # Médias em minutos
        media_min = (total_ligacoes_minatend / count_min) if count_min > 0 else 0
        media_max = (total_ligacoes_maxatend / count_max) if count_max > 0 else 0

        def formatar_tempo(minutos: float) -> str:
            if minutos < 60:
                return f"{round(minutos)} min"
            elif minutos < 1440:
                return f"{minutos / 60:.1f} h"
            else:
                return f"{minutos / 1440:.2f} dias"

        return jsonify({
            "status": "success",
            "dias": dias,
            "tmin_total": formatar_tempo(total_ligacoes_minatend),
            "tmax_total": formatar_tempo(total_ligacoes_maxatend),
            "tmin_media": formatar_tempo(media_min),
            "tmax_media": formatar_tempo(media_max)
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Rota que traz os SLAs globais
@okrs_bp.route('/slaOkrs', methods=['POST'])
def sla_insights_okrs():
    try:
        data = request.get_json()
        dias = int(data.get('dias', 1)) 
        hoje = datetime.now()
        data_inicio = hoje - timedelta(days=dias)

        # Chamados no período
        chamados = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.data_criacao >= datetime.combine(data_inicio.date(), datetime.min.time()),
            Chamado.data_criacao <= datetime.combine(hoje.date(), datetime.max.time())
        ).all()

        expirados_atendimento = sum(1 for c in chamados if c.sla_atendimento == 'S')
        expirados_resolucao = sum(1 for c in chamados if c.sla_resolucao == 'S')
        chamados_atendimento_prazo = sum(1 for c in chamados if c.sla_atendimento == 'N')
        chamados_finalizado_prazo = sum(1 for c in chamados if c.sla_resolucao == 'N')

        total_chamados = len(chamados)

        percentual_atendimento = round((expirados_atendimento / total_chamados) * 100, 2) if total_chamados else 0
        percentual_resolucao = round((expirados_resolucao / total_chamados) * 100, 2) if total_chamados else 0
        percentual_prazo_atendimento = round((chamados_atendimento_prazo/total_chamados) * 100, 2) if total_chamados else 0
        percentual_prazo_resolucao = round((chamados_finalizado_prazo/total_chamados) * 100, 2) if total_chamados else 0

        # 🟡 Buscar metas do banco
        metas = Metas.query.first()

        return jsonify({
            "status": "success",
            "total_chamados": total_chamados,
            "percentual_prazo_atendimento" : percentual_prazo_atendimento,
            "percentual_prazo_resolucao": percentual_prazo_resolucao,
            "percentual_atendimento": percentual_atendimento,
            "percentual_resolucao": percentual_resolucao,
            "codigos_atendimento": [c.cod_chamado for c in chamados if c.sla_atendimento == 'S'],
            "codigos_resolucao": [c.cod_chamado for c in chamados if c.sla_resolucao == 'S'],
            
            # ✅ Envie as metas para o front-end
            "meta_prazo_atendimento": metas.sla_atendimento_prazo,
            "meta_prazo_resolucao": metas.sla_resolucao_prazo
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@okrs_bp.route('/slaOkrsMes', methods=['POST'])
def sla_okrs_mes():
    try:
        from collections import defaultdict
        from datetime import datetime, timedelta

        data = request.get_json()
        dias = int(data.get('dias', 180))
        hoje = datetime.now()
        data_inicio = hoje - timedelta(days=dias)

        chamados = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.data_criacao >= data_inicio,
            Chamado.data_criacao <= hoje
        ).all()

        # Agrupar chamados por mês
        chamados_por_mes = defaultdict(list)
        for chamado in chamados:
            key = chamado.data_criacao.strftime('%Y-%m')  # Exemplo: '2025-09'
            chamados_por_mes[key].append(chamado)

        labels = []
        atendimento_prazo = []
        resolucao_prazo = []

        for key in sorted(chamados_por_mes.keys()):
            lista = chamados_por_mes[key]
            total = len(lista)

            no_prazo_atendimento = sum(1 for c in lista if c.sla_atendimento == 'N')
            no_prazo_resolucao = sum(1 for c in lista if c.sla_resolucao == 'N')

            pct_atendimento = round((no_prazo_atendimento / total) * 100, 2) if total else 0
            pct_resolucao = round((no_prazo_resolucao / total) * 100, 2) if total else 0

            mes_formatado = datetime.strptime(key, '%Y-%m').strftime('%b/%y').capitalize()
            labels.append(mes_formatado)
            atendimento_prazo.append(pct_atendimento)
            resolucao_prazo.append(pct_resolucao)

        return jsonify({
            "status": "success",
            "labels": labels,
            "sla_atendimento": atendimento_prazo,
            "sla_resolucao": resolucao_prazo
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@okrs_bp.route('/csatOkrs', methods=['POST'])
def csat_okrs():
    data = request.get_json()
    dias = int(data.get('dias', 1))
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
            func.length(PesquisaSatisfacao.alternativa) > 0
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

@okrs_bp.route('/csatOkrsMensal', methods=['POST'])
def csat_okrs_mensal():
    data = request.get_json()
    dias = int(data.get('dias', 180))  # padrão 30 dias
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

    # Buscar alternativas e data agrupando por dia
    query = (
        db.session.query(
            func.date(PesquisaSatisfacao.data_resposta).label('data'),
            PesquisaSatisfacao.alternativa
        )
        .filter(
            PesquisaSatisfacao.data_resposta >= data_limite,
            PesquisaSatisfacao.alternativa.isnot(None),
            func.length(PesquisaSatisfacao.alternativa) > 0
        )
        .all()
    )

    # Agregar respostas por dia
    respostas_por_dia = {}
    for registro in query:
        data_str = registro.data.strftime('%Y-%m-%d')
        valor = registro.alternativa.strip()
        if valor.isdigit():
            numero = int(valor)
            if 0 <= numero <= 10:
                nota = numero
            else:
                continue
        elif valor in CSAT_MAP:
            nota = CSAT_MAP[valor]
        else:
            continue

        if data_str not in respostas_por_dia:
            respostas_por_dia[data_str] = []
        respostas_por_dia[data_str].append(nota)

    # Calcular CSAT por dia (percentual de notas >=7)
    resultado = []
    for data_str in sorted(respostas_por_dia.keys()):
        notas = respostas_por_dia[data_str]
        total = len(notas)
        satisfatorias = sum(1 for n in notas if n >= 7)
        csat_val = round((satisfatorias / total) * 100, 2) if total else 0
        resultado.append({"date": data_str, "csat": csat_val})

    return jsonify(resultado)

@okrs_bp.route('/csatMensal', methods=['POST'])
def csat_mensal():
    try:
        data = request.get_json()
        dias = int(data.get('dias', 180))
        hoje = datetime.now()
        data_inicio = hoje - timedelta(days=dias)

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

        # Buscar respostas no período
        respostas = db.session.query(
            PesquisaSatisfacao.alternativa,
            PesquisaSatisfacao.data_resposta
        ).filter(
            PesquisaSatisfacao.data_resposta >= data_inicio,
            PesquisaSatisfacao.alternativa.isnot(None),
            func.length(PesquisaSatisfacao.alternativa) > 0
        ).all()

        respostas_por_mes = defaultdict(list)

        for alt, data_resposta in respostas:
            valor = alt.strip()
            nota = None

            if valor.isdigit():
                numero = int(valor)
                if 0 <= numero <= 10:
                    nota = numero
            elif valor in CSAT_MAP:
                nota = CSAT_MAP[valor]

            if nota is not None:
                chave_mes = data_resposta.strftime('%Y-%m')
                respostas_por_mes[chave_mes].append(nota)

        labels = []
        csat_mensal = []

        for key in sorted(respostas_por_mes.keys()):
            notas = respostas_por_mes[key]
            total = len(notas)
            satisfatorias = sum(1 for n in notas if n >= 7)  # ou >= 8, dependendo da sua política

            csat = round((satisfatorias / total) * 100, 2) if total else 0

            mes_formatado = datetime.strptime(key, '%Y-%m').strftime('%b/%y').capitalize()
            labels.append(mes_formatado)
            csat_mensal.append(csat)

        return jsonify({
            "status": "success",
            "labels": labels,
            "csat": csat_mensal
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@okrs_bp.route('/cesOkrs', methods=['POST'])
def ces_okrs():
    try:
        data = request.get_json()

        # Garantir que 'dias' seja um inteiro válido
        try:
            dias = int(data.get('dias', 1))
        except (ValueError, TypeError):
            dias = 1

        data_limite = (datetime.now() - timedelta(days=dias)).date()

        CES_MAP = {
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

        respostas_brutas = db.session.query(PesquisaSatisfacao.alternativa).filter(
            and_(
                PesquisaSatisfacao.data_resposta >= data_limite,
                PesquisaSatisfacao.alternativa.isnot(None),
                func.length(PesquisaSatisfacao.alternativa) > 0
            )
        ).all()

        valores_convertidos = []

        for resp in respostas_brutas:
            valor = resp[0].strip()
            if valor.isdigit():
                numero = int(valor)
                if 0 <= numero <= 10:
                    valores_convertidos.append(numero)
            elif valor in CES_MAP:
                valores_convertidos.append(CES_MAP[valor])

        total_respostas_ces = len(valores_convertidos)

        if total_respostas_ces > 0:
            soma_ponderada = sum(valores_convertidos)
            ces_final = round(soma_ponderada / total_respostas_ces, 2)
            ces_percentual = round((ces_final / 10) * 100, 2)

            # Definir nota e descrição com base no percentual
            if ces_percentual == 0:
                nota = 1
                descricao = 'Alto esforço'
            elif ces_percentual < 16.3:
                nota = 1
                descricao = 'Alto esforço'
            elif ces_percentual < 33.3:
                nota = 2
                descricao = 'Alto esforço'
            elif ces_percentual < 50:
                nota = 3
                descricao = 'Alto esforço'
            elif ces_percentual < 66.7:
                nota = 4
                descricao = 'Esforço moderado'
            elif ces_percentual < 83:
                nota = 5
                descricao = 'Esforço moderado'
            elif ces_percentual < 92:
                nota = 6
                descricao = 'Baixo esforço'
            else:
                nota = 7
                descricao = 'Baixo esforço'
        else:
            nota = 0
            descricao = 'Sem dados'
            ces_percentual = 0.0

        return jsonify({
            "status": "success",
            "nota": nota,
            "descricao": descricao,
            "total_respostas_ces": total_respostas_ces,
            "ces_percentual": ces_percentual
        })

    except Exception as e:
        # Log no servidor (opcional: enviar para monitoramento)
        print(f"[ERRO /ces] {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@okrs_bp.route('/npsOkrs', methods=['POST'])
def nps_okrs():
    data = request.get_json()
    dias = int(data.get('dias', 1))
    data_limite = (datetime.now() - timedelta(days=dias)).date()

    NPS_MAP = {
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
            func.length(PesquisaSatisfacao.alternativa) > 0
        )
    ).all()

    # Converter para escala numérica
    notas = [NPS_MAP.get(alt[0], 0) for alt in alternativas_brutas if NPS_MAP.get(alt[0])]

    total = len(notas)
    if total == 0:
        return jsonify({"nps": 0, "status": "Sem dados suficientes"}), 200

    # Classificar em promotores, neutros e detratores
    promotores = sum(1 for n in notas if n >= 9)
    neutros = sum(1 for n in notas if 7 <= n <= 8)
    detratores = sum(1 for n in notas if n <= 6)

    # Cálculo do NPS
    nps_valor = ((promotores - detratores) / total) * 100
    nps_valor = round(nps_valor, 2)

    # Classificação
    if nps_valor >= 75:
        status = "Excelente"
    elif nps_valor >= 50:
        status = "Muito bom"
    elif nps_valor >= 40:
        status = "Razoável"
    else:
        status = "Ruim"

    return jsonify({
        "nps": nps_valor,
        "status": status,
        "total_respostas": total,
        "promotores": promotores,
        "neutros": neutros,
        "detratores": detratores
    }), 200

@okrs_bp.route('/setMetas', methods=['POST'])
def set_metas():
    data = request.get_json()

    # Tenta buscar o registro com ID fixo (por exemplo, ID=1)
    metas = Metas.query.get(1)

    if not metas:
        metas = Metas(id=1)  # Cria com id=1 se não existir
        db.session.add(metas)

    # Atualiza os campos com os dados enviados
    metas.reabertos = data.get('reabertos')
    metas.fcr = data.get('fcr')
    metas.tma = data.get('tma')
    metas.tms = data.get('tms')
    metas.tmin = data.get('tmin')
    metas.tmax = data.get('tmax')
    metas.sla_atendimento_prazo = data.get('sla_atendimento_prazo')
    metas.sla_resolucao_prazo = data.get('sla_resolucao_prazo')
    metas.csat = data.get('csat')

    db.session.commit()

    return jsonify(status='success', message='Meta foi registrada com sucesso')

@okrs_bp.route('/getMetas', methods=['GET'])
def get_metas():
    meta = Metas.query.first()
    if not meta:
        return jsonify({"error": "Nenhuma meta definida"}), 404

    return jsonify({
        "reabertos": meta.reabertos,
        "fcr": meta.fcr,
        "tma": meta.tma,
        "tms": meta.tms,
        "tmin": meta.tmin,
        "tmax": meta.tmax,
        "sla_atendimento_prazo": meta.sla_atendimento_prazo,
        "sla_resolucao_prazo": meta.sla_resolucao_prazo,
        "csat": meta.csat
    })

@okrs_bp.route('/fcrMensal', methods=['POST'])
def fcr_mensal():
    try:
        data = request.get_json()
        dias = int(data.get('dias', 180))  # padrão: últimos 6 meses

        hoje = datetime.utcnow()
        data_inicio = hoje - timedelta(days=dias)

        # Filtra registros no período
        registros = RelatorioColaboradores.query.filter(
            RelatorioColaboradores.data_criacao >= data_inicio,
            RelatorioColaboradores.nome_status == 'Resolvido'
        ).all()

        chamados = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.nome_status == 'Resolvido',
            Chamado.data_finalizacao != None,
            Chamado.data_finalizacao >= data_inicio,
            Chamado.data_finalizacao <= hoje
        ).all()

        # Agrupar por mês
        chamados_por_mes = defaultdict(list)
        fcr_por_mes = defaultdict(list)

        for chamado in chamados:
            key = chamado.data_finalizacao.strftime('%Y-%m')
            chamados_por_mes[key].append(chamado.cod_chamado)

        for reg in registros:
            if reg.first_call == 'S' and reg.cod_chamado:
                key = reg.data_criacao.strftime('%Y-%m')
                fcr_por_mes[key].append(reg.cod_chamado)

        labels = []
        fcr_percentuais = []

        for key in sorted(chamados_por_mes.keys()):
            total = len(chamados_por_mes[key])
            fcr = len(set(fcr_por_mes.get(key, [])))
            percentual = round((fcr / total) * 100, 2) if total else 0

            mes_formatado = datetime.strptime(key, '%Y-%m').strftime('%b/%y').capitalize()
            labels.append(mes_formatado)
            fcr_percentuais.append(percentual)

        return jsonify({
            "status": "success",
            "labels": labels,
            "fcr": fcr_percentuais
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@okrs_bp.route('/fcrOkrs', methods=['POST'])
def fcr_okrs():
    try:
        data = request.get_json()
        dias = int(data.get('dias', 1))

        hoje = datetime.utcnow()
        data_limite = hoje - timedelta(days=dias)

        # Todos os chamados do operador
        total_registros = RelatorioColaboradores.query.filter(
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
            Chamado.data_finalizacao <= fim
        ).count()

        # Chamados com FCR
        fcr_registros = [r for r in total_registros if r.first_call == 'S']
        codigos_fcr = [r.cod_chamado for r in fcr_registros if r.cod_chamado]

        return jsonify({
            "status": "success",
            "total_fcr": len(codigos_fcr),
            "percentual_fcr": round((len(codigos_fcr) / total_chamados) * 100, 2) if total_chamados else 0,
            "cod_chamados": codigos_fcr,
            "total_chamados": total_chamados
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500