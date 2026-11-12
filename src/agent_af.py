"""BC Copilot — Fase 2b: el mismo agente con Microsoft Agent Framework."""
import asyncio
import json
import os
from typing import Annotated

from dotenv import load_dotenv
from azure.identity import AzureCliCredential
from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient

from rag import retrieve
from doc_intel import extraer_factura
from pydantic import BaseModel, Field

class LineaFactura(BaseModel):
    # TODO 3B: descripcion, cantidad, precio_unitario, importe
    #(los numericos pueden faltar -> float | None)
    descripcion: str = Field(description="Descripcion del item de la factura")
    cantidad: float | None = Field(description="Cantidad del item de la factura")
    precio_unitario: float | None = Field(description="Precio unitario del item de la factura")
    importe: float | None = Field(description="Importe total del item de la factura")

class Factura(BaseModel):
    # TODO 3B: numero, fecha, proveedor, cliente, moneda (puede faltar),
    #          subtotal, impuestos, total, lineas: list[LineaFactura],
    #          campos_baja_confianza: list[str]   <- los que tengan confianza < 0.8
    numero: str = Field(description="Numero de la factura")
    fecha: str = Field(description="Fecha de la factura YYYY-MM-DD")
    proveedor: str = Field(description="Proveedor de la factura")
    cliente: str = Field(description="Cliente de la factura")
    moneda: str | None = Field(description="Moneda de la factura")
    subtotal: float = Field(description="Subtotal de la factura")
    impuestos: float = Field(description="Impuestos de la factura")
    total: float = Field(description="Total de la factura")
    lineas: list[LineaFactura] = Field(description="Lineas de la factura")
    campos_baja_confianza: list[str] = Field(description="Campos con confianza < 0.8")

load_dotenv()
#   - el docstring reemplaza la "description" de TOOL_SCHEMAS
#   - Annotated[str, Field(description=...)] reemplaza la de "query"
#   - agregá un print("  [tool] buscar_en_documentacion:", query) para ver cuándo la llama
@tool(approval_mode="never_require", 
      description="Busca en la documentacion oficial de Business Central y devuelve los fragmentos mas relevantes con su fuente. Usala para preguntas sobre conceptos, configuracion o funcionamiento de Business Central.")
def buscar_en_documentacion(query: Annotated[str, Field(description="El tema a buscar")]) -> str:
    print("  [tool] buscar_en_documentacion:", query)
    hits = retrieve(query)
    if not hits:
        return "No se encontraron resultados en la documentacion."
    return "\n\n".join(f"[fuente: {h['source']}]\n{h['text']}" for h in hits)


@tool(approval_mode="never_require", 
      description="Extrae datos estructurados de una factura (PDF o imagen) usando OCR. Usala cuando el usuario indique la ruta de un archivo de factura.")
def extraer_datos_factura(ruta_archivo: Annotated[str, Field(description="La ruta del archivo de factura (PDF o imagen).")]) -> str:
    print("  [tool] extraer_datos_factura:", ruta_archivo)
    datos = extraer_factura(ruta_archivo)
    return json.dumps(datos, ensure_ascii=False)


async def main():
    #(las 2 primeras salen de PROJECT_ENDPOINT y MODEL_DEPLOYMENT_NAME del .env)
    client = FoundryChatClient(
        project_endpoint=os.environ["PROJECT_ENDPOINT"],
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        credential=AzureCliCredential(),
    )
    #Usá las mismas instrucciones que agent.py.
    SYSTEM = (
    "Sos un asistente para consultores de Business Central. Tenes dos herramientas: "
    "una para buscar en la documentacion y otra para extraer datos de documentos. "
    "Elegi la adecuada segun la peticion. Al responder sobre documentacion, cita la "
    "fuente entre corchetes. No inventes. "
    "Solo podes hacer lo que permiten tus dos herramientas. No ofrezcas exportar, "
    "importar a Business Central ni otras acciones que no puedas ejecutar. "
    "No propongas siguientes pasos salvo que el usuario los pida."
)
    
    async with (
        Agent(
            client=client,
            name="bc-copilot",
            instructions=SYSTEM,
            tools=[buscar_en_documentacion, extraer_datos_factura],
        ) as agent,
    ):
        try:  
            preguntas = [
            ("Para que sirven los posting groups?", None),
            ("Extrae los datos de la factura en data/sample-invoice.pdf", Factura),
            ("Hola, gracias por la ayuda!", None),
            ]
            for p, formato in preguntas:
                print(f"\nPREGUNTA: {p}")
                if formato:
                    respuesta = await agent.run(p, options={"response_format": formato})
                    factura = respuesta.value
                    print(factura.model_dump_json(indent=2))
                    suma = sum(l.importe or 0 for l in factura.lineas)
                    print("Cuadra con subtotal:", abs(suma - factura.subtotal) < 0.01)
                else:
                    respuesta = await agent.run(p)
                    print("RESPUESTA:", respuesta.text)
        except Exception as e:
            print("Error:", e)


asyncio.run(main())