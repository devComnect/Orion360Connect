from flask import Blueprint, jsonify, request, send_file, make_response, current_app
from application.models import Chamado, db, RelatorioColaboradores, PerformanceColaboradores, RegistroChamadas, ChamadasDetalhes, DoorAccessLogs, UserAccess, DeviceAccess, EventosAtendentes, Turnos
from application.models import PesquisaSatisfacao
from datetime import datetime, time as dt_time
from modules.relatorios.utils import get_turno, get_turno_ligacao, is_hora_valida, cores_por_turno, extrair_ces, extrair_csat, extrair_nps 
from collections import Counter
from io import BytesIO
from fpdf import FPDF
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import func, and_, or_, extract
from zoneinfo import ZoneInfo  # Python 3.9+
from datetime import datetime, timedelta
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import PageBreak, Image
import os


relatorios_bp = Blueprint('relatorios_bp', __name__, url_prefix='/relatorios')


@relatorios_bp.route("/extrairRelatorios", methods=['POST'])
def extrair_relatorios():
    data_inicio = request.form.get('data_inicio')
    hora_inicio = request.form.get('hora_inicio')
    data_final = request.form.get('data_final')
    hora_final = request.form.get('hora_final')
    operador = request.form.get('operador')

    if not all([data_inicio, hora_inicio, data_final, hora_final, operador]):
        return {"status": "error", "message": "Parâmetros ausentes"}, 400

    try:
        dt_inicio = datetime.strptime(f"{data_inicio} {hora_inicio}", '%Y-%m-%d %H:%M')
        dt_final = datetime.strptime(f"{data_final} {hora_final}", '%Y-%m-%d %H:%M')
    except ValueError:
        return {"status": "error", "message": "Formato de data/hora inválido"}, 400

    # ---------- CHAMADOS ----------
    chamados = Chamado.query.filter(
        Chamado.operador == operador,
        Chamado.data_criacao >= dt_inicio,
        Chamado.data_criacao <= dt_final
    ).order_by(Chamado.data_criacao).all()
    total_chamados = len(chamados)

    # ---------- SLA ----------  
    expirados_atendimento = sum(1 for c in chamados if c.sla_atendimento == 'S')
    expirados_resolucao = sum(1 for c in chamados if c.sla_resolucao == 'S')
    chamados_atendimento_prazo = sum(1 for c in chamados if c.sla_atendimento == 'N')
    chamados_finalizado_prazo = sum(1 for c in chamados if c.sla_resolucao == 'N')

    percentual_atendimento = round((expirados_atendimento / total_chamados) * 100, 2) if total_chamados else 0
    percentual_resolucao = round((expirados_resolucao / total_chamados) * 100, 2) if total_chamados else 0
    percentual_prazo_atendimento = round((chamados_atendimento_prazo / total_chamados) * 100, 2) if total_chamados else 0
    percentual_prazo_resolucao = round((chamados_finalizado_prazo / total_chamados) * 100, 2) if total_chamados else 0

    # ---------- PERFORMANCE ----------
    performance = PerformanceColaboradores.query.filter(
        PerformanceColaboradores.name == operador,
        PerformanceColaboradores.data >= dt_inicio.date(),
        PerformanceColaboradores.data <= dt_final.date()
    ).order_by(PerformanceColaboradores.data).all()

    total_ligacoes_atendidas = sum(p.ch_atendidas or 0 for p in performance)
    total_ligacoes_naoatendidas = sum(p.ch_naoatendidas or 0 for p in performance)

    # ---------- LIGAÇÕES EFETUADAS ----------
    total_ligacoes_efetuadas = db.session.query(
        func.count()
    ).filter(
        RegistroChamadas.status == 'Atendida',
        RegistroChamadas.data_hora >= dt_inicio,
        RegistroChamadas.data_hora <= dt_final,
        RegistroChamadas.nome_atendente.ilike(f'%{operador}%')
    ).scalar() or 0

    # ---------- TRANSFERÊNCIAS ----------
    total_transferencias = db.session.query(func.count()).filter(
        ChamadasDetalhes.transferencia.ilike('%Ramal%'),
        ChamadasDetalhes.data >= dt_inicio.date(),
        ChamadasDetalhes.data <= dt_final.date(),
        ChamadasDetalhes.nomeAtendente.ilike(f'%{operador}%')
    ).scalar() or 0

    # ---------- PAUSAS ----------
    from datetime import timedelta

    # Função auxiliar para converter duração string (HH:MM:SS) em timedelta
    def _parse_duration_to_timedelta(duracao_raw):
        try:
            if isinstance(duracao_raw, str):
                parts = duracao_raw.split(':')
                if len(parts) == 3:
                    h, m, s = map(int, parts)
                    return timedelta(hours=h, minutes=m, seconds=s)
                elif len(parts) == 2:
                    m, s = map(int, parts)
                    return timedelta(minutes=m, seconds=s)
            elif isinstance(duracao_raw, timedelta):
                return duracao_raw
        except Exception:
            pass
        return timedelta(0)

    # Buscar nome da pausa, total e duração
    pausas_raw = db.session.query(
        EventosAtendentes.nome_pausa,
        EventosAtendentes.duracao
    ).filter(
        EventosAtendentes.nome_atendente.ilike(f'%{operador}%'),
        EventosAtendentes.data >= dt_inicio.date(),
        EventosAtendentes.data <= dt_final.date(),
        EventosAtendentes.evento == 'Pausa'
    ).all()

    from collections import defaultdict
    pausas_agrupadas = defaultdict(lambda: {'total': 0, 'duracao': timedelta()})

    for nome_pausa, duracao in pausas_raw:
        key = nome_pausa or '-'
        pausas_agrupadas[key]['total'] += 1
        pausas_agrupadas[key]['duracao'] += _parse_duration_to_timedelta(duracao)

    # ---------- TEMPO MIN/MAX ATENDIMENTO ----------
    count_min = db.session.query(func.count(PerformanceColaboradores.id)).filter(
        PerformanceColaboradores.tempo_minatend != 0,
        PerformanceColaboradores.data >= dt_inicio.date(),
        PerformanceColaboradores.data <= dt_final.date(),
        PerformanceColaboradores.name.ilike(f'%{operador}%')
    ).scalar() or 0

    count_max = db.session.query(func.count(PerformanceColaboradores.id)).filter(
        PerformanceColaboradores.tempo_maxatend != 0,
        PerformanceColaboradores.data >= dt_inicio.date(),
        PerformanceColaboradores.data <= dt_final.date(),
        PerformanceColaboradores.name.ilike(f'%{operador}%')
    ).scalar() or 0

    total_ligacoes_minatend = db.session.query(
        func.sum(PerformanceColaboradores.tempo_minatend)
    ).filter(
        PerformanceColaboradores.tempo_minatend != 0,
        PerformanceColaboradores.data >= dt_inicio.date(),
        PerformanceColaboradores.data <= dt_final.date(),
        PerformanceColaboradores.name.ilike(f'%{operador}%')
    ).scalar() or 0

    total_ligacoes_maxatend = db.session.query(
        func.sum(PerformanceColaboradores.tempo_maxatend)
    ).filter(
        PerformanceColaboradores.tempo_maxatend != 0,
        PerformanceColaboradores.data >= dt_inicio.date(),
        PerformanceColaboradores.data <= dt_final.date(),
        PerformanceColaboradores.name.ilike(f'%{operador}%')
    ).scalar() or 0

    # Obtenha os registros de FCR e filtre diretamente na aplicação
    registros_fcr = RelatorioColaboradores.query.filter(
        func.lower(RelatorioColaboradores.operador) == operador,
        RelatorioColaboradores.data_criacao >= dt_inicio,
        RelatorioColaboradores.data_criacao <= dt_final,
        RelatorioColaboradores.nome_status == 'Resolvido'
    ).all()

    fcr_registros = [r for r in registros_fcr if r.first_call == 'S']
    total_fcr = len(fcr_registros)

    total_ligacoes_minatend /= 60
    total_ligacoes_maxatend /= 60

    media_min = (total_ligacoes_minatend / count_min) if count_min > 0 else 0
    media_max = (total_ligacoes_maxatend / count_max) if count_max > 0 else 0

    def formatar_tempo(minutos: float) -> str:
        if minutos < 60:
            return f"{round(minutos)} min"
        elif minutos < 1440:
            return f"{minutos / 60:.1f} h"
        else:
            return f"{minutos / 1440:.2f} dias"

    # ---------- GERAÇÃO DO PDF ----------
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    centered_style_title = ParagraphStyle(name="centered_title", parent=styles['Title'], alignment=TA_CENTER)
    centered_style_subtitle = ParagraphStyle(name="centered_subtitle", parent=styles['Normal'], alignment=TA_CENTER)
    centered_style_section = ParagraphStyle(name="centered_section", parent=styles['Heading2'], alignment=TA_CENTER)

    # Título principal
    elements.append(Paragraph(f"Relatório do Operador: {operador}", centered_style_title))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Período: {data_inicio} {hora_inicio} até {data_final} {hora_final}", centered_style_subtitle))
    elements.append(Spacer(1, 12))

    # ---------- Tabela de Chamados ----------
    data_chamados = [['Descrição', 'Total']]
    data_chamados.extend([
        ['Total de chamados', str(total_chamados)],
        ['Total First Call Resolution', str(total_fcr)],
        ['SLA Atendimento (Prazo)', f"{percentual_prazo_atendimento}%"],
        ['SLA Atendimento (expirado)', f"{percentual_atendimento}%"],
        ['SLA Resolução (Prazo)', f"{percentual_prazo_resolucao}%"],
        ['SLA Resolução (expirado)', f"{percentual_resolucao}%"],
    ])
    table_chamados = Table(data_chamados, colWidths=[250, 100])
    table_chamados.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkgray),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,0), 'LEFT'),
        ('ALIGN', (0,1), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 11),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 0.5, colors.gray)
    ]))
    elements.append(Paragraph("Chamados", centered_style_section))
    elements.append(table_chamados)
    elements.append(Spacer(1,12))

    # ---------- Tabela de Ligações ----------
    data_ligacoes = [['Descrição', 'Total']]
    data_ligacoes.extend([
        ['Ligações Atendidas', str(total_ligacoes_atendidas)],
        ['Ligações não Atendidas', str(total_ligacoes_naoatendidas)],
        ['Ligações Efetuadas', str(total_ligacoes_efetuadas)],
        ['Ligações Transferidas', str(total_transferencias)],
        ['Tempo Mínimo Atendimento (Média)', formatar_tempo(media_min)],
        ['Tempo Máximo Atendimento (Média)', formatar_tempo(media_max)]
    ])
    table_ligacoes = Table(data_ligacoes, colWidths=[250, 100])
    table_ligacoes.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkgray),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,0), 'LEFT'),
        ('ALIGN', (0,1), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 11),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 0.5, colors.gray)
    ]))
    elements.append(Paragraph("Ligações", centered_style_section))
    elements.append(table_ligacoes)
    elements.append(Spacer(1,12))

    # ---------- Tabela de Pausas ----------
    data_pausas = [['Nome da pausa', 'Total', 'Duração total']]
    for nome_pausa, dados in pausas_agrupadas.items():
        duracao_str = str(dados['duracao'])  # formato: H:MM:SS
        data_pausas.append([nome_pausa, str(dados['total']), duracao_str])
    table_pausas = Table(data_pausas, colWidths=[200, 80, 100])
    table_pausas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkgray),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,0), 'LEFT'),
        ('ALIGN', (0,1), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 11),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 0.5, colors.gray)
    ]))
    elements.append(Paragraph("Pausas", centered_style_section))
    elements.append(table_pausas)
    elements.append(Spacer(1,12))

    # ---------- Build PDF ----------
    import traceback
    try:
        doc.build(elements)
    except Exception as e:
        print("Erro ao gerar PDF:", e)
        traceback.print_exc()
        return {"status": "error", "message": f"Erro ao gerar PDF: {e}"}, 500

    buffer.seek(0)
    operador_safe = operador.replace(" ", "_")
    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=relatorio_{operador_safe}_{data_inicio}_a_{data_final}.pdf'

    return response

@relatorios_bp.route("/extrairControleAcesso", methods=['POST'])
def extrair_controle_acesso():
    data_inicio = request.form.get('data')
    hora_inicio = request.form.get('hora')
    data_fim = request.form.get('dataFinalAcesso')
    hora_fim = request.form.get('horaFinalAcesso')
    operador = request.form.get('operadorControle')
    leitor_id = request.form.get('leitorasSelect')

    tz = ZoneInfo("America/Sao_Paulo")

    datahora_inicio = datetime.strptime(f"{data_inicio} {hora_inicio}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)
    datahora_fim = datetime.strptime(f"{data_fim} {hora_fim}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)

    timestamp_inicio = int((datahora_inicio - timedelta(hours=3)).timestamp())
    timestamp_fim = int((datahora_fim - timedelta(hours=3)).timestamp())

    query = (
        db.session.query(
            DoorAccessLogs.id.label('acesso_id'),
            UserAccess.id.label('usuario_id'),
            UserAccess.name.label('nome_usuario'),
            DeviceAccess.id.label('dispositivo_id'),
            DeviceAccess.name.label('nome_dispositivo'),
            func.from_unixtime(DoorAccessLogs.time).label('data_acesso'),
            DoorAccessLogs.event.label('tipo_evento'),
            DoorAccessLogs.hw_device_id,
            DoorAccessLogs.identifier_id,
            DoorAccessLogs.card_value,
            DoorAccessLogs.qrcode_value
        )
        .join(UserAccess, DoorAccessLogs.user_id == UserAccess.id)
        .join(DeviceAccess, DoorAccessLogs.device_id == DeviceAccess.id)
        .filter(DoorAccessLogs.time.between(timestamp_inicio, timestamp_fim))
    )

    if operador and operador != "Todos":
        query = query.filter(UserAccess.name == operador)

    if leitor_id and leitor_id != "Todos":
        query = query.filter(DeviceAccess.id == int(leitor_id))

    query = query.order_by(DoorAccessLogs.time.desc())
    resultados = query.all()

    buffer = BytesIO()

    # Usando SimpleDocTemplate e Platypus para PDF com tabela
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    title = Paragraph("Relatório de Controle de Acesso", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    colaborador_text = f"Colaborador: {operador if operador and operador != 'Todos' else 'Todos'}"
    periodo_text = f"Período: {data_inicio} {hora_inicio} até {data_fim} {hora_fim}"

    elements.append(Paragraph(colaborador_text, styles['Normal']))
    elements.append(Paragraph(periodo_text, styles['Normal']))
    elements.append(Spacer(1, 12))

    # Cabeçalho da tabela
    # Cabeçalho da tabela atualizado
    data = [
        ['Data Acesso', 'Leitora', 'Evento']
    ]

# Preenche linhas da tabela com os resultados
    for row in resultados:
        data_acesso_sp = row.data_acesso + timedelta(hours=3)  # ajustar para horário de SP
        data.append([
            data_acesso_sp.strftime('%Y-%m-%d %H:%M:%S'),
            row.nome_dispositivo,
            str(row.tipo_evento)
        ])

    # Cria a tabela e aplica estilo
    table = Table(data, colWidths=[150, 150, 150])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgray),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),

        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),

        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),

        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
    ])
    table.setStyle(style)
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    response = make_response(buffer.read())
    response.headers['Content-Type'] = 'application/pdf'

    operador_safe = operador.replace(" ", "_") if operador and operador != "Todos" else "todos"
    response.headers['Content-Disposition'] = f'attachment; filename=controle_acesso_{operador_safe}_{data_inicio}_a_{data_fim}.pdf'

    return response

@relatorios_bp.route("/extrairComparativoRelatorios", methods=['POST'])
def extrair_comparativo_relatorios():
    data_inicio = request.form.get('data_inicio_comp')
    hora_inicio = request.form.get('hora_inicio_comp')
    data_final = request.form.get('data_final_comp')
    hora_final = request.form.get('hora_final_comp')
    nome = request.form.get('nome_operador')

    if not all([data_inicio, hora_inicio, data_final, hora_final]):
        return {"status": "error", "message": "Parâmetros ausentes"}, 400

    try:
        dt_inicio = datetime.strptime(f"{data_inicio} {hora_inicio}", '%Y-%m-%d %H:%M')
        dt_final = datetime.strptime(f"{data_final} {hora_final}", '%Y-%m-%d %H:%M')
    except ValueError:
        return {"status": "error", "message": "Formato de data/hora inválido"}, 400

    # ---------- CHAMADOS ----------
    query_chamados = Chamado.query.filter(
        Chamado.data_criacao >= dt_inicio,
        Chamado.data_criacao <= dt_final
    )
    if nome:
        query_chamados = query_chamados.filter(Chamado.operador.ilike(f'%{nome}%'))

    chamados = query_chamados.order_by(Chamado.data_criacao).all()
    total_chamados = len(chamados)

    expirados_atendimento = sum(1 for c in chamados if c.sla_atendimento == 'S')
    expirados_resolucao = sum(1 for c in chamados if c.sla_resolucao == 'S')
    chamados_atendimento_prazo = sum(1 for c in chamados if c.sla_atendimento == 'N')
    chamados_finalizado_prazo = sum(1 for c in chamados if c.sla_resolucao == 'N')

    percentual_atendimento = round((expirados_atendimento / total_chamados) * 100, 2) if total_chamados else 0
    percentual_resolucao = round((expirados_resolucao / total_chamados) * 100, 2) if total_chamados else 0
    percentual_prazo_atendimento = round((chamados_atendimento_prazo / total_chamados) * 100, 2) if total_chamados else 0
    percentual_prazo_resolucao = round((chamados_finalizado_prazo / total_chamados) * 100, 2) if total_chamados else 0

    # ---------- LIGAÇÕES (ChamadasDetalhes) com filtro de hora válida ----------
    

    query_ligacoes_geral = ChamadasDetalhes.query.filter(
        ChamadasDetalhes.data >= dt_inicio.date(),
        ChamadasDetalhes.data <= dt_final.date(),
    )
    if nome:
        query_ligacoes_geral = query_ligacoes_geral.filter(
            ChamadasDetalhes.nomeAtendente.ilike(f"%{nome}%")
        )
    ligacoes_geral = query_ligacoes_geral.all()

    # Filtrar ligações válidas para usar no gráfico e total de "atendidas" consistente
    ligacoes_validas = [
        l for l in ligacoes_geral
        if is_hora_valida(l.horaEntradaPos)
    ]

    total_ligacoes_atendidas = sum(1 for l in ligacoes_validas if l.tipo == 'Atendida')
    # Ajuste: dependendo dos tipos existentes no banco, substituir o tipo de "não atendida" correto
    total_ligacoes_naoatendidas = sum(1 for l in ligacoes_validas if l.tipo != 'Atendida')
    # Se quiser usar um tipo específico, por exemplo "Não Atendida", "Abandonada", etc,
    #troque a condição acima para refletir o que for aplicável.

    # Também contabilizar quantas foram desconsideradas por hora inválida
    ligacoes_atendidas_invalidas = sum(
        1 for l in ligacoes_geral
        if l.tipo == 'Atendida' and not is_hora_valida(l.horaEntradaPos)
    )

    # Manter o cálculo de transferidas ou de ligações efetuadas conforme necessidade
    total_ligacoes_efetuadas = db.session.query(func.count()).filter(
        RegistroChamadas.status == 'Atendida',
        RegistroChamadas.data_hora >= dt_inicio,
        RegistroChamadas.data_hora <= dt_final,
    ).scalar() or 0

    query_transferidas = db.session.query(func.count()).filter(
        ChamadasDetalhes.transferencia.ilike('%Ramal%'),
        ChamadasDetalhes.data >= dt_inicio.date(),
        ChamadasDetalhes.data <= dt_final.date()
    )
    if nome:
        query_transferidas = query_transferidas.filter(ChamadasDetalhes.nomeAtendente.ilike(f'%{nome}%'))
    total_ligacoes_transferidas = query_transferidas.scalar() or 0

    # ---------- FCR ----------
    registros_fcr = RelatorioColaboradores.query.filter(
        RelatorioColaboradores.data_criacao >= dt_inicio,
        RelatorioColaboradores.data_criacao <= dt_final,
        RelatorioColaboradores.nome_status == 'Resolvido'
    ).all()

    fcr_registros = [r for r in registros_fcr if r.first_call == 'S']
    total_fcr = len(fcr_registros)

    reabertos_registros = RelatorioColaboradores.query.filter(
        func.date(RelatorioColaboradores.data_criacao) >= dt_inicio,
        func.date(RelatorioColaboradores.data_criacao) <= dt_final,
    ).all()

    reabertos = [r for r in reabertos_registros if r.reaberto == 'Reaberto']
    total_reabertos = len(reabertos)

    # ---------- PDF SETUP ----------
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    centered_title = ParagraphStyle('centered_title', parent=styles['Title'], alignment=TA_CENTER)
    centered_subtitle = ParagraphStyle('centered_subtitle', parent=styles['Normal'], alignment=TA_CENTER)
    centered_section = ParagraphStyle('centered_section', parent=styles['Heading2'], alignment=TA_CENTER)

    elements.append(Paragraph("Relatório Comparativo", centered_title))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Período: {dt_inicio.strftime('%d/%m/%Y %H:%M')} a {dt_final.strftime('%d/%m/%Y %H:%M')}", centered_subtitle))
    elements.append(Spacer(1, 12))

    # ---------- Tabela de Chamados ----------
    data_chamados = [
        ['Descrição', 'Total'],
        ['Total de chamados', str(total_chamados)],
        ['Total First Call Resolution', str(total_fcr)],
        ['Total Chamados Reabertos', str(total_reabertos)],
        ['SLA Atendimento (Prazo)', f"{percentual_prazo_atendimento}%"],
        ['SLA Atendimento (Expirado)', f"{percentual_atendimento}%"],
        ['SLA Resolução (Prazo)', f"{percentual_prazo_resolucao}%"],
        ['SLA Resolução (Expirado)', f"{percentual_resolucao}%"]
    ]
    table_chamados = Table(data_chamados, colWidths=[250, 100])
    table_chamados.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkgray),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 11),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 0.5, colors.gray)
    ]))
    elements.append(Paragraph("Chamados", centered_section))
    elements.append(table_chamados)
    elements.append(Spacer(1, 12))

    

    # ---------- Tabela de Ligações ----------
    data_ligacoes = [
        ['Descrição', 'Total'],
        ['Ligações Atendidas', str(total_ligacoes_atendidas)],
        ['Ligações não Atendidas', str(total_ligacoes_naoatendidas)],
        ['Ligações Efetuadas', str(total_ligacoes_efetuadas)],
        ['Ligações Transferidas', str(total_ligacoes_transferidas)]
    ]
    table_ligacoes = Table(data_ligacoes, colWidths=[250, 100])
    table_ligacoes.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkgray),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 11),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 0.5, colors.gray)
    ]))
    elements.append(Paragraph("Ligações", centered_section))
    elements.append(table_ligacoes)
    elements.append(Spacer(1, 12))

    elements.append(PageBreak())
    # ---------- Gráfico de Chamados por Turno ----------
    turnos = [get_turno(ch.data_criacao) for ch in chamados]
    turno_counts = Counter(turnos)
    if turno_counts:
        labels = list(turno_counts.keys())
        sizes = list(turno_counts.values())
        colors_pizza = [cores_por_turno.get(label, "#808080") for label in labels]

        plt.figure(figsize=(4.5, 4.5))
        plt.pie(
            sizes, labels=labels,
            autopct='%1.1f%%',
            startangle=140, colors=colors_pizza,
            wedgeprops={'width': 0.4}  # Donut
        )
        centre_circle = plt.Circle((0, 0), 0.70, fc='white')
        fig = plt.gcf()
        fig.gca().add_artist(centre_circle)
        plt.axis('equal')

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight')
        plt.close()

        from reportlab.platypus import Image
        img_buffer.seek(0)
        elements.append(Paragraph("Distribuição de Chamados por Turno", centered_section))
        elements.append(Image(img_buffer, width=200, height=200))
        elements.append(Spacer(1, 12))

    # ---------- Gráfico de Ligações por Turno ----------
    turnos_ligacoes = []
    for l in ligacoes_validas:
        try:
            hora = l.horaEntradaPos.strip().split(" ")[0]
            dt_hora = datetime.strptime(hora, "%H:%M:%S")
            turno = get_turno(dt_hora)
            turnos_ligacoes.append(turno)
        except:
            continue

    turno_counts_ligacoes = Counter(turnos_ligacoes)
    if turno_counts_ligacoes:
        labels_lig = list(turno_counts_ligacoes.keys())
        sizes_lig = list(turno_counts_ligacoes.values())
        colors_pizza = [cores_por_turno.get(label, "#808080") for label in labels_lig]


        plt.figure(figsize=(4.5, 4.5))
        plt.pie(
            sizes_lig, labels=labels_lig,
            autopct='%1.1f%%',
            startangle=140, colors=colors_pizza,
            wedgeprops={'width': 0.4}  # <- Donut aqui
        )
        centre_circle = plt.Circle((0, 0), 0.70, fc='white')
        fig = plt.gcf()
        fig.gca().add_artist(centre_circle)
        plt.axis('equal')

        img_buffer_lig = BytesIO()
        plt.savefig(img_buffer_lig, format='PNG', bbox_inches='tight')
        plt.close()

        from reportlab.platypus import Image
        img_buffer_lig.seek(0)
        elements.append(Paragraph("Distribuição de Ligações por Turno", centered_section))
        elements.append(Image(img_buffer_lig, width=200, height=200))
        elements.append(Spacer(1, 12))

    # ---------- FINALIZAÇÃO ----------
    doc.build(elements)
    buffer.seek(0)
    filename = f"relatorio_comparativo_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

# Alterar para pegar os usuários da tabela de usuários
@relatorios_bp.route("/getOperadores", methods=['GET'])
def get_operadores():
    operadores_ignorar = ['Alexandre', 'API', 'Caio', 'Fabio', 'Paulo', 'Luciano']  # operadores a ignorar
    operadores = (
        db.session.query(Chamado.operador)
        .filter(Chamado.operador.isnot(None),
                ~Chamado.operador.in_(operadores_ignorar))
        .distinct()
        .order_by(Chamado.operador)
        .all()
    )
    nomes = [op[0] for op in operadores]
    return jsonify(nomes)

@relatorios_bp.route('/getTurnos', methods=['GET'])
def get_turnos():
    turnos = Turnos.query.all()
    turno_list = []

    for turno in turnos:
        if turno.matutino_inicio and turno.matutino_final:
            turno_list.append({
                'id': turno.id,
                'tipo': 'matutino',
                'inicio': turno.matutino_inicio,
                'final': turno.matutino_final
            })

        if turno.vespertino_inicio and turno.vespertino_final:
            turno_list.append({
                'id': turno.id,
                'tipo': 'vespertino',
                'inicio': turno.vespertino_inicio,
                'final': turno.vespertino_final
            })

        if turno.noturno_inicio and turno.noturno_final:
            turno_list.append({
                'id': turno.id,
                'tipo': 'noturno',
                'inicio': turno.noturno_inicio,
                'final': turno.noturno_final
            })

    return jsonify(turno_list), 200

@relatorios_bp.route('/extrairRelatorioTurnos', methods=['POST'])
def extrair_relatorios_turnos():
    try:
        data_inicio = request.form.get('data_inicio_turnos')
        data_fim = request.form.get('data_final_turnos')
        turno = request.form.get('turno')

        if not data_inicio or not data_fim or not turno:
            return {"status": "error", "message": "Parâmetros ausentes"}, 400

        try:
            turno_tipo, turno_id = turno.split("_")
            turno_id = int(turno_id)
        except Exception:
            return {"status": "error", "message": "Turno inválido"}, 400

        turno_row = Turnos.query.get(turno_id)
        if not turno_row:
            return {"status": "error", "message": "Turno não encontrado"}, 404

        hora_inicio_str = getattr(turno_row, f"{turno_tipo}_inicio")
        hora_final_str = getattr(turno_row, f"{turno_tipo}_final")

        if not hora_inicio_str or not hora_final_str:
            return {"status": "error", "message": "Horários do turno incompletos"}, 400

        # conversões
        dt_inicio_data = datetime.strptime(data_inicio, "%Y-%m-%d").date()
        dt_fim_data = datetime.strptime(data_fim, "%Y-%m-%d").date()
        hora_inicio = datetime.strptime(hora_inicio_str, "%H:%M").time()
        hora_final = datetime.strptime(hora_final_str, "%H:%M").time()

        num_dias = (dt_fim_data - dt_inicio_data).days + 1

        # Dicionários para agrupar por mês
        dados_chamados = {}
        dados_ligacoes = {}
        dados_efetuadas = {}

        # --- Loop por dias respeitando turno ---
        for dia_offset in range(num_dias):
            dia_atual = dt_inicio_data + timedelta(days=dia_offset)

            # --- CHAMADOS ---
            if hora_inicio < hora_final:
                dt_inicio_turno = datetime.combine(dia_atual, hora_inicio)
                dt_fim_turno = datetime.combine(dia_atual, hora_final)
                query_chamados = Chamado.query.filter(
                    Chamado.data_criacao >= dt_inicio_turno,
                    Chamado.data_criacao <= dt_fim_turno,
                    Chamado.nome_status != 'Cancelado'
                )
            else:
                # turno atravessa meia-noite
                dt_inicio_turno_1 = datetime.combine(dia_atual, hora_inicio)
                dt_fim_turno_1 = datetime.combine(dia_atual, dt_time(23, 59, 59))
                dia_seguinte = dia_atual + timedelta(days=1)
                dt_inicio_turno_2 = datetime.combine(dia_seguinte, dt_time(0, 0))
                dt_fim_turno_2 = datetime.combine(dia_seguinte, hora_final)
                query_chamados = Chamado.query.filter(
                    or_(
                        and_(Chamado.data_criacao >= dt_inicio_turno_1, Chamado.data_criacao <= dt_fim_turno_1),
                        and_(Chamado.data_criacao >= dt_inicio_turno_2, Chamado.data_criacao <= dt_fim_turno_2),
                    ),
                    Chamado.nome_status != 'Cancelado'
                )

            total_chamados = query_chamados.count()
            if total_chamados:
                mes_key = dia_atual.strftime("%Y-%m")
                dados_chamados[mes_key] = dados_chamados.get(mes_key, 0) + total_chamados

            # --- LIGAÇÕES RECEBIDAS (ChamadasDetalhes) ---
            if hora_inicio < hora_final:
                query_ligacoes = ChamadasDetalhes.query.filter(
                    ChamadasDetalhes.data == dia_atual,
                    ChamadasDetalhes.horaEntradaPos >= hora_inicio.strftime("%H:%M"),
                    ChamadasDetalhes.horaEntradaPos <= hora_final.strftime("%H:%M"),
                )
            else:
                dia_seguinte = dia_atual + timedelta(days=1)
                query_ligacoes = ChamadasDetalhes.query.filter(
                    or_(
                        and_(ChamadasDetalhes.data == dia_atual,
                             ChamadasDetalhes.horaEntradaPos >= hora_inicio.strftime("%H:%M")),
                        and_(ChamadasDetalhes.data == dia_seguinte,
                             ChamadasDetalhes.horaEntradaPos <= hora_final.strftime("%H:%M")),
                    )
                )

            total_ligacoes = query_ligacoes.count()
            if total_ligacoes:
                mes_key = dia_atual.strftime("%Y-%m")
                dados_ligacoes[mes_key] = dados_ligacoes.get(mes_key, 0) + total_ligacoes

            # --- LIGAÇÕES EFETUADAS (RegistroChamadas) ---
            if hora_inicio < hora_final:
                query_efetuadas = RegistroChamadas.query.filter(
                    RegistroChamadas.status == 'Atendida',
                    RegistroChamadas.data_hora >= datetime.combine(dia_atual, hora_inicio),
                    RegistroChamadas.data_hora <= datetime.combine(dia_atual, hora_final),
                )
            else:
                dt_inicio_turno_1 = datetime.combine(dia_atual, hora_inicio)
                dt_fim_turno_1 = datetime.combine(dia_atual, dt_time(23, 59, 59))
                dia_seguinte = dia_atual + timedelta(days=1)
                dt_inicio_turno_2 = datetime.combine(dia_seguinte, dt_time(0, 0))
                dt_fim_turno_2 = datetime.combine(dia_seguinte, hora_final)
                query_efetuadas = RegistroChamadas.query.filter(
                    RegistroChamadas.status == 'Atendida',
                    or_(
                        and_(RegistroChamadas.data_hora >= dt_inicio_turno_1, RegistroChamadas.data_hora <= dt_fim_turno_1),
                        and_(RegistroChamadas.data_hora >= dt_inicio_turno_2, RegistroChamadas.data_hora <= dt_fim_turno_2),
                    )
                )

            total_efetuadas = query_efetuadas.count()
            if total_efetuadas:
                mes_key = dia_atual.strftime("%Y-%m")
                dados_efetuadas[mes_key] = dados_efetuadas.get(mes_key, 0) + total_efetuadas

        # ---------------- PDF ----------------
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        centered_title = ParagraphStyle('centered_title', parent=styles['Title'], alignment=TA_CENTER)
        centered_subtitle = ParagraphStyle('centered_subtitle', parent=styles['Normal'], alignment=TA_CENTER)

        elements.append(Paragraph("Relatório Turnos: Chamados vs Ligações", centered_title))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Período: {dt_inicio_data.strftime('%d/%m/%Y')} a {dt_fim_data.strftime('%d/%m/%Y')}", centered_subtitle))
        elements.append(Paragraph(f"Turno: {turno_tipo.title()} ({hora_inicio_str} às {hora_final_str})", centered_subtitle))
        elements.append(Spacer(1, 24))

        # --- GRÁFICO POR MÊS --- (3 séries)
        meses = sorted(set(dados_chamados.keys()) | set(dados_ligacoes.keys()) | set(dados_efetuadas.keys()))
        # se não houver meses, crie um placeholder com o mês inicial
        if not meses:
            meses = [dt_inicio_data.strftime("%Y-%m")]

        valores_chamados = [dados_chamados.get(m, 0) for m in meses]
        valores_ligacoes = [dados_ligacoes.get(m, 0) for m in meses]
        valores_efetuadas = [dados_efetuadas.get(m, 0) for m in meses]

        x = list(range(len(meses)))
        # ajusta largura/figura conforme qtd meses
        fig_width = max(6, len(meses) * 0.8)
        plt.figure(figsize=(fig_width, 5))
        plt.bar([i - 0.25 for i in x], valores_chamados, width=0.25, label="Chamados", color="#007bff")
        plt.bar([i for i in x], valores_ligacoes, width=0.25, label="Ligações Recebidas", color="#28a745")
        plt.bar([i + 0.25 for i in x], valores_efetuadas, width=0.25, label="Ligações Efetuadas", color="#dc3545")  # vermelho
        plt.xticks(x, meses, rotation=45)
        plt.ylabel("Quantidade")
        plt.legend()
        plt.tight_layout()

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches="tight")
        plt.close()
        img_buffer.seek(0)
        elements.append(Image(img_buffer, width=500, height=260))
        elements.append(Spacer(1, 24))

        # Resumo tabela (totais gerais)
        total_chamados_final = sum(valores_chamados)
        total_ligacoes_final = sum(valores_ligacoes)
        total_efetuadas_final = sum(valores_efetuadas)
        data_resumo = [
            ["Descrição", "Total"],
            ["Chamados no período", str(total_chamados_final)],
            ["Ligações Recebidas no período", str(total_ligacoes_final)],
            ["Ligações Efetuadas no período", str(total_efetuadas_final)],
        ]
        tabela_resumo = Table(data_resumo, colWidths=[300, 100])
        tabela_resumo.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.darkgray),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 11),
            ("BOTTOMPADDING", (0,0), (-1,0), 8),
            ("BACKGROUND", (0,1), (-1,-1), colors.beige),
            ("GRID", (0,0), (-1,-1), 0.5, colors.gray),
        ]))
        elements.append(tabela_resumo)
        elements.append(Spacer(1, 24))

        data_mensal = [["Mês", "Chamados", "Ligações Recebidas", "Ligações Efetuadas"]]
        for i, mes in enumerate(meses):
            # converte "2025-01" para "Janeiro/2025"
            mes_formatado = datetime.strptime(mes, "%Y-%m").strftime("%B/%Y").capitalize()
            data_mensal.append([
                mes_formatado,
                str(valores_chamados[i]),
                str(valores_ligacoes[i]),
                str(valores_efetuadas[i]),
            ])

        tabela_mensal = Table(data_mensal, colWidths=[150, 100, 130, 130])
        tabela_mensal.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.darkgray),
            ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 11),
            ("BOTTOMPADDING", (0,0), (-1,0), 8),
            ("BACKGROUND", (0,1), (-1,-1), colors.beige),
            ("GRID", (0,0), (-1,-1), 0.5, colors.gray),
        ]))
        elements.append(tabela_mensal)

        # Build PDF e retorno
        doc.build(elements)
        buffer.seek(0)
        filename = f"comparativo_chamados_ligacoes_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")

    except Exception:
        current_app.logger.exception("Erro ao gerar relatório de turnos")
        return {"status": "error", "message": "Erro interno ao gerar o relatório. Verifique os logs."}, 500

@relatorios_bp.route("/getColaboradores", methods=['GET'])
def get_colaboradores():
    nomes = (
        db.session.query(UserAccess.name)
        .join(DoorAccessLogs, DoorAccessLogs.user_id == UserAccess.id)
        .filter(UserAccess.name.isnot(None))  # evita nomes nulos
        .distinct()
        .order_by(UserAccess.name.asc())
        .all()
    )

    colaboradores = [nome[0] for nome in nomes]

    return jsonify(colaboradores)

@relatorios_bp.route("/extrairSatisfacao", methods=['POST'])
def extrair_satisfacao():
    data_inicio = request.form.get('data_inicio_satisfacao')
    data_fim = request.form.get('data_final_satisfacao')
    psatisfacao = request.form.get('pesquisa_satisfacao')

    data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
    data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()

    if psatisfacao == 'ces':
        return extrair_ces(data_inicio, data_fim)

    if psatisfacao == 'nps':
        return extrair_nps(data_inicio, data_fim)

    if psatisfacao == 'csat':
        return extrair_csat(data_inicio, data_fim)

    return jsonify({"error": "Tipo de pesquisa inválida"}), 400


@relatorios_bp.route("/getLeitoras", methods=['GET'])
def get_leitoras():
    leitoras = (
        db.session.query(DeviceAccess.id, DeviceAccess.name)
        .join(DoorAccessLogs, DoorAccessLogs.device_id == DeviceAccess.id)
        .filter(DeviceAccess.name.isnot(None))  # evita nomes nulos
        .distinct()
        .order_by(DeviceAccess.name.asc())
        .all()
    )

    leitoras_formatadas = [{"id": id_, "name": name} for id_, name in leitoras]

    return jsonify(leitoras_formatadas)