from . import collectors, handlers


class ExceptionInformation:
    def __init__(self, exc, unhandled=True):
        self.exc = exc
        self.exc_type = type(exc)
        self.traceback = exc.__traceback__
        self.frame_stack = self.traceback.tb_frame
        self.unhandled = unhandled


class Reaper:
    def __init__(self, collectors=None, handlers=None):
        self.collectors = collectors or []
        self.handlers = handlers or []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if args[1] is not None:
            self.exception_3arg(*args, unhandled=False)

    def exception(self, exc, unhandled=True):
        info = ExceptionInformation(exc, unhandled=unhandled)
        collection = {col.name: col.collect(info) for col in self.collectors}
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
