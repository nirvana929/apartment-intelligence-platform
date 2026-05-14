from __future__ import annotations

from pydantic import BaseModel

from aptguide2.core.config import Settings


class DependencyCheck(BaseModel):
    name: str
    ok: bool
    required: bool = True
    category: str = "runtime"
    detail: str = ""


class ReadinessReport(BaseModel):
    checks: list[DependencyCheck]

    @property
    def all_required_ok(self) -> bool:
        return all(check.ok for check in self.checks if check.required)


_VALID_AUTH_MODES = {"dev", "lease_token"}


def build_readiness_report(settings: Settings | None = None) -> ReadinessReport:
    """Build a readiness report for all configured dependencies.

    Each check validates configuration values without performing expensive
    live network probes so the endpoint stays fast.
    """
    if settings is None:
        settings = Settings()

    checks = [
        DependencyCheck(
            name="pipeline",
            ok=settings.pipeline_version == "harness_v1",
            category="pipeline",
            detail=f"pipeline_version={settings.pipeline_version}",
        ),
        DependencyCheck(
            name="auth_mode",
            ok=settings.auth_mode in _VALID_AUTH_MODES,
            category="auth",
            detail=f"auth_mode={settings.auth_mode}",
        ),
        DependencyCheck(
            name="mysql_config",
            ok=bool(settings.mysql_dsn and settings.mysql_dsn != "mysql+asyncmy://root:change-me@localhost:3306/aptguide2"),
            category="storage",
            detail="mysql_dsn is configured" if settings.mysql_dsn else "mysql_dsn is empty",
        ),
        DependencyCheck(
            name="redis_config",
            ok=bool(settings.redis_url),
            category="storage",
            detail="redis_url is configured" if settings.redis_url else "redis_url is empty",
        ),
        DependencyCheck(
            name="lease_config",
            ok=bool(settings.lease_base_url),
            category="integration",
            detail="lease_base_url is configured" if settings.lease_base_url else "lease_base_url is empty",
        ),
        DependencyCheck(
            name="milvus_config",
            ok=bool(settings.milvus_uri),
            category="storage",
            detail="milvus_uri is configured" if settings.milvus_uri else "milvus_uri is empty",
        ),
        DependencyCheck(
            name="embedding_config",
            ok=bool(settings.embedding_base_url and settings.embedding_model),
            category="integration",
            detail=f"embedding_model={settings.embedding_model}",
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
