# Spec: Agente RAG — BimBam Buy Assistant

## Problem Statement

Uma equipe de suporte de e-commerce (cenário fictício: BimBam Buy) recebe repetidamente as mesmas perguntas sobre políticas de reembolso, envio, garantia e programa de afiliados. As pessoas responsáveis por atender precisam abrir e reler manualmente vários documentos internos (PDFs de FAQ, políticas e guias) toda vez que alguém pergunta algo, o que consome tempo e gera respostas inconsistentes entre atendentes.

## Solution

Um agente conversacional que responde perguntas em linguagem natural sobre os documentos internos da BimBam Buy (FAQ de pagamento, política de reembolso e devoluções, guia de envios, programa de afiliados, manual de garantia). O agente recupera os trechos relevantes desses documentos e gera uma resposta direta, em vez de a pessoa precisar abrir e ler o PDF inteiro. A aplicação é acessível publicamente por meio de uma URL, com uma interface de chat simples.

## User Stories

1. Como pessoa usuária, quero digitar uma pergunta em português sobre políticas da BimBam Buy, para que eu receba uma resposta direta sem precisar abrir nenhum PDF.
2. Como pessoa usuária, quero perguntar sobre a política de reembolso e devoluções, para saber prazos e condições sem procurar no documento.
3. Como pessoa usuária, quero perguntar sobre métodos de pagamento aceitos, para confirmar rapidamente uma dúvida de compra.
4. Como pessoa usuária, quero perguntar sobre prazos e condições de envio, para saber quando esperar um pedido.
5. Como pessoa usuária, quero perguntar sobre o programa de afiliados, para entender como participar e quais são as regras.
6. Como pessoa usuária, quero perguntar sobre a política de garantia, para saber o que fazer com um produto com defeito.
7. Como pessoa usuária, quero que o agente responda apenas com base no conteúdo real dos documentos, para não receber informação inventada.
8. Como pessoa usuária, quero receber uma mensagem clara quando a pergunta não puder ser respondida com base nos documentos disponíveis, em vez de uma resposta genérica ou inventada.
9. Como pessoa usuária, quero uma interface de chat simples, para conseguir conversar com o agente sem fricção.
10. Como pessoa avaliando o projeto, quero acessar a aplicação publicamente por uma URL, para confirmar que o deploy funciona de fato.
11. Como pessoa avaliando o projeto, quero ver no repositório uma documentação clara da arquitetura, tecnologias e instruções de execução, para entender e reproduzir a solução.
12. Como pessoa avaliando o projeto, quero ver exemplos reais de perguntas e respostas do agente, para validar que ele funciona como descrito.
13. Como pessoa desenvolvedora dando manutenção no projeto, quero que o índice de busca dos documentos seja gerado por um processo separado e reprodutível, para poder atualizar os documentos-fonte sem reescrever o agente.
14. Como pessoa desenvolvedora, quero que a etapa de geração de resposta seja isolada da etapa de busca, para poder trocar o modelo de linguagem usado sem afetar a lógica de recuperação de contexto.
15. Como pessoa desenvolvedora, quero que a aplicação funcione localmente antes de qualquer deploy, para validar o comportamento sem depender da infraestrutura de nuvem.

## Implementation Decisions

- **Fonte de dados:** conjunto de documentos PDF da BimBam Buy (FAQ de métodos de pagamento, política de reembolso e devoluções, guia de envios, programa de afiliados, manual de garantia). Estático — não há upload de novos documentos pela interface nesta versão.
- **Indexação (processo offline, separado da aplicação em produção):** os documentos são convertidos em texto, divididos em trechos (chunking), e cada trecho é transformado em um vetor de embedding. O índice vetorial resultante é salvo em disco e versionado junto com o restante do código — não é gerado em tempo de execução na produção.
- **Busca (retrieval):** dada uma pergunta, o sistema gera seu embedding e busca no índice vetorial os trechos mais relevantes dos documentos.
- **Geração de resposta:** os trechos recuperados são combinados com a pergunta original num prompt, que é enviado a um modelo de linguagem hospedado externamente. A chamada a esse serviço é feita via requisição HTTP direta (sem depender de uma biblioteca de orquestração de terceiros), o que mantém o comportamento mais previsível e fácil de depurar.
- **Camada de API:** uma única rota HTTP que recebe a pergunta em texto e devolve a resposta gerada. Essa rota orquestra busca + geração internamente; retrieval e geração não são expostos como endpoints separados.
- **Interface:** uma página web mínima com um campo de entrada de texto e um histórico de mensagens da conversa — sem framework de front-end pesado.
- **Hospedagem:** a aplicação é publicada numa plataforma de hospedagem serverless, acessível por URL pública.
- **Tratamento de perguntas fora de escopo:** se a busca não encontrar trechos suficientemente relevantes, o agente deve responder informando que não encontrou a informação nos documentos disponíveis, em vez de gerar uma resposta sem base documental.

## Testing Decisions

- Um bom teste aqui valida o comportamento observável — "esta pergunta produz uma resposta que contém a informação correta" — e não a implementação interna (não valida quais trechos exatos foram recuperados, nem detalhes do formato do prompt enviado ao modelo de linguagem).
- **Seam único:** a rota da API (pergunta → resposta) é o ponto de teste. Retrieval e geração são tratados como caixa-preta por trás dela.
- Casos de teste mínimos por história de usuário: uma pergunta por documento-fonte (reembolso, pagamento, envio, afiliados, garantia) verificando que a resposta contém a informação esperada; um caso de pergunta claramente fora de escopo (não coberta por nenhum documento), verificando que o agente não inventa uma resposta.
- Não há testes automatizados anteriores neste projeto para servir de referência — este é o primeiro conjunto de testes do projeto.

## Out of Scope

- Upload de novos documentos pela interface (documentos são fixos, definidos no processo de indexação).
- Autenticação de usuários ou controle de acesso.
- Suporte a múltiplos idiomas além do português.
- Histórico de conversas persistente entre sessões (o histórico existe apenas durante a sessão ativa no navegador).
- Orquestração multi-agente ou uso de frameworks de agentes mais sofisticados — fica como possível evolução futura, não faz parte do escopo mínimo.
- Interface visual elaborada — o foco é o funcionamento do agente, não a estética da interface.

## Further Notes

- A geração do índice vetorial (chunking + embeddings) é tratada como uma etapa offline, separada e reprodutível — os documentos-fonte de entrada e o índice resultante devem poder ser regenerados a partir de um único processo, sem depender de estado manual.
- A validação de que a aplicação está de fato acessível publicamente (URL funcionando) é parte dos critérios de aceite deste projeto, junto com a qualidade das respostas geradas.
