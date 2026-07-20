"""Load and run synthetic approval scenarios."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
import json
from pathlib import Path
from typing import Any

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


ROLE_BY_LABEL = {r.value: r for r in Role}


def _parse_scenario(payload: Any) -> tuple[str, list[ScenarioStep]]:
    if not isinstance(payload, dict):
        raise ValueError("scenario must be a JSON object")
    name = payload.get("name")
    raw_steps = payload.get("steps")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("scenario.name must be a non-empty string")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise ValueError("scenario.steps must be a non-empty list")

    steps: list[ScenarioStep] = []
    for index, raw in enumerate(raw_steps, start=1):
        if not isinstance(raw, dict) or not isinstance(raw.get("action"), str):
            raise ValueError(f"scenario step {index} must contain a string action")
        unknown = set(raw) - {"action", "expect_allow"}
        if unknown:
            raise ValueError(
                f"scenario step {index} has unknown fields: {', '.join(sorted(unknown))}"
            )
        expected = raw.get("expect_allow")
        if expected is not None and not isinstance(expected, bool):
            raise ValueError(f"scenario step {index}.expect_allow must be boolean")
        steps.append(ScenarioStep(raw["action"], expected))
    return name, steps


def load_scenario(path: Path | None = None) -> tuple[str, list[ScenarioStep]]:
    """Load a scenario from disk, or the example bundled in the wheel."""
    if path is None:
        source = files("approval_maze").joinpath("data/enterprise_demo.json")
        payload = json.loads(source.read_text(encoding="utf-8"))
    else:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    return _parse_scenario(payload)


def run_scenario(
    steps: list[ScenarioStep] | None = None,
    *,
    name: str | None = None,
) -> ScenarioResult:
    if steps is None:
        loaded_name, steps = load_scenario()
        name = name or loaded_name
    else:
        name = name or "custom"
    maze = new_maze()
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
            if label not in ROLE_BY_LABEL:
                failures.append(f"step {i}: unknown role {label!r}")
                continue
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
