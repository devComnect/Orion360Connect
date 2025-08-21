from app import app
from modules.tasks.utils import importar_detalhes_chamadas_hoje,importar_registro_chamadas_incremental, processar_e_armazenar_eventos,importar_grupos, processar_e_armazenar_performance, processar_e_armazenar_performance_vyrtos, importar_categorias, importar_pSatisfacao, importar_fcr_reabertos, processar_e_armazenar_performance_incremental, processar_e_armazenar_performance_vyrtos_incremental


with app.app_context():
    print("Tarefa em execução!")
    processar_e_armazenar_eventos()


'''def importar_eventos():
    try:
        hoje = datetime.now().date()
        data_inicio = hoje - timedelta(days=1)

        # Autenticação
        auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
        if "access_token" not in auth_response:
            return jsonify({"status": "error", "message": "Falha na autenticação"}), 500

        access_token = auth_response["access_token"]

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

        total_registros = 0
        dados_encontrados = False

        for operador_id, nome_operador in OPERADORES_MAP.items():
            offset = 0
            while True:
                params = {
                    "initial_date": data_inicio.strftime('%d/%m/%Y'),
                    "final_date": hoje.strftime('%d/%m/%Y'),
                    "initial_hour": "00:00:00",
                    "final_hour": "23:59:59",
                    "fixed": 0,
                    "week": [],
                    "agents": [operador_id],
                    "queues": [1],
                    "options": {"sort": {"data": 1}, "offset": offset, "count": -1},
                    "conf": {}
                }

                app.logger.info(f"[{nome_operador}] Buscando eventos de {data_inicio} a {hoje}, offset {offset}")
                response = utils.atendenteEventosData(access_token, params)
                dados = response.get("result", {}).get("data", [])

                if not dados:
                    break

                dados_encontrados = True

                for item in dados:
                    try:
                        data_raw = item["data"].split("T")[0] if "T" in item["data"] else item["data"]
                        data_registro = datetime.strptime(data_raw, "%Y/%m/%d").date() if "/" in data_raw else datetime.strptime(data_raw, "%Y-%m-%d").date()
                        data_inicio_ev = datetime.strptime(item["dataInicio"], "%Y-%m-%d %H:%M:%S")
                        data_fim_ev = datetime.strptime(item["dataFim"], "%Y-%m-%d %H:%M:%S")

                        duracao_parts = item.get("duracao", "00:00:00").split(":")
                        duracao_ev = timedelta(
                            hours=int(duracao_parts[0]),
                            minutes=int(duracao_parts[1]),
                            seconds=int(duracao_parts[2])
                        )

                        sinaliza_duracao = bool(int(item.get("sinalizaDuracao", 0)))

                        registro_existente = EventosAtendentes.query.filter_by(
                            atendente=operador_id,
                            data=data_registro,
                            data_inicio=data_inicio_ev,
                            data_fim=data_fim_ev,
                            evento=item.get("evento", "")
                        ).first()

                        if registro_existente:
                            # Atualiza campos existentes
                            registro_existente.nome_atendente = nome_operador
                            registro_existente.parametro = item.get("parametro")
                            registro_existente.nome_pausa = item.get("nomePausa")
                            registro_existente.sinaliza_duracao = sinaliza_duracao
                            registro_existente.duracao = duracao_ev
                            registro_existente.complemento = item.get("complemento")
                            registro_existente.data_importacao = datetime.utcnow()
                        else:
                            novo_registro = EventosAtendentes(
                                data=data_registro,
                                atendente=operador_id,
                                nome_atendente=nome_operador,
                                evento=item.get("evento", ""),
                                parametro=item.get("parametro"),
                                nome_pausa=item.get("nomePausa"),
                                data_inicio=data_inicio_ev,
                                data_fim=data_fim_ev,
                                sinaliza_duracao=sinaliza_duracao,
                                duracao=duracao_ev,
                                complemento=item.get("complemento"),
                                data_importacao=datetime.utcnow()
                            )
                            db.session.add(novo_registro)

                        total_registros += 1

                    except Exception as e:
                        app.logger.error(f"[ERRO] {nome_operador} evento em {item.get('data')}: {str(e)}")

                offset += 1000

        if not dados_encontrados:
            app.logger.info("Nenhum dado encontrado nos últimos 2 dias. Tentando buscar dados apenas de hoje.")
            # Repetir o processo apenas para hoje (pode copiar o código acima adaptando data_inicio e final_date para hoje)
            # Para não ficar muito longo aqui, me avise se quiser que eu faça essa parte também.

        db.session.commit()
        return jsonify({"status": "success", "message": f"{total_registros} registros de eventos inseridos ou atualizados."})

    except Exception as e:
        app.logger.error(f"Erro na tarefa importar_eventos: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500'''

'''def processar_e_armazenar_eventos(dias=1, incremental=False):
    hoje = datetime.now().date()
    ontem = hoje - timedelta(days=1)

    # Autenticação
    auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
    if "access_token" not in auth_response:
        return {"status": "error", "message": "Falha na autenticação"}
    access_token = auth_response["access_token"]

    # Intervalo de datas para busca
    data_inicial = hoje #- timedelta(days=dias)
    data_final = hoje

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

    # Se não for incremental, limpa a tabela
    if not incremental:
        try:
            EventosAtendentes.query.delete()
            db.session.commit()
            print("Tabela EventosAtendentes limpa com sucesso.")
        except Exception as e:
            db.session.rollback()
            return {"status": "error", "message": f"Erro ao limpar a tabela: {str(e)}"}

    # Funções auxiliares internas para parsing seguro
    def parse_data(data_str):
        if not data_str or data_str.strip() in ["-", ""]:
            return None
        for fmt in ["%d/%m/%Y", "%Y/%m/%d", "%Y-%m-%d"]:
            try:
                return datetime.strptime(data_str, fmt).date()
            except ValueError:
                continue
        return None

    def parse_datetime(dt_str):
        if not dt_str or dt_str.strip() in ["-", ""]:
            return None
        for fmt in ["%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y/%m/%d %H:%M:%S"]:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        return None

    def parse_timedelta(valor):
        if not valor or valor.strip() in ["-", ""]:
            return None
        try:
            h, m, s = map(int, valor.split(":"))
            return timedelta(hours=h, minutes=m, seconds=s)
        except ValueError:
            return None

    def parse_bool(valor):
        return str(valor).strip() in ["1", "True", "true"]

    for operador_id in operadores_ids:
        nome_operador = OPERADORES_MAP.get(operador_id, "Desconhecido")

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

                print(f"[{nome_operador}] Buscando eventos de {inicio} até {fim}, offset {offset}")
                response = utils.atendenteEventosData(access_token, params)
                dados = response.get("result", {}).get("data", [])

                if not dados:
                    break

                for item in dados:
                    try:
                        registro = EventosAtendentes(
                            data=parse_data(item.get("data")),
                            atendente=operador_id,
                            nome_atendente=nome_operador,
                            evento=item.get("evento") or "-",
                            parametro=item.get("parametro") or None,
                            nome_pausa=item.get("nomePausa") or None,
                            data_inicio=parse_datetime(item.get("dataInicio")),
                            data_fim=parse_datetime(item.get("dataFim")),
                            sinaliza_duracao=parse_bool(item.get("sinalizaDuracao")),
                            duracao=parse_timedelta(item.get("duracao")),
                            complemento=item.get("complemento") or None,
                            data_importacao=datetime.utcnow()
                        )
                        db.session.add(registro)
                        total_registros += 1

                    except Exception as e:
                        print(f"[ERRO] {nome_operador} em {item.get('dataInicio')}: {str(e)}")

                db.session.flush()
                offset += 1000

            print(f"[{nome_operador}] Total eventos inseridos de {inicio} a {fim}: {total_registros}")

        db.session.commit()

    return {"status": "success", "message": "Eventos importados com sucesso."}'''

'''def importar_detalhes_chamadas_individual(nome_operador):
    def gerar_intervalos_diarios(inicio, fim, dias_por_lote=7):
        data_atual = inicio
        while data_atual <= fim:
            data_final = min(data_atual + timedelta(days=dias_por_lote - 1), fim)
            yield data_atual, data_final
            data_atual = data_final + timedelta(days=1)

    hoje = datetime.now().date()
    data_inicio = hoje - timedelta(days=180)

    auth_response = authenticate_relatorio(CREDENTIALS["username"], CREDENTIALS["password"])
    if "access_token" not in auth_response:
        print("❌ Falha na autenticação")
        return {"status": "error", "message": "Falha na autenticação"}

    access_token = auth_response["access_token"]
    total_registros = 0
    data_importacao_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for inicio_lote, fim_lote in gerar_intervalos_diarios(data_inicio, hoje, dias_por_lote=7):
        offset = 0
        while True:
            params = {
                "initial_date": inicio_lote.strftime('%d/%m/%Y'),  # formato dd/mm/yyyy como usado no Postman
                "final_date": fim_lote.strftime('%d/%m/%Y'),
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

            print(f"\n🔍 Enviando requisição para operador {nome_operador}...")
            print(f"📅 Período: {inicio_lote} até {fim_lote}")
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
                print(f"⚠️ Nenhum dado retornado para operador {nome_operador}")
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
    return {"status": "success", "total_registros": total_registros}'''