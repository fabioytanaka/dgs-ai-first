# Problemas Identificados no Pipeline de RAG e Propostas de Correção

**Exercício 1.3 — NovaTech Assistente de Atendimento IA**

---

## Problema 1 — Conflito de versões de documento recuperadas no mesmo resultado

### Descrição
Ao executar o Teste 4 ("Qual o multiplicador de frete para o Sudeste?"), o pipeline retornou chunks de **ambas** as versões do PROC-042 no top 3:
- PROC-042-frete-especial-v1 (mar/2023): Sudeste = **1.0**
- PROC-042-v2-frete-especial-revisado (nov/2023): Sudeste = **1.1**

Como os dois documentos compartilham vocabulário quase idêntico (mesmas tabelas, mesma estrutura de seções), o embedding de similaridade não consegue distinguir qual versão é mais relevante — ambas têm scores próximos (0.88 e 0.85).

**Risco:** Se o prompt não tratar explicitamente o conflito, o LLM pode:
- Usar o valor mais antigo (1.0) sem perceber que há uma versão mais recente
- Misturar valores das duas versões na mesma resposta (ex: usar multiplicador da v1 com fator de peso da v2)
- Apresentar o valor mais recente sem alertar o atendente sobre a existência de chamados que ainda usam a tabela antiga

### Evidência
Detectado durante o Teste 4. O `prompt_builder.py` sinalizou o conflito via `_detect_version_conflicts()`, mas a detecção depende de padronização dos nomes de arquivo — nomes diferentes poderiam não ser detectados.

### Proposta de Correção

**Correção 1 (curto prazo) — Metadado de vigência explícito:**
Adicionar campo `vigencia_inicio` e `vigencia_fim` aos metadados de cada documento durante a ingestão. Durante a montagem do prompt, o `PromptBuilder` usa esse metadado para ordenar chunks de versões concorrentes, sempre priorizando o mais recente.

```python
# Em ingest.py — extrair vigência do cabeçalho do documento
def _extract_vigencia(self, content: str) -> dict:
    # Regex para "Data de emissão: 10/11/2023" → {"vigencia_inicio": "2023-11-10"}
    match = re.search(r'Data de emissão.*?(\d{2}/\d{2}/\d{4})', content)
    if match:
        return {"vigencia_inicio": match.group(1)}
    return {}
```

**Correção 2 (médio prazo) — Estratégia de deduplicação por documento-raiz:**
No retrieval, identificar documentos com o mesmo "raiz" (ex: PROC-042) e retornar apenas o mais recente automaticamente, a menos que o chamado seja anterior à data de vigência da versão mais recente.

**Correção 3 (processo) — Marcar PROC-042 v1 como obsoleto:**
A raiz do problema é operacional: o PROC-042 v1 nunca foi marcado como obsoleto no SharePoint. A correção mais efetiva é cultural/processual: implementar revisão de documentos que define obrigatoriamente a data de obsolescência ao publicar uma nova versão.

---

## Problema 2 — Chunking que corta tabela de multiplicadores em documentos longos

### Descrição
O PROC-042-v2 tem a tabela de multiplicadores regionais no meio de uma seção longa (Seção 2). Dependendo do tamanho do chunk configurado e do conteúdo textual antes da tabela, é possível que o chunk que inicia antes da tabela seja cortado **antes** que a tabela complete.

Resultado observado durante os testes: quando a seção 2 (fórmula + tabela) é longa o suficiente para exceder o `MAX_CHUNK_TOKENS`, o overlap de 15% pode retornar o início da tabela no final de um chunk e o restante no chunk seguinte:

```
Chunk 1 (500 tokens): "...Fator de peso: 1.0 para 500-1.000kg... | Região | Multiplicador |
|--------|------|  | Sul | 1.3 | | Sudeste | 1.1 |"

Chunk 2 (500 tokens): "| Centro-Oeste | 1.4 | | Nordeste | 1.5 | | Norte | 1.8 |"
```

**Risco:** Uma pergunta sobre "multiplicador do Norte" pode recuperar apenas o Chunk 2, que não tem o prefixo da tabela — o LLM vê uma lista de pares sem contexto e pode errar na interpretação de qual coluna é qual.

### Evidência
Identificado ao analisar o teste `TestChunkingQuality.test_table_not_split`. O chunk recuperado para a query "tabela multiplicadores regionais" continha apenas parte das regiões quando a tabela era fragmentada.

### Proposta de Correção

**Correção 1 (curto prazo) — Detecção de tabela Markdown antes do corte:**
No `DocumentChunker._protect_tables()`, verificar se o chunk atual termina no meio de uma tabela Markdown antes de fazer o corte. Se o corte cair dentro de um bloco de tabela (detectado por `|` no início da linha), atrasar o corte para após o fim da tabela.

```python
def _find_safe_cut_point(self, words: list, target_end: int) -> int:
    """Encontra um ponto de corte que não quebre uma tabela."""
    # Reconstrói o texto parcial para detectar tabelas
    partial_text = ' '.join(words[:target_end])
    # Se a última linha for parte de uma tabela, busca o fim da tabela
    lines = partial_text.split('\n')
    for i in range(len(lines) - 1, -1, -1):
        if not lines[i].strip().startswith('|'):
            return len(' '.join(lines[:i+1]).split())
    return target_end
```

**Correção 2 (médio prazo) — Chunk dedicado por tabela com contexto completo:**
Extrair cada tabela como um chunk próprio, prefixado com o contexto do heading e os valores das colunas explicitados em texto:

```
"Tabela de multiplicadores regionais — PROC-042-v2, seção 2.1, nov/2023:
Sul=1.3, Sudeste=1.1, Centro-Oeste=1.4, Nordeste=1.5, Norte=1.8"
```

Isso também melhora o retrieval semântico, pois o texto descritivo é mais similar à pergunta do usuário do que o formato `| Região | 1.3 |`.

---

## Problema 3 — FAQ como fonte de igual peso a documentos normativos no retrieval

### Descrição
O FAQ-Atendimento tem linguagem informal e coloquial muito próxima da linguagem das perguntas dos atendentes (ex: "Na prática, a gente orienta..."). Isso faz com que o embedding do FAQ tenha alta similaridade semântica com perguntas práticas, colocando o FAQ no top 3 dos resultados com frequência.

**Risco:** Para perguntas críticas (valores de SLA, prazos de devolução), o FAQ pode aparecer antes do documento normativo, e se o prompt não tratar a hierarquia, o LLM usa o FAQ como fonte primária.

### Evidência
No Teste 1, o FAQ apareceu no rank 3 com score 0.61 para "prazo de devolução" — próximo o suficiente para influenciar a resposta.

### Proposta de Correção

**Correção — Peso de confiabilidade na re-ranqueamento pós-retrieval:**
Após o retrieval semântico, aplicar um fator de desconto nos scores do FAQ antes de ordenar:

```python
RELIABILITY_WEIGHTS = {
    "POL": 1.0,    # documentos normativos
    "PROC": 1.0,
    "SLA": 1.0,
    "FAQ": 0.75    # desconto de 25% para FAQ
}

def rerank_by_reliability(chunks):
    for chunk in chunks:
        source = chunk["metadata"]["source"]
        prefix = source.split("-")[0].upper()
        weight = RELIABILITY_WEIGHTS.get(prefix, 0.9)
        chunk["adjusted_score"] = chunk["score"] * weight
    return sorted(chunks, key=lambda x: x["adjusted_score"], reverse=True)
```

---

## Sumário

| Problema | Impacto | Severidade | Correção prioritária |
|----------|---------|-----------|----------------------|
| 1 — Conflito de versões do PROC-042 | Valores incorretos de frete repassados a clientes | 🔴 Crítico | Metadado de vigência + deduplicação por raiz |
| 2 — Tabela cortada pelo chunking | Multiplicadores parciais retornados | 🟠 Alto | Detecção de tabela antes do corte |
| 3 — FAQ com peso igual a normativos | Resposta baseada em fonte não validada | 🟡 Médio | Re-ranqueamento pós-retrieval |
