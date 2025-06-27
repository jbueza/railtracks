from __future__ import annotations

from typing import Any, TYPE_CHECKING

from typing_extensions import Self



if TYPE_CHECKING:
    from requestcompletion.utils.profiling import Stamp


class Edge:
    def __init__(
            self,
            *,
            identifier: str | None = None,
            source: str | None = None,
            target: str,
            stamp: Stamp,
            details: dict[str, Any],
            parent: Self | None = None,
    ):
        self.identifier = identifier
        self.source = source
        self.target = target
        self.stamp = stamp
        self.details = details
        assert parent is None or parent.identifier == identifier, "The parent identifier must match the edge identifier"
        assert parent is None or (parent.source == source and parent.target == target), "The parent edge must have the same source and target"
        self.parent = parent



class Vertex:
    def __init__(
            self,
            *,
            identifier: str,
            node_type: str,
            stamp: Stamp,
            details: dict[str, Any],
            parent: Self | None,
    ):
        """
        The V
        """
        self.identifier = identifier
        self.node_type = node_type
        self.details = details
        self.stamp = stamp
        assert parent is None or parent.identifier == identifier, "The parent identifier must match the vertex identifier"
        self.parent = parent


