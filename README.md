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
- [ ] Fase 3 — IA responsable + demo desplegada
- [ ] Fase 4 — Empaquetado (arquitectura, vídeo, evaluación)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # completá PROVIDER y las variables del proveedor que elijas
```

`data/` no se versiona (está en `.gitignore`): agregá ahí tus propios `.md`/`.txt` con
documentación de BC antes de indexar.

Los scripts se corren desde `src/` (usan imports directos entre sí, sin paquete instalable), por
ejemplo `cd src && python chat.py`.

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

## Arquitectura

_(Diagrama a agregar en la Fase 4.)_

## Stack

Python · Azure AI Foundry · Azure AI Search · Azure AI Document Intelligence ·
Streamlit (Fase 3, pendiente) · GitHub
