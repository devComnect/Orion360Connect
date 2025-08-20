from flask import Blueprint, jsonify, request, render_template, url_for, send_file, make_response
from application.models import Chamado, db,  PerformanceColaboradores, RegistroChamadas, ChamadasDetalhes, DoorAccessLogs, UserAccess, DeviceAccess
from datetime import datetime, time
from modules.relatorios.utils import get_turno
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
from reportlab.lib.styles import getSampleStyleSheet
import os


relatorios_bp = Blueprint('relatorios_bp', __name__, url_prefix='/relatorios')


@relatorios_bp.route("/extrairRelatorios", methods=['POST'])
def extrair_relatorios():
    data_inicio = request.form.get('data_inicio')  # yyyy-mm-dd
    hora_inicio = request.form.get('hora_inicio')  # HH:MM
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

    # Consulta chamados
    chamados = Chamado.query.filter(
        Chamado.operador == operador,
        Chamado.data_criacao >= dt_inicio,
        Chamado.data_criacao <= dt_final
    ).order_by(Chamado.data_criacao).all()
    total_chamados = len(chamados)

    # Consulta performance (por data)
    performance = PerformanceColaboradores.query.filter(
        PerformanceColaboradores.name == operador,
        PerformanceColaboradores.data >= dt_inicio.date(),
        PerformanceColaboradores.data <= dt_final.date()
    ).order_by(PerformanceColaboradores.data).all()

    total_ligacoes_atendidas = sum(p.ch_atendidas or 0 for p in performance)
    total_ligacoes_naoatendidas = sum(p.ch_naoatendidas or 0 for p in performance)

    # Total ligações efetuadas no período
    total_ligacoes_efetuadas = db.session.query(
        func.count()
    ).filter(
        RegistroChamadas.status == 'Atendida',
        RegistroChamadas.data_hora >= dt_inicio,
        RegistroChamadas.data_hora <= dt_final,
        RegistroChamadas.nome_atendente.ilike(f'%{operador}%')
    ).scalar() or 0

    # Total transferências no período
    total_transferencias = db.session.query(func.count()).filter(
        ChamadasDetalhes.transferencia.ilike('%Ramal%'),
        ChamadasDetalhes.data >= dt_inicio.date(),
        ChamadasDetalhes.data <= dt_final.date(),
        ChamadasDetalhes.nomeAtendente.ilike(f'%{operador}%')
    ).scalar() or 0

    # Geração do PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Relatório do Operador: {operador}", ln=True, align="C")

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Período: {dt_inicio.strftime('%d/%m/%Y %H:%M')} a {dt_final.strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(5)

    # ---------- TABELA DE CHAMADOS ----------
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Chamados:", ln=True)
    pdf.set_font("Arial", "", 12)

    pdf.set_fill_color(220, 220, 220)
    pdf.cell(80, 8, "Descrição", border=1, fill=True)
    pdf.cell(40, 8, "Total", border=1, ln=True, fill=True)
    pdf.cell(80, 8, "Total de chamados", border=1)
    pdf.cell(40, 8, str(total_chamados), border=1, ln=True)
    pdf.ln(5)

    # ---------- TABELA DE LIGAÇÕES ----------
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Ligações:", ln=True)
    pdf.set_font("Arial", "", 12)

    pdf.set_fill_color(220, 220, 220)
    pdf.cell(80, 8, "Descrição", border=1, fill=True)
    pdf.cell(40, 8, "Total", border=1, ln=True, fill=True)

    pdf.cell(80, 8, "Ligações atendidas", border=1)
    pdf.cell(40, 8, str(total_ligacoes_atendidas), border=1, ln=True)

    pdf.cell(80, 8, "Ligações não atendidas", border=1)
    pdf.cell(40, 8, str(total_ligacoes_naoatendidas), border=1, ln=True)

    pdf.cell(80, 8, "Ligações efetuadas", border=1)
    pdf.cell(40, 8, str(total_ligacoes_efetuadas), border=1, ln=True)

    pdf.cell(80, 8, "Ligações transferidas", border=1)
    pdf.cell(40, 8, str(total_transferencias), border=1, ln=True)
    pdf.ln(5)

    # Finalização
    buffer = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    buffer.write(pdf_bytes)
    buffer.seek(0)

    filename = f"relatorio_{operador}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

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

        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
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
    nome = request.form.get('nome_operador')  # exemplo, caso queira filtrar por operador

    if not all([data_inicio, hora_inicio, data_final, hora_final]):
        return {"status": "error", "message": "Parâmetros ausentes"}, 400

    try:
        dt_inicio = datetime.strptime(f"{data_inicio} {hora_inicio}", '%Y-%m-%d %H:%M')
        dt_final = datetime.strptime(f"{data_final} {hora_final}", '%Y-%m-%d %H:%M')
    except ValueError:
        return {"status": "error", "message": "Formato de data/hora inválido"}, 400

    chamados = Chamado.query.filter(
        Chamado.data_criacao >= dt_inicio,
        Chamado.data_criacao <= dt_final
    ).order_by(Chamado.data_criacao).all()

    performance = PerformanceColaboradores.query.filter(
        PerformanceColaboradores.data >= dt_inicio.date(),
        PerformanceColaboradores.data <= dt_final.date()
    ).order_by(PerformanceColaboradores.data).all()

    # Total ligações efetuadas no período
    total_ligacoes_efetuadas = db.session.query(
        func.count()
    ).filter(
        RegistroChamadas.status == 'Atendida',
        RegistroChamadas.data_hora >= dt_inicio,
        RegistroChamadas.data_hora <= dt_final,
    ).scalar() or 0

    # Total ligações transferidas no período e opcionalmente por operador
    query_transferidas = db.session.query(func.count()).filter(
        ChamadasDetalhes.transferencia.ilike('%Ramal%'),
        ChamadasDetalhes.data >= dt_inicio.date(),
        ChamadasDetalhes.data <= dt_final.date()
    )
    if nome:
        query_transferidas = query_transferidas.filter(
            ChamadasDetalhes.nomeAtendente.ilike(f'%{nome}%')
        )

    total_ligacoes_transferidas = query_transferidas.scalar() or 0

    total_chamados = len(chamados)
    total_ligacoes_atendidas = sum(p.ch_atendidas or 0 for p in performance)
    total_ligacoes_naoatendidas = sum(p.ch_naoatendidas or 0 for p in performance)

    turnos = [get_turno(ch.data_criacao) for ch in chamados]
    turno_counts = Counter(turnos)

    img_pizza_path = None
    img_barra_path = None

    if turno_counts:
        labels = list(turno_counts.keys())
        sizes = list(turno_counts.values())
        colors = ['#4CAF50', '#2196F3', '#FF5722']

        def func_autopct(pct, all_vals):
            absolute = int(round(pct/100.*sum(all_vals)))
            return f"{absolute}\n({pct:.1f}%)"

        plt.figure(figsize=(4.5, 4.5))
        plt.pie(sizes, labels=labels, autopct=lambda pct: func_autopct(pct, sizes), startangle=140, colors=colors)
        plt.title('', fontsize=10)
        plt.axis('equal')

        img_buffer_pizza = BytesIO()
        plt.savefig(img_buffer_pizza, format='PNG', bbox_inches='tight')
        plt.close()

        import tempfile
        temp_pizza = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        temp_pizza.write(img_buffer_pizza.getbuffer())
        temp_pizza.close()
        img_pizza_path = temp_pizza.name

        # Gráfico de Barras
        plt.figure(figsize=(4.5, 2.5))
        plt.bar(labels, sizes, color=colors)
        plt.title("Chamados por Turno (Barras)", fontsize=10)
        plt.xlabel("Turno")
        plt.ylabel("Quantidade")
        plt.tight_layout()

        img_buffer_barra = BytesIO()
        plt.savefig(img_buffer_barra, format='PNG', bbox_inches='tight')
        plt.close()

        temp_barra = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        temp_barra.write(img_buffer_barra.getbuffer())
        temp_barra.close()
        img_barra_path = temp_barra.name

    # Geração do PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Relatório Comparativo:", ln=True, align="C")

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Período: {dt_inicio.strftime('%d/%m/%Y %H:%M')} a {dt_final.strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(5)

    # Chamados
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Chamados:", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Total de chamados: {total_chamados}", ln=True)
    pdf.ln(2)

    # Performance
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Ligações:", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Total ligações atendidas: {total_ligacoes_atendidas}", ln=True)
    pdf.cell(0, 8, f"Total ligações não atendidas: {total_ligacoes_naoatendidas}", ln=True)
    pdf.cell(0, 8, f"Total ligações efetuadas: {total_ligacoes_efetuadas}", ln=True)
    pdf.cell(0, 8, f"Total ligações transferidas: {total_ligacoes_transferidas}", ln=True)
    pdf.ln(2)

    # Gráfico de Pizza
    if img_pizza_path and os.path.exists(img_pizza_path):
        current_y = pdf.get_y()
        if current_y > 220:
            pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Distribuição de Chamados por Turno:", ln=True)
        pdf.ln(2)
        pdf.image(img_pizza_path, x=pdf.get_x() + 30, w=pdf.w / 2.2)
        pdf.ln(5)
        os.remove(img_pizza_path)

    # (Gráfico de barras comentado)

    # Finaliza PDF
    buffer = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    buffer.write(pdf_bytes)
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