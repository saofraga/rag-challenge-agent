import os
import time

import numpy as np
import requests

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models"
EMBED_MODEL = os.environ.get("GEMINI_EMBED_MODEL", "gemini-embedding-001")
EMBED_DIMENSION = 768

BATCH_SIZE = 16
MAX_RETRIES = 3


def _api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY não configurada. Crie uma chave em "
            "https://aistudio.google.com/apikey e defina a variável de ambiente."
        )
    return key


def embed_batch(texts: list[str]) -> list[list[float]]:
    api_key = _api_key()
    embeddings: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        response = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = requests.post(
                    f"{GEMINI_URL}/{EMBED_MODEL}:batchEmbedContents",
                    headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                    json={
                        "requests": [
                            {
                                "model": f"models/{EMBED_MODEL}",
                                "content": {"parts": [{"text": text}]},
                                "output_dimensionality": EMBED_DIMENSION,
                            }
                            for text in batch
                        ]
                    },
                    timeout=60,
                )
                if response.status_code == 429 and attempt < MAX_RETRIES:
                    time.sleep(2 ** attempt)
                    continue
                response.raise_for_status()
                break
            except requests.exceptions.ConnectionError as exc:
                raise RuntimeError("Não foi possível conectar à API de embeddings do Gemini.") from exc
            except requests.exceptions.HTTPError as exc:
                raise RuntimeError(
                    f"A API de embeddings do Gemini recusou o pedido (modelo '{EMBED_MODEL}'). "
                    "Confirme que GEMINI_API_KEY é válida."
                ) from exc

        batch_embeddings = response.json()["embeddings"]
        if len(batch_embeddings) != len(batch):
            raise RuntimeError(
                f"A API retornou {len(batch_embeddings)} embeddings para "
                f"{len(batch)} textos enviados — resposta inconsistente."
            )
        embeddings.extend(item["values"] for item in batch_embeddings)
    return embeddings


def embed_query(text: str) -> list[float]:
    vector = np.array(embed_batch([text])[0], dtype="float32")
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector.tolist()
