"""DES clock + queue behavior."""

from __future__ import annotations

from approval_maze.des import DiscreteEventClock, EventKind
from approval_maze.engine import new_maze
from approval_maze.roles import Role


def test_arrival_enqueues_and_approve_clears() -> None:
    clock = DiscreteEventClock()
    clock.schedule(0.0, EventKind.ARRIVAL, role=Role.HOUMU, tool="send_external", request_id="r1")
    clock.schedule(2.0, EventKind.APPROVE, role=Role.HOUMU, request_id="r1")
    clock.run_until(0.0)
    assert len(clock.queues[Role.HOUMU]) == 1
    clock.run_until(2.0)
    assert len(clock.queues[Role.HOUMU]) == 0
    assert ("r1", Role.HOUMU) in clock.approved
    assert clock.now == 2.0


def test_denied_tool_creates_waiting_queue() -> None:
    maze = new_maze()
    maze.try_tool("send_external")
    waiting = {r for r, q in maze.clock.queues.items() if q}
    assert waiting == {Role.HOUMU, Role.JOUSHIS}
