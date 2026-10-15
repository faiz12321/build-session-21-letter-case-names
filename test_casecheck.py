import io
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import casecheck
import make_sample


def run(*args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = casecheck.main(["casecheck.py", *map(str, args)])
    return code, buf.getvalue()


class Groups(unittest.TestCase):
    def test_no_collision(self):
        self.assertEqual(casecheck.find_groups(["a.txt", "b.txt"]), [])

    def test_two_names(self):
        self.assertEqual(casecheck.find_groups(["Foo.txt", "foo.txt"]), [["Foo.txt", "foo.txt"]])

    def test_three_names_one_group(self):
        self.assertEqual(casecheck.find_groups(["a", "A", "a"]), [["a", "A"]])

    def test_same_name_twice_is_not_a_collision(self):
        self.assertEqual(casecheck.find_groups(["a.txt", "a.txt"]), [])

    def test_two_separate_groups(self):
        self.assertEqual(len(casecheck.find_groups(["a", "A", "b", "B", "c"])), 2)

    def test_order_of_first_appearance(self):
        self.assertEqual(casecheck.find_groups(["b", "A", "a", "B"]), [["b", "B"], ["A", "a"]])

    def test_different_text_is_not_a_collision(self):
        self.assertEqual(casecheck.find_groups(["a.txt", "a.txt.bak", "A1.txt"]), [])

    def test_accented_letters(self):
        self.assertEqual(len(casecheck.find_groups(["\u00e9cole", "\u00c9COLE"])), 1)

    def test_empty_list(self):
        self.assertEqual(casecheck.find_groups([]), [])


class Names(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def write(self, data):
        p = Path(self.tmp) / "list.txt"
        p.write_bytes(data)
        return p

    def test_sample_list(self):
        folder = make_sample.make(Path(self.tmp) / "s")
        code, out = run("names", folder / "names.txt")
        self.assertEqual(code, 1)
        self.assertIn("Names checked: 10", out)
        self.assertIn("differ only in letter case: 3", out)
        self.assertIn("'notes.txt', 'Notes.txt', 'NOTES.TXT'", out)

    def test_clean_list(self):
        code, out = run("names", self.write(b"a.txt\nb.txt\n"))
        self.assertEqual(code, 0)
        self.assertIn("No names found", out)

    def test_windows_line_endings_in_list(self):
        code, out = run("names", self.write(b"A.txt\r\na.txt\r\n"))
        self.assertEqual(code, 1)
        self.assertIn("'A.txt', 'a.txt'", out)

    def test_blank_lines_skipped(self):
        code, out = run("names", self.write(b"\n\nA\n\na\n"))
        self.assertIn("Names checked: 2", out)

    def test_only_first_20_shown(self):
        lines = "".join(f"n{i}\nN{i}\n" for i in range(25)).encode()
        code, out = run("names", self.write(lines))
        self.assertIn("differ only in letter case: 25", out)
        self.assertIn("and 5 more. Showing the first 20.", out)
        self.assertNotIn("'n24'", out)

    def test_missing_list(self):
        code, out = run("names", Path(self.tmp) / "nope.txt")
        self.assertEqual(code, 2)
        self.assertIn("Could not read", out)

    def test_not_utf8(self):
        code, out = run("names", self.write(b"\xff\xfe\x00bad"))
        self.assertEqual(code, 2)
        self.assertIn("not valid UTF-8", out)

    def test_usage(self):
        self.assertEqual(run()[0], 2)
        self.assertEqual(run("oops", "x")[0], 2)

    def test_special_names_printed_as_escapes(self):
        code, out = run("names", self.write("caf\u00e9\nCAF\u00c9\n".encode("utf-8")))
        self.assertIn("\\xe9", out)
        self.assertIn("\\xc9", out)


class Folder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_sample_folder_is_clean(self):
        folder = make_sample.make(Path(self.tmp) / "s")
        code, out = run("folder", folder / "tree")
        self.assertEqual(code, 0)
        self.assertIn("Names checked: 4", out)

    def test_collision_inside_one_folder(self):
        fake = [("/x", ["docs"], ["a.txt"]), ("/x/docs", [], ["Plan.txt", "plan.txt"])]
        with mock.patch("os.walk", return_value=fake):
            count, found = casecheck.scan_folder("/x")
        self.assertEqual(count, 4)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][1], ["Plan.txt", "plan.txt"])

    def test_same_name_in_different_folders_is_fine(self):
        fake = [("/x", ["docs", "DOCS2"], ["a.txt"]), ("/x/docs", [], ["a.txt"]), ("/x/DOCS2", [], ["A.txt"])]
        with mock.patch("os.walk", return_value=fake):
            count, found = casecheck.scan_folder("/x")
        self.assertEqual(found, [])

    def test_folder_and_file_with_same_name_apart_from_case(self):
        fake = [("/x", ["Docs"], ["docs"])]
        with mock.patch("os.walk", return_value=fake):
            count, found = casecheck.scan_folder("/x")
        self.assertEqual(len(found), 1)

    def test_folder_report_names_the_folder(self):
        fake = [("/x", ["docs"], []), ("/x/docs", [], ["A", "a"])]
        with mock.patch("os.walk", return_value=fake), mock.patch("os.path.isdir", return_value=True):
            code, out = run("folder", "/x")
        self.assertEqual(code, 1)
        self.assertIn("in 'docs': 'A', 'a'", out)

    def test_not_a_folder(self):
        code, out = run("folder", Path(self.tmp) / "nope")
        self.assertEqual(code, 2)
        self.assertIn("Not a folder", out)


class ReadOnly(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def snapshot(self, folder):
        out = {}
        for dirpath, dirs, files in os.walk(folder):
            for n in dirs + files:
                p = os.path.join(dirpath, n)
                out[p] = os.path.getmtime(p) if os.path.isfile(p) else None
        return out

    def test_nothing_changed_or_created(self):
        folder = make_sample.make(Path(self.tmp) / "s")
        before = self.snapshot(folder)
        run("names", folder / "names.txt")
        run("folder", folder / "tree")
        self.assertEqual(before, self.snapshot(folder))

    def test_no_case_variant_file_is_created(self):
        folder = make_sample.make(Path(self.tmp) / "s")
        run("names", folder / "names.txt")
        self.assertEqual(sorted(os.listdir(folder)), ["names.txt", "tree"])


if __name__ == "__main__":
    unittest.main()
