import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from agno.media import File

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.report_schema import AuditResult


def reload_my_os(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    sys.modules.pop("my_os", None)
    return importlib.import_module("my_os")


def test_load_nfe_input_from_text(monkeypatch: pytest.MonkeyPatch):
    my_os = reload_my_os(monkeypatch)
    xml_content = Path("tests/fixtures/nfe_teste_erros.xml").read_text(encoding="utf-8")
    run_context = SimpleNamespace(session_state={})

    result = my_os._load_nfe_input(run_context=run_context, xml_content=xml_content)

    assert "NFe carregada com sucesso" in result
    assert run_context.session_state["current_nfe_source"] == "texto-colado"
    assert "current_nfe_parsed" in run_context.session_state
    assert run_context.session_state["current_audit_result"] is None


def test_load_nfe_input_from_file(monkeypatch: pytest.MonkeyPatch):
    my_os = reload_my_os(monkeypatch)
    run_context = SimpleNamespace(session_state={})
    nfe_file = File(filepath="tests/fixtures/nfe_teste_erros.xml")

    result = my_os._load_nfe_input(run_context=run_context, files=[nfe_file])

    assert "NFe carregada com sucesso" in result
    assert run_context.session_state["current_nfe_source"].startswith("arquivo:")
    assert run_context.session_state["current_nfe_filename"] == "nfe_teste_erros.xml"


def test_load_nfe_input_rejects_multiple_files(monkeypatch: pytest.MonkeyPatch):
    my_os = reload_my_os(monkeypatch)
    run_context = SimpleNamespace(session_state={})
    files = [
        File(filepath="tests/fixtures/nfe_teste_erros.xml"),
        File(filepath="tests/fixtures/nfe_teste_erros.xml"),
    ]

    result = my_os._load_nfe_input(run_context=run_context, files=files)

    assert "Envie apenas 1 arquivo XML" in result
    assert run_context.session_state["current_nfe_status"] == "Nenhuma NFe carregada nesta sessão."


def test_load_nfe_input_rejects_non_xml_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    my_os = reload_my_os(monkeypatch)
    run_context = SimpleNamespace(session_state={})
    invalid_file = tmp_path / "nota.txt"
    invalid_file.write_text("isso não é xml", encoding="utf-8")

    result = my_os._load_nfe_input(run_context=run_context, files=[File(filepath=str(invalid_file))])

    assert "não é um XML suportado" in result
    assert run_context.session_state["current_nfe_status"] == "Nenhuma NFe carregada nesta sessão."


def test_audit_current_nfe_stores_structured_result(monkeypatch: pytest.MonkeyPatch):
    my_os = reload_my_os(monkeypatch)
    run_context = SimpleNamespace(
        session_state={
            "current_nfe_parsed": {
                "chave_acesso": "35230512345678901234550010000001231234567890",
                "itens": [{"nItem": 1}],
            }
        }
    )

    dummy_audit = AuditResult(
        nfe_access_key="35230512345678901234550010000001231234567890",
        risk_score=72,
        total_items_analyzed=1,
        inconsistencies=[],
        summary="Auditoria de teste concluída.",
    )
    monkeypatch.setattr(my_os, "_run_structured_audit", lambda nfe_data: dummy_audit)

    result = my_os._audit_current_nfe(run_context=run_context)

    assert '"risk_score": 72' in result
    assert run_context.session_state["current_audit_result"]["risk_score"] == 72


def test_summarize_current_audit(monkeypatch: pytest.MonkeyPatch):
    my_os = reload_my_os(monkeypatch)
    audit_result = AuditResult(
        nfe_access_key="35230512345678901234550010000001231234567890",
        risk_score=18,
        total_items_analyzed=2,
        inconsistencies=[],
        summary="Nenhuma inconsistência encontrada.",
    )
    run_context = SimpleNamespace(
        session_state={"current_audit_result": audit_result.model_dump(mode="json")}
    )

    result = my_os._summarize_current_audit(run_context=run_context)

    assert "score de risco 18/100" in result
    assert "Nenhuma inconsistência" in result


def test_agent_media_configuration(monkeypatch: pytest.MonkeyPatch):
    my_os = reload_my_os(monkeypatch)

    assert my_os.auditor_agent.send_media_to_model is False
    assert my_os.auditor_agent.store_media is True
    assert my_os.auditor_agent.session_state["current_nfe_status"] == "Nenhuma NFe carregada nesta sessão."
