"""
BC Copilot — Agente con DOS herramientas (Fase 2).
Con una sola herramienta el agente decidia "usar o no". Con dos, decide CUAL.
El loop de tool calling es identico: solo crecio el toolbox (TOOLS + TOOL_SCHEMAS).
"""
import json

from provider import get_client, CHAT_MODEL
from rag import retrieve

client = get_client()


# --- Herramienta 1: buscar en la documentacion (RAG) ---
def buscar_en_documentacion(query):
    hits = retrieve(query)
    if not hits:
        return "No se encontraron resultados en la documentacion."
    return "\n\n".join(f"[fuente: {h['source']}]\n{h['text']}" for h in hits)


# --- Herramienta 2: extraer datos de un documento (por ahora, texto pegado) ---
def extraer_datos_de_documento(texto):
    prompt = (
        "Extrae los datos clave del siguiente documento (factura, reporte, etc.) "
        "y devolvelos en JSON con las claves que correspondan "
        "(por ejemplo: numero, fecha, proveedor, total, items). "
        "Devolve SOLO el JSON.\n\n"
        f"DOCUMENTO:\n{texto}"
    )
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},  # modo JSON: fuerza salida JSON valida
    )
    return resp.choices[0].message.content


# Mapa nombre -> funcion (el loop ejecuta lo que el modelo pida, sea cual sea)
TOOLS = {
    "buscar_en_documentacion": buscar_en_documentacion,
    "extraer_datos_de_documento": extraer_datos_de_documento,
}

# Esquemas que ve el modelo. Las 'description' son lo que usa para elegir.
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_en_documentacion",
            "description": (
                "Busca en la documentacion oficial de Business Central y devuelve los "
                "fragmentos mas relevantes con su fuente. Usala para preguntas sobre "
                "conceptos, configuracion o funcionamiento de Business Central."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "El tema a buscar"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "extraer_datos_de_documento",
            "description": (
                "Extrae datos estructurados (numero, fecha, proveedor, total, items) de "
                "un documento como una factura o un reporte. Usala cuando el usuario "
                "proporcione el texto de un documento para extraer su informacion."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {"type": "string", "description": "El texto del documento"}
                },
                "required": ["texto"],
            },
        },
    },
]

SYSTEM = (
    "Sos un asistente para consultores de Business Central. Tenes dos herramientas: "
    "una para buscar en la documentacion y otra para extraer datos de documentos. "
    "Elegi la adecuada segun la peticion. Al responder sobre documentacion, cita la "
    "fuente entre corchetes. No inventes."
)


def run_agent(pregunta, max_turns=5):
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": pregunta},
    ]
    for _ in range(max_turns):
        resp = client.chat.completions.create(
            model=CHAT_MODEL, messages=messages, tools=TOOL_SCHEMAS
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:
            return msg.content
        messages.append(msg)
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            print(f"  [agente] decide llamar -> {tc.function.name}")
            resultado = TOOLS[tc.function.name](**args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": resultado,
            })
    return "Se alcanzo el limite de pasos sin una respuesta final."


if __name__ == "__main__":
    factura = (
        "Extrae los datos de esta factura:\n\n"
        "Factura N 0001-00004521\n"
        "Fecha: 15/03/2026\n"
        "Proveedor: Distribuidora del Sur SA (CUIT 30-12345678-9)\n"
        "Item: Servicio de consultoria BC - 40 hs - $200000\n"
        "Total: $242000 (IVA incluido)"
    )
    for pregunta in [
        "Para que sirven los posting groups?",   # -> buscar_en_documentacion
        factura,                                  # -> extraer_datos_de_documento
        "Hola, gracias por la ayuda!",            # -> ninguna herramienta
    ]:
        print(f"\nPREGUNTA: {pregunta[:60]}...")
        print(f"RESPUESTA: {run_agent(pregunta)}")