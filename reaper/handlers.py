import abc
import pprint
import sys
import traceback
from xml.etree import ElementTree as ETree


class Handler(abc.ABC):
    @abc.abstractmethod
    def handle(self, info, collection):
        pass


class PrintTracebackHandler(Handler):
    def __init__(self, print_when_not_unhandled=False):
        self.print_when_not_unhandled = print_when_not_unhandled

    def handle(self, info, collection):
        if not info.unhandled and not self.print_when_not_unhandled:
            return
        traceback.print_exception(info.exc_type, info.exc, info.traceback)


class PPrintStreamHandler(Handler):
    def __init__(self, stream=sys.stdout):
        self.stream = stream

    def handle(self, info, collection):
        print(pprint.pformat(collection),
              file=self.stream,
              flush=True)


class XMLFileDumpHandler(Handler):
    def __init__(self, fname):
        self.fname = fname

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
            print("Unhandled type", type(var))
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
        print(root)
        self.xmlify(collection, root)
        self.indent(root)
        with open(self.fname, "wb") as f:
            f.write(ETree.tostring(root))
