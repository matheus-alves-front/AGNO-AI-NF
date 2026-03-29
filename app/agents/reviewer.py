"""
Reviewer Agent - Agente Crítico para Double-Check

Este agente faz uma segunda análise do resultado do Auditor
para reduzir falsos positivos e validar as sugestões.
"""

from agno.agent import Agent

from app.config.llm_provider import build_chat_model
from app.models.report_schema import AuditResult


REVIEWER_SYSTEM_PROMPT = """Você é o ReviewerFiscal, um revisor especialista em auditoria tributária.

Sua função é REVISAR o resultado de uma auditoria fiscal feita por outro agente.

SUAS RESPONSABILIDADES:

1. VALIDAR cada inconsistência reportada:
   - A inconsistência é real ou falso positivo?
   - A severidade está correta?
   - A sugestão de correção está adequada?
   - A referência legal está correta?

2. IDENTIFICAR problemas não detectados:
   - O auditor deixou passar algum erro?
   - Há inconsistências óbvias não reportadas?

3. AJUSTAR o risk_score:
   - O score final reflete a real situação da nota?
   - Considere o impacto fiscal de cada erro

CRITÉRIOS DE REVISÃO:

- Falso Positivo: Remova inconsistências que não são realmente erros
- Severidade Incorreta: Ajuste para refletir o real impacto fiscal
- Referência Inválida: Remova ou corrija citações legais incorretas

IMPORTANTE:
- Seja mais rigoroso que o auditor
- Prefira qualidade sobre quantidade
- Se em dúvida, mantenha a inconsistência mas reduza a confidence
"""


def create_reviewer_agent(
    model_id: str | None = None,
    temperature: float = 0.0,
    debug: bool = False
) -> Agent:
    """
    Cria o agente revisor.
    
    Args:
        model_id: Override opcional do modelo configurado por provider
        temperature: Usar 0.0 para máxima consistência
        debug: Mostrar tool calls
        
    Returns:
        Agent configurado para revisão
    """
    
    agent = Agent(
        name="ReviewerFiscal",
        model=build_chat_model(model_id=model_id, temperature=temperature),
        description=(
            "Revisor tributário que valida resultados de auditoria, "
            "removendo falsos positivos e validando sugestões de correção."
        ),
        instructions=[REVIEWER_SYSTEM_PROMPT],
        output_schema=AuditResult,
        structured_outputs=True,
        show_tool_calls=debug,
        markdown=True,
    )
    
    return agent


# Instância default do reviewer
reviewer_agent = create_reviewer_agent()


async def review_audit(
    original_audit: AuditResult,
    nfe_data: dict
) -> AuditResult:
    """
    Revisa o resultado de uma auditoria.
    
    Args:
        original_audit: Resultado da auditoria original
        nfe_data: Dados da NFe para contexto
        
    Returns:
        AuditResult revisado
    """
    import json
    
    prompt = f"""
Revise a seguinte auditoria fiscal e corrija/valide as inconsistências encontradas.

## Dados da NFe:
```json
{json.dumps(nfe_data, indent=2, ensure_ascii=False)}
```

## Auditoria Original:
```json
{original_audit.model_dump_json(indent=2)}
```

Retorne o resultado REVISADO, mantendo apenas inconsistências válidas e corrigindo erros de análise.
"""
    
    response = await reviewer_agent.arun(prompt)
    
    return response.content
