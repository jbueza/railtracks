from ..nodes.nodes import Node


class Task:
    """A simple class used to represent a task to be completed by the executor of choice."""

    def __init__(
        self,
        request_id: str,
        node: Node,
    ):
        self.request_id = request_id
        self.node = node

    @property
    def invoke(self):
        """The callable that this task is representing."""
        return self.node.invoke
