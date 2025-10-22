from flask import Blueprint, jsonify, render_template, request, url_for, send_file
import requests
from modules.insights.utils import formatar_tempo
from datetime import datetime, timedelta
from application.models import Chamado, db, PesquisaSatisfacao, RelatorioColaboradores, PerformanceColaboradores, Metas
from collections import Counter
from sqlalchemy import func, and_, or_, extract, text
import numpy as np
from collections import defaultdict
import pandas as pd
import re, os, io


def gerar_relatorio_sla(inicio_ano, fim_ano):
    """
    Gera o relatório anual de SLA (Atendimento e Resolução)
    baseado nos chamados entre as datas fornecidas.
    """
    # Busca todos os chamados do período
    chamados = Chamado.query.filter(
        Chamado.nome_status != 'Cancelado',
        Chamado.data_criacao >= inicio_ano,
        Chamado.data_criacao <= fim_ano
    ).all()

    # Agrupa chamados por mês
    chamados_por_mes = defaultdict(list)
    for chamado in chamados:
        chave_mes = chamado.data_criacao.strftime('%Y-%m')
        chamados_por_mes[chave_mes].append(chamado)

    meses = pd.date_range(start=inicio_ano, end=fim_ano, freq='MS').strftime('%Y-%m')
    labels = []
    atendimento_prazo = []
    resolucao_prazo = []

    for mes in meses:
        lista = chamados_por_mes.get(mes, [])
        total = len(lista)

        no_prazo_atendimento = sum(1 for c in lista if c.sla_atendimento == 'N')
        no_prazo_resolucao = sum(1 for c in lista if c.sla_resolucao == 'N')

        pct_atendimento = round((no_prazo_atendimento / total) * 100, 2) if total else 0
        pct_resolucao = round((no_prazo_resolucao / total) * 100, 2) if total else 0

        labels.append(datetime.strptime(mes, '%Y-%m').strftime('%b/%Y'))
        atendimento_prazo.append(pct_atendimento)
        resolucao_prazo.append(pct_resolucao)

    # Cria DataFrame
    df = pd.DataFrame({
        "Mês": labels,
        "SLA Atendimento (%)": atendimento_prazo,
        "SLA Resolução (%)": resolucao_prazo
    })

    # Calcula médias anuais
    media_atendimento = round(sum(atendimento_prazo) / len(atendimento_prazo), 2) if atendimento_prazo else 0
    media_resolucao = round(sum(resolucao_prazo) / len(resolucao_prazo), 2) if resolucao_prazo else 0

    df.loc[len(df)] = ["Média Anual", media_atendimento, media_resolucao]

    return df, "SLA Anual"

def gerar_relatorio_tma_tms(inicio_ano, fim_ano):
    try:
        chamados_validos = db.session.query(Chamado).filter(
            Chamado.data_criacao >= inicio_ano,
            Chamado.data_criacao <= fim_ano,
            Chamado.data_criacao.isnot(None),
            Chamado.restante_p_atendimento.isnot(None),
            Chamado.restante_s_atendimento.isnot(None),
            Chamado.nome_status.ilike('%Resolvido%')
        ).all()

        tma_por_mes = defaultdict(list)
        tms_por_mes = defaultdict(list)

        for chamado in chamados_validos:
            try:
                ano = chamado.data_criacao.year
                mes = chamado.data_criacao.month

                tempo_p = (chamado.restante_p_atendimento or "").strip()
                tempo_s = (chamado.restante_s_atendimento or "").strip()
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

                if restante_p.total_seconds() < 0 or restante_s.total_seconds() < 0:
                    continue

                tms_individual = restante_s - restante_p
                if tms_individual.total_seconds() < 0 or tms_individual > timedelta(days=30):
                    continue

                # Guarda valores em segundos
                tma_por_mes[(ano, mes)].append(restante_p.total_seconds())
                tms_por_mes[(ano, mes)].append(tms_individual.total_seconds())

            except:
                continue

        # Função auxiliar para converter minutos em formato h:mm
        def formatar_tempo(minutos):
            horas = int(minutos // 60)
            mins = int(round(minutos % 60))
            return f"{horas}h{mins:02d}min"

        # Monta DataFrame
        meses_ordenados = sorted(tma_por_mes.keys())
        dados = []

        todas_tma = []
        todas_tms = []

        for ano, mes in meses_ordenados:
            tma_lista = tma_por_mes.get((ano, mes), [])
            tms_lista = tms_por_mes.get((ano, mes), [])

            if not tma_lista or not tms_lista:
                continue

            media_tma = np.mean(tma_lista) / 60  # minutos
            media_tms = np.mean(tms_lista) / 60  # minutos
            mes_label = datetime(ano, mes, 1).strftime('%b/%y').capitalize()

            todas_tma.append(media_tma)
            todas_tms.append(media_tms)

            dados.append({
                "Mês": mes_label,
                "TMA médio": formatar_tempo(media_tma),
                "TMS médio": formatar_tempo(media_tms)
            })

        # --- Média Final ---
        if todas_tma and todas_tms:
            media_final_tma = np.mean(todas_tma)
            media_final_tms = np.mean(todas_tms)
            dados.append({
                "Mês": "Média Anual",
                "TMA médio": formatar_tempo(media_final_tma),
                "TMS médio": formatar_tempo(media_final_tms)
            })

        df = pd.DataFrame(dados)
        return df, "TMA_TMS"

    except Exception as e:
        print(f"Erro ao gerar relatório TMA/TMS: {e}")
        df_erro = pd.DataFrame([{"Erro": str(e)}])
        return df_erro, "TMA_TMS"

def gerar_relatorio_fcr(inicio_ano, fim_ano):
    try:
        # --- Busca dados dos relatórios de colaboradores e chamados resolvidos ---
        registros = RelatorioColaboradores.query.filter(
            RelatorioColaboradores.data_criacao >= inicio_ano,
            RelatorioColaboradores.data_criacao <= fim_ano,
            RelatorioColaboradores.nome_status == 'Resolvido'
        ).all()

        chamados = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.nome_status == 'Resolvido',
            Chamado.data_finalizacao != None,
            Chamado.data_finalizacao >= inicio_ano,
            Chamado.data_finalizacao <= fim_ano
        ).all()

        chamados_por_mes = defaultdict(list)
        fcr_por_mes = defaultdict(list)

        # --- Agrupar chamados resolvidos por mês ---
        for chamado in chamados:
            key = chamado.data_finalizacao.strftime('%Y-%m')
            chamados_por_mes[key].append(chamado.cod_chamado)

        # --- Agrupar FCRs (primeira chamada resolvida) por mês ---
        for reg in registros:
            if reg.first_call == 'S' and reg.cod_chamado:
                key = reg.data_criacao.strftime('%Y-%m')
                fcr_por_mes[key].append(reg.cod_chamado)

        # --- Calcular percentuais ---
        dados = []
        fcr_mensal = []

        for key in sorted(chamados_por_mes.keys()):
            total_chamados = len(chamados_por_mes[key])
            total_fcr = len(set(fcr_por_mes.get(key, [])))
            percentual = round((total_fcr / total_chamados) * 100, 2) if total_chamados else 0

            mes_formatado = datetime.strptime(key, '%Y-%m').strftime('%b/%y').capitalize()
            fcr_mensal.append(percentual)

            dados.append({
                "Mês": mes_formatado,
                "FCR (%)": percentual
            })

        # --- Média Anual ---
        if fcr_mensal:
            media_anual = np.mean(fcr_mensal)
            dados.append({
                "Mês": "Média Anual",
                "FCR (%)": round(media_anual, 2)
            })

        df = pd.DataFrame(dados)
        return df, "FCR"

    except Exception as e:
        print(f"Erro ao gerar relatório FCR: {e}")
        df_erro = pd.DataFrame([{"Erro": str(e)}])
        return df_erro, "FCR"

def gerar_relatorio_reabertura(inicio_ano, fim_ano):
    """Gera o DataFrame de reabertos por mês para exportação anual."""
    chamados = Chamado.query.filter(
        Chamado.nome_status == 'Resolvido',
        Chamado.nome_status != 'Cancelado',
        Chamado.data_finalizacao != None,
        Chamado.data_finalizacao >= inicio_ano,
        Chamado.data_finalizacao <= fim_ano
    ).all()

    registros = RelatorioColaboradores.query.filter(
        func.date(RelatorioColaboradores.data_criacao) >= inicio_ano,
        func.date(RelatorioColaboradores.data_criacao) <= fim_ano
    ).all()

    chamados_por_mes = defaultdict(list)
    reabertos_por_mes = defaultdict(list)

    for chamado in chamados:
        key = chamado.data_finalizacao.strftime('%Y-%m')
        chamados_por_mes[key].append(chamado.cod_chamado)

    for reg in registros:
        if reg.reaberto == 'Reaberto' and reg.cod_chamado:
            key = reg.data_criacao.strftime('%Y-%m')
            reabertos_por_mes[key].append(reg.cod_chamado)

    meses, total_chamados, reabertos, percentual = [], [], [], []

    for key in sorted(chamados_por_mes.keys()):
        total = len(chamados_por_mes[key])
        qtd_reabertos = len(set(reabertos_por_mes.get(key, [])))
        perc = round((qtd_reabertos / total) * 100, 2) if total else 0

        meses.append(datetime.strptime(key, '%Y-%m').strftime('%b/%y').capitalize())
        total_chamados.append(total)
        reabertos.append(qtd_reabertos)
        percentual.append(perc)

    media_final = round(sum(percentual) / len(percentual), 2) if percentual else 0

    df = pd.DataFrame({
        "Mês": meses,
        "Total Chamados": total_chamados,
        "Reabertos": reabertos,
        "Percentual (%)": percentual
    })

    df.loc[len(df)] = ["Média Anual", "", "", media_final]

    return df, "Reabertos"



def gerar_relatorio_csat(inicio_ano, fim_ano):
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
        PesquisaSatisfacao.data_resposta >= inicio_ano,
        PesquisaSatisfacao.data_resposta <= fim_ano,
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

    meses = pd.date_range(start=inicio_ano, end=fim_ano, freq='MS').strftime('%Y-%m')
    csat_valores = []
    status_valores = []

    for mes in meses:
        notas = respostas_por_mes.get(mes, [])
        total = len(notas)
        satisfatorias = sum(1 for n in notas if n >= 7)
        csat = round((satisfatorias / total) * 100, 2) if total else 0
        csat_valores.append(csat)

        if csat >= 90:
            status = "Excelente"
        elif csat >= 70:
            status = "Bom"
        elif csat >= 50:
            status = "Regular"
        else:
            status = "Ruim"
        status_valores.append(status)

    df = pd.DataFrame({
        "Mês": [datetime.strptime(m, '%Y-%m').strftime('%b/%Y') for m in meses],
        "CSAT (%)": csat_valores,
        "Status": status_valores
    })

    media_anual = round(sum(csat_valores) / len(csat_valores), 2) if csat_valores else 0
    if media_anual >= 90:
        status_media = "Excelente"
    elif media_anual >= 70:
        status_media = "Bom"
    elif media_anual >= 50:
        status_media = "Regular"
    else:
        status_media = "Ruim"

    df.loc[len(df)] = ["Média Anual", media_anual, status_media]

    return df, "CSAT Anual"