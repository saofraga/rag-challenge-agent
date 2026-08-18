# rag-challenge-agent

Agente conversacional que responde perguntas sobre os documentos internos da BimBam Buy (pagamento, reembolso e devoluções, envios, afiliados e garantia).

## Indexação dos documentos

Os PDFs-fonte ficam em `docs/fontes/bimbam-buy/`. O índice vetorial usado nas buscas é gerado por um processo offline separado da aplicação e versionado em `index/`.

Para gerar (ou regenerar, após atualizar algum PDF) o índice do zero:

```bash
source .venv/bin/activate
python -m indexing.build_index
```

O processo lê cada PDF, divide o texto em trechos, gera o embedding de cada trecho localmente via Ollama (modelo `nomic-embed-text`) e salva o índice FAISS resultante (`index/bimbam_buy.faiss`) junto com os metadados de cada trecho (`index/bimbam_buy_chunks.json`).
