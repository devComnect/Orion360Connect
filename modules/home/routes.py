from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, session
#from flask_login import login_required
from modules.login.decorators import login_required, admin_required 
from application.models import db, User, PerformanceColaboradores
from modules.login.session_manager import SessionManager
from datetime import datetime
import pandas as pd
import os
from modules.home.utils import render_performance_individual
from modules.operadores.utils import calcular_performance_colaborador


home_bp = Blueprint('home_bp', __name__)

@home_bp.route('/dashboard', methods=['GET'])
@login_required
def render_home():
    return render_template('dashboard.html')

@home_bp.route('/', methods=['GET'])
def render_login():
    return render_template('login.html')

@home_bp.route('/colaboradores', methods=['GET'])
@login_required
def render_operadores():
    return render_template('colaboradores.html')

@home_bp.route('/insights', methods=['GET'])
@admin_required
def render_insights():
    return render_template('insights.html')

@home_bp.route('/relatorios', methods=['GET'])
@admin_required
def render_relatorio():
    return render_template('relatorios.html')

@home_bp.route('/login/colaboradores', methods=['GET'])
def render_login_colaboradores():
    return render_template('login_colaboradores.html')

@home_bp.route('/okrs', methods=['GET'])
@admin_required
def render_okrs():
    return render_template('okrs.html')

@home_bp.route('/performance', methods=['GET'])
def render_performance():
    nome = session.get("nome") 
    if not nome:
        nome = "Colaborador"  
    dados = calcular_performance_colaborador(nome, 1)  

    return render_template("colaboradores_individual.html", nome=nome, dados=dados)

@home_bp.route('/performance/colaboradoresN2', methods=['GET'])
def render_performance_n2():
    nome = session.get('nome')
    if not nome:
        nome = "Colaborador"  
    dados = calcular_performance_colaborador(nome, 1)  

    return render_template('colaboradores_individual_nivel2.html', nome=nome, dados=dados)

@home_bp.route('/guardians', methods=['GET'])
@login_required
def render_guardians():
    return render_template('guardians.html')

@home_bp.route('/guardiansIndividual', methods=['GET'])
def render_guardians_individual():
    return render_template('guardians_individual.html')

@home_bp.route('/relatoriosIndividual', methods=['GET'])
def render_relatorios_individual():
    return render_template('relatorios_colaboradores_nivel2.html')

@home_bp.route('/register', methods=['GET'])
@admin_required
def render_register():
    return render_template('register.html')

@home_bp.route('/registerColaboradores', methods=['GET'])
def render_register_colaboradores():
    return render_template('register_colaboradores.html')

@home_bp.route('/escala', methods=['GET'])
@login_required
def render_escala():
    caminho_arquivo = r'C:\Users\Administrator\Desktop\AnalisysData\static\files\Suporte.xlsx'
    abas_para_ignorar = {'Escala', 'Configuração', 'Dashboard', 'Ajuda'}

    ordem_meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]

    # ✅ Verificação 1: Arquivo existe?
    if not os.path.isfile(caminho_arquivo):
        return f"Arquivo não encontrado: {caminho_arquivo}", 404

    try:
        # ✅ Carrega planilha (suporta .xlsx e .xlsm)
        xls = pd.ExcelFile(caminho_arquivo, engine='openpyxl')
    except Exception as e:
        return f"Erro ao abrir o arquivo Excel: {str(e)}", 500

    # ✅ Processa abas
    abas_validas = [aba for aba in xls.sheet_names if aba not in abas_para_ignorar]
    abas_validas.sort(key=lambda aba: ordem_meses.index(aba) if aba in ordem_meses else 999)

    abas = []

    for aba in abas_validas:
        try:
            # 🚀 Lê sem cabeçalho, mantém tudo exatamente como está no Excel
            df = pd.read_excel(xls, sheet_name=aba, header=None)

            # Substitui NaN por vazio e reseta index
            df.fillna('', inplace=True)
            df.reset_index(drop=True, inplace=True)

            # Converte para lista de listas (ordem idêntica ao Excel)
            abas.append({
                "nome": aba,
                "dados": df.values.tolist()
            })

        except Exception as e:
            print(f"[ERRO] Falha ao ler aba '{aba}': {e}")
            continue

    return render_template('escala.html', abas=abas)





