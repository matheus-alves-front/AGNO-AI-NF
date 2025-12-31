"""
AgentOS Server - Serve o agente fiscal via Agno Playground

Este é o ponto de entrada para o AgentOS Playground.

Uso:
    python playground.py
    
Depois acesse: https://app.agno.com/playground
E conecte em: http://localhost:7777
"""

from agno.agent import Agent
from agno.models.google import Gemini
from agno.playground import Playground, serve_playground_app

from app.models.report_schema import AuditResult


# System Prompt
AUDITOR_SYSTEM_PROMPT = """Você é o AuditorFiscal, um especialista em compliance tributário brasileiro.

Sua especialidade inclui:
- ICMS, IPI, PIS/COFINS
- NCM (Nomenclatura Comum do Mercosul)
- CFOP (Código Fiscal de Operações)
- CST/CSOSN

REGRAS DE ANÁLISE:
1. NCM vs Descrição: "Cerveja" com NCM de "Refrigerante" = ERRO CRÍTICO
2. CST vs Regime: CRT 1/2 (Simples) usa CSOSN, CRT 3 (Normal) usa CST
3. Origem estrangeira em operação interestadual = 4% ICMS

Retorne análises estruturadas com:
- Descrição do erro
- Sugestão de correção
- Referência legal

Seja preciso e não invente leis.
"""

# Cria o agente para o Playground
auditor_agent = Agent(
    name="AuditorFiscal",
    agent_id="auditor-fiscal-nfe",
    model=Gemini(id="gemini-2.0-flash"),
    description="Auditor tributário especialista em NFe. Analisa notas fiscais e identifica inconsistências.",
    instructions=[AUDITOR_SYSTEM_PROMPT],
    markdown=True,
)

# Cria o Playground
app = Playground(agents=[auditor_agent]).get_app()

if __name__ == "__main__":
    serve_playground_app("playground:app", reload=True, port=7777)
