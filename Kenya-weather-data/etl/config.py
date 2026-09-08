"""
Contains configuration for the ETL process.
"""

startdate = "20230101"
enddate = "20260731"

locations = {
    "location1": {
        "name": "Uasin Gishu",
        "latitude": -0.5167,
        "longitude": 35.2833
    },
    "location2": {
        "name": "Trans Nzoia",
        "latitude": 0.2833,
        "longitude": 35.2833
    },
    "location3": {
        "name": "Nakuru",
        "latitude": -0.2833,
        "longitude": 36.0667
    },
    "location4": {
        "name": "Bungoma",
        "latitude": 0.5667,
        "longitude": 34.5667
    }
}

parameters = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "WS2M", "ALLSKY_SFC_SW_DWN", "RH2M", "GWETTOP"]