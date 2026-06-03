# Specification — Cenário 1: Assistente de IA para Atendimento NovaTech
**Papel:** Desenvolvedor  
**Trilha:** AI First — DB1 Global Software  
**Data:** Junho/2026  
**Branch:** cenario-1

---

## 1. Contexto do Projeto

A NovaTech é uma empresa de logística com 1.200 funcionários. A equipe de atendimento (45 pessoas) gasta em média **12 minutos por chamado** buscando informações em documentação dispersa em SharePoint (~800 docs), Confluence (~400 páginas) e planilhas de rede (~50 arquivos XLSX).

O objetivo é construir um **assistente de IA baseado em RAG** que permita consultas em linguagem natural com respostas fundamentadas na documentação oficial.

---

## 2. Escopo dos Exercícios (papel: Desenvolvedor)

| Exercício | Título | Ferramenta Principal |
|-----------|--------|----------------------|
| 1.1 | Análise de viabilidade técnica com fundamentos de LLM e engenharia de contexto | Claude (chat) |
| 1.2 | Prototipação de prompt com engenharia de contexto | Claude (chat) |
| 1.3 | Construção de pipeline de RAG com ferramentas open-source | Claude + GitHub Copilot |

---

## 3. Entregáveis por Exercício

### Exercício 1.1
- `exercicio-1.1/analise-viabilidade-tecnica.md` — Análise técnica final com estimativa de tokens, estratégia de chunking, orçamento de contexto, e feedback do Claude incorporado.

### Exercício 1.2
- `exercicio-1.2/system-prompt-v1.md` — System prompt versão 1 com mapeamento estático/dinâmico
- `exercicio-1.2/resultados-teste-v1.md` — Resultado dos testes com análise crítica
- `exercicio-1.2/system-prompt-v2.md` — System prompt versão 2 (iterado)
- `exercicio-1.2/resultados-teste-v2.md` — Resultados da segunda rodada e comparação

### Exercício 1.3
- `exercicio-1.3/src/ingest.py` — Script de ingestão de documentos com chunking + embeddings + ChromaDB
- `exercicio-1.3/src/retrieval.py` — Função de busca por similaridade
- `exercicio-1.3/src/prompt_builder.py` — Montagem do prompt final (system + chunks + pergunta)
- `exercicio-1.3/src/main.py` — Pipeline orquestrador end-to-end
- `exercicio-1.3/tests/test_retrieval.py` — 5 testes com gabarito do Anexo B
- `exercicio-1.3/docs/resultados-testes.md` — Documentação dos resultados, chunks recuperados vs esperados
- `exercicio-1.3/docs/problemas-identificados.md` — 2+ problemas reais encontrados com propostas de correção

---

## 4. Stack Técnica

| Componente | Tecnologia | Justificativa |
|------------|-----------|---------------|
| Linguagem | Python 3.11+ | Ecossistema ML mais rico |
| Vector store | ChromaDB | Open-source, local, zero configuração |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Gratuito, qualidade razoável para PT-BR |
| Orquestração | Código manual (sem LangChain) | Entender as abstrações antes de usá-las |
| LLM para testes | Claude (via chat manual) | Conforme especificação do exercício |
| Documentação | Markdown | Legibilidade e versionamento no Git |

---

## 5. Critérios de Aceitação Técnicos

- [ ] Pipeline roda do início ao fim sem erros críticos
- [ ] Chunking justificado (não fixo em 512 tokens sem motivo)
- [ ] 5 testes documentados com comparação vs Anexo B (≥ 3/5 corretos)
- [ ] 2+ problemas reais identificados com propostas concretas de correção
- [ ] System prompt com constraints claros, não genérico
- [ ] Mapeamento estático/dinâmico do contexto documentado
- [ ] Iteração v1 → v2 verificável (melhoria concreta documentada)

---

## 6. Estrutura do Repositório

```
dgs-ai-first/
└── cenario-1/
    ├── specification.md          ← este arquivo
    ├── README.md                 ← índice dos entregáveis
    ├── exercicio-1.1/
    │   └── analise-viabilidade-tecnica.md
    ├── exercicio-1.2/
    │   ├── system-prompt-v1.md
    │   ├── resultados-teste-v1.md
    │   ├── system-prompt-v2.md
    │   └── resultados-teste-v2.md
    └── exercicio-1.3/
        ├── src/
        │   ├── ingest.py
        │   ├── retrieval.py
        │   ├── prompt_builder.py
        │   └── main.py
        ├── tests/
        │   └── test_retrieval.py
        └── docs/
            ├── resultados-testes.md
            └── problemas-identificados.md
```
