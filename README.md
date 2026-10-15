# Find file names that differ only in letter case

A small read-only Python tool built step by step. Give it a list of file names (a text file, one name per line) or a folder. It prints groups of names that are the same when upper and lower case are ignored, such as `Report.docx` and `report.DOCX`. It never renames, creates or changes any file.

Why it matters: Microsoft's "Case Sensitivity" page says Windows treats FOO.txt and foo.txt as the same name by default, while Linux treats them as different. Two such files can sit side by side on Linux but not in one ordinary Windows folder.

## Run it

    python make_sample.py                          # makes a made-up list and a small folder in sample/
    python casecheck.py names sample/names.txt     # check a list of names
    python casecheck.py folder sample/tree         # check the names inside a folder
    python -m unittest -v                          # twenty-six automated tests

On Windows, if `python` is not found, use `py`.

## Files

- `casecheck.py` - the tool
- `make_sample.py` - makes a made-up list of ten names (three groups differ only in case, listed only as text) and a small folder of ordinary files
- `test_casecheck.py` - tests

## Notes

- Names are compared with Python's casefold. It is a close match for ordinary letters, but a file system uses its own table, so for unusual letters the answer can differ.
- In folder mode names are compared only with the other names in the same folder. In list mode every line is compared as a whole.
- A name repeated exactly is not reported, only names that differ in case.
- Only the first 20 groups are printed. The count covers all of them.
- Names are printed with accented and special characters written as escapes, so they show on any console.
- The tool only reads names. Tests check that nothing is created or changed. No pair of names that differ only in case is ever created as files, because that would fail on Windows. The folder scan with such names is tested with a stand-in for the folder listing.
- Tested only on small made-up names. Python 3.10 and 3.12 on Linux, and, by GitHub Actions, Python 3.12 on Windows and Ubuntu. Not tested on a Windows 10 or 11 desktop or on real folders.
- Educational example, no warranty. Use at your own risk.
- Code is MIT licensed (see LICENSE). Python and the Microsoft page belong to their owners; this repository includes neither.
