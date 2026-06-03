"""
retrieval.py — Busca por similaridade semântica no ChromaDB
NovaTech — Assistente de Atendimento IA

Desenvolvido com suporte do GitHub Copilot.

Recebe uma pergunta em linguagem natural, gera o embedding,
busca os N chunks mais similares, e retorna com score de similaridade.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = Path(__file__).parent.parent / ".chroma"
COLLECTION_NAME = "novatech_docs"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Número padrão de chunks a recuperar
# Justificativa: 8 chunks × ~500 palavras = ~4.000 tokens para contexto de documentação.
# Abaixo do "sweet spot" de lost in the middle (>10 chunks degrada atenção do modelo).
# Suficiente para perguntas multi-domínio (frete + devolução + SLA em uma query).
DEFAULT_N_RESULTS = 8


class RAGRetriever:
    """
    Busca semântica no índice vetorial do ChromaDB.
    
    # Copilot foi usado para gerar a lógica de filtragem por metadata
    # e o cálculo de score normalizado.
    """

    def __init__(self):
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        self.client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        self.collection = self.client.get_collection(name=COLLECTION_NAME)

    def search(
        self,
        query: str,
        n_results: int = DEFAULT_N_RESULTS,
        source_filter: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Busca os N chunks mais similares à query.
        
        Args:
            query: Pergunta em linguagem natural
            n_results: Número de chunks a recuperar
            source_filter: Filtrar por fonte específica (ex: "POL-001-politica-devolucao")
            min_score: Score mínimo de similaridade (0.0 a 1.0)
        
        Returns:
            Lista de chunks com texto, metadados e score de similaridade
        """
        # Gera embedding da query
        query_embedding = self.embedder.encode([query])[0].tolist()
        
        # Monta filtro de metadata se fornecido
        where = None
        if source_filter:
            where = {"source": {"$eq": source_filter}}
        
        # Busca no ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, self.collection.count()),
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # Formata resultado
        chunks = []
        for i in range(len(results["documents"][0])):
            # ChromaDB retorna distância coseno (0 = idêntico, 2 = oposto)
            # Convertemos para score de similaridade (1 = idêntico, 0 = sem relação)
            distance = results["distances"][0][i]
            similarity_score = 1 - (distance / 2)  # normalização para [0, 1]
            
            if similarity_score < min_score:
                continue
            
            chunks.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": round(similarity_score, 4),
                "rank": i + 1
            })
        
        return chunks

    def search_multi_query(
        self,
        queries: List[str],
        n_results_per_query: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Busca com múltiplas queries (útil para perguntas multi-domínio).
        Remove duplicatas, ordena por maior score.
        
        Exemplo de uso: uma pergunta sobre "custo do frete de carga perigosa que
        precisa ser devolvida" se beneficia de queries separadas:
        - "carga perigosa devolução"
        - "frete especial carga perigosa"
        
        # Copilot sugeriu a deduplicação por chunk_hash nos metadados
        """
        all_chunks = []
        seen_hashes = set()
        
        for query in queries:
            results = self.search(query, n_results=n_results_per_query)
            for chunk in results:
                chunk_hash = chunk["metadata"].get("chunk_hash", chunk["text"][:50])
                if chunk_hash not in seen_hashes:
                    seen_hashes.add(chunk_hash)
                    all_chunks.append(chunk)
        
        # Ordena por score decrescente e retorna top N
        all_chunks.sort(key=lambda x: x["score"], reverse=True)
        return all_chunks[:DEFAULT_N_RESULTS]

    def format_for_display(self, chunks: List[Dict[str, Any]]) -> str:
        """Formata chunks para exibição em logs/debug."""
        lines = []
        for chunk in chunks:
            meta = chunk["metadata"]
            lines.append(
                f"[Rank {chunk['rank']} | Score: {chunk['score']:.4f}] "
                f"{meta.get('source', 'N/A')} — {meta.get('section', 'N/A')} "
                f"(v{meta.get('versao', '?')})"
            )
        return '\n'.join(lines)


def search_documents(
    query: str,
    n_results: int = DEFAULT_N_RESULTS,
    verbose: bool = False
) -> List[Dict[str, Any]]:
    """
    Função de conveniência para busca rápida sem instanciar a classe.
    Usada nos testes automatizados.
    """
    retriever = RAGRetriever()
    results = retriever.search(query, n_results=n_results)
    
    if verbose:
        print(f"\n🔍 Query: {query!r}")
        print(f"📄 {len(results)} chunks recuperados:")
        print(retriever.format_for_display(results))
    
    return results


if __name__ == "__main__":
    # Teste rápido de sanidade
    test_queries = [
        "prazo de devolução de mercadorias",
        "carga perigosa devolução elegível",
        "SLA cliente Gold resolução",
        "multiplicador frete região Norte",
        "tier Platinum existe NovaTech"
    ]
    
    retriever = RAGRetriever()
    
    for query in test_queries:
        print(f"\n{'='*60}")
        results = retriever.search(query, n_results=3)
        print(f"Query: {query!r}")
        print(retriever.format_for_display(results))
