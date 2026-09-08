# src/etl/transform.py

import json
import pandas as pd
from pathlib import Path
from src.etl.extract import get_county_files
import time
from geopy.geocoders import Nominatim


def load_county_data(county_name: str, raw_dir: str = "data/raw") -> dict:
    """
    Load and merge all yearly JSON files for a given county into one
    combined {parameter: {date: value}} structure spanning all years.
    """
    files = get_county_files(county_name, raw_dir)
    if not files:
        raise FileNotFoundError(f"No raw files found for county: {county_name}")

    merged = {}
    for file_path in sorted(files):
        with open(file_path, "r") as f:
            year_data = json.load(f)

        for param, date_values in year_data.items():
            merged.setdefault(param, {}).update(date_values)

    return merged


def reshape_to_dataframe(county_data: dict, county_name: str) -> pd.DataFrame:
    """
    Convert a {parameter: {date: value}} dict into a tidy wide DataFrame:
    one row per date, one column per parameter, plus a county column.
    """
    df = pd.DataFrame(county_data)
    df.index.name = "date"
    df = df.reset_index()

    # Convert date strings ("20230101") to real datetime
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")

    # Tag every row with the county it came from
    df["county"] = county_name

    # Sort chronologically — files were merged in file order, not necessarily date order
    df = df.sort_values("date").reset_index(drop=True)

    return df


def counties_data(county_names):
    geolocator = Nominatim(user_agent="weather_map_app")
    records = []

    for i, (county_name, query) in enumerate(county_names.items(), start=1):
        location = geolocator.geocode(query)
        if location is None:
            raise ValueError(f"Geocoding failed for {query} - check the query string")

        records.append({
            "county_id": i,
            "county_name": county_name,
            "latitude": location.latitude,
            "longitude": location.longitude,
        })
        time.sleep(1)

    return pd.DataFrame(records)

def seasons_data():
        seasons_df = pd.DataFrame([
            {"season_id": 1, "season_name": "long_rains",  "start_month": 3,  "end_month": 5},
            {"season_id": 2, "season_name": "dry_season_1", "start_month": 6,  "end_month": 9},
            {"season_id": 3, "season_name": "short_rains", "start_month": 10, "end_month": 12},
            {"season_id": 4, "season_name": "dry_season_2", "start_month": 1,  "end_month": 2},
        ])

        return seasons_df

def _month_to_season(month, seasons_df):
    for _, row in seasons_df.iterrows():
        if row["start_month"] <= row["end_month"]:
            if row["start_month"] <= month <= row["end_month"]:
                return row["season_id"]
        else:
            if month >= row["start_month"] or month <= row["end_month"]:
                return row["season_id"]
    return None

def build_daily_weather_df(weather_df: pd.DataFrame, counties_df: pd.DataFrame, seasons_df: pd.DataFrame) -> pd.DataFrame:
    """
    Take the raw combined weather dataframe and turn it into the
    load-ready daily_weather table: renamed columns, county_id FK,
    season_id FK, no leftover text/helper columns.
    """
    column_rename_map = {
        "T2M": "temp_avg_c",
        "T2M_MAX": "temp_max_c",
        "T2M_MIN": "temp_min_c",
        "PRECTOTCORR": "precip_mm",
        "WS2M": "wind_speed_ms",
        "ALLSKY_SFC_SW_DWN": "solar_radiation_kwh_m2",
        "RH2M": "humidity_pct",
        "GWETTOP": "soil_moisture_top", 
    }
    df = weather_df.rename(columns=column_rename_map)

    # Map each county to its id
    county_id_map = dict(zip(counties_df["county_name"], counties_df["county_id"]))
    df["county_id"] = df["county"].map(county_id_map)

    # Map each month to its season
    df["season_id"] = df["date"].dt.month.apply(lambda m: _month_to_season(m, seasons_df))
    if df["county_id"].isna().any():
        raise ValueError("Some rows failed to map to a county_id — check county name spelling")
    if df["season_id"].isna().any():
        raise ValueError("Some rows failed to map to a season_id — check season month ranges")

    df = df.drop(columns=["county"])

    return df


def monthly_summary(daily_weather_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate daily_weather to one row per county per month.
    """
    df = daily_weather_df.copy()
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    grouped = (
        df.groupby(["county_id", "year", "month"])
        .agg(
            avg_temp_c=("temp_avg_c", "mean"),
            total_precip_mm=("precip_mm", "sum"),
            avg_humidity_pct=("humidity_pct", "mean"),
            season_id=("season_id", lambda x: x.mode().iloc[0]),  # most common season that month
        )
        .reset_index()
    )
    return grouped



    