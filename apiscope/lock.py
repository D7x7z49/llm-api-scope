# apiscope/lock.py
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from apiscope.constants import LOCK_FILENAME
from apiscope.errors import MessageError


class LockError(MessageError):
    pass


@dataclass(slots=True)
class WriteLock:
    path: Path
    connection: sqlite3.Connection | None

    def release(self) -> None:
        connection = self.connection
        if connection is None:
            return
        self.connection = None
        try:
            if connection.in_transaction:
                connection.rollback()
        finally:
            connection.close()


# hold one immediate transaction; SQLite releases it when the connection closes.
def acquire_write_lock(home_root: Path) -> WriteLock:
    path = home_root / LOCK_FILENAME
    connection: sqlite3.Connection | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path, timeout=0.0, isolation_level=None)
        connection.execute("BEGIN IMMEDIATE")
    except (OSError, sqlite3.Error) as error:
        _close_connection(connection)
        if isinstance(error, sqlite3.Error) and _is_busy(error):
            raise LockError("root.error.write_lock.busy", {"path": str(path)}) from error
        raise LockError(
            "root.error.write_lock.unavailable",
            {"path": str(path), "detail": str(error)},
        ) from error
    return WriteLock(path=path, connection=connection)


def _is_busy(error: sqlite3.Error) -> bool:
    code = getattr(error, "sqlite_errorcode", None)
    return code is not None and (code & 0xFF) in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED}


def _close_connection(connection: sqlite3.Connection | None) -> None:
    if connection is None:
        return
    try:
        connection.close()
    except sqlite3.Error:
        pass


__all__ = ["LockError", "WriteLock", "acquire_write_lock"]
