from datetime import datetime, timedelta, time, date
from flask import jsonify, request, render_template, session
from sqlalchemy import func, cast, Date, or_
from application.models import db, ChamadasDetalhes, DesempenhoAtendenteVyrtos, PerformanceColaboradores, PesquisaSatisfacao, RelatorioColaboradores, RegistroChamadas, EventosAtendentes


# MODELOS que você já tem no projeto
# from application.models import ChamadasDetalhes, EventosAtendentes, PerformanceColaboradores

# ======================
# HELPERS
# ======================
def _parse_duration_to_timedelta(val):
    """
    Converte vários formatos possíveis de 'duracao' para timedelta:
    - timedelta -> retorna direto
    - datetime/time -> usa hora/minuto/segundo como delta desde 00:00:00
    - int/float -> interpreta como segundos
    - str -> tenta vários formatos: "YYYY-%m-%d %H:%M:%S", "HH:MM:SS", "MM:SS" ou número em segundos
    - None -> timedelta(0)
    """
    if val is None:
        return timedelta()
    if isinstance(val, timedelta):
        return val
    if isinstance(val, datetime):
        return timedelta(hours=val.hour, minutes=val.minute, seconds=val.second)
    if isinstance(val, time):
        return timedelta(hours=val.hour, minutes=val.minute, seconds=val.second)
    if isinstance(val, (int, float)):
        return timedelta(seconds=int(val))
    if isinstance(val, str):
        s = val.strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%H:%M:%S", "%M:%S"):
            try:
                dt = datetime.strptime(s, fmt)
                return timedelta(hours=dt.hour, minutes=dt.minute, seconds=dt.second)
            except Exception:
                continue
        try:
            secs = float(s)
            return timedelta(seconds=int(secs))
        except Exception:
            return timedelta()
    return timedelta()

def _format_timedelta(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# ======================
# FUNÇÃO PRINCIPAL DE PERFORMANCE
# ======================
def calcular_performance_colaborador(nome: str, dias: int):
    hoje = datetime.now().date()
    data_inicial = hoje - timedelta(days=dias)

    # === CHAMADAS ATENDIDAS
    atendimentos_result = db.session.query(
        cast(ChamadasDetalhes.data, Date).label('dia'),
        func.count(ChamadasDetalhes.id)
    ).filter(
        ChamadasDetalhes.tipo == 'Atendida',
        ChamadasDetalhes.nomeAtendente.ilike(f"%{nome}%"),
        cast(ChamadasDetalhes.data, Date) >= data_inicial,
        cast(ChamadasDetalhes.data, Date) <= hoje,
        or_(
            ChamadasDetalhes.transferencia.is_(None),
            ChamadasDetalhes.transferencia == '-',
            ~ChamadasDetalhes.transferencia.ilike('%Ramal%')
        )
    ).group_by(
        cast(ChamadasDetalhes.data, Date)
    ).all()

    atendimentos_por_dia_map = {d: total for d, total in atendimentos_result}
    ch_atendidas = sum(atendimentos_por_dia_map.values())

    # === CHAMADAS NÃO ATENDIDAS
    nao_atendidas_result = db.session.query(
        func.count(EventosAtendentes.id)
    ).filter(
        EventosAtendentes.nome_atendente.ilike(f"%{nome}%"),
        EventosAtendentes.evento == 'Chamada N&atilde;o Atendida',
        EventosAtendentes.data >= data_inicial,
        EventosAtendentes.data <= hoje
    ).scalar() or 0

    # === PERFORMANCE GERAL
    registros = PerformanceColaboradores.query.filter(
        PerformanceColaboradores.name.ilike(f"%{nome}%"),
        PerformanceColaboradores.data >= data_inicial,
        PerformanceColaboradores.data <= hoje
    ).all()

    pausas_produtivas = 0
    pausas_improdutivas = 0
    pausas_detalhadas = []
    duracao_produtiva = timedelta()
    duracao_improdutiva = timedelta()

    # === PAUSAS DETALHADAS
    pausas_rows = db.session.query(
        EventosAtendentes.nome_pausa,
        EventosAtendentes.parametro,
        EventosAtendentes.duracao
    ).filter(
        EventosAtendentes.nome_atendente.ilike(f"%{nome}%"),
        EventosAtendentes.data >= data_inicial,
        EventosAtendentes.data <= hoje,
        EventosAtendentes.evento == 'Pausa',
        EventosAtendentes.nome_pausa != 'Refeicao'
    ).all()

    pausa_map = {}
    for row in pausas_rows:
        nome_pausa, parametro, duracao_raw = row
        delta = _parse_duration_to_timedelta(duracao_raw)

        key = (nome_pausa, str(parametro))
        entry = pausa_map.get(key)
        if not entry:
            entry = {"nome_pausa": nome_pausa, "parametro": parametro, "total": 0, "duracao": timedelta()}
            pausa_map[key] = entry

        entry["total"] += 1
        entry["duracao"] += delta

        if str(parametro) in ['3', '4']:
            duracao_produtiva += delta
            pausas_produtivas += 1
        else:
            duracao_improdutiva += delta
            pausas_improdutivas += 1

    for entry in pausa_map.values():
        pausas_detalhadas.append({
            "nome_pausa": entry["nome_pausa"],
            "parametro": entry["parametro"],
            "total": entry["total"],
            "duracao": _format_timedelta(entry["duracao"])
        })

    acumulado = {
        "tempo_online": 0,
        "tempo_livre": 0,
        "tempo_servico": 0,
        "pimprod_refeicao": 0,
        "tempo_minatend": None,
        "tempo_medatend": [],
        "tempo_maxatend": None
    }

    for r in registros:
        acumulado["tempo_online"] += r.tempo_online
        acumulado["tempo_livre"] += r.tempo_livre
        acumulado["tempo_servico"] += r.tempo_servico
        acumulado["pimprod_refeicao"] += r.pimprod_refeicao

        if r.tempo_minatend is not None:
            acumulado["tempo_minatend"] = r.tempo_minatend if acumulado["tempo_minatend"] is None else min(acumulado["tempo_minatend"], r.tempo_minatend)
        if r.tempo_maxatend is not None:
            acumulado["tempo_maxatend"] = r.tempo_maxatend if acumulado["tempo_maxatend"] is None else max(acumulado["tempo_maxatend"], r.tempo_maxatend)
        if r.tempo_medatend is not None:
            acumulado["tempo_medatend"].append(r.tempo_medatend)

    media_geral = (
        sum(acumulado["tempo_medatend"]) / len(acumulado["tempo_medatend"])
        if acumulado["tempo_medatend"] else 0
    )

    return {
        "periodo": dias,
        "ch_atendidas": ch_atendidas,
        "ch_naoatendidas": nao_atendidas_result,
        "tempo_online": acumulado["tempo_online"],
        "tempo_livre": acumulado["tempo_livre"],
        "tempo_servico": acumulado["tempo_servico"],
        "pimprod_refeicao": acumulado["pimprod_refeicao"],
        "tempo_minatend": acumulado["tempo_minatend"] or 0,
        "tempo_medatend": round(media_geral, 2),
        "tempo_maxatend": acumulado["tempo_maxatend"] or 0,
        "pausas_produtivas": pausas_produtivas,
        "pausas_improdutivas": pausas_improdutivas,
        "pausas_detalhadas": pausas_detalhadas,
        "duracao_produtiva": _format_timedelta(duracao_produtiva),
        "duracao_improdutiva": _format_timedelta(duracao_improdutiva)
    }