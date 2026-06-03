# Exercício 1.1 — Análise de Viabilidade Técnica com Fundamentos de LLM e Engenharia de Contexto

**Papel:** Desenvolvedor  
**Ferramentas usadas:** Claude (chat) — iteração documentada na seção 5  
**Data:** Junho/2026

---

## 1. Análise por Tipo de Fonte

### 1.1 PDFs com tabelas complexas (SharePoint)

**Desafio para o pipeline de RAG:**  
Tabelas com 15+ colunas como as de frete (PROC-042) são frequentemente destruídas durante a extração de texto de PDF. Bibliotecas como `pdfminer` e `PyMuPDF` linearizam tabelas em sequências de texto sem estrutura, perdendo o alinhamento linha × coluna. O chunk resultante pode ser algo como `"Sul 1.2 Sudeste 1.0 Centro-Oeste 1.3..."` — texto que o embedding trata como sequência de palavras, não como tabela estruturada. Uma pergunta como "qual o multiplicador do Nordeste?" pode não recuperar o chunk correto se a representação semântica da tabela colapsada for fraca.

**Impacto na qualidade das respostas:**  
O LLM recebe texto malformado e pode inferir valores incorretos, ou o retrieval pode falhar completamente — o chunk da tabela de frete não sobe no ranking de similaridade porque a representação vetorial de uma tabela linearizada é pobre.

**Estratégia de tratamento:**  
- Usar `pdfplumber` (não `pdfminer`) para extração, pois preserva estrutura de tabelas como objetos separados.
- Converter tabelas para Markdown estruturado antes do chunking: `| Região | Multiplicador |`.
- Criar chunks separados para cada tabela, com prefixo de contexto: `"Tabela de multiplicadores regionais PROC-042-v2, seção 2.1: [tabela em markdown]"`.
- Não cortar tabelas no meio de um chunk — usar chunking por seção semântica, não por token count fixo.

---

### 1.2 PDFs escaneados (OCR necessário)

**Desafio:**  
~15% dos PDFs do SharePoint são documentos escaneados. PDFs escaneados são imagens — não há texto extraível diretamente. Sem OCR, esses documentos ficam invisíveis para o pipeline. Com OCR ruim (ex: Tesseract sem fine-tuning para PT-BR), o texto extraído pode conter erros que corrompem o significado (ex: "3 dias úteis" virando "8 dias úteis").

**Impacto:**  
Documentos ausentes do índice = silêncio no retrieval (o assistente não encontra a informação). Documentos com OCR ruim = alucinação involuntária embutida na base de conhecimento.

**Estratégia de tratamento:**  
- Usar Azure AI Document Intelligence (ou similar) para OCR com maior acurácia em PT-BR do que Tesseract puro.
- Implementar etapa de QA de extração: comparar número de palavras esperadas × extraídas; documentos com baixa densidade de texto disparam alerta manual.
- Marcar documentos com origem OCR nos metadados do chunk para que o sistema possa indicar menor confiança na resposta.

---

### 1.3 Wiki do Confluence (HTML com links internos e macros)

**Desafio:**  
Páginas wiki têm: (a) links internos que criam dependências entre páginas — uma página pode só fazer sentido no contexto da página anterior; (b) macros customizadas (ex: painéis de aviso, expandable sections) que renderizam como HTML não-semântico; (c) estrutura de headings que pode não refletir a hierarquia real do conteúdo.

**Impacto:**  
Links internos não seguidos = chunks sem contexto suficiente. Um chunk que diz "conforme descrito acima" ou "veja seção 3.2 desta página" perde completamente o sentido quando isolado.

**Estratégia de tratamento:**  
- Usar a API REST do Confluence para exportar páginas como JSON estruturado (não HTML raw).
- Resolver links internos durante a ingestão: quando a página A referencia a página B, incluir um resumo de B no chunk de A como metadado contextual.
- Filtrar macros via limpeza de HTML antes do chunking (BeautifulSoup com remoção de tags não-textuais).
- Usar o título da página e breadcrumbs como prefixo do chunk para preservar hierarquia.

---

### 1.4 Planilhas com fórmulas interdependentes (XLSX)

**Desafio:**  
Planilhas de referência de frete têm fórmulas que calculam valores dinâmicos (ex: `=B2*VLOOKUP(C2,tabela_mult,2,0)`). O texto extraído da planilha não contém os valores calculados — contém as fórmulas em texto. Uma pergunta sobre "qual o valor do frete base" pode recuperar um chunk com `=B2*...` que não responde nada para o LLM.

**Impacto:**  
O LLM recebe fórmulas em vez de dados, o que gera respostas nonsense ou recusa ("não encontrei a informação").

**Estratégia de tratamento:**  
- Usar `openpyxl` com `data_only=True` para extrair valores calculados (não fórmulas) das células.
- Exportar planilhas como tabelas Markdown antes da ingestão.
- Para planilhas atualizadas mensalmente, automatizar a re-ingestão ao detectar mudança de hash do arquivo.

---

## 2. Estimativa de Tamanho da Base em Tokens

### Premissas de cálculo

- Regra prática: **1 token ≈ 0,75 palavras** (ou ~4 caracteres em inglês; para PT-BR, ligeiramente mais — usar 0,70 palavras/token por segurança)
- Fórmula: tokens = palavras / 0,75

### Cálculo por fonte

#### SharePoint — PDFs (~800 documentos)
- Média estimada: 10 páginas por documento
- Palavras por página em PDF corporativo: ~300 palavras (considerando tabelas, cabeçalhos, espaço em branco)
- Total de palavras: 800 docs × 10 páginas × 300 palavras = **2.400.000 palavras**
- Tokens estimados: 2.400.000 / 0,75 ≈ **3.200.000 tokens**

#### Confluence Wiki (~400 páginas)
- Média informada: 1.500 palavras por página
- Total de palavras: 400 × 1.500 = **600.000 palavras**
- Tokens estimados: 600.000 / 0,75 = **800.000 tokens**

#### Planilhas (~50 arquivos XLSX)
- Planilha de frete: estimativa de 500 células com dados alfanuméricos ≈ 200 palavras por planilha
- Total de palavras: 50 × 200 = **10.000 palavras**
- Tokens estimados: 10.000 / 0,75 ≈ **13.300 tokens**

#### Total estimado

| Fonte | Tokens estimados |
|-------|-----------------|
| SharePoint (PDFs) | ~3.200.000 |
| Confluence (Wiki) | ~800.000 |
| Planilhas (XLSX) | ~13.300 |
| **Total** | **~4.013.300 tokens** |

> **Nota pós-revisão com Claude:** A estimativa inicial de 10 páginas/doc pode ser otimista. Documentos de política e compliance tendem a ser mais densos (15-20 páginas). Uma estimativa conservadora revisada chegaria a ~6-8 milhões de tokens. A estimativa de 4M tokens é o cenário otimista.

**Conclusão:** A base completa tem **4 a 8 milhões de tokens** — não cabe em nenhuma janela de contexto disponível (GPT-4o: 128K tokens). Isso confirma a necessidade de RAG: **o modelo nunca verá todos os documentos de uma vez**.

---

## 3. Análise de Orçamento de Contexto

### Composição do contexto por query

Modelo de referência: GPT-4o (128K tokens de janela de contexto)

| Componente | Tamanho estimado | Tipo |
|------------|-----------------|------|
| System prompt (identidade + regras + guardrails) | ~800 tokens | Estático |
| Metadados do cliente (tier, contrato) | ~100 tokens | Dinâmico por sessão |
| Histórico de conversa (últimas 3 trocas) | ~1.500 tokens | Dinâmico, crescente |
| Pergunta do atendente | ~50 tokens | Dinâmico por query |
| **Orçamento disponível para chunks** | **~125.550 tokens** | Dinâmico por query |

### Quantos chunks cabem?

Com chunks de **500 tokens** cada:  
`125.550 / 500 ≈ 251 chunks por query`

**Por que não usar todos os 251 chunks?** Aqui entra o efeito **Lost in the Middle**.

### Efeito Lost in the Middle

Pesquisa de Liu et al. (2023) demonstrou que LLMs têm desempenho significativamente pior ao usar informação posicionada no **meio** de contextos longos. O desempenho cai progressivamente conforme os documentos relevantes ficam mais "enterrados" no centro do contexto. Informação no início e no fim do contexto é muito mais utilizada.

**Implicação prática:** Enviar 251 chunks não significa que o LLM usará todos — na prática, chunks no meio serão ignorados. Experimentos indicam que **5 a 10 chunks** é o intervalo prático ideal:
- Suficiente para cobrir perguntas multi-domínio (ex: frete + devolução + SLA).
- Pequeno o suficiente para que todos os chunks fiquem na zona de alta atenção do modelo.
- Permite reservar espaço para histórico de conversa sem sacrificar qualidade.

**Orçamento prático recomendado:**
- **8 chunks de 500 tokens** = 4.000 tokens para contexto de documentação
- Sobra ~121.000 tokens para histórico extenso se necessário

---

## 4. Estratégia de Chunking Recomendada

### Por que não usar 512 tokens fixos?

Chunking fixo em 512 tokens sem considerar a estrutura do documento quebra regras de negócio no meio:

```
❌ Exemplo ruim — chunk fixo corta uma tabela:
"...O cliente pode solicitar a devolução em até 7 dias úteis. 3.2. Exceções As
seguintes categorias NÃO são elegíveis: Cargas perigosas classes 1 a 6 da ANTT..."

[CORTE AQUI — 512 tokens]

"...Inclui: explosivos (classe 1), gases (classe 2)..."
```

O segundo chunk, sem o contexto "são exceções de devolução", pode ser recuperado para uma pergunta sobre devolução e levar o LLM a inferir que gases são elegíveis para devolução.

### Estratégia recomendada: Chunking por Seção Semântica

**Princípio:** Usar a estrutura do documento (headings H2/H3) como delimitadores naturais de chunk.

**Regras:**
1. Cada seção numerada vira no mínimo um chunk (ex: `3.1 Prazo geral`, `3.2 Exceções`)
2. Seções longas (>700 tokens) são divididas com **overlap de 15%** (105 tokens) para preservar contexto de fronteira
3. Tabelas nunca são cortadas — recebem chunk próprio com prefixo contextual
4. Cada chunk recebe metadados: `{fonte, versão, seção, data_publicação, hash_documento}`

**Justificativa pelo tipo de pergunta:**  
O atendente pergunta: "Posso devolver carga perigosa?" → O retrieval precisa encontrar a seção 3.2 completa (com a regra de exceção intacta), não um fragmento que menciona "carga perigosa" sem a negação.

**Justificativa pelo lost in the middle:**  
Chunks menores e mais focados semanticamente permitem que os 8 chunks recuperados sejam todos altamente relevantes, maximizando o aproveitamento do orçamento de atenção.

---

## 5. Iteração com Claude — Pontos Fracos Identificados e Incorporados

**Prompt enviado ao Claude:**  
> "Revise esta análise técnica de viabilidade de RAG para a NovaTech. Identifique estimativas otimistas demais, riscos não cobertos e lacunas de raciocínio."

**Feedback recebido e incorporações:**

| Ponto levantado pelo Claude | Incorporação na análise |
|-----------------------------|------------------------|
| "A estimativa de 300 palavras/página pode ser baixa para documentos de compliance" | Adicionei nota de revisão na seção 2 com range conservador de 4-8M tokens |
| "OCR ruim embute erro na fonte de verdade — é pior que ausência" | Adicionei risco de OCR com QA de extração na seção 1.2 |
| "Planilhas atualizadas mensalmente precisam de re-ingestão automatizada" | Adicionei estratégia de hash para re-ingestão incremental na seção 1.4 |
| "Lost in the middle foi mencionado mas não quantificado" | Adicionei referência de pesquisa e recomendação concreta de 5-10 chunks |
| "Confluência com macros customizadas é subestimada como risco" | Expandido a seção 1.3 com tratamento específico de macros |

**Diferença verificável:** A versão inicial da estimativa de tokens era um número único (~4M). Após o feedback, a análise apresenta um range (4-8M) com justificativa de variância. A análise de chunking original dizia apenas "usar seções do documento" — após revisão, especifica regras concretas (overlap de 15%, chunk próprio para tabelas, tamanho máximo de 700 tokens).

---

## 6. Sumário de Riscos Técnicos

| Risco | Probabilidade | Impacto |
|-------|--------------|---------|
| Extração destrutiva de tabelas PDF | Alta | Alto — multiplicadores de frete incorretos nas respostas |
| OCR com erros em ~15% dos PDFs | Alta | Alto — erros embutidos na base de conhecimento |
| Documentos contraditórios (PROC-042 v1 vs v2) | Confirmada | Crítico — respostas que misturam regras de versões diferentes |
| Lost in the middle com muitos chunks | Média | Médio — degradação silenciosa de qualidade |
| Re-ingestão não automatizada de planilhas mensais | Alta (sem processo) | Médio — respostas baseadas em dados desatualizados |
