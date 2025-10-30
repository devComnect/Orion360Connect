from datetime import datetime, timedelta
from application.models import Chamado, db, PesquisaSatisfacao, RelatorioColaboradores, PerformanceColaboradores, Metas
from sqlalchemy import func, and_, or_, extract, text
import numpy as np
from collections import defaultdict
import pandas as pd
import re, os, io


def gerar_relatorio_sla(inicio_ano, fim_ano):
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
    atendimento_acumulado = []  # nova coluna acumulada
    resolucao_acumulado = []    # nova coluna acumulada

    acumulado_total = 0
    acumulado_no_prazo_atendimento = 0
    acumulado_no_prazo_resolucao = 0

    for mes in meses:
        lista = chamados_por_mes.get(mes, [])
        total = len(lista)

        no_prazo_atendimento = sum(1 for c in lista if c.sla_atendimento == 'N')
        no_prazo_resolucao = sum(1 for c in lista if c.sla_resolucao == 'N')

        pct_atendimento = round((no_prazo_atendimento / total) * 100, 2) if total else 0
        pct_resolucao = round((no_prazo_resolucao / total) * 100, 2) if total else 0

        # Atualiza acumulados
        acumulado_total += total
        acumulado_no_prazo_atendimento += no_prazo_atendimento
        acumulado_no_prazo_resolucao += no_prazo_resolucao

        pct_atendimento_acum = round((acumulado_no_prazo_atendimento / acumulado_total) * 100, 2) if acumulado_total else 0
        pct_resolucao_acum = round((acumulado_no_prazo_resolucao / acumulado_total) * 100, 2) if acumulado_total else 0

        labels.append(datetime.strptime(mes, '%Y-%m').strftime('%b/%Y'))
        atendimento_prazo.append(pct_atendimento)
        resolucao_prazo.append(pct_resolucao)
        atendimento_acumulado.append(pct_atendimento_acum)
        resolucao_acumulado.append(pct_resolucao_acum)

    # Cria DataFrame
    df = pd.DataFrame({
        "Mês": labels,
        "SLA Atendimento (%)": atendimento_prazo,
        "SLA Resolução (%)": resolucao_prazo,
        "SLA Atendimento Acumulado (%)": atendimento_acumulado,
        "SLA Resolução Acumulado (%)": resolucao_acumulado
    })

    # Calcula médias anuais
    media_atendimento = round(sum(atendimento_prazo) / len(atendimento_prazo), 2) if atendimento_prazo else 0
    media_resolucao = round(sum(resolucao_prazo) / len(resolucao_prazo), 2) if resolucao_prazo else 0
    media_atendimento_acum = round(atendimento_acumulado[-1], 2) if atendimento_acumulado else 0
    media_resolucao_acum = round(resolucao_acumulado[-1], 2) if resolucao_acumulado else 0

    df.loc[len(df)] = [
        "Média Anual",
        media_atendimento,
        media_resolucao,
        media_atendimento_acum,
        media_resolucao_acum
    ]

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
                ano, mes = chamado.data_criacao.year, chamado.data_criacao.month

                tempo_p = (chamado.restante_p_atendimento or "").strip()
                tempo_s = (chamado.restante_s_atendimento or "").strip()
                if not tempo_p or not tempo_s:
                    continue

                # Função para converter string em timedelta
                def parse_tempo(t):
                    sinal = -1 if t.startswith("-") else 1
                    partes = t.replace("-", "").split(":")
                    h, m, s = (list(map(int, partes)) + [0, 0, 0])[:3]
                    return timedelta(hours=h, minutes=m, seconds=s) * sinal

                restante_p = parse_tempo(tempo_p)
                restante_s = parse_tempo(tempo_s)

                if restante_p.total_seconds() < 0 or restante_s.total_seconds() < 0:
                    continue

                tms_individual = restante_s - restante_p
                if tms_individual.total_seconds() < 0 or tms_individual > timedelta(days=30):
                    continue

                tma_por_mes[(ano, mes)].append(restante_p.total_seconds())
                tms_por_mes[(ano, mes)].append(tms_individual.total_seconds())

            except:
                continue

        # Função auxiliar para formatar minutos
        def formatar_tempo(minutos):
            horas = int(minutos // 60)
            mins = int(round(minutos % 60))
            return f"{horas}h{mins:02d}min"

        meses_ordenados = sorted(set(tma_por_mes.keys()) | set(tms_por_mes.keys()))
        dados = []

        # Variáveis acumulativas
        soma_tma = soma_tms = qtd_total = 0

        for ano, mes in meses_ordenados:
            tma_lista = tma_por_mes.get((ano, mes), [])
            tms_lista = tms_por_mes.get((ano, mes), [])

            if not tma_lista or not tms_lista:
                continue

            media_tma_mes = np.mean(tma_lista)
            media_tms_mes = np.mean(tms_lista)
            qtd_mes = len(tma_lista)

            # Atualiza acumuladores
            soma_tma += sum(tma_lista)
            soma_tms += sum(tms_lista)
            qtd_total += qtd_mes

            media_tma_acum = soma_tma / qtd_total
            media_tms_acum = soma_tms / qtd_total

            mes_label = datetime(ano, mes, 1).strftime('%b/%y').capitalize()

            dados.append({
                "Mês": mes_label,
                "TMA médio": formatar_tempo(media_tma_mes / 60),
                "TMS médio": formatar_tempo(media_tms_mes / 60),
                "TMA Acumulado": formatar_tempo(media_tma_acum / 60),
                "TMS Acumulado": formatar_tempo(media_tms_acum / 60)
            })

        # Média anual
        if dados:
            media_final_tma = soma_tma / qtd_total
            media_final_tms = soma_tms / qtd_total
            dados.append({
                "Mês": "Média Anual",
                "TMA médio": formatar_tempo(np.mean([np.mean(tma_por_mes[m]) for m in meses_ordenados]) / 60),
                "TMS médio": formatar_tempo(np.mean([np.mean(tms_por_mes[m]) for m in meses_ordenados]) / 60),
                "TMA Acumulado": formatar_tempo(media_final_tma / 60),
                "TMS Acumulado": formatar_tempo(media_final_tms / 60)
            })

        df = pd.DataFrame(dados)
        return df, "TMA_TMS Anual"

    except Exception as e:
        print(f"Erro ao gerar relatório TMA/TMS: {e}")
        df_erro = pd.DataFrame([{"Erro": str(e)}])
        return df_erro, "TMA_TMS Anual"

def gerar_relatorio_fcr(inicio_ano, fim_ano):
    try:
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

        # Agrupa chamados resolvidos por mês
        for chamado in chamados:
            key = chamado.data_finalizacao.strftime('%Y-%m')
            chamados_por_mes[key].append(chamado.cod_chamado)

        # Agrupa FCRs por mês
        for reg in registros:
            if reg.first_call == 'S' and reg.cod_chamado:
                key = reg.data_criacao.strftime('%Y-%m')
                fcr_por_mes[key].append(reg.cod_chamado)

        # Calcula percentuais e acumulativo
        dados = []
        fcr_acumulado = []
        acumulado_total = 0
        acumulado_fcr = 0

        for key in sorted(chamados_por_mes.keys()):
            total_chamados = len(chamados_por_mes[key])
            total_fcr = len(set(fcr_por_mes.get(key, [])))
            percentual = round((total_fcr / total_chamados) * 100, 2) if total_chamados else 0

            # Atualiza acumulado
            acumulado_total += total_chamados
            acumulado_fcr += total_fcr
            percentual_acum = round((acumulado_fcr / acumulado_total) * 100, 2) if acumulado_total else 0

            mes_formatado = datetime.strptime(key, '%Y-%m').strftime('%b/%y').capitalize()
            dados.append({
                "Mês": mes_formatado,
                "FCR (%)": percentual,
                "FCR Acumulado (%)": percentual_acum
            })

        # Média anual
        if dados:
            media_anual = np.mean([d["FCR (%)"] for d in dados])
            media_acum = round((acumulado_fcr / acumulado_total) * 100, 2) if acumulado_total else 0
            dados.append({
                "Mês": "Média Anual",
                "FCR (%)": round(media_anual, 2),
                "FCR Acumulado (%)": media_acum
            })

        df = pd.DataFrame(dados)
        return df, "FCR Anual"

    except Exception as e:
        print(f"Erro ao gerar relatório FCR: {e}")
        df_erro = pd.DataFrame([{"Erro": str(e)}])
        return df_erro, "FCR Anual"

def gerar_relatorio_reabertura(inicio_ano, fim_ano):
    """Gera o DataFrame de reabertos por mês para exportação anual, incluindo acumulativo."""
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

    # Agrupa chamados e reabertos por mês
    for chamado in chamados:
        key = chamado.data_finalizacao.strftime('%Y-%m')
        chamados_por_mes[key].append(chamado.cod_chamado)

    for reg in registros:
        if reg.reaberto == 'Reaberto' and reg.cod_chamado:
            key = reg.data_criacao.strftime('%Y-%m')
            reabertos_por_mes[key].append(reg.cod_chamado)

    meses, total_chamados, reabertos, percentual, percentual_acumulado = [], [], [], [], []

    acumulado_total = 0
    acumulado_reabertos = 0

    for key in sorted(chamados_por_mes.keys()):
        total = len(chamados_por_mes[key])
        qtd_reabertos = len(set(reabertos_por_mes.get(key, [])))
        perc = round((qtd_reabertos / total) * 100, 2) if total else 0

        # Atualiza acumulativo
        acumulado_total += total
        acumulado_reabertos += qtd_reabertos
        perc_acum = round((acumulado_reabertos / acumulado_total) * 100, 2) if acumulado_total else 0

        meses.append(datetime.strptime(key, '%Y-%m').strftime('%b/%y').capitalize())
        total_chamados.append(total)
        reabertos.append(qtd_reabertos)
        percentual.append(perc)
        percentual_acumulado.append(perc_acum)

    media_final = round(sum(percentual) / len(percentual), 2) if percentual else 0
    media_acumulada = round((acumulado_reabertos / acumulado_total) * 100, 2) if acumulado_total else 0

    df = pd.DataFrame({
        "Mês": meses,
        "Total Chamados": total_chamados,
        "Reabertos": reabertos,
        "Percentual (%)": percentual,
        "Percentual Acumulado (%)": percentual_acumulado
    })

    df.loc[len(df)] = ["Média Anual", "", "", media_final, media_acumulada]

    return df, "Reabertos Anual"


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
    csat_acumulado_valores = []  # coluna acumulativa
    status_valores = []

    total_notas_acum = 0
    total_satisfatorias_acum = 0

    for mes in meses:
        notas = respostas_por_mes.get(mes, [])
        total = len(notas)
        satisfatorias = sum(1 for n in notas if n >= 7)

        # CSAT do mês
        csat_mes = round((satisfatorias / total) * 100, 2) if total else 0
        csat_valores.append(csat_mes)

        # CSAT acumulado
        total_notas_acum += total
        total_satisfatorias_acum += satisfatorias
        csat_acum = round((total_satisfatorias_acum / total_notas_acum) * 100, 2) if total_notas_acum else 0
        csat_acumulado_valores.append(csat_acum)

        # Status do mês
        if csat_mes >= 90:
            status = "Excelente"
        elif csat_mes >= 70:
            status = "Bom"
        elif csat_mes >= 50:
            status = "Regular"
        else:
            status = "Ruim"
        status_valores.append(status)

    df = pd.DataFrame({
        "Mês": [datetime.strptime(m, '%Y-%m').strftime('%b/%Y') for m in meses],
        "CSAT (%)": csat_valores,
        "CSAT Acumulado (%)": csat_acumulado_valores,  # adiciona coluna na planilha
        "Status": status_valores
    })

    media_anual = round(sum(csat_valores) / len(csat_valores), 2) if csat_valores else 0
    media_acumulada = round(csat_acumulado_valores[-1], 2) if csat_acumulado_valores else 0  # último acumulado
    if media_anual >= 90:
        status_media = "Excelente"
    elif media_anual >= 70:
        status_media = "Bom"
    elif media_anual >= 50:
        status_media = "Regular"
    else:
        status_media = "Ruim"

    df.loc[len(df)] = ["Média Anual", media_anual, media_acumulada, status_media]

    return df, "CSAT Anual"
