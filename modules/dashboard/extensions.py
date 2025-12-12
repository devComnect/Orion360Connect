# Extendions para que seja possível o resgate de informações

tipos_desejados = ['000003', '000101', '000004', '000060', '000001', '000071']
mapeamento_tipos = {
    '000101': 'Portal Comnect',
    '000071': 'Interno',
    '000003': 'E-mail',
    '000004': 'Telefone',
    '000001': 'Portal Solicitante',
    '000060': 'WhatsApp'
}
cores = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
grupos_desejados = ['INFOSEC', 'DEV', 'NOC', 'CSM', 'SUPORTE TI']


payload = {
        "Pesquisa": "",
        "Tatual": "",
        "Ativo": "NaFila",
        "StatusSLA": "S",
        "Colunas": {
            "Chave": "on",
            "CodChamado": "on",
            "NomePrioridade": "on",
            "DataCriacao": "on",
            "HoraCriacao": "on",
            "DataFinalizacao": "on",
            "HoraFinalizacao": "on",
            "DataAlteracao": "on",
            "HoraAlteracao": "on",
            "NomeStatus": "on",
            "Assunto": "on",
            "Descricao": "on",
            "ChaveUsuario": "on",
            "NomeUsuario": "on",
            "SobrenomeUsuario": "on",
            "NomeCompletoSolicitante": "on",
            "SolicitanteEmail": "on",
            "NomeOperador": "on",
            "SobrenomeOperador": "on",
            "TotalAcoes": "on",
            "TotalAnexos": "on",
            "Sla": "on",
            "CodGrupo": "on",
            "NomeGrupo": "on",
            "CodSolicitacao": "off",
            "CodSubCategoria": "off",
            "CodTipoOcorrencia": "off",
            "CodCategoriaTipo": "off",
            "CodPrioridadeAtual": "off",
            "CodStatusAtual": "off"
        },
        "Ordem": [{
            "Coluna": "Chave",
            "Direcao": "true"
        }]
    }