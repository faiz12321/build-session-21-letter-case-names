"""Makes a made-up list of file names and a small folder to practise on.

Run: python make_sample.py
The list holds names that would collide on a case-insensitive file system, so they
stay as text. Only ordinary files with different names are created.
"""
from pathlib import Path
import stat

NAMES = [
    "Report.docx",
    "notes.txt",
    "photo1.jpg",
    "report.DOCX",
    "Notes.txt",
    "docs/Plan.txt",
    "budget.xlsx",
    "NOTES.TXT",
    "Photo2.jpg",
    "docs/plan.txt",
]


def make(folder):
    folder = Path(folder).absolute()
    if '..' in folder.parts:
        raise OSError('Parent-traversal setup paths are unsupported.')
    for parent in reversed(folder.parents):
        info = parent.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise OSError('Linked/reparse parents are unsupported.')
    folder.mkdir()
    with (folder / "names.txt").open("xb") as handle:
        handle.write(("\n".join(NAMES) + "\n").encode("utf-8"))
    tree = folder / "tree"
    (tree / "docs").mkdir(parents=True)
    with (tree / "Readme.txt").open("xb") as handle: handle.write(b"hello\n")
    with (tree / "docs" / "plan.txt").open("xb") as handle: handle.write(b"plan\n")
    with (tree / "docs" / "Plan v2.txt").open("xb") as handle: handle.write(b"plan\n")
    return folder


if __name__ == "__main__":
    try:
        make(Path(__file__).absolute().parent / "sample")
    except FileExistsError:
        raise SystemExit("Stopped: sample already exists. Nothing was replaced or deleted.")
    print("Made sample/names.txt and sample/tree with three small files")
