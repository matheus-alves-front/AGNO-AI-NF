"""
NFe Parser Tool - Extrai dados estruturados de XMLs de Notas Fiscais Eletrônicas

Este módulo usa a biblioteca oficial nfelib para garantir compatibilidade
com o schema NFe v4.00 da SEFAZ.

REGRA DE OURO: Não reinventar a roda. Usar nfelib, não BeautifulSoup/Regex.
"""

from typing import Any
import json
from enum import Enum
from pathlib import Path

try:
    from nfelib.nfe.bindings.v4_0.nfe_v4_00 import Nfe
    NFELIB_AVAILABLE = True
except ImportError:
    NFELIB_AVAILABLE = False
    # Fallback para desenvolvimento sem nfelib instalada
    Nfe = None


class NfeParser:
    """
    Parser de Notas Fiscais Eletrônicas usando nfelib.
    
    Extrai apenas campos relevantes para reduzir contexto do LLM,
    economizando tokens e melhorando performance.
    """
    
    def __init__(self):
        if not NFELIB_AVAILABLE:
            raise ImportError(
                "nfelib não está instalada. "
                "Execute: pip install nfelib"
            )
    
    def parse_from_path(self, xml_path: str) -> dict[str, Any]:
        """
        Lê um arquivo XML de NFe e retorna um dicionário estruturado.
        
        Args:
            xml_path: Caminho para o arquivo XML da NFe
            
        Returns:
            Dicionário com dados extraídos da NFe
        """
        path = Path(xml_path)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {xml_path}")
        
        nfe = Nfe.from_path(str(path))
        return self._extract_nfe_data(nfe)
    
    def parse_from_string(self, xml_content: str) -> dict[str, Any]:
        """
        Parseia uma string XML de NFe.
        
        Args:
            xml_content: Conteúdo XML como string
            
        Returns:
            Dicionário com dados extraídos da NFe
        """
        nfe = Nfe.from_xml(xml_content)
        return self._extract_nfe_data(nfe)
    
    def _extract_nfe_data(self, nfe: Any) -> dict[str, Any]:
        """
        Extrai dados relevantes da NFe para auditoria.
        
        Remove campos nulos/vazios para economizar tokens no LLM.
        """
        nfe_root = getattr(nfe, "NFe", nfe)
        inf_nfe = nfe_root.infNFe
        
        # Dados do emitente
        emit = self._extract_emit(inf_nfe.emit)
        
        # Dados do destinatário
        dest = self._extract_dest(inf_nfe.dest)
        
        # Itens da nota
        items = [self._extract_item(det) for det in inf_nfe.det]
        
        # Totais
        totals = self._extract_totals(inf_nfe.total)
        
        result = {
            "chave_acesso": self._get_access_key(nfe_root),
            "numero": getattr(inf_nfe.ide, 'nNF', None),
            "serie": getattr(inf_nfe.ide, 'serie', None),
            "data_emissao": str(getattr(inf_nfe.ide, 'dhEmi', '')),
            "natureza_operacao": getattr(inf_nfe.ide, 'natOp', None),
            "emitente": emit,
            "destinatario": dest,
            "itens": items,
            "totais": totals,
        }
        
        return self._clean_empty_fields(result)
    
    def _get_access_key(self, nfe: Any) -> str:
        """Extrai a chave de acesso de 44 dígitos."""
        try:
            # A chave está no atributo Id da infNFe, formato: NFe + 44 dígitos
            inf_id = getattr(nfe.infNFe, 'Id', '')
            if inf_id and inf_id.startswith('NFe'):
                return inf_id[3:]  # Remove prefixo 'NFe'
            return inf_id
        except Exception:
            return ""
    
    def _extract_emit(self, emit: Any) -> dict[str, Any]:
        """Extrai dados do emitente."""
        if emit is None:
            return {}
        
        return {
            "cnpj": getattr(emit, 'CNPJ', None),
            "cpf": getattr(emit, 'CPF', None),
            "razao_social": getattr(emit, 'xNome', None),
            "nome_fantasia": getattr(emit, 'xFant', None),
            "ie": getattr(emit, 'IE', None),
            "crt": getattr(emit, 'CRT', None),  # Código Regime Tributário
            "uf": getattr(emit.enderEmit, 'UF', None) if emit.enderEmit else None,
        }
    
    def _extract_dest(self, dest: Any) -> dict[str, Any]:
        """Extrai dados do destinatário."""
        if dest is None:
            return {}
        
        return {
            "cnpj": getattr(dest, 'CNPJ', None),
            "cpf": getattr(dest, 'CPF', None),
            "razao_social": getattr(dest, 'xNome', None),
            "ie": getattr(dest, 'IE', None),
            "uf": getattr(dest.enderDest, 'UF', None) if dest.enderDest else None,
        }
    
    def _extract_item(self, det: Any) -> dict[str, Any]:
        """
        Extrai dados de um item da nota.
        
        Inclui informações tributárias para validação de consistência.
        """
        prod = det.prod
        imposto = det.imposto
        
        item = {
            "nItem": det.nItem,
            "xProd": getattr(prod, 'xProd', None),  # Descrição do produto
            "NCM": getattr(prod, 'NCM', None),
            "CEST": getattr(prod, 'CEST', None),
            "CFOP": getattr(prod, 'CFOP', None),
            "uCom": getattr(prod, 'uCom', None),
            "qCom": float(getattr(prod, 'qCom', 0)),
            "vUnCom": float(getattr(prod, 'vUnCom', 0)),
            "vProd": float(getattr(prod, 'vProd', 0)),
        }
        
        # Extrair dados de ICMS
        if imposto and imposto.ICMS:
            item["icms"] = self._extract_icms(imposto.ICMS)
        
        # Extrair dados de IPI
        if imposto and imposto.IPI:
            item["ipi"] = self._extract_ipi(imposto.IPI)
        
        # Extrair dados de PIS
        if imposto and imposto.PIS:
            item["pis"] = self._extract_pis(imposto.PIS)
        
        # Extrair dados de COFINS
        if imposto and imposto.COFINS:
            item["cofins"] = self._extract_cofins(imposto.COFINS)
        
        return item
    
    def _extract_icms(self, icms: Any) -> dict[str, Any]:
        """
        Extrai dados de ICMS considerando todos os grupos possíveis.
        
        O ICMS pode estar em diferentes grupos: ICMS00, ICMS10, ICMS20, etc.
        ou ICMSSN101, ICMSSN102, etc. para Simples Nacional.
        """
        icms_data = {}
        
        # Lista de possíveis grupos ICMS (regime normal)
        grupos_icms = [
            'ICMS00', 'ICMS10', 'ICMS20', 'ICMS30', 'ICMS40', 
            'ICMS51', 'ICMS60', 'ICMS70', 'ICMS90'
        ]
        
        # Lista de grupos ICMS Simples Nacional
        grupos_sn = [
            'ICMSSN101', 'ICMSSN102', 'ICMSSN201', 'ICMSSN202',
            'ICMSSN500', 'ICMSSN900'
        ]
        
        for grupo in grupos_icms:
            icms_grupo = getattr(icms, grupo, None)
            if icms_grupo:
                icms_data = {
                    "grupo": grupo,
                    "orig": getattr(icms_grupo, 'orig', None),
                    "CST": getattr(icms_grupo, 'CST', None),
                    "pICMS": float(getattr(icms_grupo, 'pICMS', 0)) if hasattr(icms_grupo, 'pICMS') else None,
                    "vICMS": float(getattr(icms_grupo, 'vICMS', 0)) if hasattr(icms_grupo, 'vICMS') else None,
                }
                break
        
        # Se não encontrou regime normal, verificar Simples Nacional
        if not icms_data:
            for grupo in grupos_sn:
                icms_grupo = getattr(icms, grupo, None)
                if icms_grupo:
                    icms_data = {
                        "grupo": grupo,
                        "orig": getattr(icms_grupo, 'orig', None),
                        "CSOSN": getattr(icms_grupo, 'CSOSN', None),
                        "pCredSN": float(getattr(icms_grupo, 'pCredSN', 0)) if hasattr(icms_grupo, 'pCredSN') else None,
                    }
                    break
        
        return icms_data
    
    def _extract_ipi(self, ipi: Any) -> dict[str, Any]:
        """Extrai dados de IPI."""
        ipi_data = {}
        
        if hasattr(ipi, 'IPITrib') and ipi.IPITrib:
            ipi_data = {
                "CST": getattr(ipi.IPITrib, 'CST', None),
                "pIPI": float(getattr(ipi.IPITrib, 'pIPI', 0)) if hasattr(ipi.IPITrib, 'pIPI') else None,
                "vIPI": float(getattr(ipi.IPITrib, 'vIPI', 0)) if hasattr(ipi.IPITrib, 'vIPI') else None,
            }
        elif hasattr(ipi, 'IPINT') and ipi.IPINT:
            ipi_data = {
                "CST": getattr(ipi.IPINT, 'CST', None),
            }
        
        return ipi_data
    
    def _extract_pis(self, pis: Any) -> dict[str, Any]:
        """Extrai dados de PIS."""
        pis_data = {}
        
        grupos = ['PISAliq', 'PISQtde', 'PISNT', 'PISOutr']
        for grupo in grupos:
            pis_grupo = getattr(pis, grupo, None)
            if pis_grupo:
                pis_data = {
                    "grupo": grupo,
                    "CST": getattr(pis_grupo, 'CST', None),
                    "pPIS": float(getattr(pis_grupo, 'pPIS', 0)) if hasattr(pis_grupo, 'pPIS') else None,
                    "vPIS": float(getattr(pis_grupo, 'vPIS', 0)) if hasattr(pis_grupo, 'vPIS') else None,
                }
                break
        
        return pis_data
    
    def _extract_cofins(self, cofins: Any) -> dict[str, Any]:
        """Extrai dados de COFINS."""
        cofins_data = {}
        
        grupos = ['COFINSAliq', 'COFINSQtde', 'COFINSNT', 'COFINSOutr']
        for grupo in grupos:
            cofins_grupo = getattr(cofins, grupo, None)
            if cofins_grupo:
                cofins_data = {
                    "grupo": grupo,
                    "CST": getattr(cofins_grupo, 'CST', None),
                    "pCOFINS": float(getattr(cofins_grupo, 'pCOFINS', 0)) if hasattr(cofins_grupo, 'pCOFINS') else None,
                    "vCOFINS": float(getattr(cofins_grupo, 'vCOFINS', 0)) if hasattr(cofins_grupo, 'vCOFINS') else None,
                }
                break
        
        return cofins_data
    
    def _extract_totals(self, total: Any) -> dict[str, Any]:
        """Extrai totais da nota."""
        if total is None or total.ICMSTot is None:
            return {}
        
        icms_tot = total.ICMSTot
        
        return {
            "vBC": float(getattr(icms_tot, 'vBC', 0)),
            "vICMS": float(getattr(icms_tot, 'vICMS', 0)),
            "vIPI": float(getattr(icms_tot, 'vIPI', 0)),
            "vPIS": float(getattr(icms_tot, 'vPIS', 0)),
            "vCOFINS": float(getattr(icms_tot, 'vCOFINS', 0)),
            "vNF": float(getattr(icms_tot, 'vNF', 0)),
        }
    
    def _clean_empty_fields(self, data: dict) -> dict:
        """
        Remove campos nulos, vazios ou zero para economizar tokens.
        
        Mantém zeros apenas em campos de valor monetário relevantes.
        """
        if isinstance(data, dict):
            return {
                k: self._clean_empty_fields(v)
                for k, v in data.items()
                if v is not None and v != "" and v != {} and v != []
            }
        elif isinstance(data, list):
            return [self._clean_empty_fields(item) for item in data if item]
        elif isinstance(data, Enum):
            return data.value
        elif hasattr(data, "value"):
            return data.value
        return data
    
    def to_json(self, nfe_data: dict, indent: int = 2) -> str:
        """Converte dados da NFe para JSON."""
        return json.dumps(nfe_data, indent=indent, ensure_ascii=False)


# Toolkit para Agno
class NfeToolkit:
    """
    Toolkit de NFe para uso com Agno Framework.
    
    Registra tools que o agente pode usar para parsear NFes.
    """
    
    def __init__(self):
        self.name = "nfe_tools"
        self.parser = NfeParser() if NFELIB_AVAILABLE else None
    
    def parse_nfe(self, xml_path: str) -> str:
        """
        Lê um arquivo XML de NFe e retorna um JSON estruturado.
        
        Args:
            xml_path: Caminho para o arquivo XML
            
        Returns:
            JSON string com dados da NFe
        """
        if not self.parser:
            return json.dumps({"error": "nfelib não disponível"})
        
        try:
            data = self.parser.parse_from_path(xml_path)
            return self.parser.to_json(data)
        except Exception as e:
            return json.dumps({"error": str(e)})
    
    def parse_nfe_content(self, xml_content: str) -> str:
        """
        Parseia conteúdo XML de NFe diretamente.
        
        Args:
            xml_content: String com o conteúdo XML
            
        Returns:
            JSON string com dados da NFe
        """
        if not self.parser:
            return json.dumps({"error": "nfelib não disponível"})
        
        try:
            data = self.parser.parse_from_string(xml_content)
            return self.parser.to_json(data)
        except Exception as e:
            return json.dumps({"error": str(e)})


# Instância singleton para uso direto
nfe_toolkit = NfeToolkit()
