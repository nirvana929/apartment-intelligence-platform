from types import SimpleNamespace

from aptguide3.api.deps import _maybe_wrap_langsmith


class DummyClient:
    pass


def test_langsmith_wrapper_is_noop_when_disabled():
    client = DummyClient()
    settings = SimpleNamespace(
        langsmith_tracing=False,
        langsmith_project="aptguide3-local",
        service_name="aptguide3",
        environment="test",
    )

    assert _maybe_wrap_langsmith(client, settings) is client


def test_langsmith_wrapper_does_not_require_api_key_when_disabled():
    client = DummyClient()
    settings = SimpleNamespace(
        langsmith_tracing=False,
        langsmith_project="aptguide3-local",
        service_name="aptguide3",
        environment="test",
    )

    wrapped = _maybe_wrap_langsmith(client, settings)

    assert wrapped is client
