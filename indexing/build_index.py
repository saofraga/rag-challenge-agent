# Gera o índice vetorial dos documentos da BimBam Buy a partir dos PDFs em
# docs/fontes/bimbam-buy/. Rodar com: python -m indexing.build_index
# (dentro do ambiente virtual, com GEMINI_API_KEY configurada em .env).
# Reexecutar este script a qualquer momento regenera o índice do zero —
# inclusive após atualizar algum PDF-fonte.

import json
from pathlib import Path

import faiss
import numpy as np
from dotenv import load_dotenv

load_dotenv()

from rag.chunking import chunk_text  # noqa: E402
from rag.embeddings import embed_batch  # noqa: E402
from rag.pdf_text import extract_text  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "docs" / "fontes" / "bimbam-buy"
INDEX_DIR = REPO_ROOT / "index"
INDEX_PATH = INDEX_DIR / "bimbam_buy.faiss"
CHUNKS_PATH = INDEX_DIR / "bimbam_buy_chunks.json"


def build_index() -> None:
    pdf_paths = sorted(SOURCE_DIR.glob("*.pdf"))
    if not pdf_paths:
        raise SystemExit(f"Nenhum PDF encontrado em {SOURCE_DIR}")

    chunks = []
    for pdf_path in pdf_paths:
        title = pdf_path.stem.replace("-", " ")
        text = extract_text(pdf_path)
        doc_chunks = chunk_text(text)
        if not doc_chunks:
            raise SystemExit(
                f"Nenhum texto extraído de {pdf_path.name} — verifique se o PDF "
                "não é uma imagem escaneada sem camada de texto."
            )
        for chunk_index, chunk in enumerate(doc_chunks):
            chunks.append({
                "source": pdf_path.name,
                "chunk_index": chunk_index,
                "text": f"{title}. {chunk}",
            })
        print(f"{pdf_path.name}: {len(doc_chunks)} trechos")

    print(f"Total de trechos: {len(chunks)}")
    print("Gerando embeddings via Gemini...")
    vectors = np.array(embed_batch([c["text"] for c in chunks]), dtype="float32")
    faiss.normalize_L2(vectors)

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))
    CHUNKS_PATH.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Índice salvo em {INDEX_PATH}")
    print(f"Metadados salvos em {CHUNKS_PATH}")


if __name__ == "__main__":
    build_index()
