class MultiDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__()
        for initial in args:
            [self.__setitem__(*a) for a in initial.items()]
        [self.__setitem__(*a) for a in kwargs.items()]

    def __setitem__(self, key, value):
        if key not in self:
            super().__setitem__(key, [])
        self[key].append(value)

    def __repr__(self):
        contents = ", ".join(repr(k) + ": " + repr(v) for k, v in self.items())
        return "{{{}}}".format(contents)

    def __len__(self):
        return sum(len(i) for i in super().values())

    def items(self):
        for name, values in super().items():
            for value in values:
                yield name, value

    def values(self):
        for values in super().values():
            for value in values:
                yield value


if __name__ == "__main__":
    assert issubclass(MultiDict, dict)
    md = MultiDict({"a": 0, "b": "hi"}, c=5)
    md["a"] = 1
    md["a"] = 2
    md["a"] = 3
    for i, j in md.items():
        print(i, j)
    print(md)
    assert "a" in md
    assert len(md) == 6
