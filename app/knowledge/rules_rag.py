"""
Rules RAG - Base de Conhecimento Tributário com PgVector

Configura o PgVectorKnowledgeBase para armazenar e consultar
legislação tributária (Tabela TIPI, CFOPs, NCMs, etc.).

Estratégia de Chunking: Por Artigo/Seção para manter contexto legal intacto.
"""

import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


# Configuração do banco de dados
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://fiscal_user:fiscal_pass@localhost:5432/fiscal_agent"
)


class TaxKnowledgeBase:
    """
    Base de conhecimento tributário usando pgvector para RAG.
    
    Armazena:
    - Tabela TIPI (NCM -> IPI)
    - Tabela de CFOPs
    - Regras CST/CSOSN
    - Legislação ICMS
    """
    
    def __init__(
        self,
        db_url: str = DATABASE_URL,
        table_name: str = "tax_knowledge",
        embedding_dimension: int = 768,  # Gemini text-embedding-004
    ):
        self.db_url = db_url
        self.table_name = table_name
        self.embedding_dimension = embedding_dimension
        self._embedder = None
        self._db = None
    
    @property
    def embedder(self):
        """Lazy load do embedder Gemini."""
        if self._embedder is None:
            try:
                import google.generativeai as genai
                
                api_key = os.getenv("GOOGLE_API_KEY")
                if api_key:
                    genai.configure(api_key=api_key)
                
                self._embedder = genai.embed_content
            except ImportError:
                raise ImportError(
                    "google-generativeai não está instalado. "
                    "Execute: pip install google-generativeai"
                )
        return self._embedder
    
    def get_embedding(self, text: str) -> list[float]:
        """Gera embedding para um texto usando Gemini."""
        result = self.embedder(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document",
        )
        return result['embedding']
    
    def get_query_embedding(self, query: str) -> list[float]:
        """Gera embedding para uma query de busca."""
        result = self.embedder(
            model="models/text-embedding-004",
            content=query,
            task_type="retrieval_query",
        )
        return result['embedding']
    
    def add_document(
        self, 
        content: str, 
        metadata: dict | None = None,
        conn = None
    ) -> int:
        """
        Adiciona um documento à base de conhecimento.
        
        Args:
            content: Texto do documento
            metadata: Metadados (tipo, fonte, etc.)
            conn: Conexão com o banco (opcional)
            
        Returns:
            ID do documento inserido
        """
        import psycopg2
        from psycopg2.extras import Json
        
        embedding = self.get_embedding(content)
        
        close_conn = False
        if conn is None:
            conn = psycopg2.connect(self.db_url)
            close_conn = True
        
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {self.table_name} (content, metadata, embedding)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (content, Json(metadata or {}), embedding)
                )
                doc_id = cur.fetchone()[0]
                conn.commit()
                return doc_id
        finally:
            if close_conn:
                conn.close()
    
    def search(
        self, 
        query: str, 
        limit: int = 5,
        threshold: float = 0.7
    ) -> list[dict[str, Any]]:
        """
        Busca documentos similares à query.
        
        Args:
            query: Texto da busca
            limit: Número máximo de resultados
            threshold: Similaridade mínima (0-1)
            
        Returns:
            Lista de documentos com score de similaridade
        """
        import psycopg2
        
        query_embedding = self.get_query_embedding(query)
        
        conn = psycopg2.connect(self.db_url)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT 
                        id,
                        content, 
                        metadata,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM {self.table_name}
                    WHERE 1 - (embedding <=> %s::vector) > %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (query_embedding, query_embedding, threshold, query_embedding, limit)
                )
                
                results = []
                for row in cur.fetchall():
                    results.append({
                        "id": row[0],
                        "content": row[1],
                        "metadata": row[2],
                        "similarity": float(row[3]),
                    })
                
                return results
        finally:
            conn.close()
    
    def search_by_type(
        self, 
        query: str, 
        doc_type: str,
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Busca documentos de um tipo específico.
        
        Args:
            query: Texto da busca
            doc_type: Tipo do documento (tipi, cfop, cst, legislacao)
            limit: Número máximo de resultados
        """
        import psycopg2
        
        query_embedding = self.get_query_embedding(query)
        
        conn = psycopg2.connect(self.db_url)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT 
                        id,
                        content, 
                        metadata,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM {self.table_name}
                    WHERE metadata->>'type' = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (query_embedding, doc_type, query_embedding, limit)
                )
                
                results = []
                for row in cur.fetchall():
                    results.append({
                        "id": row[0],
                        "content": row[1],
                        "metadata": row[2],
                        "similarity": float(row[3]),
                    })
                
                return results
        finally:
            conn.close()


# Instância singleton
tax_kb = TaxKnowledgeBase()


def get_ncm_info(ncm: str) -> list[dict]:
    """
    Busca informações sobre um NCM na base de conhecimento.
    
    Args:
        ncm: Código NCM (8 dígitos)
        
    Returns:
        Lista de documentos relevantes sobre o NCM
    """
    return tax_kb.search_by_type(
        query=f"NCM {ncm}",
        doc_type="tipi",
        limit=3
    )


def get_cfop_info(cfop: str) -> list[dict]:
    """
    Busca informações sobre um CFOP.
    
    Args:
        cfop: Código CFOP (4 dígitos)
        
    Returns:
        Lista de documentos relevantes sobre o CFOP
    """
    return tax_kb.search_by_type(
        query=f"CFOP {cfop}",
        doc_type="cfop",
        limit=3
    )


def search_legislation(query: str) -> list[dict]:
    """
    Busca na legislação tributária.
    
    Args:
        query: Termo de busca
        
    Returns:
        Lista de documentos legais relevantes
    """
    return tax_kb.search(query=query, limit=5, threshold=0.6)
