"""
Unit Tests for Data Cleaning & Normalization inside load_to_staging.py.
Allows offline validation of cleaning operations in CI/CD.
"""

import unittest
import pandas as pd
import json
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from pipeline.etl.load.load_to_staging import clean_and_normalize


class TestDataCleaning(unittest.TestCase):

    def test_clean_and_normalize(self):
        # Create a sample raw dataframe with issues:
        # - Row 1: Normal row
        # - Row 2: Duplicate source_id (should be dropped, leaving Row 3)
        # - Row 3: Latest duplicate source_id (should keep this one)
        # - Row 4: Missing title (should be dropped)
        # - Row 5: Missing source_id (should be dropped)
        # - Row 6: Unstripped strings & invalid JSON
        raw_data = [
            {
                "source_id": "vnw_1",
                "title": " Data Engineer ",
                "company_name": "Tech Corp",
                "location_cities": '["HCM"]',
                "salary_min": "1000",
                "salary_max": "2000",
                "skills": '["Python"]',
                "benefits": '["Insurance"]',
            },
            {
                "source_id": "vnw_2",
                "title": "Old Duplicate",
                "company_name": "A Company",
                "location_cities": "[]",
                "salary_min": "0",
                "salary_max": "0",
                "skills": "[]",
                "benefits": "[]",
            },
            {
                "source_id": "vnw_2",
                "title": "New Duplicate",
                "company_name": "A Company",
                "location_cities": "[]",
                "salary_min": "500",
                "salary_max": "1000",
                "skills": "[]",
                "benefits": "[]",
            },
            {
                "source_id": "vnw_3",
                "title": None,  # Null title
                "company_name": "B Company",
                "location_cities": "[]",
            },
            {
                "source_id": "",  # Empty source_id
                "title": "Valid Title",
                "company_name": "C Company",
                "location_cities": "[]",
            },
            {
                "source_id": "vnw_4",
                "title": "Frontend Developer",
                "company_name": None,  # Null company_name
                "location_cities": "invalid_json_array",  # Invalid JSON
                "salary_min": None,
                "salary_max": "not_a_number",
            },
        ]

        df_raw = pd.DataFrame(raw_data)
        df_cleaned = clean_and_normalize(df_raw)

        # Assertions
        # 1. Row count should be 3 (vnw_1, vnw_2 (latest duplicate), and vnw_4)
        self.assertEqual(len(df_cleaned), 3)

        # 2. Duplicate handling: check that the latest vnw_2 is kept
        vnw_2_row = df_cleaned[df_cleaned["source_id"] == "vnw_2"].iloc[0]
        self.assertEqual(vnw_2_row["title"], "New Duplicate")
        self.assertEqual(int(vnw_2_row["salary_min"]), 500)

        # 3. String stripping and capitalization
        vnw_1_row = df_cleaned[df_cleaned["source_id"] == "vnw_1"].iloc[0]
        self.assertEqual(vnw_1_row["title"], "Data Engineer")

        # 4. Null replacement and defaults
        vnw_4_row = df_cleaned[df_cleaned["source_id"] == "vnw_4"].iloc[0]
        self.assertEqual(vnw_4_row["company_name"], "Unknown Company")
        self.assertEqual(int(vnw_4_row["salary_min"]), 0)
        self.assertEqual(int(vnw_4_row["salary_max"]), 0)
        self.assertEqual(vnw_4_row["location_cities"], "[]")


if __name__ == "__main__":
    unittest.main()
