from datetime import timedelta

def formatar_tempo(minutos: float) -> str:
    if minutos < 60:
        return f"{round(minutos)} min"
    elif minutos < 1440:  # 24h * 60
        horas = minutos / 60
        return f"{horas:.1f} h"
    else:
        dias = minutos / 1440
        return f"{dias:.2f} dias"
    

def parse_tempo(s):
    try:
        negativo = s.startswith('-')
        h, m, s = map(int, s.replace('-', '').split(':'))
        delta = timedelta(hours=h, minutes=m, seconds=s)
        return -delta if negativo else delta
    except:
        return None