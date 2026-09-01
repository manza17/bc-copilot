import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

PROVIDER = os.environ.get("PROVIDER", "ollama")


def get_client():
    if PROVIDER == "azure":
        # Keyless: pedimos un token de Entra ID usando tu sesion de `az login`.
        from azure.identity import DefaultAzureCredential

        token = DefaultAzureCredential().get_token("https://ai.azure.com/.default").token
        # El token dura ~1 h; alcanza de sobra para correr el script.
        return OpenAI(
            base_url=os.environ["AZURE_OPENAI_ENDPOINT"],  # termina en /openai/v1/
            api_key=token,
        )

    # ollama / gemini / cualquier endpoint compatible con OpenAI
    return OpenAI(
        base_url=os.environ["OPENAI_BASE_URL"],
        api_key=os.environ["OPENAI_API_KEY"],
    )


CHAT_MODEL = os.environ.get("MODEL", "llama3.1")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")