import unittest
from datetime import time as dtime

from app.common import norm_num, parse_time_value, to_iso


class CommonTests(unittest.TestCase):
    def test_norm_num(self):
        self.assertEqual(norm_num(200.0), "200")
        self.assertEqual(norm_num("200-1"), "200")

    def test_to_iso(self):
        self.assertEqual(to_iso("10/05/2026"), "2026-10-05")

    def test_parse_time_value(self):
        self.assertEqual(parse_time_value("7:45 AM"), ("time", dtime(7, 45)))
        self.assertEqual(parse_time_value("Will Call"), ("willcall", None))
