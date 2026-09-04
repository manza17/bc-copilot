"""
Ingesta (se corre una sola vez, o cada vez que cambian los documentos):
carga los .md de data/, los trocea, los embebe y los sube al indice de AI Search.
Reusa load_documents / chunk_document / embed de rag.py.
"""
import os

from dotenv import load_dotenv
from azure.search.documents import SearchClient

from rag import load_documents, chunk_document, embed, DATA_DIR

load_dotenv()

ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"]
INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX", "bc-docs")


def _search_credential():
    key = os.environ.get("AZURE_SEARCH_KEY")
    if key:
        from azure.core.credentials import AzureKeyCredential
        return AzureKeyCredential(key)
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential()


def build_search_documents():
    """Convierte cada chunk en un documento con los campos del indice."""
    docs = load_documents(DATA_DIR)
    search_docs = []
    for doc in docs:
        chunks = chunk_document(doc)
        vectors = embed([c["text"] for c in chunks])  # embebemos todos los chunks del doc
        safe_source = doc["source"].replace(".", "_")
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            search_docs.append({
                "id": f"{safe_source}-{i}",            # clave unica por chunk
                "content": chunk["text"],
                "source": chunk["source"],
                "contentVector": vector.tolist(),      # numpy array -> lista de floats
            })
    return search_docs


if __name__ == "__main__":
    print("Cargando y embebiendo documentos...")
    search_docs = build_search_documents()

    client = SearchClient(ENDPOINT, INDEX_NAME, credential=_search_credential())
    result = client.upload_documents(documents=search_docs)

    exitosos = sum(1 for r in result if r.succeeded)
    print(f"Subidos {exitosos}/{len(search_docs)} chunks al indice '{INDEX_NAME}'.")