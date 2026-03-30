from __future__ import annotations

from domain.service.conflict import ServiceConflicts


class ConflictError(Exception):
    def __init__(self, conflicts: ServiceConflicts) -> None:
        self.conflicts = conflicts
        super().__init__("Service has scheduling conflicts")
