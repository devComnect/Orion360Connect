import requests
from settings import endpoints
from modules.deskmanager.authenticate.routes import token_desk
from flask import jsonify, request


def verificarFilho(chave):
    try:
        token_response = token_desk()
        if not token_response:
            return jsonify({"status": "error", "message": "Falha na autenticação"}), 401
        
        payload = {
            "Chave": f'{chave}'
            } 
        
        response = requests.post(
            'https://api.desk.ms/ChamadosSuporte/vincular',
            headers={'Authorization': f'{token_response}', 'Content-Type': 'application/json'},
            json=payload,
        )
    except:
        Exception

    return response