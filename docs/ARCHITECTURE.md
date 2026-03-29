# Architecture Guidelines: Fiscal Agent

## Visão geral

O projeto usa o AgentOS do Agno como runtime principal. O entrypoint é [my_os.py](/home/matheusalves/Dev/projects/AGNO-AI-NF/my_os.py), que monta um `AgentOS`, registra o agente fiscal e expõe a API FastAPI nativa do Agno.

Princípios desta arquitetura:

- `my_os.py` deve ser fino e focado em bootstrap.
- A resolução de provider deve ficar centralizada em [app/config/llm_provider.py](/home/matheusalves/Dev/projects/AGNO-AI-NF/app/config/llm_provider.py).
- O mesmo `LLM_PROVIDER` controla chat e embeddings.
- O ingest deve falhar cedo quando a configuração do provider estiver incompleta.
- A base vetorial deve permanecer compatível com a dimensão definida no schema SQL.

## Stack atual

| Camada | Tecnologia |
|--------|------------|
| Runtime | Agno AgentOS |
| API | FastAPI nativo do Agno |
| Parsing XML | `nfelib` |
| Modelos | Pydantic v2 |
| Vector store | PostgreSQL 16 + pgvector |
| Providers suportados | `gemini`, `ollama`, `huggingface` |

## Componentes

### Runtime

- [my_os.py](/home/matheusalves/Dev/projects/AGNO-AI-NF/my_os.py)
- Responsável por:
  - carregar env;
  - construir o modelo via factory;
  - registrar tools;
  - subir o `AgentOS`.

### Configuração de provider

- [app/config/llm_provider.py](/home/matheusalves/Dev/projects/AGNO-AI-NF/app/config/llm_provider.py)
- Responsável por:
  - resolver `LLM_PROVIDER`;
  - auto-detectar provider quando necessário;
  - validar env vars;
  - construir chat model;
  - construir embedder.

Precedência de auto-detect:

1. `gemini`
2. `ollama`
3. `huggingface`

Se `LLM_PROVIDER` estiver definido, ele sempre vence a auto-detecção.

### Agentes

- [app/agents/auditor.py](/home/matheusalves/Dev/projects/AGNO-AI-NF/app/agents/auditor.py)
- [app/agents/reviewer.py](/home/matheusalves/Dev/projects/AGNO-AI-NF/app/agents/reviewer.py)

Regras:

- devem usar `build_chat_model(...)`;
- devem retornar `response_model=AuditResult`;
- não devem instanciar provider diretamente.

### Knowledge / ingest

- [app/knowledge/rules_rag.py](/home/matheusalves/Dev/projects/AGNO-AI-NF/app/knowledge/rules_rag.py)
- [scripts/load_knowledge.py](/home/matheusalves/Dev/projects/AGNO-AI-NF/scripts/load_knowledge.py)
- [scripts/init_db.sql](/home/matheusalves/Dev/projects/AGNO-AI-NF/scripts/init_db.sql)

Regras:

- embeddings seguem o provider ativo;
- a dimensão esperada vem da config;
- o schema atual usa `vector(768)`;
- mudanças de modelo de embedding fora desse padrão exigem migração de banco.

## Variáveis públicas

### Core

```env
LLM_PROVIDER=gemini|ollama|huggingface
DATABASE_URL=postgresql://fiscal_user:fiscal_pass@localhost:5432/fiscal_agent
EMBEDDING_DIMENSIONS=768
HOST=0.0.0.0
PORT=8000
AGNO_RELOAD=false
```

### Gemini

```env
GOOGLE_API_KEY=...
GEMINI_MODEL_ID=gemini-2.0-flash-001
GEMINI_EMBEDDING_MODEL_ID=gemini-embedding-001
```

### Ollama

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_BASE_URL=
OLLAMA_API_KEY=
OLLAMA_MODEL_ID=llama3.2
OLLAMA_EMBEDDING_MODEL_ID=nomic-embed-text
```

### Hugging Face

```env
HF_TOKEN=...
HUGGINGFACE_API_KEY=
HUGGINGFACE_BASE_URL=
HUGGINGFACE_MODEL_ID=meta-llama/Llama-3.1-8B-Instruct
HUGGINGFACE_EMBEDDING_MODEL_ID=sentence-transformers/all-mpnet-base-v2
```

## Fluxo principal

```mermaid
flowchart TD
    A[Boot de my_os.py] --> B[Resolver provider em llm_provider.py]
    B --> C[Construir chat model]
    C --> D[Registrar Agent no AgentOS]
    D --> E[Subir FastAPI nativo do Agno]
    E --> F[/docs]
    E --> G[/config]
    H[scripts/load_knowledge.py] --> I[Construir embedder do mesmo provider]
    I --> J[Gerar embeddings]
    J --> K[Persistir em pgvector]
```

## Diretrizes de implementação

- Não adicionar novos entrypoints HTTP manuais para fluxos que já cabem no AgentOS.
- Não espalhar lógica de seleção de provider pelo código.
- Não assumir Gemini como default sem passar pela factory.
- Não trocar o modelo de embedding sem checar a dimensão da tabela.
- Qualquer novo provider deve entrar primeiro em `app/config/llm_provider.py`, depois em docs e testes.
