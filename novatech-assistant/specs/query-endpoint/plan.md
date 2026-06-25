# Plan — Query Endpoint

> **Autor:** Tech Lead (converte `requirements.md` em abordagem técnica). **Status:** Aprovado (Gate 1 → habilita geração de tasks).
> Reproduzido a partir do plan.md simulado fornecido no enunciado do Dev 2.2.

## Approach
Azure Function HTTP trigger que:
1. Recebe pergunta do atendente via `POST /api/query`.
2. Converte pergunta em embedding via Azure OpenAI.
3. Busca top-5 chunks no Azure AI Search.
4. Monta prompt com chunks + system prompt + pergunta (respeitando context budget: ~4K system + ~8K chunks + pergunta).
5. Envia ao GPT-4o e retorna resposta com `source_document`.

## Technical Decisions
- TypeScript com Azure Functions v4.
- Zod para validação de input/output.
- Retry com exponential backoff para chamadas Azure.
- Structured logging com pino (nunca `console.log`).

## Prior Decisions (do cenário 1)
- Context budget definido na ADR-0002: ~4K system + ~8K chunks.
- Documentos contraditórios tratados com metadado de vigência (ADR-0003).
- System prompt versionado em `/prompts/system-prompt.md`.

## Dependencies
- Azure AI Search index deve estar populado (módulo `pipeline-ingestao`).
- System prompt deve estar finalizado (ver `/prompts/system-prompt.md`).

## Conexão com o cenário 1
O protótipo de RAG com ferramentas open-source (ChromaDB + sentence-transformers, Dev 1.3) **validou a abordagem** e expôs o problema de chunking de tabelas (ADR-0004). Este plan é a versão de **produção**: a mesma sequência (embed → search → prompt → complete) agora roda sobre Azure AI Search + Azure OpenAI, com os padrões do projeto (Zod, pino, errors customizados).
