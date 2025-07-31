import requests, json
import settings.endpoints as endpoints
from urllib.parse import urlencode
from application.models import db, DesempenhoAtendente, DesempenhoAtendenteVyrtos, PerformanceColaboradores, Chamado, Categoria, PesquisaSatisfacao, RelatorioColaboradores
from modules.delgrande.auth.utils import authenticate, authenticate_relatorio
from modules.deskmanager.authenticate.routes import token_desk
import modules.delgrande.relatorios.utils as utils
from settings.endpoints import CREDENTIALS, RELATORIO_CHAMADOS_SUPORTE
from flask import jsonify, current_app as app
import json
from datetime import timedelta, datetime


def get_relatorio(token, params):
    base_url = endpoints.REPORT

    # Montagem manual da URL com os parâmetros esperados pela API
    url = (
        f"{base_url}"
        f"?initial_date={params.initial_date}"
        f"&initial_hour={params.initial_hour}"
        f"&final_date={params.final_date}"
        f"&final_hour={params.final_hour}"
        f"&fixed={params.fixed}"
        f"&week={params.week}"
        f"&options={params.options}"
        f"&queues={params.queues}"
        f"&agents={params.agents}"
        f"&transfer_display={params.transfer_display}"
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "status_code": getattr(e.response, "status_code", 500),
            "url": url
        }

def get_relatorio_login_logoff(token, params):
    base_url = endpoints.LOGIN_LOGOFF

    # Serializar corretamente a lista de semana e agentes
    week = params.week.replace(" ", "")  # "1,2,3,4,5"
    agents = params.agents.replace(" ", "")  # "1001,1002"

    # Converter string JSON do options para URL-encoded (com segurança)
    try:
        options = json.loads(params.options)
        options_encoded = json.dumps(options)
    except Exception:
        options_encoded = "{}"

    # Montar a URL manualmente
    url = (
        f"{base_url}"
        f"?initial_date={params.initial_date}"
        f"&initial_hour={params.initial_hour}"
        f"&final_date={params.final_date}"
        f"&final_hour={params.final_hour}"
        f"&fixed={params.fixed}"
        f"&week={week}"
        f"&options={options_encoded}"
        f"&agents={agents}"
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "status_code": getattr(e.response, "status_code", 500),
            "url": url
        }

def get_chamada_saida(token, params):
    base_url = endpoints.CHAMADA_SAIDA

    # Serializar corretamente a lista de semana e agentes
    week = params.week.replace(" ", "")
    agents = params.agents.replace(" ", "")

    # Converter string JSON do options para URL-encoded (com segurança)
    try:
        options = json.loads(params.options)
        options_encoded = json.dumps(options)
    except Exception:
        options_encoded = "{}"

    # Montar a URL manualmente
    url = (
        f"{base_url}"
        f"?initial_date={params.initial_date}"
        f"&initial_hour={params.initial_hour}"
        f"&final_date={params.final_date}"
        f"&final_hour={params.final_hour}"
        f"&fixed={params.fixed}"
        f"&week={week}"
        f"&conf={params.conf}"
        f"&options={options_encoded}"
        f"&agents={agents}"
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "status_code": getattr(e.response, "status_code", 500),
            "url": url
        }

def atendentePerformance(token, params):
    base_url = endpoints.PERFORMANCE_ATENDENTES

    query_params = {
        "initial_date": params.initial_date,
        "initial_hour": params.initial_hour,
        "final_date": params.final_date,
        "final_hour": params.final_hour,
        "week": params.week,
        "fixed": params.fixed,
        "conf": params.conf,
        "agents": params.agents,
        "queues": params.queues,
        "options": params.options
    }

    # Transforma dicionários em strings JSON antes de passar para requests
    for key in ["options", "conf", "agents",  "initial_date", "final_date"]:
        if isinstance(query_params[key], (dict, list)):
            query_params[key] = json.dumps(query_params[key])

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(base_url, headers=headers, params=query_params)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "status_code": getattr(e.response, "status_code", 500),
            "url": base_url
        }

'''def atendentePerformanceVyrtos(token, params):
    base_url = endpoints.PERFORMANCE_ATENDENTES

    query_params = {
        "initial_date": params.initial_date,
        "initial_hour": params.initial_hour,
        "final_date": params.final_date,
        "final_hour": params.final_hour,
        "week": params.week,
        "fixed": params.fixed,
        "agents": params.agents,  # NÃO em JSON
        "queues": params.queues,  # NÃO em JSON
        "options": params.options,
        "conf": params.conf
    }

    # Somente `options` e `conf` são enviados como JSON strings
    for key in ["options", "conf"]:
        if isinstance(query_params[key], (dict, list)):
            query_params[key] = json.dumps(query_params[key])

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(base_url, headers=headers, params=query_params)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "status_code": getattr(e.response, "status_code", 500),
            "url": base_url
        }'''

def gerar_intervalos(data_inicial, data_final, tamanho=15):
    """
    Gera tuplas (data_inicio, data_fim) em blocos de no máximo 'tamanho' dias.
    """
    atual = data_inicial
    while atual <= data_final:
        proximo = min(atual + timedelta(days=tamanho - 1), data_final)
        yield (atual, proximo)
        atual = proximo + timedelta(days=1)

def processar_e_armazenar_performance(dias=180, incremental=False):
    hoje = datetime.now().date()
    ontem = hoje - timedelta(days=1)
    
    if dias != 180 and not incremental:
        raise ValueError("Somente o intervalo de 180 dias é permitido para carga completa.")

    # Autenticação
    auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
    if "access_token" not in auth_response:
        return {"status": "error", "message": "Falha na autenticação"}
    access_token = auth_response["access_token"]

    # Datas de busca
    data_inicial = hoje - timedelta(days=dias - 1)
    data_final = hoje

    # IDs e nomes dos operadores
    OPERADORES_MAP = {
        2020: "Renato",
        2021: "Matheus",
        2022: "Gustavo",
        2023: "Raysa",
        2024: "Lucas",
        2025: "Danilo",
        2028: "Henrique",
        2029: "Rafael"
    }

    operadores_ids = list(OPERADORES_MAP.keys())

    # Limpa somente se for carga completa
    if not incremental:
        try:
            PerformanceColaboradores.query.delete()
            db.session.commit()
            print("Tabela de PerformanceColaboradores limpa com sucesso.")
        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": f"Erro ao limpar a tabela: {str(e)}"}

    for operador_id in operadores_ids:
        nome_operador = OPERADORES_MAP.get(operador_id, "Desconhecido")

        for inicio, fim in gerar_intervalos(data_inicial, data_final, tamanho=15):  # usar intervalos menores
            offset = 0
            total_registros = 0

            while True:
                params = {
                    "initial_date": inicio.strftime('%Y-%m-%d'),
                    "final_date": fim.strftime('%Y-%m-%d'),
                    "initial_hour": "00:00:00",
                    "final_hour": "23:59:59",
                    "fixed": 0,
                    "week": [],
                    "agents": [operador_id],
                    "queues": [1],
                    "options": {"sort": {"data": 1}, "offset": offset, "count": 1000},
                    "conf": {}
                }

                print(f"[{nome_operador}] Buscando {inicio} até {fim}, offset {offset}")
                response = utils.atendentePerformanceData(access_token, params)
                dados = response.get("result", {}).get("data", [])

                if not dados:
                    break

                for item in dados:
                    try:
                        data_registro = datetime.strptime(item["data"], "%Y-%m-%d").date()

                        # Evita duplicidade se incremental
                        if incremental:
                            exists = PerformanceColaboradores.query.filter_by(
                                operador_id=operador_id,
                                data=data_registro
                            ).first()
                            if exists:
                                continue

                        registro = PerformanceColaboradores(
                            name=nome_operador,
                            operador_id=operador_id,
                            data=data_registro,
                            ch_atendidas=item.get("ch_atendidas", 0),
                            ch_naoatendidas=item.get("ch_naoatendidas", 0),
                            tempo_online=item.get("tempo_online", 0),
                            tempo_livre=item.get("tempo_livre", 0),
                            tempo_servico=item.get("tempo_servico", 0),
                            pimprod_refeicao=item.get("pimprod_Refeicao", 0),
                            tempo_minatend=item.get("tempo_minatend"),
                            tempo_medatend=item.get("tempo_medatend"),
                            tempo_maxatend=item.get("tempo_maxatend"),
                            data_importacao=datetime.now()
                        )
                        db.session.add(registro)
                        total_registros += 1
                    except Exception as e:
                        print(f"[ERRO] {nome_operador} em {item.get('data')}: {str(e)}")

                db.session.flush()
                offset += 1000  # Próxima página

            print(f"[{nome_operador}] Total inserido de {inicio} a {fim}: {total_registros}")

        db.session.commit()

    return {"status": "success", "message": "Dados inseridos com sucesso (modo incremental)." if incremental else "Carga completa realizada com sucesso."}

def processar_e_armazenar_performance_incremental():
    try:
        # Datas: hoje e 2 dias atrás
        hoje = datetime.now().date()
        data_inicio = hoje - timedelta(days=2)  # 2 dias atrás
        
        # Autenticação para API externa
        auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
        if "access_token" not in auth_response:
            return jsonify({"status": "error", "message": "Falha na autenticação"}), 500
        access_token = auth_response["access_token"]

        OPERADORES_MAP = {
            2020: "Renato",
            2021: "Matheus",
            2022: "Gustavo",
            2023: "Raysa",
            2024: "Lucas",
            2025: "Danilo",
            2028: "Henrique",
            2029: "Rafael"
        }

        total_registros = 0
        dados_encontrados = False
        
        for operador_id, nome_operador in OPERADORES_MAP.items():
            offset = 0
            
            while True:
                params = {
                    "initial_date": data_inicio.strftime('%Y-%m-%d'),
                    "final_date": hoje.strftime('%Y-%m-%d'),
                    "initial_hour": "00:00:00",
                    "final_hour": "23:59:59",
                    "fixed": 0,
                    "week": [],
                    "agents": [operador_id],
                    "queues": [1],
                    "options": {"sort": {"data": 1}, "offset": offset, "count": 1000},
                    "conf": {}
                }

                app.logger.info(f"[{nome_operador}] Buscando dados de {data_inicio} a {hoje}, offset {offset}")
                response = utils.atendentePerformanceData(access_token, params)
                dados = response.get("result", {}).get("data", [])

                if not dados:
                    app.logger.info(f"[{nome_operador}] Nenhum dado retornado para o período.")
                    break

                dados_encontrados = True
                for item in dados:
                    try:
                        data_raw = item["data"].split("T")[0] if "T" in item["data"] else item["data"]
                        data_registro = datetime.strptime(data_raw, "%Y-%m-%d").date()

                        # Monta o objeto para merge (update or insert)
                        registro = PerformanceColaboradores(
                            operador_id=operador_id,
                            name=nome_operador,
                            data=data_registro,
                            ch_atendidas=item.get("ch_atendidas", 0),
                            ch_naoatendidas=item.get("ch_naoatendidas", 0),
                            tempo_online=item.get("tempo_online", 0),
                            tempo_livre=item.get("tempo_livre", 0),
                            tempo_servico=item.get("tempo_servico", 0),
                            pimprod_refeicao=item.get("pimprod_Refeicao", 0),
                            tempo_minatend=item.get("tempo_minatend"),
                            tempo_medatend=item.get("tempo_medatend"),
                            tempo_maxatend=item.get("tempo_maxatend"),
                            data_importacao=datetime.now()
                        )

                        db.session.merge(registro)  # insere ou atualiza automaticamente
                        total_registros += 1
                    except Exception as e:
                        app.logger.error(f"[ERRO] {nome_operador} em {item.get('data')}: {str(e)}")

                offset += 1000

        # Se não encontrou dados no intervalo maior, tenta pegar só o de hoje (processamento diário normal)
        if not dados_encontrados:
            app.logger.info("Nenhum dado encontrado no período extendido. Buscando dados de hoje somente.")
            for operador_id, nome_operador in OPERADORES_MAP.items():
                offset = 0
                while True:
                    params = {
                        "initial_date": hoje.strftime('%Y-%m-%d'),
                        "final_date": hoje.strftime('%Y-%m-%d'),
                        "initial_hour": "00:00:00",
                        "final_hour": "23:59:59",
                        "fixed": 0,
                        "week": [],
                        "agents": [operador_id],
                        "queues": [1],
                        "options": {"sort": {"data": 1}, "offset": offset, "count": 1000},
                        "conf": {}
                    }

                    app.logger.info(f"[{nome_operador}] Buscando dados de hoje, offset {offset}")
                    response = utils.atendentePerformanceData(access_token, params)
                    dados = response.get("result", {}).get("data", [])

                    if not dados:
                        break

                    for item in dados:
                        try:
                            data_raw = item["data"].split("T")[0] if "T" in item["data"] else item["data"]
                            data_registro = datetime.strptime(data_raw, "%Y-%m-%d").date()

                            registro = PerformanceColaboradores(
                                operador_id=operador_id,
                                name=nome_operador,
                                data=data_registro,
                                ch_atendidas=item.get("ch_atendidas", 0),
                                ch_naoatendidas=item.get("ch_naoatendidas", 0),
                                tempo_online=item.get("tempo_online", 0),
                                tempo_livre=item.get("tempo_livre", 0),
                                tempo_servico=item.get("tempo_servico", 0),
                                pimprod_refeicao=item.get("pimprod_Refeicao", 0),
                                tempo_minatend=item.get("tempo_minatend"),
                                tempo_medatend=item.get("tempo_medatend"),
                                tempo_maxatend=item.get("tempo_maxatend"),
                                data_importacao=datetime.now()
                            )
                            db.session.merge(registro)
                            total_registros += 1
                        except Exception as e:
                            app.logger.error(f"[ERRO] {nome_operador} em {item.get('data')}: {str(e)}")

                    offset += 1000

        db.session.commit()
        return jsonify({"status": "success", "message": f"{total_registros} registros inseridos ou atualizados."})

    except Exception as e:
        app.logger.error(f"Erro na rota atualizar_performance_incremental: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def processar_e_armazenar_performance_vyrtos_incremental():
    hoje = datetime.now().date()

    # Autenticação
    auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
    if "access_token" not in auth_response:
        return {"status": "error", "message": "Falha na autenticação"}
    access_token = auth_response["access_token"]

    OPERADORES_MAP = {
        2020: "Renato",
        2021: "Matheus",
        2022: "Gustavo",
        2023: "Raysa",
        2024: "Lucas",
        2025: "Danilo",
        2028: "Henrique",
        2029: "Rafael"
    }

    total_registros = 0

    for operador_id, nome_operador in OPERADORES_MAP.items():
        offset = 0
        registros = []

        while True:
            params = {
                "initial_date": hoje.strftime('%Y-%m-%d'),
                "final_date": hoje.strftime('%Y-%m-%d'),
                "initial_hour": "00:00:00",
                "final_hour": "23:59:59",
                "fixed": 0,
                "week": [],
                "agents": [operador_id],
                "queues": [10],
                "options": {"sort": {"data": 1}, "offset": offset, "count": 1000},
                "conf": {}
            }

            print(f"[{nome_operador}] Buscando dados de {hoje}, offset {offset}")
            response = utils.atendentePerformanceData(access_token, params)
            dados = response.get("result", {}).get("data", [])

            if not dados:
                print(f"[{nome_operador}] Nenhum dado retornado.")
                break

            for item in dados:
                try:
                    data_raw = item["data"].split("T")[0] if "T" in item["data"] else item["data"]
                    data_registro = datetime.strptime(data_raw, "%Y-%m-%d").date()

                    # Evita duplicidade
                    exists = DesempenhoAtendenteVyrtos.query.filter_by(
                        operador_id=operador_id,
                        data=data_registro
                    ).first()
                    if exists:
                        continue

                    registro = DesempenhoAtendenteVyrtos(
                        name=nome_operador,
                        operador_id=operador_id,
                        data=data_registro,
                        ch_atendidas=item.get("ch_atendidas", 0),
                        ch_naoatendidas=item.get("ch_naoatendidas", 0),
                        tempo_online=item.get("tempo_online", 0),
                        tempo_livre=item.get("tempo_livre", 0),
                        tempo_servico=item.get("tempo_servico", 0),
                        pimprod_refeicao=item.get("pimprod_Refeicao", 0),
                        tempo_minatend=item.get("tempo_minatend"),
                        tempo_medatend=item.get("tempo_medatend"),
                        tempo_maxatend=item.get("tempo_maxatend"),
                        data_importacao=datetime.now()
                    )
                    registros.append(registro)

                except Exception as e:
                    print(f"[ERRO] {nome_operador} em {item.get('data')}: {str(e)}")

            if len(dados) < 1000:
                break

            offset += 1000

        if registros:
            db.session.bulk_save_objects(registros)
            db.session.commit()
            print(f"[{nome_operador}] {len(registros)} registros inseridos.")
            total_registros += len(registros)

    return {
        "status": "success",
        "message": f"{total_registros} registros inseridos no modo incremental (Vyrtos)."
    }

def processar_e_armazenar_performance_vyrtos(dias=180, incremental=False):
    hoje = datetime.now().date()
    ontem = hoje - timedelta(days=1)
    
    if dias != 180 and not incremental:
        raise ValueError("Somente o intervalo de 180 dias é permitido para carga completa.")

    # Autenticação
    auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
    if "access_token" not in auth_response:
        return {"status": "error", "message": "Falha na autenticação"}
    access_token = auth_response["access_token"]

    # Datas de busca
    data_inicial = hoje - timedelta(days=dias - 1)
    data_final = hoje

    # IDs e nomes dos operadores
    OPERADORES_MAP = {
        2020: "Renato",
        2021: "Matheus",
        2022: "Gustavo",
        2023: "Raysa",
        2024: "Lucas",
        2025: "Danilo",
        2028: "Henrique",
        2029: "Rafael"
    }

    operadores_ids = list(OPERADORES_MAP.keys())

    # Limpa somente se for carga completa
    if not incremental:
        try:
            DesempenhoAtendenteVyrtos.query.delete()
            db.session.commit()
            print("Tabela de PerformanceColaboradores limpa com sucesso.")
        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": f"Erro ao limpar a tabela: {str(e)}"}

    for operador_id in operadores_ids:
        nome_operador = OPERADORES_MAP.get(operador_id, "Desconhecido")

        for inicio, fim in gerar_intervalos(data_inicial, data_final, tamanho=15):  # usar intervalos menores
            offset = 0
            total_registros = 0

            while True:
                params = {
                    "initial_date": inicio.strftime('%Y-%m-%d'),
                    "final_date": fim.strftime('%Y-%m-%d'),
                    "initial_hour": "00:00:00",
                    "final_hour": "23:59:59",
                    "fixed": 0,
                    "week": [],
                    "agents": [operador_id],
                    "queues": [10],
                    "options": {"sort": {"data": 1}, "offset": offset, "count": 1000},
                    "conf": {}
                }

                print(f"[{nome_operador}] Buscando {inicio} até {fim}, offset {offset}")
                response = utils.atendentePerformanceData(access_token, params)
                dados = response.get("result", {}).get("data", [])

                if not dados:
                    break

                for item in dados:
                    try:
                        data_registro = datetime.strptime(item["data"], "%Y-%m-%d").date()

                        # Evita duplicidade se incremental
                        if incremental:
                            exists = DesempenhoAtendenteVyrtos.query.filter_by(
                                operador_id=operador_id,
                                data=data_registro
                            ).first()
                            if exists:
                                continue

                        registro = DesempenhoAtendenteVyrtos(
                            name=nome_operador,
                            operador_id=operador_id,
                            data=data_registro,
                            ch_atendidas=item.get("ch_atendidas", 0),
                            ch_naoatendidas=item.get("ch_naoatendidas", 0),
                            tempo_online=item.get("tempo_online", 0),
                            tempo_livre=item.get("tempo_livre", 0),
                            tempo_servico=item.get("tempo_servico", 0),
                            pimprod_refeicao=item.get("pimprod_Refeicao", 0),
                            tempo_minatend=item.get("tempo_minatend"),
                            tempo_medatend=item.get("tempo_medatend"),
                            tempo_maxatend=item.get("tempo_maxatend")
                        )
                        db.session.add(registro)
                        total_registros += 1
                    except Exception as e:
                        print(f"[ERRO] {nome_operador} em {item.get('data')}: {str(e)}")

                db.session.flush()
                offset += 1000  # Próxima página

            print(f"[{nome_operador}] Total inserido de {inicio} a {fim}: {total_registros}")

        db.session.commit()

    return {"status": "success", "message": "Dados inseridos com sucesso (modo incremental)." if incremental else "Carga completa realizada com sucesso."}

def atendentePerformanceData(token, params: dict):
    base_url = endpoints.PERFORMANCE_ATENDENTES

    # Faz uma cópia do dicionário para evitar mutações externas
    query_params = params.copy()

    print("-> Query Params:", query_params)

    # Transforma os valores de listas e dicionários em JSON strings, se necessário
    for key in ["options", "conf", "agents", "queues", "week"]:
        if key in query_params and isinstance(query_params[key], (dict, list)):
            query_params[key] = json.dumps(query_params[key])

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(base_url, headers=headers, params=query_params)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "status_code": getattr(e.response, "status_code", 500),
            "url": base_url
        }

def importar_chamados():
    token = token_desk()

    if not token:
        raise Exception("Falha na autenticação")
    
    payload = {
        "Pesquisa": "",
        "Tatual": "",
        "Ativo": "Todos",
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
            "CodSolicitacao": "on",
            "CodSubCategoria": "on",
            "CodTipoOcorrencia": "on",
            "CodCategoriaTipo": "on",
            "CodPrioridadeAtual": "on",
            "CodStatusAtual": "on"
        },
        "Ordem": [{
            "Coluna": "Chave",
            "Direcao": "false"
        }]
    }

    response = requests.post(
        'https://api.desk.ms/ChamadosSuporte/lista',
        headers={'Authorization': f'{token}', 'Content-Type': 'application/json'},
        json=payload,
    )
    response.raise_for_status()
    chamados_api = response.json().get("root", [])

    def data_valida(data_str):
        return data_str and data_str != '0000-00-00'

    total_inseridos = 0
    total_atualizados = 0

    with db.session.begin():
        for chamado in chamados_api:
            try:
                data_str = chamado.get('DataCriacao')
                hora_str = chamado.get('HoraCriacao')
                data_finali = chamado.get('DataFinalizacao')
                hora_finali = chamado.get('HoraFinalizacao')

                if not data_valida(data_str):
                    continue

                try:
                    if hora_str:
                        try:
                            data_criacao = datetime.strptime(f"{data_str} {hora_str}", '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            data_criacao = datetime.strptime(f"{data_str} {hora_str}", '%Y-%m-%d %H:%M')
                    else:
                        data_criacao = datetime.strptime(data_str, '%Y-%m-%d')
                except Exception as e:
                    print(f"Erro ao processar data de criação do chamado {chamado.get('CodChamado')}: {e}")
                    continue

                data_finalizacao = None
                if data_valida(data_finali):
                    try:
                        if hora_finali:
                            try:
                                data_finalizacao = datetime.strptime(f"{data_finali} {hora_finali}", '%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                data_finalizacao = datetime.strptime(f"{data_finali} {hora_finali}", '%Y-%m-%d %H:%M')
                        else:
                            data_finalizacao = datetime.strptime(data_finali, '%Y-%m-%d')
                    except Exception as e:
                        print(f"Erro ao processar data de finalização do chamado {chamado.get('CodChamado')}: {e}")

                chave = chamado.get('Chave')
                existente = Chamado.query.filter_by(chave=chave).first()

                if existente:
                    # Atualiza campos relevantes
                    existente.cod_chamado = chamado.get('CodChamado')
                    existente.data_criacao = data_criacao
                    existente.nome_status = chamado.get('NomeStatus')
                    existente.nome_grupo = chamado.get('NomeGrupo')
                    existente.cod_solicitacao = chamado.get('CodSolicitacao')
                    existente.operador = chamado.get('NomeOperador')
                    existente.sla_atendimento = chamado.get('Sla1Expirado')
                    existente.sla_resolucao = chamado.get('Sla2Expirado')
                    existente.cod_categoria_tipo = chamado.get('CodCategoriaTipo')
                    existente.solicitante_email = chamado.get('SolicitanteEmail')
                    existente.nome_prioridade = chamado.get('NomePrioridade'),
                    existente.cod_tipo_ocorrencia = chamado.get('CodTipoOcorrencia'),
                    existente.cod_sub_categoria = chamado.get('CodSubCategoria'),
                    existente.restante_p_atendimento = chamado.get('TempoRestantePrimeiroAtendimento'),
                    existente.restante_s_atendimento = chamado.get('TempoRestanteSegundoAtendimento'),
                    
                    existente.data_finalizacao = data_finalizacao
                    existente.mes_referencia = f"{data_criacao.year}-{data_criacao.month:02d}"
                    existente.data_importacao = datetime.now()
                    total_atualizados += 1
                else:
                    novo_chamado = Chamado(
                        chave=chave,
                        cod_chamado=chamado.get('CodChamado'),
                        data_criacao=data_criacao,
                        nome_status=chamado.get('NomeStatus'),
                        nome_grupo=chamado.get('NomeGrupo'),
                        cod_solicitacao=chamado.get('CodSolicitacao'),
                        operador=chamado.get('NomeOperador'),
                        sla_atendimento=chamado.get('Sla1Expirado'),
                        sla_resolucao=chamado.get('Sla2Expirado'),
                        cod_categoria_tipo=chamado.get('CodCategoriaTipo'),
                        cod_tipo_ocorrencia = chamado.get('CodTipoOcorrencia'),
                        solicitante_email = chamado.get('SolicitanteEmail'),
                        nome_prioridade = chamado.get('NomePrioridade'),
                        restante_p_atendimento = chamado.get('TempoRestantePrimeiroAtendimento'),
                        restante_s_atendimento = chamado.get('TempoRestanteSegundoAtendimento'),
                        data_finalizacao=data_finalizacao,
                        mes_referencia=f"{data_criacao.year}-{data_criacao.month:02d}",
                        data_importacao=datetime.now()
                    )
                    db.session.add(novo_chamado)
                    total_inseridos += 1

            except Exception as e:
                print(f"Erro ao processar chamado: {e}")
                continue

    return {
        "total_api": len(chamados_api),
        "inseridos": total_inseridos,
        "atualizados": total_atualizados
    }

def parse_data(data_str):
    """Converte string no formato 'YYYY-MM-DD' para datetime.date"""
    try:
        return datetime.strptime(data_str, "%Y-%m-%d").date()
    except:
        return None

def importar_pSatisfacao():
    token = token_desk()
    if not token:
        raise Exception("Falha na autenticação")

    payload = {
        "Pesquisa": "",
        "Respondidas": "",
        "ModoExibicao": "Alternativa",
        "Colunas": {
            "ReferenciaChamado": "on",
            "AssuntoChamado": "on",
            "DataRespostaChamado": "on",
            "DataFinalizacaoChamado": "on",
            "Empresa": "on",
            "Solicitante": "on",
            "Operador": "on",
            "Grupo": "on",
            "Questionarios": "on",
            "Questoes": "on",
            "Alternativas": "on",
            "RespDissertativa": "on"
        },
        "Filtro": {
            "CodPS": [""],
            "CodQuestao": [""],
            "DataPersonalizada": [""],
            "PesquisaSatisfacaoData": [""],
            "DataPersonalizada2": [""],
            "ExpiraPesquisaSatisfacao": [""]
        }
    }

    response = requests.post(
        'https://api.desk.ms/PesquisaSatisfacao/lista',
        headers={'Authorization': token, 'Content-Type': 'application/json'},
        json=payload,
    )

    response.raise_for_status()
    p_satisfacao = response.json().get("root", [])

    print(f"Total recebido: {len(p_satisfacao)}")

    existentes = set(
        row.referencia_chamado for row in PesquisaSatisfacao.query.with_entities(PesquisaSatisfacao.referencia_chamado).all()
    )

    novos = []
    for satisfacao in p_satisfacao:
        ref = satisfacao.get("ReferenciaChamado")
        if not ref or ref in existentes:
            continue  # pular se já existe

        nova = PesquisaSatisfacao(
            referencia_chamado=ref,
            assunto=satisfacao.get("AssuntoChamado"),
            data_resposta=parse_data(satisfacao.get("DataRespostaChamado")),
            data_finalizacao=parse_data(satisfacao.get("DataFinalizacaoChamado")),
            empresa=satisfacao.get("Empresa"),
            solicitante=satisfacao.get("Solicitante"),
            operador=satisfacao.get("Operador"),
            grupo=satisfacao.get("Grupo"),
            questionario=satisfacao.get("Questionarios"),
            questao=satisfacao.get("Questoes"),
            alternativa=satisfacao.get("Alternativas"),
            resposta_dissertativa=satisfacao.get("RespDissertativa")
        )
        novos.append(nova)

    if novos:
        db.session.bulk_save_objects(novos)
        db.session.commit()
        print(f"{len(novos)} registros inseridos.")
    else:
        print("Nenhum novo registro para inserir.")

def importar_fcr_reabertos():
    print("Tarefa em execução!")

    token = token_desk()
    url = RELATORIO_CHAMADOS_SUPORTE
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }

    cod_colaboradores = {
        'Gustavo': '77',
        'Danilo': '78',
        'Henrique': '76',
        'Lucas': '75',
        'Matheus': '74',
        'Rafael': '73',
        'Raysa': '72',
        'Renato': '71',
    }

    if not token:
        raise Exception('Falha na autenticação')

    for nome, codigo in cod_colaboradores.items():
        payload = {
            "Chave": codigo,
            "APartirDe": "0",
            "Total": "50000"
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            print(f"[ERRO] Falha na requisição de {nome} ({codigo}): {response.status_code}")
            continue

        try:
            resposta = response.json()
        except json.JSONDecodeError:
            print(f"[ERRO] Resposta inválida de {nome}: não é JSON.")
            continue

        chamados = resposta.get("root", [])

        if not isinstance(chamados, list):
            print(f"[ERRO] Resposta inesperada para {nome}. Esperava lista em 'root'.")
            print("Resposta bruta:", resposta)
            continue

        print(f"{nome} ({codigo}) retornou {len(chamados)} chamados.")

        for item in chamados:
            if not isinstance(item, dict):
                print(f"[ERRO] Item malformado em {nome}: {item}")
                continue

            cod_chamado = item.get("CodChamado")
            if not cod_chamado:
                continue

            registro = RelatorioColaboradores.query.filter_by(cod_chamado=cod_chamado).first()

            dados = {
                "chave": codigo,
                "operador": nome,  # <=== operador (nome do colaborador)
                "nome_status": item.get("NomeStatus"),
                "reaberto": item.get("Reaberto"),
                "first_call": item.get("FirstCall"),
                "tempo_sem_interacao": item.get("TempoSemInteracao"),
                "sla1_expirado": item.get("Sla1Expirado"),
                "nome_sla1_status": item.get("NomeSla1Status"),
                "sla2_expirado": item.get("Sla2Expirado"),
                "nome_sla2_status": item.get("NomeSla2Status"),
                "pesquisa_satisfacao_respondido": item.get("PesquisaSatisfacaoRespondido"),
                "nome_solicitacao": item.get("NomeSolicitacao"),
                "fantasia": item.get("Fantasia"),
                "nome_completo_solicitante": item.get("NomeCompletoSolicitante"),
                "cod_chamado": cod_chamado,
                "data_criacao": item.get("DataCriacao"),
                "data_finalizacao": item.get("DataFinalizacao"),
                "possui_ps": item.get("PossuiPS"),
                "ps_expirou": item.get("PSExpirou")
            }

            if registro:
                atualizou = False
                for campo, valor in dados.items():
                    if getattr(registro, campo) != valor:
                        setattr(registro, campo, valor)
                        atualizou = True
                if atualizou:
                    db.session.commit()
            else:
                novo_registro = RelatorioColaboradores(**dados)
                db.session.add(novo_registro)
                db.session.commit()

    print("Tarefa finalizada.")

def importar_categorias():
    token = token_desk()

    if not token:
        raise Exception("Falha na autenticação")
    
    payload = {
        "Pesquisa": "",		
        "Ativo": "S",			
        "Ordem": [			
            {
        "Coluna": "SubCategoria",
        "Direcao": "true"		
        }
    ]}

    response = requests.post(
        'https://api.desk.ms/SubCategorias/lista',
        headers={'Authorization': f'{token}', 'Content-Type': 'application/json'},
        json=payload,
    )
    response.raise_for_status()
    categorias_api = response.json().get("root", [])

    total_inseridos = 0
    total_atualizados = 0

    with db.session.begin():
        for categorias in categorias_api:
            persist_categorias = Categoria(
                chave = categorias.get("Chave"),
                sequencia = categorias.get("Sequencia"),
                sub_categoria = categorias.get("SubCategoria"),
                categoria = categorias.get("Categoria"),
                data_importacao = datetime.now()
            )

            db.session.add(persist_categorias)
            total_inseridos += 1

    return {
        "total_api": len(categorias_api),
        "inseridos": total_inseridos,
    }