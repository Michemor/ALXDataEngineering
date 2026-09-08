import unittest
from unittest.mock import patch, MagicMock
from src.etl.extract import fetch_weather_data, split_by_year, save_raw_data, run_data_extraction
from src.etl.config import locations


class TestExtract(unittest.TestCase):
    @patch("requests.Session.get")
    def test_fetch_weather_data(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"properties": {"parameter": {}}}
        mock_get.return_value = mock_response

        result = fetch_weather_data(locations["location1"]["latitude"], locations["location1"]["longitude"])
        self.assertIsInstance(result, dict)

    def test_split_by_year(self):
        sample_data = {
            "properties": {
                "parameter": {
                    "T2M": {
                        "20230101": 25.0,
                        "20230102": 26.0,
                        "20240101": 24.0,
                    }
                }
            }
        }
        expected_output = {
            "2023": {
                "T2M": {
                    "20230101": 25.0,
                    "20230102": 26.0,
                }
            },
            "2024": {
                "T2M": {
                    "20240101": 24.0,
                }
            }
        }
        result = split_by_year(sample_data)
        self.assertEqual(result, expected_output)

    def test_save_raw_data(self):
        sample_year_data = {
            "T2M": {
                "20230101": 25.0,
                "20230102": 26.0,
            }
        }
        location_name = "TestLocation"
        year = "2023"
        file_path = save_raw_data(sample_year_data, location_name, year, raw_dir="test_data/raw")

        self.assertTrue(file_path.exists())
        file_path.unlink()

    @patch("src.etl.extract.fetch_weather_data")
    def test_run_data_extraction(self, mock_fetch):
        mock_fetch.return_value = {
            "properties": {
                "parameter": {
                    "T2M": {
                        "20230101": 25.0,
                    }
                }
            }
        }
        result = run_data_extraction()
        self.assertEqual(result, "Data extraction completed.")


if __name__ == "__main__":
    unittest.main()