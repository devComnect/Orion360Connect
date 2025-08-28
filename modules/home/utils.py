from flask import Blueprint, jsonify, render_template, request, redirect, url_for
#from flask_login import login_required
from modules.login.decorators import login_required
from datetime import datetime
import pandas as pd
import os

def carregar_abas_excel(caminho_arquivo, abas_para_ignorar, ordem_meses, como_lista=False):
    """Carrega abas do Excel e retorna no formato pedido (dict ou lista de listas)."""
    if not os.path.isfile(caminho_arquivo):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

    try:
        xls = pd.ExcelFile(caminho_arquivo, engine='openpyxl')
    except Exception as e:
        raise RuntimeError(f"Erro ao abrir o arquivo Excel: {str(e)}")

    abas_validas = [aba for aba in xls.sheet_names if aba not in abas_para_ignorar]
    abas_validas.sort(key=lambda aba: ordem_meses.index(aba) if aba in ordem_meses else 999)

    abas = []
    for aba in abas_validas:
        try:
            # Se for lista de listas -> não define cabeçalho
            if como_lista:
                df = pd.read_excel(xls, sheet_name=aba, header=None)
            else:
                df = pd.read_excel(xls, sheet_name=aba)

                # Converte datas para string
                df = df.applymap(
                    lambda x: x.strftime('%Y-%m-%d') if isinstance(x, (pd.Timestamp, datetime)) and pd.notnull(x) else x
                )

            df.fillna('', inplace=True)
            df.reset_index(drop=True, inplace=True)

            abas.append({
                "nome": aba,
                "dados": df.values.tolist() if como_lista else df.to_dict(orient='records')
            })

        except Exception as e:
            print(f"[ERRO] Falha ao ler aba '{aba}': {e}")
            continue

    return abas
