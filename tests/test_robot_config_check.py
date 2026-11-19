import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_robot_config import check  # noqa: E402


def test_virtual_config_passes():
    assert check(ROOT / "config/robot/virtual") == []


def test_untaught_real_config_is_rejected():
    errors = check(ROOT / "config/robot/real")
    assert any("cup_pick.joint" in e for e in errors)
    assert any("coffee_start" in e for e in errors)


def test_taught_values_pass(tmp_path):
    (tmp_path / "poses.yaml").write_text("poses:\n  home:\n    joint: [0, 0, 90, 0, 90, 0]\n")
    (tmp_path / "io.yaml").write_text("outputs:\n  coffee_start: 1\ninputs:\n  coffee_ready: 1\n")
    assert check(tmp_path) == []
