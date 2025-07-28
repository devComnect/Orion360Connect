from flask import Blueprint, jsonify, request
from settings import endpoints
import requests, json, os
import calendar
from modules.deskmanager.authenticate.routes import token_desk
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date
from application.models import db, Chamado
from sqlalchemy import extract, func


dashboard_bp = Blueprint('dashboard_bp', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/ChamadosSuporte/fila', methods=['POST'])
def listar_chamados_fila():
    token_response = token_desk()

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

    try:
        response = requests.post(
            'https://api.desk.ms/ChamadosSuporte/lista',
            headers={
                'Authorization': f'{token_response}',
                'Content-Type': 'application/json'
            },
            json=payload
        )
        # Verifica se a requisição foi bem sucedida
        if response.status_code == 200:
            data = response.json()
            
            # Captura apenas o total do retorno
            total_chamados = data.get("total", "0")
            
            return jsonify({
                "status": "success",
                "total_chamados": total_chamados
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Erro na requisição",
                "status_code": response.status_code
            }), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao conectar com o servidor",
            "details": str(e)
        }), 500

'''@dashboard_bp.route('/ChamadosSuporte/sla_andamento', methods=['POST'])
def listar_sla_andamento():
    token_response = token_desk()
    url = endpoints.LISTA_CHAMADOS_SUPORTE

    payload = {
        "Pesquisa": "",
        "Tatual": "",
        "Ativo": "EmAberto",
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
            "Sla1Expirado": "on",
            "Sla2Expirado": "on",
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

    try:
        response = requests.post(
            url,
            headers={
                'Authorization': f'{token_response}',
                'Content-Type': 'application/json'
            },
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            chamados = data.get("root", [])

            chamados_suporte = [
                c for c in chamados 
                if c.get("NomeGrupo", "").strip().upper() == "SUPORTE COMNECT - N1"

            ]

            hoje = datetime.now()

            sla1_expirado = 0
            sla1_nao_expirado = 0
            sla2_expirado = 0
            sla2_nao_expirado = 0

            codigos_sla1 = []
            codigos_sla2 = []

            for chamado in chamados_suporte:
                data_criacao = chamado.get("DataCriacao")
                if data_criacao and datetime.strptime(data_criacao, "%Y-%m-%d").month == hoje.month:
                    sla1 = chamado.get("Sla1Expirado", "").upper()
                    sla2 = chamado.get("Sla2Expirado", "").upper()
                    cod_chamado = chamado.get("CodChamado")

                    if sla1 == "S":
                        sla1_expirado += 1
                        codigos_sla1.append(cod_chamado)
                    elif sla1 == "N":
                        sla1_nao_expirado += 1

                    if sla2 == "S":
                        sla2_expirado += 1
                        codigos_sla2.append(cod_chamado)
                    elif sla2 == "N":
                        sla2_nao_expirado += 1

            return jsonify({
                "status": "success",
                "sla1_expirado": sla1_expirado,
                "sla1_nao_expirado": sla1_nao_expirado,
                "sla2_expirado": sla2_expirado,
                "sla2_nao_expirado": sla2_nao_expirado,
                "total": len(chamados_suporte),
                "codigos_sla1": codigos_sla1,
                "codigos_sla2": codigos_sla2,
                "grupo_filtrado": "SUPORTE",
                "mes_referencia": hoje.strftime("%Y-%m")
            })

        return jsonify({
            "status": "error",
            "message": "Erro na requisição",
            "status_code": response.status_code
        }), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao conectar com o servidor",
            "details": str(e)
        }), 500'''

def parse_tempo(s):
    try:
        negativo = s.startswith('-')
        h, m, s = map(int, s.replace('-', '').split(':'))
        delta = timedelta(hours=h, minutes=m, seconds=s)
        return -delta if negativo else delta
    except:
        return None

@dashboard_bp.route('/ChamadosSuporte/sla_andamento', methods=['POST'])
def listar_sla_andamento():
    try:
        hoje = datetime.now()

        chamados = Chamado.query.filter(
            db.extract('month', Chamado.data_criacao) == hoje.month,
            db.extract('year', Chamado.data_criacao) == hoje.year,
            Chamado.nome_grupo.ilike('%SUPORTE%'),
            ~Chamado.nome_status.in_(["Resolvido", "Cancelado"])
        ).all()

        sla1_expirado = 0
        sla1_nao_expirado = 0
        sla2_expirado = 0
        sla2_nao_expirado = 0
        sla1_quase_estourando = 0
        sla2_quase_estourando = 0

        codigos_sla1 = []
        codigos_sla2 = []
        codigos_sla1_critico = []
        codigos_sla2_critico = []

        for chamado in chamados:
            sla1 = (chamado.sla_atendimento or "").strip().upper()
            sla2 = (chamado.sla_resolucao or "").strip().upper()
            restante1_raw = (chamado.restante_p_atendimento or "").strip()
            restante2_raw = (chamado.restante_s_atendimento or "").strip()
            restante1 = parse_tempo(restante1_raw)
            restante2 = parse_tempo(restante2_raw)
            cod = chamado.cod_chamado

            # SLA 1 - Atendimento
            if sla1 == "S" or (restante1 is not None and restante1 <= timedelta(minutes=0)):
                sla1_expirado += 1
                codigos_sla1.append(cod)
            elif restante1 is not None and restante1 <= timedelta(minutes=5):
                sla1_quase_estourando += 1
                codigos_sla1_critico.append(cod)
            elif restante1 is not None:
                sla1_nao_expirado += 1

            # SLA 2 - Resolução
            if sla2 == "S" or (restante2 is not None and restante2 <= timedelta(minutes=0)):
                sla2_expirado += 1
                codigos_sla2.append(cod)
            elif restante2 is not None and restante2 <= timedelta(minutes=5):
                sla2_quase_estourando += 1
                codigos_sla2_critico.append(cod)
            elif restante2 is not None:
                sla2_nao_expirado += 1

        return jsonify({
            "status": "success",
            "sla1_expirado": sla1_expirado,
            "sla1_nao_expirado": sla1_nao_expirado,
            "sla1_quase_estourando": sla1_quase_estourando,
            "sla2_expirado": sla2_expirado,
            "sla2_nao_expirado": sla2_nao_expirado,
            "sla2_quase_estourando": sla2_quase_estourando,
            "total": len(chamados),
            "codigos_sla1": codigos_sla1,
            "codigos_sla2": codigos_sla2,
            "codigos_sla1_critico": codigos_sla1_critico,
            "codigos_sla2_critico": codigos_sla2_critico,
            "grupo_filtrado": "SUPORTE",
            "mes_referencia": hoje.strftime("%Y-%m")
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao consultar os dados",
            "details": str(e)
        }), 500

# Rota oficial funcional
'''@dashboard_bp.route('/ChamadosSuporte/contagem_mes_atual', methods=['POST'])
def contar_chamados_mes_atual():
    try:
        token_response = token_desk()
        if not token_response:
            return jsonify({"status": "error", "message": "Falha na autenticação"}), 401

        hoje = datetime.now()

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
            headers={'Authorization': f'{token_response}', 'Content-Type': 'application/json'},
            json=payload,
        )
        response.raise_for_status()
        chamados_api = response.json().get("root", [])

        def data_valida(data_str):
            return data_str and data_str != '0000-00-00'

        with db.session.begin():
            db.session.query(Chamado).delete()

            for chamado in chamados_api:
                try:
                    chave = chamado.get('Chave')
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

                    novo_chamado = Chamado(
                        chave=chamado.get('Chave'),
                        cod_chamado=chamado.get('CodChamado'),
                        data_criacao=data_criacao,
                        nome_status=chamado.get('NomeStatus'),
                        nome_grupo=chamado.get('NomeGrupo'),
                        cod_solicitacao=chamado.get('CodSolicitacao'),
                        operador=chamado.get('NomeOperador'),
                        sla_atendimento = chamado.get('Sla1Expirado'),
                        sla_resolucao = chamado.get('Sla2Expirado'),
                        cod_categoria_tipo = chamado.get('CodCategoriaTipo'),
                        data_finalizacao=data_finalizacao,
                        mes_referencia=f"{data_criacao.year}-{data_criacao.month:02d}",
                        data_importacao=datetime.now()
                    )
                    db.session.add(novo_chamado)

                except ValueError as e:
                    print(f"Erro ao processar chamado {chamado.get('CodChamado')}: {str(e)}")
                    continue

        total_mes_atual = Chamado.query.filter(
            db.extract('month', Chamado.data_criacao) == hoje.month,
            db.extract('year', Chamado.data_criacao) == hoje.year
        ).count()

        total_abertos = Chamado.query.filter(
            db.extract('month', Chamado.data_criacao) == hoje.month,
            db.extract('year', Chamado.data_criacao) == hoje.year,
            ~Chamado.nome_status.in_(["Resolvido", "Cancelado"])
        ).count()

        total_finalizados = Chamado.query.filter(
            db.extract('month', Chamado.data_criacao) == hoje.month,
            db.extract('year', Chamado.data_criacao) == hoje.year,
            Chamado.nome_status.in_(["Resolvido", "Cancelado"]),
            Chamado.data_finalizacao != None
        ).count()

        return jsonify({
            "status": "success",
            "total_mes_atual": total_mes_atual,
            "total_abertos": total_abertos,
            "total_finalizados": total_finalizados,
            "mes_referencia": f"{hoje.month}/{hoje.year}",
            "registros_processados": len(chamados_api)
        })

    except requests.exceptions.RequestException as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Erro na comunicação com a API Desk",
            "details": str(e)
        }), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Erro inesperado",
            "details": str(e)
        }), 500'''

@dashboard_bp.route('/ChamadosSuporte/estatisticas_mensais', methods=['GET'])
def estatisticas_chamados():
    try:
        # Obter todos os chamados abertos (não resolvidos ou cancelados)
        chamados_abertos = db.session.query(
            Chamado.chave, 
            Chamado.nome_status,
            Chamado.nome_grupo
        ).filter(
            Chamado.nome_status.notin_(['cancelado', 'resolvido'])
        ).all()

        # Processar os resultados
        status_counts = {}
        grupos = set()
        
        for chamado in chamados_abertos:
            status = chamado.nome_status
            grupo = chamado.nome_grupo
            grupos.add(grupo)
            
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1

        # Formatar resposta para o gráfico
        labels = list(status_counts.keys())
        dados = list(status_counts.values())
        
        return jsonify({
            "status": "success",
            "data": {
                "labels": labels,
                "datasets": [{
                    "data": dados,
                    "backgroundColor": [
                        '#FF6384', '#36A2EB', '#FFCE56',
                        '#4BC0C0', '#9966FF', '#FF9F40'
                    ]
                }],
                "total": sum(dados),
                "grupos": list(grupos)  # Lista de grupos associados
            },
            "chamados_abertos": [{
                "chave": chamado.chave,  # Retornando chave em vez de id
                "nome_status": chamado.nome_status,
                "nome_grupo": chamado.nome_grupo
            } for chamado in chamados_abertos]
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500
    
@dashboard_bp.route('/ChamadosSuporte/por_grupo_mes_atual', methods=['GET'])
def chamados_por_grupo_mes():

    try:
        hoje = datetime.now()

        # Consulta agrupando por grupo
        resultados = db.session.query(
            Chamado.nome_grupo,
            func.count(Chamado.id).label('total')
        ).filter(
            extract('month', Chamado.data_criacao) == hoje.month,
            extract('year', Chamado.data_criacao) == hoje.year
        ).group_by(
            Chamado.nome_grupo
        ).order_by(
            func.count(Chamado.id).desc()
        ).all()

        labels = [r[0] or "Sem Grupo" for r in resultados]
        dados = [r[1] for r in resultados]

        return jsonify({
            "status": "success",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": "Chamados por Grupo",
                    "data": dados,
                    "backgroundColor": [
                        '#007bff', '#6610f2', '#6f42c1',
                        '#e83e8c', '#fd7e14', '#20c997',
                        '#17a2b8', '#6c757d', '#343a40'
                    ] * len(labels)  # repete as cores se precisar
                }]
            },
            "mes_referencia": f"{hoje.month}/{hoje.year}"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao buscar dados por grupo",
            "details": str(e)
        }), 500
    
@dashboard_bp.route('/ChamadosSuporte/por_tipo_solicitacao_mes_atual', methods=['POST'])
def chamados_por_tipo_solicitacao_hoje():
    try:
        hoje = datetime.now().date()
        inicio_dia = datetime.combine(hoje, datetime.min.time())
        fim_dia = inicio_dia + timedelta(days=1)

        tipos_desejados = ['000003', '000101', '000004', '000060', '000001', '000071']
        mapeamento_tipos = {
            '000101': 'Portal Comnect',
            '000071': 'Interno',
            '000003': 'E-mail',
            '000004': 'Telefone',
            '000001': 'Portal Solicitante',
            '000060': 'WhatsApp'
        }

        # Consulta agrupando por tipo e hora
        resultados = db.session.query(
            Chamado.cod_solicitacao,
            func.extract('hour', Chamado.data_criacao).label('hora'),
            func.count(Chamado.id)
        ).filter(
            Chamado.cod_solicitacao.in_(tipos_desejados),
            Chamado.data_criacao >= inicio_dia,
            Chamado.data_criacao < fim_dia
        ).group_by(
            Chamado.cod_solicitacao,
            'hora'
        ).all()

        # Inicializar estrutura: {tipo: [0, 0, ..., 0] para cada hora}
        dados_por_tipo = {
            cod: [0] * 24 for cod in tipos_desejados
        }

        # Preencher os dados
        for cod_tipo, hora, total in resultados:
            hora = int(hora)
            if cod_tipo in dados_por_tipo and 0 <= hora <= 23:
                dados_por_tipo[cod_tipo][hora] = total

        cores = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']

        # Construir os datasets
        datasets = []
        for i, cod in enumerate(tipos_desejados):
            datasets.append({
                'label': mapeamento_tipos.get(cod, cod),
                'data': dados_por_tipo[cod],
                'backgroundColor': cores[i],
                'borderColor': cores[i],
                'fill': False,
                'tension': 0.3,
                'borderWidth': 2
            })

        return jsonify({
            'status': 'success',
            'data': {
                'labels': [f"{h:02d}h" for h in range(24)],  # Eixo X: horas
                'datasets': datasets
            },
            'data_referencia': hoje.strftime('%d/%m/%Y')
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@dashboard_bp.route('/ChamadosSuporte/abertos_vs_resolvidos', methods=['POST'])
def chamados_abertos_vs_resolvidos():
    try:
        hoje = datetime.now().date()
        inicio_dia = datetime.combine(hoje, datetime.min.time())
        fim_dia = inicio_dia + timedelta(days=1)

        horas_do_dia = list(range(0, 24))
        total_por_hora = {hora: 0 for hora in horas_do_dia}
        resolvidos_por_hora = {hora: 0 for hora in horas_do_dia}

        # Chamados abertos no dia atual (por hora da criação)
        resultados_abertos = db.session.query(
            func.extract('hour', Chamado.data_criacao).label('hora'),
            func.count(Chamado.id)
        ).filter(
            Chamado.data_criacao >= inicio_dia,
            Chamado.data_criacao < fim_dia
        ).group_by('hora').all()

        for hora, total in resultados_abertos:
            total_por_hora[int(hora)] = total

        # Chamados resolvidos no dia atual (por hora da finalização)
        resultados_resolvidos = db.session.query(
            func.extract('hour', Chamado.data_finalizacao).label('hora'),
            func.count(Chamado.id)
        ).filter(
            Chamado.data_finalizacao >= inicio_dia,
            Chamado.data_finalizacao < fim_dia,
            Chamado.nome_status == 'Resolvido'
        ).group_by('hora').all()

        for hora, total in resultados_resolvidos:
            resolvidos_por_hora[int(hora)] = total

        return jsonify({
            'status': 'success',
            'labels': [f'{h:02d}:00' for h in horas_do_dia],
            'datasets': [
                {
                    'label': 'Chamados Abertos',
                    'data': [total_por_hora[h] for h in horas_do_dia],
                    'backgroundColor': 'rgba(255, 99, 132, 0.7)',
                    'borderColor': 'rgba(255, 99, 132, 1)',
                    'borderWidth': 2
                },
                {
                    'label': 'Chamados Resolvidos',
                    'data': [resolvidos_por_hora[h] for h in horas_do_dia],
                    'backgroundColor': 'rgba(75, 192, 75, 0.7)',
                    'borderColor': 'rgba(75, 192, 192, 1)',
                    'borderWidth': 2
                }
            ],
            'resumo': {
                'total_abertos': sum(total_por_hora.values()),
                'total_resolvidos': sum(resolvidos_por_hora.values()),
                'diferenca': sum(total_por_hora.values()) - sum(resolvidos_por_hora.values())
            },
            'data_referencia': hoje.strftime('%d/%m/%Y')
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

'''@dashboard_bp.route('/ChamadosSuporte/sla_andamento_grupos', methods=['POST'])
def listar_sla_andamento_grupos():
    token_response = token_desk()
    url = endpoints.LISTA_CHAMADOS_SUPORTE

    payload = {
        "Pesquisa": "",
        "Tatual": "",
        "Ativo": "EmAberto",
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
            "Sla1Expirado": "on",
            "Sla2Expirado": "on",
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

    try:
        response = requests.post(
            url,
            headers={
                'Authorization': f'{token_response}',
                'Content-Type': 'application/json'
            },
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            chamados = data.get("root", [])

            grupos_desejados = ['INFOSEC - N2','DEV - N2', 'NOC - N2', "CSM"]
            chamados_grupos = [
                c for c in chamados
                if any(grupo in c.get("NomeGrupo", "").upper() for grupo in grupos_desejados)
            ]

            # Nova filtragem: remover prioridades indesejadas
            prioridades_ignorar = {"5 - Planejada", "4 - Baixa"}
            chamados_grupos = [
                c for c in chamados_grupos
                if c.get("NomePrioridade") not in prioridades_ignorar
            ]

            prioridades_ignorar = {"5 - Planejada", "4 - Baixa"}
                chamados_grupos = [
                    c for c in chamados_grupos
                    if not (
                        c.get("NomeGrupo", "").upper() == "DEV" and
                        c.get("NomePrioridade") in prioridades_ignorar
                    )
                ]

            hoje = datetime.now()
            primeiro_dia_mes = hoje.replace(day=1)

            sla1_expirado = 0
            sla1_nao_expirado = 0
            sla2_expirado = 0
            sla2_nao_expirado = 0

            chamados_com_tempo = []

            for chamado in chamados_grupos:
                data_criacao = chamado.get("DataCriacao")
                if data_criacao and datetime.strptime(data_criacao, "%Y-%m-%d").month == hoje.month:
                    # SLA 1
                    tempo_restante_sla1 = chamado.get("TempoRestantePrimeiroAtendimento", "00:00:00")
                    horas_sla1, minutos_sla1, segundos_sla1 = map(int, tempo_restante_sla1.split(':'))
                    total_segundos_sla1 = horas_sla1 * 3600 + minutos_sla1 * 60 + segundos_sla1

                    sla1_total = 1800  # 30 minutos padrão
                    porcentagem_sla1 = (total_segundos_sla1 / sla1_total) * 100 if sla1_total else 0

                    sla1 = chamado.get("Sla1Expirado", "").upper()
                    if sla1 == "S":
                        sla1_expirado += 1
                        status_sla1 = "expirado"
                    elif sla1 == "N":
                        sla1_nao_expirado += 1
                        status_sla1 = "alerta" if porcentagem_sla1 < 20 else "dentro_prazo"

                    # SLA 2
                    tempo_restante_sla2 = chamado.get("TempoRestanteSegundoAtendimento", "00:00:00")
                    horas_sla2, minutos_sla2, segundos_sla2 = map(int, tempo_restante_sla2.split(':'))
                    total_segundos_sla2 = horas_sla2 * 3600 + minutos_sla2 * 60 + segundos_sla2

                    sla2_total = 86400  # 24 horas padrão
                    porcentagem_sla2 = (total_segundos_sla2 / sla2_total) * 100 if sla2_total else 0

                    sla2 = chamado.get("Sla2Expirado", "").upper()
                    if sla2 == "S":
                        sla2_expirado += 1
                        status_sla2 = "expirado"
                    elif sla2 == "N":
                        sla2_nao_expirado += 1
                        status_sla2 = "alerta" if porcentagem_sla2 < 20 else "dentro_prazo"

                    chamados_com_tempo.append({
                        **chamado,
                        "PorcentagemSLA1": round(porcentagem_sla1, 2),
                        "StatusSLA1": status_sla1,
                        "PorcentagemSLA2": round(porcentagem_sla2, 2),
                        "StatusSLA2": status_sla2
                    })

            return jsonify({
                "status": "success",
                "sla1_expirado": sla1_expirado,
                "sla1_nao_expirado": sla1_nao_expirado,
                "sla2_expirado": sla2_expirado,
                "sla2_nao_expirado": sla2_nao_expirado,
                "total": len(chamados_grupos),
                "grupo_filtrado": ", ".join(grupos_desejados),
                "mes_referencia": hoje.strftime("%Y-%m"),
                "chamados": chamados_com_tempo
            })

        return jsonify({
            "status": "error",
            "message": "Erro na requisição",
            "status_code": response.status_code
        }), response.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "message": "Erro ao conectar com o servidor",
            "details": str(e)
        }), 500'''

@dashboard_bp.route('/ChamadosSuporte/sla_andamento_grupos', methods=['POST'])
def listar_sla_andamento_grupos():
    grupos_desejados = ['INFOSEC - N2', 'DEV - N2', 'NOC - N2', 'CSM']
    mes_referencia_atual = datetime.now().strftime('%Y-%m')

    chamados = Chamado.query.filter(
        Chamado.nome_status.notin_(['Resolvido', 'Cancelado']),
        Chamado.nome_prioridade.notin_(['5 - Planejada', '4 - Baixa']),
        db.or_(
            Chamado.nome_grupo.ilike('%DEV - N2%'),
            Chamado.nome_grupo.ilike('%INFOSEC - N2%'),
            Chamado.nome_grupo.ilike('%CSM%'),
            Chamado.nome_grupo.ilike('%NOC - N2%')
        ),
        Chamado.sla_atendimento.in_(['S', 'N']),
        Chamado.sla_resolucao.in_(['S', 'N']),
    ).all()

    # Contadores
    sla1_expirado = sla1_nao_expirado = sla1_quase_estourando = 0
    sla2_expirado = sla2_nao_expirado = sla2_quase_estourando = 0

    # Listas de códigos
    codigos_sla1 = []
    codigos_sla2 = []
    codigos_sla1_critico = []
    codigos_sla2_critico = []

    for chamado in chamados:
        restante1_raw = (chamado.restante_p_atendimento or "").strip()
        restante2_raw = (chamado.restante_s_atendimento or "").strip()
        restante1 = parse_tempo(restante1_raw)
        restante2 = parse_tempo(restante2_raw)
        cod = chamado.cod_chamado

        # SLA Atendimento
        if chamado.sla_atendimento == "S":
            sla1_expirado += 1
            codigos_sla1.append(cod)
        elif chamado.sla_atendimento == "N" and restante1 is not None:
            if timedelta(minutes=0) < restante1 <= timedelta(minutes=5):
                sla1_quase_estourando += 1
                codigos_sla1_critico.append(cod)
            elif restante1 > timedelta(minutes=10):
                sla1_nao_expirado += 1
            else:
                sla1_expirado += 1
                codigos_sla1.append(cod)

        # SLA Resolução
        if chamado.sla_resolucao == "S":
            sla2_expirado += 1
            codigos_sla2.append(cod)
        elif chamado.sla_resolucao == "N" and restante2 is not None:
            if timedelta(minutes=0) < restante2 <= timedelta(minutes=5):
                sla2_quase_estourando += 1
                codigos_sla2_critico.append(cod)
            elif restante2 > timedelta(minutes=10):
                sla2_nao_expirado += 1
            else:
                sla2_expirado += 1
                codigos_sla2.append(cod)

    return jsonify({
        "status": "success",
        "sla1_expirado": sla1_expirado,
        "sla1_nao_expirado": sla1_nao_expirado,
        "sla1_quase_estourando": sla1_quase_estourando,
        "sla2_expirado": sla2_expirado,
        "sla2_nao_expirado": sla2_nao_expirado,
        "sla2_quase_estourando": sla2_quase_estourando,
        "codigos_sla1": codigos_sla1,
        "codigos_sla2": codigos_sla2,
        "codigos_sla1_critico": codigos_sla1_critico,
        "codigos_sla2_critico": codigos_sla2_critico,
        "total": len(chamados),
        "grupos": grupos_desejados,
        "mes_referencia": mes_referencia_atual
    })





