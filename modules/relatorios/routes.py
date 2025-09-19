from flask import Blueprint, jsonify, request, render_template, url_for, send_file, make_response
from application.models import Chamado, db, RelatorioColaboradores, PerformanceColaboradores, RegistroChamadas, ChamadasDetalhes, DoorAccessLogs, UserAccess, DeviceAccess, EventosAtendentes
from datetime import datetime, time
from modules.relatorios.utils import get_turno, get_turno_ligacao
from collections import Counter
from io import BytesIO
from fpdf import FPDF
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import func
from zoneinfo import ZoneInfo  # Python 3.9+
from datetime import datetime, timedelta
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import PageBreak
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
    pausas = db.session.query(
        EventosAtendentes.nome_pausa,
        func.count().label('total')
    ).filter(
        EventosAtendentes.nome_atendente.ilike(f'%{operador}%'),
        EventosAtendentes.data >= dt_inicio.date(),
        EventosAtendentes.data <= dt_final.date(),
        EventosAtendentes.evento == 'Pausa'
    ).group_by(EventosAtendentes.nome_pausa).all()

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
        ('ALIGN', (0,0), (-1,0), 'LEFT'),  # Centraliza só cabeçalho
        ('ALIGN', (0,1), (-1,-1), 'LEFT'),   # Alinha o resto à esquerda
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
        ('ALIGN', (0,0), (-1,0), 'LEFT'),  # Centraliza só cabeçalho
        ('ALIGN', (0,1), (-1,-1), 'LEFT'),   # Alinha o resto à esquerda
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
    data_pausas = [['Nome da pausa', 'Total']]
    for p in pausas:
        data_pausas.append([p.nome_pausa or '-', str(p.total)])
    table_pausas = Table(data_pausas, colWidths=[250, 100])
    table_pausas.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkgray),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,0), 'LEFT'),  # Centraliza só cabeçalho
        ('ALIGN', (0,1), (-1,-1), 'LEFT'),   # Alinha o resto à esquerda
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
    def is_hora_valida(hora_str):
        try:
            if not hora_str or len(hora_str.strip()) < 5:
                return False
            hms = hora_str.strip().split(" ")[0]
            datetime.strptime(hms, '%H:%M:%S')
            return True
        except Exception:
            return False

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
        colors_pizza = ['#4CAF50', '#2196F3', '#FF5722']

        plt.pie(
            sizes, labels=labels,
            autopct=lambda pct: f"{int(round(pct/100.*sum(sizes)))}\n({pct:.1f}%)",
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
        colors_pizza = ['#4CAF50', '#2196F3', '#FF5722']

        plt.figure(figsize=(4.5, 4.5))
        plt.pie(
            sizes_lig, labels=labels_lig,
            autopct=lambda pct: f"{int(round(pct/100.*sum(sizes_lig)))}\n({pct:.1f}%)",
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