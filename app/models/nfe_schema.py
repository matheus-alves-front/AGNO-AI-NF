"""
NFe Schema - Modelos Pydantic espelhando a estrutura da NFe

Estes modelos representam a estrutura da Nota Fiscal Eletrônica
conforme o layout v4.00 da SEFAZ.
"""

from pydantic import BaseModel, Field
from typing import Literal


class EnderecoNFe(BaseModel):
    """Endereço (emitente ou destinatário)."""
    logradouro: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro: str | None = None
    municipio: str | None = None
    cod_municipio: str | None = None
    uf: str | None = None
    cep: str | None = None


class EmitenteNFe(BaseModel):
    """Dados do emitente da NFe."""
    cnpj: str | None = Field(None, description="CNPJ do emitente")
    cpf: str | None = Field(None, description="CPF do emitente (pessoa física)")
    razao_social: str | None = Field(None, alias="xNome")
    nome_fantasia: str | None = Field(None, alias="xFant")
    ie: str | None = Field(None, description="Inscrição Estadual")
    crt: Literal["1", "2", "3"] | None = Field(
        None, 
        description="Código Regime Tributário: 1=Simples Nacional, 2=SN Excesso, 3=Normal"
    )
    endereco: EnderecoNFe | None = None


class DestinatarioNFe(BaseModel):
    """Dados do destinatário da NFe."""
    cnpj: str | None = None
    cpf: str | None = None
    razao_social: str | None = None
    ie: str | None = None
    endereco: EnderecoNFe | None = None


class ICMSItem(BaseModel):
    """Dados de ICMS de um item."""
    grupo: str = Field(..., description="Grupo ICMS (ex: ICMS00, ICMSSN101)")
    orig: str | None = Field(
        None,
        description="Origem da mercadoria: 0=Nacional, 1=Estrangeira Importação Direta, 2=Estrangeira Mercado Interno, etc."
    )
    cst: str | None = Field(None, description="CST - Código de Situação Tributária (regime normal)")
    csosn: str | None = Field(None, description="CSOSN - Código de Situação da Operação no Simples Nacional")
    aliquota: float | None = Field(None, description="Alíquota do ICMS (%)")
    base_calculo: float | None = Field(None, description="Base de cálculo")
    valor: float | None = Field(None, description="Valor do ICMS")


class IPIItem(BaseModel):
    """Dados de IPI de um item."""
    cst: str | None = None
    aliquota: float | None = None
    valor: float | None = None


class PISItem(BaseModel):
    """Dados de PIS de um item."""
    cst: str | None = None
    aliquota: float | None = None
    valor: float | None = None


class COFINSItem(BaseModel):
    """Dados de COFINS de um item."""
    cst: str | None = None
    aliquota: float | None = None
    valor: float | None = None


class ItemNFe(BaseModel):
    """
    Item da Nota Fiscal.
    
    Contém informações do produto e seus tributos.
    """
    n_item: int = Field(..., description="Número sequencial do item", ge=1)
    
    # Dados do produto
    x_prod: str = Field(..., description="Descrição do produto")
    ncm: str = Field(..., description="Código NCM (8 dígitos)")
    cest: str | None = Field(None, description="Código CEST (7 dígitos)")
    cfop: str = Field(..., description="Código Fiscal de Operação (4 dígitos)")
    
    # Quantidades e valores
    unidade: str | None = Field(None, description="Unidade comercial")
    quantidade: float = Field(default=0)
    valor_unitario: float = Field(default=0)
    valor_total: float = Field(default=0)
    
    # Tributos
    icms: ICMSItem | None = None
    ipi: IPIItem | None = None
    pis: PISItem | None = None
    cofins: COFINSItem | None = None


class TotaisNFe(BaseModel):
    """Totais da NFe."""
    base_calculo_icms: float = 0
    valor_icms: float = 0
    valor_ipi: float = 0
    valor_pis: float = 0
    valor_cofins: float = 0
    valor_total_nota: float = 0


class NFeParsed(BaseModel):
    """
    Representação completa de uma NFe parseada.
    
    Este modelo é usado internamente após o parsing do XML.
    """
    chave_acesso: str = Field(..., description="Chave de acesso de 44 dígitos")
    numero: int | None = None
    serie: int | None = None
    data_emissao: str | None = None
    natureza_operacao: str | None = None
    
    emitente: EmitenteNFe | None = None
    destinatario: DestinatarioNFe | None = None
    
    itens: list[ItemNFe] = Field(default_factory=list)
    totais: TotaisNFe | None = None
    
    @property
    def total_itens(self) -> int:
        """Retorna quantidade de itens."""
        return len(self.itens)
    
    @property
    def is_simples_nacional(self) -> bool:
        """Verifica se emitente é do Simples Nacional."""
        if self.emitente and self.emitente.crt:
            return self.emitente.crt in ("1", "2")
        return False
