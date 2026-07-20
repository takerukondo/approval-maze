"""Fixed JP enterprise approval roles (稟議4ロール). Not a BPMN editor."""

from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    """The four gate roles. Order is display convention only."""

    RINGI = "稟議"  # business / budget approver
    HOUMU = "法務"  # legal
    JOUSHIS = "情シス"  # IT / security
    GENBA = "現場"  # field / ops owner


ALL_ROLES: tuple[Role, ...] = (
    Role.RINGI,
    Role.HOUMU,
    Role.JOUSHIS,
    Role.GENBA,
)
