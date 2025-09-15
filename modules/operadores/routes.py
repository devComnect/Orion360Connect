from flask import Blueprint, jsonify, request, render_template, url_for, session
import modules.tasks.utils as utils
from application.models import db, ChamadasDetalhes, DesempenhoAtendenteVyrtos, PerformanceColaboradores, PesquisaSatisfacao, RelatorioColaboradores, RegistroChamadas, EventosAtendentes
from modules.auth.utils import authenticate, authenticate_relatorio
from application.models import Chamado
from settings.endpoints import CREDENTIALS
from datetime import datetime, timedelta, date, time
from sqlalchemy import func, cast, Date, and_, or_


operadores_bp = Blueprint('operadores_bp', __name__, url_prefix='/operadores')


@operadores_bp.route('/performanceColaboradoresRender', methods=['POST'])
def performance_colaboradores_render():
    session.pop('dados', None)
    session.pop('nome', None)
    data = request.get_json()
    nome = data.get('nome')

    if not nome:
        return jsonify({"status": "error", "message": "Nome do operador não fornecido"}), 400

    ontem = date.today() - timedelta(days=1)
    hoje = datetime.today()


    registros = PerformanceColaboradores.query.filter(
        PerformanceColaboradores.name == nome,
        PerformanceColaboradores.data == hoje.date()
    )

    acumulado = {
        "ch_atendidas": 0,
        "ch_naoatendidas": 0,
        "tempo_online": 0,
        "tempo_livre": 0,
        "tempo_servico": 0,
        "pimprod_refeicao": 0,
        "tempo_minatend": None,
        "tempo_medatend": [],
        "tempo_maxatend": None
    }

    for item in registros:
        acumulado["ch_atendidas"] = item.ch_atendidas
        acumulado["ch_naoatendidas"] += item.ch_naoatendidas
        acumulado["tempo_online"] += item.tempo_online
        acumulado["tempo_livre"] += item.tempo_livre
        acumulado["tempo_servico"] += item.tempo_servico
        acumulado["pimprod_refeicao"] += item.pimprod_refeicao

        if item.tempo_minatend is not None:
            acumulado["tempo_minatend"] = (
                item.tempo_minatend
                if acumulado["tempo_minatend"] is None
                else min(acumulado["tempo_minatend"], item.tempo_minatend)
            )

        if item.tempo_maxatend is not None:
            acumulado["tempo_maxatend"] = (
                item.tempo_maxatend
                if acumulado["tempo_maxatend"] is None
                else max(acumulado["tempo_maxatend"], item.tempo_maxatend)
            )

        if item.tempo_medatend is not None:
            acumulado["tempo_medatend"].append(item.tempo_medatend)

    media_geral = (
        sum(acumulado["tempo_medatend"]) / len(acumulado["tempo_medatend"])
        if acumulado["tempo_medatend"] else 0
    )

    dados = {
        "ch_atendidas": acumulado["ch_atendidas"],
        "ch_naoatendidas": acumulado["ch_naoatendidas"],
        "tempo_online": acumulado["tempo_online"],
        "tempo_livre": acumulado["tempo_livre"],
        "tempo_servico": acumulado["tempo_servico"],
        "pimprod_refeicao": acumulado["pimprod_refeicao"],
        "tempo_minatend": acumulado["tempo_minatend"] or 0,
        "tempo_medatend": round(media_geral, 2),
        "tempo_maxatend": acumulado["tempo_maxatend"] or 0
    }

    session['nome'] = nome
    session['dados'] = dados

    return jsonify({"redirect_url": url_for('operadores_bp.render_operadores')})

@operadores_bp.route('/colaboradores', methods=['GET'])
def render_operadores():
    nome = session.get('nome')
    dados = session.get('dados')

    if not nome or not dados:
        return "Dados não encontrados na sessão", 400

    return render_template('colaboradores.html', nome=nome, dados=dados)

def _parse_duration_to_timedelta(val):
    """
    Converte vários formatos possíveis de 'duracao' para timedelta:
    - timedelta -> retorna direto
    - datetime/time -> usa hora/minuto/segundo como delta desde 00:00:00
    - int/float -> interpreta como segundos
    - str -> tenta vários formatos: "YYYY-%m-%d %H:%M:%S", "HH:MM:SS", "MM:SS" ou número em segundos
    - None/indeterminado -> timedelta(0)
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
        # tenta formatos conhecidos
        for fmt in ("%Y-%m-%d %H:%M:%S", "%H:%M:%S", "%M:%S"):
            try:
                dt = datetime.strptime(s, fmt)
                return timedelta(hours=dt.hour, minutes=dt.minute, seconds=dt.second)
            except Exception:
                continue
        # tenta interpretar como número de segundos
        try:
            secs = float(s)
            return timedelta(seconds=int(secs))
        except Exception:
            return timedelta()
    # fallback
    return timedelta()

def _format_timedelta(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

@operadores_bp.route('/performanceColaboradores', methods=['POST'])
def get_performance_colaboradores():
    data = request.get_json()
    nome = data.get('nome', '').strip().title()
    dias_str = str(data.get('dias'))

    hoje = datetime.now().date()
    try:
        dias = int(dias_str)
    except ValueError:
        return jsonify({"status": "error", "message": "O valor de 'dias' deve ser um número inteiro"}), 400

    data_inicial = hoje - timedelta(days=dias)

    # === CONTAGEM DE CHAMADAS ATENDIDAS
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

    # === CONTAGEM DE CHAMADAS NÃO ATENDIDAS
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

    # acumuladores
    pausas_produtivas = 0
    pausas_improdutivas = 0
    pausas_detalhadas = []

    duracao_produtiva = timedelta()
    duracao_improdutiva = timedelta()

    # === BUSCA PAUSAS (traz todos os registros; agregamos no Python)
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

    # agrupa por (nome_pausa, parametro)
    pausa_map = {}  # key -> {'nome_pausa', 'parametro', 'total', 'duracao' (timedelta)}
    for row in pausas_rows:
        # a ordem retornada segue a query: nome_pausa, parametro, duracao
        nome_pausa, parametro, duracao_raw = row
        delta = _parse_duration_to_timedelta(duracao_raw)

        key = (nome_pausa, str(parametro))
        entry = pausa_map.get(key)
        if not entry:
            entry = {
                "nome_pausa": nome_pausa,
                "parametro": parametro,
                "total": 0,
                "duracao": timedelta()
            }
            pausa_map[key] = entry

        entry["total"] += 1
        entry["duracao"] += delta

        # contabiliza produtiva/improdutiva global
        if str(parametro) in ['3', '4']:
            duracao_produtiva += delta
            pausas_produtivas += 1
        else:
            duracao_improdutiva += delta
            pausas_improdutivas += 1

    # monta lista detalhada final
    for entry in pausa_map.values():
        pausas_detalhadas.append({
            "nome_pausa": entry["nome_pausa"],
            "parametro": entry["parametro"],
            "total": entry["total"],
            "duracao": _format_timedelta(entry["duracao"])
        })

    # === consolida demais métricas
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

    dados = {
        "periodo": dias_str,
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

    return jsonify({"status": "success", "dados": dados})

@operadores_bp.route('/ChamadosSuporte/ticketsOperador', methods=['POST'])
def chamados_por_operador_periodo():
    try:
        data = request.json
        nome_operador = data.get("nome")
        dias = int(data.get("dias"))

        if not nome_operador:
            return jsonify({"status": "error", "message": "Nome do operador não fornecido."}), 400

        hoje = datetime.now().date()

        if dias == 1:
            data_inicio = hoje  # hoje
            data_fim = hoje
        else:
            data_inicio = hoje - timedelta(days=dias - 1)  # últimos N dias incluindo hoje
            data_fim = hoje

        chamados = db.session.query(
            Chamado.cod_chamado,
            Chamado.cod_solicitacao,
            Chamado.data_criacao,
            Chamado.data_finalizacao,
            Chamado.nome_grupo,
            Chamado.nome_status
        ).filter(
            cast(Chamado.data_criacao, Date) >= data_inicio,
            cast(Chamado.data_criacao, Date) <= data_fim,
            Chamado.operador == nome_operador
        ).all()

        lista_chamados = [{
            "cod_chamado": c.cod_chamado,
            "cod_solicitacao": c.cod_solicitacao,
            "data_criacao": c.data_criacao.strftime("%Y-%m-%d %H:%M:%S") if c.data_criacao else None,
            "data_finalizacao": c.data_finalizacao.strftime("%Y-%m-%d %H:%M:%S") if c.data_finalizacao else None,
            "nome_grupo": c.nome_grupo,
            "nome_status": c.nome_status
        } for c in chamados]

        return jsonify({
            "status": "success",
            "total_chamados": len(lista_chamados),
            "data_referencia": f"{data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}",
            "chamados": lista_chamados
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@operadores_bp.route('/ChamadosSuporte/ticketsTelefoneVsAtendidas', methods=['POST'])
def chamados_telefone_vs_atendidas():
    try:
        data = request.get_json()
        nome_operador = data.get("nome", "").strip().title()
        dias_str = str(data.get("dias", "1"))

        if not nome_operador:
            return jsonify({'status': 'error', 'message': 'Nome do operador não fornecido'}), 400

        

        # Trata o número de dias informado
        try:
            dias = int(dias_str)
        except ValueError:
            return jsonify({"status": "error", "message": "O valor de 'dias' deve ser um número inteiro"}), 400

        hoje = datetime.now().date()
        data_inicial = hoje - timedelta(days=dias)

        lista_dias = [
            data_inicial + timedelta(days=i)
            for i in range((hoje - data_inicial).days + 1)
        ]
        labels = [dia.strftime('%d/%m') for dia in lista_dias]

        # === TICKETS (com filtro para remover cancelados)
        chamados_result = db.session.query(
            func.date(Chamado.data_criacao).label('dia'),
            func.count(Chamado.id)
        ).filter(
            Chamado.cod_solicitacao == '000004',
            Chamado.operador == nome_operador,
            func.date(Chamado.data_criacao).in_(lista_dias)
        ).group_by(
            func.date(Chamado.data_criacao)
        ).all()

        chamados_por_dia = {dia: total for dia, total in chamados_result}
        dados_chamados = [chamados_por_dia.get(dia, 0) for dia in lista_dias]

        # === LIGAÇÕES (Atendidas e que não foram transferidas para Ramal)
        atendimentos_result = db.session.query(
            cast(ChamadasDetalhes.data, Date).label('dia'),
            func.count(ChamadasDetalhes.id)
        ).filter(
            ChamadasDetalhes.tipo == 'Atendida',
            ChamadasDetalhes.nomeAtendente.ilike(f"%{nome_operador}%"),
            cast(ChamadasDetalhes.data, Date).in_(lista_dias),
            or_(
                ChamadasDetalhes.transferencia.is_(None),
                ChamadasDetalhes.transferencia == '-',
                ~ChamadasDetalhes.transferencia.ilike('%Ramal%')
            )
        ).group_by(
            cast(ChamadasDetalhes.data, Date)
        ).all()

        atendimentos_por_dia_map = {data: total for data, total in atendimentos_result}
        atendimentos_por_dia = [atendimentos_por_dia_map.get(dia, 0) for dia in lista_dias]

        # === TOTALIZAÇÃO E DIFERENÇA
        total_tickets = sum(dados_chamados)
        total_ligacoes = sum(atendimentos_por_dia)
        diferenca = total_tickets - total_ligacoes

        return jsonify({
            'status': 'success',
            'data': {
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Tickets',
                        'data': dados_chamados,
                        'backgroundColor': 'rgba(255, 99, 132, 0.5)',
                        'borderColor': 'rgba(255, 99, 132, 1)',
                        'fill': False,
                        'tension': 0.3
                    },
                    {
                        'label': 'Ligações',
                        'data': atendimentos_por_dia,
                        'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                        'borderColor': 'rgba(54, 162, 235, 1)',
                        'fill': False,
                        'tension': 0.3
                    }
                ],
                'resumo': {
                    'total_tickets': total_tickets,
                    'total_ligacoes': total_ligacoes,
                    'diferenca': diferenca
                }
            }
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@operadores_bp.route('/GetSlaOperador', methods=['POST'])
def get_sla_operador():
    data = request.get_json()
    nome = data.get('nome')

    dias = int(data.get('dias', 1))

    data_inicio = datetime.now() - timedelta(days=dias)

    # Filtro com operador, período e grupo de suporte
    chamados = Chamado.query.filter(
        #Chamado.nome_grupo.ilike('%SUPORTE%'),
        Chamado.nome_status != 'Cancelado',
        Chamado.operador == nome,
        Chamado.data_criacao >= data_inicio
    ).all()

    # Filtra apenas os expirados
    chamados_expirados = [
        c for c in chamados if c.sla_atendimento == 'S' or c.sla_resolucao == 'S'
    ]

    expirados_atendimento = sum(1 for c in chamados if c.sla_atendimento == 'S')
    expirados_resolucao = sum(1 for c in chamados if c.sla_resolucao == 'S')
    


    return jsonify({
        "chamados": [c.to_dict() for c in chamados_expirados],
        "expirados_atendimento": expirados_atendimento,
        "expirados_resolucao": expirados_resolucao,
        "codigos_atendimento": [c.cod_chamado for c in chamados_expirados if c.sla_atendimento == 'S'],
        "codigos_resolucao": [c.cod_chamado for c in chamados_expirados if c.sla_resolucao == 'S']
    })

@operadores_bp.route('/pSatisfacaoOperador', methods=['POST'])
def listar_p_satisfacao():
    data = request.get_json()
    dias = int(data.get('dias'))
    nome = data.get('nome')

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

    # Busca alternativa + referência do chamado
    alternativas_brutas = db.session.query(
        PesquisaSatisfacao.alternativa,
        PesquisaSatisfacao.referencia_chamado
    ).filter(
        and_(
            PesquisaSatisfacao.data_resposta >= data_limite,
            PesquisaSatisfacao.alternativa.isnot(None),
            func.length(PesquisaSatisfacao.alternativa) > 0,
            PesquisaSatisfacao.operador.ilike(f"{nome}%")
        )
    ).all()

    # Usamos dict para garantir unicidade por referência
    respostas_unicas = {}

    for alternativa, referencia in alternativas_brutas:
        if referencia in respostas_unicas:
            continue  # ignora duplicados
        valor = alternativa.strip()
        numero = None
        if valor.isdigit():
            n = int(valor)
            if 0 <= n <= 10:
                numero = n
        elif valor in CSAT_MAP:
            numero = CSAT_MAP[valor]

        if numero is not None:
            respostas_unicas[referencia] = numero

    total_respondidas = len(respostas_unicas)
    respostas_satisfatorias = sum(1 for nota in respostas_unicas.values() if nota >= 7)
    csat = round((respostas_satisfatorias / total_respondidas) * 100, 2) if total_respondidas else 0

    # Apenas referências satisfatórias
    referencias_satisfatorias = [ref for ref, nota in respostas_unicas.items() if nota >= 7]

    return jsonify({
        "status": "success",
        "total_respondidas": total_respondidas,
        "respostas_satisfatorias": respostas_satisfatorias,
        "csat": csat,
        "referencia_chamados": list(respostas_unicas.keys()),
        "referencias_satisfatorias": referencias_satisfatorias
    })

@operadores_bp.route('/performanceColaboradoresRender/n2', methods=['POST'])
def performance_colaboradores_render_n2():
    session.pop('dados', None)
    session.pop('nome', None)

    data = request.get_json()
    nome = data.get('nome')

    session['nome'] = nome

    return jsonify({"redirect_url": url_for('operadores_bp.render_operadores_n2')})

@operadores_bp.route('/getChamadosAbertos', methods=['POST'])
def get_chamados_abertos():
    try:
        data = request.get_json()
        nome = data.get('nome')
        dias = int(data.get('dias', 1))  # padrão 1 dia

        if not nome:
            return jsonify({"status": "error", "message": "Nome do operador não fornecido."}), 400

        hoje = datetime.now().date()

        # Se 'dias' for 1, traz chamados abertos independentemente da data
        if dias == 1:
            chamados = Chamado.query.filter(
                Chamado.nome_status.notin_(['Cancelado', 'Resolvido']),
                Chamado.operador == nome
            ).all()

        else:
            data_inicio = hoje - timedelta(days=dias - 1)
            data_fim = hoje

            inicio = datetime.combine(data_inicio, datetime.min.time())
            fim = datetime.combine(data_fim, datetime.max.time())

            chamados = Chamado.query.filter(
                Chamado.nome_status.notin_(['Cancelado', 'Resolvido']),
                Chamado.data_criacao >= inicio,
                Chamado.data_criacao <= fim,
                Chamado.operador == nome
            ).all()

        total_chamados = len(chamados)
        codigos = [c.cod_chamado for c in chamados]

        return jsonify({
            "status": "success",
            "total_chamados": total_chamados,
            "cod_chamados": codigos
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@operadores_bp.route('/tma_tms/colaboradores', methods=['POST'])
def tma_e_tms_colaboradores():
    try:
        data = request.get_json()
        dias = int(data.get("dias", 1))
        nome = data.get("nome", "").strip()

        data_limite = datetime.utcnow() - timedelta(days=dias)

        query = db.session.query(Chamado).filter(
            Chamado.data_criacao >= data_limite,
            Chamado.data_criacao.isnot(None),
            Chamado.restante_p_atendimento.isnot(None),
            Chamado.restante_s_atendimento.isnot(None),
            Chamado.nome_status.ilike('%Resolvido%'), 
            Chamado.operador == nome
        )

        chamados_validos = query.all()

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

        def zscore_clip(values, lower=-3, upper=3):
            media = np.mean(values)
            std = np.std(values)
            if std == 0:
                return values
            zscores = (values - media) / std
            zscores_clipped = np.clip(zscores, lower, upper)
            return media + zscores_clipped * std

        tma_array = np.array(tma_list)
        tms_array = np.array(tms_list)

        tma_normalizado = zscore_clip(tma_array)
        tms_normalizado = zscore_clip(tms_array)

        media_tma = np.mean(tma_normalizado) / 60
        mediana_tma = np.median(tma_normalizado) / 60
        media_tms = np.mean(tms_normalizado) / 60
        mediana_tms = np.median(tms_normalizado) / 60

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

@operadores_bp.route('/slaColaboradores', methods=['POST'])
def sla_colaboradores():
    try:
        data = request.get_json()
        dias = int(data.get('dias', 1))
        nome = data.get('nome', '').strip().lower()

        hoje = datetime.now()
        data_inicio = hoje - timedelta(days=dias)

        # Consulta base
        query = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.data_criacao >= datetime.combine(data_inicio.date(), datetime.min.time()),
            Chamado.data_criacao <= datetime.combine(hoje.date(), datetime.max.time())
        )

        # Aplica filtro de nome, se fornecido
        if nome:
            query = query.filter(Chamado.operador.ilike(f"%{nome}%"))  # 👈 filtro aplicado

        chamados = query.all()

        expirados_atendimento = sum(1 for c in chamados if c.sla_atendimento == 'S')
        expirados_resolucao = sum(1 for c in chamados if c.sla_resolucao == 'S')
        chamados_atendimento_prazo = sum(1 for c in chamados if c.sla_atendimento == 'N')
        chamados_finalizado_prazo = sum(1 for c in chamados if c.sla_resolucao == 'N')

        chamados_expirados = [
            c for c in chamados if c.sla_atendimento == 'S' or c.sla_resolucao == 'S'
        ]

        total_chamados = len(chamados)

        percentual_atendimento = round((expirados_atendimento / total_chamados) * 100, 2) if total_chamados else 0
        percentual_resolucao = round((expirados_resolucao / total_chamados) * 100, 2) if total_chamados else 0
        percentual_prazo_atendimento = round((chamados_atendimento_prazo / total_chamados) * 100, 2) if total_chamados else 0
        percentual_prazo_resolucao = round((chamados_finalizado_prazo / total_chamados) * 100, 2) if total_chamados else 0

        return jsonify({
            "status": "success",
            "total_chamados": total_chamados,
            "prazo_atendimento": chamados_atendimento_prazo,
            "percentual_prazo_atendimento": percentual_prazo_atendimento,
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

@operadores_bp.route('/fcrColaboradores', methods=['POST'])
def fcr_colaboradores():
    try:
        data = request.get_json()
        dias = int(data.get('dias'))
        nome = data.get('nome', '').strip().lower()

        hoje = datetime.utcnow().date()
        data_limite = hoje - timedelta(days=dias)

        # Todos os chamados do operador
        total_registros = RelatorioColaboradores.query.filter(
            func.lower(RelatorioColaboradores.operador) == nome,
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
            Chamado.data_finalizacao <= fim,
            Chamado.operador == nome
        ).count()

        # Chamados com FCR
        fcr_registros = [r for r in total_registros if r.first_call == 'S']
        codigos_fcr = [r.cod_chamado for r in fcr_registros if r.cod_chamado]

        return jsonify({
            "status": "success",
            "total_fcr": len(codigos_fcr),
            "percentual_fcr": round((len(fcr_registros) / total_chamados) * 100, 2) if total_registros else 0,
            "cod_chamados": codigos_fcr,
            "total_chamados": total_chamados
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@operadores_bp.route('/reabertosColaboradores', methods=['POST'])
def reabertos_colaboradores():
    try:
        data = request.get_json()
        dias = int(data.get('dias'))
        nome = data.get('nome', '').strip().lower()

        hoje = datetime.utcnow()
        data_limite = hoje - timedelta(days=dias)


        # Todos os chamados do operador no período
        total_registros = RelatorioColaboradores.query.filter(
            RelatorioColaboradores.operador.ilike(nome),
            func.date(RelatorioColaboradores.data_criacao) >= data_limite
        ).all()

        data_inicio = hoje - timedelta(days=dias)

        inicio = datetime.combine(data_inicio, datetime.min.time())
        fim = datetime.combine(hoje, datetime.max.time())

        total_chamados = Chamado.query.filter(
            Chamado.nome_status != 'Cancelado',
            Chamado.nome_status == 'Resolvido',
            Chamado.data_finalizacao != None,
            Chamado.data_finalizacao >= inicio,
            Chamado.data_finalizacao <= fim,
            Chamado.operador == nome
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

@operadores_bp.route('/colaboradores/n2', methods=['GET'])
def render_operadores_n2():
    nome = session.get('nome')

    return render_template('colaboradores_nivel2.html', nome=nome)

@operadores_bp.route('/chamadastransferidasColaboradores', methods=['POST'])
def get_ligacoes_transferidas_colaboradores():
    try:
        data = request.get_json(force=True)
        nome = data.get('nome', '').strip().lower()
        dias = int(data.get("dias", 1))

        # Calcula a data limite (apenas data, sem hora)
        data_limite = (datetime.now() - timedelta(days=dias)).date()

        total_ligacoes = db.session.query(
            func.count()
        ).filter(
            ChamadasDetalhes.transferencia.ilike('%Ramal%'),
            ChamadasDetalhes.data >= data_limite,  # comparação entre date e date
            ChamadasDetalhes.nomeAtendente.ilike(f'%{nome}%')
        ).scalar() or 0

        return jsonify({
            "status": "success",
            "total_ligacoes": total_ligacoes
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@operadores_bp.route('/tminTmaxColaboradores', methods=['POST'])
def get_tmin_tmax_colaboradores():
    try:
        data = request.get_json(force=True)
        nome = data.get('nome', '').strip().lower()
        dias = int(data.get("dias", 1))
        hoje = datetime.now().date()

        # Calcula a data limite (apenas data, sem hora)
        data_limite = (datetime.now() - timedelta(days=dias)).date()

        # Contagem de registros válidos
        count_min = db.session.query(func.count(PerformanceColaboradores.id)).filter(
            PerformanceColaboradores.tempo_minatend != 0,
            PerformanceColaboradores.data >= data_limite,
            PerformanceColaboradores.data <= hoje,
            PerformanceColaboradores.name.ilike(f'%{nome}%')
        ).scalar() or 0

        count_max = db.session.query(func.count(PerformanceColaboradores.id)).filter(
            PerformanceColaboradores.tempo_maxatend != 0,
            PerformanceColaboradores.data >= data_limite,
            PerformanceColaboradores.data <= hoje,
            PerformanceColaboradores.name.ilike(f'%{nome}%')
        ).scalar() or 0

        # Totais (em segundos → converte p/ minutos)
        total_ligacoes_minatend = db.session.query(
            func.sum(PerformanceColaboradores.tempo_minatend)
        ).filter(
            PerformanceColaboradores.tempo_minatend != 0,
            PerformanceColaboradores.data >= data_limite,
            PerformanceColaboradores.data <= hoje,
            PerformanceColaboradores.name.ilike(f'%{nome}%')
        ).scalar() or 0

        total_ligacoes_maxatend = db.session.query(
            func.sum(PerformanceColaboradores.tempo_maxatend)
        ).filter(
            PerformanceColaboradores.tempo_maxatend != 0,
            PerformanceColaboradores.data >= data_limite,
            PerformanceColaboradores.data <= hoje,
            PerformanceColaboradores.name.ilike(f'%{nome}%')
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

@operadores_bp.route('/chamadasEfetuadasColaboradores', methods=['POST'])
def get_ligacoes_efetuadas_colaboradores():
    try:
        data = request.get_json(force=True)
        nome = data.get('nome', '').strip().lower()
        dias = int(data.get("dias", 1))  
        data_limite = datetime.now() - timedelta(days=dias)

        total_ligacoes = db.session.query(
            func.count()
        ).filter(
            RegistroChamadas.status == 'Atendida',
            RegistroChamadas.data_hora >= data_limite,
            RegistroChamadas.nome_atendente.ilike(f'%{nome}%')  # busca parcial
        ).scalar() or 0

        return jsonify({
            "status": "success",
            "total_ligacoes": total_ligacoes
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500