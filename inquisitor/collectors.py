import abc
import builtins
import collections.abc
import inspect
import io
import logging
import platform
import sys
import time
import types

from . import multidict


class Collector(abc.ABC):
    def __init__(self, name):
        self.collector_name = name

    @abc.abstractmethod
    def collect(self, info):
        pass


class Snipped:
    def __repr__(self):
        return "<snipped>"


class FrameStackCollector(Collector):
    def __init__(self, max_levels=5):
        super().__init__("frame_stack")
        self.max_levels = max_levels

    def try_get_vars(self, var):
        try:
            return vars(var)
        except TypeError:
            return {}

    def record(self, var):
        if id(var) in (id(builtins), id(builtins.__dict__)):
            return False
        elif (isinstance(var, types.ModuleType)
              and getattr(var, "__file__",
                          sys.base_prefix).startswith(sys.base_prefix)):
            return False
        elif (isinstance(var, types.ModuleType)
              and getattr(var, "__package__", "") == "inquisitor"):
            return False
        elif (isinstance(var, (types.FunctionType, types.MethodType))
              and var.__name__.startswith("__")):
            return False
        return True

    def record_attr(self, name):
        if name.startswith("__"):
            return False
        return True

    def get_var(self, var, seen=None, level=0):
        if level == self.max_levels:
            return Snipped()
        if seen is None:
            seen = set()
        if id(var) in seen:
            return {"id": id(var)}
        if not self.record(var):
            return Snipped()
        seen.add(id(var))
        info = multidict.MultiDict(id=id(var),
                                   repr=(repr(var) if self.record(var)
                                         else "<snipped>"))
        for n, value in self.try_get_vars(var).items():
            if self.record_attr(n):
                info["attr"] = {"name": n,
                                "value": self.get_var(value,
                                                      seen=seen,
                                                      level=level + 1)}
        if isinstance(var, collections.abc.Mapping):
            for key, value in var.items():
                info["mapping_item"] = {"key": self.get_var(key, seen=seen,
                                                            level=level + 1),
                                        "value": self.get_var(value, seen=seen,
                                                              level=level + 1)}
        elif (isinstance(var, collections.abc.Sequence)
              and not isinstance(var, (str, bytes))):
            for item in var:
                info["item"] = self.get_var(item, seen=seen, level=level + 1)
        return info

    def collect(self, info):
        frames = multidict.MultiDict()
        stack = inspect.getinnerframes(info.traceback)
        seen = set()
        for f, file, lineno, func, *_ in stack:
            globs = {n: self.get_var(v, seen) for n, v in f.f_globals.items()
                     if self.record_attr(n)}
            if f.f_locals is not f.f_globals:
                locs = {n: self.get_var(v, seen) for n, v in f.f_locals.items()
                        if self.record_attr(n)}
            else:
                locs = "<same as globals>"
            frames["frame"] = multidict.MultiDict(locals=locs,
                                                  globals=globs,
                                                  filename=file,
                                                  lineno=lineno,
                                                  function=func)
        return frames


class SystemInformationCollector(Collector):
    def __init__(self):
        super().__init__("system_information")

    def collect(self, info):
        uname = dict(zip(("system", "node", "release", "version",
                          "machine", "processor"), platform.uname()))
        python = {"version": platform.python_version(),
                  "implementation": platform.python_implementation(),
                  "compiler": platform.python_compiler(),
                  "revision": platform.python_revision(),
                  "branch": platform.python_branch()
                  }
        return {"platform": platform.platform(),
                "api_version": sys.api_version,
                "argv": sys.argv,
                "base_prefix": sys.base_prefix,
                "executable": sys.executable,
                "uname": uname,
                "python": python
                }


class TimeCollector(Collector):
    def __init__(self):
        super().__init__("time")
        self.start_time = time.time()

    def collect(self, info):
        return {"start_time": time.ctime(self.start_time),
                "exception_time": time.ctime(),
                "running_for": time.time() - self.start_time
                }


class ExceptionInfoCollector(Collector):
    def __init__(self):
        super().__init__("exception_info")

    def collect(self, info):
        return {"type": info.exc_type.__qualname__,
                "msg": str(info.exc),
                "args": info.exc.args}


class LoggingCollector(Collector, logging.StreamHandler):
    def __init__(self):
        Collector.__init__(self, "logging")
        logging.StreamHandler.__init__(self, stream=io.StringIO())
        self.setLevel(logging.DEBUG)

    def collect(self, info):
        return self.stream.getvalue()
