class WorkflowError(Exception):
    """
    Base exception for application-layer failures.

    Production-oriented improvement:
    Typed exceptions make error handling explicit. The presentation layer can
    turn these into stable error DTOs instead of leaking raw provider messages.

    Expansion point:
    - Add subclasses for auth, validation, quota, provider, or persistence
      failures as the workflow grows.
    """

    code = "WORKFLOW_ERROR"

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        if code:
            self.code = code


class ProviderUnavailableError(WorkflowError):
    """
    Raised when a concrete infrastructure provider cannot complete an operation.

    The use case catches these around optional/fallback-friendly steps such as
    partial STT and TTS segment synthesis.
    """

    code = "PROVIDER_UNAVAILABLE"
