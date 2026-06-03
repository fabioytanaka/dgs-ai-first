"""
main.py — Orquestrador do Pipeline de RAG
NovaTech — Assistente de Atendimento IA

Desenvolvido com suporte do GitHub Copilot.

Pipeline end-to-end:
1. Ingestão dos documentos (se necessário)
2. Busca por similaridade semântica
3. Montagem do prompt completo
4. [Para testes manuais] Exibe prompt para colar no Claude

Uso:
    python main.py --ingest          # Ingere todos os documentos
    python main.py --query "..."     # Faz uma busca e monta o prompt
    python main.py --test            # Executa 5 queries de teste do Anexo B
"""

import argparse
import sys
from pathlib import Path

# Adiciona o diretório src ao path para imports relativos
sys.path.insert(0, str(Path(__file__).parent))

from ingest import RAGIngestor, DOCS_DIR
from retrieval import RAGRetriever, DEFAULT_N_RESULTS
from prompt_builder import PromptBuilder


# 5 queries de teste baseadas no mapa de cobertura do Anexo B
TEST_QUERIES = [
    {
        "query": "Qual o prazo de devolução de mercadorias?",
        "expected_sources": ["POL-001-politica-devolucao"],
        "expected_chunks": ["POL-001-A", "POL-001-B"],
        "gabarito": "7 dias úteis (seção 3.1), com exceções para cargas perigosas (seção 3.2)"
    },
    {
        "query": "Posso devolver carga perigosa?",
        "expected_sources": ["POL-001-politica-devolucao"],
        "expected_chunks": ["POL-001-B"],
        "gabarito": "NÃO — cargas perigosas classes 1 a 6 ANTT não são elegíveis (seção 3.2)"
    },
    {
        "query": "Qual o SLA do cliente Gold?",
        "expected_sources": ["SLA-2024-tabela-sla-clientes"],
        "expected_chunks": ["SLA-2024-B"],
        "gabarito": "Resposta em até 2h úteis, resolução em até 24h úteis (chamados gerais)"
    },
    {
        "query": "Qual o multiplicador de frete para a região Sudeste?",
        "expected_sources": ["PROC-042-v2-frete-especial-revisado"],
        "expected_chunks": ["PROC-042v2-B"],
        "gabarito": "1.1 (v2/nov2023) — ATENÇÃO: v1 tem 1.0, possível conflito de versão"
    },
    {
        "query": "Existe tier Platinum na NovaTech?",
        "expected_sources": ["SLA-2024-tabela-sla-clientes"],
        "expected_chunks": ["SLA-2024-A"],
        "gabarito": "NÃO existe — apenas Gold, Silver e Standard (seção 1)"
    }
]


class RAGPipeline:
    """Pipeline completo de RAG: retrieval + prompt building."""

    def __init__(self):
        self.retriever = RAGRetriever()
        self.builder = PromptBuilder()

    def run_query(
        self,
        question: str,
        n_results: int = DEFAULT_N_RESULTS,
        client_tier: str = None,
        ticket_id: str = None,
        verbose: bool = True
    ) -> dict:
        """Executa uma query completa: busca → monta prompt → retorna resultado."""
        
        if verbose:
            print(f"\n{'='*70}")
            print(f"🔍 Pergunta: {question!r}")
            print(f"{'='*70}")
        
        # 1. Retrieval
        chunks = self.retriever.search(question, n_results=n_results)
        
        if verbose:
            print(f"\n📄 {len(chunks)} chunks recuperados:")
            print(self.retriever.format_for_display(chunks))
        
        # 2. Monta prompt
        prompt_result = self.builder.build(
            question=question,
            chunks=chunks,
            client_tier=client_tier,
            ticket_id=ticket_id
        )
        
        if verbose:
            self.builder.print_prompt_summary(prompt_result)
        
        return {
            "question": question,
            "chunks": chunks,
            "prompt": prompt_result
        }

    def run_tests(self) -> list:
        """
        Executa os 5 testes do mapa de cobertura do Anexo B.
        Compara chunks recuperados com gabarito esperado.
        """
        print("\n" + "="*70)
        print("🧪 EXECUTANDO 5 TESTES COM GABARITO DO ANEXO B")
        print("="*70)
        
        results = []
        
        for i, test in enumerate(TEST_QUERIES, 1):
            print(f"\n{'─'*70}")
            print(f"TESTE {i}: {test['query']}")
            print(f"{'─'*70}")
            
            # Executa a busca
            chunks = self.retriever.search(test["query"], n_results=5)
            
            # Verifica se as fontes esperadas aparecem
            retrieved_sources = [c["metadata"].get("source", "") for c in chunks]
            
            found_expected = []
            for expected_source in test["expected_sources"]:
                if any(expected_source in src for src in retrieved_sources):
                    found_expected.append(expected_source)
            
            coverage = len(found_expected) / len(test["expected_sources"])
            status = "✅" if coverage >= 0.5 else "❌"
            
            print(f"\nFontes esperadas: {test['expected_sources']}")
            print(f"Fontes recuperadas: {retrieved_sources[:3]}")
            print(f"Cobertura: {coverage:.0%} {status}")
            print(f"\nGabarito: {test['gabarito']}")
            
            print("\nTop 3 chunks recuperados:")
            for j, chunk in enumerate(chunks[:3], 1):
                meta = chunk["metadata"]
                print(
                    f"  [{j}] Score: {chunk['score']:.4f} | "
                    f"{meta.get('source')} — {meta.get('section', '')[:50]}"
                )
            
            results.append({
                "test_num": i,
                "query": test["query"],
                "expected": test["expected_sources"],
                "retrieved": retrieved_sources[:3],
                "coverage": coverage,
                "passed": coverage >= 0.5
            })
        
        # Resumo
        passed = sum(1 for r in results if r["passed"])
        print(f"\n{'='*70}")
        print(f"📊 RESULTADO FINAL: {passed}/{len(results)} testes passaram")
        print("="*70)
        
        return results


def main():
    parser = argparse.ArgumentParser(description="Pipeline de RAG — NovaTech")
    parser.add_argument("--ingest", action="store_true", help="Ingere documentos")
    parser.add_argument("--query", type=str, help="Faz uma busca")
    parser.add_argument("--test", action="store_true", help="Executa 5 testes do Anexo B")
    parser.add_argument("--n", type=int, default=DEFAULT_N_RESULTS, help="Número de chunks")
    parser.add_argument("--tier", type=str, default=None, help="Tier do cliente (Gold/Silver/Standard)")
    
    args = parser.parse_args()
    
    if args.ingest:
        print("📥 Iniciando ingestão...")
        from ingest import main as ingest_main
        ingest_main()
        return
    
    if args.test:
        pipeline = RAGPipeline()
        pipeline.run_tests()
        return
    
    if args.query:
        pipeline = RAGPipeline()
        result = pipeline.run_query(
            question=args.query,
            n_results=args.n,
            client_tier=args.tier,
            verbose=True
        )
        
        print("\n" + "="*70)
        print("📝 PROMPT MONTADO (cole no Claude para obter a resposta):")
        print("="*70)
        print(result["prompt"]["full_prompt"])
        return
    
    # Sem argumentos: modo interativo
    print("🤖 Pipeline de RAG — NovaTech")
    print("Digite 'sair' para encerrar.\n")
    
    pipeline = RAGPipeline()
    
    while True:
        question = input("Pergunta: ").strip()
        if question.lower() in ["sair", "exit", "quit"]:
            break
        if not question:
            continue
        
        pipeline.run_query(question, verbose=True)


if __name__ == "__main__":
    main()
