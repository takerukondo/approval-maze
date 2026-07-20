"""Core loop: tool-call → gate check → DES approvals → allow/deny."""

from __future__ import annotations

from dataclasses import dataclass, field

from approval_maze.des import DiscreteEventClock, EventKind
from approval_maze.roles import Role
from approval_maze.tools import TOOLS, ToolSpec, get_tool


@dataclass
class DenyReason:
    tool: str
    missing_roles: list[Role]
    message: str


@dataclass
class ToolCallResult:
    allowed: bool
    tool: str
    request_id: str
    deny: DenyReason | None = None
    granted_roles: list[Role] = field(default_factory=list)


@dataclass
class MazeState:
    """Playable state for one synthetic scenario."""

    clock: DiscreteEventClock
    granted: set[Role] = field(default_factory=set)
    request_counter: int = 0
    log: list[str] = field(default_factory=list)

    def _next_request_id(self, tool: str) -> str:
        self.request_counter += 1
        return f"req-{self.request_counter}-{tool}"

    def missing_for(self, tool: ToolSpec) -> list[Role]:
        return sorted(tool.required_gates - self.granted, key=lambda r: r.value)

    def try_tool(self, tool_name: str) -> ToolCallResult:
        tool = get_tool(tool_name)
        request_id = self._next_request_id(tool_name)
        missing = self.missing_for(tool)
        if missing:
            # Enqueue arrivals for missing roles so TUI shows waiting queues.
            for role in missing:
                self.clock.schedule(
                    0.0,
                    EventKind.ARRIVAL,
                    role=role,
                    tool=tool_name,
                    request_id=request_id,
                )
            self.clock.run_until(self.clock.now)
            reason = DenyReason(
                tool=tool_name,
                missing_roles=missing,
                message=(
                    f"DENIED {tool_name}: waiting on "
                    + " / ".join(r.value for r in missing)
                ),
            )
            self.log.append(reason.message)
            return ToolCallResult(
                allowed=False,
                tool=tool_name,
                request_id=request_id,
                deny=reason,
            )
        self.log.append(f"ALLOWED {tool_name} (all gates open)")
        return ToolCallResult(
            allowed=True,
            tool=tool_name,
            request_id=request_id,
            granted_roles=sorted(tool.required_gates, key=lambda r: r.value),
        )

    def schedule_approvals(self, role: Role, delay: float = 1.0) -> None:
        """Schedule a DES approve event for `role` (head of that queue or free grant)."""
        self.clock.schedule(delay, EventKind.APPROVE, role=role, request_id="")

    def advance(self, dt: float = 1.0) -> None:
        target = self.clock.now + dt
        before = set(self.granted)
        events = self.clock.run_until(target)
        for ev in events:
            if ev.kind == EventKind.APPROVE and ev.role is not None:
                self.granted.add(ev.role)
                self.log.append(
                    f"t={self.clock.now:.1f} APPROVED role={ev.role.value}"
                )
                # Clear any remaining queue items for this role after grant.
                self.clock.queues[ev.role].clear()
        newly = self.granted - before
        if newly and not events:
            # Direct grant path (approve with empty queue still opens gate).
            pass

    def grant_now(self, role: Role) -> None:
        """Immediate approval (for interactive play / tests)."""
        self.granted.add(role)
        self.clock.queues[role].clear()
        self.clock.approved.add(("*", role))
        self.log.append(f"t={self.clock.now:.1f} APPROVED role={role.value}")


def new_maze() -> MazeState:
    return MazeState(clock=DiscreteEventClock())


def known_tools() -> list[str]:
    return sorted(TOOLS)
