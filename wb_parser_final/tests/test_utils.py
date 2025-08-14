import pytest
import sys
import os

# Add the project root to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project.selenium_parser.utils.clickhouse_insert import parse_category_levels

@pytest.mark.parametrize("category_raw, expected_category, expected_levels", [
    ("odezhda_zhenschinam_bluzki-i-rubashki", "bluzki-i-rubashki", ["bluzki-i-rubashki", "zhenschinam", "odezhda", None]),
    ("obuv_muzhskaya_kedy-i-krossovki", "kedy-i-krossovki", ["kedy-i-krossovki", "muzhskaya", "obuv", None]),
    ("aksessuary_sumki-i-ryukzaki", "sumki-i-ryukzaki", ["sumki-i-ryukzaki", "aksessuary", None, None]),
    ("elektronika", "elektronika", ["elektronika", None, None, None]),
    ("", "", [None, None, None, None]),
    ("a_b_c_d_e", "e", ["e", "d", "c", "b"]), # Test with more than 4 levels
])
def test_parse_category_levels(category_raw, expected_category, expected_levels):
    """
    Tests the category parsing logic with various inputs.
    """
    category, levels = parse_category_levels(category_raw)
    assert category == expected_category
    assert levels == expected_levels
