"""
ingest.py — Pipeline de Ingestão de Documentos para RAG
NovaTech — Assistente de Atendimento IA

Desenvolvido com suporte do GitHub Copilot.
Stack: sentence-transformers + ChromaDB

Estratégia de chunking: por seção semântica (headings H2/H3),
não por token count fixo. Justificativa: documentos de política e
procedimento têm regras completas dentro de cada seção numerada.
Cortar por tokens fixos quebraria regras de negócio no meio,
gerando chunks sem contexto suficiente para o LLM.

Overhead de overlap (15%) preserva contexto de fronteira entre seções.
"""

import re
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any

import chromadb
from sentence_transformers import SentenceTransformer

# Configurações do pipeline
DOCS_DIR = Path(__file__).parent.parent / "docs" / "source"
CHROMA_PATH = Path(__file__).parent.parent / ".chroma"
COLLECTION_NAME = "novatech_docs"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Parâmetros de chunking
MAX_CHUNK_TOKENS = 600      # máximo por chunk (em palavras, aproximado)
OVERLAP_WORDS = 80          # overlap entre chunks de seções longas (~15% de 600)
MIN_CHUNK_WORDS = 30        # chunks menores que isso são descartados (cabeçalhos vazios)


class DocumentChunker:
    """
    Divide documentos Markdown em chunks por seção semântica.
    Tabelas são preservadas como chunks próprios, nunca cortadas.
    
    # Copilot foi usado para gerar a regex de detecção de headings
    # e a lógica de preservação de blocos de tabela.
    """

    def __init__(self):
        self.heading_pattern = re.compile(r'^#{1,4}\s+', re.MULTILINE)
        self.table_pattern = re.compile(r'(\|.+\|\n)+', re.MULTILINE)

    def _count_words(self, text: str) -> int:
        return len(text.split())

    def _extract_metadata_from_header(self, content: str) -> Dict[str, str]:
        """Extrai metadados do cabeçalho do documento Markdown."""
        metadata = {}
        lines = content.split('\n')[:20]  # Apenas as primeiras 20 linhas
        
        for line in lines:
            if '**Versão:**' in line or 'Versão:' in line:
                metadata['versao'] = line.split(':', 1)[-1].strip().strip('*').strip()
            if '**Última atualização:**' in line or 'Última atualização:' in line:
                metadata['data_atualizacao'] = line.split(':', 1)[-1].strip().strip('*').strip()
            if '**Responsável:**' in line or 'Responsável:' in line:
                metadata['responsavel'] = line.split(':', 1)[-1].strip().strip('*').strip()
        
        return metadata

    def _split_by_sections(self, content: str) -> List[Dict[str, str]]:
        """
        Divide o conteúdo por seções de heading (## ou ###).
        Cada seção = potencial chunk.
        """
        sections = []
        current_section = {"heading": "", "content": ""}
        
        lines = content.split('\n')
        for line in lines:
            if re.match(r'^#{1,4}\s+', line):
                # Salva a seção anterior se tiver conteúdo
                if current_section["content"].strip():
                    sections.append(current_section.copy())
                current_section = {"heading": line.strip(), "content": ""}
            else:
                current_section["content"] += line + '\n'
        
        # Última seção
        if current_section["content"].strip():
            sections.append(current_section)
        
        return sections

    def _protect_tables(self, text: str) -> List[Dict[str, str]]:
        """
        Identifica blocos de tabela no texto e os separa como chunks próprios.
        Tabelas NUNCA são cortadas no meio — regra crítica para dados de frete.
        
        # Copilot sugeriu a abordagem de split por regex de tabela
        """
        parts = []
        table_matches = list(self.table_pattern.finditer(text))
        
        if not table_matches:
            return [{"type": "text", "content": text}]
        
        last_end = 0
        for match in table_matches:
            # Texto antes da tabela
            before = text[last_end:match.start()].strip()
            if before:
                parts.append({"type": "text", "content": before})
            # A tabela em si
            parts.append({"type": "table", "content": match.group()})
            last_end = match.end()
        
        # Texto após a última tabela
        after = text[last_end:].strip()
        if after:
            parts.append({"type": "text", "content": after})
        
        return parts

    def chunk_document(self, content: str, source_name: str) -> List[Dict[str, Any]]:
        """
        Chunking principal: divide por seção semântica,
        protege tabelas, aplica overlap em seções longas.
        """
        chunks = []
        doc_metadata = self._extract_metadata_from_header(content)
        sections = self._split_by_sections(content)
        
        for section in sections:
            heading = section["heading"]
            section_content = section["content"]
            
            # Proteger tabelas dentro da seção
            parts = self._protect_tables(section_content)
            
            for part in parts:
                part_text = part["content"]
                word_count = self._count_words(part_text)
                
                # Descartar chunks muito pequenos (apenas cabeçalhos)
                if word_count < MIN_CHUNK_WORDS:
                    continue
                
                # Prefixo contextual: essencial para que o chunk faça sentido isolado
                # Sem isso, um chunk sobre "Prazo geral" sem saber que é da POL-001
                # perde completamente o contexto.
                prefix = f"[{source_name}] {heading}\n\n"
                chunk_text = prefix + part_text.strip()
                
                if word_count <= MAX_CHUNK_TOKENS or part["type"] == "table":
                    # Seção cabe em um chunk (ou é tabela — nunca dividir)
                    chunks.append({
                        "text": chunk_text,
                        "metadata": {
                            "source": source_name,
                            "section": heading,
                            "type": part["type"],
                            "word_count": word_count,
                            "versao": doc_metadata.get("versao", ""),
                            "data_atualizacao": doc_metadata.get("data_atualizacao", ""),
                            "chunk_hash": hashlib.md5(chunk_text.encode()).hexdigest()[:8]
                        }
                    })
                else:
                    # Seção longa: dividir com overlap
                    words = part_text.split()
                    start = 0
                    while start < len(words):
                        end = min(start + MAX_CHUNK_TOKENS, len(words))
                        sub_text = ' '.join(words[start:end])
                        chunk_text = prefix + sub_text
                        chunks.append({
                            "text": chunk_text,
                            "metadata": {
                                "source": source_name,
                                "section": f"{heading} (parte {start // MAX_CHUNK_TOKENS + 1})",
                                "type": "text",
                                "word_count": len(words[start:end]),
                                "versao": doc_metadata.get("versao", ""),
                                "data_atualizacao": doc_metadata.get("data_atualizacao", ""),
                                "chunk_hash": hashlib.md5(chunk_text.encode()).hexdigest()[:8]
                            }
                        })
                        start += MAX_CHUNK_TOKENS - OVERLAP_WORDS  # overlap de 15%
        
        return chunks


class RAGIngestor:
    """
    Orquestra a ingestão: lê arquivos → chunking → embedding → ChromaDB.
    """

    def __init__(self):
        print("Carregando modelo de embeddings...")
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        
        print(f"Conectando ao ChromaDB em {CHROMA_PATH}...")
        self.client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}  # distância coseno para similaridade semântica
        )
        
        self.chunker = DocumentChunker()

    def ingest_file(self, filepath: Path) -> int:
        """Ingere um único arquivo Markdown. Retorna número de chunks criados."""
        source_name = filepath.stem  # nome do arquivo sem extensão
        content = filepath.read_text(encoding="utf-8")
        
        chunks = self.chunker.chunk_document(content, source_name)
        
        if not chunks:
            print(f"  ⚠️  Nenhum chunk gerado para {source_name}")
            return 0
        
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        ids = [f"{source_name}_{i:04d}" for i in range(len(chunks))]
        
        print(f"  Gerando {len(texts)} embeddings para {source_name}...")
        embeddings = self.embedder.encode(texts, show_progress_bar=False).tolist()
        
        # Upsert: substitui se já existir (suporte a re-ingestão incremental)
        self.collection.upsert(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"  ✅ {len(chunks)} chunks indexados de {source_name}")
        return len(chunks)

    def ingest_directory(self, docs_dir: Path) -> Dict[str, int]:
        """Ingere todos os arquivos .md de um diretório."""
        results = {}
        md_files = list(docs_dir.glob("*.md"))
        
        if not md_files:
            print(f"⚠️  Nenhum arquivo .md encontrado em {docs_dir}")
            return results
        
        print(f"\n📂 Ingerindo {len(md_files)} documentos de {docs_dir}...\n")
        
        for filepath in sorted(md_files):
            print(f"→ Processando: {filepath.name}")
            count = self.ingest_file(filepath)
            results[filepath.name] = count
        
        total = sum(results.values())
        print(f"\n✅ Ingestão concluída: {total} chunks indexados de {len(md_files)} documentos")
        
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da coleção indexada."""
        count = self.collection.count()
        return {
            "total_chunks": count,
            "collection": COLLECTION_NAME,
            "embedding_model": EMBEDDING_MODEL
        }


def main():
    """Ponto de entrada para execução direta."""
    # Para desenvolvimento/teste, copia os arquivos de upload para o diretório de source
    import shutil
    
    source_docs = [
        Path("/mnt/user-data/uploads/POL-001-politica-devolucao.md"),
        Path("/mnt/user-data/uploads/PROC-042-frete-especial-v1.md"),
        Path("/mnt/user-data/uploads/PROC-042-v2-frete-especial-revisado.md"),
        Path("/mnt/user-data/uploads/SLA-2024-tabela-sla-clientes.md"),
        Path("/mnt/user-data/uploads/FAQ-atendimento.md"),
    ]
    
    docs_dir = Path("/home/claude/cenario-1/exercicio-1.3/docs/source")
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    for src in source_docs:
        if src.exists():
            shutil.copy(src, docs_dir / src.name)
    
    ingestor = RAGIngestor()
    results = ingestor.ingest_directory(docs_dir)
    
    stats = ingestor.get_stats()
    print(f"\n📊 Estatísticas finais: {stats}")
    
    return results


if __name__ == "__main__":
    main()
