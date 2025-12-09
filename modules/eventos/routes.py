from flask import request, jsonify, Blueprint
from datetime import datetime
from application.models import EventFault, db

eventos_bp = Blueprint('eventos_bp', __name__, url_prefix='/eventos')

@eventos_bp.route("/eventos-falha/registrar", methods=["POST"])
def registrar_evento_falha():
    try:
        service_id = request.form.get("chamado_id")
        data_evento = request.form.get("data_evento")
        hora_evento = request.form.get("hora_evento")
        id = request.form.get("falha_id")

        time_sla = datetime.strptime(f"{data_evento} {hora_evento}", "%Y-%m-%d %H:%M")

        # Apaga tudo que existir na tabela (garante apenas 1 registro)
        EventFault.query.delete()

        # Cria o único registro permitido
        evento = EventFault(
            ID=id,
            SERVICEID=service_id,
            TIME_SLA=time_sla,
            PRODUCTID=None,
            SMS_RETURN=""
        )

        db.session.add(evento)
        db.session.commit()

        return jsonify({"success": True, "message": "Registro salvo com sucesso!"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@eventos_bp.route("/eventos-falha/listar", methods=["GET"])
def listar_eventos_falha():
    try:
        eventos = EventFault.query.filter(
            EventFault.SERVICEID.isnot(None),
            EventFault.TIME_SLA.isnot(None)
        ).all()

        lista = [
            {
                "id": ev.ID,
                "texto": ev.SERVICEID,
                "sla": ev.TIME_SLA.strftime("%d/%m/%Y %H:%M")
            }
            for ev in eventos
        ]

        return jsonify(lista)

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@eventos_bp.route("/eventos-falha/limpar", methods=["POST"])
def limpar_eventos_falha():
    EventFault.query.delete()
    db.session.commit()
    return jsonify({"success": True, "message": "Evento(s) limpo(s) com sucesso!"})

