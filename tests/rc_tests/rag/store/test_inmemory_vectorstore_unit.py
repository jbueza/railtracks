import pytest
import numpy as np
from conftest import DummyEmbeddingService, DummyRecord, DummySearchResult, DummyMetric, dummy_uuid_str

# -------------- Auto-patch module dependencies (pytest-style) --------------
@pytest.fixture(autouse=True)
def patch_vectorstore_deps(monkeypatch):
    import requestcompletion.RAG.vector_store.in_memory as vsmem
    # Patch all dependencies in the *module under test's namespace*:
    monkeypatch.setattr(vsmem, "uuid_str", dummy_uuid_str)
    monkeypatch.setattr(vsmem, "BaseEmbeddingService", DummyEmbeddingService)
    monkeypatch.setattr(vsmem, "VectorRecord", DummyRecord)
    monkeypatch.setattr(vsmem, "SearchResult", DummySearchResult)
    monkeypatch.setattr(vsmem, "Metric", DummyMetric)
    # Dummy versions of vector utils
    monkeypatch.setattr(vsmem, "normalize_vector", lambda v: v/np.linalg.norm(v) if np.linalg.norm(v) else v)
    monkeypatch.setattr(vsmem, "distance", lambda a, b, metric="cosine": float(np.sum((np.array(a)-np.array(b))**2)) if metric == "l2" else -float(np.dot(a,b)))
    # No need to patch AbstractVectorStore if real base is abstract and not used directly

from requestcompletion.RAG.vector_store.in_memory import InMemoryVectorStore

# --------------------------- TESTS -----------------------------

@pytest.fixture
def store():
    return InMemoryVectorStore(
        embedding_service=DummyEmbeddingService(),
        metric="cosine",
        dim=3,
    )

def test_add_and_count(store):
    n = store.count()
    ids = store.add(["hello", "world"])
    assert len(ids) == 2
    assert store.count() == n + 2
    vr = DummyRecord(id="rec1", vector=[1,2,3], text="hi")
    ids2 = store.add([vr], embed=False)
    assert len(ids2) == 1
    assert store.count() == n + 3

def test_add_metadata_length_mismatch(store):
    with pytest.raises(ValueError):
        store.add(["a", "b"], metadata=[{}, {}, {}])

def test_search_text_and_vector(store):
    store.add(["abc", "def", "ghi"])
    results = store.search("abc", top_k=2, embed=True)
    assert len(results) == 2
    v = store.embedding_service.embed("def")
    results2 = store.search(v, top_k=1, embed=False)
    assert len(results2) == 1

def test_search_wrong_embed_flag(store):
    store.add(["text"])
    with pytest.raises(ValueError):
        store.search([1,2,3], embed=True)
    with pytest.raises(ValueError):
        store.search("text", embed=False)

def test_delete(store):
    ids = store.add(["x", "y"])
    deleted = store.delete([ids[0]])
    assert deleted == 1
    assert store.count() == 1
    deleted2 = store.delete(["nonexistent"])
    assert deleted2 == 0

def test_update_vector(store):
    ids = store.add(["orig"])
    new_vec = [9.0, 9.0, 9.0]
    store.update(ids[0], new_vec, embed=False)
    actual = store._vectors[ids[0]]
    assert np.allclose(actual, new_vec) or np.allclose(actual, np.array(new_vec)/np.linalg.norm(new_vec))

def test_update_text(store):
    ids = store.add(["orig"])
    store.update(ids[0], "new text", embed=True)
    assert store._record[ids[0]].text == "new text"

def test_update_keyerror(store):
    with pytest.raises(KeyError):
        store.update("notfound", [1,2,3], embed=False)

def test_update_wrong_embed_flag(store):
    ids = store.add(["a"])
    with pytest.raises(ValueError):
        store.update(ids[0], [1,2,3], embed=True)
    with pytest.raises(ValueError):
        store.update(ids[0], "foo", embed=False)