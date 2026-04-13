from django.test import TestCase

from apps.connections.connectors.base import BaseConnector, InvalidTableNameError


class TableNameValidationTest(TestCase):
    """Test SQL injection prevention via table name validation."""

    def test_valid_table_names(self):
        valid_names = [
            "employees",
            "my_table",
            "schema_v2",
            "Table123",
            "public.users",
            "_private",
        ]
        for name in valid_names:
            result = BaseConnector.validate_table_name(name)
            self.assertEqual(result, name)

    def test_rejects_sql_injection_attempts(self):
        attack_vectors = [
            "employees; DROP TABLE employees; --",
            "users' OR '1'='1",
            "table; DELETE FROM users",
            'table" UNION SELECT * FROM passwords',
            "../../etc/passwd",
            "table\nDROP TABLE users",
            "",
            " ",
            "table name with spaces",
        ]
        for attack in attack_vectors:
            with self.assertRaises(InvalidTableNameError, msg=f"Should reject: {attack!r}"):
                BaseConnector.validate_table_name(attack)

    def test_rejects_overly_long_names(self):
        long_name = "a" * 129
        with self.assertRaises(InvalidTableNameError):
            BaseConnector.validate_table_name(long_name)

    def test_max_length_name_accepted(self):
        name = "a" * 128
        result = BaseConnector.validate_table_name(name)
        self.assertEqual(result, name)
