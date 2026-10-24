import unittest

from src.exporter import encode_public_row


class PublicExportContractTests(unittest.TestCase):
    def test_preserves_stable_fields_and_excludes_machine_specific_path(self) -> None:
        self.assertEqual(
            encode_public_row(
                {"id": "row-1", "value": "safe", "source_path": "/home/user/private"}
            ),
            {"id": "row-1", "value": "safe"},
        )


if __name__ == "__main__":
    unittest.main()
