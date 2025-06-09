from __future__ import annotations


from pydantic import BaseModel, Field

from typing import Callable, Coroutine

from .utils.logging.config import allowable_log_levels


# There may be moments when you are confused what should be in this config object vs. what should
class ExecutorConfig:

    def __init__(
        self,
        *,
        timeout: float = 50.0,
        end_on_error: bool = False,
        logging_setting: allowable_log_levels = "VERBOSE",
        subscriber: (
            Callable[[str], None] | Callable[[str], Coroutine[None, None, None]]
        ),
    ):
        """
        ExecutorConfig is special configuration object designed to allow customization of the executor in the RC system.

        Args:
            timeout (float): The maximum number of seconds to wait for a response to your top level request
            end_on_error (bool): If true, the executor will stop execution when an exception is encountered.
            logging_setting (allowable_log_levels): The setting for the level of logging you would like to have.
            subscriber (Callable or Coroutine): A function or coroutine that will handle streaming messages.

        """

    timeout: float = Field(
        default=50,
        description="The maximum number of time in seconds you would like to wait for a response.",
    )
    end_on_error: bool = Field(
        default=False,
        description="If true the executor will stop execution when an error is encountered.",
    )
    logging_setting: allowable_log_levels = Field(
        default="VERBOSE",
        description="The setting for the level of logging you would like to have.",
    )
