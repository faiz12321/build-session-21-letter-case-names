"""Makes a made-up list of file names and a small folder to practise on.

Run: python make_sample.py
The list holds names that would collide on a case-insensitive file system, so they
stay as text. Only ordinary files with different names are created.
"""
from pathlib import Path

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
    folder = Path(folder)
    folder.mkdir(exist_ok=True)
    (folder / "names.txt").write_bytes(("\n".join(NAMES) + "\n").encode("utf-8"))
    tree = folder / "tree"
    (tree / "docs").mkdir(parents=True, exist_ok=True)
    (tree / "Readme.txt").write_text("hello\n", encoding="utf-8")
    (tree / "docs" / "plan.txt").write_text("plan\n", encoding="utf-8")
    (tree / "docs" / "Plan v2.txt").write_text("plan\n", encoding="utf-8")
    return folder


if __name__ == "__main__":
    make("sample")
    print("Made sample/names.txt and sample/tree with three small files")
