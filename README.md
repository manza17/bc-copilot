# BC Copilot

Asistente para consultores de **Microsoft Dynamics 365 Business Central**: un agente con RAG
sobre la documentación oficial que responde consultas funcionales y técnicas **con citas a la
fuente**, y extrae datos de facturas (PDF/imagen) vía OCR con Azure AI Document Intelligence.

> Proyecto de portafolio en construcción. Objetivo: certificación AI-103 (Azure AI Apps &
> Agents Developer) + demostración de skills en RAG, agentes y Azure AI Foundry.

## Estado

- [x] Fase 0 — Prototipo local (llamada a un modelo, agnóstico del proveedor)
- [x] Fase 1A — RAG en Azure AI Foundry (chat + embeddings, keyless)
- [x] Fase 1B — Retrieve sobre Azure AI Search (búsqueda híbrida: HNSW + BM25)
- [x] Fase 2 — Agente con tool-calling (RAG + extracción de documentos)
- [x] Fase 2b — El mismo agente con Microsoft Agent Framework + salida estructurada (Pydantic)
- [ ] Fase 3 — IA responsable + demo desplegada
- [ ] Fase 4 — Empaquetado (arquitectura, vídeo, evaluación)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # completá PROVIDER y las variables del proveedor que elijas
```

**Con Azure (Windows):** creá un proyecto de Foundry en el portal dentro de `rg-bc-copilot` y corré
`powershell -ExecutionPolicy Bypass -File scripts\setup-azure.ps1`. El script despliega `gpt-5-mini` y
`text-embedding-3-small` (Global Standard), crea AI Search (Free) y Document Intelligence (F0), y escribe el `.env`.

`data/` no se versiona (está en `.gitignore`): agregá ahí tus propios `.md`/`.txt` con
documentación de BC antes de indexar.

Corré los scripts **desde la raíz del repo** (`python src/agent.py`): las rutas como
`data/sample-invoice.pdf` son relativas a la carpeta actual. Los imports entre módulos de `src/`
funcionan igual porque Python agrega la carpeta del script al `sys.path`.

- **Fase 0 — chat simple, sin RAG** (usa siempre `OPENAI_BASE_URL`/`OPENAI_API_KEY`, no lee `PROVIDER`):
  ```bash
  python src/chat.py
  ```
- **Fase 1 — RAG con Azure AI Search** (usa `PROVIDER` para elegir Azure o un endpoint OpenAI-compatible):
  ```bash
  python src/create_index.py   # una sola vez: crea el índice
  python src/ingest.py         # una vez, y cada vez que cambien los docs de data/
  python src/rag.py            # pregunta de ejemplo con RAG + citas de fuente
  ```
- **Fase 2 — agente con tool-calling** (elige entre buscar en la documentación o extraer datos de
  una factura en PDF/imagen vía OCR con Azure AI Document Intelligence, requiere
  `AZURE_DOCINTEL_ENDPOINT`):
  ```bash
  python src/agent.py
  ```
- **Fase 2b — el mismo agente con Microsoft Agent Framework** (requiere `PROJECT_ENDPOINT` y
  `MODEL_DEPLOYMENT_NAME`, y `az login`):
  ```bash
  python src/agent_af.py
  ```
  | `agent.py` (OpenAI SDK, a mano) | `agent_af.py` (Agent Framework) |
  |---|---|
  | `TOOL_SCHEMAS`: 45 líneas de JSON schema | Se genera desde la función: nombre, `@tool(description=...)` y `Annotated[str, Field(...)]` |
  | Mapa `TOOLS` + loop `run_agent` (detecta `tool_calls`, ejecuta, devuelve el resultado con `tool_call_id`) | `await agent.run(pregunta)`: el framework hace el loop |
  | Respuesta en texto libre | La factura sale como objeto `Factura` (Pydantic) con `options={"response_format": Factura}`, y se valida en código que la suma de las líneas cuadre con el subtotal |

  `doc_intel.py` ahora también extrae las líneas (`Items`): es un campo de tipo array, así que se
  recorre con `value_array` / `value_object` en vez de `content`.

## Arquitectura

_(Diagrama a agregar en la Fase 4.)_

## Stack

Python · Azure AI Foundry · Azure AI Search · Azure AI Document Intelligence ·
Streamlit (Fase 3, pendiente) · GitHub
