"""Minimal discrete-event simulation: clock + approval queues."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from heapq import heappop, heappush
from typing import Any

from approval_maze.roles import Role


class EventKind(str, Enum):
    ARRIVAL = "arrival"  # request enters a role queue
    APPROVE = "approve"  # role grants approval
    RELEASE = "release"  # gate opens after all required approvals


@dataclass(order=True)
class Event:
    time: float
    seq: int
    kind: EventKind = field(compare=False)
    role: Role | None = field(compare=False, default=None)
    tool: str | None = field(compare=False, default=None)
    request_id: str = field(compare=False, default="")
    payload: dict[str, Any] = field(compare=False, default_factory=dict)


@dataclass
class QueueItem:
    request_id: str
    tool: str
    arrived_at: float


class DiscreteEventClock:
    """Simple DES with per-role FIFO queues and scheduled approvals."""

    def __init__(self) -> None:
        self.now: float = 0.0
        self._seq: int = 0
        self._events: list[Event] = []
        self.queues: dict[Role, list[QueueItem]] = {r: [] for r in Role}
        self.approved: set[tuple[str, Role]] = set()  # (request_id, role)
        self.history: list[Event] = []

    def schedule(
        self,
        delay: float,
        kind: EventKind,
        *,
        role: Role | None = None,
        tool: str | None = None,
        request_id: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:
        self._seq += 1
        heappush(
            self._events,
            Event(
                time=self.now + delay,
                seq=self._seq,
                kind=kind,
                role=role,
                tool=tool,
                request_id=request_id,
                payload=payload or {},
            ),
        )

    def enqueue(self, role: Role, request_id: str, tool: str) -> None:
        self.queues[role].append(
            QueueItem(request_id=request_id, tool=tool, arrived_at=self.now)
        )

    def waiting_roles_for(self, request_id: str) -> list[Role]:
        out: list[Role] = []
        for role, q in self.queues.items():
            if any(item.request_id == request_id for item in q):
                out.append(role)
        return out

    def step(self) -> Event | None:
        if not self._events:
            return None
        event = heappop(self._events)
        self.now = event.time
        self.history.append(event)
        if event.kind == EventKind.ARRIVAL and event.role is not None:
            self.enqueue(event.role, event.request_id, event.tool or "")
        elif event.kind == EventKind.APPROVE and event.role is not None:
            q = self.queues[event.role]
            # Approve matching request if present, else head of queue.
            idx = next(
                (i for i, item in enumerate(q) if item.request_id == event.request_id),
                0 if q else None,
            )
            if idx is not None and q:
                item = q.pop(idx)
                self.approved.add((item.request_id, event.role))
        return event

    def run_until(self, t: float) -> list[Event]:
        fired: list[Event] = []
        while self._events and self._events[0].time <= t:
            ev = self.step()
            if ev is not None:
                fired.append(ev)
        self.now = max(self.now, t)
        return fired

    def drain(self) -> list[Event]:
        fired: list[Event] = []
        while self._events:
            ev = self.step()
            if ev is not None:
                fired.append(ev)
        return fired
