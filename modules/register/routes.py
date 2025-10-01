from flask import Blueprint, jsonify, request
from application.models import db, Turnos, User


register_bp = Blueprint('register_bp', __name__, url_prefix='/register')


@register_bp.route('/registerTurnos', methods=['POST'])
def register_turnos():
    data = request.get_json()
    inicio_turno = data.get('inicio_turno_cadastrar')
    final_turno = data.get('final_turno_cadastrar')
    turnos = data.get('list_turnos')

    if turnos == 'matutino':
        novo_turno = Turnos(
            matutino_inicio = inicio_turno,
            matutino_final = final_turno,
        )
    if turnos == 'vespertino':
        novo_turno = Turnos(
            vespertino_inicio = inicio_turno,
            vespertino_final = final_turno,
            )
    if turnos == 'noturno':
        novo_turno = Turnos(
            noturno_inicio = inicio_turno,
            noturno_final = final_turno,
        )

    db.session.add(novo_turno)
    db.session.commit()

    return jsonify(status='success', message='Turno cadastrado com sucesso!')

@register_bp.route('/editTurnos', methods=['POST'])
def edit_turnos():
    data = request.get_json()
    inicio_turno = data.get('inicio_turno_editar')
    final_turno = data.get('final_turno_editar')
    id_turno = data.get('id_turno_editar')
    turno = data.get('list_turnos_editar')

    turno_query = Turnos.query.filter_by(id=id_turno).first()
    if not turno_query:
        return jsonify(status = 'error', message = 'Turno não encontrado.')
    
    if turno == 'matutino':
        turno_query.matutino_inicio = inicio_turno
        turno_query.matutino_final = final_turno
    if turno == 'vespertino':
        turno_query.vespertino_inicio = inicio_turno
        turno_query.vespertino_final = final_turno
    if turno == 'noturno':
        turno_query.noturno_inicio = inicio_turno
        turno_query.noturno_final = final_turno
    
    db.session.commit()

    return jsonify(status = 'success', message = 'Turno atualizado com sucesso')

@register_bp.route('/deleteTurnos', methods=['POST'])
def delete_turnos():
    data = request.get_json()
    id_turno = data.get('id_turno_exclusao')

    turno_query = Turnos.query.filter_by(id=id_turno).first()

    db.session.delete(turno_query)
    db.session.commit()


    return jsonify(status='success', message='Turno excluido com sucesso.')

@register_bp.route('/getListID', methods=['GET'])
def get_list_id():
    turnos = Turnos.query.all()

    lista_turnos = []

    for turno in turnos:
        if turno.matutino_inicio:
            lista_turnos.append({'id': turno.id, 'periodo': turno.matutino_inicio +'/'+ turno.matutino_final})
        if turno.vespertino_inicio:
            lista_turnos.append({'id': turno.id, 'periodo': turno.vespertino_inicio +'/'+ turno.vespertino_final})
        if turno.noturno_inicio:
            lista_turnos.append({'id': turno.id, 'periodo': turno.noturno_inicio +'/'+ turno.noturno_final})

    return jsonify(lista_turnos)


@register_bp.route('/setColaboradores', methods=['POST'])
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

@register_bp.route('/deleteColaboradores', methods=['POST'])
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

@register_bp.route('/updateColaboradores', methods=['POST'])
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