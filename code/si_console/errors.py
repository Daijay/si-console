# This file holds the shared error shapes. It is copied from Autumn's
# autumn/schema.py and autumn/models.py, which both use the same idea:
# one error type per layer, with a message, a fix the user can act on,
# and a status code. Callers never have to know which provider failed.
# No secrets are ever put in an error message. Keys are never logged.
"""Shared error types. Every error carries a code, a message, and a remedy."""

from __future__ import annotations


class ConsoleError(Exception):
    """Base error for SI Console. Has a machine readable code."""

    def __init__(self, code: str, message: str, remedy: str = "", status: int = 500):
        self.code = code
        self.message = message
        self.remedy = remedy
        self.status = status
        super().__init__(message)

    def to_dict(self) -> dict:
        """One shape for HTTP answers and for log lines."""
        return {"code": self.code, "message": self.message, "remedy": self.remedy}


class ModelError(ConsoleError):
    """A DeepSeek call failed. Copied from Autumn models.ModelError."""

    def __init__(self, message: str, remedy: str = "", status: int = 502):
        super().__init__("MODEL_ERROR", message, remedy, status)


class EscalationNeeded(ModelError):
    """T1 is exhausted or denied: the task goes to escalate_to_human
    (MODEL_TIERS.md "Qwen4 Max -> escalate_to_human")."""

    def __init__(self, message: str, remedy: str = ""):
        super().__init__(message, remedy or "Escalate to the human at the console.", 503)
        self.code = "ESCALATE"


class ZeroPathNeeded(ModelError):
    """T3 is exhausted: the caller must use a $0 code path instead
    (voice_intents.py or a prewritten narration sentence)."""

    def __init__(self, message: str, remedy: str = ""):
        super().__init__(
            message, remedy or "Use voice_intents.py or a prewritten sentence.", 503
        )
        self.code = "ZERO_PATH"


class VaultError(ConsoleError):
    """A vault read or write could not be done safely.

    Codes are copied from Autumn vault_writer.VaultWriteError, plus new
    ones for frontmatter work that Autumn never did:
      no_vault, outside_vault, missing_file, unreadable, not_found,
      ambiguous, bad_frontmatter, bad_status, bad_dependency,
      duplicate_task, vault_conflict, vault_write_fail
    """

    def __init__(self, code: str, message: str, remedy: str = "", status: int = 400):
        super().__init__(code, message, remedy, status)


class GuardError(ConsoleError):
    """GUARD blocked a call. See guard.py. The block is the safe answer."""

    def __init__(self, code: str, message: str, remedy: str = ""):
        super().__init__(code, message, remedy, 403)


class ToolError(ConsoleError):
    """A tool call failed validation or the tool itself failed."""

    def __init__(self, code: str, message: str, remedy: str = "", status: int = 400):
        super().__init__(code, message, remedy, status)


class SourceError(ConsoleError):
    """A source (vault scan, Bocha search, price file) failed.

    Copied from Autumn autumn/schema.py SourceError. Autumn fails loudly
    instead of showing an empty result, and SI Console keeps that rule.
    A failed source must never produce a fake all clear.
    """

    def __init__(self, source: str, message: str, remedy: str = ""):
        super().__init__("SOURCE_ERROR", f"[{source}] {message}", remedy, 502)
        self.source = source
