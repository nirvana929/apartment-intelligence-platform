from aptguide2.system.readiness import (
    DependencyCheck,
    ReadinessReport,
    build_readiness_report,
    render_markdown_report,
)


def test_readiness_report_passes_only_when_all_required_checks_pass():
    report = ReadinessReport(checks=[
        DependencyCheck(name="milvus", ok=True, required=True, detail="ok"),
        DependencyCheck(name="lease", ok=False, required=True, detail="down"),
        DependencyCheck(name="optional", ok=False, required=False, detail="missing"),
    ])

    assert report.all_required_ok is False


def test_readiness_report_all_required_ok():
    report = ReadinessReport(checks=[
        DependencyCheck(name="milvus", ok=True, required=True, detail="ok"),
        DependencyCheck(name="optional", ok=False, required=False, detail="missing"),
    ])

    assert report.all_required_ok is True


def test_render_markdown_report_includes_blockers():
    report = ReadinessReport(checks=[
        DependencyCheck(name="milvus", ok=False, required=True, detail="connection refused"),
    ])

    markdown = render_markdown_report(report)

    assert "# Live Dependency Readiness Report" in markdown
    assert "connection refused" in markdown
    assert "NO" in markdown


def test_render_markdown_report_shows_yes_when_all_ready():
    report = ReadinessReport(checks=[
        DependencyCheck(name="milvus", ok=True, required=True, detail="ok"),
    ])

    markdown = render_markdown_report(report)

    assert "YES" in markdown
    assert "ok" in markdown


def test_build_readiness_report_includes_pipeline_check():
    from aptguide2.core.config import Settings

    settings = Settings(pipeline_version="harness_v1")
    report = build_readiness_report(settings)

    pipeline_checks = [c for c in report.checks if c.name == "pipeline"]
    assert len(pipeline_checks) == 1
    assert pipeline_checks[0].ok is True
    assert "harness_v1" in pipeline_checks[0].detail


def test_build_readiness_report_pipeline_not_harness():
    from aptguide2.core.config import Settings

    settings = Settings(pipeline_version="v1")
    report = build_readiness_report(settings)

    pipeline_checks = [c for c in report.checks if c.name == "pipeline"]
    assert len(pipeline_checks) == 1
    assert pipeline_checks[0].ok is False


def test_readiness_report_contains_standalone_dependencies():
    """Readiness report must include all 7 standalone dependency checks."""
    from aptguide2.core.config import Settings

    settings = Settings()
    report = build_readiness_report(settings)

    check_names = [c.name for c in report.checks]
    expected = ["pipeline", "auth_mode", "mysql_config", "redis_config",
                "lease_config", "milvus_config", "embedding_config"]
    assert check_names == expected

    # Every check must carry the category field
    for check in report.checks:
        assert check.category != "", f"{check.name} missing category"
