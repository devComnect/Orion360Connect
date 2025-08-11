from functools import wraps
from flask import redirect, url_for, request
from modules.login.session_manager import SessionManager

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not SessionManager.is_authenticated():
            # Pode ajustar a rota de login conforme seu blueprint
            return redirect(url_for('login.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

'''# Lista de usuários autorizados
USUARIOS_AUTORIZADOS = ['fsilva', 'avaz', 'lolegario']

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not SessionManager.is_authenticated():
            flash('Você precisa estar logado para acessar essa página.', 'warning')
            return redirect(url_for('login.login', next=request.url))

        username = SessionManager.get('username')
        if username not in USUARIOS_AUTORIZADOS:
            flash('Você não tem permissão para acessar essa página.', 'danger')
            return redirect(url_for('home_bp.render_login'))  # ou outra página segura

        return f(*args, **kwargs)
    return decorated_function'''
