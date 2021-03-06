# coding=utf-8

import unittest

from dmutils.presenters import Presenters
presenters = Presenters()


class TestPresenters(unittest.TestCase):
    def test_service_id(self):
        G5 = presenters.present(
            "5.G5.12345",
            {"type": "service_id"}
        )
        G6 = presenters.present(
            "1234567891023456",
            {"type": "service_id"}
        )
        self.assertEqual(
            G5,
            ["5.G5.12345"]
        )
        self.assertEqual(
            G6,
            ["1234", "5678", "9102", "3456"]
        )

    def test_upload(self):
        file = presenters.present(
            "http://example.com/path/to/file.pdf",
            {"type": "upload"}
        )
        self.assertEqual(
            file,
            {
                "url": "http://example.com/path/to/file.pdf",
                "filename": "file.pdf"
            }
        )

    def test_boolean(self):
        yes = presenters.present(
            True,
            {"type": "boolean"}
        )
        no = presenters.present(
            False,
            {"type": "boolean"}
        )
        nothing = presenters.present(
            None,
            {"type": "boolean"}
        )
        empty = presenters.present(
            "",
            {"type": "boolean"}
        )
        self.assertEqual(yes, "Yes")
        self.assertEqual(no, "No")
        self.assertEqual(nothing, "")
        self.assertEqual(empty, "")
