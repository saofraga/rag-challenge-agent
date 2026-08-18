import os

import numpy as np
import requests

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")

BATCH_SIZE = 16


def embed_batch(texts: list[str]) -> list[list[float]]:
    embeddings: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        try:
            response = requests.post(
                f"{OLLAMA_HOST}/api/embed",
                json={"model": EMBED_MODEL, "input": batch},
                timeout=120,
            )
            response.raise_for_status()
        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(
                f"Não foi possível conectar ao Ollama em {OLLAMA_HOST}. "
                "Confirme que o Ollama está rodando localmente."
            ) from exc
        except requests.exceptions.HTTPError as exc:
            raise RuntimeError(
                f"Ollama recusou o pedido de embedding (modelo '{EMBED_MODEL}'). "
                f"Confirme que o modelo foi baixado com: ollama pull {EMBED_MODEL}"
            ) from exc

        batch_embeddings = response.json()["embeddings"]
        if len(batch_embeddings) != len(batch):
            raise RuntimeError(
                f"Ollama retornou {len(batch_embeddings)} embeddings para "
                f"{len(batch)} textos enviados — resposta inconsistente."
            )
        embeddings.extend(batch_embeddings)
    return embeddings


def embed_query(text: str) -> list[float]:
    vector = np.array(embed_batch([text])[0], dtype="float32")
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector.tolist()
