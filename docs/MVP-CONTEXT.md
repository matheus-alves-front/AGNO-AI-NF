TECHNICAL SPEC PACK: Agente Fiscal Inteligente (MVP 1)
Este pacote contém os 3 documentos mandatários para o desenvolvimento via "Vibecoding" (AI-Assisted Programming).
________________
ARQUIVO 1: MVP-REQUIREMENTS.md
Este documento define o que deve ser construído, sem ambiguidade.
MVP Requirements: Agente Fiscal Inteligente (Auditor NFe)
1. Definição do Produto
Um sistema SaaS back-end first que ingere arquivos XML de Notas Fiscais Eletrônicas (NFe - Modelo 55), executa uma auditoria híbrida (Regras Rígidas + Análise Semântica via IA) e retorna um relatório estruturado de conformidade tributária.
2. Fluxo do Usuário (User Journey)
1. Upload: Usuário envia um ou múltiplos arquivos .xml (NFe) via interface.
2. Processamento: O sistema processa assincronamente cada nota.
3. Auditoria:
   * O sistema valida a estrutura do XML.
   * O sistema cruza dados fiscais (CFOP vs CST/CSOSN).
   * A IA analisa a descrição do produto vs NCM (Ex: "Cerveja" com NCM de "Refrigerante").
4. Review: Usuário visualiza um Dashboard com "Notas em Risco".
5. Interação: Usuário clica em um erro e pergunta: "Por que isso está errado?", a IA explica citando a base legal.
6. Exportação: Geração de PDF com o laudo da auditoria.
3. Requisitos Funcionais (RF)
3.1. Ingestão e Parsing (Core)
* **** Suporte nativo à NFe v4.00 (Layout atual da SEFAZ).
* **** O parser deve ser resiliente a namespaces XML (comum em notas de diferentes estados).
* **** Extração obrigatória de dados aninhados: det (itens), imposto (ICMS, IPI, PIS, COFINS), total, emit e dest.
3.2. Motor de Auditoria (Híbrido)
* ** Auditoria Determinística (Python puro):**
   * Validar consistência Origem da Mercadoria (primeiro dígito CST) vs Alíquota de ICMS (Ex: Origem 2 [Estrangeira] geralmente implica 4% em interestadual).
   * Validar CSOSN (Simples Nacional) vs CRT do emitente.
* ** Auditoria Semântica (LLM Agent):**
   * Validar xProd (Descrição) vs NCM. O Agente deve possuir "senso comum" de mercado.
   * Validar CEST (Substituição Tributária) quando o NCM exigir.
* ** RAG Jurídico:**
   * O Agente deve consultar a tabela TIPI e Lei do ICMS para justificar a correção.
3.3. Output Estruturado
* **** O resultado da auditoria NÃO pode ser texto livre. Deve ser um JSON estrito seguindo o schema AuditReport (ver Architecture).
4. Requisitos Não-Funcionais (RNF)
* **** Tempo de processamento: < 15 segundos por XML.
* **** Privacidade: Dados sensíveis (CNPJ, Valores) não devem ser usados para retreino de modelos públicos.
* **** Stack: Agno (Orquestração), AgentOS (Serving), FastAPI (Backend), PostgreSQL + pgvector (Memória/RAG).
________________
ARQUIVO 2: ARCHITECTURE.md
Este documento define como a IA deve codar. Copie este conteúdo no contexto do seu editor (Cursor/Windsurf) ou chat.
Architecture Guidelines: Fiscal Agent MVP
1. Tech Stack & Libraries
* Framework: Agno (v1.0+)
* Runtime: AgentOS
* Parsing: nfelib (Essencial: Usar bindings oficiais, não usar BeautifulSoup/Regex para XML).
* Database: PostgreSQL 16+ com extensão vector.
* Validation: Pydantic v2.
* LLM Provider: OpenAI (gpt-4o para raciocínio, gpt-4o-mini para tarefas simples).
2. Directory Structuretext
fiscal_agent/
├── app/
│ ├── agents/
│ │ ├── init.py
│ │ ├── auditor.py # O Agente Principal
│ │ └── reviewer.py # Agente "Crítico" (Double check)
│ ├── knowledge/
│ │ ├── init.py
│ │ ├── rules_rag.py # Config do PgVectorKnowledgeBase
│ │ └── sources/ # PDFs/JSONs (Tabela TIPI, RICMS)
│ ├── tools/
│ │ ├── init.py
│ │ ├── nfe_parser.py # Wrapper da nfelib (Custom Tool)
│ │ └── tax_calculator.py # Calculadora determinística
│ ├── models/
│ │ ├── init.py
│ │ ├── nfe_schema.py # Pydantic models espelhando a NFe
│ │ └── report_schema.py # Pydantic models do Output
│ └── main.py # Entrypoint do AgentOS
├── storage/ # Local storage (se não usar DB externo)
├── scripts/ # Scripts de seed (banco de dados)
├── tests/
├──.env
├── Dockerfile
└── requirements.txt






## 3. Implementation Details & Coding Standards

### 3.1. Parsing de NFe (`app/tools/nfe_parser.py`)
**Regra de Ouro:** Não reinvente a roda. Use `nfelib`.
O Agente não deve ler o XML bruto (muitos tokens). A tool deve extrair e limpar.

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
       items =
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

3.2. Structured Outputs (app/models/report_schema.py)
O Agno deve ser forçado a responder usando Pydantic. Isso é crucial para o frontend do SaaS.


Python




from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class TaxInconsistency(BaseModel):
   item_index: int = Field(..., description="Número do item na nota (nItem)")
   severity: Literal
   issue_type: Literal
   description: str = Field(..., description="Explicação humana do erro")
   suggested_fix: str = Field(..., description="Valor sugerido (ex: NCM correto)")
   legal_reference: Optional[str] = Field(None, description="Lei ou norma citada")

class AuditResult(BaseModel):
   nfe_access_key: str
   risk_score: int = Field(..., description="0 a 100, onde 100 é alto risco")
   inconsistencies: List

3.3. O Agente (app/agents/auditor.py)
Configure o agente com structured_outputs=True.


Python




from agno.agent import Agent
from agno.models.openai import OpenAIChat
from app.knowledge.rules_rag import tax_kb
from app.tools.nfe_tools import NfeToolkit
from app.models.report_schema import AuditResult

fiscal_agent = Agent(
   name="AuditorFiscal",
   model=OpenAIChat(id="gpt-4o"),
   tools=,
   knowledge=tax_kb,
   description="Você é um auditor tributário especialista em legislação brasileira (ICMS/IPI/PIS/COFINS).",
   instructions=,
   response_model=AuditResult, # FORÇA O OUTPUT JSON
   show_tool_calls=True,
   markdown=True
)

4. Base de Conhecimento (RAG)
Não coloque toda a legislação no prompt. Use PgVector.
* Chunking Strategy: Chunk por "Artigo" ou "Seção" da lei, não por tamanho fixo de caracteres, para manter o contexto legal intacto.
________________
ARQUIVO 3: MVP-CHECKLIST.md
Este documento é o plano de execução. Marque conforme avança.
Checklist de Desenvolvimento: Agente Fiscal MVP
Fase 1: Fundação (Environment & Core Tools)
* [ ] Configurar AgentOS: Inicializar projeto Agno com Docker (agno init).
* [ ] Database Setup: Subir container PostgreSQL com extensão pgvector.
* [ ] Dependency Install: pip install agno nfelib pydantic openai psycopg-binary.
* [ ] Parser Implementation: Criar app/tools/nfe_parser.py.
   * [ ] Implementar leitura via nfelib.
   * [ ] Criar função de limpeza (remover campos nulos/vazios para economizar tokens).
   * [ ] Testar parser com XMLs de homologação (SP, MG, RJ).
Fase 2: Conhecimento (RAG Pipeline)
* [ ] Data Gathering: Baixar Tabela TIPI 2025 (.pdf ou.csv) e Tabela de CFOPs.
* [ ] Vector Store: Configurar app/knowledge/rules_rag.py apontando para o Postgres local.
* [ ] Ingestion Script: Criar script load_knowledge.py que lê os PDFs/CSVs e insere no PgVector.
   * [ ] Crítico: Testar o chunking. O Agente consegue achar "NCM de Cerveja"?
Fase 3: Lógica do Agente (Brain)
* [ ] Pydantic Models: Definir AuditResult e TaxInconsistency em app/models.
* [ ] Agent Definition: Criar app/agents/auditor.py.
* [ ] Prompt Engineering:
   * [ ] Escrever System Prompt focado em compliance.
   * [ ] Adicionar "Few-Shot Examples" no prompt (exemplo de um erro de NCM e como corrigir).
* [ ] Integration Test: Rodar o agente via script Python simples passando um XML e validando se ele cospe o JSON correto.
Fase 4: Interface & AgentOS Serving
* [ ] API Endpoint: O AgentOS expõe FastAPI automaticamente, mas verifique as rotas.
* [ ] Playground: Usar o Agno Playground para testar upload de arquivo.
* [ ] PDF Generation: (Opcional para MVP 1.0) Criar uma tool simples generate_pdf_report usando fpdf que recebe o JSON do agente e cria um arquivo visual.
Fase 5: Validação Final (Quality Assurance)
* [ ] Stress Test: Enviar 10 XMLs simultaneamente.
* [ ] Hallucination Check: Verificar se o agente inventa leis. (Ajustar temperature=0).
* [ ] Cost Check: Verificar quantos tokens gasta por nota média (ajustar parser se necessário).