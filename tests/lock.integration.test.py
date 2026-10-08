# tests/lock.integration.test.py
import subprocess
import sys
from pathlib import Path

import pytest

from apiscope.lock import LockError, acquire_write_lock


def test_write_lock_excludes_another_process_and_releases_on_exit(tmp_path: Path) -> None:
    worker = "\n".join(
        [
            "import os",
            "import sys",
            "from pathlib import Path",
            "from apiscope.lock import acquire_write_lock",
            "lock = acquire_write_lock(Path(sys.argv[1]))",
            "print(lock.path, flush=True)",
            "sys.stdin.readline()",
            "os._exit(0)",
        ]
    )
    project_root = Path(__file__).resolve().parents[1]
    process = subprocess.Popen(
        [sys.executable, "-c", worker, str(tmp_path)],
        cwd=project_root,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        assert process.stdout is not None
        if not process.stdout.readline():
            detail = process.stderr.read() if process.stderr is not None else ""
            pytest.fail(f"worker did not acquire the lock: {detail}")

        with pytest.raises(LockError) as raised:
            acquire_write_lock(tmp_path)
        assert raised.value.code == "root.error.write_lock.busy"

        assert process.stdin is not None
        process.stdin.write("exit\n")
        process.stdin.flush()
        assert process.wait(timeout=5) == 0

        lock = acquire_write_lock(tmp_path)
        lock.release()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        if process.stdin is not None:
            process.stdin.close()
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()
