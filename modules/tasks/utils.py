import requests, json
import settings.endpoints as endpoints
from urllib.parse import urlencode
from application.models import db, RegistroChamadas, ChamadasDetalhes, DesempenhoAtendente, DesempenhoAtendenteVyrtos, PerformanceColaboradores, Grupos, Chamado, Categoria, PesquisaSatisfacao, EventosAtendentes, RelatorioColaboradores
from modules.auth.utils import authenticate, authenticate_relatorio
from modules.deskmanager.authenticate.routes import token_desk
import modules.tasks.utils as utils
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
        hoje = datetime.now().date()
        data_inicio = hoje - timedelta(days=1)

        # Autenticação
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
                    break

                dados_encontrados = True

                for item in dados:
                    try:
                        data_raw = item["data"].split("T")[0] if "T" in item["data"] else item["data"]
                        data_registro = datetime.strptime(data_raw, "%Y-%m-%d").date()

                        # Verifica se já existe registro
                        registro_existente = PerformanceColaboradores.query.filter_by(
                            operador_id=operador_id,
                            data=data_registro
                        ).first()

                        if registro_existente:
                            # Atualiza campos existentes
                            registro_existente.name = nome_operador
                            registro_existente.ch_atendidas = item.get("ch_atendidas", 0)
                            registro_existente.ch_naoatendidas = item.get("ch_naoatendidas", 0)
                            registro_existente.tempo_online = item.get("tempo_online", 0)
                            registro_existente.tempo_livre = item.get("tempo_livre", 0)
                            registro_existente.tempo_servico = item.get("tempo_servico", 0)
                            registro_existente.pimprod_refeicao = item.get("pimprod_Refeicao", 0)
                            registro_existente.tempo_minatend = item.get("tempo_minatend")
                            registro_existente.tempo_medatend = item.get("tempo_medatend")
                            registro_existente.tempo_maxatend = item.get("tempo_maxatend")
                            registro_existente.data_importacao = datetime.now()
                        else:
                            novo_registro = PerformanceColaboradores(
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
                            db.session.add(novo_registro)

                        total_registros += 1

                    except Exception as e:
                        app.logger.error(f"[ERRO] {nome_operador} em {item.get('data')}: {str(e)}")

                offset += 1000  # Próxima página

        # Se nenhum dado foi encontrado, tenta pegar dados só de hoje
        if not dados_encontrados:
            app.logger.info("Nenhum dado encontrado nos últimos 2 dias. Tentando buscar dados apenas de hoje.")
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

                    response = utils.atendentePerformanceData(access_token, params)
                    dados = response.get("result", {}).get("data", [])

                    if not dados:
                        break

                    for item in dados:
                        try:
                            data_raw = item["data"].split("T")[0] if "T" in item["data"] else item["data"]
                            data_registro = datetime.strptime(data_raw, "%Y-%m-%d").date()

                            registro_existente = PerformanceColaboradores.query.filter_by(
                                operador_id=operador_id,
                                data=data_registro
                            ).first()

                            if registro_existente:
                                registro_existente.name = nome_operador
                                registro_existente.ch_atendidas = item.get("ch_atendidas", 0)
                                registro_existente.ch_naoatendidas = item.get("ch_naoatendidas", 0)
                                registro_existente.tempo_online = item.get("tempo_online", 0)
                                registro_existente.tempo_livre = item.get("tempo_livre", 0)
                                registro_existente.tempo_servico = item.get("tempo_servico", 0)
                                registro_existente.pimprod_refeicao = item.get("pimprod_Refeicao", 0)
                                registro_existente.tempo_minatend = item.get("tempo_minatend")
                                registro_existente.tempo_medatend = item.get("tempo_medatend")
                                registro_existente.tempo_maxatend = item.get("tempo_maxatend")
                                registro_existente.data_importacao = datetime.now()
                            else:
                                novo_registro = PerformanceColaboradores(
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
                                db.session.add(novo_registro)

                            total_registros += 1
                        except Exception as e:
                            app.logger.error(f"[ERRO] {nome_operador} em {item.get('data')}: {str(e)}")

                    offset += 1000

        db.session.commit()
        return jsonify({"status": "success", "message": f"{total_registros} registros inseridos ou atualizados."})

    except Exception as e:
        app.logger.error(f"Erro na tarefa processar_e_armazenar_performance_incremental: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def processar_e_armazenar_performance_vyrtos_incremental():
    hoje = datetime.now().date()
    data_inicio = hoje - timedelta(days=2)

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
                "initial_date": data_inicio.strftime('%d/%m/%Y'),
                "final_date": hoje.strftime('%d/%m/%Y'),
                "initial_hour": "00:00:00",
                "final_hour": "23:59:59",
                "fixed": 1,
                "week": [1, 2, 3, 4, 5],
                "queues": [10],
                "agents": [operador_id],
                "options": {"sort": {"data": -1}, "offset": offset, "count": 1000},
                "conf": {}
            }

            print(f"\n[{nome_operador}] Buscando dados de {data_inicio} a {hoje}, offset {offset}")
            response = utils.atendentePerformanceData(access_token, params)
            dados = response.get("result", {}).get("data", [])

            if not dados:
                print(f"[{nome_operador}] Nenhum dado retornado.")
                break

            for item in dados:
                try:
                    print(f"[{nome_operador}] Dado recebido: {item}")
                    data_str = item.get("data")
                    if not data_str:
                        print(f"[{nome_operador}] ⚠️ Campo 'data' ausente. Item ignorado.")
                        continue

                    try:
                        data_registro = datetime.strptime(data_str, "%Y-%m-%d").date()
                    except Exception as e:
                        print(f"[{nome_operador}] ⚠️ Erro ao converter data '{data_str}': {e}")
                        continue

                    exists = DesempenhoAtendenteVyrtos.query.filter_by(
                        operador_id=operador_id,
                        data=data_registro
                    ).first()
                    if exists:
                        print(f"[{nome_operador}] Registro existente para {data_registro}. Ignorado.")
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
                        pimprod_refeicao=item.get("pimprod_Refeicao_2", 0),
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
        else:
            print(f"[{nome_operador}] Nenhum novo registro inserido.")

    if total_registros == 0:
        print("⚠️ Nenhum dado foi inserido no banco para o período.")

    return {
        "status": "success",
        "message": f"{total_registros} registros inseridos no modo incremental (Vyrtos)."
    }

def processar_e_armazenar_performance_vyrtos(dias=180, incremental=False):
    hoje = datetime.now().date()
    
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

    if not incremental:
        try:
            DesempenhoAtendenteVyrtos.query.delete()
            db.session.commit()
            print("🧹 Tabela desempenho_atendente_vyrtos limpa com sucesso.")
        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": f"Erro ao limpar a tabela: {str(e)}"}

    for operador_id, nome_operador in OPERADORES_MAP.items():
        total_registros_operador = 0
        print(f"🔄 Processando operador: {nome_operador} ({operador_id})")

        for inicio, fim in gerar_intervalos(data_inicial, data_final, tamanho=15):
            offset = 0

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

                print(f"📡 [{nome_operador}] Buscando de {inicio} a {fim}, offset {offset}")
                response = utils.atendentePerformanceData(access_token, params)
                dados = response.get("result", {}).get("data", [])

                if not dados:
                    break

                for item in dados:
                    try:
                        data_registro = datetime.strptime(item["data"], "%Y-%m-%d").date()

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
                            tempo_maxatend=item.get("tempo_maxatend"),
                            data_importacao=datetime.now()
                        )
                        db.session.add(registro)
                        total_registros_operador += 1
                    except Exception as e:
                        print(f"[ERRO] {nome_operador} em {item.get('data')}: {str(e)}")

                offset += 1000  # Próxima página de resultados

        try:
            db.session.commit()
            print(f"✅ [{nome_operador}] Total de registros inseridos: {total_registros_operador}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao inserir dados para {nome_operador}: {str(e)}")

    return {
        "status": "success",
        "message": "Dados inseridos com sucesso (modo incremental)." if incremental else "Carga completa realizada com sucesso."
    }

def atendentePerformanceData(token, params: dict):
    base_url = endpoints.PERFORMANCE_ATENDENTES

    # Faz uma cópia do dicionário para evitar mutações externas
    query_params = params.copy()

    print("-> Query Params (antes do ajuste):", query_params)

    # Converte listas/dicionários de forma adequada para query string
    for key in ["options", "conf"]:
        if key in query_params and isinstance(query_params[key], (dict, list)):
            query_params[key] = json.dumps(query_params[key])

    for key in ["agents", "queues", "week"]:
        if key in query_params and isinstance(query_params[key], list):
            query_params[key] = ",".join(map(str, query_params[key]))

    print("-> Query Params (após o ajuste):", query_params)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(base_url, headers=headers, params=query_params)
        response.raise_for_status()  # levanta erro se status != 200
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "status_code": getattr(e.response, "status_code", 500),
            "url": base_url
        }

def registroChamadas(token, params: dict):
    base_url = endpoints.CHAMADA_SAIDA

    # Faz uma cópia do dicionário para evitar mutações externas
    query_params = params.copy()

    print("-> Query Params (antes do ajuste):", query_params)

    # Converte listas/dicionários de forma adequada para query string
    for key in ["options", "conf"]:
        if key in query_params and isinstance(query_params[key], (dict, list)):
            query_params[key] = json.dumps(query_params[key])

    for key in ["agents", "queues", "week"]:
        if key in query_params and isinstance(query_params[key], list):
            query_params[key] = ",".join(map(str, query_params[key]))

    print("-> Query Params (após o ajuste):", query_params)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(base_url, headers=headers, params=query_params)
        response.raise_for_status()  # levanta erro se status != 200
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "status_code": getattr(e.response, "status_code", 500),
            "url": base_url
        }
    
def detalhesChamadas(token, params: dict):
    base_url = endpoints.DETALHE_CHAMADAS

    # Faz uma cópia do dicionário para evitar mutações externas
    query_params = params.copy()

    print("-> Query Params (antes do ajuste):", query_params)

    # Converte listas/dicionários de forma adequada para query string
    for key in ["conf"]:
        if key in query_params and isinstance(query_params[key], (dict, list)):
            query_params[key] = json.dumps(query_params[key])

    for key in ["agents", "queues", "week"]:
        if key in query_params and isinstance(query_params[key], list):
            query_params[key] = ",".join(map(str, query_params[key]))

    print("-> Query Params (após o ajuste):", query_params)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(base_url, headers=headers, params=query_params)
        response.raise_for_status()  # levanta erro se status != 200
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "status_code": getattr(e.response, "status_code", 500),
            "url": base_url
        }

def atendenteEventosData(token, params: dict):
    base_url = endpoints.EVENTOS_ATENDENTES

    # Faz uma cópia do dicionário para evitar mutações externas
    query_params = params.copy()

    print("-> Query Params (antes do ajuste):", query_params)

    # Converte listas/dicionários de forma adequada para query string
    for key in ["options", "conf"]:
        if key in query_params and isinstance(query_params[key], (dict, list)):
            query_params[key] = json.dumps(query_params[key])

    for key in ["agents", "queues", "week"]:
        if key in query_params and isinstance(query_params[key], list):
            query_params[key] = ",".join(map(str, query_params[key]))

    print("-> Query Params (após o ajuste):", query_params)

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(base_url, headers=headers, params=query_params)
        response.raise_for_status()  # levanta erro se status != 200
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
        'Gustavo': '90',
        'Danilo': '91',
        'Henrique': '89',
        'Lucas': '88',
        'Matheus': '87',
        'Rafael': '86',
        'Raysa': '85',
        'Renato': '84',
        'Fernando': '94',
        'Luciano': '95',
        'Eduardo': '93',
        'Chrysthyanne': '92',

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
                "grupo" : item.get("NomeGrupo"),
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
                "data_criacao": parse_data(item.get("DataCriacao")),
                "data_finalizacao": parse_data(item.get("DataFinalizacao")),
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

# Converte a data se existir e estiver no formato DD-MM-YYYY
def parse_data(data_str):
    if data_str:
        try:
            return datetime.strptime(data_str, "%d-%m-%Y").date()
        except ValueError:
            # Se não for no formato esperado, tente ISO
            try:
                return datetime.strptime(data_str, "%Y-%m-%d").date()
            except ValueError:
                return None
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

def importar_grupos():
    token = token_desk()

    url = endpoints.LISTA_GRUPOS

    headers = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }

    if not token:
        raise Exception("Falha na autenticação")
    
    payload = {
        "Pesquisa": "",
        "Ativo": "1",
        "Ordem": [
            {
            "Coluna": "Nome",
            "Direcao": "true"
            }
        ]
        }
    

    response = requests.post(url, headers=headers, json=payload)

    response.raise_for_status()
    grupos_api = response.json().get("root", [])


    with db.session.begin():
        for grupos in grupos_api:
            persist_grupos = Grupos(
                chave = grupos.get("Chave"),
                nome = grupos.get("Nome"),
                email = grupos.get("Email"),
                opcoes = grupos.get("Opcoes"),
                bloqueado = grupos.get('Bloqueado'),
                qtd_operadores = grupos.get('QtdOperadores'),
                smtp_ativo = grupos.get('SmtpAtivo')            
                )

            db.session.add(persist_grupos)

    return {
        "total_api": len(grupos_api),
    }

def processar_e_armazenar_eventos():
    hoje = datetime.now().date()
    data_inicial = hoje
    data_final = hoje

    print(f"🔄 Importando eventos SOMENTE do dia {hoje}")

    # Autenticação
    auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
    if "access_token" not in auth_response:
        print("❌ Falha na autenticação")
        return {"status": "error", "message": "Falha na autenticação"}
    access_token = auth_response["access_token"]

    # Mapeamento operadores
    OPERADORES_MAP = {
        2020: "Renato Ragga",
        2021: "Matheus",
        2022: "Gustavo",
        2023: "Raysa",
        2024: "Lucas",
        2025: "Danilo",
        2028: "Henrique",
        2029: "Rafael"
    }

    operadores_ids = list(OPERADORES_MAP.keys())

    # Funções auxiliares internas para parsing seguro
    def parse_data(data_str):
        if not data_str or str(data_str).strip() in ["-", ""]:
            return None
        for fmt in ["%d/%m/%Y", "%Y/%m/%d", "%Y-%m-%d"]:
            try:
                return datetime.strptime(data_str, fmt).date()
            except ValueError:
                continue
        print(f"⚠️ Data inválida recebida: {data_str}")
        return None

    def parse_datetime(dt_str):
        if not dt_str or str(dt_str).strip() in ["-", ""]:
            return None
        for fmt in ["%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y/%m/%d %H:%M:%S"]:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        print(f"⚠️ Datetime inválido recebido: {dt_str}")
        return None

    def parse_timedelta(valor):
        if not valor or str(valor).strip() in ["-", ""]:
            return None
        try:
            h, m, s = map(int, valor.split(":"))
            return timedelta(hours=h, minutes=m, seconds=s)
        except Exception as e:
            print(f"⚠️ Erro ao parsear timedelta '{valor}': {e}")
            return None

    def parse_bool(valor):
        return str(valor).strip() in ["1", "True", "true"]

    for operador_id in operadores_ids:
        nome_operador = OPERADORES_MAP.get(operador_id, "Desconhecido")
        print(f"\n👤 Processando operador {nome_operador} (ID {operador_id})")

        for inicio, fim in gerar_intervalos(data_inicial, data_final, tamanho=15):
            offset = 0
            total_registros = 0

            while True:
                params = {
                    "initial_date": inicio.strftime('%d/%m/%Y'),
                    "final_date": fim.strftime('%d/%m/%Y'),
                    "initial_hour": "00:00:00",
                    "final_hour": "23:59:59",
                    "fixed": 0,
                    "week": [],
                    "agents": [operador_id],
                    "queues": [1],
                    "options": {"sort": {"data": 1}, "offset": offset, "count": 1000},
                    "conf": {}
                }

                print(f"➡️ [{nome_operador}] Buscando eventos de {inicio} até {fim}, offset {offset}")
                response = utils.atendenteEventosData(access_token, params)

                if not response:
                    print(f"❌ [{nome_operador}] Resposta vazia da API")
                    break

                dados = response.get("result", {}).get("data", [])
                print(f"📦 [{nome_operador}] Registros recebidos: {len(dados)}")

                if not dados:
                    break

                for item in dados:
                    try:
                        print(f"🔍 [{nome_operador}] Item cru: {item}")

                        data_evento = parse_data(item.get("data"))
                        data_inicio = parse_datetime(item.get("dataInicio"))
                        data_fim = parse_datetime(item.get("dataFim"))

                        if not item.get("evento") and not data_inicio:
                            print(f"⚠️ [{nome_operador}] Evento descartado (sem evento e sem dataInicio): {item}")
                            continue

                        existe = EventosAtendentes.query.filter_by(
                            atendente=operador_id,
                            data_inicio=data_inicio,
                            evento=item.get("evento")
                        ).first()

                        if existe:
                            print(f"⏭️ [{nome_operador}] Evento já existe: {item.get('evento')} em {data_inicio}")
                            continue

                        registro = EventosAtendentes(
                            data=data_evento,
                            atendente=operador_id,
                            nome_atendente=nome_operador,
                            evento=item.get("evento") or "-",
                            parametro=item.get("parametro") or None,
                            nome_pausa=item.get("nomePausa") or None,
                            data_inicio=data_inicio,
                            data_fim=data_fim,
                            sinaliza_duracao=parse_bool(item.get("sinalizaDuracao")),
                            duracao=parse_timedelta(item.get("duracao")),
                            complemento=item.get("complemento") or None,
                            data_importacao=datetime.utcnow()
                        )
                        db.session.add(registro)
                        total_registros += 1

                    except Exception as e:
                        print(f"❌ [{nome_operador}] Erro ao processar item: {e} | Dados: {item}")

                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"❌ Erro ao salvar registros no banco: {e}")

                offset += 1000

            print(f"✅ [{nome_operador}] Total eventos inseridos de {inicio} a {fim}: {total_registros}")

    return {"status": "success", "message": f"Eventos importados apenas do dia {hoje}."}

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

def importar_registro_chamadas_incremental():
    hoje = datetime.now().date()

    # Autenticação
    auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
    if "access_token" not in auth_response:
        print("❌ Falha na autenticação:", auth_response)
        return {"status": "error", "message": "Falha na autenticação"}

    access_token = auth_response["access_token"]
    print(f"✅ Token obtido: {access_token[:10]}...")

    total_inseridos = 0
    offset = 0
    print(f"\n📅 Buscando registros do dia {hoje.strftime('%d/%m/%Y')}")

    while True:
        params = {
            "initial_date": hoje.strftime('%d/%m/%Y'),
            "final_date": hoje.strftime('%d/%m/%Y'),
            "initial_hour": "00:00:00",
            "final_hour": "23:59:59",
            "options": json.dumps({
                "sort": {"data": -1},
                "offset": offset,
                "count": 100
            })
        }

        print(f"➡️ Requisição com offset={offset}, params={params}")
        response = utils.registroChamadas(access_token, params)

        # Validação de resposta
        if not response:
            print("❌ Resposta da API veio vazia")
            break

        mensagens = response.get("result", {}).get("messages", [])
        print("ℹ️ Mensagens API:", mensagens)

        dados = response.get("result", {}).get("data", [])
        print(f"📦 Registros recebidos: {len(dados)}")

        if not dados:
            print("⚠️ Nenhum dado retornado, encerrando loop.")
            break

        novos_registros = 0

        for item in dados:
            try:
                unique_id = item.get("uniqueID")
                if not unique_id:
                    print("⚠️ Registro sem uniqueID:", item)
                    continue

                # Verifica se já existe no banco
                existe = RegistroChamadas.query.filter_by(unique_id=unique_id).first()
                if existe:
                    print(f"⏭️ Registro já existe: {unique_id}")
                    continue

                print(f"➕ Novo registro {unique_id} - DataHora={item.get('dataHora')}")

                registro = RegistroChamadas(
                    data_hora=datetime.strptime(item["dataHora"], "%Y-%m-%d %H:%M:%S"),
                    unique_id=unique_id,
                    status=item.get("status"),
                    numero=item.get("numero"),
                    tempo_espera=item.get("tempoEspera"),
                    tempo_atendimento=item.get("tempoAtendimento"),
                    nome_atendente=item.get("nomeAtendente"),
                    motivo=item.get("motivo"),
                    sub_motivo=item.get("subMotivo"),
                    desconexao_local=item.get("desconexaoLocal"),
                    data_importacao=datetime.utcnow()
                )
                db.session.add(registro)
                novos_registros += 1
                total_inseridos += 1

            except Exception as e:
                print(f"❌ Erro ao processar registro {item}: {e}")
                continue

        try:
            db.session.commit()
            print(f"💾 {novos_registros} registros salvos neste batch.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao dar commit: {e}")

        offset += 100

        if len(dados) < 100:
            print("🚪 Menos de 100 registros recebidos, encerrando paginação.")
            break

    return {"status": "success", "message": f"Importação concluída. Total inseridos: {total_inseridos}"}

def importar_detalhes_chamadas_hoje():
    hoje = datetime.now().date()
    data_inicio = hoje
    data_fim = hoje

    auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
    if "access_token" not in auth_response:
        print("❌ Falha na autenticação")
        return {"status": "error", "message": "Falha na autenticação"}

    access_token = auth_response["access_token"]
    total_registros = 0
    data_importacao_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    offset = 0
    while True:
        params = {
                "initial_date": data_inicio.strftime('%d/%m/%Y'),  # formato dd/mm/yyyy como usado no Postman
                "final_date": data_fim.strftime('%d/%m/%Y'),
                "initial_hour": "00:00:00",
                "final_hour": "23:59:59",
                "fixed": 1,
                "week": "1,2,3,4,5",
                "agents": [2020,2021,2022,2023,2024,2025,2028,2029],         # deve ser string simples, não lista
                "queues": [1],                      # também string
                "transfer_display": 1,
                "conf": json.dumps({
                    "call_answered": 1,
                    "call_abandoned": 0
                }),
                "options": json.dumps({
                    "sort": {"data": -1},
                    "offset": offset,
                    "count": 100
                })
            }

        print(f"\n🔍 Enviando requisição para todos os operadores...")
        print(f"📅 Período: {data_inicio} até {data_fim}")
        print(f"-> Corpo da requisição (JSON): {json.dumps(params, indent=2, ensure_ascii=False)}")

        try:
            api_response = detalhesChamadas(access_token, params)
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")
            break

        if not api_response or "result" not in api_response:
            print(f"❗ Resposta inválida da API: {json.dumps(api_response, indent=2, ensure_ascii=False)}")
            break

        result = api_response["result"]
        if "data" not in result or not result["data"]:
            print(f"⚠️ Nenhum dado retornado")
            break

        print(f"✅ {len(result['data'])} registros retornados")
        print("📦 Exemplo de dado:")
        print(json.dumps(result["data"][0], indent=2, ensure_ascii=False, default=str))

        registros = []
        for item in result["data"]:
            if db.session.query(ChamadasDetalhes).filter_by(uniqueID=item.get("uniqueID")).first():
                continue

            campos_obrigatorios = [
                item.get("uniqueID"),
                item.get("data"),
                item.get("numero"),
                item.get("nomeAtendente")
            ]
            if any(v in [None, '', '0'] for v in campos_obrigatorios):
                print(f"⛔ Registro ignorado (faltando campos): {json.dumps(item, indent=2, ensure_ascii=False)}")
                continue

            registros.append(ChamadasDetalhes(
                idFila=str(item.get("idFila") or None),
                nomeFila=str(item.get("nomeFila") or None),
                uniqueID=str(item.get("uniqueID") or None),
                data=str(item.get("data") or None),
                tipo=str(item.get("tipo") or None),
                numero=str(item.get("numero") or None),
                origem=str(item.get("origem") or None),
                tipoOrigem=str(item.get("tipoOrigem") or None),
                filaOrigem=str(item.get("filaOrigem") or None),
                horaEntradaPos=str(item.get("horaEntradaPos") or None),
                horaAtendimento=str(item.get("horaAtendimento") or None),
                horaTerminoPos=str(item.get("horaTerminoPos") or None),
                tempoEspera=str(item.get("tempoEspera") or None),
                tempoAtendimento=str(item.get("tempoAtendimento") or None),
                numeroAtendente=str(item.get("numeroAtendente") or None),
                nomeAtendente=str(item.get("nomeAtendente") or None),
                desconexaoLocal=str(item.get("desconexaoLocal") or None),
                transferencia=str(item.get("transferencia") or None),
                motivo=str(item.get("motivo") or None),
                rotuloSubMotivo=str(item.get("rotuloSubMotivo") or None),
                subMotivo=str(item.get("subMotivo") or None),
                isAtendida=str(item.get("isAtendida") or None),
                isAbandonada=str(item.get("isAbandonada") or None),
                isTransbordoPorTempo=str(item.get("isTransbordoPorTempo") or None),
                isTransbordoPorTecla=str(item.get("isTransbordoPorTecla") or None),
                isIncompleta=str(item.get("isIncompleta") or None),
                numeroSemFormato=str(item.get("numeroSemFormato") or None),
                tipoAbandonada=str(item.get("tipoAbandonada") or None),
                Nome=str(item.get("Nome") or None),
                protocolo=str(item.get("protocolo") or None),
                retentativaSucesso=str(item.get("retentativaSucesso") or None),
                dataImportacao=data_importacao_str
            ))

        if registros:
            print(f"💾 Salvando {len(registros)} registros no banco")
            db.session.bulk_save_objects(registros)
            db.session.commit()
            total_registros += len(registros)
        else:
            print("🟡 Nenhum registro válido para salvar")

        if len(result["data"]) < 100:
            break

        offset += 100

    print(f"\n✅ Importação finalizada. Total de registros salvos: {total_registros}")
    return {"status": "success", "total_registros": total_registros}
