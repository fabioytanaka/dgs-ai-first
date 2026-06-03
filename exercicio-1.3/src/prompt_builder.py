"""
prompt_builder.py — Montagem do Prompt Final para o LLM
NovaTech — Assistente de Atendimento IA

Desenvolvido com suporte do GitHub Copilot.

Recebe os chunks recuperados + pergunta e monta o prompt completo
(system prompt + chunks + pergunta) pronto para envio ao LLM.

Implementa o orçamento de contexto definido na análise do exercício 1.1:
- System prompt estático: ~890 tokens
- Metadados do cliente: ~80 tokens  
- Chunks: até 8 × ~500 tokens = ~4.000 tokens
- Pergunta: ~50 tokens
- Total por query: ~5.020 tokens (bem dentro do limite de 128K do GPT-4o)
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

# System prompt v2 (conforme exercício 1.2)
SYSTEM_PROMPT_TEMPLATE = """# IDENTIDADE

Você é o Assistente de Atendimento da NovaTech, uma empresa de logística brasileira.
Seu papel é ajudar os atendentes da NovaTech a encontrar informações corretas sobre
procedimentos, políticas de devolução, regras de frete e SLAs de clientes.

Você não atende clientes diretamente — você apoia os atendentes internos da NovaTech.

# REGRAS E GUARDRAILS

## Regra 1 — Sempre citar a fonte
Toda informação fornecida DEVE indicar a fonte: nome do documento, versão e seção.
Exemplo correto: "Conforme POL-001, seção 3.1 (versão 3.1, jan/2024)..."
Nunca responda sem indicar de onde veio a informação.

## Regra 2 — Nunca inventar prazos ou valores
Se uma informação numérica (prazo em dias, valor em reais, multiplicador de frete,
percentual de SLA) não estiver explicitamente nos documentos fornecidos, NÃO a infira.
Diga explicitamente que a informação não foi encontrada.

## Regra 3 — Quando não encontrar resposta
Se os documentos fornecidos não contiverem a resposta, responda exatamente:
"Não encontrei esta informação na documentação disponível. Recomendo escalar para
o supervisor ou consultar diretamente o setor responsável."
Nunca tente "completar" a resposta com conhecimento geral.

## Regra 4 — Idioma e tom
Responda sempre em português formal, mas acessível. Evite jargão técnico.

## Regra 5 — Conflito entre versões de documentos
Se os chunks contiverem informações de versões diferentes do mesmo documento:
a) Sinalize o conflito explicitamente no início da resposta.
b) Apresente as duas versões com nome, número de versão e data de cada uma.
c) Use como padrão a versão com data mais recente.
d) Oriente o atendente sobre chamados anteriores à data de vigência.
Nunca misture valores de versões diferentes sem avisar.

## Regra 6 — Comunicar confiabilidade da fonte
Quando a resposta vier do FAQ-Atendimento (documento informal), informe ao atendente:
"⚠️ Esta informação vem do FAQ interno, que não foi validado formalmente.
Confirme na documentação normativa antes de comunicar ao cliente."

# INSTRUÇÕES PARA USO DOS CHUNKS

Use APENAS as informações contidas nos chunks abaixo para responder.

Prioridade de fontes:
1. SLA-2024 (documento contratual) — máxima confiabilidade
2. POL-xxx e PROC-xxx (documentos normativos) — alta confiabilidade  
3. FAQ-Atendimento — menor confiabilidade; use com aviso explícito (Regra 6)

# FORMATO DE RESPOSTA

Para perguntas de política ou prazo:
1. Resposta direta (1-2 frases com o resultado)
2. Base documental (citação de fonte com seção e versão)
3. Exceções relevantes (se existirem)
4. Ação recomendada ao atendente

Para perguntas de cálculo (frete, custos):
1. Fórmula utilizada
2. Valores identificados nos documentos para cada variável
3. Resultado calculado (ou motivo pelo qual não é possível calcular)
4. Fonte (documento, versão, seção)
5. Alertas de versão se aplicável

Para perguntas sem resposta nos documentos: aplique a Regra 3.
"""


class PromptBuilder:
    """
    Monta o prompt completo para o LLM.
    
    Responsabilidades:
    - Formatar chunks recuperados em bloco de contexto legível
    - Inserir metadados do cliente (tier, etc.)
    - Controlar orçamento de tokens (truncar histórico se necessário)
    - Detectar potenciais conflitos de versão entre os chunks
    
    # Copilot ajudou a gerar a detecção de conflito de versões por metadata
    """

    def __init__(self, system_prompt: str = SYSTEM_PROMPT_TEMPLATE):
        self.system_prompt = system_prompt

    def _format_chunk(self, chunk: Dict[str, Any], rank: int) -> str:
        """Formata um único chunk para inclusão no contexto."""
        meta = chunk["metadata"]
        source = meta.get("source", "Desconhecido")
        section = meta.get("section", "")
        versao = meta.get("versao", "")
        data = meta.get("data_atualizacao", "")
        score = chunk.get("score", 0)
        
        header = f"--- DOCUMENTO {rank}: {source}"
        if versao:
            header += f" (v{versao}"
            if data:
                header += f", {data}"
            header += ")"
        if section:
            header += f" — {section}"
        header += f" [relevância: {score:.2f}] ---"
        
        return f"{header}\n{chunk['text']}\n"

    def _detect_version_conflicts(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """
        Detecta chunks de versões diferentes do mesmo documento base.
        Ex: PROC-042-frete-especial-v1 e PROC-042-v2-frete-especial-revisado
        retornam no mesmo resultado → conflito potencial.
        
        # Copilot sugeriu a comparação por prefixo normalizado do source
        """
        conflicts = []
        sources_seen = {}
        
        for chunk in chunks:
            source = chunk["metadata"].get("source", "")
            # Normaliza o nome: remove versão para agrupar documentos relacionados
            base_name = source.replace("-v2-", "-").replace("-v1", "").replace("-revisado", "")
            
            if base_name in sources_seen and sources_seen[base_name] != source:
                conflict_pair = f"{sources_seen[base_name]} vs {source}"
                if conflict_pair not in conflicts:
                    conflicts.append(conflict_pair)
            else:
                sources_seen[base_name] = source
        
        return conflicts

    def build(
        self,
        question: str,
        chunks: List[Dict[str, Any]],
        client_tier: Optional[str] = None,
        ticket_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Monta o prompt completo.
        
        Returns:
            Dict com:
            - 'system': o system prompt estático
            - 'context_block': o bloco de contexto dinâmico
            - 'full_prompt': prompt completo para colar no Claude (chat)
            - 'metadata': informações sobre o prompt montado
        """
        # Bloco de metadados do atendimento
        context_parts = []
        
        if client_tier or ticket_id:
            atendimento_block = "[CONTEXTO DO ATENDIMENTO]\n"
            if client_tier:
                atendimento_block += f"Tier do cliente: {client_tier}\n"
            if ticket_id:
                atendimento_block += f"Número do chamado: {ticket_id}\n"
            context_parts.append(atendimento_block)
        
        # Detectar conflitos de versão antes de montar
        conflicts = self._detect_version_conflicts(chunks)
        if conflicts:
            conflict_warning = (
                "⚠️ ALERTA DO PIPELINE: Os chunks recuperados contêm versões "
                f"potencialmente conflitantes: {'; '.join(conflicts)}. "
                "Aplique a Regra 5 ao responder.\n"
            )
            context_parts.append(conflict_warning)
        
        # Bloco de documentação recuperada
        if chunks:
            docs_block = "[DOCUMENTAÇÃO RECUPERADA]\n"
            for i, chunk in enumerate(chunks, 1):
                docs_block += self._format_chunk(chunk, i) + "\n"
            context_parts.append(docs_block)
        else:
            context_parts.append(
                "[DOCUMENTAÇÃO RECUPERADA]\nNenhum documento relevante encontrado.\n"
            )
        
        # Histórico de conversa (limitado para evitar context rot)
        if conversation_history:
            # Mantém apenas as últimas 3 trocas para controlar crescimento do contexto
            recent_history = conversation_history[-6:]  # 3 pares user/assistant
            history_block = "[HISTÓRICO DA CONVERSA]\n"
            for msg in recent_history:
                role = "Atendente" if msg["role"] == "user" else "Assistente"
                history_block += f"{role}: {msg['content']}\n\n"
            context_parts.append(history_block)
        
        # Pergunta atual
        context_parts.append(f"[PERGUNTA DO ATENDENTE]\n{question}")
        
        context_block = "\n".join(context_parts)
        
        # Prompt completo (formato para uso manual no Claude chat)
        full_prompt = f"{self.system_prompt}\n\n{'='*60}\n\n{context_block}"
        
        # Estimativa de tokens (aproximação: 0.75 palavras/token)
        estimated_tokens = len(full_prompt.split()) / 0.75
        
        return {
            "system": self.system_prompt,
            "context_block": context_block,
            "full_prompt": full_prompt,
            "metadata": {
                "n_chunks": len(chunks),
                "version_conflicts_detected": conflicts,
                "estimated_tokens": int(estimated_tokens),
                "history_turns": len(conversation_history) if conversation_history else 0
            }
        }

    def print_prompt_summary(self, prompt_result: Dict[str, Any]) -> None:
        """Imprime resumo do prompt para debug."""
        meta = prompt_result["metadata"]
        print(f"\n📋 Prompt montado:")
        print(f"   Chunks: {meta['n_chunks']}")
        print(f"   Tokens estimados: ~{meta['estimated_tokens']}")
        print(f"   Turnos no histórico: {meta['history_turns']}")
        if meta["version_conflicts_detected"]:
            print(f"   ⚠️  Conflitos de versão detectados: {meta['version_conflicts_detected']}")


def build_prompt(
    question: str,
    chunks: List[Dict[str, Any]],
    client_tier: Optional[str] = None,
    ticket_id: Optional[str] = None
) -> str:
    """Função de conveniência para montar prompt rapidamente."""
    builder = PromptBuilder()
    result = builder.build(question, chunks, client_tier, ticket_id)
    return result["full_prompt"]
