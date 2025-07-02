import time
import threading
import pytest

from requestcompletion.utils.profiling import Stamp, StampManager
import pickle

# ================ Fixtures & Helpers ==================
@pytest.fixture
def stamp_fixture():
    return Stamp(time=10.0, step=1, identifier="foo")

@pytest.fixture
def another_stamp_fixture():
    return Stamp(time=15.5, step=1, identifier="bar")

@pytest.fixture
def stampmanager_fixture():
    return StampManager()
# ================= END Fixtures & Helpers =============

# ================= START Stamp tests ==================
def test_stamp_lt_orders_by_step(stamp_fixture, another_stamp_fixture):
    """__lt__ gives precedence to step before time"""
    s1 = Stamp(time=10, step=1, identifier="foo")
    s2 = Stamp(time=4, step=2, identifier="foo")
    assert s1 < s2

def test_stamp_lt_orders_by_time_on_same_step():
    s1 = Stamp(time=10, step=1, identifier="foo")
    s2 = Stamp(time=15, step=1, identifier="foo")
    assert s1 < s2

def test_stamp_hash_is_unique_for_unique_fields():
    s1 = Stamp(time=10, step=1, identifier="foo")
    s2 = Stamp(time=10, step=1, identifier="bar")
    assert hash(s1) != hash(s2)

def test_stamp_hash_matches_tuple(stamp_fixture):
    s = stamp_fixture
    assert hash(s) == hash((s.time, s.step, s.identifier))
# ================= END Stamp tests ====================

# ============ START StampManager tests ================
def test_create_stamp_basic(stampmanager_fixture):
    sm = stampmanager_fixture
    s = sm.create_stamp("first")
    assert isinstance(s, Stamp)
    assert s.step == 0
    assert s.identifier == "first"
    # Step increments
    s2 = sm.create_stamp("second")
    assert s2.step == 1

def test_create_stamp_step_logs(stampmanager_fixture):
    sm = stampmanager_fixture
    sm.create_stamp("msg1")
    sm.create_stamp("msg2")
    logs = sm.step_logs
    # Should contain two steps, each with the correct message
    assert logs[0] == ["msg1"]
    assert logs[1] == ["msg2"]

def test_stamp_creator_shared_step(stampmanager_fixture):
    sm = stampmanager_fixture
    creator = sm.stamp_creator()
    st1 = creator("a")
    st2 = creator("b")
    # Both should have the same 'step'
    assert st1.step == st2.step
    # They should differ in identifier
    assert st1.identifier == "a"
    assert st2.identifier == "b"
    # After stamp_creator was called, sm._step should have incremented by 1
    assert sm._step >= st2.step + 1

def test_stamp_creator_step_logs(stampmanager_fixture):
    sm = stampmanager_fixture
    creator = sm.stamp_creator()
    creator("foo")
    creator("bar")
    logs = sm.step_logs
    shared_step = next(iter(logs))
    # Both messages should be present in same list
    log_vals = list(logs.values())
    assert "foo" in log_vals[0]
    assert "bar" in log_vals[0]

def test_all_stamps_sorted_returns_sorted(stampmanager_fixture):
    sm = stampmanager_fixture
    s1 = sm.create_stamp("msg1")
    time.sleep(0.01)  # Ensure time difference
    s2 = sm.create_stamp("msg2")
    all_stamps = sm.all_stamps
    assert all_stamps[0].identifier == "msg1"
    assert all_stamps[1].identifier == "msg2"

def test_step_logs_is_deepcopy(stampmanager_fixture):
    sm = stampmanager_fixture
    sm.create_stamp("x")
    sl1 = sm.step_logs
    sl1[0].append("evil")
    assert sl1 != sm.step_logs  # Changing copy doesn't affect original

def test_all_stamps_is_deepcopy(stampmanager_fixture):
    sm = stampmanager_fixture
    sm.create_stamp("foo")
    all1 = sm.all_stamps
    all1[0].identifier = "evil"
    assert all1 != sm.all_stamps

def test_create_lock_returns_new_lock():
    lock_type = type(threading.Lock()) 
    l1 = StampManager._create_lock()
    l2 = StampManager._create_lock()
    assert isinstance(l1, lock_type)
    assert l1 is not l2

def test_stampmanager_pickle_roundtrip(stampmanager_fixture):
    lock_type = type(threading.Lock()) 
    sm = stampmanager_fixture
    sm.create_stamp("abc")
    pkl = pickle.dumps(sm)
    sm2 = pickle.loads(pkl)
    # _stamp_lock should be re-created, not shared
    assert isinstance(sm2._stamp_lock, lock_type)
    assert sm2.step_logs == sm.step_logs
# ============= END StampManager tests =================
