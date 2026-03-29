"""
Stress Test Script - Testa o sistema sob carga

Envia múltiplas requisições simultâneas para testar performance e estabilidade.

Uso:
    python scripts/stress_test.py
"""

import asyncio
import time
import json
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import httpx

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# Configurações
API_URL = "http://localhost:8000"
NUM_CONCURRENT = 10  # Requisições simultâneas
TIMEOUT = 60  # Timeout em segundos


# NFe de teste (dados já parseados)
SAMPLE_NFE_DATA = {
    "chave_acesso": "35230512345678901234550010000001231234567890",
    "numero": 123,
    "serie": 1,
    "data_emissao": "2023-05-15T10:30:00-03:00",
    "natureza_operacao": "VENDA DE MERCADORIA",
    "emitente": {
        "cnpj": "12345678901234",
        "razao_social": "EMPRESA TESTE LTDA",
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
            "qCom": 100,
            "vProd": 350.00,
            "icms": {"grupo": "ICMSSN102", "orig": "0", "CSOSN": "102"}
        },
        {
            "nItem": 2,
            "xProd": "REFRIGERANTE COLA 2L",
            "NCM": "22021000",
            "CFOP": "6102",
            "qCom": 50,
            "vProd": 400.00,
            "icms": {"grupo": "ICMSSN102", "orig": "0", "CSOSN": "102"}
        }
    ],
    "totais": {"vNF": 750.00}
}


async def check_health():
    """Verifica se o AgentOS está disponível."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_URL}/config")
            return response.status_code == 200
        except Exception:
            return False


async def single_audit_request(request_id: int) -> dict:
    """
    Executa uma única requisição de auditoria.
    
    Simula o fluxo que o agente faria.
    """
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.get(f"{API_URL}/config")
            
            elapsed = time.time() - start_time
            
            return {
                "request_id": request_id,
                "status": "success",
                "status_code": response.status_code,
                "elapsed_ms": round(elapsed * 1000, 2),
                "response": response.json() if response.status_code == 200 else None
            }
            
        except httpx.TimeoutException:
            elapsed = time.time() - start_time
            return {
                "request_id": request_id,
                "status": "timeout",
                "elapsed_ms": round(elapsed * 1000, 2),
                "error": "Request timeout"
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "request_id": request_id,
                "status": "error",
                "elapsed_ms": round(elapsed * 1000, 2),
                "error": str(e)
            }


async def run_stress_test():
    """Executa o teste de stress."""
    print("=" * 60)
    print("🚀 Iniciando Stress Test do Agente Fiscal")
    print("=" * 60)
    
    # Verifica se API está online
    print("\n🔍 Verificando disponibilidade da API...")
    if not await check_health():
        print("❌ API não está disponível!")
        print("   Execute: python my_os.py")
        return
    print("✅ API disponível\n")
    
    # Executa requisições em paralelo
    print(f"📊 Enviando {NUM_CONCURRENT} requisições simultâneas...")
    print("-" * 60)
    
    start_time = time.time()
    
    tasks = [single_audit_request(i) for i in range(NUM_CONCURRENT)]
    results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    
    # Analisa resultados
    success = [r for r in results if r["status"] == "success"]
    errors = [r for r in results if r["status"] == "error"]
    timeouts = [r for r in results if r["status"] == "timeout"]
    
    elapsed_times = [r["elapsed_ms"] for r in results if "elapsed_ms" in r]
    
    print("\n" + "=" * 60)
    print("📈 RESULTADOS DO STRESS TEST")
    print("=" * 60)
    
    print(f"\n📊 Resumo:")
    print(f"   Total de requisições: {NUM_CONCURRENT}")
    print(f"   ✅ Sucesso: {len(success)}")
    print(f"   ❌ Erros: {len(errors)}")
    print(f"   ⏰ Timeouts: {len(timeouts)}")
    
    print(f"\n⏱️ Tempo:")
    print(f"   Total: {total_time:.2f}s")
    print(f"   Média por requisição: {sum(elapsed_times)/len(elapsed_times):.2f}ms")
    print(f"   Mínimo: {min(elapsed_times):.2f}ms")
    print(f"   Máximo: {max(elapsed_times):.2f}ms")
    
    print(f"\n🚀 Throughput: {NUM_CONCURRENT/total_time:.2f} req/s")
    
    # Taxa de sucesso
    success_rate = (len(success) / NUM_CONCURRENT) * 100
    if success_rate == 100:
        print(f"\n✅ Taxa de sucesso: {success_rate:.1f}%")
    elif success_rate >= 80:
        print(f"\n⚠️ Taxa de sucesso: {success_rate:.1f}%")
    else:
        print(f"\n❌ Taxa de sucesso: {success_rate:.1f}%")
    
    # Erros detalhados
    if errors:
        print("\n❌ Erros encontrados:")
        for e in errors[:5]:  # Mostra apenas os 5 primeiros
            print(f"   Request {e['request_id']}: {e.get('error', 'Unknown')}")
    
    print("\n" + "=" * 60)


def test_schema_validation():
    """Testa validação dos schemas Pydantic."""
    print("\n🧪 Testando validação de schemas...")
    
    try:
        from app.models.report_schema import AuditResult, TaxInconsistency
        
        # Cria um resultado de teste
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
            summary="Teste de validação de schema."
        )
        
        # Testa serialização
        json_str = result.model_dump_json()
        parsed = json.loads(json_str)
        
        assert parsed["risk_score"] == 75
        assert len(parsed["inconsistencies"]) == 1
        
        print("   ✅ Schemas validados com sucesso")
        
    except Exception as e:
        print(f"   ❌ Erro na validação: {e}")


def main():
    """Ponto de entrada principal."""
    print("\n" + "=" * 60)
    print("🔬 SUITE DE TESTES - AGENTE FISCAL INTELIGENTE")
    print("=" * 60)
    
    # Testa schemas
    test_schema_validation()
    
    # Testa stress
    asyncio.run(run_stress_test())


if __name__ == "__main__":
    main()
