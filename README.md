# Cenário 1 — Fase de Entendimento e Contexto
**Trilha AI First — DB1 Global Software**  
**Papel:** Desenvolvedor  
**Branch:** `cenario-1`  
**Prazo:** 06/06/2026

---

## Índice de Entregáveis

### Specification
- [`specification.md`](./specification.md) — Plano, escopo, stack e critérios de aceitação

### Exercício 1.1 — Análise de Viabilidade Técnica
> **Tópicos:** Fundamentos de LLM (tokens, context window), Engenharia de Contexto (lost in the middle, orçamento de atenção), RAG (desafios de extração)

- [`exercicio-1.1/analise-viabilidade-tecnica.md`](./exercicio-1.1/analise-viabilidade-tecnica.md)
  - Análise por tipo de fonte (PDFs com tabelas, PDFs escaneados, Confluence, XLSX)
  - Estimativa de tokens: 4–8 milhões de tokens na base completa
  - Análise de orçamento de contexto: 8 chunks × 500 tokens como sweet spot
  - Estratégia de chunking por seção semântica (justificada pelo lost in the middle)
  - Iteração com Claude documentada: 5 pontos incorporados

### Exercício 1.2 — Prototipação de Prompt com Engenharia de Contexto
> **Tópicos:** Engenharia de Prompt (system prompt), Engenharia de Contexto (estático vs dinâmico)

- [`exercicio-1.2/system-prompt-v1.md`](./exercicio-1.2/system-prompt-v1.md) — System prompt v1 + mapeamento estático/dinâmico
- [`exercicio-1.2/resultados-teste-v1.md`](./exercicio-1.2/resultados-teste-v1.md) — Testes v1 com análise crítica
- [`exercicio-1.2/system-prompt-v2.md`](./exercicio-1.2/system-prompt-v2.md) — System prompt v2 com melhorias documentadas
- [`exercicio-1.2/resultados-teste-v2.md`](./exercicio-1.2/resultados-teste-v2.md) — Testes v2 e comparação com v1

**Armadilha tratada:** Pergunta "prazo de devolução para carga perigosa" → resposta correta é que **NÃO** pode devolver (POL-001, seção 3.2). Identificada e corrigida na v2.

### Exercício 1.3 — Pipeline de RAG com Ferramentas Open-Source
> **Tópicos:** RAG (pipeline completo), Engenharia de Contexto (chunks como unidade de contexto)

```
exercicio-1.3/
├── src/
│   ├── ingest.py          # Ingestão: lê .md → chunking semântico → embeddings → ChromaDB
│   ├── retrieval.py       # Busca por similaridade semântica
│   ├── prompt_builder.py  # Monta prompt completo (system + chunks + pergunta)
│   └── main.py            # Orquestrador: --ingest | --query | --test
├── tests/
│   └── test_retrieval.py  # 5 testes com gabarito do Anexo B
├── docs/
│   ├── resultados-testes.md          # Resultado dos 5 testes com análise
│   └── problemas-identificados.md   # 3 problemas reais + propostas de correção
└── requirements.txt
```

**Como executar:**
```bash
pip install -r exercicio-1.3/requirements.txt

# 1. Ingere os documentos
python exercicio-1.3/src/main.py --ingest

# 2. Testa o pipeline com as 5 queries do Anexo B
python exercicio-1.3/src/main.py --test

# 3. Faz uma query livre
python exercicio-1.3/src/main.py --query "Posso devolver carga perigosa?" --tier Gold

# 4. Roda os testes unitários
python exercicio-1.3/tests/test_retrieval.py
```

---

## Evidências de Uso das Ferramentas

| Ferramenta | Evidência |
|------------|-----------|
| Claude (chat) — Exercício 1.1 | Iteração documentada em `analise-viabilidade-tecnica.md`, seção 5 — 5 pontos de feedback incorporados com comparação antes/depois |
| Claude (chat) — Exercício 1.2 | System prompts v1 e v2 testados no Claude; análise de 4 perguntas com respostas reais documentadas em `resultados-teste-v*.md` |
| GitHub Copilot — Exercício 1.3 | Comentários inline `# Copilot foi usado para...` nos arquivos `ingest.py`, `retrieval.py`, `prompt_builder.py` e `test_retrieval.py` identificam as seções onde o Copilot gerou completions |

---

## Conceitos Demonstrados

| Conceito | Onde aparece |
|----------|-------------|
| Tokens e context window | Ex 1.1 — Estimativa de 4-8M tokens vs 128K da janela |
| Orçamento de atenção | Ex 1.1 — Sweet spot de 8 chunks para evitar lost in the middle |
| Lost in the middle | Ex 1.1 — Referência de pesquisa + recomendação de 5-10 chunks |
| Contexto estático vs dinâmico | Ex 1.2 — Tabela com estimativa de tokens por componente |
| Engenharia de prompt | Ex 1.2 — System prompt com 6 guardrails, iterado de v1 para v2 |
| RAG como sistema de dados | Ex 1.3 — Chunking semântico, detecção de conflito de versões, re-ranking |
| Chunks como unidade de contexto | Ex 1.3 — `prompt_builder.py` com orçamento e detecção de conflitos |
