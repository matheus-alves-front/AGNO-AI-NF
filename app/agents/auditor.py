"""
Auditor Agent - Agente Principal de Auditoria Fiscal

Este é o agente responsável por analisar NFes e identificar
inconsistências tributárias usando análise híbrida:
- Regras determinísticas (Python puro)
- Análise semântica (LLM configurável)
- RAG jurídico (consulta à legislação)
"""

from agno.agent import Agent

from app.config.llm_provider import build_chat_model
from app.models.report_schema import AuditResult


# System Prompt focado em compliance tributário brasileiro
AUDITOR_SYSTEM_PROMPT = """Você é o AuditorFiscal, um especialista em compliance tributário brasileiro.

Sua especialidade inclui:
- ICMS (Imposto sobre Circulação de Mercadorias e Serviços)
- IPI (Imposto sobre Produtos Industrializados)
- PIS/COFINS (Contribuições federais)
- NCM (Nomenclatura Comum do Mercosul)
- CFOP (Código Fiscal de Operações e Prestações)
- CST/CSOSN (Códigos de Situação Tributária)

REGRAS DE ANÁLISE:

1. NCM vs Descrição do Produto:
   - O NCM deve corresponder exatamente ao produto descrito
   - Ex: "Cerveja" com NCM de "Refrigerante" é ERRO CRÍTICO
   - Use seu conhecimento de mercado para validar

2. CFOP vs Operação:
   - CFOPs iniciados em 5 = operações internas (mesmo estado)
   - CFOPs iniciados em 6 = operações interestaduais
   - CFOPs iniciados em 7 = operações de exportação
   - Valide se o CFOP corresponde à natureza da operação

3. CST vs Regime Tributário:
   - CRT 1 ou 2 (Simples Nacional) DEVE usar CSOSN, não CST
   - CRT 3 (Regime Normal) DEVE usar CST, não CSOSN
   
4. Origem da Mercadoria (1º dígito do CST):
   - 0 = Nacional
   - 1 = Estrangeira - Importação direta
   - 2 = Estrangeira - Adquirida no mercado interno
   - 3-8 = Outras origens específicas
   - Mercadoria estrangeira em operação interestadual geralmente = 4% ICMS

5. CEST (Substituição Tributária):
   - Alguns NCMs EXIGEM CEST
   - Ausência de CEST obrigatório = ERRO

FORMATO DE RESPOSTA:
Você DEVE retornar um JSON válido conforme o schema AuditResult.
Cada inconsistência deve ter:
- Explicação clara do erro
- Sugestão de correção
- Referência legal quando possível

PATCHES DE CORREÇÃO:
- Sempre que possível, preencha correction_patches.
- Cada patch deve indicar item, campo afetado, valor atual, valor sugerido e motivo.
- Não invente patch quando não houver confiança suficiente.

IMPORTANTE:
- Não invente leis ou normas
- Se não tiver certeza, indique confidence baixo
- Seja preciso e objetivo
"""

# Few-shot examples para melhorar acurácia
FEW_SHOT_EXAMPLES = """
EXEMPLO 1 - Erro de NCM:
Item: "CERVEJA PILSEN 350ML"
NCM informado: 2202.10.00 (Refrigerantes)
NCM correto: 2203.00.00 (Cervejas de malte)
Severidade: critical
Referência: TIPI - Capítulo 22

EXEMPLO 2 - Erro de CSOSN:
Emitente CRT: 1 (Simples Nacional)
CST informado: 00 (Tributada integralmente)
Erro: Emitente do Simples deve usar CSOSN, não CST
Correção: Usar CSOSN adequado (ex: 101, 102, 500)
Severidade: high
Referência: LC 123/2006, Art. 18

EXEMPLO 3 - Alíquota interestadual:
Origem: 2 (Estrangeira - mercado interno)
Operação: Interestadual (CFOP 6xxx)
Alíquota informada: 12%
Alíquota correta: 4%
Severidade: high
Referência: Resolução SF nº 13/2012
"""


def create_auditor_agent(
    model_id: str | None = None,
    temperature: float = 0.1,
    debug: bool = False,
    use_knowledge: bool = True
) -> Agent:
    """
    Cria e configura o agente auditor fiscal.
    
    Args:
        model_id: Override opcional do modelo configurado por provider
        temperature: Temperatura do modelo (0.0 = mais determinístico)
        debug: Se True, mostra tool calls
        use_knowledge: Se True, integra com base de conhecimento RAG
        
    Returns:
        Agent configurado para auditoria fiscal
    """
    
    # Combina system prompt + few-shot examples
    full_instructions = [
        AUDITOR_SYSTEM_PROMPT,
        "EXEMPLOS DE ANÁLISE:",
        FEW_SHOT_EXAMPLES,
        "Agora analise a NFe fornecida e retorne o resultado da auditoria.",
    ]
    
    # Configura conhecimento RAG se disponível
    knowledge = None
    if use_knowledge:
        try:
            from app.knowledge.rules_rag import tax_kb, search_legislation
            # O knowledge será usado via consulta direta no prompt
            full_instructions.append(
                "\nVocê tem acesso à base de conhecimento tributário (TIPI, CFOPs, CST/CSOSN). "
                "Use essas informações para fundamentar suas análises."
            )
        except ImportError:
            pass
    
    agent = Agent(
        name="AuditorFiscal",
        model=build_chat_model(model_id=model_id, temperature=temperature),
        description=(
            "Auditor tributário especialista em legislação brasileira. "
            "Analisa NFes e identifica inconsistências em NCM, CST, CFOP, "
            "alíquotas e outros campos tributários."
        ),
        instructions=full_instructions,
        output_schema=AuditResult,
        structured_outputs=True,
        show_tool_calls=debug,
        markdown=True,
    )
    
    return agent


# Instância default do auditor
auditor_agent = create_auditor_agent()


async def audit_nfe(nfe_data: dict) -> AuditResult:
    """
    Executa auditoria em uma NFe já parseada.
    
    Args:
        nfe_data: Dicionário com dados da NFe (output do NfeParser)
        
    Returns:
        AuditResult com inconsistências encontradas
    """
    import json
    
    # Formata os dados para o prompt
    prompt = f"""
Analise a seguinte Nota Fiscal Eletrônica e identifique TODAS as inconsistências tributárias:

```json
{json.dumps(nfe_data, indent=2, ensure_ascii=False)}
```

Retorne o resultado da auditoria no formato JSON especificado.
"""
    
    # Executa o agente
    response = await auditor_agent.arun(prompt)
    
    return response.content


def audit_nfe_sync(nfe_data: dict) -> AuditResult:
    """Versão síncrona da auditoria."""
    import json
    
    prompt = f"""
Analise a seguinte Nota Fiscal Eletrônica e identifique TODAS as inconsistências tributárias:

```json
{json.dumps(nfe_data, indent=2, ensure_ascii=False)}
```

Retorne o resultado da auditoria no formato JSON especificado.
"""
    
    response = auditor_agent.run(prompt)
    
    return response.content
