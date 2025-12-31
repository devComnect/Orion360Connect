from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
#from flask_login import login_required
from modules.login.decorators import login_required
from application.models import db, User, PerformanceColaboradores
from modules.login.session_manager import SessionManager
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


def render_performance_individual(username_view):
    """
    Busca os dados de performance de um colaborador específico (se fornecido na URL),
    ou do colaborador logado.
    """
    from datetime import datetime

    target_username = username_view or SessionManager.get("username")

    if not target_username:
        flash("Sessão inválida ou nome de usuário não fornecido.", "warning")
        return redirect(url_for('login.login'))

    # Dicionários de mapeamento
    OPERADORES_CREDENTIAL = {
        "dneto": 2025, "gmaciel": 2022, "lkaizer": 2024, "msilva": 2021,
        "esilva": 2029, "gmelo": 2023, "rragga": 2020, "halmeida": 2028,
        "epinheiro": "Eduardo", "fzanella": "Fernando", "crodrigues": "Chrysthyanne"
    }
    OPERADORES_CONVERSION = {
        "dneto": "Danilo", "gmaciel": "Gustavo", "lkaizer": "Lucas", "msilva": "Matheus",
        "esilva": "Rafael", "gmelo": "Raysa", "rragga": "Renato", "halmeida": "Henrique",
        "epinheiro": "Eduardo", "fzanella": "Fernando", "crodrigues": "Chrysthyanne"
    }

    operador_id = OPERADORES_CREDENTIAL.get(target_username)
    nome_exibicao = OPERADORES_CONVERSION.get(target_username, target_username)

    # Preenche valores padrão (sempre definidos!)
    nome = nome_exibicao
    dados = {
        "ch_atendidas": 0, "ch_naoatendidas": 0, "tempo_online": 0,
        "tempo_livre": 0, "tempo_servico": 0, "pimprod_Refeicao": 0,
        "tempo_minatend": 0, "tempo_medatend": 0, "tempo_maxatend": 0
    }

    # Só busca se tiver operador_id
    if operador_id:
        hoje = datetime.now().date()
        registros = PerformanceColaboradores.query.filter_by(operador_id=operador_id, data=hoje).all()

        if registros:
            acumulado = {
                "ch_atendidas": 0, "ch_naoatendidas": 0, "tempo_online": 0,
                "tempo_livre": 0, "tempo_servico": 0, "pimprod_Refeicao": 0,
                "tempo_minatend": None, "tempo_medatend": [], "tempo_maxatend": None
            }

            for item in registros:
                acumulado["ch_atendidas"] += item.ch_atendidas or 0
                acumulado["ch_naoatendidas"] += item.ch_naoatendidas or 0
                acumulado["tempo_online"] += item.tempo_online or 0
                acumulado["tempo_livre"] += item.tempo_livre or 0
                acumulado["tempo_servico"] += item.tempo_servico or 0
                acumulado["pimprod_Refeicao"] += item.pimprod_refeicao or 0

                if item.tempo_minatend is not None:
                    if acumulado["tempo_minatend"] is None or item.tempo_minatend < acumulado["tempo_minatend"]:
                        acumulado["tempo_minatend"] = item.tempo_minatend

                if item.tempo_maxatend is not None:
                    if acumulado["tempo_maxatend"] is None or item.tempo_maxatend > acumulado["tempo_maxatend"]:
                        acumulado["tempo_maxatend"] = item.tempo_maxatend

                if item.tempo_medatend is not None:
                    acumulado["tempo_medatend"].append(item.tempo_medatend)

            media_geral = (sum(acumulado["tempo_medatend"]) / len(acumulado["tempo_medatend"])) if acumulado["tempo_medatend"] else 0

            dados.update({
                "ch_atendidas": acumulado["ch_atendidas"],
                "ch_naoatendidas": acumulado["ch_naoatendidas"],
                "tempo_online": acumulado["tempo_online"],
                "tempo_livre": acumulado["tempo_livre"],
                "tempo_servico": acumulado["tempo_servico"],
                "pimprod_Refeicao": acumulado["pimprod_Refeicao"],
                "tempo_minatend": acumulado["tempo_minatend"] or 0,
                "tempo_medatend": round(media_geral, 2),
                "tempo_maxatend": acumulado["tempo_maxatend"] or 0
            })

    return nome, dados
