from flask import Blueprint, jsonify, request
from modules.auth.utils import authenticate

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/v2/auth', methods=['POST'])
def getToken():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username e password são obrigatórios"}), 400
    
    response = authenticate(username, password)
    
    if "error" in response:
        return jsonify(response), 500
    
    return jsonify(response)