# approval-maze

An agent asks to send a file outside the company. Legal says yes; IT has not.
Should the tool call run?

`approval-maze` is a small, deterministic model of that gap between an agent's
intent and an organisation's permission to act. It turns four familiar Japanese
approval roles—稟議, 法務, 情シス, 現場—into gates in front of tool calls, then
shows exactly why a call is blocked and what approval is still missing.

I built it because most agent demos treat human approval as one boolean. Real
deployment work is messier: authority is split across people, approvals arrive
at different times, and "legal approved" does not imply "production access is
safe".

## Try it

Python 3.11+ is required. From the repository root:

```bash
python -m pip install -e . && approval-maze demo
```

The demo deliberately retries the same calls as approvals arrive:

```text
DENIED send_external: waiting on 法務 / 情シス
t=2.0 APPROVED role=法務
DENIED send_external: waiting on 情シス
t=3.0 APPROVED role=情シス
ALLOWED send_external (all gates open)
```

For a hands-on version, run `approval-maze play` and try commands such as
`tool send_external`, `approve 法務`, and `status`.

## Scenarios are data, not branches in the demo

The bundled run comes from
[`enterprise_demo.json`](src/approval_maze/data/enterprise_demo.json). A custom
scenario uses the same small JSON format:

```json
{
  "name": "one_gate",
  "steps": [
    {"action": "tool:read_doc", "expect_allow": false},
    {"action": "approve:稟議"},
    {"action": "tool:read_doc", "expect_allow": true}
  ]
}
```

Run it with `approval-maze demo --scenario one_gate.json`. The loader rejects
empty scenarios, unknown fields, and non-boolean expectations so a typo cannot
silently weaken an assertion.

## Design choices

- The simulator is deterministic. A discrete-event clock makes approval order
  and queue state reproducible in tests; no wall-clock sleeps are involved.
- Denial is the default. Every tool declares its required gates, and a missing
  gate produces an explicit reason rather than an implicit retry.
- The vocabulary is intentionally narrow. The project models one decision loop,
  not BPMN, identity, authentication, or a workflow editor.
- The included roles and policies are synthetic. They are a useful shape for a
  conversation, not a claim about how every Japanese company operates.

## Sharp edges

Approvals currently open a role globally for the life of one maze. They do not
expire, carry document scope, or distinguish two users. Queue arrivals are
modelled, but there is no cancellation or escalation. Those omissions keep the
state machine inspectable; they are also the first things I would change before
using this model as the basis of a real policy engine.

## Development

```bash
python -m pip install -e ".[dev]"
pytest -q
python -m build
```

The CI job installs the package, runs the tests, and executes the bundled demo.

MIT licensed.
