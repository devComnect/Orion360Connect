from flask import Blueprint, jsonify, request, render_template, redirect
from settings import endpoints
import requests
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__, url_prefix='/api')

@auth_bp.route('/autenticar', methods=['POST'])
def token_desk():        
    headers = {
        'Authorization': endpoints.CREDENTIALS_DESK['Authorization'],
        'Content-Type': 'application/json'
    }
    
    data = {
        "PublicKey": endpoints.CREDENTIALS_DESK['PublicKey']
    }

    try:
        response = requests.post(endpoints.AUTHENTICATE_DESK, headers=headers, json=data)
        
        if response.status_code == 200:
            # Retorna apenas o token como string
            return response.text.strip('"')
        else:
            return jsonify({
                "error": "Falha na autenticação",
                "status_code": response.status_code,
                "response": response.text
            }), response.status_code
               
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
