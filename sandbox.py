"""
Sandboxed execution for student-submitted Python code.

Replaces the old substring-blocklist approach (trivially bypassed, e.g.
"imp" + "ort os") with:
  - A restricted-builtins namespace (whitelist only, no eval/exec/compile/
    open/__import__/getattr/setattr/globals/locals/etc.)
  - Real process isolation via `multiprocessing`, so a runaway/hostile
    script can be killed outright rather than just timing out logically.
  - A wall-clock timeout (kills infinite loops).
  - CPU-time and memory limits on POSIX hosts (Linux/macOS — i.e. wherever
    this will actually be deployed) via the `resource` module. These are
    silently skipped on Windows, where `resource` doesn't exist; the
    timeout + process kill still apply there.

This module is intentionally free of any Streamlit/session-state code and
has no import-time side effects, so it's safe to import from a freshly
spawned child process on any platform (important for Windows, which uses
"spawn" instead of "fork" and re-imports the target module).

Abuse protection lives in two places:
  - `safe_exec` itself caps how many sandboxed processes may run at once,
    process-wide, via a semaphore (protects the server regardless of how
    many Streamlit sessions/users are hammering "Run" concurrently).
  - Per-user/per-session throttling (how often *one* student can click
    Run) is intentionally NOT handled here, since this module has no
    notion of "session" — see `run_student_code()` in remote_tech_app.py
    for that layer.
"""

import builtins
import contextlib
import io
import multiprocessing as mp
import queue as _queue
import threading

# ---------------------------------------------------------------------------
# Process-wide concurrency cap. Each safe_exec() call spawns a real OS
# process, which is by far the most expensive thing this app does — without
# a cap, enough simultaneous "Run" clicks (accidental or deliberate) could
# exhaust CPU/memory on the host. `_CONCURRENCY_WAIT_SECONDS` is how long a
# call will queue for a free slot before giving up and reporting "busy"
# rather than blocking the Streamlit session forever.
# ---------------------------------------------------------------------------
MAX_CONCURRENT_EXECUTIONS = 4
_CONCURRENCY_WAIT_SECONDS = 5
_concurrency_semaphore = threading.Semaphore(MAX_CONCURRENT_EXECUTIONS)

# ---------------------------------------------------------------------------
# Whitelisted builtins. Only what's needed for the current quest content
# (variables, arithmetic, conditionals, loops, functions, lists/dicts).
# Deliberately excludes: eval, exec, compile, open, __import__, getattr,
# setattr, delattr, globals, locals, vars, dir, help, input, exit, quit,
# breakpoint, __build_class__ (no student-defined classes needed yet).
# ---------------------------------------------------------------------------
_SAFE_BUILTIN_NAMES = (
    "abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes",
    "callable", "chr", "complex", "dict", "divmod", "enumerate", "filter",
    "float", "format", "frozenset", "hash", "hex", "id", "int",
    "isinstance", "issubclass", "iter", "len", "list", "map", "max", "min",
    "next", "object", "oct", "ord", "pow", "print", "range", "repr",
    "reversed", "round", "set", "slice", "sorted", "str", "sum", "tuple",
    "type", "zip",
    # Exceptions students may legitimately hit or catch
    "ArithmeticError", "AssertionError", "AttributeError", "Exception",
    "IndexError", "KeyError", "NameError", "OverflowError", "RuntimeError",
    "StopIteration", "TypeError", "ValueError", "ZeroDivisionError",
)

_TIMED_OUT = "__sandbox_timeout__"


def _build_safe_builtins():
    return {name: getattr(builtins, name) for name in _SAFE_BUILTIN_NAMES
            if hasattr(builtins, name)}


def _picklable(value):
    """Only hand simple, safe-to-pickle types back across the process boundary."""
    return isinstance(value, (int, float, str, bool, list, dict, tuple, set,
                               frozenset, type(None)))


def _apply_resource_limits(cpu_seconds=3, memory_bytes=256 * 1024 * 1024):
    """Best-effort CPU/memory caps. No-op on platforms without `resource` (Windows)."""
    try:
        import resource
    except ImportError:
        return
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
    except (ValueError, OSError):
        pass
    try:
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
    except (ValueError, OSError):
        pass


def _worker(code, result_queue):
    _apply_resource_limits()
    safe_builtins = _build_safe_builtins()
    stdout_capture = io.StringIO()
    local_vars = {}
    try:
        with contextlib.redirect_stdout(stdout_capture):
            compiled = compile(code, "<student_code>", "exec")
            exec(compiled, {"__builtins__": safe_builtins}, local_vars)
        safe_vars = {k: v for k, v in local_vars.items() if _picklable(v)}
        result_queue.put((stdout_capture.getvalue().strip(), safe_vars, None))
    except MemoryError:
        result_queue.put(("", {}, "Your code used too much memory."))
    except Exception as e:
        # Keep only the message — the traceback can reference internals
        # of the sandbox itself, which we don't want to leak.
        result_queue.put(("", {}, f"{type(e).__name__}: {e}"))


def safe_exec(code, timeout=3):
    """
    Run student code in an isolated process with a restricted builtins
    namespace. Returns (stdout, local_vars, error) exactly like the old
    safe_exec did, so call sites don't need to change.

    Blocks (briefly) for a free execution slot if the server is already
    running MAX_CONCURRENT_EXECUTIONS sandboxes; if none frees up within
    _CONCURRENCY_WAIT_SECONDS it fails soft with a "busy" message instead
    of spawning an unbounded number of processes.
    """
    acquired = _concurrency_semaphore.acquire(timeout=_CONCURRENCY_WAIT_SECONDS)
    if not acquired:
        return "", {}, "The code sandbox is busy right now — please try again in a few seconds."

    try:
        result_queue = mp.Queue()
        proc = mp.Process(target=_worker, args=(code, result_queue), daemon=True)
        proc.start()
        proc.join(timeout)

        if proc.is_alive():
            proc.terminate()
            proc.join(1)
            if proc.is_alive():
                proc.kill()
                proc.join()
            return "", {}, "Your code took too long to run (possible infinite loop). Try again!"

        try:
            output, variables, error = result_queue.get_nowait()
            return output, variables, error
        except _queue.Empty:
            # Process died without reporting (e.g. killed by the OS OOM killer
            # or hit the memory rlimit hard) rather than raising MemoryError cleanly.
            return "", {}, "Your code crashed or used too many resources. Try again!"
    finally:
        _concurrency_semaphore.release()
