from functools import wraps
from flask import redirect, url_for, request, flash
from modules.login.session_manager import SessionManager
from application.models import User


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not SessionManager.is_authenticated():
            flash('Você precisa estar logado para acessar essa página.', 'warning')
            return redirect(url_for('login.login', next=request.url))

        # Busca o ID do usuário na sessão
        user_id = SessionManager.get('user_id')
        if not user_id:
            flash('Sessão inválida. Por favor, faça o login novamente.', 'danger')
            return redirect(url_for('login.login'))

        # Busca o usuário no banco de dados a cada requisição
        user = User.query.get(user_id)

        # Verifica se o usuário existe e se é um administrador
        if not user or not user.is_admin:
            flash('Você nao tem permissão para acessar essa página.', 'danger')
            SessionManager.logout_user() # Limpa a sessão por segurança
            return redirect(url_for('login.login'))

        return f(*args, **kwargs)
    return decorated_function
