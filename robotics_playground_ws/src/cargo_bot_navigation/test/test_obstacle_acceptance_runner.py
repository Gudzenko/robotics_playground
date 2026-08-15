"""Run obstacle launch tests in isolated ROS processes."""

from pathlib import Path
import subprocess
import sys


def test_obstacle_scenarios_pass_in_isolated_processes():
    runner = Path(__file__).with_name('run_navigation_acceptance.py')
    result = subprocess.run(
        [
            sys.executable,
            str(runner),
        ],
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )

    assert result.returncode == 0, (result.stdout + result.stderr)[-12000:]
