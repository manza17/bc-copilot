"""
BC Copilot — Document Intelligence (Fase 2, extraccion real de facturas).
Usa el modelo prebuilt-invoice: OCR + layout + campos tipados con confianza.
Reemplaza la extraccion por LLM sobre texto pegado.
"""
import os

from dotenv import load_dotenv
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

load_dotenv()

ENDPOINT = os.environ["AZURE_DOCINTEL_ENDPOINT"]


def _credential():
    key = os.environ.get("AZURE_DOCINTEL_KEY")
    if key:
        from azure.core.credentials import AzureKeyCredential
        return AzureKeyCredential(key)
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential()


client = DocumentIntelligenceClient(endpoint=ENDPOINT, credential=_credential())


def extraer_factura(file_path):
    """Analiza una factura (PDF/imagen) y devuelve sus campos con score de confianza."""
    with open(file_path, "rb") as f:
        data = f.read()

    # Operacion de larga duracion: arrancamos el analisis y esperamos el resultado.
    poller = client.begin_analyze_document(
        "prebuilt-invoice",
        AnalyzeDocumentRequest(bytes_source=data),
    )
    result = poller.result()

    datos = {}
    for doc in result.documents or []:          # normalmente 1 factura por archivo
        for nombre, campo in (doc.fields or {}).items():
            datos[nombre] = {
                "valor": campo.get("content"),
                "confianza": campo.get("confidence"),
            }
    return datos


if __name__ == "__main__":
    import json

    ruta = os.path.join(os.path.dirname(__file__), "..", "data", "sample-invoice.pdf")
    print(f"Analizando {ruta} ...")
    datos = extraer_factura(ruta)
    print(json.dumps(datos, indent=2, ensure_ascii=False))