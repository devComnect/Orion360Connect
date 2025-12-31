from functools import wraps
from flask import redirect, url_for, request, flash, session
from .session_manager import SessionManager
from application.models import User, Guardians

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

###
def guardian_admin_required(f):
    """
    Verifica se o usuário está logado E se ele é um Admin do Portal OU um Admin do Guardians.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not SessionManager.is_authenticated():
            flash('Você precisa estar logado para acessar essa página.', 'warning')
            return redirect(url_for('login.login', next=request.url))

        user_id = SessionManager.get('user_id')
        user = User.query.get(user_id)

        if not user:
            flash('Sessão inválida. Por favor, faça o login novamente.', 'danger')
            return redirect(url_for('login.login'))

        guardian = Guardians.query.filter_by(user_id=user.id).first()
        
        is_portal_admin = user.is_admin
        is_n2_user = user.is_nivel2
        is_guardian_admin = guardian.is_admin if guardian else False

        if is_portal_admin or is_n2_user or is_guardian_admin:
            return f(*args, **kwargs) # Permite o acesso

        # Se não for nenhum dos três, bloqueia.
        flash('Você não tem permissão de administrador para acessar esta área.', 'danger')
        return redirect(url_for('home_bp.render_performance'))

    return decorated_function