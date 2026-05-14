"""Wiring guard tests for AptGuide 2.0 mainline integration.

These tests prove that the current code does NOT touch legacy RAG.
They guard against old RAG being reintroduced after the v2 replacement.
"""

from pathlib import Path

from aptguide2.interaction.classifier import LLMInteractionClassifier

ROOT = Path(__file__).resolve().parents[3]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_api_app_does_not_import_legacy_pipeline() -> None:
    source = read("src/aptguide2/api/app.py")

    assert "from aptguide2.rag.pipeline import" not in source
    assert "run_pipeline(" not in source


def test_api_deps_does_not_register_rag_baseline_procedure() -> None:
    source = read("src/aptguide2/api/deps.py")

    assert "RagBaselineProcedure" not in source
    assert "harness.modules.rag.baseline" not in source


def test_default_pipeline_version_is_harness_mainline() -> None:
    from aptguide2.core.config import Settings

    assert Settings().pipeline_version == "harness_v1"


def test_rag_v2_does_not_import_legacy_pipeline_contracts() -> None:
    source = read("src/aptguide2/rag/pipeline_v2.py")

    assert "from aptguide2.rag.pipeline import PipelineResult" not in source


def test_pipeline_v2_does_not_call_mvp_retrieval_functions() -> None:
    source = read("src/aptguide2/rag/pipeline_v2.py")

    assert "from aptguide2.rag.kb_retrieval import retrieve_kb" not in source
    assert "from aptguide2.rag.room_retrieval import retrieve_rooms" not in source
    assert "retrieve_kb(qr" not in source
    assert "retrieve_rooms(qr" not in source


def test_pipeline_v2_uses_v2_native_retrieval() -> None:
    source = read("src/aptguide2/rag/pipeline_v2.py")

    assert "from aptguide2.rag.kb_v2 import retrieve_kb_v2" in source
    assert "from aptguide2.rag.room_v2 import retrieve_ranked_rooms_v2" in source


def test_runtime_does_not_expose_rag_baseline_adapter() -> None:
    baseline = ROOT / "src/aptguide2/harness/modules/rag/baseline.py"

    assert not baseline.exists()


def test_legacy_pipeline_not_importable_from_runtime() -> None:
    pipeline = ROOT / "src/aptguide2/rag/pipeline.py"

    assert not pipeline.exists()


def test_default_interaction_classifier_is_llm(monkeypatch):
    from aptguide2.api import deps
    from aptguide2.core.config import Settings

    deps.get_settings.cache_clear()

    monkeypatch.setattr(deps, "get_settings", lambda: Settings(llm_api_key="test-key"))
    classifier = deps.get_interaction_classifier()

    assert isinstance(classifier, LLMInteractionClassifier)
