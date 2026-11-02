import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from organize import OTHER, category_for, main, organize, unique_destination


class CategoryForTests(unittest.TestCase):
    def test_known_extensions(self):
        self.assertEqual(category_for(Path("photo.jpg")), "Images")
        self.assertEqual(category_for(Path("report.pdf")), "Documents")
        self.assertEqual(category_for(Path("data.csv")), "Spreadsheets")
        self.assertEqual(category_for(Path("song.mp3")), "Audio")

    def test_case_insensitive(self):
        self.assertEqual(category_for(Path("PHOTO.JPG")), "Images")

    def test_unknown_and_missing_extension(self):
        self.assertEqual(category_for(Path("thing.xyz")), OTHER)
        self.assertEqual(category_for(Path("Makefile")), OTHER)


class OrganizeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def touch(self, name, content="x"):
        path = self.dir / name
        path.write_text(content)
        return path

    def test_moves_files_into_categories(self):
        self.touch("a.png")
        self.touch("b.pdf")
        self.touch("c.unknown")
        moves = organize(self.dir)
        self.assertEqual(len(moves), 3)
        self.assertTrue((self.dir / "Images" / "a.png").exists())
        self.assertTrue((self.dir / "Documents" / "b.pdf").exists())
        self.assertTrue((self.dir / OTHER / "c.unknown").exists())
        self.assertFalse((self.dir / "a.png").exists())

    def test_dry_run_changes_nothing(self):
        self.touch("a.png")
        moves = organize(self.dir, dry_run=True)
        self.assertEqual(moves, [(self.dir / "a.png", self.dir / "Images" / "a.png")])
        self.assertTrue((self.dir / "a.png").exists())
        self.assertFalse((self.dir / "Images").exists())

    def test_skips_hidden_files_and_directories(self):
        self.touch(".DS_Store")
        (self.dir / "existing_folder").mkdir()
        self.assertEqual(organize(self.dir), [])
        self.assertTrue((self.dir / ".DS_Store").exists())
        self.assertTrue((self.dir / "existing_folder").is_dir())

    def test_skips_symlinks(self):
        target = self.touch("real.txt")
        (self.dir / "link.txt").symlink_to(target)
        organize(self.dir)
        self.assertTrue((self.dir / "link.txt").is_symlink())
        self.assertTrue((self.dir / "Documents" / "real.txt").exists())

    def test_name_collision_does_not_overwrite(self):
        (self.dir / "Images").mkdir()
        (self.dir / "Images" / "a.png").write_text("old")
        self.touch("a.png", "new")
        organize(self.dir)
        self.assertEqual((self.dir / "Images" / "a.png").read_text(), "old")
        self.assertEqual((self.dir / "Images" / "a (1).png").read_text(), "new")

    def test_skips_files_named_like_category_folders(self):
        # A file 'Other' blocks the Other/ folder, so Makefile must stay put
        # instead of crashing. 'images' does the same for Images/ on
        # case-insensitive filesystems (macOS) but not on Linux.
        self.touch("Other")
        self.touch("images")
        self.touch("a.png")
        self.touch("Makefile")
        self.touch("b.pdf")
        moves = organize(self.dir)
        self.assertTrue((self.dir / "Other").is_file())
        self.assertTrue((self.dir / "Makefile").exists())
        self.assertTrue((self.dir / "images").is_file())
        self.assertTrue((self.dir / "Documents" / "b.pdf").exists())
        moved = {src.name for src, _ in moves}
        self.assertNotIn("Other", moved)
        self.assertNotIn("images", moved)

    def test_dry_run_plans_unique_destinations(self):
        (self.dir / "Images").mkdir()
        (self.dir / "Images" / "a.png").write_text("old")
        self.touch("a.png")
        self.touch("a (1).png")
        planned = [dest for _, dest in organize(self.dir, dry_run=True)]
        self.assertEqual(len(planned), len(set(planned)))
        real = [dest for _, dest in organize(self.dir)]
        self.assertEqual(planned, real)

    def test_moves_extensionless_and_multi_dot_files(self):
        self.touch("Makefile")
        self.touch("backup.tar.gz")
        organize(self.dir)
        self.assertTrue((self.dir / OTHER / "Makefile").exists())
        self.assertTrue((self.dir / "Archives" / "backup.tar.gz").exists())

    def test_broken_symlink_at_destination_is_not_replaced(self):
        (self.dir / "Images").mkdir()
        (self.dir / "Images" / "a.png").symlink_to(self.dir / "nowhere")
        self.touch("a.png")
        organize(self.dir)
        self.assertTrue((self.dir / "Images" / "a.png").is_symlink())
        self.assertTrue((self.dir / "Images" / "a (1).png").exists())

    def test_running_twice_is_a_no_op(self):
        self.touch("a.png")
        organize(self.dir)
        self.assertEqual(organize(self.dir), [])

    def test_not_a_directory_raises(self):
        with self.assertRaises(NotADirectoryError):
            organize(self.dir / "missing")

    def test_unique_destination_counts_up(self):
        (self.dir / "f.txt").write_text("")
        (self.dir / "f (1).txt").write_text("")
        self.assertEqual(unique_destination(self.dir / "f.txt"), self.dir / "f (2).txt")


class MainTests(unittest.TestCase):
    def test_cli_dry_run_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.png").write_text("x")
            out = io.StringIO()
            with redirect_stdout(out):
                code = main([tmp, "--dry-run"])
            self.assertEqual(code, 0)
            self.assertIn("a.png -> Images/a.png", out.getvalue())
            self.assertIn("1 file(s) would be moved", out.getvalue())
            self.assertTrue(Path(tmp, "a.png").exists())

    def test_cli_bad_folder_returns_1(self):
        err = io.StringIO()
        with redirect_stderr(err):
            code = main(["/definitely/not/here"])
        self.assertEqual(code, 1)
        self.assertIn("Not a directory", err.getvalue())

    def test_cli_unreadable_folder_returns_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            locked = Path(tmp, "locked")
            locked.mkdir(mode=0o000)
            try:
                err = io.StringIO()
                with redirect_stderr(err):
                    code = main([str(locked)])
                self.assertEqual(code, 1)
                self.assertIn("Permission denied", err.getvalue())
            finally:
                locked.chmod(0o755)


if __name__ == "__main__":
    unittest.main()
