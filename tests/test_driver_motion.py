import threading

import pytest

from robot_driver.doosan_adapter import DoosanAdapter


class FakeDsr:

    def __init__(self, check_values):
        self.calls = []
        self.check_values = list(check_values)
        self.check_count = 0

    def amovej(self, pos, vel=None, acc=None):
        self.calls.append(("amovej", pos, vel, acc))
        return 0

    def amovel(self, pos, vel=None, acc=None):
        self.calls.append(("amovel", pos, vel, acc))
        return 0

    def check_motion(self):
        self.check_count += 1
        if len(self.check_values) > 1:
            return self.check_values.pop(0)
        return self.check_values[0]


def make_adapter(check_values):
    adapter = DoosanAdapter.__new__(DoosanAdapter)
    adapter.dsr = FakeDsr(check_values)
    adapter.available = True
    adapter.stop_event = threading.Event()
    return adapter


def test_move_joint_waits_until_idle():
    a = make_adapter([2, 2, 0])
    a.move_joint([0, 0, 90, 0, 90, 0], 30.0, 30.0)
    assert a.dsr.calls == [("amovej", [0, 0, 90, 0, 90, 0], 30.0, 30.0)]
    assert a.dsr.check_count == 3


def test_move_line_uses_async_motion():
    a = make_adapter([0])
    a.move_line([1, 2, 3, 4, 5, 6], 100.0, 50.0)
    assert a.dsr.calls == [("amovel", [1, 2, 3, 4, 5, 6], [100.0, 100.0], [50.0, 50.0])]


def test_move_joint_raises_when_stopped():
    a = make_adapter([2, 0])
    a.stop_event.set()
    with pytest.raises(RuntimeError, match="stopped"):
        a.move_joint([0] * 6, 30.0, 30.0)


def test_stop_during_motion_raises():
    a = make_adapter([2, 2, 0])
    original = a.dsr.check_motion

    def check_and_stop():
        value = original()
        if a.dsr.check_count == 2:
            a.stop_event.set()
        return value

    a.dsr.check_motion = check_and_stop
    with pytest.raises(RuntimeError, match="stopped"):
        a.move_joint([0] * 6, 30.0, 30.0)


def test_check_motion_failure_raises():
    a = make_adapter([-1])
    with pytest.raises(RuntimeError, match="check_motion failed"):
        a.move_joint([0] * 6, 30.0, 30.0)


def test_stop_event_cleared_on_new_motion():
    a = make_adapter([0])
    a.stop_event.set()
    a.clear_stop()
    a.move_joint([0] * 6, 30.0, 30.0)


def test_stop_waits_for_controller_idle():
    a = make_adapter([2, 2, 2, 0])
    a.stop_event.set()
    with pytest.raises(RuntimeError, match="stopped"):
        a._wait_motion(tick=0.001)
    assert a.dsr.check_count == 4


def test_latched_stop_prevents_new_motion():
    a = make_adapter([0])
    a.stop_event.set()
    with pytest.raises(RuntimeError, match="stopped"):
        a.move_joint([0] * 6, 30.0, 30.0)
    with pytest.raises(RuntimeError, match="stopped"):
        a.move_line([0] * 6, 30.0, 30.0)
    assert a.dsr.calls == []
