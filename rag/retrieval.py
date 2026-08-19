import json
import re
from pathlib import Path

import faiss
import numpy as np

from rag.embeddings import embed_query

REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = REPO_ROOT / "index" / "bimbam_buy.faiss"
CHUNKS_PATH = REPO_ROOT / "index" / "bimbam_buy_chunks.json"

# Peso do sinal léxico (sobreposição de palavras) somado ao score de
# similaridade por embedding. Complementa a busca semântica para perguntas
# onde o embedding sozinho não discrimina bem entre documentos parecidos.
LEXICAL_WEIGHT = 0.3

STOPWORDS = {
    "a", "o", "as", "os", "de", "da", "do", "das", "dos", "um", "uma", "uns",
    "umas", "e", "ou", "que", "com", "para", "por", "em", "no", "na", "nos",
    "nas", "se", "é", "são", "meu", "minha", "seu", "sua", "como", "quando",
    "onde", "qual", "quais", "isso", "este", "esta", "isto", "ao", "aos", "à",
    "às", "tem", "ter", "ser", "estar", "há",
}

_index = None
_chunks = None
_chunk_tokens = None


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"\w+", text.lower())
    return {t for t in tokens if t not in STOPWORDS and len(t) > 2}


def _lexical_score(query_tokens: set[str], chunk_tokens: set[str]) -> float:
    if not query_tokens:
        return 0.0
    return len(query_tokens & chunk_tokens) / len(query_tokens)


def _load():
    global _index, _chunks, _chunk_tokens
    if _index is None:
        if not INDEX_PATH.exists() or not CHUNKS_PATH.exists():
            raise RuntimeError(
                f"Índice não encontrado em {INDEX_PATH}. "
                "Rode primeiro: python -m indexing.build_index"
            )
        _index = faiss.read_index(str(INDEX_PATH))
        _chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
        _chunk_tokens = [_tokenize(chunk["text"]) for chunk in _chunks]
    return _index, _chunks, _chunk_tokens


def search(question: str, k: int = 8) -> list[dict]:
    index, chunks, chunk_tokens = _load()
    vector = np.array([embed_query(question)], dtype="float32")
    scores, positions = index.search(vector, index.ntotal)

    query_tokens = _tokenize(question)
    candidates = []
    for score, position in zip(scores[0], positions[0]):
        if position < 0:
            continue
        lexical = _lexical_score(query_tokens, chunk_tokens[position])
        combined_score = float(score) + LEXICAL_WEIGHT * lexical
        candidates.append((combined_score, position))

    candidates.sort(key=lambda item: item[0], reverse=True)

    results = []
    for combined_score, position in candidates[:k]:
        chunk = chunks[position]
        results.append({
            "source": chunk["source"],
            "text": chunk["text"],
            "score": combined_score,
        })
    return results
