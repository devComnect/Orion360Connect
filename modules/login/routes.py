from flask import Blueprint, request, render_template, redirect, flash, url_for, current_app, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from application.models import db, User, PerformanceColaboradores, Guardians, NivelSeguranca
from datetime import datetime
from modules.login.session_manager import SessionManager
from modules.home.routes import render_performance_individual
import logging
from sqlalchemy import func

login_bp = Blueprint('login', __name__)

## ------------------------------------------- Bloco Rotas Login -------------------------------------------------------------------------------------------- ##

@login_bp.route('/', methods=['GET', 'POST'])
def home():
    # Protege a rota com SessionManager
    if not SessionManager.is_authenticated():
        return redirect(url_for('login.login'))
    return render_template('dashboard.html')

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter(func.lower(User.username) == func.lower(username)).first()

        if user and user.password == password:
            # Login de sessão
            SessionManager.login_user(user)  # mantém compatibilidade
            session['user_id'] = user.id
            session['is_authenticated'] = True
            session['is_portal_admin'] = user.is_admin
            session['is_nivel2'] = int(user.is_nivel2 or 0)    # garante int, trata None como 0

            #REDIRECIONA PARA CENTRAL EXTERNA
            session['is_externo'] = bool(user.is_externo)
            if user.is_externo:
                return redirect(url_for('guardians_bp.central_externa'))



            # Vincula ou cria perfil Guardian
            guardian = Guardians.query.filter_by(user_id=user.id).first()
            if not guardian:
                nivel_base = NivelSeguranca.query.order_by(NivelSeguranca.score_minimo.asc()).first()
                if nivel_base:
                    novo_guardian = Guardians(
                        user_id=user.id,
                        nome=user.name or user.username,
                        email=user.email,
                        nivel_id=nivel_base.id
                    )
                    db.session.add(novo_guardian)
                    db.session.commit()
                    flash('Seu perfil de Guardião foi criado!', 'success')
                    guardian = novo_guardian

            session['is_guardian_admin'] = getattr(guardian, "is_admin", False)

            print("DEBUG is_nivel2:", user.is_nivel2, type(user.is_nivel2))
            print(f"DEBUG login: user={user.username}, is_admin={user.is_admin}, is_nivel2={user.is_nivel2} ({type(user.is_nivel2)})")


            # Redireciona baseado na permissão
            if user.is_admin:
                return redirect(url_for('home_bp.render_insights'))
            
            elif user.is_nivel2_user:  # <--- usa a propriedade robusta
                nome, dados = render_performance_individual(username)
                session['nome'] = nome
                session['dados'] = dados
                return redirect(url_for('home_bp.render_performance_n2'))
            
            else:
                # Gera dados do colaborador e salva na sessão
                nome, dados = render_performance_individual(username)
                session['nome'] = nome
                session['dados'] = dados
                return redirect(url_for('home_bp.render_performance'))

        else:
            flash('Credenciais inválidas. Tente novamente.', 'danger')

    return render_template('login.html')

@login_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    try:
        current_app.logger.info("Logout iniciado.")
        # Limpa dados do SessionManager
        SessionManager.logout_user()

        # Limpa variáveis extras da sessão
        session.pop('is_authenticated', None)
        session.pop('is_portal_admin', None)
        session.pop('is_guardian_admin', None)
        session.pop('nome', None)
        session.pop('dados', None)
        current_app.logger.info("Sessão limpa com sucesso.")
        return redirect(url_for('login.home'))

    except Exception as e:
        current_app.logger.error(f"Erro no logout: {e}", exc_info=True)
        return f"Erro interno no logout: {str(e)}", 500

#Depois que juntar tudo apagar
@login_bp.route('/logout/colaboradores', methods=['POST', 'GET'])
def logout_colaboradores():
    try:
        current_app.logger.info(f"Logout iniciado. Usuário autenticado? {current_user.is_authenticated}")
        
        if current_user.is_authenticated:
            logout_user()

        session.pop('username', None)
        return redirect(url_for('home_bp.render_login_colaboradores'))
    
    except Exception as e:
        current_app.logger.error(f"Erro no logout: {e}", exc_info=True)
        return f"Erro interno no logout: {str(e)}", 500
    
@login_bp.route('/setColaboradores', methods=['POST'])
def insert_colaboradores():
    data = request.get_json()

    nome = data.get('nome')
    username = data.get('username')
    email = data.get('email')
    senha = data.get('senha')
    is_admin = str(data.get('nivel_acesso')) == "1"


    if not nome or not username or not email or not senha or not is_admin:
        return jsonify(status='error', message='Todos os campos são obrigatórios!')

    if User.query.filter_by(email=email).first():
        return jsonify(status='error', message='Email já está em uso!')

    if User.query.filter_by(username=username).first():
        return jsonify(status='error', message='Usuário já existe!')

    novo_usuario = User(
        username=username,
        password=senha,
        email=email,
        name=nome,
        is_admin=is_admin    
        )

    db.session.add(novo_usuario)
    db.session.commit()

    return jsonify(status='success', message='Usuário cadastrado com sucesso!')

@login_bp.route('/deleteColaboradores', methods=['POST'])
def delete_colaboradores():
    data = request.get_json()

    email_username = data.get('email-username')
    if not email_username:
        return jsonify(status='error', message='Informe o e-mail ou username para exclusão.')

    # Procura o usuário pelo email ou username
    usuario = User.query.filter(
        (User.email == email_username) | (User.username == email_username)
    ).first()

    if not usuario:
        return jsonify(status='error', message='Usuário não encontrado.')

    try:
        db.session.delete(usuario)
        db.session.commit()
        return jsonify(status='success', message='Usuário excluído com sucesso!')
    except Exception as e:
        db.session.rollback()
        return jsonify(status='error', message='Erro ao excluir usuário: ' + str(e))

@login_bp.route('/updateColaboradores', methods=['POST'])
def update_colaboradores():
    data = request.get_json()

    nome = data.get('nome')
    username = data.get('username')
    email = data.get('email')
    senha = data.get('senha')  # Pode estar em branco
    nivel_acesso = data.get('nivel_acesso')

    if not nome or not username or not email or nivel_acesso is None:
        return jsonify(status='error', message='Todos os campos obrigatórios devem ser preenchidos.')

    # Busca o usuário pelo e-mail
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify(status='error', message='Usuário não encontrado.')

    # Atualiza os dados
    user.name = nome
    user.username = username
    user.is_admin = str(nivel_acesso) == "1" or nivel_acesso == "admin"

    if senha:
        user.password = senha  # Lembre-se: aplicar hash aqui se necessário

    db.session.commit()

    return jsonify(status='success', message='Usuário atualizado com sucesso.')

@login_bp.route('/alterar_senha_colaborador', methods=['POST'])
def update_password():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    username = data.get('username')
    nova_senha = data.get('senha')

    if not username or not nova_senha:
        return jsonify({'error': 'Username e senha são obrigatórios.'}), 400

    colaborador = User.query.filter_by(username=username).first()
    if not colaborador:
        return jsonify({'error': 'Usuário não encontrado.'}), 404

    colaborador.password  = nova_senha
    db.session.commit()

    return jsonify({'message': 'Senha atualizada com sucesso!'})


