"""Terminate simulator processes belonging to one Gazebo partition."""

import os
from pathlib import Path
import signal
import time


def partition_processes(partition, proc_root=Path('/proc')):
    """Return process IDs whose environment has the exact GZ partition."""
    expected = f'GZ_PARTITION={partition}'.encode()
    matches = []
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == os.getpid():
            continue
        try:
            environment = (entry / 'environ').read_bytes().split(b'\0')
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if expected in environment:
            matches.append(pid)
    return sorted(matches)


def terminate_partition(partition, wait_seconds=2.0):
    """Stop every process isolated in one Gazebo transport partition."""
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGKILL):
        processes = partition_processes(partition)
        if not processes:
            return
        for pid in processes:
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + wait_seconds
        while time.monotonic() < deadline:
            if not partition_processes(partition):
                return
            time.sleep(0.05)
