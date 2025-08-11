from functools import wraps
from flask import redirect, url_for, request, flash
from modules.login.session_manager import SessionManager


USUARIOS_AUTORIZADOS = ['fsilva', 'avaz', 'lolegario']

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not SessionManager.is_authenticated():
            flash('Você precisa estar logado para acessar essa página.', 'warning')
            return redirect(url_for('login.login', next=request.url))

        username = SessionManager.get('username')
        if not username or username.strip().lower() not in [u.lower() for u in USUARIOS_AUTORIZADOS]:
            flash('Você não tem permissão para acessar essa página.', 'danger')
            return redirect(url_for('home_bp.render_login'))

        return f(*args, **kwargs)
    return decorated_function
