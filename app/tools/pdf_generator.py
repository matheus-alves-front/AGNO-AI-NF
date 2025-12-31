"""
PDF Report Generator - Gera laudos de auditoria em PDF

Usa fpdf2 para criar relatórios visuais a partir do AuditResult.
"""

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False
    FPDF = None

if TYPE_CHECKING:
    from app.models.report_schema import AuditResult


class AuditPDFReport:
    """
    Gerador de relatórios PDF para auditoria fiscal.
    """
    
    # Cores por severidade
    SEVERITY_COLORS = {
        "critical": (220, 53, 69),    # Vermelho
        "high": (255, 153, 0),        # Laranja
        "medium": (255, 193, 7),      # Amarelo
        "low": (40, 167, 69),         # Verde
    }
    
    def __init__(self):
        if not FPDF_AVAILABLE:
            raise ImportError(
                "fpdf2 não está instalado. "
                "Execute: pip install fpdf2"
            )
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
    
    def generate(self, audit_result: "AuditResult", output_path: str | Path) -> str:
        """
        Gera o PDF do relatório de auditoria.
        
        Args:
            audit_result: Resultado da auditoria
            output_path: Caminho para salvar o PDF
            
        Returns:
            Caminho absoluto do arquivo gerado
        """
        self.pdf.add_page()
        
        # Cabeçalho
        self._add_header(audit_result)
        
        # Resumo executivo
        self._add_summary(audit_result)
        
        # Score de risco
        self._add_risk_score(audit_result)
        
        # Lista de inconsistências
        self._add_inconsistencies(audit_result)
        
        # Rodapé
        self._add_footer()
        
        # Salva o PDF
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.pdf.output(str(output_path))
        
        return str(output_path.absolute())
    
    def _add_header(self, audit_result: "AuditResult"):
        """Adiciona cabeçalho do relatório."""
        self.pdf.set_font("Helvetica", "B", 20)
        self.pdf.set_text_color(0, 51, 102)
        self.pdf.cell(0, 15, "LAUDO DE AUDITORIA FISCAL", ln=True, align="C")
        
        self.pdf.set_font("Helvetica", "", 10)
        self.pdf.set_text_color(100, 100, 100)
        self.pdf.cell(0, 8, "Agente Fiscal Inteligente - Auditoria Automatizada de NFe", ln=True, align="C")
        
        self.pdf.ln(5)
        
        # Informações da nota
        self.pdf.set_font("Helvetica", "B", 11)
        self.pdf.set_text_color(0, 0, 0)
        self.pdf.cell(0, 8, f"Chave de Acesso: {audit_result.nfe_access_key}", ln=True)
        
        if audit_result.metadata:
            meta = audit_result.metadata
            if meta.numero:
                self.pdf.set_font("Helvetica", "", 10)
                self.pdf.cell(0, 6, f"Nota Fiscal: {meta.numero} | Série: {meta.serie or 'N/A'}", ln=True)
            if meta.emitente_razao:
                self.pdf.cell(0, 6, f"Emitente: {meta.emitente_razao}", ln=True)
            if meta.valor_total:
                self.pdf.cell(0, 6, f"Valor Total: R$ {meta.valor_total:,.2f}", ln=True)
        
        self.pdf.ln(5)
        self.pdf.set_draw_color(200, 200, 200)
        self.pdf.line(10, self.pdf.get_y(), 200, self.pdf.get_y())
        self.pdf.ln(5)
    
    def _add_summary(self, audit_result: "AuditResult"):
        """Adiciona resumo executivo."""
        self.pdf.set_font("Helvetica", "B", 12)
        self.pdf.set_text_color(0, 51, 102)
        self.pdf.cell(0, 10, "RESUMO EXECUTIVO", ln=True)
        
        self.pdf.set_font("Helvetica", "", 10)
        self.pdf.set_text_color(0, 0, 0)
        
        # Quebra o resumo em linhas
        self.pdf.multi_cell(0, 6, audit_result.summary)
        self.pdf.ln(5)
    
    def _add_risk_score(self, audit_result: "AuditResult"):
        """Adiciona indicador visual de score de risco."""
        self.pdf.set_font("Helvetica", "B", 12)
        self.pdf.set_text_color(0, 51, 102)
        self.pdf.cell(0, 10, "SCORE DE RISCO", ln=True)
        
        score = audit_result.risk_score
        
        # Determina cor baseado no score
        if score <= 20:
            color = (40, 167, 69)  # Verde
            nivel = "BAIXO"
        elif score <= 50:
            color = (255, 193, 7)  # Amarelo
            nivel = "MÉDIO"
        elif score <= 80:
            color = (255, 153, 0)  # Laranja
            nivel = "ALTO"
        else:
            color = (220, 53, 69)  # Vermelho
            nivel = "CRÍTICO"
        
        # Barra de progresso
        bar_width = 180
        bar_height = 12
        x = 15
        y = self.pdf.get_y()
        
        # Fundo cinza
        self.pdf.set_fill_color(230, 230, 230)
        self.pdf.rect(x, y, bar_width, bar_height, "F")
        
        # Barra colorida
        self.pdf.set_fill_color(*color)
        filled_width = (score / 100) * bar_width
        self.pdf.rect(x, y, filled_width, bar_height, "F")
        
        # Texto do score
        self.pdf.set_xy(x, y)
        self.pdf.set_font("Helvetica", "B", 10)
        self.pdf.set_text_color(255, 255, 255) if score > 50 else self.pdf.set_text_color(0, 0, 0)
        self.pdf.cell(bar_width, bar_height, f"{score}/100 - RISCO {nivel}", align="C")
        
        self.pdf.ln(18)
        
        # Estatísticas
        issues = audit_result.issues_by_severity
        self.pdf.set_font("Helvetica", "", 10)
        self.pdf.set_text_color(0, 0, 0)
        self.pdf.cell(0, 6, f"Total de itens analisados: {audit_result.total_items_analyzed}", ln=True)
        self.pdf.cell(0, 6, f"Inconsistências encontradas: {len(audit_result.inconsistencies)}", ln=True)
        self.pdf.cell(0, 6, 
            f"Por severidade: Crítico({issues['critical']}) | "
            f"Alto({issues['high']}) | Médio({issues['medium']}) | Baixo({issues['low']})", 
            ln=True
        )
        self.pdf.ln(5)
    
    def _add_inconsistencies(self, audit_result: "AuditResult"):
        """Adiciona lista de inconsistências."""
        if not audit_result.inconsistencies:
            self.pdf.set_font("Helvetica", "B", 12)
            self.pdf.set_text_color(40, 167, 69)
            self.pdf.cell(0, 10, "✓ NENHUMA INCONSISTÊNCIA ENCONTRADA", ln=True)
            return
        
        self.pdf.set_font("Helvetica", "B", 12)
        self.pdf.set_text_color(0, 51, 102)
        self.pdf.cell(0, 10, "INCONSISTÊNCIAS IDENTIFICADAS", ln=True)
        
        for i, issue in enumerate(audit_result.inconsistencies, 1):
            # Verifica se precisa de nova página
            if self.pdf.get_y() > 250:
                self.pdf.add_page()
            
            # Cor de fundo baseado na severidade
            color = self.SEVERITY_COLORS.get(issue.severity, (100, 100, 100))
            
            # Cabeçalho da inconsistência
            self.pdf.set_fill_color(*color)
            self.pdf.set_text_color(255, 255, 255)
            self.pdf.set_font("Helvetica", "B", 10)
            
            severity_label = issue.severity.upper()
            self.pdf.cell(0, 8, 
                f"  #{i} | Item {issue.item_index} | {issue.issue_type.upper()} | {severity_label}", 
                ln=True, fill=True
            )
            
            # Corpo
            self.pdf.set_text_color(0, 0, 0)
            self.pdf.set_font("Helvetica", "", 10)
            
            # Descrição
            self.pdf.multi_cell(0, 5, f"Problema: {issue.description}")
            
            # Valor atual e sugestão
            if issue.current_value:
                self.pdf.cell(0, 5, f"Valor atual: {issue.current_value}", ln=True)
            self.pdf.set_font("Helvetica", "B", 10)
            self.pdf.cell(0, 5, f"Sugestão: {issue.suggested_fix}", ln=True)
            
            # Referência legal
            if issue.legal_reference:
                self.pdf.set_font("Helvetica", "I", 9)
                self.pdf.set_text_color(100, 100, 100)
                self.pdf.cell(0, 5, f"Base legal: {issue.legal_reference}", ln=True)
            
            # Confiança
            self.pdf.set_font("Helvetica", "", 9)
            self.pdf.set_text_color(150, 150, 150)
            self.pdf.cell(0, 5, f"Confiança: {issue.confidence:.0%}", ln=True)
            
            self.pdf.ln(3)
    
    def _add_footer(self):
        """Adiciona rodapé."""
        self.pdf.ln(10)
        self.pdf.set_draw_color(200, 200, 200)
        self.pdf.line(10, self.pdf.get_y(), 200, self.pdf.get_y())
        
        self.pdf.ln(5)
        self.pdf.set_font("Helvetica", "I", 8)
        self.pdf.set_text_color(150, 150, 150)
        
        now = datetime.now().strftime("%d/%m/%Y às %H:%M")
        self.pdf.cell(0, 5, f"Relatório gerado em {now}", ln=True, align="C")
        self.pdf.cell(0, 5, "Agente Fiscal Inteligente - Auditoria com IA Generativa", ln=True, align="C")
        self.pdf.cell(0, 5, "Este documento foi gerado automaticamente e não substitui análise profissional.", ln=True, align="C")


def generate_audit_pdf(audit_result: "AuditResult", output_dir: str = "storage/reports") -> str:
    """
    Função helper para gerar PDF de auditoria.
    
    Args:
        audit_result: Resultado da auditoria
        output_dir: Diretório para salvar o PDF
        
    Returns:
        Caminho do arquivo PDF gerado
    """
    generator = AuditPDFReport()
    
    # Gera nome do arquivo baseado na chave de acesso
    filename = f"auditoria_{audit_result.nfe_access_key}.pdf"
    output_path = Path(output_dir) / filename
    
    return generator.generate(audit_result, output_path)
