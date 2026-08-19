# rag-challenge-agent

Agente conversacional que responde perguntas sobre os documentos internos da BimBam Buy (pagamento, reembolso e devoluções, envios, afiliados e garantia).

**Aplicação publicada:** https://rag-challenge-agent.vercel.app

## Indexação dos documentos

Os PDFs-fonte ficam em `docs/fontes/bimbam-buy/`. O índice vetorial usado nas buscas é gerado por um processo offline separado da aplicação e versionado em `index/`.

Para gerar (ou regenerar, após atualizar algum PDF) o índice do zero:

```bash
source .venv/bin/activate
python -m indexing.build_index
```

O processo lê cada PDF, divide o texto em trechos, gera o embedding de cada trecho via API do Gemini, e salva o índice FAISS resultante (`index/bimbam_buy.faiss`) junto com os metadados de cada trecho (`index/bimbam_buy_chunks.json`).

## Rodando a API localmente

A aplicação expõe uma única rota, `POST /perguntar`, que recebe uma pergunta em texto e devolve uma resposta fundamentada nos documentos indexados. A busca (embeddings) usa a API do Gemini e a geração da resposta usa a Ollama Cloud — ambas chamadas por HTTPS direto, sem depender de nenhum processo rodando localmente.

1. Configure num arquivo `.env` na raiz do projeto (veja `.env.example`):
   ```
   OLLAMA_API_KEY=sua_chave_aqui
   GEMINI_API_KEY=sua_chave_aqui
   ```
   - Chave da Ollama Cloud: [ollama.com/settings/keys](https://ollama.com/settings/keys)
   - Chave do Gemini: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Suba a API:
   ```bash
   source .venv/bin/activate
   uvicorn app:app --reload
   ```
3. Faça uma pergunta:
   ```bash
   curl -X POST http://localhost:8000/perguntar \
     -H "Content-Type: application/json" \
     -d '{"pergunta": "Quantos dias tenho para devolver um produto?"}'
   ```

A busca combina similaridade por embedding com sobreposição de palavras-chave, e o texto de todos os trechos recuperados é avaliado pelo modelo de geração antes de compor a resposta — perguntas sem informação suficiente nos documentos recebem uma mensagem informando isso, em vez de uma resposta inventada.

## Testes

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

Os testes chamam a rota real (`POST /perguntar`), cobrindo uma pergunta por documento-fonte e uma pergunta fora de escopo. Requerem `OLLAMA_API_KEY` e `GEMINI_API_KEY` configuradas e o índice já gerado.
