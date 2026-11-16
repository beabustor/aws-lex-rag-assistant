"""Contrato Lex V2 local. Despliegue y permisos AWS pendientes de verificar."""
from copy import deepcopy
from src.rag import retrieve

SERVICES = {"web", "app"}
CATEGORIES = {"acceso", "error"}


def value(slots, name):
    return ((slots.get(name) or {}).get("value") or {}).get("interpretedValue", "").lower()


def lambda_handler(event, context=None):
    state = deepcopy(event.get("sessionState") or {})
    intent = state.setdefault("intent", {"name": "FallbackIntent"})
    slots = intent.setdefault("slots", {})
    attrs = state.setdefault("sessionAttributes", {})
    name = intent.get("name", "FallbackIntent")
    attrs["handoffRequested"] = "false"

    def reply(text, slot=None):
        state["dialogAction"] = {"type": "ElicitSlot", "slotToElicit": slot} if slot else {"type": "Close"}
        intent["state"] = "InProgress" if slot else "Fulfilled"
        return {"sessionState": state, "messages": [{"contentType": "PlainText", "content": text}]}

    if name == "FallbackIntent":
        try:
            attempts = max(0, int(attrs.get("fallbackCount", "0"))) + 1
        except (TypeError, ValueError):
            attempts = 1
        attrs["fallbackCount"] = str(attempts)
        if attempts >= 2:
            attrs["handoffRequested"] = "true"
            return reply("No he logrado entenderte. Solicito atención humana; esta demo no conecta con un agente real.")
        return reply("¿Quieres consultar horarios, servicios, soporte o hablar con un agente?")

    attrs["fallbackCount"] = "0"
    if name == "HablarConAgente":
        attrs["handoffRequested"] = "true"
        return reply("Solicitud de atención humana registrada. La transferencia real requiere Amazon Connect.")
    if name == "SolicitarSoporte":
        for slot, allowed, prompt in [
            ("Servicio", SERVICES, "¿El problema afecta a la web o a la app?"),
            ("Categoria", CATEGORIES, "¿Es un problema de acceso o un error?"),
        ]:
            if value(slots, slot) not in allowed:
                slots[slot] = None
                return reply(prompt, slot)
        return reply("He recogido el servicio y la categoría. Esta demo no crea un ticket real.")
    queries = {"ConsultarHorario": "horarios", "ConsultarServicios": "servicios"}
    if name in queries or name == "ConsultarFAQ":
        try:
            return reply(retrieve(queries.get(name, event.get("inputTranscript", ""))))
        except (OSError, UnicodeError):
            return reply("No puedo consultar la documentación ahora. Inténtalo más tarde o solicita un agente.")
    intent["name"] = "FallbackIntent"
    return reply("Esta intención no está configurada. Pregunta por servicios, horarios o soporte.")
