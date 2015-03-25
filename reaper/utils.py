import pathlib
import re


B, KiB, MiB, GiB, TiB = map((2).__pow__, range(0, 50, 10))


class ReportManager:
    def __init__(self, directory, patten, max_no_files=None,
                 max_files_size=None, num_sub="no"):
        self.directory = pathlib.Path(directory)
        self.patten = patten
        self.max_files_size = max_files_size
        self.max_no_files = max_no_files
        self.num_sub = "{{{}}}".format(num_sub)
        if self.num_sub not in self.patten:
            return ValueError("Number substitution not in patten")
        re_pat = re.escape(patten).replace(re.escape(self.num_sub),
                                           r"(?P<num>\d+)")
        self.re_patten = re.compile(re_pat)
        self.size_checks()

    @property
    def files(self):
        return [fname for fname in self.directory.iterdir()
                if self.re_patten.match(fname.name)]

    @property
    def directory_size(self):
        return sum(p.stat().st_size for p in self.files)

    @property
    def directory_size_str(self):
        dir_size = self.directory_size
        if dir_size < KiB:
            return "{} B".format(dir_size)
        elif dir_size < MiB:
            return "{:.2f} KiB".format(dir_size / KiB)
        elif dir_size < GiB:
            return "{:.2f} MiB".format(dir_size / MiB)
        elif dir_size < TiB:
            return "{:.2f} GiB".format(dir_size / GiB)
        else:
            return "{:.2f} TiB".format(dir_size / TiB)

    @property
    def next_filename(self):
        reported_nums = [int(self.re_patten.match(fname.name).group("num"))
                         for fname in self.files]
        for i in range(len(reported_nums) + 1):
            if i not in reported_nums:
                return str(self.directory / self.patten.format(no=i))

    @property
    def first_modified_filename(self):
        return min(self.files,
                   key=lambda p: p.stat().st_mtime) if self.files else None

    def size_checks(self):
        if self.max_files_size is not None:
            while self.directory_size > self.max_files_size:
                self.first_modified_filename.unlink()
        if self.max_no_files is not None:
            while len(self.files) > self.max_no_files:
                self.first_modified_filename.unlink()


if __name__ == "__main__":
    rep_man = ReportManager("bug_info", "crash{no}.xml",
                            max_no_files=1, max_files_size=MiB)

    print(rep_man.files)
    print(rep_man.next_filename)
    print(rep_man.directory_size_str)
    print(rep_man.first_modified_filename)

    rep_man.size_checks()

    print(rep_man.files)
    print(rep_man.next_filename)
    print(rep_man.directory_size_str)
    print(rep_man.first_modified_filename)
