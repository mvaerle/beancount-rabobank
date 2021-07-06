import unittest
from os import path

from beancount.ingest import regression_pytest as regtest
from . import rabobank

IMPORTER = rabobank.Importer("EUR", "Assets:Rabobank:Checkings")


@regtest.with_importer(IMPORTER)
@regtest.with_testdir(path.join(path.dirname(__file__), "test_files"))
class TestImporter(regtest.ImporterTestBase):
    pass


if __name__ == '__main__':
    unittest.main()
