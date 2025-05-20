import contextvars
import queue
import threading
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .run import Runner
    from .config import ExecutorConfig


active_runner = contextvars.ContextVar("active_runner", default=None)
config = contextvars.ContextVar("executor_config", default=None)
streamer = contextvars.ContextVar("data_streamer", default=None)

# TODO handle this whole issues around global configuration variables after
