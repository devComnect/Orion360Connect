from flask import Blueprint, request, render_template, redirect, flash, url_for, current_app, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from application.models import db, User, PerformanceColaboradores
from datetime import datetime
from modules.login.session_manager import SessionManager
import logging

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

        # Buscando todos os administradores
        usuarios_permitidos = User.query.filter_by(is_admin=1).all()

        # Verificando se o usuário está na lista de administradores
        if not any(user.username == username for user in usuarios_permitidos):
            flash('Usuário não autorizado para acessar este sistema.', 'danger')
            return render_template('login.html')

        # Buscando o usuário pelo nome de usuário
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('Usuário não encontrado.', 'danger')
            return render_template('login.html')

        # Verificando a senha
        if user.password == password:
            SessionManager.login_user(user)
            return redirect(url_for('home_bp.render_insights'))
        else:
            flash('Credenciais inválidas. Tente novamente.', 'danger')

    return render_template('login.html')

@login_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    try:
        current_app.logger.info(f"Logout iniciado.")
        SessionManager.logout_user()
        return redirect(url_for('login.login'))
    except Exception as e:
        current_app.logger.error(f"Erro no logout: {e}", exc_info=True)
        return f"Erro interno no logout: {str(e)}", 500

@login_bp.route('/login/colaboradores', methods=['GET', 'POST'])
def login_colaboradores():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if not user:
            print(f'Usuário {username} não foi encontrado no banco de dados.')
            flash('Usuário não encontrado.', 'danger')
            return render_template('login.html')

        if user.password == password:
            print(f"Login bem-sucedido para o usuário {username}")
            login_user(user)
            session['username'] = user.username  # Salva na sessão
            
            OPERADORES_CREDENTIAL = {
                "dneto": 2025,
                "gmaciel": 2022,
                "lkaizer": 2024,
                "msilva" : 2021,
                "esilva" : 2029,
                "gmelo" : 2023,
                "rragga" : 2020,
                "halmeida": 2028,
            }

            operador_id = OPERADORES_CREDENTIAL.get(username)

            # Define a data (ontem)
            hoje = datetime.now().date()

            # Busca os registros no banco
            registros = PerformanceColaboradores.query.filter_by(operador_id=operador_id, data=hoje).all()

            # Inicializa os acumuladores
            acumulado = {
                "ch_atendidas": 0,
                "ch_naoatendidas": 0,
                "tempo_online": 0,
                "tempo_livre": 0,
                "tempo_servico": 0,
                "pimprod_Refeicao": 0,
                "tempo_minatend": None,
                "tempo_medatend": [],
                "tempo_maxatend": None
            }

            for item in registros:
                acumulado["ch_atendidas"] += item.ch_atendidas
                acumulado["ch_naoatendidas"] += item.ch_naoatendidas
                acumulado["tempo_online"] += item.tempo_online
                acumulado["tempo_livre"] += item.tempo_livre
                acumulado["tempo_servico"] += item.tempo_servico
                acumulado["pimprod_Refeicao"] += item.pimprod_refeicao

                if item.tempo_minatend is not None:
                    acumulado["tempo_minatend"] = (
                        item.tempo_minatend
                        if acumulado["tempo_minatend"] is None
                        else min(acumulado["tempo_minatend"], item.tempo_minatend)
                    )

                if item.tempo_maxatend is not None:
                    acumulado["tempo_maxatend"] = (
                        item.tempo_maxatend
                        if acumulado["tempo_maxatend"] is None
                        else max(acumulado["tempo_maxatend"], item.tempo_maxatend)
                    )

                if item.tempo_medatend is not None:
                    acumulado["tempo_medatend"].append(item.tempo_medatend)

            media_geral = (
                sum(acumulado["tempo_medatend"]) / len(acumulado["tempo_medatend"])
                if acumulado["tempo_medatend"] else 0
            )

            dados = {
                "ch_atendidas": acumulado["ch_atendidas"],
                "ch_naoatendidas": acumulado["ch_naoatendidas"],
                "tempo_online": acumulado["tempo_online"],
                "tempo_livre": acumulado["tempo_livre"],
                "tempo_servico": acumulado["tempo_servico"],
                "pimprod_Refeicao": acumulado["pimprod_Refeicao"],
                "tempo_minatend": acumulado["tempo_minatend"] or 0,
                "tempo_medatend": round(media_geral, 2),
                "tempo_maxatend": acumulado["tempo_maxatend"] or 0
            }

            OPERADORES_CONVERSION = {
                "dneto": "Danilo",
                "gmaciel": "Gustavo",
                "lkaizer": "Lucas",
                "msilva" : "Matheus",
                "esilva" : "Rafael",
                "gmelo" : "Raysa",
                "rragga" : "Renato",
                "halmeida": "Henrique",
                "epinheiro": "Eduardo",
                "fzanella": "Fernando",
                "crodrigues" : "Chrysthyanne"
            }

            session['nome'] = OPERADORES_CONVERSION.get(username)

            return redirect(url_for('login.render_login_operadores'))


        else:
            print("Senha incorreta.")
            flash('Credenciais inválidas. Tente novamente.', 'danger')

    return render_template('login_colaboradores.html')

@login_bp.route('/render/colaboradores', methods=['GET'])
def render_login_operadores():
    lista_nivel2 = ['Fernando', 'Eduardo', 'Chrysthyanne', 'Luciano']

    nome = session.get('nome')
    if nome in lista_nivel2:
        return render_template('colaboradores_individual_nivel2.html', nome=nome)

    else:
        return render_template('colaboradores_individual.html', nome=nome)

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


