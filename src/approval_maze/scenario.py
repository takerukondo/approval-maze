"""One synthetic enterprise demo scenario (not real company policy)."""

from __future__ import annotations

from dataclasses import dataclass

from approval_maze.engine import MazeState, ToolCallResult, new_maze
from approval_maze.roles import Role


@dataclass
class ScenarioStep:
    action: str  # tool:<name> | approve:<role> | advance:<dt>
    expect_allow: bool | None = None


@dataclass
class ScenarioResult:
    name: str
    ok: bool
    steps_run: int
    log: list[str]
    failures: list[str]


# Synthetic Acme-JP demo: agent tries external send before legal/IT approve.
SCENARIO_STEPS: list[ScenarioStep] = [
    ScenarioStep("tool:read_doc", expect_allow=False),  # needs 稟議
    ScenarioStep("approve:稟議"),
    ScenarioStep("tool:read_doc", expect_allow=True),
    ScenarioStep("tool:send_external", expect_allow=False),  # needs 法務+情シス
    ScenarioStep("approve:法務"),
    ScenarioStep("tool:send_external", expect_allow=False),  # still 情シス
    ScenarioStep("approve:情シス"),
    ScenarioStep("tool:send_external", expect_allow=True),
    ScenarioStep("tool:change_prod", expect_allow=False),  # needs 現場 too
    ScenarioStep("approve:現場"),
    ScenarioStep("tool:change_prod", expect_allow=True),
]


ROLE_BY_LABEL = {r.value: r for r in Role}


def run_scenario(
    steps: list[ScenarioStep] | None = None,
    *,
    name: str = "enterprise_demo",
) -> ScenarioResult:
    maze = new_maze()
    steps = steps or SCENARIO_STEPS
    failures: list[str] = []
    for i, step in enumerate(steps, start=1):
        if step.action.startswith("tool:"):
            tool = step.action.split(":", 1)[1]
            result = maze.try_tool(tool)
            if step.expect_allow is not None and result.allowed != step.expect_allow:
                failures.append(
                    f"step {i} {step.action}: expected allow={step.expect_allow}, "
                    f"got allow={result.allowed}"
                    + (
                        f" ({result.deny.message})"
                        if result.deny
                        else ""
                    )
                )
        elif step.action.startswith("approve:"):
            label = step.action.split(":", 1)[1]
            role = ROLE_BY_LABEL[label]
            maze.schedule_approvals(role, delay=1.0)
            maze.advance(1.0)
            if role not in maze.granted:
                maze.grant_now(role)
        elif step.action.startswith("advance:"):
            dt = float(step.action.split(":", 1)[1])
            maze.advance(dt)
        else:
            failures.append(f"step {i}: unknown action {step.action!r}")
    return ScenarioResult(
        name=name,
        ok=not failures,
        steps_run=len(steps),
        log=list(maze.log),
        failures=failures,
    )


def play_interactive_once() -> MazeState:
    """Seed maze for TUI / demo: no grants yet."""
    return new_maze()
