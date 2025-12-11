from datetime import datetime, time, timedelta
from application.models import db, PesquisaSatisfacao
from flask import request, jsonify
from sqlalchemy import func, and_, or_, extract
from flask import send_file
import io
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file
from sqlalchemy import func


cores_por_turno = {
    "07:00/16:00": "#4CAF50",
    "09:30/18:30": "#2196F3",
    "10:00/19:00": "#FF9800",
    "13:00/22:00": "#9C27B0",
    "22:00/07:00": "#CD5C5C",
    "06:00/15:00": "#009688",       
    "12:00/21:00": "#3F51B5",       
    "08:00/17:00": "#795548",       
}

def get_turno(dt):
    if not isinstance(dt, datetime):
        raise ValueError("A data deve ser do tipo datetime")

    hora = dt.time()

    if time(7, 0) <= hora < time(16, 0):
        return "07:00/16:00"
    elif time(9, 0) <= hora < time(18, 0):
        return "09:30/18:30"
    elif time(10, 0) <= hora < time(19, 0):
        return "10:00/19:00"
    elif time(13, 0) <= hora < time(22, 0):
        return "13:00/22:00"
    else:
        # Esse intervalo cobre de 22:00 até 07:00 do dia seguinte
        return "22:00/07:00"

def get_turno_ligacao(hora_str):
    from datetime import datetime
    h, m, s = map(int, hora_str.split(":"))
    hora = h + m / 60 + s / 3600

    if 7 <= hora < 16:
        return "07:00/16:00"
    elif 9 <= hora < 18:
        return "09:30/18:30"
    elif 10 <= hora < 19:
        return "10:00/19:00"
    elif 13 <= hora < 22:
        return "13:00/22:00"
    else:
        return "22:00/07:00"

def is_hora_valida(hora_str):
    try:
        if not hora_str or len(hora_str) < 5:
            return False
        hora = hora_str.strip().split(" ")[0]
        datetime.strptime(hora, '%H:%M:%S')
        return True
    except:
        return False
    
def parse_duration_to_timedelta(duracao_str):
    try:
        h, m, s = map(int, duracao_str.split(':'))
        return timedelta(hours=h, minutes=m, seconds=s)
    except Exception:
        return timedelta(0)
    
def formatar_tempo(minutos: float) -> str:
        if minutos < 60:
            return f"{round(minutos)} min"
        elif minutos < 1440:
            return f"{minutos / 60:.1f} h"
        else:
            return f"{minutos / 1440:.2f} dias"

def gerar_pdf_relatorio(titulo, texto, tabela_dados, grafico_path):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Título
    story.append(Paragraph(f"<b>{titulo}</b>", styles["Title"]))
    story.append(Spacer(1, 20))

    # Texto
    for linha in texto:
        story.append(Paragraph(linha, styles["Normal"]))
        story.append(Spacer(1, 10))

    # Tabela
    tabela = Table(tabela_dados)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("BOX", (0,0), (-1,-1), 1, colors.black),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(tabela)
    story.append(Spacer(1, 20))

    # Gráfico
    img = Image(grafico_path, width=400, height=250)
    story.append(img)

    doc.build(story)
    buffer.seek(0)

    return buffer



def extrair_nps(data_inicio, data_fim):

    NPS_MAP = {
        'Péssimo': 1, 'Discordo Totalmente': 2, 'Discordo Parcialmente': 3,
        'Neutro': 4, 'Concordo Parcialmente': 5, 'Regular': 6, 'Bom': 7,
        'Concordo': 8, 'Concordo Plenamente': 9, 'Ótimo': 10
    }

    alternativas = db.session.query(PesquisaSatisfacao.alternativa).filter(
        PesquisaSatisfacao.data_resposta >= data_inicio,
        PesquisaSatisfacao.data_resposta <= data_fim,
        PesquisaSatisfacao.alternativa.isnot(None),
        func.length(PesquisaSatisfacao.alternativa) > 0
    ).all()

    notas = [NPS_MAP.get(a[0]) for a in alternativas if NPS_MAP.get(a[0])]

    total = len(notas)

    if total == 0:
        buffer = gerar_pdf_relatorio(
            "Relatório NPS",
            ["Não há respostas no período selecionado."],
            [["Campo", "Valor"], ["Total", "0"]],
            ""
        )
        return send_file(buffer, as_attachment=True, download_name="relatorio_nps.pdf")

    promotores = sum(1 for n in notas if n >= 9)
    neutros = sum(1 for n in notas if 7 <= n <= 8)
    detratores = sum(1 for n in notas if n <= 6)

    nps = round(((promotores - detratores) / total) * 100, 2)

    if nps >= 75: status = "Excelente"
    elif nps >= 50: status = "Muito bom"
    elif nps >= 40: status = "Razoável"
    else: status = "Ruim"

    # --- GERA GRÁFICO ---
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(["Promotores", "Neutros", "Detratores"], [promotores, neutros, detratores])
    ax.set_title("Distribuição NPS")
    grafico_path = "grafico_nps.png"
    fig.savefig(grafico_path, bbox_inches="tight")
    plt.close(fig)

    tabela = [
        ["Métrica", "Valor"],
        ["Período", f"{data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}"],
        ["Total respostas", total],
        ["Promotores", promotores],
        ["Neutros", neutros],
        ["Detratores", detratores],
        ["NPS", f"{nps}%"],
        ["Classificação", status],
    ]

    texto = [
        "Relatório completo de NPS do período informado.",
        "Abaixo a síntese dos indicadores."
    ]

    buffer = gerar_pdf_relatorio("Relatório NPS", texto, tabela, grafico_path)

    return send_file(buffer, as_attachment=True, download_name="relatorio_nps.pdf")



def extrair_ces(data_inicio, data_fim):

    CES_MAP = {
        'Péssimo': 1, 'Discordo Totalmente': 2, 'Discordo Parcialmente': 3,
        'Neutro': 4, 'Concordo Parcialmente': 5, 'Regular': 6, 'Bom': 7,
        'Concordo': 8, 'Concordo Plenamente': 9, 'Ótimo': 10
    }

    respostas = db.session.query(PesquisaSatisfacao.alternativa).filter(
        PesquisaSatisfacao.data_resposta >= data_inicio,
        PesquisaSatisfacao.data_resposta <= data_fim,
        PesquisaSatisfacao.alternativa.isnot(None),
        func.length(PesquisaSatisfacao.alternativa) > 0
    ).all()

    valores = []
    for r in respostas:
        v = r[0].strip()
        if v.isdigit() and 0 <= int(v) <= 10:
            valores.append(int(v))
        elif v in CES_MAP:
            valores.append(CES_MAP[v])

    total = len(valores)

    # Sem respostas
    if total == 0:
        buffer = gerar_pdf_relatorio(
            "Relatório CES",
            ["Não há respostas para o período selecionado."],
            [["Campo", "Valor"], ["Total", "0"]],
            ""
        )
        return send_file(buffer, as_attachment=True, download_name="relatorio_ces.pdf")

    # Cálculos
    media = round(sum(valores) / total, 2)
    percentual = round((media / 10) * 100, 2)

    if percentual < 50: 
        status = "Alto esforço"
    elif percentual < 80: 
        status = "Esforço moderado"
    else: 
        status = "Baixo esforço"

    # Distribuição de frequência
    from collections import Counter
    contagem = Counter(valores)

    labels = [f"Nota {nota}" for nota in contagem.keys()]
    sizes = list(contagem.values())

    # -------- GRÁFICO DE ROSCA COM LEGENDA --------
    fig, ax = plt.subplots(figsize=(7, 6))

    wedges, texts = ax.pie(
        sizes,
        wedgeprops=dict(width=0.4),
        startangle=90
    )

    # Círculo interno para virar rosca
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    fig.gca().add_artist(centre_circle)

    ax.set_title("Distribuição das Notas CES")

    # **Legenda com labels + valores**
    ax.legend(
        wedges,
        [f"{labels[i]} — {sizes[i]} respostas" for i in range(len(labels))],
        title="Notas",
        loc="center left",
        bbox_to_anchor=(1, 0.5)
    )

    grafico_path = "grafico_ces.png"
    fig.savefig(grafico_path, bbox_inches="tight")
    plt.close(fig)

    # Tabela para PDF
    tabela = [
        ["Métrica", "Valor"],
        ["Período", f"{data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}"],
        ["Total respostas", total],
        ["Média", media],
        ["Percentual", f"{percentual}%"],
        ["Classificação", status],
    ]

    texto = [
        "Relatório completo de CES do período informado.",
        "O gráfico exibe a distribuição das notas dadas pelos clientes.",
        "Quanto maior a nota, menor o esforço percebido pelo usuário."
    ]

    buffer = gerar_pdf_relatorio("Relatório CES", texto, tabela, grafico_path)
    return send_file(buffer, as_attachment=True, download_name="relatorio_ces.pdf")



       

def extrair_csat(data_inicio, data_fim):

    CSAT_MAP = {
        'Péssimo': 1, 'Discordo Totalmente': 2, 'Discordo Parcialmente': 3,
        'Neutro': 4, 'Concordo Parcialmente': 5, 'Regular': 6, 'Bom': 7,
        'Concordo': 8, 'Concordo Plenamente': 9, 'Ótimo': 10
    }

    respostas = db.session.query(
        PesquisaSatisfacao.alternativa,
        PesquisaSatisfacao.referencia_chamado
    ).filter(
        PesquisaSatisfacao.data_resposta >= data_inicio,
        PesquisaSatisfacao.data_resposta <= data_fim,
        PesquisaSatisfacao.alternativa.isnot(None),
        func.length(PesquisaSatisfacao.alternativa) > 0
    ).all()

    unicos = {}
    for alt, ref in respostas:
        if ref not in unicos:
            nota = CSAT_MAP.get(alt)
            if nota:
                unicos[ref] = nota

    total = len(unicos)

    if total == 0:
        buffer = gerar_pdf_relatorio(
            "Relatório CSAT",
            ["Nenhum chamado respondeu à pesquisa."],
            [["Campo", "Valor"], ["Total", "0"]],
            ""
        )
        return send_file(buffer, as_attachment=True, download_name="relatorio_csat.pdf")

    satisf = sum(1 for x in unicos.values() if x >= 7)
    csat = round((satisf / total) * 100, 2)

    # --- GERA GRÁFICO ---
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(["Satisfatórios", "Outros"], [satisf, total - satisf])
    ax.set_title("Distribuição CSAT")
    grafico_path = "grafico_csat.png"
    fig.savefig(grafico_path, bbox_inches="tight")
    plt.close(fig)

    tabela = [
        ["Métrica", "Valor"],
        ["Período", f"{data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}"],
        ["Total Chamados", total],
        ["Satisfatórios", satisf],
        ["CSAT", f"{csat}%"],
    ]

    texto = [
        "Relatório completo de CSAT do período informado.",
        "Abaixo estão os indicadores principais."
    ]

    buffer = gerar_pdf_relatorio("Relatório CSAT", texto, tabela, grafico_path)

    return send_file(buffer, as_attachment=True, download_name="relatorio_csat.pdf")

