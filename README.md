# BimBam Buy — Atendimento

Agente conversacional que responde, em português, perguntas sobre os documentos internos da BimBam Buy (loja online fictícia): métodos de pagamento, política de reembolso e devoluções, prazos e custos de envio, garantia de produtos e o programa de afiliados.

Em vez de uma pessoa precisar abrir e ler um PDF inteiro para achar uma informação pontual, ela conversa com o agente e recebe uma resposta direta, fundamentada no conteúdo real dos documentos — e uma mensagem clara quando a pergunta está fora do que os documentos cobrem, em vez de uma resposta inventada.

**Aplicação publicada:** https://rag-challenge-agent.vercel.app

## Arquitetura

A solução tem duas etapas bem separadas:

**1. Indexação dos documentos (offline, executada uma vez e sempre que um PDF muda)**

```
PDFs (docs/fontes/bimbam-buy/) → extração de texto → divisão em trechos
  → embedding de cada trecho (API do Gemini) → índice vetorial FAISS
```

O índice resultante (`index/bimbam_buy.faiss` + `index/bimbam_buy_chunks.json`) é versionado no repositório, para que a aplicação nunca precise gerar embeddings em tempo de execução — só consultar um índice já pronto.

**2. Resposta a perguntas (rota única da API, em tempo real)**

```
pergunta → embedding da pergunta (Gemini) → busca híbrida no índice FAISS
  (similaridade por embedding + sobreposição de palavras-chave)
  → trechos mais relevantes → prompt de geração → resposta (Ollama Cloud)
```

A busca combina dois sinais — similaridade semântica por embedding e sobreposição literal de palavras — porque perguntas parecidas em vocabulário mas sobre assuntos diferentes (ex: prazos de pagamento vs. prazos de envio) podem confundir um único sinal isolado. Os trechos recuperados são passados ao modelo de geração com a instrução explícita de avaliar todos e responder apenas com base no que de fato trata do assunto perguntado — e de dizer claramente quando nenhum trecho contém a resposta.

A interface de chat é uma página estática (HTML/CSS/JavaScript, sem framework), servida pela própria API na mesma origem da rota de perguntas.

## Tecnologias

- **Python 3 / FastAPI** — backend e rota única (`POST /perguntar`)
- **FAISS** — índice vetorial local, embutido no processo
- **API do Gemini** — geração dos embeddings (indexação e busca)
- **Ollama Cloud** — geração da resposta final, via chamada HTTPS direta
- **HTML/CSS/JavaScript puro** — interface de chat
- **Vercel** — hospedagem, com deploy automático a partir do repositório

## Estrutura do repositório

```
docs/fontes/bimbam-buy/   PDFs-fonte (documentos internos da BimBam Buy)
indexing/build_index.py  Script de indexação (offline, reprodutível)
rag/                      Extração de texto, chunking, embeddings, busca e geração
index/                    Índice vetorial FAISS e metadados dos trechos (versionados)
static/index.html         Interface de chat
app.py                    Aplicação FastAPI (rota única + interface estática)
tests/test_api.py         Testes automatizados da rota de perguntas
```

## Executando localmente

**Pré-requisitos:** Python 3.11+, uma chave da Ollama Cloud e uma chave do Gemini (ambas gratuitas).

1. Rode o script de setup, que cria o ambiente virtual e instala as dependências:
   ```bash
   ./setup.sh
   ```
2. Crie um arquivo `.env` na raiz do projeto (veja `.env.example`) com:
   ```
   OLLAMA_API_KEY=sua_chave_aqui
   GEMINI_API_KEY=sua_chave_aqui
   ```
   - Chave da Ollama Cloud: [ollama.com/settings/keys](https://ollama.com/settings/keys)
   - Chave do Gemini: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
3. Gere o índice vetorial a partir dos PDFs-fonte:
   ```bash
   source .venv/bin/activate
   python -m indexing.build_index
   ```
4. Suba a aplicação:
   ```bash
   uvicorn app:app --reload
   ```
5. Abra `http://localhost:8000` no navegador para usar a interface de chat, ou chame a API diretamente:
   ```bash
   curl -X POST http://localhost:8000/perguntar \
     -H "Content-Type: application/json" \
     -d '{"pergunta": "Quantos dias tenho para devolver um produto?"}'
   ```

### Testes

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

Os testes chamam a rota real (`POST /perguntar`) — não simulam a busca ou a geração — cobrindo uma pergunta por documento-fonte e uma pergunta fora de escopo. Requerem as duas chaves de API configuradas e o índice já gerado.

## Exemplos reais de uso

Capturados na aplicação publicada em produção:

> **Pergunta:** Quantos dias tenho para devolver um produto?
>
> **Resposta:** Você tem duas regras de prazo, dependendo do motivo da devolução: Para arrependimento (quando decide que não quer mais o produto), a solicitação deve ser feita dentro de 10 dias corridos a partir do recebimento do pedido. Se o produto chegou errado, com falta ou com dano visível, a solicitação deve ser feita em até 48 horas após a entrega.

> **Pergunta:** Quais formas de pagamento a BimBam Buy aceita?
>
> **Resposta:** A BimBam Buy aceita as seguintes formas de pagamento: Cartão de crédito, Cartão de débito, Transferência bancária ou PIX, pagamento em dinheiro em pontos habilitados e carteiras digitais.

> **Pergunta:** Quanto tempo demora para meu pedido chegar?
>
> **Resposta:** O tempo estimado de entrega depende da sua localização: em áreas urbanas principais o pedido costuma chegar em 2 a 5 dias úteis, em áreas secundárias de 4 a 8 dias úteis, e em áreas de cobertura estendida de 6 a 12 dias úteis.

> **Pergunta:** Como funciona o programa de afiliados da BimBam Buy?
>
> **Resposta:** O Programa de Afiliados da BimBam Buy permite que criadores de conteúdo, sites de cupons, mídias digitais, comunidades de compras, educadores ou outros parceiros promovam produtos da marca e recebam uma comissão por vendas validamente atribuídas.

> **Pergunta:** Qual é a capital da Mongólia?
>
> **Resposta:** Não encontrei essa informação nos documentos disponíveis da BimBam Buy.

## Deploy

A aplicação está publicada na Vercel (https://rag-challenge-agent.vercel.app), com deploy automático a cada atualização do repositório. Não há etapa de build separada: o índice vetorial já vem pronto e versionado, e a aplicação chama a API de embeddings e a Ollama Cloud diretamente por HTTPS — sem nenhuma dependência de processo local.

## Fora de escopo

- Upload de novos documentos pela interface (os documentos-fonte são fixos).
- Autenticação de usuários.
- Suporte a idiomas além do português.
- Histórico de conversas persistente entre sessões (o histórico existe apenas durante a sessão ativa no navegador).
