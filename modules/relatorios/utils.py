from datetime import datetime, time

def get_turno(dt):
    # Certificando-se de que a entrada seja datetime
    if not isinstance(dt, datetime):
        raise ValueError("A data deve ser do tipo datetime")
    
    hora = dt.hour  # Obtém a hora diretamente como um inteiro

    # Verifica em qual intervalo a hora se encaixa
    if 7 <= hora < 13:
        return "07:00/16:00"
    elif 13 <= hora < 22:
        return "13:00/22:00"
    else:
        return "22:00/07:00"