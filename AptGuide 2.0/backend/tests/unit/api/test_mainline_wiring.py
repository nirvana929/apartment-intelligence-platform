"""Wiring guard tests for AptGuide 2.0 mainline integration.

These tests prove that the current code still touches legacy RAG.
They must FAIL on the current codebase and PASS after Tasks 2-4 are complete.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_api_app_does_not_import_legacy_pipeline() -> None:
    source = (ROOT / "src/aptguide2/api/app.py").read_text(encoding="utf-8")

    assert "from aptguide2.rag.pipeline import" not in source
    assert "run_pipeline(" not in source


def test_api_deps_does_not_register_rag_baseline_procedure() -> None:
    source = (ROOT / "src/aptguide2/api/deps.py").read_text(encoding="utf-8")

    assert "RagBaselineProcedure" not in source
    assert "harness.modules.rag.baseline" not in source


def test_default_pipeline_version_is_harness_mainline() -> None:
    from aptguide2.core.config import Settings

    assert Settings().pipeline_version == "harness_v1"


def test_rag_v2_does_not_import_legacy_pipeline_contracts() -> None:
    source = (ROOT / "src/aptguide2/rag/pipeline_v2.py").read_text(encoding="utf-8")

    assert "from aptguide2.rag.pipeline import PipelineResult" not in source
