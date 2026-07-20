"""Agent tools with fixed gate requirements (synthetic schema only)."""

from __future__ import annotations

from dataclasses import dataclass

from approval_maze.roles import Role


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    required_gates: frozenset[Role]


# Three tools — keep frozen for micro scope.
TOOLS: dict[str, ToolSpec] = {
    "read_doc": ToolSpec(
        name="read_doc",
        description="Read an internal synthetic document",
        required_gates=frozenset({Role.RINGI}),
    ),
    "send_external": ToolSpec(
        name="send_external",
        description="Send data outside the company boundary",
        required_gates=frozenset({Role.HOUMU, Role.JOUSHIS}),
    ),
    "change_prod": ToolSpec(
        name="change_prod",
        description="Mutate a production configuration",
        required_gates=frozenset({Role.RINGI, Role.JOUSHIS, Role.GENBA}),
    ),
}


def get_tool(name: str) -> ToolSpec:
    try:
        return TOOLS[name]
    except KeyError as exc:
        known = ", ".join(sorted(TOOLS))
        raise KeyError(f"unknown tool {name!r}; known: {known}") from exc
