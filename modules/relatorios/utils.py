from datetime import datetime, time, timedelta

cores_por_turno = {
    "07:00/16:00": "#4CAF50",
    "09:30/18:30": "#2196F3",
    "10:00/19:00": "#FF9800",
    "13:00/22:00": "#9C27B0",
    "22:00/07:00": "#CD5C5C",
    "06:00/15:00": "#009688",       # Exemplo novo turno
    "12:00/21:00": "#3F51B5",       # Outro exemplo
    "08:00/17:00": "#795548",       # Outro exemplo
}

def get_turno(dt):
    if not isinstance(dt, datetime):
        raise ValueError("A data deve ser do tipo datetime")

    hora = dt.time()

    if time(7, 0) <= hora < time(16, 0):
        return "07:00/16:00"
    elif time(9, 0) <= hora < time(18, 0):
        return "09:30/18:30"
    elif time(10, 0) <= hora < time(19, 0):
        return "10:00/19:00"
    elif time(13, 0) <= hora < time(22, 0):
        return "13:00/22:00"
    else:
        # Esse intervalo cobre de 22:00 até 07:00 do dia seguinte
        return "22:00/07:00"

def get_turno_ligacao(hora_str):
    from datetime import datetime
    h, m, s = map(int, hora_str.split(":"))
    hora = h + m / 60 + s / 3600

    if 7 <= hora < 16:
        return "07:00/16:00"
    elif 9 <= hora < 18:
        return "09:30/18:30"
    elif 10 <= hora < 19:
        return "10:00/19:00"
    elif 13 <= hora < 22:
        return "13:00/22:00"
    else:
        return "22:00/07:00"


def is_hora_valida(hora_str):
    try:
        if not hora_str or len(hora_str) < 5:
            return False
        hora = hora_str.strip().split(" ")[0]
        datetime.strptime(hora, '%H:%M:%S')
        return True
    except:
        return False
    

def _parse_duration_to_timedelta(duracao_str):
    """Ex: '00:12:30' -> timedelta(minutes=12, seconds=30)"""
    try:
        h, m, s = map(int, duracao_str.split(':'))
        return timedelta(hours=h, minutes=m, seconds=s)
    except Exception:
        return timedelta(0)