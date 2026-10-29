import unittest

from app.strings import STRINGS


class StringsTests(unittest.TestCase):
    def test_languages_have_the_same_keys(self):
        self.assertEqual(set(STRINGS["es"]), set(STRINGS["en"]))


if __name__ == "__main__":
    unittest.main()
