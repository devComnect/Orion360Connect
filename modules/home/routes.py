from flask import Blueprint, jsonify, render_template, request, redirect, url_for
from flask_login import login_required
import pandas as pd

home_bp = Blueprint('home_bp', __name__)

@home_bp.route('/dashboard', methods=['GET'])
def render_home():
    return render_template('dashboard.html')

@home_bp.route('/', methods=['GET'])
def render_login():
    return render_template('login.html')

@home_bp.route('/admin', methods=['GET'])
def render_admin():
    return render_template('admin.html')

@home_bp.route('/colaboradores', methods=['GET'])
def render_operadores():
    return render_template('colaboradores.html')

@home_bp.route('/insights', methods=['GET'])
def render_insights():
    return render_template('insights.html')

@home_bp.route('/relatorios', methods=['GET'])
def render_relatorio():
    return render_template('relatorios.html')

@home_bp.route('/login', methods=['GET'])
def render_login_colaboradores():
    return render_template('login_colaboradores.html')

@home_bp.route('/okrs', methods=['GET'])
def render_okrs():
    return render_template('okrs.html')

@home_bp.route('/dashboard_colaborador', methods=['GET'])
def render_dashboard_colaborador():
    return render_template('dashboard_colaboradores.html')

@home_bp.route('/performance', methods=['GET'])
def render_performance():
    return redirect(url_for('login.render_login_operadores'))

@home_bp.route('/performance/colaboradoresN2', methods=['GET'])
def render_performance_n2():
    return render_template('colaboradores_individual_nivel2.html')

@home_bp.route('/escala', methods=['GET'])
def render_escala():
    caminho_arquivo = r'C:\Users\Administrator\Desktop\AnalisysData\static\files\Suporte 2026.xlsm'

    # Lê todas as abas da planilha .xlsm
    xls = pd.ExcelFile(caminho_arquivo)
    abas = {}
    for aba in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=aba)
        df.fillna('', inplace=True)
        abas[aba] = df.to_dict(orient='records')

    # Debug para checar dados no console do servidor
    print("Abas encontradas:", list(abas.keys()))
    for aba, dados in abas.items():
        print(f"Aba '{aba}' exemplo:", dados[:2])

    return render_template('escala.html', abas=abas)