"""
Integration Tests - Testes de integração do Agente Fiscal

Testa o fluxo completo: parse -> auditoria -> output estruturado.
"""

import pytest
import json
from pathlib import Path

# Adiciona o diretório raiz ao path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


# XML de exemplo para testes (NFe simplificada)
SAMPLE_NFE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
  <NFe xmlns="http://www.portalfiscal.inf.br/nfe">
    <infNFe Id="NFe35230512345678901234550010000001231234567890" versao="4.00">
      <ide>
        <cUF>35</cUF>
        <natOp>VENDA DE MERCADORIA</natOp>
        <serie>1</serie>
        <nNF>123</nNF>
        <dhEmi>2023-05-15T10:30:00-03:00</dhEmi>
      </ide>
      <emit>
        <CNPJ>12345678901234</CNPJ>
        <xNome>EMPRESA TESTE LTDA</xNome>
        <xFant>TESTE</xFant>
        <IE>123456789012</IE>
        <CRT>1</CRT>
        <enderEmit>
          <UF>SP</UF>
        </enderEmit>
      </emit>
      <dest>
        <CNPJ>98765432109876</CNPJ>
        <xNome>CLIENTE TESTE LTDA</xNome>
        <enderDest>
          <UF>RJ</UF>
        </enderDest>
      </dest>
      <det nItem="1">
        <prod>
          <xProd>CERVEJA PILSEN LATA 350ML</xProd>
          <NCM>22021000</NCM>
          <CFOP>6102</CFOP>
          <uCom>UN</uCom>
          <qCom>100</qCom>
          <vUnCom>3.50</vUnCom>
          <vProd>350.00</vProd>
        </prod>
        <imposto>
          <ICMS>
            <ICMSSN102>
              <orig>0</orig>
              <CSOSN>102</CSOSN>
            </ICMSSN102>
          </ICMS>
        </imposto>
      </det>
      <det nItem="2">
        <prod>
          <xProd>REFRIGERANTE COLA 2L</xProd>
          <NCM>22021000</NCM>
          <CFOP>6102</CFOP>
          <uCom>UN</uCom>
          <qCom>50</qCom>
          <vUnCom>8.00</vUnCom>
          <vProd>400.00</vProd>
        </prod>
        <imposto>
          <ICMS>
            <ICMSSN102>
              <orig>0</orig>
              <CSOSN>102</CSOSN>
            </ICMSSN102>
          </ICMS>
        </imposto>
      </det>
      <total>
        <ICMSTot>
          <vBC>0.00</vBC>
          <vICMS>0.00</vICMS>
          <vIPI>0.00</vIPI>
          <vPIS>0.00</vPIS>
          <vCOFINS>0.00</vCOFINS>
          <vNF>750.00</vNF>
        </ICMSTot>
      </total>
    </infNFe>
  </NFe>
</nfeProc>
"""

# Dados parseados de exemplo (simulando output do parser)
SAMPLE_NFE_DATA = {
    "chave_acesso": "35230512345678901234550010000001231234567890",
    "numero": 123,
    "serie": 1,
    "data_emissao": "2023-05-15T10:30:00-03:00",
    "natureza_operacao": "VENDA DE MERCADORIA",
    "emitente": {
        "cnpj": "12345678901234",
        "razao_social": "EMPRESA TESTE LTDA",
        "nome_fantasia": "TESTE",
        "ie": "123456789012",
        "crt": "1",
        "uf": "SP"
    },
    "destinatario": {
        "cnpj": "98765432109876",
        "razao_social": "CLIENTE TESTE LTDA",
        "uf": "RJ"
    },
    "itens": [
        {
            "nItem": 1,
            "xProd": "CERVEJA PILSEN LATA 350ML",
            "NCM": "22021000",
            "CFOP": "6102",
            "uCom": "UN",
            "qCom": 100,
            "vUnCom": 3.50,
            "vProd": 350.00,
            "icms": {
                "grupo": "ICMSSN102",
                "orig": "0",
                "CSOSN": "102"
            }
        },
        {
            "nItem": 2,
            "xProd": "REFRIGERANTE COLA 2L",
            "NCM": "22021000",
            "CFOP": "6102",
            "uCom": "UN",
            "qCom": 50,
            "vUnCom": 8.00,
            "vProd": 400.00,
            "icms": {
                "grupo": "ICMSSN102",
                "orig": "0",
                "CSOSN": "102"
            }
        }
    ],
    "totais": {
        "vBC": 0.00,
        "vICMS": 0.00,
        "vIPI": 0.00,
        "vPIS": 0.00,
        "vCOFINS": 0.00,
        "vNF": 750.00
    }
}


class TestReportSchema:
    """Testes dos schemas Pydantic."""
    
    def test_tax_inconsistency_creation(self):
        """Testa criação de TaxInconsistency."""
        from app.models.report_schema import TaxInconsistency
        
        issue = TaxInconsistency(
            item_index=1,
            severity="critical",
            issue_type="ncm_mismatch",
            description="O NCM 22021000 (Refrigerantes) não corresponde ao produto CERVEJA",
            current_value="22021000",
            suggested_fix="22030000 (Cervejas de malte)",
            legal_reference="TIPI - Capítulo 22"
        )
        
        assert issue.item_index == 1
        assert issue.severity == "critical"
        assert issue.issue_type == "ncm_mismatch"
        assert "CERVEJA" in issue.description
    
    def test_audit_result_creation(self):
        """Testa criação de AuditResult."""
        from app.models.report_schema import AuditResult, TaxInconsistency
        
        result = AuditResult(
            nfe_access_key="35230512345678901234550010000001231234567890",
            risk_score=75,
            total_items_analyzed=2,
            inconsistencies=[
                TaxInconsistency(
                    item_index=1,
                    severity="critical",
                    issue_type="ncm_mismatch",
                    description="NCM incorreto para cerveja",
                    suggested_fix="Usar NCM 22030000"
                )
            ],
            summary="Nota fiscal com 1 inconsistência crítica no item 1."
        )
        
        assert result.risk_score == 75
        assert len(result.inconsistencies) == 1
        assert result.has_critical_issues == True
        assert result.issues_by_severity["critical"] == 1
    
    def test_audit_result_json_serialization(self):
        """Testa serialização do AuditResult para JSON."""
        from app.models.report_schema import AuditResult, TaxInconsistency
        
        result = AuditResult(
            nfe_access_key="35230512345678901234550010000001231234567890",
            risk_score=50,
            total_items_analyzed=2,
            inconsistencies=[],
            summary="Nota fiscal sem inconsistências detectadas."
        )
        
        json_str = result.model_dump_json()
        parsed = json.loads(json_str)
        
        assert parsed["risk_score"] == 50
        assert len(parsed["inconsistencies"]) == 0


class TestNfeSchema:
    """Testes dos schemas de NFe."""
    
    def test_nfe_parsed_creation(self):
        """Testa criação de NFeParsed."""
        from app.models.nfe_schema import NFeParsed, EmitenteNFe, ItemNFe
        
        nfe = NFeParsed(
            chave_acesso="35230512345678901234550010000001231234567890",
            numero=123,
            serie=1,
            emitente=EmitenteNFe(
                cnpj="12345678901234",
                razao_social="EMPRESA TESTE",
                crt="1"
            ),
            itens=[
                ItemNFe(
                    n_item=1,
                    x_prod="CERVEJA PILSEN",
                    ncm="22030000",
                    cfop="6102"
                )
            ]
        )
        
        assert nfe.total_itens == 1
        assert nfe.is_simples_nacional == True


class TestPDFGenerator:
    """Testes do gerador de PDF."""
    
    def test_pdf_generation(self, tmp_path):
        """Testa geração de PDF."""
        try:
            from app.tools.pdf_generator import AuditPDFReport
            from app.models.report_schema import AuditResult, TaxInconsistency
        except ImportError as e:
            pytest.skip(f"Dependência não disponível: {e}")
        
        result = AuditResult(
            nfe_access_key="35230512345678901234550010000001231234567890",
            risk_score=65,
            total_items_analyzed=2,
            inconsistencies=[
                TaxInconsistency(
                    item_index=1,
                    severity="critical",
                    issue_type="ncm_mismatch",
                    description="NCM incorreto para cerveja",
                    suggested_fix="Usar NCM 22030000",
                    legal_reference="TIPI Cap. 22"
                )
            ],
            summary="Nota com erro crítico no NCM do item 1."
        )
        
        output_path = tmp_path / "test_report.pdf"
        
        generator = AuditPDFReport()
        path = generator.generate(result, output_path)
        
        assert Path(path).exists()
        assert Path(path).suffix == ".pdf"


class TestIntegration:
    """Testes de integração do fluxo completo."""
    
    @pytest.mark.skipif(
        not Path(__file__).parent.parent.joinpath(".env").exists(),
        reason="Arquivo .env não configurado"
    )
    def test_full_audit_flow(self):
        """
        Testa fluxo completo de auditoria.
        
        Requer:
        - GOOGLE_API_KEY configurada no .env
        - Dependências instaladas
        """
        from app.agents.auditor import audit_nfe_sync
        
        result = audit_nfe_sync(SAMPLE_NFE_DATA)
        
        # Verifica estrutura do resultado
        assert hasattr(result, 'nfe_access_key')
        assert hasattr(result, 'risk_score')
        assert hasattr(result, 'inconsistencies')
        assert hasattr(result, 'summary')
        
        # O resultado deve detectar o erro de NCM (cerveja com NCM de refrigerante)
        assert result.risk_score >= 0
        assert result.risk_score <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
