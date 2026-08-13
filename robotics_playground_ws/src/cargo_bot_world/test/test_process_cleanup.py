"""Tests for scoped Gazebo process discovery."""

from pathlib import Path

from cargo_bot_world.process_cleanup import partition_processes


def write_environment(root, pid, values):
    process = root / str(pid)
    process.mkdir()
    (process / 'environ').write_bytes(b'\0'.join(values) + b'\0')


def test_partition_processes_matches_only_exact_partition(tmp_path):
    write_environment(tmp_path, 101, [b'GZ_PARTITION=test_a', b'OTHER=value'])
    write_environment(tmp_path, 102, [b'GZ_PARTITION=test_b'])
    write_environment(tmp_path, 103, [b'GZ_PARTITION=test_a_extra'])
    (tmp_path / 'not_a_pid').mkdir()

    assert partition_processes('test_a', Path(tmp_path)) == [101]
