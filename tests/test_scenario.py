"""Fixed enterprise_demo scenario must play end-to-end."""

from __future__ import annotations

from approval_maze.scenario import run_scenario


def test_enterprise_demo_completes() -> None:
    result = run_scenario()
    assert result.ok, result.failures
    assert result.steps_run >= 10
    # Must include both deny and allow moments for send_external
    joined = "\n".join(result.log)
    assert "DENIED send_external" in joined
    assert "ALLOWED send_external" in joined
    assert "ALLOWED change_prod" in joined
