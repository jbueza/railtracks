from .base import RCError


class NodeInvocationError(RCError):
    """
    Raised during node for execution problems in graph, including node or orchestration failures.
    For example, bad config, missing required parameters, or structural errors.
    """

    def __init__(
        self, message: str = None, notes: list[str] = None, fatal: bool = False
    ):
        super().__init__(message)
        self.notes = notes or []
        self.fatal = fatal

    def __str__(self):
        base = super().__str__()
        if self.notes:
            notes_str = (
                "\n"
                + self._color("Tips to debug:\n", self.GREEN)
                + "\n".join(self._color(f"- {note}", self.GREEN) for note in self.notes)
            )
            return f"\n{self._color(base, self.RED)}{notes_str}"
        return self._color(base, self.RED)


class GlobalTimeOutError(RCError):
    """
    Raised on global timeout for whole execution.
    """

    def __init__(self, timeout: float):
        super().__init__(f"Execution timed out after {timeout} seconds")


class LLMError(RCError):
    """
    Raised when an error occurs during LLM invocation or completion.
    """

    pass
