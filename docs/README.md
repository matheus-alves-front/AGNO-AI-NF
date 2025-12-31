# 🤖 Agente Fiscal Inteligente

Sistema SaaS de auditoria automatizada de Notas Fiscais Eletrônicas (NFe) usando IA Generativa (Google Gemini).

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![Gemini](https://img.shields.io/badge/LLM-Gemini%202.0-orange)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20+%20pgvector-blue)

---

## 📋 O que faz?

- **Ingere** arquivos XML de NFe v4.00
- **Audita** usando IA híbrida (regras + análise semântica)
- **Identifica** inconsistências tributárias (NCM, CST, CFOP, alíquotas)
- **Retorna** resultados estruturados (JSON) ou laudos em PDF
- **Explica** erros citando a base legal

---

## 🛠️ Stack Tecnológica

| Componente | Tecnologia |
|------------|------------|
| LLM | Google Gemini 2.0 Flash |
| Framework | Agno + FastAPI |
| Parser NFe | nfelib |
| Vector DB | PostgreSQL + pgvector |
| Validação | Pydantic v2 |

---

## 🚀 Quick Start

### Pré-requisitos

- Python 3.12+
- Docker e Docker Compose
- Chave de API do Google Gemini

### 1. Clone o repositório

```bash
git clone <seu-repo>
cd AI-NF
```

### 2. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` e adicione sua chave do Gemini:

```env
GOOGLE_API_KEY=sua-chave-aqui
DATABASE_URL=postgresql://fiscal_user:fiscal_pass@localhost:5432/fiscal_agent
```

### 3. Suba o banco de dados

```bash
docker compose up -d
```

Aguarde alguns segundos e verifique se está rodando:

```bash
docker compose ps
```

### 4. Crie um ambiente virtual e instale dependências

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 5. Carregue a base de conhecimento

```bash
python scripts/load_knowledge.py
```

Este script irá:
- Baixar/gerar dados da TIPI (NCMs)
- Gerar tabela completa de CFOPs (600+)
- Carregar tudo no PostgreSQL com embeddings

### 6. Rode a API

```bash
python -m app.main
```

A API estará disponível em: **http://localhost:8000**

---

## 📡 Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/` | Health check e info |
| `GET` | `/health` | Status do serviço |
| `POST` | `/audit` | Audita uma NFe (XML) → JSON |
| `POST` | `/audit/batch` | Audita múltiplas NFes |
| `POST` | `/audit/pdf` | Audita e retorna PDF |
| `POST` | `/parse` | Apenas parseia XML |

### Exemplo de uso com cURL

```bash
# Auditar uma NFe
curl -X POST "http://localhost:8000/audit" \
  -F "file=@nota_fiscal.xml"

# Gerar PDF
curl -X POST "http://localhost:8000/audit/pdf" \
  -F "file=@nota_fiscal.xml" \
  -o laudo_auditoria.pdf
```

### Exemplo com Python

```python
import httpx

with open("nota_fiscal.xml", "rb") as f:
    response = httpx.post(
        "http://localhost:8000/audit",
        files={"file": f}
    )
    result = response.json()
    print(f"Risk Score: {result['risk_score']}")
    print(f"Inconsistências: {len(result['inconsistencies'])}")
```

---

## 📊 Estrutura do Projeto

```
AI-NF/
├── app/
│   ├── main.py               # Entrypoint FastAPI
│   ├── agents/
│   │   ├── auditor.py        # Agente principal (Gemini)
│   │   └── reviewer.py       # Agente de double-check
│   ├── tools/
│   │   ├── nfe_parser.py     # Parser NFe (nfelib)
│   │   └── pdf_generator.py  # Gerador de laudos PDF
│   ├── models/
│   │   ├── report_schema.py  # AuditResult, TaxInconsistency
│   │   └── nfe_schema.py     # Schemas da NFe
│   └── knowledge/
│       ├── rules_rag.py      # PgVector + Gemini embeddings
│       └── sources/          # Dados fiscais (JSON)
├── scripts/
│   ├── download_tipi.py      # Download TIPI (NCMs)
│   ├── download_cfop.py      # Gera CFOPs completos
│   ├── load_knowledge.py     # Ingestão no PgVector
│   └── stress_test.py        # Teste de carga
├── tests/
│   ├── test_integration.py
│   └── fixtures/
├── docker-compose.yml        # PostgreSQL + pgvector
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## 🧪 Testes

```bash
# Rodar testes unitários
pytest tests/ -v

# Rodar stress test (API deve estar rodando)
python scripts/stress_test.py
```

---

## 🐳 Docker (Produção)

```bash
# Build da imagem
docker build -t fiscal-agent .

# Rodar com Docker Compose (app + db)
docker compose -f docker-compose.yml up -d
```

---

## 📖 Documentação da API

Com a API rodando, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🔧 Configuração Avançada

### Variáveis de Ambiente

| Variável | Descrição | Default |
|----------|-----------|---------|
| `GOOGLE_API_KEY` | Chave API Gemini | *obrigatório* |
| `DATABASE_URL` | URL do PostgreSQL | `postgresql://fiscal_user:fiscal_pass@localhost:5432/fiscal_agent` |
| `AGNO_DEBUG` | Modo debug | `false` |
| `PORT` | Porta da API | `8000` |

### Ajuste de Performance

No arquivo `app/agents/auditor.py`, você pode ajustar:

```python
# Temperatura mais baixa = menos criativo, mais consistente
temperature=0.1

# Modelo (opções: gemini-2.0-flash, gemini-1.5-pro)
model_id="gemini-2.0-flash"
```

---

## 📝 Tipos de Inconsistências Detectadas

| Tipo | Descrição |
|------|-----------|
| `ncm_mismatch` | NCM não corresponde ao produto |
| `cst_invalid` | CST inválido para a operação |
| `csosn_invalid` | CSOSN usado por empresa regime normal |
| `cfop_error` | CFOP inconsistente |
| `cest_missing` | CEST obrigatório ausente |
| `aliquot_error` | Alíquota incorreta |
| `origin_mismatch` | Origem vs alíquota interestadual |

---

## 🤝 Contribuição

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Add nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

---

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

---

## 🆘 Suporte

Encontrou um bug? Abra uma [issue](../../issues).

---

**Desenvolvido com ❤️ e IA**
