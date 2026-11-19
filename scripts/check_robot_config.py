"""실제 로봇 실행 전 설정 검사: TODO 값, 0으로 된 포즈가 남아 있으면 실패.

사용: python3 scripts/check_robot_config.py config/robot/real
"""

import sys
from pathlib import Path

import yaml


def check(config_dir):
    config_dir = Path(config_dir)
    errors = []

    poses = yaml.safe_load((config_dir / "poses.yaml").read_text())["poses"] or {}
    for name, pose in poses.items():
        for kind in ("joint", "cartesian"):
            values = (pose or {}).get(kind)
            if values is not None and all(float(v) == 0.0 for v in values):
                errors.append(f"poses.yaml: {name}.{kind} 가 전부 0 (티칭 필요)")

    io = yaml.safe_load((config_dir / "io.yaml").read_text()) or {}
    for group, mapping in io.items():
        for name, value in (mapping or {}).items():
            if not isinstance(value, int):
                errors.append(f"io.yaml: {group}.{name} = {value} (번호 필요)")

    return errors


if __name__ == "__main__":
    problems = check(sys.argv[1])
    for line in problems:
        print("  -", line)
    sys.exit(1 if problems else 0)
