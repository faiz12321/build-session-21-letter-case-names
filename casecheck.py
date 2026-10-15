"""Finds file names that differ only in upper and lower case letters.

Run: python casecheck.py names LIST.txt
     python casecheck.py folder FOLDER
Exit code: 0 = none found, 1 = some found, 2 = could not read.
It only reads names. It never renames, creates or changes a file.
"""
import os
import sys

SHOW = 20  # how many groups to print


def find_groups(names):
    """Return groups of different names that are equal when case is ignored."""
    seen = {}
    for name in names:
        group = seen.setdefault(name.casefold(), [])
        if name not in group:
            group.append(name)
    return [group for group in seen.values() if len(group) > 1]


def read_names(path):
    with open(path, encoding="utf-8-sig") as f:
        text = f.read()
    return [line for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line != ""]


def walk(folder):
    """Yield (folder path, names inside it) for the folder and every folder under it."""
    for dirpath, dirnames, filenames in os.walk(folder):
        yield dirpath, dirnames + filenames


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
