# MVP Requirements: Agente Fiscal Inteligente (Auditor NFe)

## 1. Definição do Produto

Um sistema **SaaS back-end first** que:
- Ingere arquivos XML de Notas Fiscais Eletrônicas (NFe - Modelo 55)
- Executa auditoria híbrida (Regras Rígidas + Análise Semântica via IA)
- Retorna relatório estruturado de conformidade tributária

---

## 2. Fluxo do Usuário (User Journey)

```mermaid
flowchart LR
    A[Upload XML] --> B[Processamento Async]
    B --> C[Auditoria]
    C --> D[Dashboard]
    D --> E[Interação IA]
    E --> F[Exportação PDF]
```

| Etapa | Descrição |
|-------|-----------|
| **1. Upload** | Usuário envia um ou múltiplos arquivos `.xml` (NFe) via interface |
| **2. Processamento** | Sistema processa assincronamente cada nota |
| **3. Auditoria** | Valida estrutura XML, cruza dados fiscais (CFOP vs CST/CSOSN), IA analisa descrição vs NCM |
| **4. Review** | Dashboard com "Notas em Risco" |
| **5. Interação** | Usuário pergunta "Por que isso está errado?", IA explica citando base legal |
| **6. Exportação** | Geração de PDF com laudo da auditoria |

---

## 3. Requisitos Funcionais (RF)

### 3.1. Ingestão e Parsing (Core)

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RF-01 | Suporte nativo à NFe v4.00 (Layout atual da SEFAZ) | 🔴 CRÍTICO |
| RF-02 | Parser resiliente a namespaces XML (notas de diferentes estados) | 🔴 CRÍTICO |
| RF-03 | Extração obrigatória de dados aninhados: `det`, `imposto`, `total`, `emit`, `dest` | 🔴 CRÍTICO |

### 3.2. Motor de Auditoria (Híbrido)

#### Auditoria Determinística (Python puro)
- Validar consistência **Origem da Mercadoria** (1º dígito CST) vs **Alíquota ICMS**
  - Ex: Origem 2 [Estrangeira] → geralmente implica 4% em interestadual
- Validar **CSOSN** (Simples Nacional) vs **CRT** do emitente

#### Auditoria Semântica (LLM Agent)
- Validar `xProd` (Descrição) vs `NCM`
  - Agente deve ter "senso comum" de mercado
  - Ex: "Cerveja" com NCM de "Refrigerante" = ERRO
- Validar **CEST** (Substituição Tributária) quando NCM exigir

#### RAG Jurídico
- Agente deve consultar:
  - **Tabela TIPI** (IPI)
  - **Lei do ICMS** (RICMS estaduais)
- Para justificar correções com base legal

### 3.3. Output Estruturado

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RF-04 | Resultado da auditoria deve ser JSON estrito (schema `AuditReport`) | 🔴 CRÍTICO |
| RF-05 | Proibido texto livre - apenas structured outputs | 🔴 CRÍTICO |

---

## 4. Requisitos Não-Funcionais (RNF)

| ID | Requisito | Valor | Prioridade |
|----|-----------|-------|------------|
| RNF-01 | Tempo de processamento por XML | < 15 segundos | 🔴 CRÍTICO |
| RNF-02 | Privacidade de dados sensíveis (CNPJ, Valores) | Não usar para retreino de modelos públicos | 🔴 CRÍTICO |
| RNF-03 | Stack definida | Agno, AgentOS, FastAPI, PostgreSQL + pgvector | 🔴 CRÍTICO |

---

## 5. Critérios de Aceite do MVP

- [ ] Parser processa XMLs de SP, MG e RJ sem erros
- [ ] Agente retorna JSON válido conforme schema `AuditResult`
- [ ] RAG encontra NCM correto para produtos comuns (cerveja, refrigerante, etc)
- [ ] Tempo médio < 15s por nota
- [ ] Zero alucinações de leis inexistentes
