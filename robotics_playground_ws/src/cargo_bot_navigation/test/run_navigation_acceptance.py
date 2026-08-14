"""Run isolated navigation simulations and always terminate their process groups."""

import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys


TESTS = (
    ('test_launch_static_navigation.py', '117', 150),
    ('test_launch_static_navigation_turn.py', '118', 230),
    ('test_launch_static_navigation_long.py', '119', 250),
    ('test_launch_obstacle_navigation.py', '120', 220),
    ('test_launch_in_place_turn.py', '121', 150),
)


def stop_group(process):
    """Stop every process belonging to one isolated test invocation."""
    for sig, timeout in (
        (signal.SIGINT, 8),
        (signal.SIGTERM, 5),
        (signal.SIGKILL, 2),
    ):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            continue
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            return


def run_test(test_dir, filename, domain_id, timeout):
    """Run one launch test in a new session and return its exit status."""
    environment = os.environ.copy()
    environment['ROS_DOMAIN_ID'] = domain_id
    process = subprocess.Popen(
        [sys.executable, '-m', 'pytest', filename, '-q', '-s'],
        cwd=test_dir,
        env=environment,
        start_new_session=True,
    )
    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        return 124
    finally:
        stop_group(process)


def main():
    """Run all acceptance scenarios, stopping after the first failure."""
    parser = argparse.ArgumentParser()
    parser.add_argument('tests', nargs='*')
    parser.add_argument('--repeat', type=int, default=1)
    arguments = parser.parse_args()
    if arguments.repeat < 1:
        parser.error('--repeat must be at least 1')
    test_dir = Path(__file__).resolve().parent
    selected = set(arguments.tests)
    tests = tuple(
        test for test in TESTS
        if not selected or test[0] in selected
    )
    if not tests:
        return 2
    completed = 0
    for repetition in range(arguments.repeat):
        for filename, domain_id, timeout in tests:
            run_domain = str(int(domain_id) + repetition * len(TESTS))
            print(
                f'[{completed + 1}/{len(tests) * arguments.repeat}] '
                f'{filename} ROS_DOMAIN_ID={run_domain}',
                flush=True,
            )
            result = run_test(test_dir, filename, run_domain, timeout)
            if result != 0:
                return result
            completed += 1
    print(f'Navigation acceptance: {completed} isolated runs passed.', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
