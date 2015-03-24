import collections


class MultiDict(collections.UserDict, dict):
    def __init__(self, *args, **kwargs):
        self.data = collections.defaultdict(list)
        for initial in args:
            [self.__setitem__(*a) for a in initial.items()]
        [self.__setitem__(*a) for a in kwargs.items()]

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key].append(value)

    def __delitem__(self, key):
        del self.data[key]

    def __repr__(self):
        return "{" + ", ".join(": ".join(map(repr, p)) for p in self.items()) + "}"

    def items(self):
        for name, values in self.data.items():
            for value in values:
                yield name, value

    def values(self):
        for name, values in self.data.items():
            for value in values:
                yield value

if __name__ == "__main__":
    print(issubclass(MultiDict, dict))
    m = MultiDict({"a": 0, "b": "hi"}, c=5)
    m["a"] = 1
    m["a"] = 2
    m["a"] = 3
    for i, j in m.items():
        print(i, j)
    print(m)
