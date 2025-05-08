import contextvars

parent_id = contextvars.ContextVar("parent_id")
active_runner = contextvars.ContextVar("active_runner")
