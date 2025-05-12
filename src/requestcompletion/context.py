import contextvars

parent_id = contextvars.ContextVar("parent_id", default=None)
active_runner = contextvars.ContextVar("active_runner", default=None)
config = contextvars.ContextVar("executor_config", default=None)
streamer = contextvars.ContextVar("data_streamer", default=None)
