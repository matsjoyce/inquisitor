import abc
import logging
import pathlib
import pprint
import sys
import traceback
from xml.etree import ElementTree as ETree


class Handler(abc.ABC):
    @abc.abstractmethod
    def handle(self, info, collection):
        pass


class FileHandler(Handler):
    def __init__(self, fname=None, reportmanager=None):
        self._fname = fname
        self._reportmanager = reportmanager
        if (fname is None and reportmanager is None
           or fname is not None and reportmanager is not None):
            raise ValueError("Must have a file name or a report manager")
        self.last_filename = None

    @property
    def fname(self):
        if self._reportmanager is not None:
            self.last_filename = self._reportmanager.next_filename
        else:
            self.last_filename = self._fname
        return self.last_filename

    def update(self, info):
        if self._reportmanager is not None:
            self._reportmanager.size_checks()
        if pathlib.Path(self.last_filename).is_file():
            info.file_location = self.last_filename
        else:
            info.file_location = None


DEFAULT_EXCEPTION_MESSAGE = """An unhandled exception has been detected.
Please file a bug report at "{tracker_url}",
attaching the report file saved at "{file_location}".""".replace("\n", " ")


class MessageHandler(Handler):
    def __init__(self, title="Unhandled exception",
                 msg=DEFAULT_EXCEPTION_MESSAGE,
                 when_not_unhandled=False, ask_start_db=False, db_cmd=None):
        self.title = title
        self.msg = msg
        self.when_not_unhandled = when_not_unhandled
        self.ask_start_db = ask_start_db
        self.db_cmd = db_cmd

    def formatted_msg(self, info):
        return self.msg.format(**info.__dict__)


class PrintTracebackHandler(Handler):
    def __init__(self, print_when_not_unhandled=False):
        self.print_when_not_unhandled = print_when_not_unhandled

    def handle(self, info, collection):
        if not info.unhandled and not self.print_when_not_unhandled:
            return
        traceback.print_exception(info.exc_type, info.exc, info.traceback)


class LogTracebackHandler(Handler):
    def __init__(self, logger=None, when_not_unhandled=False):
        self.logger = logger or logging.getLogger(__name__)
        self.when_not_unhandled = when_not_unhandled

    def handle(self, info, collection):
        if not info.unhandled and not self.when_not_unhandled:
            return
        self.logger.error("Exception:",
                          exc_info=(info.exc_type, info.exc, info.traceback))


class PPrintStreamHandler(Handler):
    def __init__(self, stream=sys.stdout):
        self.stream = stream

    def handle(self, info, collection):
        print(pprint.pformat(collection),
              file=self.stream,
              flush=True)


class XMLFileDumpHandler(FileHandler):
    def xmlify(self, var, element):
        if isinstance(var, dict):
            for name, value in var.items():
                sub = ETree.SubElement(element, name)
                self.xmlify(value, sub)
        elif isinstance(var, str):
            element.text = var
        elif isinstance(var, (int, float)):
            element.text = str(var)
        elif isinstance(var, list):
            for value in var:
                sub = ETree.SubElement(element, "item")
                self.xmlify(value, sub)
        else:
            element.text = repr(var)

    def indent(self, elem, level=0):
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def handle(self, info, collection):
        root = ETree.Element("exception")
        self.xmlify(collection, root)
        self.indent(root)
        with open(self.fname, "wb") as outfile:
            outfile.write(ETree.tostring(root))
        self.update(info)


class StreamMessageHandler(MessageHandler):
    def __init__(self, *args, stream=sys.stdout, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream = stream

    def handle(self, info, collection):
        if not info.unhandled and not self.when_not_unhandled:
            return
        side_bar_width = round((80 - 2 - len(self.title)) / 2 - 0.5)
        title = " ".join(("=" * side_bar_width,
                          self.title,
                          "=" * side_bar_width))
        print(file=self.stream)
        print(title, file=self.stream)
        fmsg = self.formatted_msg(info)
        lines = [[]]
        for i in fmsg.split():
            if len(" ".join(lines[-1] + [i])) > 80:
                lines.append([])
            lines[-1].append(i)
        print("\n".join(map(" ".join, lines)),
              file=self.stream)
        print("=" * len(title), file=self.stream)
        print(file=self.stream)


class TkinterMessageHandler(MessageHandler):
    def handle(self, info, collection):
        if not info.unhandled and not self.when_not_unhandled:
            return
        from tkinter import messagebox
        if self.ask_start_db:
            r = messagebox._show(self.title, self.formatted_msg(info)
                                 + " Do you want to start the debugger?",
                                 messagebox.ERROR, messagebox.YESNO)
            if r == "yes":
                self.db_cmd(*info.three_arg)
        else:
            messagebox.showerror(title=self.title,
                                 message=self.formatted_msg(info))
