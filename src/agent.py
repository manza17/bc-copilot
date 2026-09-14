"""
BC Copilot — Agente con DOS herramientas (Fase 2).
Con una sola herramienta el agente decidia "usar o no". Con dos, decide CUAL.
El loop de tool calling es identico: solo crecio el toolbox (TOOLS + TOOL_SCHEMAS).
"""
import json

from provider import get_client, CHAT_MODEL
from rag import retrieve
from doc_intel import extraer_factura

client = get_client()


# --- Herramienta 1: buscar en la documentacion (RAG) ---
def buscar_en_documentacion(query):
    hits = retrieve(query)
    if not hits:
        return "No se encontraron resultados en la documentacion."
    return "\n\n".join(f"[fuente: {h['source']}]\n{h['text']}" for h in hits)


# --- Herramienta 2: extraer datos de una factura (PDF/imagen) via Document Intelligence ---
def extraer_datos_de_documento(ruta_archivo):
    datos = extraer_factura(ruta_archivo)
    return json.dumps(datos, ensure_ascii=False)


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
                "Extrae datos estructurados de una factura (PDF o imagen) usando OCR. "
                "Usala cuando el usuario indique la ruta de un archivo de factura."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ruta_archivo": {
                        "type": "string",
                        "description": "La ruta al archivo de la factura (PDF o imagen)",
                    }
                },
                "required": ["ruta_archivo"],
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
    for pregunta in [
        "Para que sirven los posting groups?",                        # -> buscar_en_documentacion
        "Extrae los datos de la factura en data/sample-invoice.pdf",  # -> extraer_datos_de_documento
        "Hola, gracias por la ayuda!",                                # -> ninguna herramienta
    ]:
        print(f"\nPREGUNTA: {pregunta[:60]}...")
        print(f"RESPUESTA: {run_agent(pregunta)}")