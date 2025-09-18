from datetime import datetime, time

def get_turno(dt):
    if not isinstance(dt, datetime):
        raise ValueError("A data deve ser do tipo datetime")

    hora = dt.time()

    if time(7, 0) <= hora < time(13, 0):
        return "07:00/16:00"
    elif time(13, 0) <= hora < time(22, 0):
        return "13:00/22:00"
    else:
        # Esse intervalo cobre de 22:00 até 07:00 do dia seguinte
        return "22:00/07:00"

def get_turno_ligacao(hora_str):
    from datetime import datetime
    h, m, s = map(int, hora_str.split(":"))
    hora = h + m / 60 + s / 3600

    if 7 <= hora < 13:
        return "07:00/16:00"
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