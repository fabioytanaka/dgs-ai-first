# Resultados dos Testes — System Prompt v2

**Método:** Mesmo método do v1 — prompt v2 colado no início da conversa no Claude, seguido dos chunks simulados + perguntas. Adicionado teste extra com ambas as versões do PROC-042 para validar a Regra 5 expandida.

---

## Teste 1 — "Qual o prazo de devolução para carga perigosa?"

**Resposta obtida com prompt v2:**

> "Carga perigosa NÃO é elegível para devolução pelo processo padrão.
>
> Base documental: Conforme POL-001, seção 3.2 (versão 3.1, jan/2024), cargas classificadas como perigosas (classes 1 a 6 da ANTT, conforme Resolução ANTT nº 5.947/2021) estão explicitamente excluídas do processo padrão de devolução.
>
> Exceção: Existe um processo de tratamento especial — o cliente deve contatar o setor de Gestão de Riscos (ramal 4500) para análise individual.
>
> Ação recomendada: Oriente o cliente a ligar no ramal 4500. NÃO informe que a devolução é possível pelo processo padrão."

**Análise:**
- ✅ Resposta correta e mais clara que v1 — usa "NÃO" em maiúsculas
- ✅ Citou versão e data do documento (melhoria do v2)
- ✅ Formato estruturado seguido corretamente
- ✅ Instrução explícita ao atendente sobre o que NÃO fazer
- ✅ Melhoria verificável vs v1: formato mais claro, instrução negativa explícita

**Resultado: APROVADO** ✅ (melhora sobre v1)

---

## Teste 2 — "Meu cliente é Gold, qual o SLA de resolução?"

**Resposta obtida:**

> "Para clientes Gold, o SLA de resolução é de até 24 horas úteis (chamados gerais).
>
> Base documental: SLA-2024 (versão 2024.1, jan/2024) — Clientes Gold têm resolução de chamados gerais em até 24h úteis e primeira resposta em até 2h úteis.
>
> Exceção: Para incidentes críticos, os prazos são diferentes. Essa informação não está no trecho disponível — consulte a tabela SLA-2024 completa para incidentes críticos."

**Análise:**
- ✅ Resposta correta
- ✅ Distingue chamados gerais de incidentes críticos (mesmo sem o dado, informa a distinção)
- ✅ Formato correto
- ✅ Citação com versão e data

**Resultado: APROVADO** ✅

---

## Teste 3 — "Quanto custa o frete para 600kg para Manaus?"

**Resposta obtida:**

> "Calculando o frete especial para 600kg com destino a Manaus (região Norte):
>
> Fórmula: Valor do frete = Valor base × Multiplicador regional × Fator de peso
>
> Valores identificados (PROC-042-v2, seção 2, versão 2.0, nov/2023):
> - Multiplicador da região Norte: **1.8**
> - Fator de peso para 600kg (faixa 500–1.000kg): **1.0**
>
> Resultado: Frete = Valor base × 1.8 × 1.0 = **Valor base × 1.8**
>
> Não posso calcular o valor final pois o Valor base (tabela mensal de fretes) não está nos documentos disponíveis.
>
> Fonte: PROC-042-v2, seção 2, versão 2.0."

**Análise:**
- ✅ Formato de cálculo seguido corretamente (melhoria clara do v2)
- ✅ Valores identificados separados do resultado
- ✅ Honesto sobre o que falta para completar o cálculo
- ✅ Citação com versão e data

**Resultado: APROVADO** ✅ (melhora verificável vs v1 no formato)

---

## Teste 4 (adicional) — Cenário de conflito de versões

**Setup:** Para este teste, foram fornecidos chunks de AMBAS as versões da PROC-042 (v1 com Norte=1.6, v2 com Norte=1.8).

**Pergunta:** "Qual o multiplicador de frete para a região Norte?"

**Resposta obtida:**

> "⚠️ Atenção: foram encontradas duas versões do mesmo documento com valores diferentes.
>
> PROC-042 v1 (mar/2023): Multiplicador da região Norte = **1.6**
> PROC-042-v2 (nov/2023): Multiplicador da região Norte = **1.8**
>
> Usando como padrão a versão mais recente (v2, nov/2023): multiplicador = **1.8**.
>
> Para chamados abertos a partir de 01/12/2023, use 1.8. Para chamados anteriores ainda em processamento, confirme com o supervisor se devem usar a tabela antiga (1.6).
>
> Fonte principal: PROC-042-v2, seção 2.1. Fonte alternativa: PROC-042 v1, seção 2.1."

**Análise:**
- ✅ Regra 5 ativada corretamente — não misturou os valores
- ✅ Apresentou ambas as versões com datas
- ✅ Definiu padrão (mais recente) e instruiu sobre casos de exceção
- ✅ Esta resposta seria impossível com o prompt v1 (que não tinha instrução suficientemente diretiva)

**Resultado: APROVADO** ✅ — demonstra melhoria crítica do v2 sobre v1

---

## Comparação consolidada v1 × v2

| Critério | v1 | v2 |
|----------|----|----|
| Resposta correta para carga perigosa | ✅ | ✅ (mais clara) |
| Formato estruturado por tipo de pergunta | ❌ genérico | ✅ diferenciado |
| Instrução de conflito de versões | ⚠️ insuficiente | ✅ diretiva e completa |
| Aviso de confiabilidade do FAQ | ❌ ausente | ✅ Regra 6 |
| Citação com versão e data do documento | ⚠️ incompleta | ✅ completa |
| Iteração verificável | — | ✅ 4 melhorias concretas |
