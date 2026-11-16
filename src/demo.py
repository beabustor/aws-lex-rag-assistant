"""CLI con NLU simulado por reglas; no utiliza Amazon Lex."""
from src.lambda_handler import lambda_handler
from src.rag import tokens


def main():
    state = {}
    print("Demo local. Sin conexión con AWS. Escribe salir para terminar.")
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text.lower() == "salir":
            break
        words = tokens(text)
        if words & {"agente", "persona", "humano"}:
            name = "HablarConAgente"
        elif words & {"horario", "horarios", "abris"}:
            name = "ConsultarHorario"
        elif words & {"servicios", "ofreceis"}:
            name = "ConsultarServicios"
        elif words & {"soporte", "incidencia"} or state.get("dialogAction", {}).get("type") == "ElicitSlot":
            name = "SolicitarSoporte"
        elif words & {"condiciones", "precio", "precios", "cuesta", "documentacion"}:
            name = "ConsultarFAQ"
        else:
            name = "FallbackIntent"
        previous = state.get("intent", {})
        slots = previous.get("slots", {}) if previous.get("name") == name and previous.get("state") == "InProgress" else {}
        if name == "SolicitarSoporte":
            for slot, choices in [("Servicio", {"web", "app"}), ("Categoria", {"error", "acceso"})]:
                matches = words & choices
                if len(matches) == 1:
                    slots[slot] = {"value": {"interpretedValue": next(iter(matches))}}
        event = {"inputTranscript": text, "sessionState": {"intent": {"name": name, "slots": slots}, "sessionAttributes": state.get("sessionAttributes", {})}}
        result = lambda_handler(event)
        state = result["sessionState"]
        print(result["messages"][0]["content"])


if __name__ == "__main__":
    main()
