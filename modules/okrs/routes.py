from flask import Blueprint, jsonify, request, send_file
from modules.okrs.utils import gerar_relatorio_csat, gerar_relatorio_sla, gerar_relatorio_tma_tms, gerar_relatorio_fcr, gerar_relatorio_reabertura
from datetime import datetime, timedelta
from application.models import Chamado, db, PesquisaSatisfacao, RelatorioColaboradores, PerformanceColaboradores, Metas
from sqlalchemy import func, and_, or_, extract, text
import numpy as np
from collections import defaultdict
import pandas as pd
import re, os, io

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

@okrs_bp.route('/tmaTmsMensal', methods=['POST'])
def tma_tms_mensal():
    try:
        data = request.get_json() or {}
        dias = data.get("dias", 365)
        data_limite = datetime.utcnow() - timedelta(days=dias)

        chamados_validos = db.session.query(Chamado).filter(
            Chamado.data_criacao >= data_limite,
            Chamado.data_criacao.isnot(None),
            Chamado.restante_p_atendimento.isnot(None),
            Chamado.restante_s_atendimento.isnot(None),
            Chamado.nome_status.ilike('%Resolvido%')
        ).all()

        tma_por_mes = defaultdict(list)
        tms_por_mes = defaultdict(list)
        erros = []

        for chamado in chamados_validos:
            try:
                ano = chamado.data_criacao.year
                mes = chamado.data_criacao.month

                tempo_p = (chamado.restante_p_atendimento or "").strip()
                tempo_s = (chamado.restante_s_atendimento or "").strip()

                # pula se for vazio ou inválido
                if not tempo_p or not tempo_s:
                    continue

                # ---- Processa P ----
                sinal_p = -1 if tempo_p.startswith("-") else 1
                partes_p = tempo_p.replace("-", "").split(":")
                if not all(p.isdigit() for p in partes_p):  
                    continue
                h, m, s = (list(map(int, partes_p)) + [0, 0, 0])[:3]
                restante_p = timedelta(hours=h, minutes=m, seconds=s) * sinal_p

                # ---- Processa S ----
                sinal_s = -1 if tempo_s.startswith("-") else 1
                partes_s = tempo_s.replace("-", "").split(":")
                if not all(p.isdigit() for p in partes_s):  
                    continue
                hs, ms, ss = (list(map(int, partes_s)) + [0, 0, 0])[:3]
                restante_s = timedelta(hours=hs, minutes=ms, seconds=ss) * sinal_s

                # Ignora tempos negativos
                if restante_p.total_seconds() < 0 or restante_s.total_seconds() < 0:
                    continue

                tms_individual = restante_s - restante_p
                if tms_individual.total_seconds() < 0 or tms_individual > timedelta(days=30):
                    continue

                # guarda em segundos
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

        meses_ordenados = sorted(tma_por_mes.keys())
        labels, medias_tma, medias_tms = [], [], []

        for ano, mes in meses_ordenados:
            tma_lista = tma_por_mes.get((ano, mes), [])
            tms_lista = tms_por_mes.get((ano, mes), [])

            if not tma_lista or not tms_lista:
                continue

            media_tma = np.mean(tma_lista) / 60
            media_tms = np.mean(tms_lista) / 60

            labels.append(datetime(ano, mes, 1).strftime('%b/%y'))
            medias_tma.append(round(media_tma, 2))
            medias_tms.append(round(media_tms, 2))

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

# Rota aparentemente não está em uso, talvez excluí-la mais tarde
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
    
# -----------------------------
# Rota principal de exportação
# -----------------------------
@okrs_bp.route('/exportarOkrs', methods=['POST'])
def exportar_okrs_anual():
    try:
        hoje = datetime.now()
        inicio_ano = datetime(hoje.year, 1, 1)
        fim_ano = datetime(hoje.year, 12, 31)

        # Aqui chamaremos as funções de cada métrica
        relatorios = [
            gerar_relatorio_csat(inicio_ano, fim_ano),
            gerar_relatorio_sla(inicio_ano, fim_ano),
            gerar_relatorio_tma_tms(inicio_ano, fim_ano),
            gerar_relatorio_fcr(inicio_ano, fim_ano),
            gerar_relatorio_reabertura(inicio_ano, fim_ano),
        ]

        # Monta o arquivo Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for df, aba in relatorios:
                df.to_excel(writer, index=False, sheet_name=aba)

                workbook = writer.book
                worksheet = writer.sheets[aba]

                formato_header = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2'})
                formato_num = workbook.add_format({'num_format': '0.00'})
                #formato_texto = workbook.add_format({'border': 1})

                worksheet.set_column('A:A', 15)
                worksheet.set_column('B:B', 12, formato_num)
                worksheet.set_column('C:C', 15)
                worksheet.write_row('A1', list(df.columns), formato_header)

        output.seek(0)

        return send_file(
            output,
            download_name=f"Relatorio_OKRs.xlsx",
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@okrs_bp.route('/csatQuarter', methods=['POST'])
def csat_quarter():
    try:
        hoje = datetime.now()
        ano_atual = hoje.year

        CSAT_MAP = {
            'Péssimo': 1, 'Discordo Totalmente': 2, 'Discordo Parcialmente': 3,
            'Neutro': 4, 'Concordo Parcialmente': 5, 'Regular': 6,
            'Bom': 7, 'Concordo': 8, 'Concordo Plenamente': 9, 'Ótimo': 10
        }

        # Buscar respostas apenas do ano atual
        respostas = db.session.query(
            PesquisaSatisfacao.alternativa,
            PesquisaSatisfacao.data_resposta
        ).filter(
            func.extract('year', PesquisaSatisfacao.data_resposta) == ano_atual,
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
                chave_mes = data_resposta.month  # só o número do mês
                respostas_por_mes[chave_mes].append(nota)

        # Calcula CSAT por mês
        csat_por_mes = {}
        for mes, notas in respostas_por_mes.items():
            total = len(notas)
            satisfatorias = sum(1 for n in notas if n >= 7)
            csat_por_mes[mes] = round((satisfatorias / total) * 100, 2) if total else 0

        # Distribuição de meses por quarter
        quarters = {
            'Q1': [1, 2, 3],
            'Q2': [4, 5, 6],
            'Q3': [7, 8, 9],
            'Q4': [10, 11, 12]
        }

        resultado = {}
        for q, meses in quarters.items():
            labels = []
            valores = []
            for m in meses:
                nome_mes = datetime(ano_atual, m, 1).strftime('%b').capitalize()
                labels.append(nome_mes)
                valores.append(csat_por_mes.get(m, 0))
            resultado[q] = {"labels": labels, "valores": valores}

        return jsonify({"status": "success", "quarters": resultado})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@okrs_bp.route('/slaOkrsQuarter', methods=['POST'])
def sla_okrs_quarter():
    try:
        hoje = datetime.now()
        ano_atual = hoje.year

        # Busca todos os chamados do ano atual
        chamados = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.data_criacao.between(datetime(ano_atual, 1, 1), hoje)
        ).all()

        # Agrupa chamados por mês
        sla_por_mes = defaultdict(lambda: {"sla_atendimento": 0, "sla_resolucao": 0})
        for c in chamados:
            mes = c.data_criacao.month
            if "total" not in sla_por_mes[mes]:
                sla_por_mes[mes]["total"] = 0
                sla_por_mes[mes]["atendimento_ok"] = 0
                sla_por_mes[mes]["resolucao_ok"] = 0

            sla_por_mes[mes]["total"] += 1
            sla_por_mes[mes]["atendimento_ok"] += 1 if c.sla_atendimento == 'N' else 0
            sla_por_mes[mes]["resolucao_ok"] += 1 if c.sla_resolucao == 'N' else 0

        # Calcula percentual por mês
        for m in range(1, 13):
            total = sla_por_mes[m].get("total", 0)
            if total > 0:
                sla_por_mes[m]["sla_atendimento"] = round((sla_por_mes[m]["atendimento_ok"]/total)*100,2)
                sla_por_mes[m]["sla_resolucao"] = round((sla_por_mes[m]["resolucao_ok"]/total)*100,2)
            else:
                sla_por_mes[m]["sla_atendimento"] = 0
                sla_por_mes[m]["sla_resolucao"] = 0

        # Distribuição de meses por quarter
        quarters = {
            'Q1': [1, 2, 3],
            'Q2': [4, 5, 6],
            'Q3': [7, 8, 9],
            'Q4': [10, 11, 12]
        }

        resultado = {}
        for q, meses in quarters.items():
            labels = [datetime(1900, m, 1).strftime('%b').capitalize() for m in meses]
            atendimento = [sla_por_mes[m]["sla_atendimento"] for m in meses]
            resolucao = [sla_por_mes[m]["sla_resolucao"] for m in meses]
            resultado[q] = {"labels": labels, "sla_atendimento": atendimento, "sla_resolucao": resolucao}

        return jsonify({"status": "success", "quarters": resultado})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@okrs_bp.route('/fcrQuarter', methods=['POST'])
def fcr_quarter():
    try:
        hoje = datetime.utcnow()
        ano_atual = hoje.year

        # Busca registros e chamados resolvidos no ano atual
        registros = RelatorioColaboradores.query.filter(
            RelatorioColaboradores.data_criacao.between(datetime(ano_atual, 1, 1), hoje),
            RelatorioColaboradores.nome_status == 'Resolvido'
        ).all()

        chamados = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.nome_status == 'Resolvido',
            Chamado.data_finalizacao != None,
            Chamado.data_finalizacao.between(datetime(ano_atual, 1, 1), hoje)
        ).all()

        # Agrupar por mês
        chamados_por_mes = defaultdict(list)
        fcr_por_mes = defaultdict(list)

        for chamado in chamados:
            key = chamado.data_finalizacao.month
            chamados_por_mes[key].append(chamado.cod_chamado)

        for reg in registros:
            if reg.first_call == 'S' and reg.cod_chamado:
                key = reg.data_criacao.month
                fcr_por_mes[key].append(reg.cod_chamado)

        # Distribuição de meses por quarter
        quarters = {
            'Q1': [1, 2, 3],
            'Q2': [4, 5, 6],
            'Q3': [7, 8, 9],
            'Q4': [10, 11, 12]
        }

        resultado = {}
        for q, meses in quarters.items():
            labels = [datetime(1900, m, 1).strftime('%b').capitalize() for m in meses]
            fcr_data = []

            for m in meses:
                total_chamados = len(chamados_por_mes.get(m, []))
                fcr_chamados = len(set(fcr_por_mes.get(m, [])))
                percentual = round((fcr_chamados / total_chamados) * 100, 2) if total_chamados else 0
                fcr_data.append(percentual)

            resultado[q] = {"labels": labels, "fcr": fcr_data}

        return jsonify({"status": "success", "quarters": resultado})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@okrs_bp.route('/tmaTmsQuarter', methods=['POST'])
def tma_tms_quarter():
    try:
        hoje = datetime.utcnow()
        ano_atual = hoje.year

        # Busca chamados válidos do ano atual
        chamados_validos = db.session.query(Chamado).filter(
            Chamado.data_criacao.isnot(None),
            Chamado.restante_p_atendimento.isnot(None),
            Chamado.restante_s_atendimento.isnot(None),
            Chamado.nome_status.ilike('%Resolvido%'),
            Chamado.data_criacao.between(datetime(ano_atual, 1, 1), hoje)
        ).all()

        tma_por_mes = defaultdict(list)
        tms_por_mes = defaultdict(list)

        for chamado in chamados_validos:
            try:
                mes = chamado.data_criacao.month

                # Processa TMA
                tempo_p = chamado.restante_p_atendimento.strip()
                if not tempo_p: continue
                sinal_p = -1 if tempo_p.startswith("-") else 1
                h, m, s = (list(map(int, tempo_p.replace("-", "").split(":"))) + [0, 0, 0])[:3]
                restante_p = timedelta(hours=h, minutes=m, seconds=s) * sinal_p
                if restante_p.total_seconds() < 0: continue

                # Processa TMS
                tempo_s = chamado.restante_s_atendimento.strip()
                if not tempo_s: continue
                sinal_s = -1 if tempo_s.startswith("-") else 1
                hs, ms, ss = (list(map(int, tempo_s.replace("-", "").split(":"))) + [0, 0, 0])[:3]
                restante_s = timedelta(hours=hs, minutes=ms, seconds=ss) * sinal_s
                if restante_s.total_seconds() < 0: continue

                tms_individual = restante_s - restante_p
                if tms_individual.total_seconds() < 0 or tms_individual > timedelta(days=30): continue

                tma_por_mes[mes].append(restante_p.total_seconds())
                tms_por_mes[mes].append(tms_individual.total_seconds())

            except:
                continue

        # Distribuição de meses por quarter
        quarters = {
            'Q1': [1, 2, 3],
            'Q2': [4, 5, 6],
            'Q3': [7, 8, 9],
            'Q4': [10, 11, 12]
        }

        resultado = {}
        for q, meses in quarters.items():
            labels = [datetime(1900, m, 1).strftime('%b').capitalize() for m in meses]
            tma = []
            tms = []
            for m in meses:
                lista_tma = tma_por_mes.get(m, [])
                lista_tms = tms_por_mes.get(m, [])
                media_tma = round(np.mean(lista_tma)/60, 2) if lista_tma else 0
                media_tms = round(np.mean(lista_tms)/60, 2) if lista_tms else 0
                tma.append(media_tma)
                tms.append(media_tms)
            resultado[q] = {"labels": labels, "tma": tma, "tms": tms}

        return jsonify({"status": "success", "quarters": resultado})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@okrs_bp.route('/csatAcumulado', methods=['POST'])
def csat_acumulado():
    try:
        data = request.get_json()
        dias = int(data.get('dias', 365))
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

        # Cálculo acumulativo mês a mês
        meses_ordenados = sorted(respostas_por_mes.keys())
        labels, csat_mensal, csat_acumulado = [], [], []

        total_notas_acum = 0
        total_satisfatorias_acum = 0

        for key in meses_ordenados:
            notas = respostas_por_mes[key]
            total = len(notas)
            satisfatorias = sum(1 for n in notas if n >= 7)

            csat_mes = round((satisfatorias / total) * 100, 2) if total else 0
            csat_mensal.append(csat_mes)

            # Lógica acumulativa
            total_notas_acum += total
            total_satisfatorias_acum += satisfatorias

            csat_acum = round((total_satisfatorias_acum / total_notas_acum) * 100, 2) if total_notas_acum else 0
            csat_acumulado.append(csat_acum)

            mes_formatado = datetime.strptime(key, '%Y-%m').strftime('%b/%y').capitalize()
            labels.append(mes_formatado)

        return jsonify({
            "status": "success",
            "labels": labels,
            "csat_mensal": csat_mensal,
            "csat_acumulado": csat_acumulado
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@okrs_bp.route('/tmaTmsAcumulado', methods=['POST'])
def tma_tms_acumulado():
    try:
        data = request.get_json() or {}
        dias = int(data.get("dias", 365))
        data_limite = datetime.utcnow() - timedelta(days=dias)

        chamados_validos = db.session.query(Chamado).filter(
            Chamado.data_criacao >= data_limite,
            Chamado.data_criacao.isnot(None),
            Chamado.restante_p_atendimento.isnot(None),
            Chamado.restante_s_atendimento.isnot(None),
            Chamado.nome_status.ilike('%Resolvido%')
        ).all()

        tma_por_mes = defaultdict(list)
        tms_por_mes = defaultdict(list)

        for chamado in chamados_validos:
            try:
                ano, mes = chamado.data_criacao.year, chamado.data_criacao.month
                tempo_p = (chamado.restante_p_atendimento or "").strip()
                tempo_s = (chamado.restante_s_atendimento or "").strip()
                if not tempo_p or not tempo_s:
                    continue

                def parse_tempo(t):
                    sinal = -1 if t.startswith("-") else 1
                    partes = t.replace("-", "").split(":")
                    h, m, s = (list(map(int, partes)) + [0, 0, 0])[:3]
                    return timedelta(hours=h, minutes=m, seconds=s) * sinal

                restante_p = parse_tempo(tempo_p)
                restante_s = parse_tempo(tempo_s)

                # Ignora negativos
                if restante_p.total_seconds() < 0 or restante_s.total_seconds() < 0:
                    continue

                tms_individual = restante_s - restante_p
                if tms_individual.total_seconds() < 0 or tms_individual > timedelta(days=30):
                    continue

                # Guarda em segundos
                tma_por_mes[(ano, mes)].append(restante_p.total_seconds())
                tms_por_mes[(ano, mes)].append(tms_individual.total_seconds())

            except Exception:
                continue

        # Ordena os meses
        meses_ordenados = sorted(set(tma_por_mes.keys()) | set(tms_por_mes.keys()))

        labels = []
        tma_acumulado = []
        tms_acumulado = []

        # Acumuladores
        soma_tma = soma_tms = qtd_total = 0

        for ano, mes in meses_ordenados:
            tma_mes = tma_por_mes.get((ano, mes), [])
            tms_mes = tms_por_mes.get((ano, mes), [])

            qtd_mes = len(tma_mes)
            if qtd_mes == 0:
                continue

            media_tma_mes = np.mean(tma_mes)
            media_tms_mes = np.mean(tms_mes)

            soma_tma += sum(tma_mes)
            soma_tms += sum(tms_mes)
            qtd_total += qtd_mes

            # Média acumulada até o mês atual (em minutos)
            media_tma_acum = (soma_tma / qtd_total) / 60
            media_tms_acum = (soma_tms / qtd_total) / 60

            labels.append(datetime(ano, mes, 1).strftime('%b/%y'))
            tma_acumulado.append(round(media_tma_acum, 2))
            tms_acumulado.append(round(media_tms_acum, 2))

        return jsonify({
            "status": "success",
            "labels": labels,
            "tma_acumulado_min": tma_acumulado,
            "tms_acumulado_min": tms_acumulado
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@okrs_bp.route('/fcrAcumulado', methods=['POST'])
def fcr_acumulado():
    try:
        data = request.get_json() or {}
        dias = int(data.get('dias', 180)) 
        hoje = datetime.utcnow()
        data_inicio = hoje - timedelta(days=dias)

        # --- Coleta dados ---
        registros = RelatorioColaboradores.query.filter(
            RelatorioColaboradores.data_criacao >= data_inicio,
            RelatorioColaboradores.nome_status == 'Resolvido'
        ).all()

        chamados = Chamado.query.filter(
            Chamado.nome_status == 'Resolvido',
            Chamado.data_finalizacao != None,
            Chamado.data_finalizacao >= data_inicio,
            Chamado.data_finalizacao <= hoje
        ).all()

        # --- Agrupa por mês ---
        chamados_por_mes = defaultdict(list)
        fcr_por_mes = defaultdict(list)

        for chamado in chamados:
            key = chamado.data_finalizacao.strftime('%Y-%m')
            chamados_por_mes[key].append(chamado.cod_chamado)

        for reg in registros:
            if reg.first_call == 'S' and reg.cod_chamado:
                key = reg.data_criacao.strftime('%Y-%m')
                fcr_por_mes[key].append(reg.cod_chamado)

        # --- Ordena cronologicamente ---
        meses_ordenados = sorted(chamados_por_mes.keys())

        labels = []
        fcr_acumulado = []

        acumulado_total = 0
        acumulado_fcr = 0

        # --- Cálculo acumulativo ---
        for key in meses_ordenados:
            total = len(chamados_por_mes[key])
            fcr_mes = len(set(fcr_por_mes.get(key, [])))

            acumulado_total += total
            acumulado_fcr += fcr_mes

            pct_acumulado = round((acumulado_fcr / acumulado_total) * 100, 2) if acumulado_total else 0

            mes_formatado = datetime.strptime(key, '%Y-%m').strftime('%b/%y').capitalize()
            labels.append(mes_formatado)
            fcr_acumulado.append(pct_acumulado)

        return jsonify({
            "status": "success",
            "labels": labels,
            "fcr_acumulado": fcr_acumulado
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@okrs_bp.route('/slaOkrsAcumulado', methods=['POST'])
def sla_okrs_acumulado():
    try:
        data = request.get_json()
        dias = int(data.get('dias', 180))
        hoje = datetime.now()
        data_inicio = hoje - timedelta(days=dias)

        # Filtra os chamados válidos
        chamados = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.data_criacao >= data_inicio,
            Chamado.data_criacao <= hoje
        ).all()

        # Agrupar por mês
        chamados_por_mes = defaultdict(list)
        for chamado in chamados:
            key = chamado.data_criacao.strftime('%Y-%m') 
            chamados_por_mes[key].append(chamado)

        # Ordena cronologicamente
        meses_ordenados = sorted(chamados_por_mes.keys())

        # Listas de resposta
        labels = []
        sla_atendimento_acumulado = []
        sla_resolucao_acumulado = []

        # Variáveis acumulativas
        acumulado_total = 0
        acumulado_no_prazo_atendimento = 0
        acumulado_no_prazo_resolucao = 0

        for key in meses_ordenados:
            lista = chamados_por_mes[key]
            total = len(lista)
            no_prazo_atendimento = sum(1 for c in lista if c.sla_atendimento == 'N')
            no_prazo_resolucao = sum(1 for c in lista if c.sla_resolucao == 'N')

            # Soma acumulada
            acumulado_total += total
            acumulado_no_prazo_atendimento += no_prazo_atendimento
            acumulado_no_prazo_resolucao += no_prazo_resolucao

            # Calcula o SLA acumulado até o mês corrente
            pct_atendimento_acum = round((acumulado_no_prazo_atendimento / acumulado_total) * 100, 2) if acumulado_total else 0
            pct_resolucao_acum = round((acumulado_no_prazo_resolucao / acumulado_total) * 100, 2) if acumulado_total else 0

            # Formata rótulo do mês (Ex: "Jan/25")
            mes_formatado = datetime.strptime(key, '%Y-%m').strftime('%b/%y').capitalize()
            labels.append(mes_formatado)
            sla_atendimento_acumulado.append(pct_atendimento_acum)
            sla_resolucao_acumulado.append(pct_resolucao_acum)

        return jsonify({
            "status": "success",
            "labels": labels,
            "sla_atendimento_acumulado": sla_atendimento_acumulado,
            "sla_resolucao_acumulado": sla_resolucao_acumulado
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
