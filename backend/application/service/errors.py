from __future__ import annotations

from domain.domain_service.conflict import ServiceConflicts
from domain.error import DomainError, ErrorCode


class ConflictError(DomainError):
    def __init__(
        self,
        conflicts: ServiceConflicts,
        service_names: dict[int, str],
    ) -> None:
        self.conflicts = conflicts
        self.service_names = service_names
        super().__init__(
            ErrorCode.SCHEDULING_CONFLICT, "Service has scheduling conflicts"
        )
