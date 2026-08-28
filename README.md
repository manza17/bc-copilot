# BC Copilot

Asistente para consultores de **Microsoft Dynamics 365 Business Central**: un agente con RAG
sobre la documentación oficial que responde consultas funcionales y técnicas **con citas a la
fuente**, y extrae datos de documentos (facturas, reportes).

> Proyecto de portafolio en construcción. Objetivo: certificación AI-103 (Azure AI Apps &
> Agents Developer) + demostración de skills en RAG, agentes y Azure AI Foundry.

## Estado

- [x] Fase 0 — Prototipo local (llamada a un modelo, agnóstico del proveedor)
- [ ] Fase 1 — RAG sobre docs de BC en Azure AI Foundry + AI Search
- [ ] Fase 2 — Agente con tool-calling + extracción de documentos
- [ ] Fase 3 — IA responsable + demo desplegada
- [ ] Fase 4 — Empaquetado (arquitectura, vídeo, evaluación)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # y elegí un proveedor dentro del .env
python src/chat.py
```

## Arquitectura

_(Diagrama a agregar en la Fase 4.)_

## Stack

Python · Azure AI Foundry · Azure AI Search · Streamlit · GitHub
