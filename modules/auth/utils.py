import requests
from settings import endpoints

def authenticate(username, password):
    data = {
        'username': username,
        'password': password
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    url = endpoints.AUTHENTICATE

    try:
        response = requests.post(url, data=data, headers=headers)
        try:
            json_response = response.json()
            access_token = json_response.get("result", {}).get("access_token")

            if access_token:
                return access_token
            else:
                return {
                    "error": "Access token não encontrado",
                    "response": json_response,
                    "status_code": response.status_code
                }
        except ValueError:
            return {
                "error": "Resposta não é JSON",
                "data": response.text,
                "status_code": response.status_code
            }

    except requests.exceptions.RequestException as e:
        return {"error": str(e), "status_code": 500}
    

def authenticate_relatorio(username, password):
    data = {
        'username': username,
        'password': password
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    url = endpoints.AUTHENTICATE

    try:
        response = requests.post(url, data=data, headers=headers)

        try:
            json_response = response.json()
            access_token = json_response.get("result", {}).get("access_token")

            if access_token:
                return {
                    "access_token": access_token,
                    "status_code": response.status_code
                }
            else:
                return {
                    "error": "Access token não encontrado",
                    "response": json_response,
                    "status_code": response.status_code
                }

        except ValueError:
            return {
                "error": "Resposta não é JSON",
                "data": response.text,
                "status_code": response.status_code
            }

    except requests.exceptions.RequestException as e:
        return {"error": str(e), "status_code": 500}

