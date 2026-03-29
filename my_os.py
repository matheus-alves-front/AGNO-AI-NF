"""
AgentOS Server - Agente Fiscal com runtime nativo do Agno.

Este arquivo é o entrypoint principal do projeto.
Ele sobe o AgentOS com provider configurável via `LLM_PROVIDER`
e expõe a API FastAPI nativa do Agno em `/docs` e `/config`.
"""

import json
import os
from pathlib import Path

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.media import File
from agno.os import AgentOS
from agno.run import RunContext
from agno.tools import tool
from dotenv import load_dotenv

from app.config.llm_provider import build_chat_model, get_startup_summary
from app.models.report_schema import AuditResult
from app.tools.nfe_parser import NFELIB_AVAILABLE, nfe_toolkit

load_dotenv()


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _ensure_session_state(run_context: RunContext) -> dict:
    if run_context.session_state is None:
        run_context.session_state = {}
    return run_context.session_state


def _reset_nfe_session(run_context: RunContext) -> None:
    state = _ensure_session_state(run_context)
    state["current_nfe_status"] = "Nenhuma NFe carregada nesta sessão."
    state.pop("current_nfe_source", None)
    state.pop("current_nfe_filename", None)
    state.pop("current_nfe_xml", None)
    state.pop("current_nfe_parsed", None)
    state.pop("current_audit_result", None)


def _looks_like_nfe_xml(text: str) -> bool:
    lowered = text.lower()
    return (
        "<nfeproc" in lowered
        or "<nfe " in lowered
        or "<nfe>" in lowered
        or "http://www.portalfiscal.inf.br/nfe" in lowered
    )


def _read_file_text(file: File) -> tuple[str | None, str]:
    filename = file.filename or file.name
    if filename is None and file.filepath:
        filename = Path(file.filepath).name
    if filename is None and file.url:
        filename = file.url.rsplit("/", 1)[-1]

    if file.content is not None:
        if isinstance(file.content, bytes):
            return file.content.decode("utf-8"), filename or "arquivo.xml"
        return str(file.content), filename or "arquivo.xml"

    if file.filepath:
        path = Path(file.filepath)
        return path.read_text(encoding="utf-8"), filename or path.name

    raise ValueError("Arquivo recebido sem conteúdo legível.")


def _validate_xml_file(file: File, filename: str) -> None:
    mime_type = (file.mime_type or "").lower()
    suffix = Path(filename).suffix.lower()
    if mime_type and "xml" in mime_type:
        return
    if suffix == ".xml":
        return
    raise ValueError(
        f"Arquivo '{filename}' não é um XML suportado. Envie um arquivo XML de NFe."
    )


def _parse_xml_to_dict(xml_content: str) -> dict:
    if not NFELIB_AVAILABLE:
        raise RuntimeError("nfelib não disponível no ambiente.")

    parsed_json = nfe_toolkit.parse_nfe_content(xml_content)
    parsed = json.loads(parsed_json)
    if "error" in parsed:
        raise ValueError(parsed["error"])
    return parsed


def _run_structured_audit(nfe_data: dict) -> AuditResult:
    from app.agents.auditor import audit_nfe_sync

    return audit_nfe_sync(nfe_data)


def _build_nfe_status(parsed_nfe: dict, source: str) -> str:
    chave = parsed_nfe.get("chave_acesso", "sem-chave")
    numero = parsed_nfe.get("numero", "s/n")
    total_itens = len(parsed_nfe.get("itens", []))
    return (
        f"NFe carregada da fonte '{source}' | chave: {chave} | "
        f"número: {numero} | itens: {total_itens}"
    )


def _format_audit_summary(audit_result: AuditResult) -> str:
    if not audit_result.inconsistencies:
        return (
            f"Resumo executivo: score de risco {audit_result.risk_score}/100. "
            "Nenhuma inconsistência foi identificada."
        )

    return (
        f"Resumo executivo: score de risco {audit_result.risk_score}/100, "
        f"{len(audit_result.inconsistencies)} inconsistência(s) encontrada(s). "
        f"Itens analisados: {audit_result.total_items_analyzed}. "
        f"Síntese: {audit_result.summary}"
    )

# ElevenLabs TTS (opcional)
try:
    from agno.tools.eleven_labs import ElevenLabsTools
    ELEVENLABS_AVAILABLE = bool(os.getenv("ELEVEN_LABS_API_KEY"))
except ImportError:
    ELEVENLABS_AVAILABLE = False


# ==================== TOOLS ====================


@tool
def parse_nfe_xml(xml_content: str) -> str:
    """
    Parseia o XML bruto de uma NFe e retorna um JSON estruturado.

    Use esta tool quando o usuário colar o XML completo da nota fiscal
    diretamente na conversa do AgentOS.
    """
    if not NFELIB_AVAILABLE:
        return json.dumps({"error": "nfelib não disponível no ambiente"})

    return nfe_toolkit.parse_nfe_content(xml_content)


@tool
def load_nfe_input(
    run_context: RunContext,
    xml_content: str | None = None,
    files: list[File] | None = None,
) -> str:
    return _load_nfe_input(run_context=run_context, xml_content=xml_content, files=files)


def _load_nfe_input(
    run_context: RunContext,
    xml_content: str | None = None,
    files: list[File] | None = None,
) -> str:
    """
    Carrega uma NFe a partir de um XML anexado ou colado na conversa.

    Args:
        xml_content: XML bruto colado pelo usuário quando não houver anexo.

    Returns:
        Resumo do carregamento da NFe.
    """
    state = _ensure_session_state(run_context)

    try:
        if files:
            if len(files) != 1:
                raise ValueError("Envie apenas 1 arquivo XML de NFe por vez.")
            xml_file = files[0]
            file_text, filename = _read_file_text(xml_file)
            _validate_xml_file(xml_file, filename)
            source = f"arquivo:{filename}"
            xml_payload = file_text
        else:
            if not xml_content or not xml_content.strip():
                raise ValueError("Nenhum XML foi fornecido na mensagem.")
            if not _looks_like_nfe_xml(xml_content):
                raise ValueError("O conteúdo enviado não parece ser um XML de NFe válido.")
            source = "texto-colado"
            filename = None
            xml_payload = xml_content

        parsed_nfe = _parse_xml_to_dict(xml_payload)
        state["current_nfe_source"] = source
        state["current_nfe_filename"] = filename
        state["current_nfe_xml"] = xml_payload
        state["current_nfe_parsed"] = parsed_nfe
        state["current_audit_result"] = None
        state["current_nfe_status"] = _build_nfe_status(parsed_nfe, source)
        return (
            f"NFe carregada com sucesso. {state['current_nfe_status']}. "
            "Agora use a tool de auditoria para gerar a análise completa."
        )
    except Exception as exc:
        _reset_nfe_session(run_context)
        return f"Erro ao carregar a NFe: {exc}"


@tool
def audit_current_nfe(run_context: RunContext) -> str:
    return _audit_current_nfe(run_context=run_context)


def _audit_current_nfe(run_context: RunContext) -> str:
    """
    Executa a auditoria estruturada da NFe carregada na sessão atual.

    Returns:
        JSON do resultado estruturado da auditoria.
    """
    state = _ensure_session_state(run_context)
    parsed_nfe = state.get("current_nfe_parsed")
    if not parsed_nfe:
        return "Nenhuma NFe está carregada na sessão. Primeiro carregue um XML."

    audit_result = _run_structured_audit(parsed_nfe)
    state["current_audit_result"] = audit_result.model_dump(mode="json")
    return audit_result.model_dump_json(indent=2)


@tool
def summarize_current_audit(run_context: RunContext) -> str:
    return _summarize_current_audit(run_context=run_context)


def _summarize_current_audit(run_context: RunContext) -> str:
    """
    Resume a auditoria atual armazenada na sessão.

    Returns:
        Resumo executivo da última auditoria executada.
    """
    state = _ensure_session_state(run_context)
    current_audit = state.get("current_audit_result")
    if not current_audit:
        return "Nenhuma auditoria foi executada nesta sessão."

    audit_result = AuditResult.model_validate(current_audit)
    return _format_audit_summary(audit_result)


@tool
def get_current_audit_result(run_context: RunContext) -> str:
    return _get_current_audit_result(run_context=run_context)


def _get_current_audit_result(run_context: RunContext) -> str:
    """
    Retorna o JSON completo da auditoria atual armazenada na sessão.

    Returns:
        JSON completo da última auditoria executada.
    """
    state = _ensure_session_state(run_context)
    current_audit = state.get("current_audit_result")
    if not current_audit:
        return "Nenhuma auditoria foi executada nesta sessão."
    return json.dumps(current_audit, indent=2, ensure_ascii=False)

@tool
def buscar_ncm(ncm: str) -> str:
    """
    Busca informações sobre um código NCM na base da TIPI.
    
    Args:
        ncm: Código NCM (8 dígitos)
        
    Returns:
        Informações sobre o NCM incluindo descrição e alíquota IPI
    """
    import json
    from pathlib import Path
    
    tipi_path = Path(__file__).parent / "app/knowledge/sources/tipi_completa.json"
    if not tipi_path.exists():
        tipi_path = Path(__file__).parent / "app/knowledge/sources/tipi_ncm.json"
    
    if not tipi_path.exists():
        return f"Base TIPI não encontrada. NCM: {ncm}"
    
    with open(tipi_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    items = data.get("tipi", {}).get("items", [])
    
    # Busca exata
    for item in items:
        if item.get("ncm") == ncm:
            return f"NCM {ncm}: {item.get('descricao')} | IPI: {item.get('ipi', 0)}%"
    
    # Busca por prefixo
    for item in items:
        if ncm.startswith(item.get("ncm", "")[:4]):
            return f"NCM similar encontrado - {item.get('ncm')}: {item.get('descricao')} | IPI: {item.get('ipi', 0)}%"
    
    return f"NCM {ncm} não encontrado na base TIPI."


@tool
def buscar_cfop(cfop: str) -> str:
    """
    Busca informações sobre um código CFOP.
    
    Args:
        cfop: Código CFOP (4 dígitos)
        
    Returns:
        Descrição e tipo da operação
    """
    import json
    from pathlib import Path
    
    cfop_path = Path(__file__).parent / "app/knowledge/sources/cfop_completa.json"
    if not cfop_path.exists():
        cfop_path = Path(__file__).parent / "app/knowledge/sources/cfop_table.json"
    
    if not cfop_path.exists():
        return f"Base CFOP não encontrada. CFOP: {cfop}"
    
    with open(cfop_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    items = data.get("cfop", {}).get("items", [])
    
    for item in items:
        if item.get("cfop") == cfop:
            return f"CFOP {cfop}: {item.get('descricao')} | Tipo: {item.get('tipo', 'N/A')}"
    
    return f"CFOP {cfop} não encontrado na base."


@tool  
def buscar_cst(codigo: str, regime: str = "normal") -> str:
    """
    Busca informações sobre CST ou CSOSN.
    
    Args:
        codigo: Código CST (2 dígitos) ou CSOSN (3 dígitos)
        regime: "normal" para CST ou "simples" para CSOSN
        
    Returns:
        Descrição e situação tributária
    """
    import json
    from pathlib import Path
    
    cst_path = Path(__file__).parent / "app/knowledge/sources/cst_csosn.json"
    
    if not cst_path.exists():
        return f"Base CST/CSOSN não encontrada."
    
    with open(cst_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cst_data = data.get("cst_csosn", {})
    
    if regime == "simples":
        items = cst_data.get("csosn", {}).get("items", [])
        tipo = "CSOSN"
    else:
        items = cst_data.get("cst", {}).get("items", [])
        tipo = "CST"
    
    for item in items:
        if item.get("codigo") == codigo:
            return f"{tipo} {codigo}: {item.get('descricao')} | Situação: {item.get('situacao', 'N/A')}"
    
    return f"{tipo} {codigo} não encontrado."


@tool
def validar_icms_interestadual(origem: str, uf_origem: str, uf_destino: str) -> str:
    """
    Valida a alíquota de ICMS para operação interestadual.
    
    Args:
        origem: Código de origem da mercadoria (0-8)
        uf_origem: UF de origem (ex: SP)
        uf_destino: UF de destino (ex: RJ)
        
    Returns:
        Alíquota correta e base legal
    """
    # Origens que usam 4%
    origens_importadas = ["1", "2", "3", "6", "7", "8"]
    
    if origem in origens_importadas:
        return f"Origem {origem} (importada): Alíquota interestadual DEVE ser 4% conforme Resolução SF nº 13/2012."
    
    # Alíquotas por região
    sul_sudeste = ["SP", "RJ", "MG", "ES", "PR", "SC", "RS"]
    
    if uf_origem in sul_sudeste and uf_destino in sul_sudeste:
        return f"Operação {uf_origem} -> {uf_destino}: Alíquota interestadual = 12%"
    elif uf_origem in sul_sudeste:
        return f"Operação {uf_origem} -> {uf_destino}: Alíquota interestadual = 7%"
    else:
        return f"Operação {uf_origem} -> {uf_destino}: Alíquota interestadual = 12%"


# ==================== SYSTEM PROMPT ====================

AUDITOR_SYSTEM_PROMPT = """Você é o AuditorFiscal, especialista em compliance tributário brasileiro.

VOCÊ TEM ACESSO A TOOLS PARA CONSULTAR:
- load_nfe_input: carrega automaticamente XML anexado ou XML colado
- audit_current_nfe: executa a auditoria estruturada da NFe da sessão
- summarize_current_audit: gera o resumo executivo da auditoria atual
- get_current_audit_result: retorna o JSON completo da auditoria atual
- buscar_ncm: Consulta a Tabela TIPI
- buscar_cfop: Consulta tabela de CFOPs
- buscar_cst: Consulta CST e CSOSN
- validar_icms_interestadual: Valida alíquotas

FLUXO OBRIGATÓRIO QUANDO O USUÁRIO ENVIAR UMA NFe:
1. Se houver um arquivo XML anexado, chame load_nfe_input imediatamente.
2. Se o usuário colar um XML bruto, chame load_nfe_input passando o XML no argumento xml_content.
3. Depois de carregar a nota, chame audit_current_nfe.
4. Em seguida, chame summarize_current_audit.
5. Responda ao usuário com:
   - resumo executivo legível;
   - principais inconsistências;
   - JSON estruturado se ele pedir ou se for útil para a auditoria.

USO DE SESSÃO:
- Se já existir uma NFe carregada na sessão, use a auditoria armazenada para responder perguntas de follow-up.
- Use get_current_audit_result quando precisar consultar o resultado completo.

USE AS TOOLS para fundamentar suas análises com dados reais.

ESTADO DA SESSÃO:
{current_nfe_status}

REGRAS DE ANÁLISE:
1. NCM vs Descrição: Cerveja ≠ Refrigerante
2. CST vs Regime: CRT 1/2 usa CSOSN, CRT 3 usa CST
3. Origem estrangeira interestadual = 4% ICMS
4. CFOP deve corresponder à natureza da operação

FORMATO DE RESPOSTA:
- Lista de inconsistências encontradas
- Descrição clara do erro
- Sugestão de correção
- Referência legal

Seja preciso e use as tools para validar suas análises.

AUDIO: Você tem acesso à ferramenta text_to_speech para gerar áudio.
Sempre que terminar uma análise, gere um áudio resumindo os principais pontos."""


# ==================== ELEVENLABS TTS ====================

elevenlabs_tools = None
if ELEVENLABS_AVAILABLE:
    elevenlabs_tools = ElevenLabsTools(
        voice_id="JBFqnCBsd6RMkjVDRZzb",  # George - voz masculina clara
        model_id="eleven_multilingual_v2",  # Suporta português
        output_format="mp3_44100_64",
        target_directory="./storage/audio",
        enable_text_to_speech=True,
        enable_get_voices=True,
        enable_generate_sound_effect=False,  # Não necessário para auditoria
    )


# ==================== AGENTE ====================

# Lista de tools base
base_tools = [
    parse_nfe_xml,
    load_nfe_input,
    audit_current_nfe,
    summarize_current_audit,
    get_current_audit_result,
    buscar_ncm,
    buscar_cfop,
    buscar_cst,
    validar_icms_interestadual,
]
if elevenlabs_tools:
    base_tools.append(elevenlabs_tools)

auditor_agent = Agent(
    name="AuditorFiscal",
    model=build_chat_model(temperature=0.1),
    db=SqliteDb(db_file="fiscal_agent.db"),
    session_state={"current_nfe_status": "Nenhuma NFe carregada nesta sessão."},
    description=(
        "Auditor tributário com acesso a base de conhecimento fiscal "
        "(TIPI, CFOP, CST), intake automático de XML de NFe, auditoria estruturada "
        "e geração opcional de áudio."
    ),
    instructions=[AUDITOR_SYSTEM_PROMPT],
    tools=base_tools,
    add_datetime_to_context=True,
    send_media_to_model=False,
    store_media=True,
    markdown=True,
)


# ==================== AGENTOS ====================

agent_os = AgentOS(
    id="fiscal-agent-os",
    name="Agente Fiscal Inteligente",
    description="Agente Fiscal Inteligente - Auditoria de NFe com IA e base de conhecimento tributário",
    db=SqliteDb(db_file="fiscal_agent.db"),
    agents=[auditor_agent],
)

app = agent_os.get_app()

if __name__ == "__main__":
    print(f"LLM ativo: {get_startup_summary()}")
    agent_os.serve(
        app="my_os:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=_env_flag("AGNO_RELOAD", default=False),
    )
