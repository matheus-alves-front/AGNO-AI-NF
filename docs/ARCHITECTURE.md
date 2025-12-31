# Architecture Guidelines: Fiscal Agent MVP

## 1. Tech Stack & Libraries

| Componente | Tecnologia | Versão | Propósito |
|------------|------------|--------|-----------|
| Framework | Agno | v1.0+ | Orquestração de agentes |
| Runtime | AgentOS | - | Serving com FastAPI automático |
| Parsing | `nfelib` | - | Bindings oficiais NFe (não usar BeautifulSoup/Regex) |
| Database | PostgreSQL | 16+ | Storage principal |
| Vector Store | pgvector | - | Embeddings para RAG |
| Validation | Pydantic | v2 | Structured outputs |
| LLM Provider | Google Gemini | - | gemini-2.0-flash (raciocínio), gemini-2.0-flash-lite (tarefas simples) |

---

## 2. Directory Structure

```
fiscal_agent/
├── app/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── auditor.py        # Agente Principal
│   │   └── reviewer.py       # Agente "Crítico" (Double check)
│   │
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── rules_rag.py      # Config do PgVectorKnowledgeBase
│   │   └── sources/          # PDFs/JSONs (Tabela TIPI, RICMS)
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── nfe_parser.py     # Wrapper da nfelib (Custom Tool)
│   │   └── tax_calculator.py # Calculadora determinística
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── nfe_schema.py     # Pydantic models espelhando a NFe
│   │   └── report_schema.py  # Pydantic models do Output
│   │
│   └── main.py               # Entrypoint do AgentOS
│
├── storage/                  # Local storage (se não usar DB externo)
├── scripts/                  # Scripts de seed (banco de dados)
├── tests/
├── .env
├── Dockerfile
└── requirements.txt
```

---

## 3. Implementation Details & Coding Standards

### 3.1. Parsing de NFe (`app/tools/nfe_parser.py`)

> [!IMPORTANT]
> **Regra de Ouro:** Não reinvente a roda. Use `nfelib`.
> O Agente não deve ler o XML bruto (muitos tokens). A tool deve extrair e limpar.

```python
from agno.tools import Toolkit
from nfelib.nfe.bindings.v4_0.nfe_v4_00 import Nfe
import json

class NfeToolkit(Toolkit):
    def __init__(self):
        super().__init__(name="nfe_tools")
        self.register(self.parse_nfe)

    def parse_nfe(self, xml_path: str) -> str:
        """
        Lê um arquivo XML de NFe e retorna um JSON estruturado com os itens e tributos.
        Usa nfelib para garantir compatibilidade com o schema oficial.
        """
        nfe = Nfe.from_path(xml_path)
        # Extrair apenas campos relevantes para reduzir contexto do LLM
        items = []
        for det in nfe.infNFe.det:
            items.append({
                "nItem": det.nItem,
                "xProd": det.prod.xProd,
                "NCM": det.prod.NCM,
                "CFOP": det.prod.CFOP,
                "uCom": det.prod.uCom,
                "vProd": det.prod.vProd,
                # Adicionar lógica para extrair CST/CSOSN que varia por regime
            })
        return json.dumps(items, indent=2)
```

### 3.2. Structured Outputs (`app/models/report_schema.py`)

> [!IMPORTANT]
> O Agno deve ser forçado a responder usando Pydantic.
> Isso é **crucial** para o frontend do SaaS.

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class TaxInconsistency(BaseModel):
    item_index: int = Field(..., description="Número do item na nota (nItem)")
    severity: Literal["low", "medium", "high", "critical"]
    issue_type: Literal["ncm_mismatch", "cst_invalid", "cfop_error", "cest_missing", "aliquot_error"]
    description: str = Field(..., description="Explicação humana do erro")
    suggested_fix: str = Field(..., description="Valor sugerido (ex: NCM correto)")
    legal_reference: Optional[str] = Field(None, description="Lei ou norma citada")

class AuditResult(BaseModel):
    nfe_access_key: str
    risk_score: int = Field(..., description="0 a 100, onde 100 é alto risco")
    inconsistencies: List[TaxInconsistency]
```

### 3.3. O Agente (`app/agents/auditor.py`)

> [!TIP]
> Configure o agente com `structured_outputs=True` ou use `response_model`.

```python
from agno.agent import Agent
from agno.models.google import Gemini
from app.knowledge.rules_rag import tax_kb
from app.tools.nfe_tools import NfeToolkit
from app.models.report_schema import AuditResult

fiscal_agent = Agent(
    name="AuditorFiscal",
    model=Gemini(id="gemini-2.0-flash"),
    tools=[NfeToolkit()],
    knowledge=tax_kb,
    description="Você é um auditor tributário especialista em legislação brasileira (ICMS/IPI/PIS/COFINS).",
    instructions=[
        "Analise cada item da NFe",
        "Valide NCM vs descrição do produto",
        "Cruze CFOP com CST/CSOSN",
        "Cite a legislação para cada inconsistência encontrada"
    ],
    response_model=AuditResult,  # FORÇA O OUTPUT JSON
    show_tool_calls=True,
    markdown=True
)
```

---

## 4. Base de Conhecimento (RAG)

> [!WARNING]
> **Não coloque toda a legislação no prompt.** Use PgVector.

### Chunking Strategy

| Estratégia | Descrição |
|------------|-----------|
| ✅ **Por Artigo/Seção** | Manter contexto legal intacto |
| ❌ Por tamanho fixo | Quebra contexto, causa alucinações |

### Setup do PgVectorKnowledgeBase

```python
from agno.knowledge.pgvector import PgVectorKnowledgeBase
from agno.embeddings.google import GeminiEmbedder

tax_kb = PgVectorKnowledgeBase(
    table_name="tax_knowledge",
    db_url="postgresql://user:pass@localhost:5432/fiscal_agent",
    embedder=GeminiEmbedder(model="models/text-embedding-004"),
)
```

---

## 5. Diagrama de Fluxo de Auditoria

```mermaid
flowchart TD
    A[XML Upload] --> B[NfeToolkit.parse_nfe]
    B --> C{Dados Extraídos}
    C --> D[Auditoria Determinística]
    C --> E[Auditoria Semântica LLM]
    D --> F[Regras CFOP/CST]
    E --> G[RAG Consulta TIPI]
    E --> H[Análise NCM vs xProd]
    F --> I[AuditResult JSON]
    G --> I
    H --> I
    I --> J[Reviewer Agent]
    J --> K[Output Final]
```

---

## 6. Variáveis de Ambiente (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/fiscal_agent

# Google Gemini
GOOGLE_API_KEY=your-gemini-api-key

# AgentOS
AGNO_DEBUG=true
AGNO_LOG_LEVEL=INFO
```
