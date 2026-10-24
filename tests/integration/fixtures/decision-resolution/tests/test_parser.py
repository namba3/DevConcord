import unittest

from src.parser import parse_row


class InternalParserTests(unittest.TestCase):
    def test_parses_required_fields(self) -> None:
        self.assertEqual(parse_row({"id": "row-1", "value": "safe"}), {"id": "row-1", "value": "safe"})

    def test_rejects_malformed_input_without_echoing_it(self) -> None:
        machine_specific_value = "machine-specific-path-value"
        with self.assertRaisesRegex(ValueError, "^invalid row$") as raised:
            parse_row({"id": "row-1", "source_path": machine_specific_value})
        self.assertNotIn(machine_specific_value, str(raised.exception))


if __name__ == "__main__":
    unittest.main()
