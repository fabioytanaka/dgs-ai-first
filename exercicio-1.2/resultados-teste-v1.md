# Resultados dos Testes — System Prompt v1

**Método:** O system prompt v1 foi colado no início de uma conversa no Claude, seguido dos 3 chunks simulados (A, B, C) fornecidos no exercício, e então cada pergunta foi enviada como mensagem do atendente.

---

## Chunks fornecidos no teste

```
Chunk A (POL-001, seção 3.2):
"Mercadorias podem ser devolvidas em até 7 dias úteis após o recebimento, 
exceto cargas classificadas como perigosas (classes 1 a 6 da ANTT). 
O cliente deve abrir chamado no portal e anexar fotos da mercadoria."

Chunk B (SLA-2024):
"Cliente Gold — resposta em até 2h, resolução em até 24h. 
Cliente Silver — resposta em até 4h, resolução em até 48h. 
Cliente Standard — resposta em até 8h, resolução em até 72h."

Chunk C (PROC-042-v2, seção 2):
"Frete especial para cargas acima de 500kg: valor base × multiplicador regional. 
Região Sul: 1.3. Região Sudeste: 1.1. Região Norte: 1.8. 
Região Nordeste: 1.5. Região Centro-Oeste: 1.4."
```

---

## Teste 1 — "Qual o prazo de devolução para carga perigosa?"

**Resposta obtida do Claude com prompt v1:**

> "Carga perigosa não é elegível para devolução pelo processo padrão.
> Conforme POL-001, seção 3.2, cargas classificadas como perigosas (classes 1 a 6 da ANTT) estão entre as exceções que não podem ser devolvidas pelo procedimento padrão.
> O cliente deve entrar em contato com o setor de Gestão de Riscos para tratamento individual."

**Análise:**
- ✅ Resposta correta: identificou que carga perigosa é exceção, não elegível para devolução
- ✅ Citou a fonte (POL-001, seção 3.2)
- ✅ Respeitou guardrails (não inventou prazo, não disse que "pode em 7 dias")
- ✅ Português formal
- ⚠️ Mencionou "Gestão de Riscos" mas o chunk A não contém essa informação diretamente — o chunk A do exercício é uma versão resumida que omite esse detalhe. Na base real, o chunk completo conteria o ramal 4500. **Isso é uma falha do chunk simulado, não do prompt.**

**Resultado: APROVADO** ✅

---

## Teste 2 — "Meu cliente é Gold, qual o SLA de resolução?"

**Resposta obtida:**

> "Para clientes Gold, o SLA de resolução é de até 24 horas úteis para chamados gerais.
> Conforme SLA-2024: Cliente Gold tem tempo de resolução de até 24h úteis.
> Observação: para incidentes críticos, os prazos são diferentes — mas essa informação não está no trecho disponível. Caso o chamado seja crítico, recomendo verificar a tabela SLA-2024 completa."

**Análise:**
- ✅ Resposta correta (24h para Gold)
- ✅ Citou fonte (SLA-2024)
- ✅ Honesto sobre limitação dos chunks disponíveis (não inventou SLA de incidente crítico)
- ✅ Orientou atendente a verificar tabela completa
- ✅ Respeitou todos os guardrails

**Resultado: APROVADO** ✅

---

## Teste 3 — "Quanto custa o frete para 600kg para Manaus?"

**Resposta obtida:**

> "Para um frete de 600kg com destino a Manaus (região Norte), o multiplicador regional é 1.8.
> Conforme PROC-042-v2, seção 2: para cargas acima de 500kg, o frete especial é calculado como Valor base × Multiplicador regional × Fator de peso.
> Para 600kg, o fator de peso é 1.0 (faixa de 500 a 1.000kg). Multiplicador da região Norte: 1.8.
> Portanto: Frete = Valor base × 1.8 × 1.0 = Valor base × 1.8.
> O valor base está na tabela mensal de fretes — não tenho acesso a esse valor no contexto atual."

**Análise:**
- ✅ Multiplicador correto da v2 (1.8 para Norte)
- ✅ Fator de peso correto (1.0 para 500-1.000kg)
- ✅ Fórmula correta
- ✅ Não inventou o valor base (reconheceu limitação)
- ✅ Citou fonte (PROC-042-v2, seção 2)
- ⚠️ **Problema identificado:** O modelo não mencionou que existe uma PROC-042 v1 com multiplicadores diferentes. Na base real, o pipeline pode retornar chunks de ambas as versões, e o prompt v1 não especifica com suficiente clareza como agir quando ambas aparecem juntas. A Regra 5 existe, mas o teste não ativou esse cenário porque só o chunk da v2 foi fornecido.

**Resultado: APROVADO (teste limitado — problema potencial identificado)** ⚠️

---

## Problemas identificados no v1 — motivando a iteração para v2

1. **Regra 5 (conflito de versões) está no prompt mas não é suficientemente diretiva:** Diz "sinalize o conflito" mas não define como. O atendente pode não saber o que fazer com dois valores diferentes. Melhoria: adicionar instrução para sempre usar a versão mais recente como padrão, mas informar a existência da versão anterior.

2. **Formato de resposta não define estrutura para perguntas de cálculo:** Quando a pergunta envolve fórmula (como o teste 3), o modelo respondeu bem, mas o formato poderia ser mais explícito sobre mostrar os passos do cálculo separadamente do resultado.

3. **Ausência de instrução sobre o FAQ como fonte de menor confiabilidade na resposta ao atendente:** O prompt instrui o modelo sobre hierarquia de fontes internamente, mas não o instrui a comunicar explicitamente ao atendente quando a resposta vem do FAQ (não de um documento normativo).
