import requests
from settings import endpoints

def get_filas(token, id):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    url = f'{endpoints.QUEUES}{id}/status'

    try:
        response = requests.get(url, headers=headers)
        
        try:
            json_response = response.json()
            return json_response  
        
        except ValueError:  
            return {
                "status_code": response.status_code,
                "data": response.text  
            }
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "status_code": 500}
