# 🤖 Agente Fiscal Inteligente

## O que é?

O **Agente Fiscal Inteligente** é uma solução de Inteligência Artificial que audita automaticamente Notas Fiscais Eletrônicas (NFe), identificando erros tributários antes que virem problemas com o Fisco.

Ele funciona como um **auditor tributário virtual 24/7**, analisando cada nota fiscal e apontando inconsistências com base na legislação brasileira atualizada.

---

## Para quem é?

- **Contadores e escritórios contábeis** que processam centenas de notas por mês
- **Empresas** que querem reduzir erros fiscais e multas
- **ERPs e sistemas fiscais** que desejam agregar inteligência às suas soluções
- **Consultores tributários** que buscam automatizar validações

---

## O que ele analisa?

### 📦 NCM (Nomenclatura Comum do Mercosul)
Valida se o código NCM corresponde ao produto descrito na nota.

> **Exemplo de erro detectado:**  
> Produto "Cerveja Pilsen" com NCM 2202.10.00 (Refrigerantes) ❌  
> Deveria ser 2203.00.00 (Cervejas) ✅

### 📋 CST e CSOSN
Verifica se o código de situação tributária está correto para o regime da empresa.

> **Exemplo de erro detectado:**  
> Empresa do Simples Nacional usando CST ao invés de CSOSN ❌

### 🚚 CFOP (Código Fiscal de Operações)
Analisa se o CFOP corresponde à natureza da operação (venda, transferência, devolução, etc).

### 📊 Alíquotas de ICMS
Valida as alíquotas em operações interestaduais, especialmente para produtos importados.

> **Exemplo de erro detectado:**  
> Produto importado (origem 1) em operação SP→RJ com alíquota 12% ❌  
> Deveria ser 4% conforme Resolução SF nº 13/2012 ✅

### 💰 IPI (Imposto sobre Produtos Industrializados)
Consulta a Tabela TIPI para validar as alíquotas de IPI por NCM.

---

## Como funciona?

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  NFe (XML)  │ ──► │   Agente IA  │ ──► │  Relatório de   │
│             │     │  + RAG Fiscal │     │  Inconsistências│
└─────────────┘     └──────────────┘     └─────────────────┘
```

1. **Upload da NFe** (arquivo XML ou dados via API)
2. **Análise automática** usando IA + base de conhecimento fiscal
3. **Relatório estruturado** com erros, sugestões e referências legais

---

## Bases de Conhecimento Integradas

| Base | Conteúdo | Atualização |
|------|----------|-------------|
| **TIPI** | Tabela de NCMs e alíquotas IPI | Receita Federal |
| **CFOP** | 600+ códigos de operações | Convênio SINIEF |
| **CST/CSOSN** | Códigos de situação tributária | LC 123/2006 |
| **Regras ICMS** | Alíquotas interestaduais | Resolução SF 13/2012 |

---

## Diferenciais

| Característica | Benefício |
|----------------|-----------|
| **IA Generativa** | Entende contexto, não apenas regras fixas |
| **Base Jurídica** | Cita a legislação em cada análise |
| **Tempo Real** | Resposta em segundos |
| **API Pronta** | Integração fácil com seu sistema |
| **Escalável** | Analisa milhares de notas por dia |

---

## Exemplo de Análise Real

**Entrada:**
```
Produto: WHISKY ESCOCÊS 12 ANOS
NCM: 22083000
Origem: 1 (Importado)
Operação: SP → RJ
Alíquota informada: 12%
```

**Resposta do Agente:**

> ⚠️ **Inconsistência Detectada**
> 
> A alíquota de ICMS interestadual para produto importado (origem 1) deve ser **4%**, não 12%.
> 
> **Base Legal:** Resolução do Senado Federal nº 13/2012
> 
> **Sugestão:** Corrigir a alíquota para 4% ou verificar se existe benefício fiscal específico.

---

## Formas de Uso

### 1. Interface Web (AgentOS)
Acesse pelo navegador, faça upload das notas e converse com o agente.

### 2. API REST
Integração direta com seu ERP ou sistema fiscal.

```bash
POST /audit
Content-Type: multipart/form-data
file: nota_fiscal.xml

# Retorna JSON com todas as inconsistências
```

### 3. PDF de Laudo
Gere laudos profissionais para apresentar a clientes ou órgãos fiscalizadores.

---

## Tecnologia

- **LLM:** Google Gemini 2.0 Flash
- **Framework:** Agno (AgentOS)
- **Base Vetorial:** PostgreSQL + pgvector
- **API:** FastAPI (Python)

---

## Próximos Passos

Interessado em testar? Entre em contato para:

- ✅ Demonstração personalizada
- ✅ Período de testes gratuito
- ✅ Integração com seu sistema

---

**Agente Fiscal Inteligente**  
*Auditoria tributária com IA - Menos erros, menos multas, mais tranquilidade.*
