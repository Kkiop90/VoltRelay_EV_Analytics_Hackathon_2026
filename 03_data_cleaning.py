from pathlib import Path, Path as path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "Data"/ "Raw"
CLEAN_DIR = BASE_DIR / "Data"/ "Cleaned_data"

CLEAN_DIR.mkdir(parents=True,exist_ok=True)
files =["batteries.csv",
        "city_daily_context.csv",
        "fleet_partners.csv",
        "riders.csv",
        "station_hourly_status.csv",
        "stations.csv",
        "support_tickets.csv",
        "swap_events.csv"]
data = {}
for filename in files:
    input_path = RAW_DIR / filename
    if filename == "city_daily_context.csv" and not input_path.exists():
        input_path = CLEAN_DIR / "city_daily_context_cleaned.csv"
        print(f"Raw city context file not found; using existing cleaned file: {input_path}")

    df = pd.read_csv(input_path)
    name = filename.replace(".csv", "")
    data[name]= df
    print(f"{name}: {df.shape}")

print("data load successful")
batteries = data["batteries"].copy()
print("oraginal_data:",batteries.shape)
print("exact duplicate:",batteries.duplicated().sum())
date_columns = [
    "manufacture_date",
    "commission_date",
    "retired_date"
]

for col in date_columns:
    batteries[col] = pd.to_datetime(
        batteries[col],
        errors="coerce"
    )

print("\nDate columns converted successfully!")
print(batteries[date_columns].dtypes)
numeric_columns = [
    "rated_capacity_kwh",
    "purchase_cost_inr",
    "initial_soh_pct",
    "current_soh_pct"
]

for col in numeric_columns:
    batteries[col] = pd.to_numeric(
        batteries[col],
        errors="coerce"
    )

print("\nNumerical columns converted!")
print("\nInitial SOH Summary:")
print(batteries["initial_soh_pct"].describe())

print("\nCurrent SOH Summary:")
print(batteries["current_soh_pct"].describe())

# Identify invalid SOH values
invalid_soh = batteries[
    (batteries["initial_soh_pct"] < 0) |
    (batteries["initial_soh_pct"] > 100) |
    (batteries["current_soh_pct"] < 0) |
    (batteries["current_soh_pct"] > 100)
]

print("\nInvalid SOH Records:", len(invalid_soh))
print("\nRetirement Information:")
print("Missing retirement dates:",
      batteries["retired_date"].isna().sum())

print("Missing retirement reasons:",
      batteries["retirement_reason"].isna().sum())

batteries.to_csv(
    CLEAN_DIR / "batteries_cleaned.csv",
    index=False
)

print("\nBattery cleaning completed!")
print("Final Shape:", batteries.shape)

##city daily_context cleaing
# City Daily Context Cleaning

city = data["city_daily_context"].copy()
city["date"] = pd.to_datetime(city["date"], errors="coerce")

city["city"] = city["city"].str.strip()

city["city"] = city["city"].replace({
    "Bangalore": "Bengaluru",
    "bangalore": "Bengaluru",
    "Delhi ncr": "Delhi NCR",
    "Delhi Ncr": "Delhi NCR"
})

numeric_columns = [
    "max_temp_c",
    "min_temp_c",
    "rainfall_mm",
    "grid_outage_hours"
]

for col in numeric_columns:
    city[col] = pd.to_numeric(city[col], errors="coerce")

print("Cleaned data:", city.shape)
print("\nMissing values after cleaning:")
print(city.isnull().sum())

print("\nUnique cities:")
print(city["city"].unique())

city.to_csv(CLEAN_DIR / "city_daily_context_cleaned.csv", index=False)

print("\nCity dataset cleaning successful")

#fleet parteners.csv
# Fleet Partners Cleaning

fleet = data["fleet_partners"].copy()

fleet["contract_start_date"] = pd.to_datetime(
    fleet["contract_start_date"], errors="coerce"
)

fleet["amendment_date"] = pd.to_datetime(
    fleet["amendment_date"], errors="coerce"
)

numeric_columns = [
    "discount_pct",
    "discount_pct_after_amendment",
    "payment_terms_days"
]

for col in numeric_columns:
    fleet[col] = pd.to_numeric(fleet[col], errors="coerce")

fleet["amendment_status"] = np.where(
    fleet["amendment_date"].isna(),
    "No Amendment Recorded",
    "Amendment Recorded"
)

print("\nCleaned data:", fleet.shape)

print("\nMissing values after cleaning:")
print(fleet.isnull().sum())

print("\nAmendment status:")
print(fleet["amendment_status"].value_counts())

fleet.to_csv(
    CLEAN_DIR / "fleet_partners_cleaned.csv",
    index=False
)

print("\nFleet partners cleaning successful")

# Riders Cleaning

riders = data["riders"].copy()

print("oraginal_data:", riders.shape)
print("exact duplicate:", riders.duplicated().sum())

print("\nMissing values:")
print(riders.isnull().sum())

print("\nData types:")
print(riders.dtypes)

print("\nUnique cities:")
print(riders["home_city"].unique())

print("\nData:")
print(riders.head())

riders["signup_date"] = pd.to_datetime(
    riders["signup_date"], errors="coerce"
)

riders["home_city"] = riders["home_city"].str.strip().str.lower()

riders["home_city"] = riders["home_city"].replace({
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "blr": "Bengaluru",

    "bombay": "Mumbai",
    "mum": "Mumbai",

    "hyderabad": "Hyderabad",
    "hyd": "Hyderabad",

    "pun": "Pune",
    "pune": "Pune",

    "jaipur": "Jaipur",
    "jai": "Jaipur",

    "delhi": "Delhi NCR",
    "new delhi": "Delhi NCR",
    "delhi ncr": "Delhi NCR",
    "gurgaon": "Delhi NCR"
})

riders["partner_status"] = np.where(
    riders["partner_id"].isna(),
    "Independent / Not Recorded",
    "Partner Linked"
)
riders["home_city"] = riders["home_city"].str.strip().str.title()

riders["home_city"] = riders["home_city"].replace({
    "Delhi Ncr": "Delhi NCR"
})

print("Unique cities after correction:")
print(riders["home_city"].unique())

print("\nCleaned data:", riders.shape)

print("\nMissing values after cleaning:")
print(riders.isnull().sum())

print("\nUnique cities:")
print(riders["home_city"].unique())

print("\nPartner status:")
print(riders["partner_status"].value_counts())

riders.to_csv(
    CLEAN_DIR / "riders_cleaned.csv",
    index=False
)

print("\nRiders cleaning successful")

# Stations Cleaning

stations = data["stations"].copy()

print("oraginal_data:", stations.shape)
print("exact duplicate:", stations.duplicated().sum())

# Date conversion

date_columns = [
    "commissioned_date",
    "decommissioned_date",
    "firmware_updated_date",
    "competitor_within_1_5km_since"
]

for col in date_columns:
    stations[col] = pd.to_datetime(stations[col], errors="coerce")

# Numeric conversion

numeric_columns = [
    "latitude",
    "longitude",
    "slots_2w",
    "slots_3w",
    "inventory_target_2w",
    "inventory_target_3w",
    "monthly_rent_inr",
    "monthly_maintenance_inr",
    "grid_tariff_inr_kwh"
]

for col in numeric_columns:
    stations[col] = pd.to_numeric(stations[col], errors="coerce")

# Standardize city names

stations["city"] = stations["city"].str.strip().str.lower()

stations["city"] = stations["city"].replace({
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "blr": "Bengaluru",
    "bombay": "Mumbai",
    "mum": "Mumbai",
    "hyd": "Hyderabad",
    "pun": "Pune",
    "jai": "Jaipur"
})

stations["city"] = stations["city"].str.title()
stations["city"] = stations["city"].replace({
    "Delhi Ncr": "Delhi NCR"
})

# Identify test stations

stations["is_test_station"] = stations["station_id"].str.contains(
    "TST", case=False, na=False
)

print("\nCleaned data:", stations.shape)

print("\nMissing values:")
print(stations.isnull().sum())

print("\nUnique cities:")
print(stations["city"].unique())

print("\nTest stations:")
print(stations["is_test_station"].value_counts())

stations.to_csv(
    CLEAN_DIR / "stations_cleaned.csv",
    index=False
)

print("\nStations cleaning successful")
# Station Hourly Status Cleaning

station_hourly = data["station_hourly_status"].copy()

print("oraginal_data:", station_hourly.shape)
print("exact duplicate:", station_hourly.duplicated().sum())

print("\nMissing values:")
print(station_hourly.isnull().sum())

print("\nData types:")
print(station_hourly.dtypes)

print("\nTelemetry status:")
print(station_hourly["telemetry_status"].value_counts())

print("\nData:")
print(station_hourly.head())
# Station Hourly Status Cleaning

station_hourly["hour_start"] = pd.to_datetime(
    station_hourly["hour_start"], errors="coerce"
)

numeric_columns = [
    "charged_2w_avg",
    "charged_2w_min",
    "charged_3w_min",
    "packs_charging",
    "packs_quarantined",
    "chargers_online",
    "ambient_temp_c",
    "cabinet_temp_c",
    "avg_charge_minutes",
    "outage_minutes",
    "grid_kwh"
]

for col in numeric_columns:
    station_hourly[col] = pd.to_numeric(
        station_hourly[col], errors="coerce"
    )

# Create telemetry quality flag

station_hourly["telemetry_missing_flag"] = np.where(
    station_hourly["telemetry_status"] == "missing",
    1,
    0
)

station_hourly["telemetry_partial_flag"] = np.where(
    station_hourly["telemetry_status"] == "partial",
    1,
    0
)

print("\nCleaned data:", station_hourly.shape)

print("\nMissing values:")
print(station_hourly.isnull().sum())

print("\nTelemetry status:")
print(station_hourly["telemetry_status"].value_counts())

station_hourly.to_csv(
    CLEAN_DIR / "station_hourly_status_cleaned.csv",
    index=False
)

print("\nStation hourly status cleaning successful")

# Support Tickets Cleaning

tickets = data["support_tickets"].copy()

print("oraginal_data:", tickets.shape)
print("exact duplicate:", tickets.duplicated().sum())

print("\nMissing values:")
print(tickets.isnull().sum())

print("\nData types:")
print(tickets.dtypes)

print("\nTicket categories:")
print(tickets["category"].value_counts())

print("\nResolution status:")
print(tickets["resolution_status"].value_counts())

print("\nData:")
print(tickets.head())
# Support Tickets Cleaning

tickets["created_ts"] = pd.to_datetime(
    tickets["created_ts"], errors="coerce"
)

tickets["resolution_hours"] = pd.to_numeric(
    tickets["resolution_hours"], errors="coerce"
)

tickets["csat_score"] = pd.to_numeric(
    tickets["csat_score"], errors="coerce"
)

# Create missing value flags

tickets["station_missing_flag"] = tickets["station_id"].isna().astype(int)

tickets["battery_missing_flag"] = tickets["battery_id"].isna().astype(int)

tickets["resolution_missing_flag"] = tickets["resolution_hours"].isna().astype(int)

tickets["csat_missing_flag"] = tickets["csat_score"].isna().astype(int)

# Identify duplicate tickets

tickets["is_duplicate_ticket"] = np.where(
    tickets["resolution_status"] == "duplicate",
    1,
    0
)

print("\nCleaned data:", tickets.shape)

print("\nMissing values:")
print(tickets.isnull().sum())

print("\nTicket categories:")
print(tickets["category"].value_counts())

print("\nResolution status:")
print(tickets["resolution_status"].value_counts())

tickets.to_csv(
    CLEAN_DIR / "support_tickets_cleaned.csv",
    index=False
)

print("\nSupport tickets cleaning successful")

# Swap Events Cleaning

swap_events = data["swap_events"].copy()

swap_events["event_ts"] = pd.to_datetime(
    swap_events["event_ts"],
    errors="coerce"
)

numeric_columns = [
    "attempt_seq",
    "queue_wait_sec",
    "soc_in_pct",
    "soh_in_pct",
    "soc_out_pct",
    "soh_out_pct",
    "km_since_last_swap",
    "list_price_inr",
    "discount_inr",
    "amount_charged_inr",
    "energy_to_recharge_kwh"
]

for column in numeric_columns:
    swap_events[column] = pd.to_numeric(
        swap_events[column],
        errors="coerce"
    )

# Missing value flags

swap_events["battery_in_missing"] = (
    swap_events["battery_in_id"].isna().astype(int)
)

swap_events["battery_out_missing"] = (
    swap_events["battery_out_id"].isna().astype(int)
)

# Invalid distance flag

swap_events["invalid_distance_flag"] = np.where(
    (swap_events["km_since_last_swap"] < 0) |
    (swap_events["km_since_last_swap"] > 300),
    1, 0
)

# Battery reading flags

swap_events["invalid_soc_flag"] = np.where(
    (swap_events["soc_in_pct"] < 0) |
    (swap_events["soc_in_pct"] > 100) |
    (swap_events["soc_out_pct"] < 0) |
    (swap_events["soc_out_pct"] > 100),
    1, 0
)

print("Cleaned Shape:", swap_events.shape)

print("\nMissing Values:")
print(swap_events.isnull().sum())

print("\nInvalid Distance Records:")
print(swap_events["invalid_distance_flag"].sum())

print("\nInvalid SOC Records:")
print(swap_events["invalid_soc_flag"].sum())
print("Firmware v3.2.0 records:")

print(
    swap_events["station_firmware"].value_counts()
)

print("\nFirmware v3.2.0 date range:")

print(
    swap_events[
        swap_events["station_firmware"] == "v3.2.0"
    ]["event_ts"].agg(["min", "max"])
)

print("\nSync Mode:")
print(swap_events["sync_mode"].value_counts())
affected_records = swap_events[
    (swap_events["station_firmware"] == "v3.2.0") &
    (swap_events["event_ts"] >= "2025-03-10") &
    (swap_events["event_ts"] <= "2025-04-14 23:59:59")
]

print("Affected Records:", affected_records.shape[0])

print("\nAffected Date Range:")
print(affected_records["event_ts"].agg(["min", "max"]))

print("\nAffected Stations:")
print(affected_records["station_id"].nunique())

# 1. Correct affected timestamps

swap_events["event_ts_corrected"] = swap_events["event_ts"]

affected_mask = (
    (swap_events["station_firmware"] == "v3.2.0") &
    (swap_events["event_ts"] >= "2025-03-10") &
    (swap_events["event_ts"] <= "2025-04-14 23:59:59")
)

swap_events.loc[affected_mask, "event_ts_corrected"] = (
    swap_events.loc[affected_mask, "event_ts"] +
    pd.Timedelta(minutes=330)
)

print("Corrected timestamps:", affected_mask.sum())


# 2. Identify possible offline batch near-duplicates

swap_events["possible_near_duplicate_flag"] = 0

offline_events = swap_events[
    swap_events["sync_mode"] == "offline_batch"
][[
    "rider_id",
    "station_id",
    "battery_in_id",
    "battery_out_id",
    "event_ts_corrected"
]].copy()

offline_events = offline_events.sort_values(
    [
        "rider_id",
        "station_id",
        "battery_in_id",
        "battery_out_id",
        "event_ts_corrected"
    ]
)

time_difference = offline_events.groupby(
    [
        "rider_id",
        "station_id",
        "battery_in_id",
        "battery_out_id"
    ],
    dropna=False
)["event_ts_corrected"].diff()

near_duplicate_index = offline_events.index[
    time_difference.between(
        pd.Timedelta(seconds=0),
        pd.Timedelta(minutes=5)
    )
]

swap_events.loc[
    near_duplicate_index,
    "possible_near_duplicate_flag"
] = 1

print(
    "Possible near-duplicates:",
    swap_events["possible_near_duplicate_flag"].sum()
)

del offline_events, time_difference


# 3. Identify test stations

swap_events["is_test_station"] = (
    swap_events["station_id"]
    .str.contains("TST", case=False, na=False)
    .astype(int)
)

print(
    "Test station records:",
    swap_events["is_test_station"].sum()
)


# 4. Invalid distance flag

swap_events["invalid_distance_flag"] = np.where(
    (swap_events["km_since_last_swap"] < 0) |
    (swap_events["km_since_last_swap"] > 300),
    1, 0
)


# 5. Invalid SOC flag

swap_events["invalid_soc_flag"] = np.where(
    (swap_events["soc_in_pct"] < 0) |
    (swap_events["soc_in_pct"] > 100) |
    (swap_events["soc_out_pct"] < 0) |
    (swap_events["soc_out_pct"] > 100),
    1, 0
)


# 6. Invalid SOH flag

swap_events["invalid_soh_flag"] = np.where(
    (swap_events["soh_in_pct"] < 0) |
    (swap_events["soh_in_pct"] > 100) |
    (swap_events["soh_out_pct"] < 0) |
    (swap_events["soh_out_pct"] > 100),
    1, 0
)


# 7. Completed swap indicator

swap_events["is_completed_swap"] = np.where(
    swap_events["event_type"] == "swap_completed",
    1, 0
)


# 8. Failed / non-completed attempt indicator

swap_events["is_failed_attempt"] = np.where(
    swap_events["event_type"] != "swap_completed",
    1, 0
)


# 9. Business record indicator

swap_events["is_business_record"] = np.where(
    swap_events["is_test_station"] == 0,
    1, 0
)


# 10. Final dataset summary

print("\n========== FINAL CLEANING SUMMARY ==========")

print("\nFinal Shape:")
print(swap_events.shape)

print("\nEvent Types:")
print(swap_events["event_type"].value_counts())

print("\nCompleted Swaps:")
print(swap_events["is_completed_swap"].sum())

print("\nNon-completed Attempts:")
print(swap_events["is_failed_attempt"].sum())

print("\nInvalid Distance:")
print(swap_events["invalid_distance_flag"].sum())

print("\nInvalid SOC:")
print(swap_events["invalid_soc_flag"].sum())

print("\nInvalid SOH:")
print(swap_events["invalid_soh_flag"].sum())

print("\nPossible Near-Duplicates:")
print(swap_events["possible_near_duplicate_flag"].sum())

print("\nMissing Values:")
print(swap_events.isnull().sum())


# 11. Save cleaned dataset

swap_events.to_csv(
    CLEAN_DIR / "swap_events_cleaned.csv",
    index=False
)

print("SWAP EVENTS CLEANING SUCCESSFUL")
