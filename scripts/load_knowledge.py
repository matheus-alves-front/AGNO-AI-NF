"""
Load Knowledge - Script principal para carregar TODOS os dados fiscais

Este script:
1. Executa download_tipi.py (NCMs completos)
2. Executa download_cfop.py (CFOPs completos)
3. Carrega todos os JSONs no PgVector com embeddings do provider configurado

Uso:
    python scripts/load_knowledge.py
"""

import json
import os
import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config.llm_provider import build_embedder, get_provider_config
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import Json

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://fiscal_user:fiscal_pass@localhost:5432/fiscal_agent"
)

SOURCES_DIR = ROOT_DIR / "app" / "knowledge" / "sources"
SCRIPTS_DIR = ROOT_DIR / "scripts"


def get_document_embedding(text: str) -> list[float]:
    """Gera embedding usando o provider configurado."""
    config = get_provider_config()
    embedder = build_embedder(task_type="RETRIEVAL_DOCUMENT")
    embedding = embedder.get_embedding(text[:8000])
    if len(embedding) != config.embedding_dimensions:
        raise ValueError(
            f"Embedding com dimensão inválida para provider '{config.provider}': "
            f"esperado={config.embedding_dimensions}, recebido={len(embedding)}"
        )
    return embedding


def download_data():
    """Executa scripts de download de dados."""
    print("\n📥 Baixando dados fiscais completos...")
    
    # Download TIPI
    tipi_script = SCRIPTS_DIR / "download_tipi.py"
    if tipi_script.exists():
        print("\n--- TIPI ---")
        subprocess.run([sys.executable, str(tipi_script)], check=False)
    
    # Download CFOP
    cfop_script = SCRIPTS_DIR / "download_cfop.py"
    if cfop_script.exists():
        print("\n--- CFOP ---")
        subprocess.run([sys.executable, str(cfop_script)], check=False)


def load_json_file(conn, filepath: Path, doc_type: str) -> int:
    """Carrega um arquivo JSON na base."""
    print(f"\n📦 Carregando {filepath.name}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extrai items do JSON
    items = []
    for key in data:
        if isinstance(data[key], dict) and "items" in data[key]:
            items = data[key]["items"]
            break
    
    if not items:
        print(f"   ⚠️ Nenhum item encontrado")
        return 0
    
    count = 0
    batch_size = 50
    
    with conn.cursor() as cur:
        for i, item in enumerate(items):
            # Cria texto para embedding
            if doc_type == "tipi":
                content = f"NCM: {item.get('ncm', 'N/A')}\nDescrição: {item.get('descricao', 'N/A')}\nIPI: {item.get('ipi', 0)}%"
                metadata = {"type": "tipi", "ncm": item.get('ncm')}
            elif doc_type == "cfop":
                content = f"CFOP: {item.get('cfop', 'N/A')}\nDescrição: {item.get('descricao', 'N/A')}\nTipo: {item.get('tipo', 'N/A')}"
                metadata = {"type": "cfop", "cfop": item.get('cfop')}
            elif doc_type == "cst":
                content = f"CST: {item.get('codigo', 'N/A')}\nDescrição: {item.get('descricao', 'N/A')}\nSituação: {item.get('situacao', 'N/A')}"
                metadata = {"type": "cst", "codigo": item.get('codigo')}
            else:
                content = json.dumps(item, ensure_ascii=False)
                metadata = {"type": doc_type}
            
            try:
                embedding = get_document_embedding(content)
                
                cur.execute(
                    """
                    INSERT INTO tax_knowledge (content, metadata, embedding)
                    VALUES (%s, %s, %s)
                    """,
                    (content, Json(metadata), embedding)
                )
                count += 1
                
                # Progress
                if count % batch_size == 0:
                    conn.commit()
                    print(f"   Processados: {count}/{len(items)}")
                    
            except Exception as e:
                print(f"   ✗ Erro: {e}")
    
    conn.commit()
    print(f"   ✅ {count} itens carregados")
    return count


def load_cst_csosn(conn, filepath: Path) -> int:
    """Carrega CST e CSOSN."""
    print(f"\n📊 Carregando {filepath.name}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    count = 0
    cst_data = data.get("cst_csosn", {})
    
    with conn.cursor() as cur:
        # CST
        for item in cst_data.get("cst", {}).get("items", []):
            content = f"CST {item['codigo']}: {item['descricao']}. Situação: {item['situacao']}. Regime: Normal (CRT 3)"
            try:
                embedding = get_document_embedding(content)
                cur.execute(
                    "INSERT INTO tax_knowledge (content, metadata, embedding) VALUES (%s, %s, %s)",
                    (content, Json({"type": "cst", "codigo": item['codigo']}), embedding)
                )
                count += 1
            except Exception as e:
                print(f"   ✗ CST {item['codigo']}: {e}")
        
        # CSOSN
        for item in cst_data.get("csosn", {}).get("items", []):
            content = f"CSOSN {item['codigo']}: {item['descricao']}. Situação: {item['situacao']}. Regime: Simples Nacional (CRT 1 ou 2)"
            try:
                embedding = get_document_embedding(content)
                cur.execute(
                    "INSERT INTO tax_knowledge (content, metadata, embedding) VALUES (%s, %s, %s)",
                    (content, Json({"type": "csosn", "codigo": item['codigo']}), embedding)
                )
                count += 1
            except Exception as e:
                print(f"   ✗ CSOSN {item['codigo']}: {e}")
        
        # Origem
        for item in cst_data.get("origem", {}).get("items", []):
            content = f"Origem {item['codigo']}: {item['descricao']}. ICMS Interestadual: {item['icms_interestadual']}"
            try:
                embedding = get_document_embedding(content)
                cur.execute(
                    "INSERT INTO tax_knowledge (content, metadata, embedding) VALUES (%s, %s, %s)",
                    (content, Json({"type": "origem", "codigo": item['codigo']}), embedding)
                )
                count += 1
            except Exception as e:
                print(f"   ✗ Origem {item['codigo']}: {e}")
        
        # Regras
        for regra in cst_data.get("regras_validacao", []):
            content = f"REGRA: {regra['regra']}. Severidade: {regra['severidade']}. Referência: {regra['referencia']}"
            try:
                embedding = get_document_embedding(content)
                cur.execute(
                    "INSERT INTO tax_knowledge (content, metadata, embedding) VALUES (%s, %s, %s)",
                    (content, Json({"type": "regra", "severidade": regra['severidade']}), embedding)
                )
                count += 1
            except Exception as e:
                print(f"   ✗ Regra: {e}")
    
    conn.commit()
    print(f"   ✅ {count} itens carregados")
    return count


def clear_db(conn):
    """Limpa a base."""
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE tax_knowledge RESTART IDENTITY")
    conn.commit()
    print("🗑️ Base limpa")


def main():
    print("=" * 60)
    print("🚀 CARREGAMENTO DE BASE DE CONHECIMENTO FISCAL")
    print("=" * 60)
    
    try:
        config = get_provider_config()
    except Exception as e:
        print(f"❌ Configuração de provider inválida: {e}")
        sys.exit(1)

    print(f"🧠 Provider ativo: {config.provider}")
    print(f"🧠 Modelo de embedding: {config.embedding_model_id}")
    print(f"🧠 Dimensão esperada: {config.embedding_dimensions}")
    
    # Pergunta se deve baixar dados
    resp = input("\nBaixar dados atualizados? (S/n): ").strip().lower()
    if resp != 'n':
        download_data()
    
    # Conecta ao banco
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("\n✅ Conectado ao PostgreSQL")
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("   Execute: docker compose up -d")
        sys.exit(1)
    
    try:
        # Limpar?
        resp = input("Limpar base antes de carregar? (S/n): ").strip().lower()
        if resp != 'n':
            clear_db(conn)
        
        total = 0
        
        # Carrega TIPI completa (ou fallback)
        tipi_completa = SOURCES_DIR / "tipi_completa.json"
        tipi_sample = SOURCES_DIR / "tipi_ncm.json"
        if tipi_completa.exists():
            total += load_json_file(conn, tipi_completa, "tipi")
        elif tipi_sample.exists():
            total += load_json_file(conn, tipi_sample, "tipi")
        
        # Carrega CFOP completa (ou fallback)
        cfop_completa = SOURCES_DIR / "cfop_completa.json"
        cfop_sample = SOURCES_DIR / "cfop_table.json"
        if cfop_completa.exists():
            total += load_json_file(conn, cfop_completa, "cfop")
        elif cfop_sample.exists():
            total += load_json_file(conn, cfop_sample, "cfop")
        
        # Carrega CST/CSOSN
        cst_path = SOURCES_DIR / "cst_csosn.json"
        if cst_path.exists():
            total += load_cst_csosn(conn, cst_path)
        
        print("\n" + "=" * 60)
        print(f"✅ CONCLUÍDO: {total} documentos carregados")
        print("=" * 60)
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
