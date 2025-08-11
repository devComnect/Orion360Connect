
# Endpoints globais DelGrande

AUTHENTICATE = "http://192.168.10.35:9444/v2/auth"

QUEUES = 'http://192.168.10.35:9444/v2/queues/'

REPORT = 'http://192.168.10.35:9444/v2/report/call_detailing'

LOGIN_LOGOFF = 'http://192.168.10.35:9444/v2/report/login_logoff'

CHAMADA_SAIDA = 'http://192.168.10.35:9444/v2/report/call_detailing_outgoing'

PERFORMANCE_ATENDENTES = 'http://192.168.10.35:9444/v2/report/attendants_performance'

EVENTOS_ATENDENTES = 'http://192.168.10.35:9444/v2/report/attendants_events'

# Credenciais Del Grande URA
CREDENTIALS = {
    'username' : 'integracao',
    'password' : '@Comnect'
}

# Credenciais do usuário API integração Desk Manager
CREDENTIALS_DESK = {
    'Authorization' : '59879d491404a96c3e2f3e2c0daab21486df169e',
    'PublicKey' : '1557725d2f04eabdfbc46fb7e589389a2ff7c0da'
}


# Endpoints globais Desk Manager
AUTHENTICATE_DESK = 'https://api.desk.ms/Login/autenticar'

LISTACHAMADOS = 'https://api.desk.ms/Chamados/lista'

LISTA_CHAMADOS_SUPORTE = 'https://api.desk.ms/ChamadosSuporte/lista'

RELATORIO_CHAMADOS_SUPORTE = 'https://api.desk.ms/Relatorios/imprimir'

LISTA_OPERADORES = 'https://api.desk.ms/Operadores/lista'

LISTA_GRUPOS = 'https://api.desk.ms/Grupos/lista'