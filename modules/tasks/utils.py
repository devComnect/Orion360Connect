from application.models import ServiceOrder, db
from datetime import datetime, timedelta

# Função que persiste os dados na tabela de service_order Projeto DelGrande
def atualizar_service_order(cod_chamado, data_criacao, restante1, restante2, status_nome, operador):
    """
    Atualiza ou cria um registro ServiceOrder com base no chamado recebido.
    O cod_chamado aqui JÁ CHEGA sem traço (limpo).
    """

    # 0 = resolvido/cancelado | 1 = aberto/em andamento
    service_status = 0 if status_nome in ["resolvido", "cancelado"] else 1

    # Dicionário de operadores -> ramal
    dg_user = {
        'Renato': 1020,
        'Matheus': 1021, 
        'Gustavo': 1022,
        'Raysa': 1023,
        'Lucas': 1024,
        'Danilo': 1025,
        'Henrique': 1028,
        'Rafael': 1029, 
        'Chrysthyanne': 1016,
        'Eduardo': 1018,
        'Fernando': 1019,
        'Alexandre': 1030,
        'Reinaldo': 1015,
        'Fábio': 1014,
        'Luciano': 1017,
    }

    operador_normalizado = (operador or "").strip().title()
    dg_user_id = dg_user.get(operador_normalizado)

    if dg_user_id is None:
        print(f"[AVISO] Operador não encontrado no dicionário: {operador_normalizado}")
        dg_user_id = 9999  # fallback seguro

    triagem_segundos = 0

    try:
        if restante1 and ":" in restante1:
            h, m, s = map(int, restante1.split(":"))
            triagem_segundos += h*3600 + m*60 + s

        if restante2 and ":" in restante2:
            h, m, s = map(int, restante2.split(":"))
            triagem_segundos += h*3600 + m*60 + s

        SVC_TRIAGEM = data_criacao + timedelta(seconds=triagem_segundos)

    except Exception:
        SVC_TRIAGEM = datetime.now()

    # Buscar service order existente
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
    """
    Gera tuplas (data_inicio, data_fim) em blocos de no máximo 'tamanho' dias.
    """
    atual = data_inicial
    while atual <= data_final:
        proximo = min(atual + timedelta(days=tamanho - 1), data_final)
        yield (atual, proximo)
        atual = proximo + timedelta(days=1)

def data_valida(data_str):
    return data_str and data_str != "0000-00-00"


def parse_data(data_str):
    """Converte string no formato 'YYYY-MM-DD' para datetime.date"""
    try:
        return datetime.strptime(data_str, "%Y-%m-%d").date()
    except:
        return None
    
def parse_hora(hora_str):
    """
    Converte uma string de hora 'HH:MM:SS' em datetime.time.
    Retorna None se o valor for vazio ou inválido.
    """
    if hora_str and hora_str not in ["-", ""]:
        try:
            return datetime.strptime(hora_str, "%H:%M:%S").time()
        except ValueError:
            return None
    return None