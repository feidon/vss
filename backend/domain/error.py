from __future__ import annotations

from enum import Enum


class ErrorCode(Enum):
    NOT_FOUND = "NOT_FOUND"
    VALIDATION = "VALIDATION"
    CONFLICT = "CONFLICT"
    NO_ROUTE = "NO_ROUTE"


class DomainError(Exception):
    def __init__(self, code: ErrorCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
