"""
Declarative quest engine.

Quest *content* (title, starter code, points, hints) and quest *grading
logic* both live as data (see quests_store.py / quests_seed.json) instead
of as hardcoded Python branches. Adding a quest, tweaking its wording, or
re-theming it for a different customer is now a data edit, not a code
change — that's what lets one deployment serve many schools without a
per-customer fork.

The set of *check types* below is still Python (someone still has to teach
the engine what "the function returns the right thing" means), but it's a
small, fixed vocabulary that already covers every check the six original
hardcoded quests used, plus dictionaries/functions-on-dicts content. Adding
a genuinely new *kind* of check is a code change; adding a new *quest*
built from existing check types is not.

`expr` in "var_equals_expr" checks is admin-authored content (it ships in
quests_seed.json / is edited from the Admin Dashboard), not student input,
so evaluating it directly is fine — the untrusted student code has already
been run separately, in sandbox.py's isolated subprocess, before we ever
get here. We still restrict builtins when evaluating it, mainly to catch
authoring typos loudly rather than for security.
"""

_TYPE_MAP = {
    "int": int, "float": float, "str": str, "bool": bool,
    "list": list, "dict": dict, "tuple": tuple, "set": set,
    "callable": None,  # handled specially, see below
}

_EXPR_BUILTINS = {"sum": sum, "len": len, "round": round, "min": min,
                   "max": max, "sorted": sorted, "abs": abs}


class CheckResult:
    def __init__(self, passed, message=None, hints=None):
        self.passed = passed
        self.message = message
        self.hints = hints


def _check_has_var(check, code, output, variables):
    return CheckResult(check["var"] in variables)


def _check_var_type(check, code, output, variables):
    var = check["var"]
    if var not in variables:
        return CheckResult(False)
    value = variables[var]
    for type_name in check["types"]:
        if type_name == "callable":
            if callable(value):
                return CheckResult(True)
        elif isinstance(value, _TYPE_MAP[type_name]):
            # bool is a subclass of int — don't let a bool masquerade as
            # the numeric answer to a "should be a number" check.
            if _TYPE_MAP[type_name] is not bool and isinstance(value, bool):
                continue
            return CheckResult(True)
    return CheckResult(False)


def _check_code_contains(check, code, output, variables):
    tokens = check["tokens"]
    mode = check.get("mode", "all")
    hits = [t in code for t in tokens]
    return CheckResult(all(hits) if mode == "all" else any(hits))


def _check_output_nonempty(check, code, output, variables):
    return CheckResult(bool(output and output.strip()))


def _check_output_contains_var(check, code, output, variables):
    var = check["var"]
    if var not in variables:
        return CheckResult(False)
    return CheckResult(str(variables[var]) in (output or ""))


def _check_output_line_count_at_least(check, code, output, variables):
    based_on = variables.get(check["based_on_var"])
    if not isinstance(based_on, (list, tuple, dict, set)):
        return CheckResult(False)
    needed = len(based_on)
    got = len([l for l in (output or "").splitlines() if l.strip()])
    return CheckResult(got >= needed)


def _check_conditional_output_contains(check, code, output, variables):
    if variables.get(check["when_var"]) != check["when_equals"]:
        return CheckResult(True)  # condition doesn't apply — nothing to check
    haystack = (output or "").lower()
    return CheckResult(any(term.lower() in haystack for term in check["any_of"]))


def _check_var_equals_expr(check, code, output, variables):
    var = check["var"]
    if var not in variables:
        return CheckResult(False)
    try:
        expected = eval(check["expr"], {"__builtins__": _EXPR_BUILTINS}, dict(variables))
    except Exception:
        return CheckResult(False)
    return CheckResult(variables[var] == expected)


def _check_function_returns(check, code, output, variables):
    fn = variables.get(check["var"])
    if not callable(fn):
        return CheckResult(False)
    try:
        result = fn(*check["args"])
    except Exception:
        return CheckResult(False)
    return CheckResult(result == check["expected"])


_CHECKERS = {
    "has_var": _check_has_var,
    "var_type": _check_var_type,
    "code_contains": _check_code_contains,
    "output_nonempty": _check_output_nonempty,
    "output_contains_var": _check_output_contains_var,
    "output_line_count_at_least": _check_output_line_count_at_least,
    "conditional_output_contains": _check_conditional_output_contains,
    "var_equals_expr": _check_var_equals_expr,
    "function_returns": _check_function_returns,
}


def evaluate_quest(quest, code, output, variables):
    """
    Run a quest's checks, in order, against a student's (output, variables)
    from sandbox.safe_exec(). Returns a dict:
      {"passed": True} on success, or
      {"passed": False, "hints": [...]}  (progressive hint ladder), or
      {"passed": False, "message": "..."}  (single warning)
    Mirrors the two feedback styles the original hardcoded quests used.
    """
    for check in quest.get("checks", []):
        checker = _CHECKERS.get(check["type"])
        if checker is None:
            continue  # unknown check type in edited JSON — skip rather than crash
        result = checker(check, code, output, variables)
        if not result.passed:
            if check.get("hints"):
                return {"passed": False, "hints": check["hints"]}
            return {"passed": False, "message": check.get("message", "💡 Not quite — check your code and try again.")}
    return {"passed": True}
