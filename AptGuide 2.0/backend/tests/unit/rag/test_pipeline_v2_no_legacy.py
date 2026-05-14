"""Guard tests proving pipeline_v2 does not import or call legacy RAG.

These tests scan source files at import time. They fail if anyone reintroduces
old RAG imports or calls into the v2 pipeline or harness runtime.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_pipeline_v2_no_legacy_kb_import() -> None:
    source = read("src/aptguide2/rag/pipeline_v2.py")
    assert "from aptguide2.rag.kb_retrieval import" not in source


def test_pipeline_v2_no_legacy_room_import() -> None:
    source = read("src/aptguide2/rag/pipeline_v2.py")
    assert "from aptguide2.rag.room_retrieval import" not in source


def test_pipeline_v2_no_legacy_validation_import() -> None:
    source = read("src/aptguide2/rag/pipeline_v2.py")
    assert "from aptguide2.rag.validation import validate_room_candidates" not in source


def test_pipeline_v2_no_legacy_ranking_import() -> None:
    source = read("src/aptguide2/rag/pipeline_v2.py")
    assert "from aptguide2.rag.ranking import rank_rooms" not in source


def test_pipeline_v2_no_mvp_function_calls() -> None:
    source = read("src/aptguide2/rag/pipeline_v2.py")
    assert "retrieve_kb(" not in source
    assert "retrieve_rooms(" not in source
    assert "validate_room_candidates(" not in source
    assert "rank_rooms(" not in source


def test_harness_rag_v2_adapter_has_no_legacy_imports() -> None:
    source = read("src/aptguide2/harness/modules/rag/v2.py")
    assert "from aptguide2.rag.pipeline import" not in source
    assert "RagBaselineProcedure" not in source
    assert "rag_mvp_baseline" not in source


def test_eval_runner_has_no_legacy_imports() -> None:
    source = read("evals/runners/run_rag_v2.py")
    assert "from aptguide2.rag.pipeline import" not in source
    assert "from aptguide2.rag.kb_retrieval import" not in source
    assert "from aptguide2.rag.room_retrieval import" not in source


def test_deps_has_no_baseline_registration() -> None:
    source = read("src/aptguide2/api/deps.py")
    assert "RagBaselineProcedure" not in source
    assert "rag.baseline" not in source
    assert "rag_mvp_baseline" not in source
