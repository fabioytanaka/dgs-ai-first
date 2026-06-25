# Requirements — Query Endpoint

> **Autor:** Product Specialist (Ex. PS 2.1). **Status:** Aprovado pelo Tech Lead (Gate 1).
> **Bounded context:** Atendimento ao Cliente. **Não cobre:** Gestão Documental (ingestão) nem Logística de Frete (cálculo de valores) diretamente — apenas responde sobre o que está indexado.
> Reproduzido aqui como **input** para o Dev 2.2 (a fonte de verdade é a spec do PS).

## Outcomes (resultado para o usuário)
- O atendente recebe uma resposta relevante e citada em **menos de 30 segundos**.
- Toda resposta **cita ao menos uma fonte** (documento + seção).
- Quando a confiança é baixa, a resposta inclui **aviso explícito** e sugere escalar ao supervisor.
- Cargas perigosas (classes 1–6 da ANTT) **nunca** recebem informação de devolução pelo processo padrão.

## Scope boundaries
- **Dentro:** receber pergunta do atendente, recuperar chunks, montar prompt, chamar o modelo, retornar resposta + `source_document`.
- **Fora:** ingestão/indexação de documentos (módulo `pipeline-ingestao`), cálculo determinístico de frete, e UI (Teams/painel).

## Constraints
- Context budget (ADR-0002): ~4K tokens de system prompt + ~8K de chunks (5 chunks de ~1.500 tokens) + pergunta + histórico ≤ 3 turnos.
- Documentos contraditórios (ADR-0003): priorizar versão **vigente** (metadado de vigência); informar que existe versão anterior.
- Modelo: Azure OpenAI GPT-4o (ADR-0001).
- Stack: TypeScript strict, Azure Functions v4, Zod, pino.

## Prior decisions
- ADR-0001 — Azure OpenAI (GPT-4o), janela 128K.
- ADR-0002 — Context budget (~4K system + ~8K chunks).
- ADR-0003 — Documentos contraditórios: metadado de vigência, priorizar mais recente.
- ADR-0004 — Pipeline Azure AI Search; chunking de tabelas validado no protótipo open-source (cenário 1).

## Verification criteria (testáveis pelo QA)
- VC-01: Resposta em < 30s para 95% das queries.
- VC-02: 100% das respostas incluem o campo `source_document` no JSON.
- VC-03: Queries sobre carga perigosa + devolução retornam negativa explícita.
- VC-04: Queries sem match retornam mensagem padrão de "não encontrado".
- VC-05: Input inválido (sem `question`, vazio, ou > limite) retorna **400** com erro estruturado, sem chamar o modelo.
