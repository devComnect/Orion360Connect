import pandas as pd
import pdfkit
import io
import os
import re # Para extrair os dados de resumo
import sys

print("Iniciando gerador de relatório PDF...")

# --- 1. Dados Brutos (Colados do seu TXT) ---

# Dados de Resumo e Legenda
resumo_txt = """
--- ADESÃO GERAL (Plataforma) ---
Total de Guardiões: 14
Total de Quizzes Disponíveis: 33
Total de Perguntas Disponíveis: 121

--- LEGENDA DO SCORE (0-1000) ---
O Score é uma média ponderada de 3 pilares:
  - 30% (300 pts): Adesão de Patrulhas (Consistência)
  - 30% (300 pts): Adesão de Quizzes (Participação)
  - 40% (400 pts): % de Acerto Geral (Qualidade)
"""

# Dados da Tabela (Ranking)
ranking_txt = """
Score (0-1000)       Colaborador   Username  % Acerto Geral  Adesão Patrulhas (%)  Adesão Quizzes (%)  Patrulhas (Feitas) Quizzes (Respondidos)
          839    Fernando Zanella   fzanella           96.84                53.42                96.97                 39                    32
          821 Chrysthyanne Rodrigues crodrigues           93.68                54.79                93.94                 40                    31
          814    Eduardo Pinheiro  epinheiro           87.37                54.79               100.00                 40                    33
          734        Lucas Kaizer    lkaizer           65.93                56.76               100.00                 42                    33
          721          Raysa Melo      gmelo           79.76                45.95                87.88                 34                    29
          689         Fabio Silva     fsilva           80.00                35.06                87.88                 27                    29
          683       Matheus Silva     msilva           70.79                42.47                90.91                 31                    30
          606        Renato Ragga     rragga           67.44                36.23                75.76                 25                    25
          459           lolegario  lolegario           69.35                 0.00                60.61                 15                    20
          433        Rafael Silva     esilva           64.71                27.66                30.30                 13                    10
          432    Henrique Almeida   halmeida           83.78                 7.94                24.24                  5                     8
          428      Gustavo Maciel    gmaciel           82.35                 2.70                30.30                  2                    10
"""

# --- 2. Processamento e Parsing dos Dados ---

try:
    print("Processando dados de resumo...")
    # Extrai os números do resumo usando regex
    stats = {
        'guardioes': re.search(r"Total de Guardiões: (\d+)", resumo_txt).group(1),
        'quizzes': re.search(r"Total de Quizzes Disponíveis: (\d+)", resumo_txt).group(1),
        'perguntas': re.search(r"Total de Perguntas Disponíveis: (\d+)", resumo_txt).group(1)
    }

    print("Processando dados do ranking...")
    # Usa o Pandas para ler a tabela de texto (usando múltiplos espaços como separador)
    # O 'io.StringIO' simula a leitura de um arquivo
    df = pd.read_csv(io.StringIO(ranking_txt), sep=r'\s\s+', engine='python')
    
    # Adiciona a coluna "Pódio" (Ranking)
    podio = ['🥇', '🥈', '🥉']
    df['Rank'] = [podio[i] if i < len(podio) else f'#{i+1}' for i in range(len(df))]
    
    # Reordena colunas para o PDF
    colunas_pdf = [
        'Rank', 
        'Score (0-1000)', 
        'Colaborador', 
        'Username', 
        '% Acerto Geral', 
        'Adesão Patrulhas (%)', 
        'Adesão Quizzes (%)',
        'Patrulhas (Feitas)',
        'Quizzes (Respondidos)'
    ]
    df = df[colunas_pdf]

except Exception as e:
    print(f"Erro ao processar os dados do TXT: {e}")
    print("Verifique se o formato do TXT colado está correto.")
    sys.exit()

# --- 3. Geração do HTML (O Visual) ---

print("Gerando HTML estilizado...")

# Converte o DataFrame do Pandas para uma tabela HTML
# 'escape=False' permite que a gente use os emojis
html_table = df.to_html(index=False, classes='ranking-table', escape=False)

# CSS para deixar o PDF bonito
css_style = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    body {
        font-family: 'Roboto', sans-serif;
        color: #333;
        margin: 0;
        padding: 25px;
        background-color: #f9f9f9;
    }
    
    .container {
        max-width: 1000px;
        margin: auto;
    }
    
    .header {
        text-align: center;
        border-bottom: 2px solid #0056b3;
        padding-bottom: 10px;
        margin-bottom: 25px;
    }
    
    .header h1 {
        color: #0056b3;
        margin: 0;
    }
    
    .header p {
        font-size: 14px;
        color: #777;
    }
    
    .stats-container {
        display: flex; /* Cria a linha de cards */
        justify-content: space-around;
        gap: 20px;
        margin-bottom: 25px;
    }
    
    .stat-card {
        flex-basis: 30%; /* Cada card ocupa ~30% */
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        padding: 20px;
    }
    
    .stat-card h3 {
        margin-top: 0;
        font-size: 18px;
        color: #0056b3;
    }
    
    .stat-card .number {
        font-size: 42px;
        font-weight: 700;
        color: #333;
    }
    
    .legend-box {
        background-color: #f4f8ff;
        border: 1px solid #b3cfff;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 25px;
        font-size: 14px;
    }
    
    .legend-box h2 {
        margin-top: 0;
        color: #0056b3;
        border-bottom: 1px solid #b3cfff;
        padding-bottom: 5px;
    }
    
    .legend-box ul {
        margin: 0;
        padding-left: 20px;
    }
    
    .table-container h2 {
        color: #0056b3;
        text-align: center;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 5px;
    }
    
    .ranking-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    .ranking-table th,
    .ranking-table td {
        border: 1px solid #ddd;
        padding: 10px 8px;
        text-align: left;
    }
    
    .ranking-table th {
        background-color: #0056b3;
        color: white;
        font-weight: 700;
        text-align: center;
    }
    
    .ranking-table tr:nth-child(even) {
        background-color: #f8f8f8;
    }
    
    .ranking-table tr:hover {
        background-color: #e6f0ff;
    }
    
    .ranking-table td:first-child, /* Coluna Rank */
    .ranking-table td:nth-child(2) { /* Coluna Score */
        font-weight: 700;
        text-align: center;
    }
</style>
"""

# Monta o HTML final
html_content = f"""
<html>
<head>
    <meta charset="UTF-8">
    <title>Relatório de Desempenho - Guardians</title>
    {css_style}
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RELATÓRIO DE DESEMPENHO</h1>
            <p>PORTAL GUARDIANS (Gerado em: 17/11/2025 07:08)</p>
        </div>
        
        <!-- Cards de Resumo -->
        <div class="stats-container">
            <div class="stat-card">
                <h3>Total de Guardiões</h3>
                <div class="number">{stats['guardioes']}</div>
            </div>
            <div class="stat-card">
                <h3>Quizzes Disponíveis</h3>
                <div class="number">{stats['quizzes']}</div>
            </div>
            <div class="stat-card">
                <h3>Perguntas Disponíveis</h3>
                <div class="number">{stats['perguntas']}</div>
            </div>
        </div>
        
        <!-- Legenda do Score -->
        <div class="legend-box">
            <h2>Legenda do Score (0-1000)</h2>
            <p>O Score é uma média ponderada de 3 pilares:</p>
            <ul>
                <li><b>30% (300 pts):</b> Adesão de Patrulhas (Consistência)</li>
                <li><b>30% (300 pts):</b> Adesão de Quizzes (Participação)</li>
                <li><b>40% (400 pts):</b> % de Acerto Geral (Qualidade)</li>
            </ul>
        </div>
        
        <!-- Tabela do Ranking -->
        <div class="table-container">
            <h2>Ranking de Desempenho Individual</h2>
            {html_table}
        </div>
        
    </div>
</body>
</html>
"""

# --- 4. Geração do PDF ---

output_pdf = 'relatorio_desempenho_guardians.pdf'

try:
    print(f"Gerando PDF: {output_pdf}...")
    
    # Opções para garantir que o CSS e o layout sejam bem renderizados
    options = {
        'page-size': 'A4',
        'orientation': 'Landscape', # 'Paisagem' para a tabela caber melhor
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'enable-local-file-access': None
    }
    
    # Se você NÃO adicionou o wkhtmltopdf ao PATH, precisa apontar o caminho aqui:
    # path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    # config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    # pdfkit.from_string(html_content, output_pdf, options=options, configuration=config)
    
    # Versão padrão (se estiver no PATH)
    pdfkit.from_string(html_content, output_pdf, options=options)
    
    print(f"\n--- SUCESSO! ---")
    print(f"Relatório '{output_pdf}' gerado com sucesso!")
    print(f"Caminho completo: {os.path.abspath(output_pdf)}")

except Exception as e:
    print(f"Erro ao gerar o PDF: {e}")
    print("Verifique se você instalou o 'wkhtmltopdf' e o adicionou ao PATH do sistema.")