import os
import signal
import threading
from handlers.logging import log_info, log_warning, log_error

_process_cache = {}
_lock = threading.Lock()


def add_process(name, process):
    with _lock:
        _process_cache[name] = {
            "pid": process.pid,
            "state": "running",
            "process": process
        }
        log_info(f"Process registered: {name} (PID: {process.pid})")


def remove_process(name):
    with _lock:
        if name in _process_cache:
            pid = _process_cache[name]["pid"]
            del _process_cache[name]
            log_info(f"Process unregistered: {name} (PID: {pid})")


def get_process(name):
    with _lock:
        entry = _process_cache.get(name)
        if entry:
            return entry["process"]
        return None


def get_process_info(name):
    with _lock:
        entry = _process_cache.get(name)
        if not entry:
            return None

        proc = entry["process"]
        if proc and entry["state"] == "running" and proc.poll() is not None:
            entry["state"] = f"exited ({proc.returncode})"

        return {
            "pid": entry["pid"],
            "state": entry["state"]
        }


def get_active_processes():
    with _lock:
        active = {}
        for name, entry in _process_cache.items():
            proc = entry["process"]
            if proc and proc.poll() is None:
                active[name] = proc
            elif entry["state"] == "running":
                entry["state"] = f"exited ({proc.returncode if proc else 'unknown'})"
        return active


def get_all_processes():
    with _lock:
        return dict(_process_cache)


def is_running(name):
    with _lock:
        entry = _process_cache.get(name)
        if not entry:
            return False
        proc = entry["process"]
        if proc and proc.poll() is None:
            return True
        if entry["state"] == "running":
            entry["state"] = f"exited ({proc.returncode if proc else 'unknown'})"
        return False


def list_processes():
    with _lock:
        result = {}
        for name, entry in _process_cache.items():
            proc = entry["process"]
            if proc and entry["state"] == "running" and proc.poll() is not None:
                entry["state"] = f"exited ({proc.returncode})"

            result[name] = {
                "pid": entry["pid"],
                "state": entry["state"]
            }
        return result


def stop_process(name, timeout=5):
    with _lock:
        entry = _process_cache.get(name)

    if not entry:
        return False

    proc = entry["process"]

    if not proc or proc.poll() is not None:
        with _lock:
            entry["state"] = f"exited ({proc.returncode if proc else 'unknown'})"
        return True

    try:
        proc.terminate()
        log_info(f"Sent terminate signal: {name} (PID: {proc.pid})")

        try:
            proc.wait(timeout=timeout)
            with _lock:
                entry["state"] = "stopped"
            log_info(f"Process terminated: {name}")
            return True
        except Exception:
            log_warning(f"Process did not stop in {timeout}s: {name} (PID: {proc.pid})")
            with _lock:
                entry["state"] = "hanging"
            return False

    except Exception as e:
        log_error(f"Failed to stop process {name}: {e}")
        with _lock:
            entry["state"] = "error"
        return False


def stop_all(timeout=5):
    with _lock:
        names = list(_process_cache.keys())

    for name in names:
        stop_process(name, timeout)

    with _lock:
        finished = []
        for name, entry in _process_cache.items():
            proc = entry["process"]
            if proc and proc.poll() is not None:
                if entry["state"] == "running":
                    entry["state"] = f"exited ({proc.returncode})"
                finished.append(name)


def force_kill_process(name):
    with _lock:
        entry = _process_cache.get(name)

    if not entry:
        return False

    proc = entry["process"]

    if not proc or proc.poll() is not None:
        with _lock:
            entry["state"] = f"exited ({proc.returncode if proc else 'unknown'})"
        return True

    try:
        if os.name == "nt":
            proc.kill()
        else:
            os.kill(proc.pid, signal.SIGKILL)

        proc.wait(timeout=3)
        log_warning(f"Force killed: {name} (PID: {proc.pid})")

        with _lock:
            entry["state"] = "killed"

        return True

    except Exception as e:
        log_error(f"Failed to force kill {name}: {e}")
        with _lock:
            entry["state"] = "error"
        return False


def force_kill_all():
    with _lock:
        names = list(_process_cache.keys())

    for name in names:
        force_kill_process(name)


def cleanup_finished():
    with _lock:
        finished = []
        for name, entry in _process_cache.items():
            proc = entry["process"]
            if proc and proc.poll() is not None:
                finished.append(name)

        for name in finished:
            del _process_cache[name]
            log_info(f"Cleaned up finished process: {name}")

        return len(finished)


def get_status_summary():
    with _lock:
        total = len(_process_cache)
        active = 0
        stopped = 0
        errored = 0

        for entry in _process_cache.values():
            proc = entry["process"]
            if proc and proc.poll() is None:
                active += 1
            elif entry["state"] == "error":
                errored += 1
            else:
                stopped += 1

        return {
            "total": total,
            "active": active,
            "stopped": stopped,
            "errored": errored,
            "processes": {
                name: {
                    "pid": entry["pid"],
                    "state": entry["state"]
                }
                for name, entry in _process_cache.items()
            }
        }