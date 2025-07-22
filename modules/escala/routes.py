from flask import Blueprint, jsonify, request, send_file
import pandas as pd


escala_bp = Blueprint("escala", __name__, url_prefix="/escala")

@escala_bp.route('/download_original')
def download_original():
    caminho_arquivo = r'C:\Users\Administrator\Desktop\AnalisysData\static\files\Suporte 2026.xlsm'
    return send_file(caminho_arquivo, as_attachment=True, download_name='Suporte_2026_Original.xlsm')

@escala_bp.route('/salvar-escala', methods=['POST'])
def salvar_escala():
    # 1. Obtemos todas as chaves enviadas no formulário
    dados_form = request.form.to_dict()

    # 2. Descobrimos os índices de linhas e nomes das colunas
    indices_linha = set()
    colunas = set()
    
    for chave in dados_form:
        try:
            i, col = chave.split('_', 1)
            indices_linha.add(int(i))
            colunas.add(col)
        except ValueError:
            continue

    indices_linha = sorted(indices_linha)
    colunas = sorted(colunas)  # opcional

    # 3. Reconstituímos as linhas
    linhas = []
    for i in indices_linha:
        linha = {}
        for col in colunas:
            chave = f"{i}_{col}"
            linha[col] = dados_form.get(k := chave)
        linhas.append(linha)

    # 4. Criamos o DataFrame e salvamos
    df = pd.DataFrame(linhas)
    df.to_excel('Suporte 2026.xlsm', index=False)

    return "Escala atualizada com sucesso!"