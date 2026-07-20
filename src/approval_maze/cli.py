"""CLI entrypoints for demo, scenario, and status."""

from __future__ import annotations

import argparse
import sys

from approval_maze.engine import new_maze
from approval_maze.scenario import run_scenario
from approval_maze.tui import interactive_loop, render


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="approval-maze",
        description=(
            "JP enterprise approval gates (稟議/法務/情シス/現場) as a DES maze "
            "for agent tool-calls. Synthetic policy only."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_demo = sub.add_parser("demo", help="run the fixed enterprise_demo scenario")
    p_demo.add_argument("--quiet", action="store_true")

    sub.add_parser("play", help="interactive TUI (tool / approve / advance)")

    p_try = sub.add_parser("try", help="try one tool-call against a fresh maze")
    p_try.add_argument("tool", choices=["read_doc", "send_external", "change_prod"])

    args = parser.parse_args(argv)

    if args.cmd == "demo":
        result = run_scenario()
        if not args.quiet:
            for line in result.log:
                print(line)
            print(f"\nscenario={result.name} steps={result.steps_run} ok={result.ok}")
            for f in result.failures:
                print(f"FAIL: {f}", file=sys.stderr)
        return 0 if result.ok else 1

    if args.cmd == "play":
        interactive_loop(new_maze())
        return 0

    if args.cmd == "try":
        maze = new_maze()
        result = maze.try_tool(args.tool)
        print(render(maze))
        if result.deny:
            print(result.deny.message)
            return 2
        print(f"ALLOWED {result.tool}")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
