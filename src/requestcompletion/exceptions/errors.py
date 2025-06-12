from .base import RCError
from ..llm import MessageHistory, Message


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


class NodeCreationError(RCError):
    """
    Raised during node creation/validation before any execution begins.
    For example, bad config, missing required parameters, or structural errors.
    """

    def __init__(self, message=None, notes=None):
        if message is None:
            message = "Something went wrong during node creation."
        super().__init__(message)
        self.notes = notes or []

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


class LLMError(RCError):
    """
    Raised when an error occurs during LLM invocation or completion.
    """

    def __init__(
        self,
        reason: str,
        exception_message: str = None,
        message_history: MessageHistory = None,
    ):
        self.reason = reason
        self.exception_message = exception_message
        self.message_history = message_history

        message = f"{self._color('LLM Error: ', self.BOLD_RED)}{self._color(reason, self.RED)}"
        super().__init__(message)

    def __str__(self):
        base = super().__str__()
        details = []
        if self.exception_message:
            details.append(f"{self._color('Exception message: ', self.BOLD_GREEN)}{self._color(self.exception_message, self.GREEN)}")
        if self.message_history:
            mh_str = str(self.message_history)
            indented_mh = "\n".join("    " + line for line in mh_str.splitlines())      # 2 indents (2-spaces) per indent
            details.append(self._color('Message History:\n', self.BOLD_GREEN) + self._color(indented_mh, self.GREEN))
        if details:
            notes_str = (
                "\n"
                + self._color("Details:\n", self.BOLD_GREEN)
                + "\n".join(f"  {d}" for d in details)    # 
            )
            return f"\n{self._color(base, self.RED)}{notes_str}"
        return self._color(base, self.RED)


class GlobalTimeOutError(RCError):
    """
    Raised on global timeout for whole execution.
    """

    def __init__(self, timeout: float):
        super().__init__(f"Execution timed out after {timeout} seconds")


class FatalError(RCError):
    pass


if __name__ == "__main__":
    e = Exception("This is an exception")
    history = MessageHistory(
        [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hello"),
        ]
    )
    raise LLMError(
        reason="Model returned malformed response",
        exception_message=str(e),
        message_history=history,
    )