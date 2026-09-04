"""
Crea el indice vectorial en Azure AI Search (se corre una sola vez).
Define el esquema: campos + configuracion de busqueda vectorial (HNSW).
"""
import os

from dotenv import load_dotenv
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    HnswParameters,
    VectorSearchProfile,
)

load_dotenv()


def _search_credential():
    """Usa la API key si esta en el .env; si no, cae en keyless (DefaultAzureCredential)."""
    key = os.environ.get("AZURE_SEARCH_KEY")
    if key:
        from azure.core.credentials import AzureKeyCredential
        return AzureKeyCredential(key)
    from azure.identity import DefaultAzureCredential
    return DefaultAzureCredential()

ENDPOINT = os.environ["AZURE_SEARCH_ENDPOINT"]
INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX", "bc-docs")

# --- 1. Los campos (las "columnas" del indice) ---
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
    # content: buscable por palabra clave Y retrievable (vuelve para citarlo)
    SearchableField(name="content", type=SearchFieldDataType.String),
    # source: filtrable y retrievable (para citar y filtrar por archivo)
    SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
    # contentVector: el embedding. Buscable como vector, pero NO retrievable
    # (no queremos que 1536 numeros vuelvan en cada respuesta).
    SearchField(
        name="contentVector",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=True,
        hidden=True,  # hidden=True  ->  no retrievable
        vector_search_dimensions=1536,  # <- debe coincidir con text-embedding-3-small
        vector_search_profile_name="vector-profile",
    ),
]

# --- 2. La configuracion de busqueda vectorial (HNSW) ---
vector_search = VectorSearch(
    algorithms=[
        HnswAlgorithmConfiguration(
            name="hnsw-config",
            parameters=HnswParameters(
                m=4,                 # conexiones por nodo en el grafo
                ef_construction=400, # candidatos al construir el grafo
                ef_search=500,       # candidatos al buscar
                metric="cosine",     # misma distancia que ya usabas
            ),
        )
    ],
    profiles=[
        VectorSearchProfile(
            name="vector-profile",
            algorithm_configuration_name="hnsw-config",
        )
    ],
)

# --- 3. Crear el indice ---
index = SearchIndex(name=INDEX_NAME, fields=fields, vector_search=vector_search)

client = SearchIndexClient(endpoint=ENDPOINT, credential=_search_credential())
result = client.create_or_update_index(index)
print(f"Indice '{result.name}' creado/actualizado correctamente.")