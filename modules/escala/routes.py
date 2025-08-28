from flask import Blueprint, jsonify, request, send_file
import pandas as pd


escala_bp = Blueprint("escala", __name__, url_prefix="/escala")

@escala_bp.route('/download_original')
def download_original():
    caminho_arquivo = r'C:\Users\Administrator\Desktop\AnalisysData\static\files\SuporteModelo.xlsm'
    return send_file(caminho_arquivo, as_attachment=True, download_name='Suporte.xlsm')

@escala_bp.route('/importar_escala', methods=['POST'])
def importar_escala():
    caminho_destino = r'C:\Users\Administrator\Desktop\AnalisysData\static\files\Suporte.xlsx'

    if 'file' not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400

    arquivo = request.files['file']

    if arquivo.filename == '':
        return jsonify({"erro": "Nome de arquivo inválido"}), 400

    # Verifica extensão
    if not arquivo.filename.lower().endswith(('.xls', '.xlsx', '.xlsm')):
        return jsonify({"erro": "Formato de arquivo não suportado"}), 400

    try:
        # Sobrescreve a planilha existente
        arquivo.save(caminho_destino)
        return jsonify({"mensagem": "Planilha importada com sucesso!"}), 200
    except Exception as e:
        return jsonify({"erro": f"Falha ao salvar arquivo: {str(e)}"}), 500

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
    df.to_excel('Suporte.xlsm', index=False)

    return "Escala atualizada com sucesso!"