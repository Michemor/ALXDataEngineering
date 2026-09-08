"""
We will extract data from the NASA POWER site.
Target data will be temperature, precipitation and related
weather data for Uasin Gishu, TransNzoia, Nakuru and Bungoma.
"""
import requests, json, os
from src.etl.config import startdate, enddate, locations, parameters
from pathlib import Path
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

def fetch_weather_data(latitude, longitude):
    """
    Extract data from the NASA POWER site for the specified locations.
    Returns a dictionary containing the extracted data, or None if request fails.
    """
    params = {
        "start": startdate,
        "end": enddate,
        "latitude": latitude,
        "longitude": longitude,
        "parameters": ",".join(parameters),
        "community": "ag",
        "format": "json",
        "header": "true",
    }

    retry_strategy = Retry(
        total=3,  # Total number of retries
        backoff_factor=1,  # Wait time between retries (in seconds)
        status_forcelist=[429, 500, 502, 503, 504], 
        allowed_methods=["GET"]  # Retry on these methods
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        response = session.get(BASE_URL, params=params, timeout=60)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API request failed with status code {response.status_code}.")
            try:
                print(f"Error message: {response.json()}")
            except ValueError:
                print(f"Error response text: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def split_by_year(data):
    """
    Split one multi-year dataset into yearly chunks
    {year: {parameter: {date: value}}}.
    Returns a dictionary where each key is a year and the value is the corresponding data for that year.
    """
    if not data or "properties" not in data or "parameter" not in data["properties"]:
        return {}

    yearly_data = {}
    for param_name, values in data["properties"]["parameter"].items():
        for date_str, val in values.items():
            year = date_str[:4]
            yearly_data.setdefault(year, {}).setdefault(param_name, {})[date_str] = val
    return yearly_data

def save_raw_data(year_data, location_name, year, raw_dir="data/raw"):
    """
    Save the raw data for a specific year and location to a JSON file.
    The file will be saved in the specified raw_dir with the format: {location_name}_{year}.json.
    """
    os.makedirs(raw_dir, exist_ok=True)
    location_name = format_location_name(location_name)
    file_path = Path(raw_dir) / f"{location_name}_{year}.json"
    with open(file_path, "w") as f:
        json.dump(year_data, f, indent=4)

    return file_path

def run_data_extraction():
    for location_key, location in locations.items():
        print(f"Extracting data for {location['name']}...")
        data = fetch_weather_data(location['latitude'], location['longitude'])
        if not data:
            print(f"Failed to fetch data for {location['name']}. Skipping...")
            continue

        yearly_data = split_by_year(data)
        for year, year_data in yearly_data.items():
            file_path = save_raw_data(year_data, location['name'], year)
            if year_data:
                first_param_data = next(iter(year_data.values()), {})
                day_count = len(first_param_data)
            else:
                day_count = 0
            print(f"Saved raw data for {year}: {day_count} days to {file_path}")
    return "Data extraction completed."


def get_county_files(county_name, raw_dir="data/raw"):
    """
    Get a list of JSON files for a specific county in the raw data directory.
    Returns a list of file paths.
    """
    raw_dir_path = Path(raw_dir)
    if not raw_dir_path.exists():
        print(f"Directory {raw_dir} does not exist.")
        return []

    county_files = list(raw_dir_path.glob(f"{county_name.lower()}_*.json"))
    return county_files

def format_location_name(location_name):
    """
    Format the location name to match the expected file naming convention.
    Converts to lowercase and replaces spaces with underscores.
    """
    return location_name.lower().replace(" ", "_")