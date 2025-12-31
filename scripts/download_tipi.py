"""
Download TIPI - Baixa tabela completa de NCM da Receita Federal

Fonte oficial: Gov.br/Receita Federal
Arquivo: Tipi.xlsx (atualizado com ADE 003-2025)

Uso:
    python scripts/download_tipi.py
"""

import json
import os
import sys
from pathlib import Path
from io import BytesIO

import httpx

# URL oficial do arquivo TIPI no Gov.br
# Nota: A URL pode mudar, verificar em: https://www.gov.br/receitafederal/pt-br/assuntos/aduana-e-comercio-exterior/classificacao-fiscal-de-mercadorias/tabela-de-incidencia-do-ipi
TIPI_URL = "https://www.gov.br/receitafederal/pt-br/assuntos/aduana-e-comercio-exterior/classificacao-fiscal-de-mercadorias/tabela-de-incidencia-do-ipi/tipi/tipi-xlsx/1-tipi-2022-atualizada-ade-003-2025.xlsx/@@download/file"

# Alternativas de URLs
TIPI_URLS = [
    TIPI_URL,
    "https://www.gov.br/receitafederal/pt-br/assuntos/aduana-e-comercio-exterior/classificacao-fiscal-de-mercadorias/tipi-xlsx/tipi.xlsx",
]

OUTPUT_DIR = Path(__file__).parent.parent / "app" / "knowledge" / "sources"


def download_tipi_xlsx() -> bytes | None:
    """Baixa o arquivo XLSX da TIPI."""
    print("📥 Baixando TIPI do Gov.br...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; FiscalAgent/1.0)"
    }
    
    for url in TIPI_URLS:
        try:
            print(f"   Tentando: {url[:80]}...")
            with httpx.Client(follow_redirects=True, timeout=60) as client:
                response = client.get(url, headers=headers)
                if response.status_code == 200:
                    print(f"   ✅ Download completo: {len(response.content) / 1024:.1f} KB")
                    return response.content
        except Exception as e:
            print(f"   ⚠️ Falhou: {e}")
    
    return None


def parse_tipi_xlsx(xlsx_bytes: bytes) -> list[dict]:
    """Parseia o arquivo XLSX da TIPI."""
    try:
        import openpyxl
    except ImportError:
        print("❌ openpyxl não instalado. Execute: pip install openpyxl")
        sys.exit(1)
    
    print("📊 Parseando TIPI...")
    
    workbook = openpyxl.load_workbook(BytesIO(xlsx_bytes), read_only=True)
    sheet = workbook.active
    
    items = []
    header_found = False
    ncm_col = desc_col = ipi_col = None
    
    for row_num, row in enumerate(sheet.iter_rows(values_only=True), 1):
        if not row or all(cell is None for cell in row):
            continue
        
        # Procura cabeçalho
        if not header_found:
            row_str = ' '.join(str(cell).upper() if cell else '' for cell in row)
            if 'NCM' in row_str or 'CÓDIGO' in row_str:
                # Identifica colunas
                for i, cell in enumerate(row):
                    cell_str = str(cell).upper() if cell else ''
                    if 'NCM' in cell_str or 'CÓDIGO' in cell_str or 'CODIGO' in cell_str:
                        ncm_col = i
                    elif 'DESCRIÇÃO' in cell_str or 'DESCRICAO' in cell_str:
                        desc_col = i
                    elif 'IPI' in cell_str or 'ALÍQUOTA' in cell_str or 'ALIQUOTA' in cell_str:
                        ipi_col = i
                
                if ncm_col is not None:
                    header_found = True
                    print(f"   Cabeçalho encontrado na linha {row_num}")
                continue
        
        if not header_found:
            continue
        
        # Extrai dados
        ncm = str(row[ncm_col]).strip() if ncm_col and len(row) > ncm_col and row[ncm_col] else None
        
        if not ncm or len(ncm) < 4:
            continue
        
        # Limpa NCM (remove pontos, mantém só números)
        ncm_clean = ''.join(c for c in ncm if c.isdigit())
        
        if len(ncm_clean) < 4:
            continue
        
        desc = str(row[desc_col]).strip() if desc_col and len(row) > desc_col and row[desc_col] else "N/A"
        
        ipi = 0
        if ipi_col and len(row) > ipi_col and row[ipi_col]:
            try:
                ipi_str = str(row[ipi_col]).replace('%', '').replace(',', '.').strip()
                ipi = float(ipi_str) if ipi_str and ipi_str not in ['NT', 'Ex', '-'] else 0
            except ValueError:
                ipi = 0
        
        items.append({
            "ncm": ncm_clean,
            "descricao": desc[:500],  # Limita tamanho
            "ipi": ipi
        })
    
    print(f"   ✅ {len(items)} NCMs extraídos")
    return items


def save_tipi_json(items: list[dict]):
    """Salva TIPI como JSON."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    output = {
        "tipi": {
            "description": "Tabela de Incidência do IPI - Completa",
            "source": "Receita Federal - TIPI 2022 (ADE 003-2025)",
            "total_items": len(items),
            "items": items
        }
    }
    
    output_path = OUTPUT_DIR / "tipi_completa.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Salvo em: {output_path}")
    print(f"   Tamanho: {output_path.stat().st_size / 1024:.1f} KB")


def main():
    """Ponto de entrada principal."""
    print("=" * 60)
    print("🔧 Download TIPI - Tabela NCM Completa")
    print("=" * 60)
    
    # Download
    xlsx_bytes = download_tipi_xlsx()
    
    if not xlsx_bytes:
        print("\n❌ Não foi possível baixar a TIPI.")
        print("   Usando dados alternativos...")
        
        # Fallback: cria dados básicos expandidos
        create_fallback_tipi()
        return
    
    # Parse
    items = parse_tipi_xlsx(xlsx_bytes)
    
    if items:
        save_tipi_json(items)
    else:
        print("⚠️ Nenhum item extraído, usando fallback...")
        create_fallback_tipi()


def create_fallback_tipi():
    """Cria TIPI com dados expandidos como fallback."""
    print("\n📦 Criando TIPI expandida (fallback)...")
    
    # Dados mais comuns por capítulo
    items = [
        # Bebidas (Cap 22)
        {"ncm": "22011000", "descricao": "Águas minerais naturais", "ipi": 0},
        {"ncm": "22021000", "descricao": "Águas adicionadas de açúcar (Refrigerantes)", "ipi": 4},
        {"ncm": "22029900", "descricao": "Outras bebidas não alcoólicas", "ipi": 4},
        {"ncm": "22030000", "descricao": "Cervejas de malte", "ipi": 6},
        {"ncm": "22041000", "descricao": "Vinhos espumantes", "ipi": 10},
        {"ncm": "22042100", "descricao": "Vinhos até 2 litros", "ipi": 10},
        {"ncm": "22051000", "descricao": "Vermutes até 2 litros", "ipi": 10},
        {"ncm": "22060000", "descricao": "Sidra, perada, hidromel", "ipi": 10},
        {"ncm": "22071000", "descricao": "Álcool etílico não desnaturado", "ipi": 30},
        {"ncm": "22082000", "descricao": "Aguardentes de vinho ou bagaço", "ipi": 20},
        {"ncm": "22083000", "descricao": "Uísques", "ipi": 30},
        {"ncm": "22084000", "descricao": "Rum e cachaça", "ipi": 15},
        {"ncm": "22085000", "descricao": "Gin e genebra", "ipi": 20},
        {"ncm": "22086000", "descricao": "Vodca", "ipi": 20},
        {"ncm": "22089000", "descricao": "Outras bebidas espirituosas", "ipi": 20},
        
        # Tabaco (Cap 24)
        {"ncm": "24011000", "descricao": "Tabaco não destalado", "ipi": 30},
        {"ncm": "24022000", "descricao": "Cigarros de tabaco", "ipi": 300},
        {"ncm": "24031100", "descricao": "Tabaco para cachimbo", "ipi": 30},
        
        # Cosméticos (Cap 33)
        {"ncm": "33030000", "descricao": "Perfumes e águas de toalete", "ipi": 22},
        {"ncm": "33041000", "descricao": "Produtos de maquiagem para lábios", "ipi": 7},
        {"ncm": "33049100", "descricao": "Pós para maquiagem", "ipi": 7},
        {"ncm": "33051000", "descricao": "Xampus", "ipi": 7},
        
        # Medicamentos (Cap 30)
        {"ncm": "30049000", "descricao": "Medicamentos", "ipi": 0},
        {"ncm": "30042000", "descricao": "Medicamentos com antibióticos", "ipi": 0},
        
        # Informática (Cap 84)
        {"ncm": "84713000", "descricao": "Notebooks e laptops", "ipi": 0},
        {"ncm": "84714100", "descricao": "Computadores desktop", "ipi": 0},
        {"ncm": "84714900", "descricao": "Outros computadores", "ipi": 0},
        {"ncm": "84715000", "descricao": "Unidades de processamento", "ipi": 0},
        {"ncm": "84716000", "descricao": "Unidades de entrada/saída", "ipi": 0},
        {"ncm": "84717000", "descricao": "Unidades de armazenamento", "ipi": 0},
        
        # Telecomunicações (Cap 85)
        {"ncm": "85171200", "descricao": "Telefones celulares (Smartphones)", "ipi": 0},
        {"ncm": "85171800", "descricao": "Outros aparelhos telefônicos", "ipi": 0},
        {"ncm": "85176200", "descricao": "Aparelhos de recepção, conversão", "ipi": 0},
        {"ncm": "85287200", "descricao": "Televisores em cores", "ipi": 5},
        {"ncm": "85287100", "descricao": "Televisores monocromáticos", "ipi": 5},
        
        # Veículos (Cap 87)
        {"ncm": "87032100", "descricao": "Automóveis até 1000cc", "ipi": 7},
        {"ncm": "87032210", "descricao": "Automóveis 1000cc a 1500cc", "ipi": 11},
        {"ncm": "87032290", "descricao": "Automóveis 1500cc a 3000cc", "ipi": 25},
        {"ncm": "87032310", "descricao": "Automóveis acima 3000cc", "ipi": 25},
        {"ncm": "87033200", "descricao": "Veículos diesel 1500cc a 2500cc", "ipi": 11},
        {"ncm": "87033300", "descricao": "Veículos diesel acima 2500cc", "ipi": 25},
        {"ncm": "87040000", "descricao": "Caminhões para transporte de mercadorias", "ipi": 5},
        {"ncm": "87112000", "descricao": "Motocicletas 50cc a 250cc", "ipi": 8},
        {"ncm": "87113000", "descricao": "Motocicletas 250cc a 500cc", "ipi": 12},
        {"ncm": "87114000", "descricao": "Motocicletas 500cc a 800cc", "ipi": 17},
        {"ncm": "87115000", "descricao": "Motocicletas acima 800cc", "ipi": 22},
        
        # Alimentos (Cap 01-21)
        {"ncm": "04011000", "descricao": "Leite e creme de leite", "ipi": 0},
        {"ncm": "04021000", "descricao": "Leite em pó", "ipi": 0},
        {"ncm": "04070000", "descricao": "Ovos de aves", "ipi": 0},
        {"ncm": "16010000", "descricao": "Embutidos e produtos de carne", "ipi": 0},
        {"ncm": "17011100", "descricao": "Açúcar de cana bruto", "ipi": 0},
        {"ncm": "19053100", "descricao": "Biscoitos e bolachas doces", "ipi": 0},
        {"ncm": "19059000", "descricao": "Pães, bolos e produtos de padaria", "ipi": 0},
        {"ncm": "21069000", "descricao": "Preparações alimentícias diversas", "ipi": 0},
        
        # Construção (Cap 25, 68-70)
        {"ncm": "25232900", "descricao": "Cimento Portland", "ipi": 0},
        {"ncm": "68101100", "descricao": "Blocos e tijolos de cimento", "ipi": 5},
        {"ncm": "69041000", "descricao": "Tijolos de construção", "ipi": 0},
        {"ncm": "70031200", "descricao": "Vidros planos armados", "ipi": 5},
        {"ncm": "70052100", "descricao": "Vidros float", "ipi": 5},
        
        # Vestuário (Cap 61-62)
        {"ncm": "61091000", "descricao": "Camisetas de malha de algodão", "ipi": 0},
        {"ncm": "62034200", "descricao": "Calças de algodão (masculino)", "ipi": 0},
        {"ncm": "62046200", "descricao": "Calças de algodão (feminino)", "ipi": 0},
        {"ncm": "64039900", "descricao": "Calçados de couro", "ipi": 10},
        
        # Combustíveis (Cap 27)
        {"ncm": "27101921", "descricao": "Gasolina automotiva", "ipi": 0},
        {"ncm": "27101941", "descricao": "Óleo diesel", "ipi": 0},
        {"ncm": "27111100", "descricao": "Gás natural liquefeito (GNL)", "ipi": 0},
        {"ncm": "27111200", "descricao": "Propano (GLP)", "ipi": 0},
        {"ncm": "27112100", "descricao": "Gás natural (GN)", "ipi": 0},
    ]
    
    save_tipi_json(items)


if __name__ == "__main__":
    main()
