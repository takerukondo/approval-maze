# approval-maze

> **Status: experimental / alpha** — API, TUI, and scenario surface may change without notice.

**Aha:** agent tool-calls are gated by Japan enterprise 稟議4ロール（稟議 / 法務 / 情シス / 現場）on a discrete-event clock. Unapproved tools are refused with an explicit waiting-role reason.

## Not a BPMN clone

| Looks like | Actually |
|---|---|
| BPMN / BPSim approval viz | Fixed 4 roles, 3 tools, 1 scenario — no editor |
| CSS maze / queue toy | **Tool schema ↔ gate binding** + deterministic deny tests |
| Real 稟議 system | Synthetic policy only — no employer/client data |

Magic loop: `agent calls tool → missing role gate → DENIED → DES approval arrives → ALLOWED`.

## Requirements

- Python **≥ 3.11** (macOS `/usr/bin/python3` is often 3.9 — use `python3.11` or `uv venv --python 3.11`)

## Quick demo (30s)

```bash
python3.11 -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[dev]"
approval-maze demo
# or: python -m approval_maze.cli demo
```

Expected: `read_doc` / `send_external` / `change_prod` deny until the required roles open, then allow. Exit 0.

Interactive:

```bash
approval-maze play
# > tool send_external
# > approve 法務
# > approve 情シス
# > tool send_external
```

## Tools × gates (frozen)

| tool | required gates |
|---|---|
| `read_doc` | 稟議 |
| `send_external` | 法務 + 情シス |
| `change_prod` | 稟議 + 情シス + 現場 |

## Tests

```bash
pytest -q
```

Acceptance: unapproved tool-calls always deny (`tests/test_gates.py`).

## License

MIT — see `LICENSE`.

## Security

Synthetic fixtures only. Do not load real company 稟議 rules, org charts, or SSO.
