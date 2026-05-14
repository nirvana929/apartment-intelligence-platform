import pytest

from aptguide2.harness.errors import StrategyNotFoundError
from aptguide2.harness.registry import StrategyRegistry


def test_register_and_get_strategy():
    registry = StrategyRegistry()
    strategy = object()
    registry.register("router", "rule_v1", strategy)
    assert registry.get("router", "rule_v1") is strategy


def test_missing_strategy_raises_clear_error():
    registry = StrategyRegistry()
    with pytest.raises(StrategyNotFoundError) as exc:
        registry.get("router", "missing")
    assert "router.missing" in str(exc.value)


def test_names_returns_registered_names_for_category():
    registry = StrategyRegistry()
    registry.register("router", "rule_v1", object())
    registry.register("router", "llm_v1", object())
    registry.register("reranker", "rule_v1", object())
    assert registry.names("router") == ["llm_v1", "rule_v1"]
