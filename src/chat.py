"""
BC Copilot — primer script (Fase 0)
Llama a un modelo a través de cualquier endpoint compatible con OpenAI.
El proveedor se elige en el .env, no en el código.
"""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ["OPENAI_BASE_URL"],
    api_key=os.environ["OPENAI_API_KEY"],
)
MODEL = os.environ.get("MODEL", "llama3.1")

SYSTEM_PROMPT = (
    "Sos un asistente para consultores de Microsoft Dynamics 365 Business Central. "
    "Respondé de forma clara y concisa. Si no estás seguro, decilo."
)


def ask(question: str) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    pregunta = "¿Qué es un Posting Group en Business Central y para qué se usa?"
    print(f"Modelo: {MODEL}\n")
    print(f"Pregunta: {pregunta}\n")
    print("Respuesta:")
    print(ask(pregunta))
