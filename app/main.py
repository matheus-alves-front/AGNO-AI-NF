"""
Fiscal Agent - Main Entrypoint

Este é o ponto de entrada principal do AgentOS.
Configura e expõe o agente via FastAPI.
"""

import os
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.agents.auditor import auditor_agent, audit_nfe_sync
from app.tools.nfe_parser import NfeParser, NFELIB_AVAILABLE
from app.models.report_schema import AuditResult, BatchAuditResult


# Carrega variáveis de ambiente
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle do FastAPI."""
    # Startup
    print("🚀 Fiscal Agent iniciando...")
    print(f"   nfelib disponível: {NFELIB_AVAILABLE}")
    yield
    # Shutdown
    print("👋 Fiscal Agent finalizando...")


# Cria app FastAPI
app = FastAPI(
    title="Agente Fiscal Inteligente",
    description="API para auditoria automatizada de Notas Fiscais Eletrônicas",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Health check e informações básicas."""
    return {
        "status": "online",
        "service": "Agente Fiscal Inteligente",
        "version": "1.0.0",
        "nfelib_available": NFELIB_AVAILABLE,
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/audit", response_model=AuditResult)
async def audit_single_nfe(file: UploadFile = File(...)):
    """
    Audita uma única NFe.
    
    Aceita upload de arquivo XML e retorna resultado da auditoria.
    """
    if not file.filename.endswith('.xml'):
        raise HTTPException(
            status_code=400,
            detail="Apenas arquivos XML são aceitos"
        )
    
    if not NFELIB_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="nfelib não está instalada no servidor"
        )
    
    try:
        # Lê o conteúdo do arquivo
        content = await file.read()
        xml_content = content.decode('utf-8')
        
        # Parseia a NFe
        parser = NfeParser()
        nfe_data = parser.parse_from_string(xml_content)
        
        # Executa auditoria
        result = audit_nfe_sync(nfe_data)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar NFe: {str(e)}"
        )


@app.post("/audit/batch", response_model=BatchAuditResult)
async def audit_batch_nfe(files: list[UploadFile] = File(...)):
    """
    Audita múltiplas NFes em lote.
    
    Aceita upload de múltiplos arquivos XML.
    """
    if not NFELIB_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="nfelib não está instalada no servidor"
        )
    
    results = []
    total_with_issues = 0
    
    for file in files:
        if not file.filename.endswith('.xml'):
            continue
            
        try:
            content = await file.read()
            xml_content = content.decode('utf-8')
            
            parser = NfeParser()
            nfe_data = parser.parse_from_string(xml_content)
            
            result = audit_nfe_sync(nfe_data)
            results.append(result)
            
            if result.inconsistencies:
                total_with_issues += 1
                
        except Exception as e:
            # Log erro mas continua processando outras notas
            print(f"Erro ao processar {file.filename}: {e}")
    
    return BatchAuditResult(
        total_processed=len(results),
        total_with_issues=total_with_issues,
        results=results
    )


@app.post("/parse")
async def parse_nfe(file: UploadFile = File(...)):
    """
    Apenas parseia uma NFe sem auditar.
    
    Útil para debug e visualização dos dados extraídos.
    """
    if not file.filename.endswith('.xml'):
        raise HTTPException(
            status_code=400,
            detail="Apenas arquivos XML são aceitos"
        )
    
    if not NFELIB_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="nfelib não está instalada no servidor"
        )
    
    try:
        content = await file.read()
        xml_content = content.decode('utf-8')
        
        parser = NfeParser()
        nfe_data = parser.parse_from_string(xml_content)
        
        return JSONResponse(content=nfe_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao parsear NFe: {str(e)}"
        )


@app.post("/audit/pdf")
async def audit_with_pdf(file: UploadFile = File(...)):
    """
    Audita uma NFe e retorna o PDF do laudo.
    
    Retorna o PDF como download.
    """
    from fastapi.responses import FileResponse
    
    if not file.filename.endswith('.xml'):
        raise HTTPException(
            status_code=400,
            detail="Apenas arquivos XML são aceitos"
        )
    
    if not NFELIB_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="nfelib não está instalada no servidor"
        )
    
    try:
        from app.tools.pdf_generator import generate_audit_pdf
        
        content = await file.read()
        xml_content = content.decode('utf-8')
        
        parser = NfeParser()
        nfe_data = parser.parse_from_string(xml_content)
        
        result = audit_nfe_sync(nfe_data)
        
        # Gera o PDF
        pdf_path = generate_audit_pdf(result)
        
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"auditoria_{result.nfe_access_key}.pdf"
        )
        
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="fpdf2 não está instalado para geração de PDF"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar PDF: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("AGNO_DEBUG", "false").lower() == "true"
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=debug,
    )
