"""
Kitten image getter
"""

import requests, json
from pathlib import Path
import requests.exceptions as request_exceptions


def _get_kitten_urls(json_file: str, save_path: str):
    """
    Fetches a list of kitten image URLs from a predefined source.
    Returns:
        list: A list of URLs pointing to kitten images.
    """

    with open(json_file, "r") as file:
        api_data = json.load(file)
        img_data_array = []
        for item in api_data:
            try:
                img_data_array.append(requests.get(item["urls"]["small"]).content)
            except request_exceptions.RequestException:
                continue

        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)

        for i, item in enumerate(api_data):
            img_path = save_path.joinpath(f"{item['id']}")
            with open(img_path, "wb") as img_file:
                img_file.write(img_data_array[i])


__all__ = ["_get_kitten_urls"]
