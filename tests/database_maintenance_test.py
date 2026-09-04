from pathlib import Path

from server_store.database_maintenance import main_py_running


def test_main_py_running(tmp_path: Path):
    process = tmp_path / "123"
    process.mkdir()
    (process / "cmdline").write_bytes(b"/usr/bin/python3\0/opt/app/main.py\0")
    assert main_py_running(tmp_path) is True


def test_main_py_not_running(tmp_path: Path):
    process = tmp_path / "456"
    process.mkdir()
    (process / "cmdline").write_bytes(b"/usr/bin/python3\0/opt/app/sync_push.py\0")
    assert main_py_running(tmp_path) is False
