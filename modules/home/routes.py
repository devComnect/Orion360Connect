from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required


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