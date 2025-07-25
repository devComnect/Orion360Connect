from flask import Blueprint, jsonify, request, render_template, url_for, send_file
from application.models import Chamado, db,  PerformanceColaboradores
from datetime import datetime, time
from collections import Counter
from io import BytesIO
from fpdf import FPDF
import matplotlib.pyplot as plt
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

    # Consulta chamados com data e hora
    chamados = Chamado.query.filter(
        Chamado.operador == operador,
        Chamado.data_criacao >= dt_inicio,
        Chamado.data_criacao <= dt_final
    ).order_by(Chamado.data_criacao).all()

    total_chamados = len(chamados)

    # Consulta performance (por data apenas)
    performance = PerformanceColaboradores.query.filter(
        PerformanceColaboradores.name == operador,
        PerformanceColaboradores.data >= dt_inicio.date(),
        PerformanceColaboradores.data <= dt_final.date()
    ).order_by(PerformanceColaboradores.data).all()

    total_ligacoes_atendidas = sum(p.ch_atendidas or 0 for p in performance)
    total_ligacoes_naoatendidas = sum(p.ch_naoatendidas or 0 for p in performance)

    # Geração do PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Relatório do Operador: {operador}", ln=True, align="C")

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Período: {dt_inicio.strftime('%d/%m/%Y %H:%M')} a {dt_final.strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(5)

    # Chamados
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Chamados:", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Total de chamados: {total_chamados}", ln=True)
    pdf.ln(2)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(40, 8, "Código", 1)
    pdf.cell(50, 8, "Status", 1)
    pdf.cell(60, 8, "Grupo", 1)
    pdf.cell(40, 8, "Data Criação", 1)
    pdf.ln()

    pdf.set_font("Arial", "", 10)
    if chamados:
        for chamado in chamados:
            pdf.cell(40, 8, chamado.cod_chamado or "-", 1)
            pdf.cell(50, 8, chamado.nome_status or "-", 1)
            grupo = chamado.nome_grupo or "-"
            grupo_truncado = grupo[:30] + "..." if len(grupo) > 30 else grupo
            pdf.cell(60, 8, grupo_truncado, 1)
            pdf.cell(40, 8, chamado.data_criacao.strftime('%d/%m/%Y %H:%M'), 1)
            pdf.ln()
    else:
        pdf.cell(0, 8, "Nenhum chamado encontrado.", 1, ln=True)

    pdf.ln(10)

    # Performance
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Performance de Ligações:", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Total ligações atendidas: {total_ligacoes_atendidas}", ln=True)
    pdf.cell(0, 8, f"Total ligações não atendidas: {total_ligacoes_naoatendidas}", ln=True)
    pdf.ln(2)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(30, 8, "Data", 1)
    pdf.cell(30, 8, "Atendidas", 1)
    pdf.cell(40, 8, "Não atendidas", 1)
    pdf.cell(40, 8, "Tempo Online (s)", 1)
    pdf.cell(40, 8, "Tempo Serviço (s)", 1)
    pdf.ln()

    pdf.set_font("Arial", "", 10)
    if performance:
        for perf in performance:
            pdf.cell(30, 8, perf.data.strftime('%d/%m/%Y'), 1)
            pdf.cell(30, 8, str(perf.ch_atendidas), 1)
            pdf.cell(40, 8, str(perf.ch_naoatendidas), 1)
            pdf.cell(40, 8, str(perf.tempo_online), 1)
            pdf.cell(40, 8, str(perf.tempo_servico), 1)
            pdf.ln()
    else:
        pdf.cell(0, 8, "Nenhum dado de performance encontrado.", 1, ln=True)

    # Finalização
    buffer = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    buffer.write(pdf_bytes)
    buffer.seek(0)

    filename = f"relatorio_{operador}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

'''@relatorios_bp.route("/extrairComparativoRelatorios", methods=['POST'])
def extrair_comparativo_relatorios():
    data_inicio = request.form.get('data_inicio_comp')  # yyyy-mm-dd
    hora_inicio = request.form.get('hora_inicio_comp')  # HH:MM
    data_final = request.form.get('data_final_comp')
    hora_final = request.form.get('hora_final_comp')

    if not all([data_inicio, hora_inicio, data_final, hora_final]):
        return {"status": "error", "message": "Parâmetros ausentes"}, 400

    try:
        dt_inicio = datetime.strptime(f"{data_inicio} {hora_inicio}", '%Y-%m-%d %H:%M')
        dt_final = datetime.strptime(f"{data_final} {hora_final}", '%Y-%m-%d %H:%M')
    except ValueError:
        return {"status": "error", "message": "Formato de data/hora inválido"}, 400

    # Consulta chamados com data e hora
    chamados = Chamado.query.filter(
        Chamado.data_criacao >= dt_inicio,
        Chamado.data_criacao <= dt_final
    ).order_by(Chamado.data_criacao).all()

    total_chamados = len(chamados)

    # Consulta performance (por data apenas)
    performance = PerformanceColaboradores.query.filter(
        PerformanceColaboradores.data >= dt_inicio.date(),
        PerformanceColaboradores.data <= dt_final.date()
    ).order_by(PerformanceColaboradores.data).all()

    total_ligacoes_atendidas = sum(p.ch_atendidas or 0 for p in performance)
    total_ligacoes_naoatendidas = sum(p.ch_naoatendidas or 0 for p in performance)

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

    pdf.set_font("Arial", "B", 11)
    pdf.cell(40, 8, "Código", 1)
    pdf.cell(50, 8, "Status", 1)
    pdf.cell(60, 8, "Grupo", 1)
    pdf.cell(40, 8, "Data Criação", 1)
    pdf.ln()

    pdf.set_font("Arial", "", 10)
    if chamados:
        for chamado in chamados:
            pdf.cell(40, 8, chamado.cod_chamado or "-", 1)
            pdf.cell(50, 8, chamado.nome_status or "-", 1)
            grupo = chamado.nome_grupo or "-"
            grupo_truncado = grupo[:30] + "..." if len(grupo) > 30 else grupo
            pdf.cell(60, 8, grupo_truncado, 1)
            pdf.cell(40, 8, chamado.data_criacao.strftime('%d/%m/%Y %H:%M'), 1)
            pdf.ln()
    else:
        pdf.cell(0, 8, "Nenhum chamado encontrado.", 1, ln=True)

    pdf.ln(10)

    # Performance
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Performance de Ligações:", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Total ligações atendidas: {total_ligacoes_atendidas}", ln=True)
    pdf.cell(0, 8, f"Total ligações não atendidas: {total_ligacoes_naoatendidas}", ln=True)
    pdf.ln(2)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(30, 8, "Data", 1)
    pdf.cell(30, 8, "Atendidas", 1)
    pdf.cell(40, 8, "Não atendidas", 1)
    pdf.cell(40, 8, "Tempo Online (s)", 1)
    pdf.cell(40, 8, "Tempo Serviço (s)", 1)
    pdf.ln()

    pdf.set_font("Arial", "", 10)
    if performance:
        for perf in performance:
            pdf.cell(30, 8, perf.data.strftime('%d/%m/%Y'), 1)
            pdf.cell(30, 8, str(perf.ch_atendidas), 1)
            pdf.cell(40, 8, str(perf.ch_naoatendidas), 1)
            pdf.cell(40, 8, str(perf.tempo_online), 1)
            pdf.cell(40, 8, str(perf.tempo_servico), 1)
            pdf.ln()
    else:
        pdf.cell(0, 8, "Nenhum dado de performance encontrado.", 1, ln=True)

    # Finalização
    buffer = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    buffer.write(pdf_bytes)
    buffer.seek(0)

    filename = f"relatorio_comparativo_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')'''

def get_turno(dt):
    hora = dt.time()
    if time(7, 0) <= hora < time(16, 0):
        return "07:00/16:00"
    elif time(13, 0) <= hora < time(22, 0):
        return "13:00/22:00"
    else:
        return "22:00/07:00"

@relatorios_bp.route("/extrairComparativoRelatorios", methods=['POST'])
def extrair_comparativo_relatorios():
    data_inicio = request.form.get('data_inicio_comp')
    hora_inicio = request.form.get('hora_inicio_comp')
    data_final = request.form.get('data_final_comp')
    hora_final = request.form.get('hora_final_comp')

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

    total_chamados = len(chamados)
    total_ligacoes_atendidas = sum(p.ch_atendidas or 0 for p in performance)
    total_ligacoes_naoatendidas = sum(p.ch_naoatendidas or 0 for p in performance)

    turnos = [get_turno(ch.data_criacao) for ch in chamados]
    turno_counts = Counter(turnos)

    img_pizza_path = None
    img_barra_path = None

    if turno_counts:
        # Gráfico de Pizza
        labels = list(turno_counts.keys())
        sizes = list(turno_counts.values())
        colors = ['#4CAF50', '#2196F3', '#FF5722']

        plt.figure(figsize=(4.5, 4.5))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
        plt.title('Distribuição de Chamados por Turno', fontsize=10)
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
    pdf.cell(0, 10, "Performance de Ligações:", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Total ligações atendidas: {total_ligacoes_atendidas}", ln=True)
    pdf.cell(0, 8, f"Total ligações não atendidas: {total_ligacoes_naoatendidas}", ln=True)
    pdf.ln(2)

    # Gráfico de Pizza
    if img_pizza_path and os.path.exists(img_pizza_path):
        current_y = pdf.get_y()
        if current_y > 220:
            pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Distribuição por Turno (Pizza):", ln=True)
        pdf.ln(2)
        pdf.image(img_pizza_path, x=pdf.get_x() + 30, w=pdf.w / 2.2)
        pdf.ln(5)
        os.remove(img_pizza_path)

    '''# Gráfico de Barras
    if img_barra_path and os.path.exists(img_barra_path):
        current_y = pdf.get_y()
        if current_y > 220:
            pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Distribuição por Turno (Barras):", ln=True)
        pdf.ln(2)
        pdf.image(img_barra_path, x=10, w=pdf.w - 20)
        pdf.ln(10)
        os.remove(img_barra_path)'''

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