"""
AgentOS Server - Agente Fiscal com RAG e Tools

Versão completa com:
- Base de conhecimento RAG (TIPI, CFOP, CST)
- Tool para parsear XML de NFe
- Integração com AgentOS Control Plane
"""

from dotenv import load_dotenv
load_dotenv()

import json
from typing import Optional

from agno.agent import Agent
from agno.models.google import Gemini
from agno.db.sqlite import AsyncSqliteDb
from agno.os import AgentOS
from agno.tools import tool


# ==================== TOOLS ====================

@tool
def buscar_ncm(ncm: str) -> str:
    """
    Busca informações sobre um código NCM na base da TIPI.
    
    Args:
        ncm: Código NCM (8 dígitos)
        
    Returns:
        Informações sobre o NCM incluindo descrição e alíquota IPI
    """
    import json
    from pathlib import Path
    
    tipi_path = Path(__file__).parent / "app/knowledge/sources/tipi_completa.json"
    if not tipi_path.exists():
        tipi_path = Path(__file__).parent / "app/knowledge/sources/tipi_ncm.json"
    
    if not tipi_path.exists():
        return f"Base TIPI não encontrada. NCM: {ncm}"
    
    with open(tipi_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    items = data.get("tipi", {}).get("items", [])
    
    # Busca exata
    for item in items:
        if item.get("ncm") == ncm:
            return f"NCM {ncm}: {item.get('descricao')} | IPI: {item.get('ipi', 0)}%"
    
    # Busca por prefixo
    for item in items:
        if ncm.startswith(item.get("ncm", "")[:4]):
            return f"NCM similar encontrado - {item.get('ncm')}: {item.get('descricao')} | IPI: {item.get('ipi', 0)}%"
    
    return f"NCM {ncm} não encontrado na base TIPI."


@tool
def buscar_cfop(cfop: str) -> str:
    """
    Busca informações sobre um código CFOP.
    
    Args:
        cfop: Código CFOP (4 dígitos)
        
    Returns:
        Descrição e tipo da operação
    """
    import json
    from pathlib import Path
    
    cfop_path = Path(__file__).parent / "app/knowledge/sources/cfop_completa.json"
    if not cfop_path.exists():
        cfop_path = Path(__file__).parent / "app/knowledge/sources/cfop_table.json"
    
    if not cfop_path.exists():
        return f"Base CFOP não encontrada. CFOP: {cfop}"
    
    with open(cfop_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    items = data.get("cfop", {}).get("items", [])
    
    for item in items:
        if item.get("cfop") == cfop:
            return f"CFOP {cfop}: {item.get('descricao')} | Tipo: {item.get('tipo', 'N/A')}"
    
    return f"CFOP {cfop} não encontrado na base."


@tool  
def buscar_cst(codigo: str, regime: str = "normal") -> str:
    """
    Busca informações sobre CST ou CSOSN.
    
    Args:
        codigo: Código CST (2 dígitos) ou CSOSN (3 dígitos)
        regime: "normal" para CST ou "simples" para CSOSN
        
    Returns:
        Descrição e situação tributária
    """
    import json
    from pathlib import Path
    
    cst_path = Path(__file__).parent / "app/knowledge/sources/cst_csosn.json"
    
    if not cst_path.exists():
        return f"Base CST/CSOSN não encontrada."
    
    with open(cst_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cst_data = data.get("cst_csosn", {})
    
    if regime == "simples":
        items = cst_data.get("csosn", {}).get("items", [])
        tipo = "CSOSN"
    else:
        items = cst_data.get("cst", {}).get("items", [])
        tipo = "CST"
    
    for item in items:
        if item.get("codigo") == codigo:
            return f"{tipo} {codigo}: {item.get('descricao')} | Situação: {item.get('situacao', 'N/A')}"
    
    return f"{tipo} {codigo} não encontrado."


@tool
def validar_icms_interestadual(origem: str, uf_origem: str, uf_destino: str) -> str:
    """
    Valida a alíquota de ICMS para operação interestadual.
    
    Args:
        origem: Código de origem da mercadoria (0-8)
        uf_origem: UF de origem (ex: SP)
        uf_destino: UF de destino (ex: RJ)
        
    Returns:
        Alíquota correta e base legal
    """
    # Origens que usam 4%
    origens_importadas = ["1", "2", "3", "6", "7", "8"]
    
    if origem in origens_importadas:
        return f"Origem {origem} (importada): Alíquota interestadual DEVE ser 4% conforme Resolução SF nº 13/2012."
    
    # Alíquotas por região
    sul_sudeste = ["SP", "RJ", "MG", "ES", "PR", "SC", "RS"]
    
    if uf_origem in sul_sudeste and uf_destino in sul_sudeste:
        return f"Operação {uf_origem} -> {uf_destino}: Alíquota interestadual = 12%"
    elif uf_origem in sul_sudeste:
        return f"Operação {uf_origem} -> {uf_destino}: Alíquota interestadual = 7%"
    else:
        return f"Operação {uf_origem} -> {uf_destino}: Alíquota interestadual = 12%"


# ==================== SYSTEM PROMPT ====================

AUDITOR_SYSTEM_PROMPT = """Você é o AuditorFiscal, especialista em compliance tributário brasileiro.

VOCÊ TEM ACESSO A TOOLS PARA CONSULTAR:
- buscar_ncm: Consulta a Tabela TIPI
- buscar_cfop: Consulta tabela de CFOPs
- buscar_cst: Consulta CST e CSOSN
- validar_icms_interestadual: Valida alíquotas

USE AS TOOLS para fundamentar suas análises com dados reais.

REGRAS DE ANÁLISE:
1. NCM vs Descrição: Cerveja ≠ Refrigerante
2. CST vs Regime: CRT 1/2 usa CSOSN, CRT 3 usa CST
3. Origem estrangeira interestadual = 4% ICMS
4. CFOP deve corresponder à natureza da operação

FORMATO DE RESPOSTA:
- Lista de inconsistências encontradas
- Descrição clara do erro
- Sugestão de correção
- Referência legal

Seja preciso e use as tools para validar suas análises."""


# ==================== AGENTE ====================

auditor_agent = Agent(
    name="AuditorFiscal",
    model=Gemini(id="gemini-2.0-flash"),
    db=AsyncSqliteDb(db_file="fiscal_agent.db"),
    description="Auditor tributário com acesso a base de conhecimento fiscal (TIPI, CFOP, CST). Analisa NFes e identifica inconsistências.",
    instructions=[AUDITOR_SYSTEM_PROMPT],
    tools=[buscar_ncm, buscar_cfop, buscar_cst, validar_icms_interestadual],
    markdown=True,
)


# ==================== AGENTOS ====================

agent_os = AgentOS(
    id="fiscal-agent-os",
    description="Agente Fiscal Inteligente - Auditoria de NFe com IA e base de conhecimento tributário",
    agents=[auditor_agent],
)

app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="my_os:app", reload=True)
