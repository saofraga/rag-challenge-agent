def chunk_text(text: str, chunk_size: int = 150, overlap: int = 30) -> list[str]:
    if overlap >= chunk_size:
        raise ValueError("overlap deve ser menor que chunk_size")

    words = text.split()
    if not words:
        return []

    step = chunk_size - overlap
    chunks = []
    start = 0
    while start < len(words):
        chunks.append(" ".join(words[start:start + chunk_size]))
        if start + chunk_size >= len(words):
            break
        start += step
    return chunks
