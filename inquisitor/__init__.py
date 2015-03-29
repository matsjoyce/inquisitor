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

    @property
    def three_arg(self):
        return self.exc_type, self.exc, self.traceback


DEFAULT_COLLECTORS = [collectors.FrameStackCollector(),
                      collectors.SystemInformationCollector(),
                      collectors.TimeCollector(),
                      collectors.ExceptionInfoCollector()]
DEFAULT_HANDLERS = [handlers.PrintTracebackHandler()]
DEFAULT_IGNORE = (KeyboardInterrupt, SystemExit)


class Inquisitor:
    def __init__(self, collectors=None, handlers=None, ignore=None,
                 tracker_url=None):
        self.collectors = collectors or DEFAULT_COLLECTORS
        self.handlers = handlers or DEFAULT_HANDLERS
        self.ignore = ignore or DEFAULT_IGNORE
        self.tracker_url = tracker_url
        self.enabled = True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if args[1] is not None:
            self.exception_3arg(*args, unhandled=False)

    def exception(self, exc, unhandled=True, disabled=None):
        if self.enabled:
            if not isinstance(exc, self.ignore):
                info = ExceptionInformation(exc, unhandled=unhandled,
                                            tracker_url=self.tracker_url)
                collection = {c.collector_name: c.collect(info)
                              for c in self.collectors}
                for handler in self.handlers:
                    handler.handle(info, collection)
        else:
            if disabled is not None:
                return disabled(exc)

    def exception_3arg(self, exc_type, exc, traceback,
                       unhandled=True, disabled=None):
        if disabled is None:
            return self.exception(exc, unhandled=unhandled)
        else:
            return self.exception(exc, unhandled=unhandled,
                                  disabled=lambda exc: disabled(exc_type,
                                                                exc,
                                                                traceback))

    def watch_sys_excepthook(self):
        import sys

        def replacement(*args, orig=sys.excepthook):
            return self.exception_3arg(*args, disabled=orig)

        sys.excepthook = replacement

    def watch_tkinter_report_callback_exception(self):
        import tkinter

        def replacement(root, *args,
                        orig=tkinter.Tk.report_callback_exception):
            return self.exception_3arg(*args,
                                       disabled=lambda *a: orig(root, *a))

        tkinter.Tk.report_callback_exception = replacement
