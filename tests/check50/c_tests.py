import os
import pathlib
import shutil
import sys
import tempfile
import unittest

import bootcs.check as check50
from bootcs.check import c as check50_c
from bootcs.check import internal as check50_internal

CLANG_INSTALLED = bool(shutil.which("clang"))
VALGRIND_INSTALLED = bool(shutil.which("valgrind"))
CHECKS_DIRECTORY = pathlib.Path(__file__).absolute().parent / "checks"


class Base(unittest.TestCase):
    def setUp(self):
        if not CLANG_INSTALLED:
            raise unittest.SkipTest("clang not installed")
        if not VALGRIND_INSTALLED:
            raise unittest.SkipTest("valgrind not installed")

        self.working_directory = tempfile.TemporaryDirectory()
        os.chdir(self.working_directory.name)

    def tearDown(self):
        self.working_directory.cleanup()


class TestCompile(Base):
    def test_compile_incorrect(self):
        open("blank.c", "w").close()

        with self.assertRaises(check50.Failure):
            check50_c.compile("blank.c")

    def test_compile_hello_world(self):
        with open("hello.c", "w") as f:
            src = '#include <stdio.h>\nint main() {\n    printf("hello, world!\\n");\n}'
            f.write(src)

        check50_c.compile("hello.c")

        self.assertTrue(os.path.isfile("hello"))
        check50.run("./hello").stdout("hello, world!", regex=False)


class TestValgrind(Base):
    def setUp(self):
        super().setUp()
        if not (sys.platform == "linux" or sys.platform == "linux2"):
            raise unittest.SkipTest(
                "skipping valgrind checks under anything other than Linux due to false positives"
            )

    def test_no_leak(self):
        check50_internal.check_running = True
        with open("foo.c", "w") as f:
            src = "int main() {}"
            f.write(src)

        check50_c.compile("foo.c")
        with check50_internal.register:
            check50_c.valgrind("./foo").exit()
        check50_internal.check_running = False

    def test_leak(self):
        check50_internal.check_running = True
        with open("leak.c", "w") as f:
            src = (
                "#include <stdlib.h>\n"
                "void leak() {malloc(sizeof(int));}\n"
                "int main() {\n"
                "    leak();\n"
                "}"
            )
            f.write(src)

        check50_c.compile("leak.c")
        with self.assertRaises(check50.Failure):
            with check50_internal.register:
                check50_c.valgrind("./leak").exit()
        check50_internal.check_running = False


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(module=sys.modules[__name__])
    unittest.TextTestRunner(verbosity=2).run(suite)
