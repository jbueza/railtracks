from .base import RCException


class RCFatalException(RCException):
    pass


class RCNodeCreationException(RCException):
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
            notes_str = "\n" + self.color("Tips to debug:\n", self.GREEN) + \
                        "\n".join(self.color(f"- {note}", self.GREEN) for note in self.notes)
            return f"\n{self.color(base, self.RED)}{notes_str}"
        return self.color(base, self.RED)
