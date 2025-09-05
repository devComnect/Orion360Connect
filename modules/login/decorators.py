from functools import wraps
from flask import redirect, url_for, request, flash, session

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_authenticated'):
            flash('Você precisa estar logado para acessar esta página.', 'warning')
            return redirect(url_for('login.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_authenticated'):
            flash('Você precisa estar logado para acessar esta página.', 'warning')
            return redirect(url_for('login.login', next=request.url))
        
        if not session.get('is_portal_admin'):
            flash('Acesso restrito a administradores.', 'danger')
            return redirect(url_for('home_bp.render_performance'))
        
        return f(*args, **kwargs)
    return decorated_function
