from aptguide2.persistence.models import Base


def test_required_tables_are_declared() -> None:
    assert {
        "aptguide_sessions",
        "aptguide_recent_messages",
        "aptguide_pending_actions",
        "aptguide_user_profiles",
        "aptguide_memory_candidates",
        "aptguide_handoff_tickets",
        "aptguide_operator_messages",
        "aptguide_audit_log",
    }.issubset(Base.metadata.tables.keys())
