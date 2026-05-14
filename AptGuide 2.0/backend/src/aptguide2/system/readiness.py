from __future__ import annotations

from pydantic import BaseModel

from aptguide2.core.config import Settings


class DependencyCheck(BaseModel):
    name: str
    ok: bool
    required: bool = True
    detail: str = ""


class ReadinessReport(BaseModel):
    checks: list[DependencyCheck]

    @property
    def all_required_ok(self) -> bool:
        return all(check.ok for check in self.checks if check.required)


def build_readiness_report(settings: Settings | None = None) -> ReadinessReport:
    """Build a readiness report including the configured pipeline version."""
    if settings is None:
        settings = Settings()
    checks = [
        DependencyCheck(
            name="pipeline",
            ok=settings.pipeline_version == "harness_v1",
            detail=f"pipeline_version={settings.pipeline_version}",
        ),
    ]
    return ReadinessReport(checks=checks)


def render_markdown_report(report: ReadinessReport) -> str:
    lines = [
        "# Live Dependency Readiness Report",
        "",
        f"**All required dependencies ready:** {'YES' if report.all_required_ok else 'NO'}",
        "",
        "| Dependency | Required | Ready | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for check in report.checks:
        lines.append(
            f"| {check.name} | {'yes' if check.required else 'no'} | "
            f"{'yes' if check.ok else 'no'} | {check.detail} |"
        )
    lines.append("")
    return "\n".join(lines)
