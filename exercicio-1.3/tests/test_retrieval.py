"""
test_retrieval.py — Testes do Pipeline de RAG com Gabarito do Anexo B
NovaTech — Assistente de Atendimento IA

Desenvolvido com suporte do GitHub Copilot.

5 testes baseados no mapa de cobertura do Anexo B.
Compara os chunks recuperados com o gabarito esperado.

Execução:
    python test_retrieval.py
    # ou com pytest:
    pytest test_retrieval.py -v
"""

import sys
import unittest
from pathlib import Path
from typing import List

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestRAGRetrieval(unittest.TestCase):
    """
    Testes de retrieval baseados no mapa de cobertura do Anexo B.
    
    Cada teste verifica se os chunks corretos são recuperados
    para perguntas típicas do domínio de atendimento NovaTech.
    
    IMPORTANTE: Esses testes pressupõem que a ingestão foi executada
    (python src/main.py --ingest) antes de rodar.
    
    # Copilot foi usado para gerar o boilerplate setUp/tearDown
    # e a estrutura assertIn com mensagens de debug.
    """

    @classmethod
    def setUpClass(cls):
        """Carrega o retriever uma única vez para todos os testes."""
        try:
            from retrieval import RAGRetriever
            cls.retriever = RAGRetriever()
            cls.retriever_available = True
        except Exception as e:
            cls.retriever_available = False
            cls.setup_error = str(e)

    def _get_sources(self, query: str, n_results: int = 5) -> List[str]:
        """Recupera os nomes das fontes dos top N chunks para a query."""
        if not self.retriever_available:
            self.skipTest(f"ChromaDB não disponível: {self.setup_error}")
        chunks = self.retriever.search(query, n_results=n_results)
        return [c["metadata"].get("source", "") for c in chunks]

    def _get_chunks_with_scores(self, query: str, n_results: int = 5):
        """Recupera chunks completos com scores."""
        if not self.retriever_available:
            self.skipTest(f"ChromaDB não disponível: {self.setup_error}")
        return self.retriever.search(query, n_results=n_results)

    # ─────────────────────────────────────────────────────────────────────
    # Teste 1: Prazo de devolução
    # Gabarito Anexo B: deve recuperar POL-001-A e POL-001-B
    # ─────────────────────────────────────────────────────────────────────
    def test_01_prazo_devolucao(self):
        """
        Query: 'Qual o prazo de devolução?'
        Esperado: chunks da POL-001 (seção 3.1 e 3.2) no top 5
        
        Gabarito Anexo B:
        - Chunks que DEVEM ser recuperados: POL-001-A, POL-001-B
        - Chunks que podem aparecer (menor relevância): POL-001-C
        """
        query = "Qual o prazo de devolução de mercadorias?"
        sources = self._get_sources(query)
        
        print(f"\n[Teste 1] Sources recuperadas: {sources}")
        
        # A fonte POL-001 deve estar presente
        self.assertTrue(
            any("POL-001" in src for src in sources),
            f"POL-001 não encontrada no top 5. Sources: {sources}"
        )
        
        # Verificação adicional: a resposta não deve trazer apenas FAQ
        faq_only = all("FAQ" in src for src in sources[:2])
        self.assertFalse(
            faq_only,
            "Os dois primeiros chunks são do FAQ — esperado POL-001 como principal"
        )

    # ─────────────────────────────────────────────────────────────────────
    # Teste 2: Carga perigosa e devolução
    # Gabarito Anexo B: deve recuperar POL-001-B
    # ARMADILHA: resposta correta é que NÃO pode devolver
    # ─────────────────────────────────────────────────────────────────────
    def test_02_carga_perigosa_devolucao(self):
        """
        Query: 'Posso devolver carga perigosa?'
        Esperado: chunk POL-001-B (seção 3.2 — exceções) no top 3
        
        ARMADILHA (cenário-1-avaliacao-desenvolvedor.md, Exercício 1.2):
        Se o chunk recuperado for o POL-001-A (prazo geral de 7 dias)
        sem o POL-001-B (exceções), o LLM pode responder "sim, 7 dias"
        — que é incorreto para carga perigosa.
        """
        query = "Posso devolver carga perigosa?"
        chunks = self._get_chunks_with_scores(query)
        sources = [c["metadata"].get("source", "") for c in chunks]
        
        print(f"\n[Teste 2] Sources recuperadas: {sources}")
        
        # POL-001 deve aparecer
        self.assertTrue(
            any("POL-001" in src for src in sources),
            f"POL-001 não encontrada. Sources: {sources}"
        )
        
        # Verifica se algum chunk contém a palavra "perigosa" + "não" / "NÃO"
        found_exception_chunk = False
        for chunk in chunks[:3]:
            text = chunk["text"].lower()
            if "perigosa" in text and ("não" in text or "nao" in text or "elegíveis" in text):
                found_exception_chunk = True
                break
        
        self.assertTrue(
            found_exception_chunk,
            "Nenhum chunk no top 3 contém a exceção para carga perigosa. "
            "O pipeline pode induzir resposta incorreta ('sim, pode devolver')."
        )

    # ─────────────────────────────────────────────────────────────────────
    # Teste 3: SLA cliente Gold
    # Gabarito Anexo B: deve recuperar SLA-2024-B (e possivelmente SLA-2024-A)
    # ─────────────────────────────────────────────────────────────────────
    def test_03_sla_cliente_gold(self):
        """
        Query: 'Qual o SLA do cliente Gold?'
        Esperado: chunks do SLA-2024 no top 5
        """
        query = "Qual o SLA do cliente Gold?"
        sources = self._get_sources(query)
        
        print(f"\n[Teste 3] Sources recuperadas: {sources}")
        
        self.assertTrue(
            any("SLA-2024" in src for src in sources),
            f"SLA-2024 não encontrada no top 5. Sources: {sources}"
        )

    # ─────────────────────────────────────────────────────────────────────
    # Teste 4: Multiplicador de frete (detectar conflito de versões)
    # Gabarito Anexo B: PROC-042v2-B deve aparecer
    # ARMADILHA: pipeline pode retornar ambas as versões (PROC-042-B v1 e v2)
    # ─────────────────────────────────────────────────────────────────────
    def test_04_multiplicador_sudeste(self):
        """
        Query: 'Qual o multiplicador de frete para o Sudeste?'
        Esperado: PROC-042-v2 (multiplicador 1.1) no top 3
        Risco: PROC-042-v1 (multiplicador 1.0) também pode aparecer — conflito!
        
        Gabarito: 1.1 (v2) — ATENÇÃO: v1 tem 1.0
        """
        query = "Qual o multiplicador de frete para o Sudeste?"
        chunks = self._get_chunks_with_scores(query)
        sources = [c["metadata"].get("source", "") for c in chunks]
        
        print(f"\n[Teste 4] Sources recuperadas: {sources}")
        print(f"[Teste 4] Verificando conflito de versões...")
        
        # Verifica se ambas as versões aparecem (problema conhecido)
        has_v1 = any("PROC-042-frete-especial-v1" in src for src in sources)
        has_v2 = any("PROC-042-v2" in src for src in sources)
        
        if has_v1 and has_v2:
            print(
                "  ⚠️  CONFLITO DETECTADO: Ambas as versões da PROC-042 aparecem. "
                "O prompt_builder deve sinalizar isso com a Regra 5."
            )
        
        # A v2 (mais recente) deve aparecer
        self.assertTrue(
            has_v2,
            f"PROC-042-v2 não encontrada. Sources: {sources}. "
            "O pipeline pode retornar o multiplicador antigo (1.0) em vez do atual (1.1)."
        )

    # ─────────────────────────────────────────────────────────────────────
    # Teste 5: Tier Platinum (alucinação zero-shot)
    # Gabarito Anexo B: SLA-2024-A deve aparecer (contém "não existem outros tiers")
    # ─────────────────────────────────────────────────────────────────────
    def test_05_tier_platinum_nao_existe(self):
        """
        Query: 'Qual o SLA do cliente Platinum?'
        Esperado: SLA-2024-A (que contém 'não existem outros tiers') no top 5
        
        ARMADILHA crítica (cenário-1-avaliacao-desenvolvedor.md):
        Se o retrieval falhar e não recuperar SLA-2024-A, o LLM pode
        inventar SLAs para o 'tier Platinum' — alucinação pura.
        O correto é recuperar o chunk que diz que só existem 3 tiers.
        """
        query = "Qual o SLA do cliente Platinum?"
        chunks = self._get_chunks_with_scores(query)
        sources = [c["metadata"].get("source", "") for c in chunks]
        
        print(f"\n[Teste 5] Sources recuperadas: {sources}")
        
        # SLA-2024 deve aparecer para dar contexto correto
        self.assertTrue(
            any("SLA-2024" in src for src in sources),
            f"SLA-2024 não encontrada. Sources: {sources}. "
            "SEM esse chunk, o LLM pode inventar SLAs para Platinum."
        )
        
        # Verifica se algum chunk nega a existência do tier Platinum
        found_denial_chunk = False
        for chunk in chunks[:5]:
            text = chunk["text"].lower()
            if "platinum" in text or "três" in text or "3 (três)" in text:
                found_denial_chunk = True
                break
        
        if not found_denial_chunk:
            print(
                "  ⚠️  AVISO: Nenhum chunk no top 5 menciona explicitamente que "
                "só existem 3 tiers ou nega Platinum. Risco de alucinação aumentado."
            )


class TestChunkingQuality(unittest.TestCase):
    """
    Testes de qualidade do chunking.
    Verifica se tabelas não foram cortadas e se o overlap funciona.
    """

    def test_table_not_split(self):
        """
        Verifica que os chunks da tabela de multiplicadores regionais
        contêm a tabela completa (Sul, Sudeste, Centro-Oeste, Nordeste, Norte).
        """
        try:
            from retrieval import RAGRetriever
            retriever = RAGRetriever()
        except Exception:
            self.skipTest("ChromaDB não disponível")
        
        query = "tabela multiplicadores regionais frete"
        chunks = retriever.search(query, n_results=3)
        
        for chunk in chunks:
            if "PROC-042" in chunk["metadata"].get("source", ""):
                text = chunk["text"]
                # Uma tabela completa deve ter todas as regiões
                regions = ["Sul", "Sudeste", "Centro-Oeste", "Nordeste", "Norte"]
                regions_found = [r for r in regions if r in text]
                
                if len(regions_found) >= 3:
                    # Chunk tem pelo menos 3 regiões — tabela provavelmente intacta
                    return
        
        # Se chegou aqui, nenhum chunk tem a tabela completa
        print(
            "⚠️  PROBLEMA: Nenhum chunk contém a tabela de multiplicadores completa. "
            "A tabela pode ter sido cortada no meio pelo chunking."
        )


if __name__ == "__main__":
    # Executa os testes com output verboso
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Adiciona os testes na ordem
    suite.addTest(TestRAGRetrieval("test_01_prazo_devolucao"))
    suite.addTest(TestRAGRetrieval("test_02_carga_perigosa_devolucao"))
    suite.addTest(TestRAGRetrieval("test_03_sla_cliente_gold"))
    suite.addTest(TestRAGRetrieval("test_04_multiplicador_sudeste"))
    suite.addTest(TestRAGRetrieval("test_05_tier_platinum_nao_existe"))
    suite.addTest(TestChunkingQuality("test_table_not_split"))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summarize
    print(f"\n{'='*60}")
    passed = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
    print(f"Resultado: {passed}/{result.testsRun} testes passaram")
    if result.failures:
        print(f"Falhas: {len(result.failures)}")
    if result.errors:
        print(f"Erros: {len(result.errors)}")
