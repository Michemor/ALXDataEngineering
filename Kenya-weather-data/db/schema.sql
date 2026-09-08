-------- schema for weather data tables ---



--- Counties
CREATE TABLE IF NOT EXISTS counties (
    county_id   VARCHAR(6) PRIMARY KEY,
    county_name VARCHAR(50) NOT NULL UNIQUE,
    latitude    NUMERIC(9,6) NOT NULL,
    longitude   NUMERIC(9,6) NOT NULL
);


--- Seasons
CREATE TABLE IF NOT EXISTS seasons (
    season_id    SERIAL PRIMARY KEY,
    season_name  VARCHAR(30) NOT NULL UNIQUE,
    start_month  SMALLINT NOT NULL,
    end_month    SMALLINT NOT NULL
);


CREATE TABLE IF NOT EXISTS daily_weather (
    weather_id   SERIAL PRIMARY KEY,
    county_id    VARCHAR(6) NOT NULL REFERENCES counties(county_id),
    season_id    INTEGER REFERENCES seasons(season_id),
    date         DATE NOT NULL,
    temp_avg_c   NUMERIC(6,2),
    temp_max_c   NUMERIC(6,2),
    temp_min_c   NUMERIC(6,2),
    precip_mm    NUMERIC(8,2),
    wind_speed_ms NUMERIC(6,2),
    solar_radiation_kwh_m2 NUMERIC(8,2),
    humidity_pct NUMERIC(6,2),
    soil_moisture_top NUMERIC(5,3),
    UNIQUE (county_id, date)
);

CREATE TABLE IF NOT EXISTS county_monthly_summary (
    summary_id     SERIAL PRIMARY KEY,
    county_id      VARCHAR(6) NOT NULL REFERENCES counties(county_id),
    season_id      INTEGER REFERENCES seasons(season_id),
    year           SMALLINT NOT NULL,
    month          SMALLINT NOT NULL,
    avg_temp_c     NUMERIC(6,2),
    total_precip_mm NUMERIC(8,2),
    avg_humidity_pct NUMERIC(6,2),
    UNIQUE (county_id, year, month)
);