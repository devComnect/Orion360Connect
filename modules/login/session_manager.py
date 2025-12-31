from flask import session

class SessionManager:
    @staticmethod
    def login_user(user):
        """
        Armazena informações do usuário na sessão para indicar que está logado.
        """
        session['user_id'] = user.id
        session['username'] = user.username.strip().lower()
        session['logged_in'] = True

    @staticmethod
    def logout_user():
        """
        Limpa a sessão, removendo os dados do usuário.
        """
        session.clear()

    @staticmethod
    def is_authenticated():
        """
        Verifica se o usuário está autenticado pela sessão.
        """
        return session.get('logged_in', False)

    @staticmethod
    def get_current_user():
        """
        Retorna o nome de usuário atual, se estiver autenticado.
        """
        if SessionManager.is_authenticated():
            return session.get('username')
        return None
    
    @staticmethod
    def get(key, default=None):
        return session.get(key, default)
