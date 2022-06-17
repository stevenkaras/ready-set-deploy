from typing import Iterable
import pathlib
import unittest


def find_test_files(filename: str) -> Iterable[pathlib.Path]:
    """
    Search for files that are likely unittests associated with the given filename
    """
    file = pathlib.Path(filename)
    pattern = f"test_{file.stem}.py"
    root = file.parent
    while root.parent != root:
        testdirs = [child for child in root.iterdir() if child.is_dir() and child.name in ("test", "tests")]
        for testdir in testdirs:
            yield from testdir.rglob(pattern)

        root = root.parent


def find_and_run_unittests(filename: str):
    """
    Locate and run the unittests associated with the given __file__
    """
    for testfile in find_test_files(filename):
        tests = unittest.defaultTestLoader.discover(str(testfile.parent), pattern=testfile.name)
        runner = unittest.TextTestRunner()
        runner.run(tests)
