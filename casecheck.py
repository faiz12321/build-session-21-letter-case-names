"""Finds file names that differ only in upper and lower case letters.

Run: python casecheck.py names LIST.txt
     python casecheck.py folder FOLDER
Exit code: 0 = none found, 1 = some found, 2 = could not read.
It only reads names. It never renames, creates or changes a file.
"""
import os
import sys
import stat
from pathlib import Path

SHOW = 20  # how many groups to print


def find_groups(names):
    """Return groups of different names that are equal when case is ignored."""
    seen = {}
    for name in names:
        group = seen.setdefault(name.casefold(), [])
        if name not in group:
            group.append(name)
    return [group for group in seen.values() if len(group) > 1]


def safe_input(value, directory=False):
    path = Path(value).absolute()
    if '..' in path.parts:
        raise OSError('Parent-traversal paths are unsupported.')
    for part in [*reversed(path.parents), path]:
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0) & 0x400:
            raise OSError('Links/reparse points are unsupported.')
    info = path.lstat()
    if directory:
        if not stat.S_ISDIR(info.st_mode):
            raise OSError('Expected an ordinary directory.')
    elif not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise OSError('Expected an ordinary singly linked file.')
    return path


def read_names(path):
    path = safe_input(path)
    with open(path, encoding="utf-8-sig") as f:
        text = f.read()
    return [line for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line != ""]


def walk(folder):
    """Yield each verified directory and its immediate names. Errors propagate."""
    folder = safe_input(folder, directory=True)
    stack = [folder]
    count = 0
    while stack:
        current = stack.pop()
        safe_input(current, directory=True)
        names = []
        with os.scandir(current) as entries:
            for entry in entries:
                count += 1
                if count > 10000:
                    raise OSError('More than 10000 entries; refusing this tree.')
                info = entry.stat(follow_symlinks=False)
                directory = stat.S_ISDIR(info.st_mode)
                child = safe_input(entry.path, directory=directory)
                names.append(entry.name)
                if directory:
                    stack.append(child)
        yield str(current), names


def scan_folder(folder):
    count = 0
    found = []
    for dirpath, names in walk(folder):
        count += len(names)
        place = os.path.relpath(dirpath, folder)
        for group in find_groups(names):
            found.append((place, group))
    return count, found


def report(count, found):
    print("Names checked:", count)
    if not found:
        print("No names found that differ only in letter case.")
        print("That does not mean the names will work on every system.")
        return 0
    print("Groups of names that differ only in letter case:", len(found))
    for place, group in found[:SHOW]:
        where = "" if place == "." else f"in {ascii(place)}: "
        print("  " + where + ", ".join(ascii(n) for n in group))
    if len(found) > SHOW:
        print("  ... and", len(found) - SHOW, "more. Showing the first", str(SHOW) + ".")
    print("Nothing was renamed or changed.")
    return 1


def main(argv):
    if len(argv) != 3 or argv[1] not in ("names", "folder"):
        print("Usage: python casecheck.py names LIST.txt")
        print("       python casecheck.py folder FOLDER")
        return 2
    try:
        if argv[1] == "names":
            names = read_names(argv[2])
            return report(len(names), [(".", g) for g in find_groups(names)])
        if not os.path.isdir(argv[2]):
            print("Not a folder:", argv[2])
            return 2
        count, found = scan_folder(argv[2])
        return report(count, found)
    except UnicodeDecodeError:
        print("The list is not valid UTF-8 text.")
        return 2
    except OSError as e:
        print("Could not read:", e)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
