import pathlib
import re


def next_filename(directory, patten, num_sub="no"):
    num_sub = "{{{}}}".format(num_sub)
    if num_sub not in patten:
        return ValueError("Number substitution not in patten")
    re_patten = re.compile(re.escape(patten).replace(re.escape(num_sub),
                                                     r"(?P<num>\d+)"))
    last_report_num = -1
    for fname in pathlib.Path(directory).iterdir():
        m = re_patten.match(fname.name)
        print(fname, m, re_patten)
        if m:
            last_report_num = max(last_report_num, int(m.group("num")))
    return str(pathlib.Path(directory) / patten.format(no=last_report_num + 1))
