from application.models import ServiceOrder, db
from datetime import datetime, timedelta

def atualizar_service_order(cod_chamado, data_criacao, restante1, restante2, status_nome, operador):
    status_normalizado = (status_nome or "").strip().lower()

    if status_normalizado in ["resolvido", "cancelado"]:
        service_order = ServiceOrder.query.filter_by(SERVICEID=cod_chamado).first()
        if service_order:
            db.session.delete(service_order)
        return  

    service_status = 1  

    dg_user = {
        'Renato': 1011, 'Matheus': 1012, 'Gustavo': 1014, 'Raysa': 1015,
        'Lucas': 1016, 'Danilo': 1013, 'Henrique': 1018, 'Rafael': 1017,
        'Chrysthyanne': 1024, 'Eduardo': 1023, 'Fernando': 1022,
        'Alexandre': 1030, 'Reinaldo': 1025, 'Fábio': 1021, 'Luciano': 1026,
    }

    operador_normalizado = (operador or "").strip().title()
    dg_user_id = dg_user.get(operador_normalizado, 9999)

    try:
        if restante1 and ":" in restante1:
            h, m, s = map(int, restante1.split(":"))
            triagem_segundos = h * 3600 + m * 60 + s
        else:
            triagem_segundos = 0

        SVC_TRIAGEM = data_criacao + timedelta(seconds=triagem_segundos)
    except:
        SVC_TRIAGEM = datetime.now()

    service_order = ServiceOrder.query.filter_by(SERVICEID=cod_chamado).first()

    if service_order:
        service_order.DGUSERID = dg_user_id
        service_order.SVC_ORDER_TRIAGEM = SVC_TRIAGEM
        service_order.SERVICE_ORDER_STS = service_status
    else:
        db.session.add(ServiceOrder(
            SERVICEID=cod_chamado,
            DGUSERID=dg_user_id,
            SVC_ORDER_TRIAGEM=SVC_TRIAGEM,
            SERVICE_ORDER_STS=service_status
        ))

def gerar_intervalos(data_inicial, data_final, tamanho=15):
    atual = data_inicial
    while atual <= data_final:
        proximo = min(atual + timedelta(days=tamanho - 1), data_final)
        yield (atual, proximo)
        atual = proximo + timedelta(days=1)

def data_valida(data_str):
    return data_str and data_str != "0000-00-00"

def parse_data(data_str):
    try:
        return datetime.strptime(data_str, "%Y-%m-%d").date()
    except:
        return None
    
def parse_hora(hora_str):
    if hora_str and hora_str not in ["-", ""]:
        try:
            return datetime.strptime(hora_str, "%H:%M:%S").time()
        except ValueError:
            return None
    return None

