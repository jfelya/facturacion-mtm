import unittest

from app.ui import status_of


class StatusTests(unittest.TestCase):
    def test_revisar_with_driver_and_milage_is_not_ok(self):
        row = {"driver": "200", "milage": 5.0, "flag": "revisar"}
        self.assertEqual(status_of(row), "REVISAR")

    def test_nota_with_driver_and_milage_stays_nota(self):
        row = {"driver": "200", "milage": 5.0, "flag": "nota"}
        self.assertEqual(status_of(row), "NOTA")


if __name__ == "__main__":
    unittest.main()
