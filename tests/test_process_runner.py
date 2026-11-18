import threading
import time

import pytest

from coffee_process.process_runner import ProcessRunner


class FakeRecipes:

    def __init__(self, steps):
        self.steps = steps

    def load_recipe(self, recipe_id):
        if recipe_id != "latte":
            raise FileNotFoundError(recipe_id)
        return {"id": recipe_id, "name": "Latte", "steps": self.steps}


class FakeRobot:

    def __init__(self):
        self.calls = []
        self.block = None
        self.fail = None
        self.moving = threading.Event()
        self._stopped = threading.Event()

    def move_to_pose(self, name, velocity, acceleration):
        self.calls.append(("move", name))
        self._stopped.clear()
        self.moving.set()
        if self.fail:
            raise self.fail
        while self.block is not None and not self.block.wait(0.01):
            if self._stopped.is_set():
                raise RuntimeError("stopped")

    def pause(self):
        self.calls.append(("pause",))

    def resume(self):
        self.calls.append(("resume",))

    def stop(self):
        self.calls.append(("stop",))
        self._stopped.set()


class FakeIO:

    def __init__(self):
        self.calls = []
        self.gripper_block = None
        self.gripper_started = threading.Event()

    def set_output(self, name, value):
        self.calls.append(("output", name, value))

    def set_gripper(self, command):
        self.calls.append(("gripper", command))
        self.gripper_started.set()
        if self.gripper_block is not None:
            self.gripper_block.wait(2)


MOVE = {"name": "Cup Pick", "action": "move", "pose": "cup_pick"}
GRIP_CLOSE = {"name": "Grip Cup", "action": "gripper", "command": "close"}
TO_MACHINE = {"name": "Coffee Machine", "action": "move", "pose": "coffee_machine"}
OUTPUT_ON = {"name": "Start Espresso", "action": "io", "output": "coffee_start", "value": True}


def wait_until(predicate, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    raise AssertionError("condition not met")


@pytest.fixture
def env():
    robot = FakeRobot()
    io = FakeIO()
    statuses = []
    recipes = FakeRecipes([MOVE, GRIP_CLOSE, OUTPUT_ON])
    runner = ProcessRunner(recipes, robot, io, on_status=statuses.append)
    yield runner, robot, io, recipes, statuses
    if robot.block is not None:
        robot.block.set()
    runner.join(2)


def ready(runner):
    runner.resume()
    runner.join(2)
    assert runner.start()[0] is True
    assert runner.state == "IDLE"


def test_initial_state_is_stopped(env):
    runner = env[0]
    assert runner.state == "STOPPED"


def test_first_reset_goes_home_only(env):
    runner, robot, *_ = env
    assert runner.resume()[0] is True
    runner.join(2)
    assert robot.calls == [("move", "home")]
    assert runner.state == "HOMED"


def test_full_recipe_done(env):
    runner, robot, io, *_ = env
    ready(runner)
    assert runner.execute("ORD-1", "latte") == (True, "accepted")
    runner.join(2)
    s = runner.snapshot()
    assert (s["state"], s["order_state"], s["progress"], s["order_id"]) == (
        "IDLE", "DONE", 100.0, "ORD-1")
    assert ("move", "cup_pick") in robot.calls
    assert io.calls == [("gripper", "close"), ("output", "coffee_start", True)]


def test_execute_unknown_recipe_rejected(env):
    runner = env[0]
    ready(runner)
    ok, _ = runner.execute("ORD-1", "mocha")
    assert ok is False
    assert runner.state == "IDLE"


def test_execute_rejected_when_not_idle(env):
    runner, robot, *_ = env
    ready(runner)
    robot.block = threading.Event()
    runner.execute("ORD-1", "latte")
    ok, _ = runner.execute("ORD-2", "latte")
    assert ok is False
    assert runner.snapshot()["order_id"] == "ORD-1"


def test_commands_rejected_in_wrong_state(env):
    runner = env[0]
    assert runner.pause()[0] is False
    assert runner.start()[0] is False
    assert runner.execute("ORD-1", "latte")[0] is False
    assert runner.state == "STOPPED"


def test_pause_resume_move_step(env):
    runner, robot, io, recipes, _ = env
    recipes.steps = [MOVE]
    ready(runner)
    robot.block = threading.Event()
    robot.moving.clear()
    runner.execute("ORD-1", "latte")
    wait_until(robot.moving.is_set)
    assert runner.pause()[0] is True
    assert runner.state == "PAUSED"
    assert runner.resume()[0] is True
    robot.block.set()
    runner.join(2)
    assert robot.calls.count(("pause",)) == 1
    assert robot.calls.count(("resume",)) == 1
    assert runner.snapshot()["order_state"] == "DONE"


def test_pause_during_wait_keeps_remaining_time(env):
    runner, robot, io, recipes, _ = env
    recipes.steps = [{"name": "Espresso Wait", "action": "wait", "seconds": 0.3}]
    ready(runner)
    started = time.monotonic()
    runner.execute("ORD-1", "latte")
    time.sleep(0.1)
    runner.pause()
    time.sleep(0.5)
    assert runner.state == "PAUSED"
    assert runner.snapshot()["order_state"] == "RUNNING"
    runner.resume()
    runner.join(2)
    assert time.monotonic() - started >= 0.8
    assert ("pause",) not in robot.calls
    assert runner.snapshot()["order_state"] == "DONE"


def test_pause_during_gripper_applies_after_step(env):
    runner, robot, io, recipes, _ = env
    recipes.steps = [GRIP_CLOSE, MOVE]
    ready(runner)
    io.gripper_block = threading.Event()
    runner.execute("ORD-1", "latte")
    wait_until(io.gripper_started.is_set)
    assert runner.pause()[0] is True
    io.gripper_block.set()
    time.sleep(0.1)
    assert ("move", "cup_pick") not in robot.calls
    assert runner.state == "PAUSED"
    runner.resume()
    runner.join(2)
    assert ("pause",) not in robot.calls
    assert ("resume",) not in robot.calls
    assert runner.snapshot()["order_state"] == "DONE"


def test_force_stop_running_marks_failed(env):
    runner, robot, io, recipes, _ = env
    recipes.steps = [MOVE]
    ready(runner)
    robot.block = threading.Event()
    robot.moving.clear()
    runner.execute("ORD-1", "latte")
    wait_until(robot.moving.is_set)
    assert runner.force_stop()[0] is True
    runner.join(2)
    s = runner.snapshot()
    assert (s["state"], s["order_state"]) == ("STOPPED", "FAILED")
    assert ("stop",) in robot.calls


def test_force_stop_while_paused(env):
    runner, robot, io, recipes, _ = env
    recipes.steps = [MOVE]
    ready(runner)
    robot.block = threading.Event()
    robot.moving.clear()
    runner.execute("ORD-1", "latte")
    wait_until(robot.moving.is_set)
    runner.pause()
    assert runner.force_stop()[0] is True
    runner.join(2)
    s = runner.snapshot()
    assert (s["state"], s["order_state"]) == ("STOPPED", "FAILED")
    assert ("stop",) in robot.calls
    assert ("resume",) not in robot.calls


def test_force_stop_during_wait(env):
    runner, robot, io, recipes, _ = env
    recipes.steps = [{"name": "Espresso Wait", "action": "wait", "seconds": 5}]
    ready(runner)
    runner.execute("ORD-1", "latte")
    time.sleep(0.05)
    runner.force_stop()
    runner.join(1)
    assert runner.state == "STOPPED"


def test_step_failure_stops(env):
    runner, robot, *_ = env
    ready(runner)
    robot.fail = RuntimeError("boom")
    runner.execute("ORD-1", "latte")
    runner.join(2)
    s = runner.snapshot()
    assert (s["state"], s["order_state"], s["message"]) == ("STOPPED", "FAILED", "boom")


def test_reset_with_cup_goes_to_trash(env):
    runner, robot, io, recipes, _ = env
    recipes.steps = [GRIP_CLOSE, TO_MACHINE]
    ready(runner)
    robot.block = threading.Event()
    runner.execute("ORD-1", "latte")
    wait_until(lambda: ("move", "coffee_machine") in robot.calls)
    runner.force_stop()
    runner.join(2)
    robot.block = None
    assert runner.resume()[0] is True
    runner.join(2)
    assert robot.calls[-2:] == [("move", "trash"), ("move", "home")]
    assert io.calls[-1] == ("gripper", "open")
    assert runner.state == "HOMED"


def test_force_stop_during_resetting(env):
    runner, robot, *_ = env
    robot.block = threading.Event()
    runner.resume()
    wait_until(robot.moving.is_set)
    assert runner.state == "RESETTING"
    assert runner.force_stop()[0] is True
    runner.join(2)
    assert runner.state == "STOPPED"


def test_next_order_requires_start_after_reset(env):
    runner = env[0]
    runner.resume()
    runner.join(2)
    assert runner.state == "HOMED"
    assert runner.execute("ORD-1", "latte")[0] is False
    assert runner.start()[0] is True
    assert runner.execute("ORD-1", "latte")[0] is True
    runner.join(2)


def test_status_callback_on_every_transition(env):
    runner, robot, io, recipes, statuses = env
    ready(runner)
    runner.execute("ORD-1", "latte")
    runner.join(2)
    states = []
    for status in statuses:
        if not states or states[-1] != status["state"]:
            states.append(status["state"])
    assert states == ["RESETTING", "HOMED", "IDLE", "RUNNING", "IDLE"]
    assert set(statuses[-1]) == {
        "order_id", "recipe_id", "state", "order_state", "current_step",
        "current_step_index", "total_steps", "progress", "message"}
