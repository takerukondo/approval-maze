"""Minimal TUI: show gates, queues, and tool deny/allow — not a CSS maze."""

from __future__ import annotations

from approval_maze.engine import MazeState, known_tools
from approval_maze.roles import ALL_ROLES, Role
from approval_maze.tools import TOOLS


def render(maze: MazeState) -> str:
    lines: list[str] = []
    lines.append("=== approval-maze ===")
    lines.append(f"DES clock t={maze.clock.now:.1f}")
    lines.append("")
    lines.append("Gates (稟議4ロール):")
    for role in ALL_ROLES:
        status = "OPEN" if role in maze.granted else "CLOSED"
        qlen = len(maze.clock.queues[role])
        waiting = ", ".join(
            f"{item.tool}@{item.request_id}" for item in maze.clock.queues[role]
        )
        wait_s = f" queue={qlen}" + (f" [{waiting}]" if waiting else "")
        lines.append(f"  [{status:6}] {role.value}{wait_s}")
    lines.append("")
    lines.append("Tools → required gates:")
    for name in known_tools():
        spec = TOOLS[name]
        need = "/".join(r.value for r in sorted(spec.required_gates, key=lambda r: r.value))
        missing = maze.missing_for(spec)
        mark = "ok" if not missing else "BLOCKED:" + "/".join(r.value for r in missing)
        lines.append(f"  {name:14} needs {need:20} → {mark}")
    lines.append("")
    if maze.log:
        lines.append("Log (recent):")
        for entry in maze.log[-8:]:
            lines.append(f"  · {entry}")
    return "\n".join(lines)


def interactive_loop(maze: MazeState) -> None:
    help_text = (
        "commands: tool <name> | approve <role> | advance [dt] | status | scenario | quit\n"
        f"tools: {', '.join(known_tools())}\n"
        f"roles: {', '.join(r.value for r in ALL_ROLES)}"
    )
    print(help_text)
    print(render(maze))
    role_map = {r.value: r for r in Role}
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not raw:
            continue
        if raw in {"q", "quit", "exit"}:
            break
        if raw in {"h", "help", "?"}:
            print(help_text)
            continue
        if raw in {"s", "status"}:
            print(render(maze))
            continue
        if raw == "scenario":
            from approval_maze.scenario import run_scenario

            result = run_scenario()
            print(f"scenario {result.name}: {'OK' if result.ok else 'FAIL'}")
            for line in result.log:
                print(f"  {line}")
            for f in result.failures:
                print(f"  !! {f}")
            continue
        parts = raw.split()
        cmd = parts[0]
        if cmd == "tool" and len(parts) >= 2:
            try:
                result = maze.try_tool(parts[1])
            except KeyError as exc:
                print(str(exc))
                continue
            if result.deny:
                print(result.deny.message)
            else:
                print(f"ALLOWED {result.tool}")
            print(render(maze))
        elif cmd == "approve" and len(parts) >= 2:
            label = parts[1]
            if label not in role_map:
                print(f"unknown role {label!r}; known: {', '.join(role_map)}")
                continue
            maze.grant_now(role_map[label])
            print(render(maze))
        elif cmd == "advance":
            if len(parts) >= 2:
                try:
                    dt = float(parts[1])
                except ValueError:
                    print(f"advance expects a number, got {parts[1]!r}")
                    continue
            else:
                dt = 1.0
            maze.advance(dt)
            print(render(maze))
        else:
            print("unknown command; try help")
