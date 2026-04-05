from __future__ import annotations

from domain.domain_service.conflict import ServiceConflicts
from domain.error import DomainError, ErrorCode


class ConflictError(DomainError):
    def __init__(self, conflicts: ServiceConflicts) -> None:
        self.conflicts = conflicts
        super().__init__(
            ErrorCode.SCHEDULING_CONFLICT, "Service has scheduling conflicts"
        )
