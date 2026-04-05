import requests
import json

OLLAMA_BASE_URL = "http://localhost:11434"
MODEL = "llama3.1:8b"

def ask_llm(messages: list) -> str:
    # System ve user mesajlarını birleştir
    system = ""
    user = ""
    for m in messages:
        if m["role"] == "system":
            system = m["content"]
        elif m["role"] == "user":
            user = m["content"]

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/chat",
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "stream": False
        },
        timeout=120
    )
    response.raise_for_status()
    return response.json()["message"]["content"]