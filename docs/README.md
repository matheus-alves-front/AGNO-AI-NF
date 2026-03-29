# Agente Fiscal Inteligente

Sistema de auditoria tributária de NFe baseado em Agno AgentOS, com parsing de XML, tools fiscais, runtime FastAPI nativo do Agno e ingest opcional de base vetorial em PostgreSQL + pgvector.

## Estado atual

- Runtime principal: [my_os.py](/home/matheusalves/Dev/projects/AGNO-AI-NF/my_os.py)
- Serving: AgentOS nativo do Agno, com `/docs` e `/config`
- Providers de chat suportados: `gemini`, `ollama`, `huggingface`
- Embeddings para ingest: seguem o mesmo `LLM_PROVIDER`
- Banco vetorial: PostgreSQL 16 + pgvector via `docker-compose.yml`

## Stack

| Componente | Tecnologia |
|------------|------------|
| Runtime | Agno AgentOS |
| API | FastAPI nativo do Agno |
| Parsing NFe | `nfelib` |
| LLM | Gemini, Ollama ou Hugging Face |
| Vector DB | PostgreSQL + pgvector |
| Validação | Pydantic v2 |
| TTS opcional | ElevenLabs |

## Estrutura principal

```text
AGNO-AI-NF/
├── my_os.py
├── app/
│   ├── agents/
│   ├── config/
│   ├── knowledge/
│   ├── models/
│   └── tools/
├── scripts/
│   ├── download_tipi.py
│   ├── download_cfop.py
│   ├── init_db.sql
│   ├── load_knowledge.py
│   └── stress_test.py
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Quick start local

### 1. Preparar `.env`

```bash
cp .env.example .env
```

Escolha um provider e preencha só o bloco correspondente.

Exemplo Gemini:

```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=sua-chave
GEMINI_MODEL_ID=gemini-2.0-flash-001
GEMINI_EMBEDDING_MODEL_ID=gemini-embedding-001
DATABASE_URL=postgresql://fiscal_user:fiscal_pass@localhost:5432/fiscal_agent
EMBEDDING_DIMENSIONS=768
```

Exemplo Ollama local:

```env
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL_ID=llama3.2
OLLAMA_EMBEDDING_MODEL_ID=nomic-embed-text
DATABASE_URL=postgresql://fiscal_user:fiscal_pass@localhost:5432/fiscal_agent
EMBEDDING_DIMENSIONS=768
```

Exemplo Hugging Face:

```env
LLM_PROVIDER=huggingface
HF_TOKEN=seu-token
HUGGINGFACE_MODEL_ID=meta-llama/Llama-3.1-8B-Instruct
HUGGINGFACE_EMBEDDING_MODEL_ID=sentence-transformers/all-mpnet-base-v2
DATABASE_URL=postgresql://fiscal_user:fiscal_pass@localhost:5432/fiscal_agent
EMBEDDING_DIMENSIONS=768
```

### 2. Subir o banco vetorial

```bash
docker compose up -d
docker compose ps
```

### 3. Instalar dependências

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U -r requirements.txt
```

### 4. Rodar o AgentOS

```bash
python my_os.py
```

Rotas úteis:

- `http://localhost:8000/docs`
- `http://localhost:8000/config`

### 5. Testar o fluxo principal no AgentOS

O fluxo principal agora é:

1. anexar 1 arquivo XML de NFe no AgentOS e pedir a auditoria; ou
2. colar o XML bruto na conversa e pedir a auditoria.

Exemplos de mensagem:

```text
Anexei uma NFe em XML. Faça a auditoria fiscal completa.
```

```text
Analise este XML de NFe e faça a auditoria completa:
<cole aqui o XML>
```

Depois da primeira auditoria, você pode fazer follow-ups como:

```text
Qual item dessa nota teve maior risco fiscal?
```

## Ingest da base fiscal

O ingest segue o mesmo `LLM_PROVIDER` do runtime. O script:

1. baixa ou gera TIPI e CFOP;
2. lê os arquivos em `app/knowledge/sources/`;
3. gera embeddings;
4. carrega tudo em `tax_knowledge`.

Execute com o banco já no ar:

```bash
python scripts/load_knowledge.py
```

Se o provider estiver mal configurado, o script falha explicitamente antes de começar.

### Observação importante sobre dimensão

A tabela `tax_knowledge.embedding` usa `vector(768)` em [scripts/init_db.sql](/home/matheusalves/Dev/projects/AGNO-AI-NF/scripts/init_db.sql). Os defaults dos três providers foram escolhidos para 768 dimensões. Se você trocar o modelo de embedding por outro com dimensão diferente, precisa:

1. ajustar `EMBEDDING_DIMENSIONS`;
2. recriar ou migrar a coluna `embedding`;
3. recarregar a base.

## Fluxo operacional completo

```bash
cp .env.example .env
docker compose up -d
python3 -m venv .venv
source .venv/bin/activate
pip install -U -r requirements.txt
python scripts/load_knowledge.py
python my_os.py
```

Depois:

1. abra `http://localhost:8000/docs`;
2. valide `http://localhost:8000/config`;
3. interaja com o agente pelo runtime do AgentOS;
4. use `python scripts/stress_test.py` para um teste básico de disponibilidade.

## Docker

O container principal usa o mesmo entrypoint:

```bash
docker build -t fiscal-agent .
docker run --env-file .env -p 8000:8000 fiscal-agent
```

Para o banco vetorial, continue usando o `docker compose up -d`.

## Testes

```bash
pytest -q
```

Os testes locais cobrem:

- schemas Pydantic;
- factory de provider;
- bootstrap do `my_os.py`;
- disponibilidade de `/docs` e `/config` via TestClient.

Testes que chamam um provider real devem ser habilitados explicitamente no futuro. O fluxo padrão da suíte não depende de rede externa.

## Limitações atuais

- O runtime principal já está no AgentOS, mas ainda existe código legado em `app/main.py` que não é mais o caminho recomendado.
- O ingest depende de acesso externo aos modelos de embedding quando o provider escolhido não for totalmente local.
- A experiência final de produto e frontend ainda não foi consolidada neste ciclo; o foco aqui é infraestrutura, runtime e operação.
