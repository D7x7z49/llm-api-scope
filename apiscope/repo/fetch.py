# apiscope/repo/fetch.py

import shutil
import subprocess
import time
from pathlib import Path

from apiscope.repo.schema import RepoEntry

# ==============================================================================
# git helpers
# ==============================================================================


def _run_git(args: list[str], cwd: Path | None = None) -> str | None:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        return result.stderr.strip()
    return None


def _clone_repo(url: str, work_dir: Path, branch: str | None = None) -> str | None:
    args = [
        "clone",
        "--depth=1",
        "--filter=blob:none",
        "--sparse",
    ]
    if branch is not None:
        args.extend(["--branch", branch])
    args.extend([url, str(work_dir)])
    return _run_git(args)


def _fetch_commit(work_dir: Path, commit: str) -> str | None:
    err = _run_git(["fetch", "origin", "--depth=1", commit], cwd=work_dir)
    if err is not None:
        return err
    return _run_git(["checkout", "FETCH_HEAD"], cwd=work_dir)


def _sparse_set(work_dir: Path, directory: str) -> str | None:
    return _run_git(["sparse-checkout", "set", directory], cwd=work_dir)


# ==============================================================================
# sync
# ==============================================================================


def _copy_docs(work_dir: Path, directory: str, dst: Path) -> str | None:
    src = work_dir / directory
    if not src.exists():
        return f"directory [{directory}] not found in <{work_dir}>"
    shutil.rmtree(dst, ignore_errors=True)
    dst.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copytree(src, dst, dirs_exist_ok=True)
    except shutil.Error as e:
        return str(e)
    return None


def sync_entry(
    entry: RepoEntry,
    tmp_dir: Path,
    cache_dir: Path,
    *,
    force: bool = False,
    ttl: int,
) -> str | None:
    work_dir = tmp_dir / entry.sha256_id
    dst_dir = cache_dir / entry.sha256_id

    # check cache freshness
    if not force and not _is_stale(dst_dir, ttl):
        return None

    # cleanup previous state
    shutil.rmtree(work_dir, ignore_errors=True)
    shutil.rmtree(dst_dir, ignore_errors=True)

    ref = entry.reference

    if ref is not None and ref[0] == "commit":
        # commit ref: clone first, then fetch specific commit
        ref_name = ref[1]
        err = _clone_repo(entry.url, work_dir)
        if err is not None:
            return err
        err = _fetch_commit(work_dir, ref_name)
        if err is not None:
            return err
    else:
        # branch or tag: clone with --branch
        branch = ref[1] if ref is not None else "main"
        err = _clone_repo(entry.url, work_dir, branch=branch)
        if err is not None:
            return err

    # sparse checkout target directory
    err = _sparse_set(work_dir, entry.dir)
    if err is not None:
        return err

    # copy extracted docs to cache
    err = _copy_docs(work_dir, entry.dir, dst_dir)
    if err is not None:
        return err

    # cleanup working directory
    shutil.rmtree(work_dir, ignore_errors=True)

    return None


# ==============================================================================
# freshness
# ==============================================================================


def _is_stale(path: Path, ttl: int) -> bool:
    if not path.exists():
        return True
    stat = path.stat()
    latest = max(stat.st_mtime, stat.st_ctime)
    return time.time() - latest > ttl
