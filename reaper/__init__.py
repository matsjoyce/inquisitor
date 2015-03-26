from . import collectors, handlers, utils


class ExceptionInformation:
    def __init__(self, exc, unhandled=True, tracker_url=None):
        self.exc = exc
        self.exc_type = type(exc)
        self.traceback = exc.__traceback__
        self.frame_stack = self.traceback.tb_frame
        self.unhandled = unhandled
        self.file_location = None
        self.tracker_url = tracker_url


DEFAULT_COLLECTORS = [collectors.FrameStackCollector(),
                      collectors.SystemInformationCollector(),
                      collectors.TimeCollector(),
                      collectors.ExceptionInfoCollector()]
DEFAULT_HANDLERS = [handlers.PrintTracebackHandler()]
DEFAULT_IGNORE = (KeyboardInterrupt, SystemExit)


class Reaper:
    def __init__(self, collectors=None, handlers=None, ignore=None,
                 tracker_url=None):
        self.collectors = collectors or DEFAULT_COLLECTORS
        self.handlers = handlers or DEFAULT_HANDLERS
        self.ignore = ignore or DEFAULT_IGNORE
        self.tracker_url = tracker_url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if args[1] is not None:
            self.exception_3arg(*args, unhandled=False)

    def exception(self, exc, unhandled=True):
        if not isinstance(exc, self.ignore):
            info = ExceptionInformation(exc, unhandled=unhandled,
                                        tracker_url=self.tracker_url)
            collection = {c.name: c.collect(info) for c in self.collectors}
            for handler in self.handlers:
                handler.handle(info, collection)

    def exception_3arg(self, exc_type, exc, traceback, unhandled=True):
        return self.exception(exc, unhandled=unhandled)

    def watch_sys_excepthook(self):
        import sys
        sys.excepthook = self.exception_3arg

    def watch_tkinter_report_callback_exception(self):
        import tkinter
        tkinter.Tk.report_callback_exception = self.exception_3arg
