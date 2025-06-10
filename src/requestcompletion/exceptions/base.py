class RCError(Exception):
    """
    A simple base class for all RCExceptions to inherit from.
    """

    RED = "\033[91m"
    GREEN = "\033[92m"
    RESET = "\033[0m"

    @classmethod
    def color(cls, text, color_code):
        return f"{color_code}{text}{cls.RESET}"
