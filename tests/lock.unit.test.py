# tests/lock.unit.test.py
import sqlite3
from pathlib import Path

import pytest

import apiscope.lock as lock_module
from apiscope.constants import LOCK_FILENAME
from apiscope.lock import LockError, acquire_write_lock


def test_acquire_write_lock_creates_an_empty_lock_database(tmp_path: Path) -> None:
    lock = acquire_write_lock(tmp_path)
    try:
        assert lock.path == tmp_path / LOCK_FILENAME
        assert lock.path.is_file()
    finally:
        lock.release()

    with sqlite3.connect(lock.path) as connection:
        tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()

    assert tables == []


def test_acquire_write_lock_rejects_a_held_lock(tmp_path: Path) -> None:
    lock = acquire_write_lock(tmp_path)
    try:
        with pytest.raises(LockError) as raised:
            acquire_write_lock(tmp_path)
    finally:
        lock.release()

    assert raised.value.code == "root.error.write_lock.busy"


def test_release_allows_the_next_acquire(tmp_path: Path) -> None:
    first = acquire_write_lock(tmp_path)
    first.release()

    second = acquire_write_lock(tmp_path)
    try:
        assert second.path.exists()
    finally:
        second.release()


def test_acquire_write_lock_closes_connection_when_begin_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailedConnection:
        closed = False

        def execute(self, statement: str) -> None:
            raise sqlite3.DatabaseError("invalid lock database")

        def close(self) -> None:
            self.closed = True

    connection = FailedConnection()
    monkeypatch.setattr(lock_module.sqlite3, "connect", lambda *args, **kwargs: connection)

    with pytest.raises(LockError) as raised:
        acquire_write_lock(tmp_path)

    assert raised.value.code == "root.error.write_lock.unavailable"
    assert connection.closed


def test_acquire_write_lock_reports_an_unusable_path(tmp_path: Path) -> None:
    (tmp_path / LOCK_FILENAME).mkdir()

    with pytest.raises(LockError) as raised:
        acquire_write_lock(tmp_path)

    assert raised.value.code == "root.error.write_lock.unavailable"
