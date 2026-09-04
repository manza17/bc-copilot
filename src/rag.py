"""
BC Copilot — RAG sobre Azure AI Search (Fase 1B)
load_documents / chunk_document / embed se mantienen (los usa ingest.py).
retrieve ahora consulta el indice de AI Search (busqueda hibrida) en vez de numpy.
"""
import glob
import os

import numpy as np
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from provider import get_client, CHAT_MODEL, EMBED_MODEL

load_dotenv()

client = get_client()
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def _search_credential():
    key = os.environ.get("AZURE_SEARCH_KEY")
    if key:
        from azure.core.credentials import AzureKeyCredential
        return AzureKeyCredential(key)
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential()


search_client = SearchClient(
    os.environ["AZURE_SEARCH_ENDPOINT"],
    os.environ.get("AZURE_SEARCH_INDEX", "bc-docs"),
    credential=_search_credential(),
)


# --- Estas tres funciones NO cambian: las reusa ingest.py ---
def load_documents(data_dir):
    docs = []
    paths = glob.glob(os.path.join(data_dir, "*.md")) + glob.glob(os.path.join(data_dir, "*.txt"))
    for path in paths:
        with open(path, encoding="utf-8") as f:
            docs.append({"source": os.path.basename(path), "text": f.read()})
    return docs


def chunk_document(doc, size=500, overlap=100):
    text = doc["text"]
    chunks, start = [], 0
    while start < len(text):
        piece = text[start:start + size].strip()
        if piece:
            chunks.append({"source": doc["source"], "text": piece})
        start += size - overlap
    return chunks


def embed(texts):
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return np.array([d.embedding for d in resp.data])


# --- retrieve: ahora consulta AI Search en vez de calcular sobre numpy ---
def retrieve(question, k=3):
    q_vector = embed([question])[0].tolist()
    vector_query = VectorizedQuery(
        vector=q_vector, k_nearest_neighbors=k, fields="contentVector"
    )
    results = search_client.search(
        search_text=question,            # BM25 (palabra clave)
        vector_queries=[vector_query],   # HNSW (vectorial)  -> juntas = hibrida
        select=["content", "source"],    # contentVector no vuelve (es hidden)
        top=k,
    )
    return [{"text": r["content"], "source": r["source"]} for r in results]


def answer(question, k=3):
    hits = retrieve(question, k)
    context = "\n\n".join(
        f"[{i + 1}] (fuente: {h['source']})\n{h['text']}" for i, h in enumerate(hits)
    )
    prompt = (
        "Responde la pregunta usando SOLO el contexto de abajo. "
        "Cita la fuente con su numero entre corchetes, por ejemplo [1]. "
        "Si el contexto no alcanza, deci que no figura en la documentacion.\n\n"
        f"CONTEXTO:\n{context}\n\nPREGUNTA: {question}"
    )
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "Sos un asistente para consultores de Business "
             "Central. Respondes con precision y siempre citas las fuentes."},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content, hits


if __name__ == "__main__":
    pregunta = "Para que sirven los posting groups y que tipos hay?"
    respuesta, fuentes = answer(pregunta)
    print(f"Pregunta: {pregunta}\n")
    print("Respuesta:")
    print(respuesta)
    print("\nFuentes recuperadas:")
    for i, h in enumerate(fuentes):
        print(f"  [{i + 1}] {h['source']}")