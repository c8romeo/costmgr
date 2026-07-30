"""packages.cost_engine.ports.reversal_port — reversal sequence port (AD-22).

AD-22: Reversal construction and ownership.
  - Sign-negating reversal row + corrected business row share a correction_group_id.
  - (tenant_id, reverses_event_id) is unique.
  - M4 calls request_reversal; M11 authorizes and writes the sequence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class ReversalRequest:
    tenant_id: UUID
    period_key: str
    target_event_id: UUID
    reason: str
    actor_id: UUID


class ReversalPort(Protocol):
    def request_reversal(self, req: ReversalRequest) -> UUID:
        """Request a reversal. Returns the new correction_group_id.

        M11 (Epic 11) owns authorization. M4 invokes this; the engine never
        performs authorization itself.
        """
        ...
