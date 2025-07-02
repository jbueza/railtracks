from uuid import uuid4
import pytest
from dataclasses import dataclass
from copy import deepcopy
from requestcompletion.utils.profiling import Stamp
from requestcompletion.state.forest import Forest, AbstractLinkedObject
from requestcompletion.state.node import (
    LinkedNode, NodeForest
)
# ================= START fixtures for forest.py ====================
@dataclass(frozen=True)
class MockLinkedObject(AbstractLinkedObject):
    message: str


@pytest.fixture
def mock_linked_object():
    def _MockLinkedObject(identifier, message, stamp, parent):
        return MockLinkedObject(identifier, stamp, parent, message)
    return _MockLinkedObject

@pytest.fixture
def forest():
    return Forest[MockLinkedObject]()

@pytest.fixture
def unique_id():
    return lambda: str(uuid4())

@pytest.fixture
def example_structure():
    # (EXACTLY your earlier structure, so DRY reused as-is)
    identifier_1 = str(uuid4())
    identifier_2 = str(uuid4())
    identifier_3 = str(uuid4())

    linked1_1 = MockLinkedObject(
        identifier_1, Stamp(8091, 0, "Init"), parent=None, message="Hello world"
    )
    linked1_2 = MockLinkedObject(
        identifier_1, Stamp(8091, 1, "second try"), parent=linked1_1, message="Hello world..."
    )
    linked1_3 = MockLinkedObject(
        identifier_1, Stamp(8091, 5, "third try"), parent=linked1_2, message="Hello world...!"
    )

    linked2_1 = MockLinkedObject(
        identifier_2, Stamp(8091, 0, "Init"), parent=None, message="Hello world"
    )
    linked2_2 = MockLinkedObject(
        identifier_2, Stamp(8091, 1, "second try"), parent=linked2_1, message="Hello world..."
    )

    linked3_1 = MockLinkedObject(
        identifier_3, Stamp(8091, 1, "Init"), parent=None, message="Hello world"
    )
    linked3_2 = MockLinkedObject(
        identifier_3, Stamp(8091, 2, "second try"), parent=linked3_1, message="Hello world..."
    )
    linked3_3 = MockLinkedObject(
        identifier_3, Stamp(8091, 3, "third try"), parent=linked3_2, message="Hello world...!"
    )
    linked3_4 = MockLinkedObject(
        identifier_3, Stamp(8091, 4, "fourth try"), parent=linked3_3, message="Hello world...!!"
    )
    linked3_5 = MockLinkedObject(
        identifier_3, Stamp(8091, 5, "fifth try"), parent=linked3_4, message="Hello world...!!!"
    )

    heap = Forest[MockLinkedObject]()
    for l in [linked1_1, linked1_2, linked1_3, linked2_1, linked2_2, linked3_1, linked3_2, linked3_3, linked3_4, linked3_5]:
        heap._update_heap(l)

    return heap, {
        "1": [linked1_1, linked1_2, linked1_3],
        "2": [linked2_1, linked2_2],
        "3": [linked3_1, linked3_2, linked3_3, linked3_4, linked3_5],
    }

# ================ END fixtures for forest.py ====================

# =================== START fixtures for node.py ====================

@pytest.fixture
def dummy_node_factory():
    class DummyNode:
        _pretty = "dummy"  # class variable for pretty_name

        def __init__(self, uuid=None, details=None):
            self.uuid = uuid or str(uuid4())
            # to keep constructor signature compatible
            self._details = details or {"dummyfield": 123}
            self._copied = False

        @property
        def details(self):
            return self._details

        @classmethod
        def pretty_name(cls):
            # match the abstract method; returns a str (static/class)
            return cls._pretty

        def safe_copy(self):
            cls = self.__class__
            result = cls(self.uuid, details=deepcopy(self.details))
            result._copied = True
            return result

        def __repr__(self):
            return f"DummyNode<{self.uuid}>"
        
    def _factory(uuid=None, details=None, pretty="dummy"):
        # Dynamically make a new subclass with desired _pretty
        node_cls = type(f"TestNode_{pretty}", (DummyNode,), {"_pretty": pretty})
        return node_cls(uuid=uuid, details=details)
    return _factory

@pytest.fixture
def linked_node_factory(dummy_node_factory):
    def _factory(identifier, stamp, parent=None, pretty='dummy', details=None):
        node = dummy_node_factory(uuid=identifier, pretty=pretty, details=details)
        return LinkedNode(identifier=identifier, _node=node, stamp=stamp, parent=parent)
    return _factory

@pytest.fixture
def node_forest():
    return NodeForest()

# ================ END fixtures for node.py =========================