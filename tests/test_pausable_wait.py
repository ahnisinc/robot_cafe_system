import threading

from robot_control.pausable_wait import wait_unless_paused


def test_returns_true_when_done():
    done = threading.Event()
    done.set()
    assert wait_unless_paused(done, lambda: False, timeout=1.0, tick=0.01) is True


def test_times_out_when_not_paused():
    assert wait_unless_paused(threading.Event(), lambda: False, timeout=0.05, tick=0.01) is False


def test_paused_time_not_counted():
    done = threading.Event()
    paused = {"value": True}

    def finish():
        paused["value"] = False
        done.set()

    threading.Timer(0.2, finish).start()
    assert wait_unless_paused(done, lambda: paused["value"], timeout=0.1, tick=0.01) is True
