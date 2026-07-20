"""Fixed enterprise_demo scenario must play end-to-end."""

from __future__ import annotations

import json

import pytest

from approval_maze.scenario import load_scenario, run_scenario


def test_enterprise_demo_completes() -> None:
    result = run_scenario()
    assert result.ok, result.failures
    assert result.steps_run >= 10
    # Must include both deny and allow moments for send_external
    joined = "\n".join(result.log)
    assert "DENIED send_external" in joined
    assert "ALLOWED send_external" in joined
    assert "ALLOWED change_prod" in joined


def test_custom_scenario_is_loaded_from_json(tmp_path) -> None:
    path = tmp_path / "one_gate.json"
    path.write_text(
        json.dumps(
            {
                "name": "one_gate",
                "steps": [
                    {"action": "tool:read_doc", "expect_allow": False},
                    {"action": "approve:稟議"},
                    {"action": "tool:read_doc", "expect_allow": True},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    name, steps = load_scenario(path)
    result = run_scenario(steps, name=name)
    assert result.ok
    assert result.name == "one_gate"


@pytest.mark.parametrize(
    "payload, message",
    [
        ({"name": "empty", "steps": []}, "non-empty list"),
        (
            {"name": "bad", "steps": [{"action": "approve:法務", "typo": 1}]},
            "unknown fields",
        ),
    ],
)
def test_invalid_scenario_is_rejected(tmp_path, payload, message) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        load_scenario(path)
