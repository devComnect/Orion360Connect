from flask import request, jsonify, Blueprint
from datetime import datetime
from application.models import EventFault, db

eventos_bp = Blueprint('eventos_bp', __name__, url_prefix='/eventos')

@eventos_bp.route("/eventos-falha/registrar", methods=["POST"])
def registrar_evento_falha():
    try:
        service_id = request.form.get("chamado_id")
        id = request.form.get("falha_id")
        data_evento = request.form.get("data_evento")
        hora_evento = request.form.get("hora_evento")

        # Monta TIME_SLA
        time_sla = datetime.strptime(f"{data_evento} {hora_evento}", "%Y-%m-%d %H:%M")

        #  Busca o registro existente
        evento = EventFault.query.get(id)

        if not evento:
            return jsonify({"error": "ID não encontrado na tabela EventFault"}), 404

        # Atualiza campos
        evento.SERVICEID = service_id
        evento.TIME_SLA = time_sla
        evento.PRODUCTID = None

        db.session.commit()

        return jsonify({"success": True, "message": "Evento atualizado com sucesso!"})

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
    try:
        ids = request.json.get("ids", [])

        if not ids:
            return jsonify({"error": "Nenhum ID enviado"}), 400

        # Para cada ID, limpa o registro
        for event_id in ids:
            ev = EventFault.query.filter_by(ID=event_id).first()
            if ev:
                ev.SERVICEID = None
                ev.TIME_SLA = None
                # OPCIONAL: limpar também o texto
                # ev.SMS_RETURN = None

        db.session.commit()
        return jsonify({"success": True, "message": "Evento(s) limpo(s) com sucesso!"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
