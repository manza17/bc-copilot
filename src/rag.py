import glob
import os

import numpy as np

from provider import get_client, CHAT_MODEL, EMBED_MODEL

client = get_client()
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_documents(data_dir):
    """Lee todos los .md y .txt de la carpeta data/."""
    docs = []
    paths = glob.glob(os.path.join(data_dir, "*.md")) + glob.glob(os.path.join(data_dir, "*.txt"))
    for path in paths:
        with open(path, encoding="utf-8") as f:
            docs.append({"source": os.path.basename(path), "text": f.read()})
    return docs


def chunk_document(doc, size=500, overlap=100):
    """Parte un documento en trozos con solapamiento, para no cortar ideas al medio."""
    text = doc["text"]
    chunks, start = [], 0
    while start < len(text):
        piece = text[start : start + size].strip()
        if piece:
            chunks.append({"source": doc["source"], "text": piece})
        start += size - overlap
    return chunks


def embed(texts):
    """Convierte una lista de textos en vectores usando el modelo de embeddings."""
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return np.array([d.embedding for d in resp.data])


def build_index(data_dir=DATA_DIR):
    """Carga, trocea y vectoriza todos los documentos. Devuelve chunks + matriz normalizada."""
    docs = load_documents(data_dir)
    chunks = [c for doc in docs for c in chunk_document(doc)]
    if not chunks:
        raise RuntimeError(f"No encontré documentos en {data_dir}")
    vectors = embed([c["text"] for c in chunks])
    vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)  # normalizar
    return chunks, vectors


def retrieve(question, chunks, vectors, k=3):
    """Devuelve los k trozos más parecidos a la pregunta (similitud coseno)."""
    q = embed([question])[0]
    q = q / np.linalg.norm(q)
    sims = vectors @ q
    top = np.argsort(sims)[::-1][:k]
    return [chunks[i] for i in top]


def answer(question, chunks, vectors, k=3):
    hits = retrieve(question, chunks, vectors, k)
    context = "\n\n".join(
        f"[{i + 1}] (fuente: {h['source']})\n{h['text']}" for i, h in enumerate(hits)
    )
    prompt = (
        "Respondé la pregunta usando SOLO el contexto de abajo. "
        "Citá la fuente con su número entre corchetes, por ejemplo [1]. "
        "Si el contexto no alcanza, decí que no figura en la documentación.\n\n"
        f"CONTEXTO:\n{context}\n\nPREGUNTA: {question}"
    )
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "Sos un asistente para consultores de Business Central. "
                "Respondés con precisión y siempre citás las fuentes.",
            },
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content, hits


if __name__ == "__main__":
    print("Indexando documentos...")
    chunks, vectors = build_index()
    print(f"{len(chunks)} chunks indexados.\n")

    pregunta = "¿Para qué sirven los posting groups y qué tipos hay?"
    respuesta, fuentes = answer(pregunta, chunks, vectors)

    print(f"Pregunta: {pregunta}\n")
    print("Respuesta:")
    print(respuesta)
    print("\nFuentes recuperadas:")
    for i, h in enumerate(fuentes):
        print(f"  [{i + 1}] {h['source']}")
