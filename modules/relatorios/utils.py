from datetime import time

def get_turno(dt):
    hora = dt.time()
    if time(7, 0) <= hora < time(16, 0):
        return "07:00/16:00"
    elif time(13, 0) <= hora < time(22, 0):
        return "13:00/22:00"
    else:
        return "22:00/07:00"