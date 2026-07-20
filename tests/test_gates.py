"""Unapproved tool-calls must always be denied."""

from __future__ import annotations

import pytest

from approval_maze.engine import new_maze
from approval_maze.roles import Role
from approval_maze.tools import TOOLS


@pytest.mark.parametrize("tool_name", sorted(TOOLS))
def test_unapproved_tool_always_denied(tool_name: str) -> None:
    maze = new_maze()
    result = maze.try_tool(tool_name)
    assert result.allowed is False
    assert result.deny is not None
    assert result.deny.missing_roles
    required = TOOLS[tool_name].required_gates
    assert set(result.deny.missing_roles) == required


def test_send_external_needs_houmu_and_joushis() -> None:
    maze = new_maze()
    maze.grant_now(Role.HOUMU)
    result = maze.try_tool("send_external")
    assert result.allowed is False
    assert result.deny is not None
    assert result.deny.missing_roles == [Role.JOUSHIS]

    maze.grant_now(Role.JOUSHIS)
    result2 = maze.try_tool("send_external")
    assert result2.allowed is True
    assert result2.deny is None


def test_read_doc_allowed_after_ringi() -> None:
    maze = new_maze()
    assert maze.try_tool("read_doc").allowed is False
    maze.grant_now(Role.RINGI)
    assert maze.try_tool("read_doc").allowed is True


def test_change_prod_needs_three_roles() -> None:
    maze = new_maze()
    maze.grant_now(Role.RINGI)
    maze.grant_now(Role.JOUSHIS)
    r = maze.try_tool("change_prod")
    assert r.allowed is False
    assert r.deny is not None
    assert r.deny.missing_roles == [Role.GENBA]
    maze.grant_now(Role.GENBA)
    assert maze.try_tool("change_prod").allowed is True


def test_unknown_tool_raises() -> None:
    maze = new_maze()
    with pytest.raises(KeyError, match="unknown tool"):
        maze.try_tool("drop_database")
