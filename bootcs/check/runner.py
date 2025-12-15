"""
Check runner for bootcs/check50.

Based on check50 by CS50 (https://github.com/cs50/check50)
Licensed under GPL-3.0
"""

import collections
from contextlib import contextmanager
import concurrent.futures as futures
import functools
import inspect
import importlib
import importlib.util
import multiprocessing
import os
from pathlib import Path
import pickle
import shutil
import signal
import sys
import tempfile
import traceback

import attr

from .. import lib50
from . import internal, _exceptions
from ._api import log, Failure, _copy, _log, _data


def _(s):
    """Translation function - returns string as-is for now."""
    return s


_check_names = []


@attr.s(slots=True)
class CheckResult:
    """Record returned by each check"""
    name = attr.ib()
    description = attr.ib()
    passed = attr.ib(default=None)
    log = attr.ib(default=attr.Factory(list))
    cause = attr.ib(default=None)
    data = attr.ib(default=attr.Factory(dict))
    dependency = attr.ib(default=None)

    @classmethod
    def from_check(cls, check, *args, **kwargs):
        """Create a check_result given a check function."""
        return cls(name=check.__name__, 
                   description=_(check.__doc__ if check.__doc__ else check.__name__.replace("_", " ")),
                   dependency=check._check_dependency.__name__ if check._check_dependency else None,
                   *args,
                   **kwargs)

    @classmethod
    def from_dict(cls, d):
        """Create a CheckResult given a dict."""
        return cls(**{field.name: d[field.name] for field in attr.fields(cls)})


class Timeout(Failure):
    def __init__(self, seconds):
        super().__init__(rationale=_("check timed out after {} seconds").format(seconds))


@contextmanager
def _timeout(seconds):
    """Context manager that runs code block until timeout is reached."""

    def _handle_timeout(*args):
        raise Timeout(seconds)

    signal.signal(signal.SIGALRM, _handle_timeout)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)


def check(dependency=None, timeout=60, max_log_lines=100):
    """
    Mark function as a check.

    :param dependency: the check that this check depends on
    :type dependency: function
    :param timeout: maximum number of seconds the check can run
    :type timeout: int
    :param max_log_lines: maximum number of lines that can appear in the log
    :type max_log_lines: int
    """
    def decorator(check):
        _check_names.append(check.__name__)
        check._check_dependency = dependency

        @functools.wraps(check)
        def wrapper(run_root_dir, dependency_state):
            result = CheckResult.from_check(check)
            state = None

            try:
                internal.run_dir = run_root_dir / check.__name__
                src_dir = run_root_dir / (dependency.__name__ if dependency else "-")
                shutil.copytree(src_dir, internal.run_dir)
                os.chdir(internal.run_dir)

                with internal.register, _timeout(seconds=timeout):
                    args = (dependency_state,) if inspect.getfullargspec(check).args else ()
                    state = check(*args)
            except Failure as e:
                result.passed = False
                result.cause = e.payload
            except BaseException as e:
                result.passed = None
                result.cause = {"rationale": _("check50 ran into an error while running checks!"),
                                "error": {
                                    "type": type(e).__name__,
                                    "value": str(e),
                                    "traceback": traceback.format_tb(e.__traceback__),
                                    "data" : e.payload if hasattr(e, "payload") else {}
                                }}
            else:
                result.passed = True
            finally:
                result.log = _log if len(_log) <= max_log_lines else ["..."] + _log[-max_log_lines:]
                result.data = _data
                return result, state
        return wrapper
    return decorator


class CheckRunner:
    def __init__(self, checks_path, included_files):
        self.checks_path = checks_path
        self.included_files = included_files

    def run(self, targets=None):
        """
        Run checks concurrently.
        Returns a list of CheckResults ordered by declaration order of the checks.
        """
        graph = self.build_subgraph(targets) if targets else self.dependency_graph

        results = {name: None for name in self.check_names}

        try:
            max_workers = int(os.environ.get("CHECK50_WORKERS"))
        except (ValueError, TypeError):
            max_workers = None

        with futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            not_done = set(executor.submit(run_check(name, self.checks_spec))
                           for name in graph[None])
            not_passed = []

            while not_done:
                done, not_done = futures.wait(not_done, return_when=futures.FIRST_COMPLETED)
                for future in done:
                    result, state = future.result()
                    results[result.name] = result
                    if result.passed:
                        for child_name in graph[result.name]:
                            not_done.add(executor.submit(
                                run_check(child_name, self.checks_spec, state)))
                    else:
                        not_passed.append(result.name)

        for name in not_passed:
            self._skip_children(name, results)

        return list(filter(None, results.values()))


    def build_subgraph(self, targets):
        """Build minimal subgraph of self.dependency_graph that contains each check in targets"""
        checks = self.dependencies_of(targets)
        subgraph = collections.defaultdict(set)
        for dep, children in self.dependency_graph.items():
            if dep is not None and dep not in checks:
                continue
            for child in children:
                if child in checks:
                    subgraph[dep].add(child)
        return subgraph


    def dependencies_of(self, targets):
        """Get all unique dependencies of the targeted checks."""
        inverse_graph = self._create_inverse_dependency_graph()
        deps = set()
        for target in targets:
            if target not in inverse_graph:
                raise _exceptions.Error(_("Unknown check: {}").format(target))
            curr_check = target
            while curr_check is not None and curr_check not in deps:
                deps.add(curr_check)
                curr_check = inverse_graph[curr_check]
        return deps


    def _create_inverse_dependency_graph(self):
        """Build an inverse dependency map, from a check to its dependency."""
        inverse_dependency_graph = {}
        for check_name, dependents in self.dependency_graph.items():
            for dependent_name in dependents:
                inverse_dependency_graph[dependent_name] = check_name
        return inverse_dependency_graph


    def _skip_children(self, check_name, results):
        """Recursively skip the children of check_name."""
        for name in self.dependency_graph[check_name]:
            if results[name] is None:
                results[name] = CheckResult(name=name, description=self.check_descriptions[name],
                                            passed=None,
                                            dependency=check_name,
                                            cause={"rationale": _("can't check until a frown turns upside down")})
                self._skip_children(name, results)


    def __enter__(self):
        internal.student_dir = Path.cwd()

        self._working_area_manager = lib50.working_area(self.included_files, name='-')
        internal.run_root_dir = self._working_area_manager.__enter__().parent

        self._cd_manager = lib50.cd(internal.run_root_dir)
        self._cd_manager.__enter__()

        self.checks_spec = importlib.util.spec_from_file_location("checks", self.checks_path)

        _check_names.clear()
        check_module = importlib.util.module_from_spec(self.checks_spec)
        self.checks_spec.loader.exec_module(check_module)
        self.check_names = _check_names.copy()
        _check_names.clear()

        checks = inspect.getmembers(check_module, lambda f: hasattr(f, "_check_dependency"))

        self.dependency_graph = collections.defaultdict(set)
        for name, check in checks:
            dependency = None if check._check_dependency is None else check._check_dependency.__name__
            self.dependency_graph[dependency].add(name)

        self.check_descriptions = {name: check.__doc__ for name, check in checks}

        return self


    def __exit__(self, type, value, tb):
        self._working_area_manager.__exit__(type, value, tb)
        self._cd_manager.__exit__(type, value, tb)


class run_check:
    """
    Check job that runs in a separate process.
    """

    CROSS_PROCESS_ATTRIBUTES = (
        "internal.check_dir",
        "internal.slug",
        "internal.student_dir",
        "internal.run_root_dir",
        "sys.excepthook",
    )

    def __init__(self, check_name, spec, state=None):
        self.check_name = check_name
        self.spec = spec
        self.state = state
        self._store_attributes()

    def _store_attributes(self):
        if multiprocessing.get_start_method() != "spawn":
           return

        self._attribute_values = [eval(name) for name in self.CROSS_PROCESS_ATTRIBUTES]
        
        for i, value in enumerate(self._attribute_values):
            try:
                pickle.dumps(value)
            except (pickle.PicklingError, AttributeError):
                self._attribute_values[i] = None
                
        self._attribute_values = tuple(self._attribute_values)


    def _set_attributes(self):
        if not hasattr(self, "_attribute_values"):
           return

        for name, val in zip(self.CROSS_PROCESS_ATTRIBUTES, self._attribute_values):
            self._set_attribute(name, val)


    @staticmethod
    def _set_attribute(name, value):
        parts = name.split(".")

        obj = sys.modules[__name__]
        for part in parts[:-1]:
            obj = getattr(obj, part)

        setattr(obj, parts[-1], value)


    def __call__(self):
        self._set_attributes()

        mod = importlib.util.module_from_spec(self.spec)
        self.spec.loader.exec_module(mod)

        internal.check_running = True
        try:
            return getattr(mod, self.check_name)(internal.run_root_dir, self.state)
        finally:
            internal.check_running = False
