"""
Report Schema - Modelos Pydantic para Output Estruturado

Define os schemas que o Agente DEVE usar para retornar resultados.
Isso é CRUCIAL para integração com frontend do SaaS.

O Agno deve ser configurado com response_model=AuditResult para
forçar outputs JSON válidos.
"""

from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class TaxInconsistency(BaseModel):
    """
    Representa uma inconsistência tributária encontrada na NFe.
    
    Cada inconsistência deve ter uma explicação clara e,
    quando possível, uma referência legal.
    """
    
    item_index: int = Field(
        ..., 
        description="Número do item na nota (nItem)",
        ge=1
    )
    
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ...,
        description=(
            "Nível de severidade: "
            "low=informativo, medium=atenção, high=risco fiscal, critical=multa provável"
        )
    )
    
    issue_type: Literal[
        "ncm_mismatch",      # NCM não corresponde à descrição do produto
        "cst_invalid",       # CST inválido para a operação
        "csosn_invalid",     # CSOSN inválido para o CRT do emitente
        "cfop_error",        # CFOP inconsistente com a operação
        "cest_missing",      # CEST obrigatório ausente
        "cest_invalid",      # CEST não corresponde ao NCM
        "aliquot_error",     # Alíquota incorreta
        "origin_mismatch",   # Origem da mercadoria inconsistente
        "icms_calc_error",   # Erro no cálculo do ICMS
        "ipi_error",         # Erro no IPI
        "pis_cofins_error",  # Erro em PIS/COFINS
        "other"              # Outros erros
    ] = Field(
        ...,
        description="Tipo da inconsistência encontrada"
    )
    
    description: str = Field(
        ..., 
        description="Explicação humana e clara do erro encontrado",
        min_length=10,
        max_length=500
    )
    
    current_value: str | None = Field(
        None,
        description="Valor atual encontrado na nota (ex: NCM atual)"
    )
    
    suggested_fix: str = Field(
        ..., 
        description="Valor ou ação sugerida para correção",
        min_length=3,
        max_length=300
    )
    
    legal_reference: str | None = Field(
        None, 
        description=(
            "Lei, decreto ou norma que fundamenta a correção. "
            "Ex: 'Art. 155, II, CF/88' ou 'Convênio ICMS 142/18'"
        )
    )
    
    confidence: float = Field(
        default=0.8,
        description="Confiança do agente na análise (0.0 a 1.0)",
        ge=0.0,
        le=1.0
    )


class NfeMetadata(BaseModel):
    """Metadados básicos da NFe analisada."""
    
    numero: int | None = Field(None, description="Número da nota")
    serie: int | None = Field(None, description="Série da nota")
    data_emissao: str | None = Field(None, description="Data de emissão")
    emitente_cnpj: str | None = Field(None, description="CNPJ do emitente")
    emitente_razao: str | None = Field(None, description="Razão social do emitente")
    destinatario_cnpj: str | None = Field(None, description="CNPJ/CPF do destinatário")
    valor_total: float | None = Field(None, description="Valor total da nota")


class AuditResult(BaseModel):
    """
    Resultado completo da auditoria de uma NFe.
    
    Este é o schema principal que o Agente retorna.
    Deve ser usado como response_model no Agno.
    """
    
    nfe_access_key: str = Field(
        ..., 
        description="Chave de acesso de 44 dígitos da NFe",
        min_length=44,
        max_length=44
    )
    
    metadata: NfeMetadata | None = Field(
        None,
        description="Metadados básicos da nota para exibição"
    )
    
    risk_score: int = Field(
        ..., 
        description=(
            "Score de risco de 0 a 100. "
            "0-20=baixo, 21-50=médio, 51-80=alto, 81-100=crítico"
        ),
        ge=0,
        le=100
    )
    
    total_items_analyzed: int = Field(
        default=0,
        description="Quantidade de itens analisados na nota"
    )
    
    inconsistencies: list[TaxInconsistency] = Field(
        default_factory=list,
        description="Lista de inconsistências encontradas"
    )
    
    summary: str = Field(
        ...,
        description="Resumo executivo da auditoria em linguagem natural",
        min_length=20,
        max_length=1000
    )
    
    analyzed_at: datetime = Field(
        default_factory=datetime.now,
        description="Data/hora da análise"
    )
    
    @property
    def has_critical_issues(self) -> bool:
        """Verifica se há issues críticos."""
        return any(i.severity == "critical" for i in self.inconsistencies)
    
    @property
    def issues_by_severity(self) -> dict[str, int]:
        """Conta issues por severidade."""
        counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for issue in self.inconsistencies:
            counts[issue.severity] += 1
        return counts


class BatchAuditResult(BaseModel):
    """Resultado de auditoria em lote (múltiplas NFes)."""
    
    total_processed: int = Field(..., description="Total de notas processadas")
    total_with_issues: int = Field(..., description="Notas com inconsistências")
    results: list[AuditResult] = Field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Taxa de notas sem problemas."""
        if self.total_processed == 0:
            return 0.0
        return (self.total_processed - self.total_with_issues) / self.total_processed
