from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from requestcompletion.pubsub.publisher import RCPublisher


class InternalContext:
    """
    The InternalContext class is used to store global variables designed to be used in the RC system.

    The tooling in the class is very tightly dependent on the requirements of the RC system.
    """

    def __init__(
        self,
        publisher: RCPublisher,
        parent_id: str | None,
    ):
        self._parent_id = parent_id
        self._publisher = publisher

    # Not super pythonic but it allows us to slap in debug statements on the getters and setters with ease
    @property
    def parent_id(self):
        return self._parent_id

    @parent_id.setter
    def parent_id(self, value: str):
        self._parent_id = value

    @property
    def publisher(self):
        return self._publisher

    @publisher.setter
    def publisher(self, value: RCPublisher):
        self._publisher = value

    def prepare_new(self, new_parent_id: str) -> InternalContext:
        """
        Prepares a new InternalContext with a new parent ID.

        Note: the previous publisher will copied by reference into the next object.
        """

        return InternalContext(
            publisher=self._publisher,
            parent_id=new_parent_id,
        )
