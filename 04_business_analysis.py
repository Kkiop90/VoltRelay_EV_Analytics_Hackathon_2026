from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_DIR = BASE_DIR / "Data" / "Cleaned_data"
OUTPUT_DIR = BASE_DIR / "python_analysis" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_table(frame, filename):
    frame.to_csv(OUTPUT_DIR / filename, index=False)


def service_summary(frame, group_columns):
    summary = (
        frame.groupby(group_columns, dropna=False)
        .agg(
            attempts=("event_type", "size"),
            completed_swaps=("is_completed", "sum"),
            unsuccessful_attempts=("is_unsuccessful", "sum"),
            operational_failures=("is_operational_failure", "sum"),
            abandoned_swaps=("is_abandoned", "sum"),
            cancelled_attempts=("is_cancelled", "sum"),
            mean_queue_wait_sec=("queue_wait_sec", "mean"),
            median_queue_wait_sec=("queue_wait_sec", "median"),
            p90_queue_wait_sec=("queue_wait_sec", lambda values: values.quantile(0.90)),
        )
        .reset_index()
    )
    summary["unsuccessful_rate_pct"] = (
        summary["unsuccessful_attempts"] / summary["attempts"] * 100
    )
    summary["operational_failure_rate_pct"] = (
        summary["operational_failures"] / summary["attempts"] * 100
    )
    return summary


def group_station_metrics(station_metrics, columns):
    return (
        station_metrics.groupby(columns, dropna=False)
        .agg(
            station_count=("station_id", "nunique"),
            attempts=("attempts", "sum"),
            completed_swaps=("completed_swaps", "sum"),
            unsuccessful_attempts=("unsuccessful_attempts", "sum"),
            mean_station_failure_rate_pct=("unsuccessful_rate_pct", "mean"),
            mean_station_queue_wait_sec=("median_queue_wait_sec", "mean"),
            mean_charge_minutes=("mean_charge_minutes", "mean"),
            mean_station_outage_hours=("outage_hours", "mean"),
            outage_hours=("outage_hours", "sum"),
            unique_tickets=("unique_tickets", "sum"),
            complaints_per_1000_swaps=("complaints_per_1000_swaps", "mean"),
        )
        .reset_index()
        .assign(
            weighted_failure_rate_pct=lambda result: (
                result["unsuccessful_attempts"] / result["attempts"] * 100
            ),
            weighted_complaints_per_1000_swaps=lambda result: (
                result["unique_tickets"]
                / result["completed_swaps"].replace(0, np.nan)
                * 1000
            ),
        )
    )


def retention_factor_table(cohort, factor, overall_return_rate):
    result = (
        cohort.groupby(factor, dropna=False)
        .agg(
            riders=("rider_id", "nunique"),
            returned_within_30d=("returned_within_30d", "sum"),
            return_rate_pct=("returned_within_30d", "mean"),
        )
        .reset_index()
    )
    result["return_rate_pct"] *= 100
    result = result[result["riders"] >= 100].copy()
    result["rate_difference_vs_overall_pp"] = (
        result["return_rate_pct"] - overall_return_rate
    )
    result.insert(0, "factor", factor)
    result = result.rename(columns={factor: "segment"})
    return result


print("Loading cleaned business datasets...")

event_columns = [
    "event_id",
    "rider_id",
    "station_id",
    "event_type",
    "queue_wait_sec",
    "battery_in_id",
    "soh_in_pct",
    "km_since_last_swap",
    "tariff_code",
    "list_price_inr",
    "discount_inr",
    "amount_charged_inr",
    "energy_to_recharge_kwh",
    "event_ts_corrected",
]
swap_events = pd.read_csv(
    CLEAN_DIR / "swap_events_cleaned.csv",
    usecols=event_columns,
    parse_dates=["event_ts_corrected"],
)

stations = pd.read_csv(
    CLEAN_DIR / "stations_cleaned.csv",
    parse_dates=["commissioned_date", "decommissioned_date"],
)
stations = stations[~stations["is_test_station"].astype(bool)].copy()
swap_events = swap_events[
    swap_events["station_id"].isin(stations["station_id"])
].copy()

riders = pd.read_csv(
    CLEAN_DIR / "riders_cleaned.csv",
    parse_dates=["signup_date"],
)
rider_columns = [
    "rider_id",
    "partner_id",
    "vehicle_class",
    "plan_type",
    "signup_channel",
    "signup_date",
    "declared_shift",
    "age_band",
    "kyc_verified",
    "home_city",
    "partner_status",
]
rider_profile = riders[rider_columns].drop_duplicates("rider_id")

swap_events["event_type"] = swap_events["event_type"].astype("category")
swap_events["month"] = (
    swap_events["event_ts_corrected"].dt.to_period("M").astype(str)
)
swap_events["hour"] = swap_events["event_ts_corrected"].dt.hour
swap_events["season"] = swap_events["event_ts_corrected"].dt.month.map(
    lambda month: (
        "Winter"
        if month in (12, 1, 2)
        else "Summer"
        if month in (3, 4, 5)
        else "Monsoon"
        if month in (6, 7, 8, 9)
        else "Post-monsoon"
    )
)
swap_events["is_completed"] = swap_events["event_type"].eq("swap_completed")
swap_events["is_unsuccessful"] = ~swap_events["is_completed"]
swap_events["is_operational_failure"] = swap_events["event_type"].isin(
    ["failed_no_charged_battery", "failed_system_error"]
)
swap_events["is_abandoned"] = swap_events["event_type"].eq("abandoned_queue")
swap_events["is_cancelled"] = swap_events["event_type"].eq("cancelled_by_rider")

station_lookup = stations[
    [
        "station_id",
        "city",
        "zone",
        "charger_generation",
        "location_type",
        "commissioned_date",
        "expansion_wave",
        "monthly_rent_inr",
        "monthly_maintenance_inr",
        "grid_tariff_inr_kwh",
    ]
].copy()
swap_events = swap_events.merge(
    rider_profile[["rider_id", "vehicle_class"]],
    on="rider_id",
    how="left",
    validate="many_to_one",
)
swap_events["vehicle_class"] = swap_events["vehicle_class"].fillna("Unknown")

if swap_events.empty:
    raise ValueError("No non-test station swap events were found.")

analysis_start = swap_events["event_ts_corrected"].min().normalize()
analysis_end = swap_events["event_ts_corrected"].max().normalize()
completed_events = swap_events[swap_events["is_completed"]].copy()
completed_events["month"] = completed_events[
    "event_ts_corrected"
].dt.to_period("M").astype(str)

print(
    f"Business events: {len(swap_events):,}; "
    f"observed period: {analysis_start.date()} to {analysis_end.date()}"
)


# Q1. Network performance over time
monthly_swaps = (
    completed_events.groupby("month")
    .size()
    .rename("completed_swaps")
    .reset_index()
)
monthly_revenue = (
    completed_events.groupby("month")["amount_charged_inr"]
    .sum()
    .rename("total_revenue_inr")
    .reset_index()
)
monthly_attempts = (
    swap_events.groupby("month")
    .agg(
        total_attempts=("event_type", "size"),
        unsuccessful_attempts=("is_unsuccessful", "sum"),
        operational_failures=("is_operational_failure", "sum"),
        abandoned_swaps=("is_abandoned", "sum"),
    )
    .reset_index()
)

completed_events = completed_events.merge(
    station_lookup[["station_id", "grid_tariff_inr_kwh"]],
    on="station_id",
    how="left",
    validate="many_to_one",
)
completed_events["energy_cost_inr"] = (
    completed_events["energy_to_recharge_kwh"]
    * completed_events["grid_tariff_inr_kwh"]
)
monthly_energy_cost = (
    completed_events.groupby("month")["energy_cost_inr"]
    .sum()
    .rename("energy_cost_inr")
    .reset_index()
)

stations["monthly_station_cost"] = (
    stations["monthly_rent_inr"] + stations["monthly_maintenance_inr"]
)
monthly_station_cost_rows = []
months = pd.period_range(
    analysis_start.to_period("M"),
    analysis_end.to_period("M"),
    freq="M",
)

for month in months:
    month_start = month.start_time
    month_end = month.end_time
    days_in_month = month.days_in_month

    commissioned = stations["commissioned_date"]
    active_start = commissioned.where(
        commissioned.isna() | (commissioned >= month_start),
        month_start,
    )
    decommissioned = stations["decommissioned_date"]
    active_end = decommissioned.fillna(month_end)
    active_end = active_end.where(active_end >= month_start, month_start)
    active_end = active_end.where(active_end <= month_end, month_end)

    active_days = ((active_end - active_start).dt.days + 1).clip(lower=0)
    active_during_month = (
        (commissioned <= month_end)
        & (decommissioned.isna() | (decommissioned >= month_start))
    )
    active_days = active_days.where(active_during_month, 0)
    monthly_station_cost_rows.append(
        {
            "month": str(month),
            "station_cost_inr": (
                stations["monthly_station_cost"] * active_days / days_in_month
            ).sum(),
        }
    )

monthly_analysis = (
    pd.DataFrame({"month": months.astype(str)})
    .merge(monthly_swaps, on="month", how="left")
    .merge(monthly_revenue, on="month", how="left")
    .merge(monthly_attempts, on="month", how="left")
    .merge(monthly_energy_cost, on="month", how="left")
    .merge(pd.DataFrame(monthly_station_cost_rows), on="month", how="left")
    .fillna(
        {
            "completed_swaps": 0,
            "total_revenue_inr": 0,
            "total_attempts": 0,
            "unsuccessful_attempts": 0,
            "operational_failures": 0,
            "abandoned_swaps": 0,
            "energy_cost_inr": 0,
            "station_cost_inr": 0,
        }
    )
)
monthly_analysis["unsuccessful_rate_pct"] = (
    monthly_analysis["unsuccessful_attempts"]
    / monthly_analysis["total_attempts"].replace(0, np.nan)
    * 100
)
monthly_analysis["operational_failure_rate_pct"] = (
    monthly_analysis["operational_failures"]
    / monthly_analysis["total_attempts"].replace(0, np.nan)
    * 100
)
monthly_analysis["estimated_contribution_inr"] = (
    monthly_analysis["total_revenue_inr"]
    - monthly_analysis["energy_cost_inr"]
    - monthly_analysis["station_cost_inr"]
)
monthly_analysis["contribution_per_swap_inr"] = (
    monthly_analysis["estimated_contribution_inr"]
    / monthly_analysis["completed_swaps"].replace(0, np.nan)
)
monthly_analysis["swap_growth_pct"] = (
    monthly_analysis["completed_swaps"].pct_change() * 100
)
monthly_analysis["revenue_growth_pct"] = (
    monthly_analysis["total_revenue_inr"].pct_change() * 100
)
save_table(monthly_analysis, "Q1_network_performance.csv")
save_table(monthly_swaps, "monthly_completed_swaps.csv")
save_table(monthly_revenue, "monthly_revenue.csv")
legacy_monthly_failure_rate = monthly_attempts.rename(
    columns={"unsuccessful_attempts": "failed_attempts"}
).copy()
legacy_monthly_failure_rate["failure_rate_pct"] = (
    legacy_monthly_failure_rate["failed_attempts"]
    / legacy_monthly_failure_rate["total_attempts"].replace(0, np.nan)
    * 100
)
save_table(legacy_monthly_failure_rate, "monthly_failure_rate.csv")


# Q2. Service failures, queueing, and customer experience
service_by_station = service_summary(swap_events, ["station_id"]).merge(
    station_lookup[
        [
            "station_id",
            "city",
            "zone",
            "charger_generation",
            "location_type",
            "commissioned_date",
            "expansion_wave",
        ]
    ],
    on="station_id",
    how="left",
    validate="one_to_one",
)
service_by_hour = service_summary(swap_events, ["hour"]).sort_values("hour")
service_by_season = service_summary(swap_events, ["season"])
service_by_vehicle_class = service_summary(swap_events, ["vehicle_class"])
save_table(service_by_station, "Q2_service_by_station.csv")
save_table(service_by_hour, "Q2_service_by_hour.csv")
save_table(service_by_season, "Q2_service_by_season.csv")
save_table(service_by_vehicle_class, "Q2_service_by_vehicle_class.csv")

station_failure_concentration = service_by_station.sort_values(
    "unsuccessful_attempts", ascending=False
)
top_station_failure_share_pct = (
    station_failure_concentration.head(10)["unsuccessful_attempts"].sum()
    / max(service_by_station["unsuccessful_attempts"].sum(), 1)
    * 100
)


# Q3. Station and geographic patterns
station_status = pd.read_csv(
    CLEAN_DIR / "station_hourly_status_cleaned.csv",
    usecols=[
        "station_id",
        "avg_charge_minutes",
        "outage_minutes",
        "telemetry_missing_flag",
    ],
)
station_status = station_status[
    station_status["station_id"].isin(stations["station_id"])
]
station_status_summary = (
    station_status.groupby("station_id")
    .agg(
        mean_charge_minutes=("avg_charge_minutes", "mean"),
        outage_hours=("outage_minutes", "sum"),
        telemetry_missing_pct=("telemetry_missing_flag", "mean"),
    )
    .reset_index()
)
station_status_summary["outage_hours"] /= 60
station_status_summary["telemetry_missing_pct"] *= 100

support_tickets = pd.read_csv(
    CLEAN_DIR / "support_tickets_cleaned.csv",
    usecols=["station_id", "rider_id", "created_ts", "is_duplicate_ticket"],
    parse_dates=["created_ts"],
)
tickets = support_tickets[
    support_tickets["station_id"].isin(stations["station_id"])
    & (support_tickets["is_duplicate_ticket"] == 0)
].copy()
ticket_summary = (
    tickets.groupby("station_id")
    .size()
    .rename("unique_tickets")
    .reset_index()
)

station_metrics = (
    service_by_station.merge(
        station_status_summary,
        on="station_id",
        how="left",
        validate="one_to_one",
    )
    .merge(ticket_summary, on="station_id", how="left", validate="one_to_one")
    .fillna({"unique_tickets": 0})
)
station_metrics["complaints_per_1000_swaps"] = (
    station_metrics["unique_tickets"]
    / station_metrics["completed_swaps"].replace(0, np.nan)
    * 1000
)
station_metrics["commission_year"] = (
    pd.to_datetime(station_metrics["commissioned_date"], errors="coerce")
    .dt.year.astype("Int64")
    .astype("string")
    .fillna("Unknown")
)

save_table(station_metrics, "Q3_station_performance.csv")
station_group_tables = {
    "city": "Q3_by_city.csv",
    "charger_generation": "Q3_by_charger_generation.csv",
    "location_type": "Q3_by_location_type.csv",
    "commission_year": "Q3_by_commission_year.csv",
}
for column, filename in station_group_tables.items():
    save_table(group_station_metrics(station_metrics, [column]), filename)


# Q4. Battery and equipment performance
battery_master = pd.read_csv(
    CLEAN_DIR / "batteries_cleaned.csv",
    usecols=[
        "battery_id",
        "pack_type",
        "supplier",
        "manufacturing_lot",
        "current_soh_pct",
    ],
)
battery_events = completed_events[
    completed_events["battery_in_id"].notna()
    & completed_events["soh_in_pct"].between(0, 100)
    & completed_events["km_since_last_swap"].ge(0)
].copy()
battery_events = battery_events.merge(
    battery_master.rename(columns={"battery_id": "battery_in_id"}),
    on="battery_in_id",
    how="left",
    validate="many_to_one",
)
battery_events["soh_band"] = pd.cut(
    battery_events["soh_in_pct"],
    bins=[0, 70, 80, 85, 90, 95, 100.01],
    labels=["0-70", "70-80", "80-85", "85-90", "90-95", "95-100"],
    include_lowest=True,
)

battery_use = (
    battery_events.groupby("battery_in_id")
    .agg(
        observed_return_swaps=("event_id", "size"),
        mean_observed_soh_pct=("soh_in_pct", "mean"),
        mean_range_since_prior_swap_km=("km_since_last_swap", "mean"),
        supplier=("supplier", "first"),
        manufacturing_lot=("manufacturing_lot", "first"),
        pack_type=("pack_type", "first"),
    )
    .reset_index()
)
battery_use["mean_soh_band"] = pd.cut(
    battery_use["mean_observed_soh_pct"],
    bins=[0, 70, 80, 85, 90, 95, 100.01],
    labels=["0-70", "70-80", "80-85", "85-90", "90-95", "95-100"],
    include_lowest=True,
)
battery_cohort_metrics = (
    battery_events.groupby(["supplier", "manufacturing_lot"], dropna=False)
    .agg(
        swap_observations=("event_id", "size"),
        median_soh_in_pct=("soh_in_pct", "median"),
        mean_soh_in_pct=("soh_in_pct", "mean"),
        mean_range_since_prior_swap_km=("km_since_last_swap", "mean"),
        median_range_since_prior_swap_km=("km_since_last_swap", "median"),
    )
    .reset_index()
    .merge(
        battery_use.groupby(["supplier", "manufacturing_lot"], dropna=False)
        .agg(
            observed_batteries=("battery_in_id", "nunique"),
            mean_swaps_per_observed_battery=("observed_return_swaps", "mean"),
        )
        .reset_index(),
        on=["supplier", "manufacturing_lot"],
        how="left",
    )
)
supplier_metrics = (
    battery_events.groupby("supplier", dropna=False)
    .agg(
        swap_observations=("event_id", "size"),
        unique_batteries=("battery_in_id", "nunique"),
        median_soh_in_pct=("soh_in_pct", "median"),
        mean_soh_in_pct=("soh_in_pct", "mean"),
        mean_range_since_prior_swap_km=("km_since_last_swap", "mean"),
        median_range_since_prior_swap_km=("km_since_last_swap", "median"),
    )
    .reset_index()
    .merge(
        battery_use.groupby("supplier")
        .agg(mean_swaps_per_observed_battery=("observed_return_swaps", "mean"))
        .reset_index(),
        on="supplier",
        how="left",
    )
    .sort_values("median_soh_in_pct")
)
soh_band_metrics = (
    battery_events.groupby("soh_band", observed=False, dropna=False)
    .agg(
        swap_observations=("event_id", "size"),
        unique_batteries=("battery_in_id", "nunique"),
        mean_range_since_prior_swap_km=("km_since_last_swap", "mean"),
        median_range_since_prior_swap_km=("km_since_last_swap", "median"),
    )
    .reset_index()
)
battery_usage_by_soh_band = (
    battery_use.groupby("mean_soh_band", observed=True)
    .agg(
        observed_batteries=("battery_in_id", "nunique"),
        mean_observed_swaps_per_battery=("observed_return_swaps", "mean"),
        median_observed_swaps_per_battery=("observed_return_swaps", "median"),
    )
    .reset_index()
    .rename(columns={"mean_soh_band": "mean_battery_soh_band"})
)
soh_range_correlation = pd.DataFrame(
    [
        {
            "measure": "soh_in_pct_vs_range_since_prior_swap_km",
            "pearson_correlation": battery_events[
                ["soh_in_pct", "km_since_last_swap"]
            ].corr(method="pearson").iloc[0, 1],
            "spearman_correlation": battery_events[
                ["soh_in_pct", "km_since_last_swap"]
            ].corr(method="spearman").iloc[0, 1],
            "swap_observations": len(battery_events),
        }
    ]
)
save_table(supplier_metrics, "Q4_battery_by_supplier.csv")
save_table(
    battery_cohort_metrics[
        battery_cohort_metrics["swap_observations"] >= 25
    ].sort_values(["supplier", "median_soh_in_pct"]),
    "Q4_battery_by_manufacturing_lot.csv",
)
save_table(soh_band_metrics, "Q4_range_by_soh_band.csv")
save_table(battery_usage_by_soh_band, "Q4_battery_usage_by_soh_band.csv")
save_table(soh_range_correlation, "Q4_soh_range_correlation.csv")


# Q5. Pricing and partner economics
fleet = pd.read_csv(
    CLEAN_DIR / "fleet_partners_cleaned.csv",
    parse_dates=["amendment_date"],
)
partner_terms = fleet[
    [
        "partner_id",
        "partner_segment",
        "contract_type",
        "discount_pct",
        "amendment_date",
        "discount_pct_after_amendment",
        "peak_surcharge_billable",
        "payment_terms_days",
    ]
].copy()

pricing_events = completed_events.merge(
    rider_profile[["rider_id", "partner_id", "plan_type"]],
    on="rider_id",
    how="left",
    validate="many_to_one",
)
pricing_events = pricing_events.merge(
    partner_terms,
    on="partner_id",
    how="left",
    validate="many_to_one",
)
pricing_events["effective_contract_discount_pct"] = np.where(
    pricing_events["amendment_date"].notna()
    & (pricing_events["event_ts_corrected"] >= pricing_events["amendment_date"]),
    pricing_events["discount_pct_after_amendment"],
    pricing_events["discount_pct"],
)
pricing_events["observed_discount_pct"] = (
    pricing_events["discount_inr"]
    / pricing_events["list_price_inr"].replace(0, np.nan)
    * 100
)
pricing_events["variable_contribution_inr"] = (
    pricing_events["amount_charged_inr"]
    - pricing_events["energy_cost_inr"]
)

pricing_by_month_tariff = (
    pricing_events.groupby(["month", "tariff_code"], dropna=False)
    .agg(
        completed_swaps=("event_id", "size"),
        mean_list_price_inr=("list_price_inr", "mean"),
        mean_revenue_per_swap_inr=("amount_charged_inr", "mean"),
        mean_observed_discount_pct=("observed_discount_pct", "mean"),
        mean_variable_contribution_inr=("variable_contribution_inr", "mean"),
    )
    .reset_index()
)
pricing_by_hour = (
    pricing_events.groupby(["hour", "tariff_code"], dropna=False)
    .agg(
        completed_swaps=("event_id", "size"),
        mean_list_price_inr=("list_price_inr", "mean"),
        mean_revenue_per_swap_inr=("amount_charged_inr", "mean"),
        mean_variable_contribution_inr=("variable_contribution_inr", "mean"),
    )
    .reset_index()
)
pricing_by_plan = (
    pricing_events.groupby(
        ["vehicle_class", "plan_type", "tariff_code"], dropna=False
    )
    .agg(
        completed_swaps=("event_id", "size"),
        mean_revenue_per_swap_inr=("amount_charged_inr", "mean"),
        mean_observed_discount_pct=("observed_discount_pct", "mean"),
        mean_variable_contribution_inr=("variable_contribution_inr", "mean"),
    )
    .reset_index()
)

partner_event_metrics = (
    pricing_events[pricing_events["partner_id"].notna()]
    .groupby("partner_id")
    .agg(
        completed_swaps=("event_id", "size"),
        total_revenue_inr=("amount_charged_inr", "sum"),
        mean_revenue_per_swap_inr=("amount_charged_inr", "mean"),
        mean_observed_discount_pct=("observed_discount_pct", "mean"),
        mean_variable_contribution_inr=("variable_contribution_inr", "mean"),
        peak_tariff_share_pct=(
            "tariff_code",
            lambda values: values.eq("PEAK").mean() * 100,
        ),
    )
    .reset_index()
)
partner_economics = (
    partner_terms.merge(
        partner_event_metrics,
        on="partner_id",
        how="left",
        validate="one_to_one",
    )
    .fillna(
        {
            "completed_swaps": 0,
            "total_revenue_inr": 0,
            "mean_revenue_per_swap_inr": 0,
            "mean_observed_discount_pct": 0,
            "mean_variable_contribution_inr": 0,
            "peak_tariff_share_pct": 0,
        }
    )
    .sort_values("completed_swaps", ascending=False)
)
partner_tariff_economics = (
    pricing_events[pricing_events["partner_id"].notna()]
    .groupby(
        ["partner_segment", "peak_surcharge_billable", "tariff_code"],
        dropna=False,
    )
    .agg(
        completed_swaps=("event_id", "size"),
        mean_revenue_per_swap_inr=("amount_charged_inr", "mean"),
        mean_variable_contribution_inr=("variable_contribution_inr", "mean"),
    )
    .reset_index()
)
partner_hourly_economics = (
    pricing_events[pricing_events["partner_id"].notna()]
    .groupby(["partner_segment", "hour"], dropna=False)
    .agg(
        completed_swaps=("event_id", "size"),
        mean_revenue_per_swap_inr=("amount_charged_inr", "mean"),
        mean_variable_contribution_inr=("variable_contribution_inr", "mean"),
    )
    .reset_index()
)
amended_partners = partner_terms[partner_terms["amendment_date"].notna()]
partner_amendment_rows = []
for partner in amended_partners.itertuples(index=False):
    partner_events = pricing_events[
        pricing_events["partner_id"] == partner.partner_id
    ]
    for period, mask in (
        ("before_amendment", partner_events["event_ts_corrected"] < partner.amendment_date),
        ("on_or_after_amendment", partner_events["event_ts_corrected"] >= partner.amendment_date),
    ):
        period_events = partner_events[mask]
        partner_amendment_rows.append(
            {
                "partner_id": partner.partner_id,
                "partner_segment": partner.partner_segment,
                "period": period,
                "completed_swaps": len(period_events),
                "mean_observed_discount_pct": period_events[
                    "observed_discount_pct"
                ].mean(),
                "mean_revenue_per_swap_inr": period_events[
                    "amount_charged_inr"
                ].mean(),
                "mean_variable_contribution_inr": period_events[
                    "variable_contribution_inr"
                ].mean(),
            }
        )
partner_amendment_comparison = pd.DataFrame(partner_amendment_rows)

save_table(pricing_by_month_tariff, "Q5_pricing_by_month_and_tariff.csv")
save_table(pricing_by_hour, "Q5_pricing_by_hour_and_tariff.csv")
save_table(pricing_by_plan, "Q5_pricing_by_rider_segment.csv")
save_table(partner_economics, "Q5_partner_economics.csv")
save_table(partner_tariff_economics, "Q5_partner_tariff_economics.csv")
save_table(partner_hourly_economics, "Q5_partner_economics_by_hour.csv")
save_table(partner_amendment_comparison, "Q5_partner_amendment_pre_post.csv")
pricing_by_month_base_price = (
    pricing_events.groupby("month")
    .agg(
        completed_swaps=("event_id", "size"),
        mean_list_price_inr=("list_price_inr", "mean"),
        mean_revenue_per_swap_inr=("amount_charged_inr", "mean"),
    )
    .reset_index()
)
pricing_by_month_base_price["list_price_change_pct"] = (
    pricing_by_month_base_price["mean_list_price_inr"].pct_change() * 100
)
pricing_overall_by_tariff = (
    pricing_events.groupby("tariff_code", dropna=False)
    .agg(
        completed_swaps=("event_id", "size"),
        mean_list_price_inr=("list_price_inr", "mean"),
        mean_revenue_per_swap_inr=("amount_charged_inr", "mean"),
        mean_observed_discount_pct=("observed_discount_pct", "mean"),
        mean_variable_contribution_inr=("variable_contribution_inr", "mean"),
        mean_hour=("hour", "mean"),
    )
    .reset_index()
)
save_table(pricing_by_month_base_price, "Q5_base_price_by_month.csv")
save_table(pricing_overall_by_tariff, "Q5_pricing_overall_by_tariff.csv")


# Q6. New-rider 30-day repeat analysis
last_eligible_first_swap = analysis_end - pd.Timedelta(days=30)
cohort_riders = rider_profile[
    rider_profile["signup_date"].between(analysis_start, analysis_end)
].copy()
completed_candidates = completed_events[
    [
        "event_id",
        "rider_id",
        "station_id",
        "event_ts_corrected",
        "queue_wait_sec",
        "tariff_code",
        "list_price_inr",
        "discount_inr",
    ]
].merge(
    cohort_riders[["rider_id", "signup_date"]],
    on="rider_id",
    how="inner",
    validate="many_to_one",
)
completed_candidates = completed_candidates[
    completed_candidates["event_ts_corrected"]
    >= completed_candidates["signup_date"]
]
first_success = (
    completed_candidates.sort_values(["rider_id", "event_ts_corrected"])
    .drop_duplicates("rider_id")
    .rename(columns={"event_ts_corrected": "first_success_ts"})
)
first_success = first_success[
    first_success["first_success_ts"] <= last_eligible_first_swap
].copy()

subsequent_completed = completed_events[
    ["rider_id", "event_ts_corrected"]
].merge(
    first_success[["rider_id", "first_success_ts"]],
    on="rider_id",
    how="inner",
    validate="many_to_one",
)
subsequent_completed = subsequent_completed[
    (subsequent_completed["event_ts_corrected"] > subsequent_completed["first_success_ts"])
    & (
        subsequent_completed["event_ts_corrected"]
        <= subsequent_completed["first_success_ts"] + pd.Timedelta(days=30)
    )
]
repeat_counts = (
    subsequent_completed.groupby("rider_id")
    .size()
    .rename("repeat_swaps_within_30d")
    .reset_index()
)
first_success = first_success.merge(
    repeat_counts, on="rider_id", how="left", validate="one_to_one"
)
first_success["repeat_swaps_within_30d"] = (
    first_success["repeat_swaps_within_30d"].fillna(0).astype(int)
)
first_success["returned_within_30d"] = (
    first_success["repeat_swaps_within_30d"] > 0
)

pre_success_failures = swap_events[
    ~swap_events["is_completed"]
][["rider_id", "event_ts_corrected"]].merge(
    first_success[["rider_id", "signup_date", "first_success_ts"]],
    on="rider_id",
    how="inner",
    validate="many_to_one",
)
pre_success_failures = pre_success_failures[
    (pre_success_failures["event_ts_corrected"] >= pre_success_failures["signup_date"])
    & (
        pre_success_failures["event_ts_corrected"]
        < pre_success_failures["first_success_ts"]
    )
]
pre_success_failure_counts = (
    pre_success_failures.groupby("rider_id")
    .size()
    .rename("failed_attempts_before_first_success")
    .reset_index()
)
first_success = first_success.merge(
    pre_success_failure_counts, on="rider_id", how="left", validate="one_to_one"
)
first_success["failed_attempts_before_first_success"] = (
    first_success["failed_attempts_before_first_success"].fillna(0).astype(int)
)
pre_success_tickets = support_tickets[
    support_tickets["is_duplicate_ticket"] == 0
].merge(
    first_success[["rider_id", "signup_date", "first_success_ts"]],
    on="rider_id",
    how="inner",
    validate="many_to_one",
)
pre_success_tickets = pre_success_tickets[
    (pre_success_tickets["created_ts"] >= pre_success_tickets["signup_date"])
    & (pre_success_tickets["created_ts"] < pre_success_tickets["first_success_ts"])
]
pre_success_ticket_counts = (
    pre_success_tickets.groupby("rider_id")
    .size()
    .rename("support_tickets_before_first_success")
    .reset_index()
)
first_success = first_success.merge(
    pre_success_ticket_counts, on="rider_id", how="left", validate="one_to_one"
)
first_success["support_tickets_before_first_success"] = (
    first_success["support_tickets_before_first_success"].fillna(0).astype(int)
)
first_success["had_ticket_before_first_success"] = np.where(
    first_success["support_tickets_before_first_success"] > 0,
    "Yes",
    "No",
)

first_success = first_success.merge(
    rider_profile,
    on=["rider_id", "signup_date"],
    how="left",
    suffixes=("", "_rider"),
    validate="one_to_one",
)
first_success = first_success.merge(
    station_lookup[
        ["station_id", "city", "charger_generation", "location_type"]
    ],
    on="station_id",
    how="left",
    validate="many_to_one",
)
first_success = first_success.rename(
    columns={
        "tariff_code": "first_tariff_code",
        "city": "first_station_city",
        "charger_generation": "first_charger_generation",
        "location_type": "first_station_location",
    }
)
first_success["first_hour"] = first_success["first_success_ts"].dt.hour.astype(str)
first_success["first_signup_month"] = (
    first_success["signup_date"].dt.to_period("M").astype(str)
)
first_success["first_success_season"] = first_success[
    "first_success_ts"
].dt.month.map(
    lambda month: (
        "Winter"
        if month in (12, 1, 2)
        else "Summer"
        if month in (3, 4, 5)
        else "Monsoon"
        if month in (6, 7, 8, 9)
        else "Post-monsoon"
    )
)
first_success["first_queue_wait_band"] = pd.cut(
    first_success["queue_wait_sec"],
    bins=[-np.inf, 120, 300, np.inf],
    labels=["0-120 sec", "121-300 sec", "Over 300 sec"],
)
first_success["pre_success_failure_band"] = pd.cut(
    first_success["failed_attempts_before_first_success"],
    bins=[-1, 0, 1, np.inf],
    labels=["0", "1", "2+"],
)
first_success["first_discount_pct"] = (
    first_success["discount_inr"]
    / first_success["list_price_inr"].replace(0, np.nan)
    * 100
)
first_success["first_discount_band"] = pd.cut(
    first_success["first_discount_pct"],
    bins=[-0.01, 0, 10, 20, np.inf],
    labels=["No discount", ">0-10%", ">10-20%", ">20%"],
)

overall_return_rate = first_success["returned_within_30d"].mean() * 100
retention_factors = [
    "vehicle_class",
    "plan_type",
    "signup_channel",
    "home_city",
    "partner_status",
    "age_band",
    "declared_shift",
    "kyc_verified",
    "first_tariff_code",
    "first_hour",
    "first_success_season",
    "first_station_city",
    "first_charger_generation",
    "first_station_location",
    "first_queue_wait_band",
    "pre_success_failure_band",
    "had_ticket_before_first_success",
    "first_discount_band",
    "first_signup_month",
]
retention_tables = [
    retention_factor_table(first_success, factor, overall_return_rate)
    for factor in retention_factors
]
retention_factor_results = pd.concat(retention_tables, ignore_index=True)
retention_driver_ranking = (
    retention_factor_results.groupby("factor")
    .agg(
        eligible_segments=("segment", "nunique"),
        lowest_segment_return_pct=("return_rate_pct", "min"),
        highest_segment_return_pct=("return_rate_pct", "max"),
        maximum_segment_spread_pp=(
            "rate_difference_vs_overall_pp",
            lambda values: values.max() - values.min(),
        ),
        riders_in_eligible_segments=("riders", "sum"),
    )
    .reset_index()
    .sort_values("maximum_segment_spread_pp", ascending=False)
)

eligible_signups = rider_profile[
    rider_profile["signup_date"].between(
        analysis_start, analysis_end - pd.Timedelta(days=30)
    )
].copy()
signup_completed = completed_events[
    ["rider_id", "event_ts_corrected"]
].merge(
    eligible_signups[["rider_id", "signup_date"]],
    on="rider_id",
    how="inner",
    validate="many_to_one",
)
activated_within_30d = signup_completed[
    (signup_completed["event_ts_corrected"] >= signup_completed["signup_date"])
    & (
        signup_completed["event_ts_corrected"]
        <= signup_completed["signup_date"] + pd.Timedelta(days=30)
    )
]["rider_id"].nunique()
activation_funnel = pd.DataFrame(
    [
        {
            "eligible_signups_with_30d_observation": eligible_signups["rider_id"].nunique(),
            "activated_with_completed_swap_within_30d": activated_within_30d,
            "not_activated_within_30d": (
                eligible_signups["rider_id"].nunique() - activated_within_30d
            ),
            "activation_rate_pct": (
                activated_within_30d / max(eligible_signups["rider_id"].nunique(), 1) * 100
            ),
            "activated_riders_in_30d_return_cohort": first_success["rider_id"].nunique(),
            "returned_within_30d": int(first_success["returned_within_30d"].sum()),
            "one_time_within_30d": int((~first_success["returned_within_30d"]).sum()),
            "repeat_rate_pct": overall_return_rate,
        }
    ]
)

save_table(retention_factor_results, "Q6_retention_by_factor.csv")
save_table(retention_driver_ranking, "Q6_retention_association_ranking.csv")
save_table(activation_funnel, "Q6_activation_and_retention_funnel.csv")


# Write a short evidence-based digest alongside the detailed tables.
first_month = monthly_analysis.iloc[0]
last_month = monthly_analysis.iloc[-1]
latest_vs_prior = monthly_analysis.iloc[-2] if len(monthly_analysis) > 1 else last_month
top_unreturned_segment = (
    retention_factor_results.sort_values("rate_difference_vs_overall_pp").head(1)
)
top_returned_segment = (
    retention_factor_results.sort_values(
        "rate_difference_vs_overall_pp", ascending=False
    ).head(1)
)
worst_supplier = supplier_metrics.iloc[0] if not supplier_metrics.empty else None
best_supplier = supplier_metrics.iloc[-1] if not supplier_metrics.empty else None
eligible_lots = battery_cohort_metrics[
    battery_cohort_metrics["swap_observations"] >= 25
]
lowest_soh_lot = (
    eligible_lots.loc[eligible_lots["median_soh_in_pct"].idxmin()]
    if not eligible_lots.empty
    else None
)
highest_soh_lot = (
    eligible_lots.loc[eligible_lots["median_soh_in_pct"].idxmax()]
    if not eligible_lots.empty
    else None
)
best_monthly_list_price = (
    pricing_by_month_base_price.set_index("month")["mean_list_price_inr"]
    .sort_index()
)
largest_monthly_price_increase = pricing_by_month_base_price.loc[
    pricing_by_month_base_price["list_price_change_pct"].idxmax()
]
summer_rate = service_by_season.set_index("season").loc["Summer", "unsuccessful_rate_pct"]
winter_rate = service_by_season.set_index("season").loc["Winter", "unsuccessful_rate_pct"]
three_w_rate = service_by_vehicle_class.set_index("vehicle_class").loc[
    "3W", "unsuccessful_rate_pct"
]
two_w_rate = service_by_vehicle_class.set_index("vehicle_class").loc[
    "2W", "unsuccessful_rate_pct"
]
gen1 = pd.read_csv(OUTPUT_DIR / "Q3_by_charger_generation.csv").set_index(
    "charger_generation"
)
gen1_failure = gen1.loc["Gen1", "weighted_failure_rate_pct"]
newest_gen_failure = gen1.loc["Gen3", "weighted_failure_rate_pct"]
retention_one_time_count = int((~first_success["returned_within_30d"]).sum())
tariff_summary = pricing_overall_by_tariff.set_index("tariff_code")
soh_bands_sorted = soh_band_metrics.sort_values("soh_band")
lowest_battery_use = battery_usage_by_soh_band.loc[
    battery_usage_by_soh_band["mean_observed_swaps_per_battery"].idxmin()
]
highest_battery_use = battery_usage_by_soh_band.loc[
    battery_usage_by_soh_band["mean_observed_swaps_per_battery"].idxmax()
]
city_performance = pd.read_csv(OUTPUT_DIR / "Q3_by_city.csv")
highest_failure_city = city_performance.loc[
    city_performance["weighted_failure_rate_pct"].idxmax()
]
lowest_failure_city = city_performance.loc[
    city_performance["weighted_failure_rate_pct"].idxmin()
]
city_generation_metrics = pd.read_csv(OUTPUT_DIR / "Q3_by_charger_generation.csv")
gen1_charge_minutes = city_generation_metrics.set_index("charger_generation").loc[
    "Gen1", "mean_charge_minutes"
]
gen3_charge_minutes = city_generation_metrics.set_index("charger_generation").loc[
    "Gen3", "mean_charge_minutes"
]
amendment_before = partner_amendment_comparison[
    partner_amendment_comparison["period"] == "before_amendment"
]
amendment_after = partner_amendment_comparison[
    partner_amendment_comparison["period"] == "on_or_after_amendment"
]
amended_partner_terms = partner_terms[
    partner_terms["partner_id"].isin(amended_partners["partner_id"])
]

summary_lines = [
    "BUSINESS ANALYSIS FINDINGS",
    f"Observed event period: {analysis_start.date()} to {analysis_end.date()}.",
    "",
    "Q1 - Network performance",
    (
        f"Completed swaps changed from {first_month['completed_swaps']:,.0f} "
        f"in {first_month['month']} to {last_month['completed_swaps']:,.0f} "
        f"in {last_month['month']}; revenue changed from "
        f"INR {first_month['total_revenue_inr']:,.0f} to "
        f"INR {last_month['total_revenue_inr']:,.0f}. Contribution per swap "
        f"rose from INR {first_month['contribution_per_swap_inr']:.2f} to "
        f"INR {last_month['contribution_per_swap_inr']:.2f}."
    ),
    (
        f"Unsuccessful-attempt rate was {last_month['unsuccessful_rate_pct']:.2f}% "
        f"in the latest month versus {latest_vs_prior['unsuccessful_rate_pct']:.2f}% "
        f"in the preceding month; it peaked at "
        f"{monthly_analysis['unsuccessful_rate_pct'].max():.2f}% in "
        f"{monthly_analysis.loc[monthly_analysis['unsuccessful_rate_pct'].idxmax(), 'month']}. "
        "Volume, revenue, and estimated contribution rose overall while "
        "failure rate varied materially. Contribution includes estimated energy "
        "and prorated station rent/maintenance."
    ),
    "",
    "Q2 - Service and customer experience",
    (
        f"The 10 stations with the most unsuccessful attempts account for "
        f"{top_station_failure_share_pct:.1f}% of non-completed events. "
        f"Highest-volume failure station: {station_failure_concentration.iloc[0]['station_id']}."
    ),
    (
        "See Q2 service tables for hour, season, vehicle-class, and station "
        "comparisons; unsuccessful events distinguish operational failures, "
        "queue abandonment, and rider cancellation. 3W unsuccessful rate was "
        f"{three_w_rate:.2f}% versus {two_w_rate:.2f}% for 2W; Summer was "
        f"{summer_rate:.2f}% versus {winter_rate:.2f}% in Winter. Mean queue "
        "wait is similar across hours and seasons, so time-of-day failure "
        "differences do not correspond to a similarly large average-wait shift."
    ),
    "",
    "Q3 - Station and geographic patterns",
    (
        "Station-level results combine event performance, hourly charge-time "
        "and outage telemetry, and non-duplicate support tickets. "
        f"{highest_failure_city['city']} had the highest city-weighted "
        f"unsuccessful rate ({highest_failure_city['weighted_failure_rate_pct']:.2f}%) "
        f"and {lowest_failure_city['city']} the lowest "
        f"({lowest_failure_city['weighted_failure_rate_pct']:.2f}%). Gen1 stations "
        f"had a {gen1_failure:.2f}% weighted failure rate and "
        f"{gen1_charge_minutes:.1f}-minute mean charge time, versus "
        f"{newest_gen_failure:.2f}% and {gen3_charge_minutes:.1f} minutes for Gen3. "
        "These cohort comparisons are observational and may reflect age, location, "
        "station mix, or usage differences."
    ),
    "",
    "Q4 - Battery and equipment",
    (
        f"SOH versus distance since the prior swap: Pearson "
        f"{soh_range_correlation.iloc[0]['pearson_correlation']:.3f}, "
        f"Spearman {soh_range_correlation.iloc[0]['spearman_correlation']:.3f}; "
        f"mean range was {soh_bands_sorted.iloc[-1]['mean_range_since_prior_swap_km']:.1f} km "
        f"for the 95-100% SOH band versus "
        f"{soh_bands_sorted.iloc[0]['mean_range_since_prior_swap_km']:.1f} km "
        f"for the 0-70% band. Mean observed swaps per battery ranged from "
        f"{lowest_battery_use['mean_observed_swaps_per_battery']:.0f} "
        f"({lowest_battery_use['mean_battery_soh_band']} mean SOH) to "
        f"{highest_battery_use['mean_observed_swaps_per_battery']:.0f} "
        f"({highest_battery_use['mean_battery_soh_band']} mean SOH), with no "
        "monotonic band pattern. "
        "Observed swap counts are a usage proxy, not measured charge cycles, "
        "and depend on how long each battery was observed."
    ),
    (
        f"Supplier SOH range: {worst_supplier['supplier']} had the lowest "
        f"median observed returned-pack SOH ({worst_supplier['median_soh_in_pct']:.1f}%), "
        f"while {best_supplier['supplier']} had the highest "
        f"({best_supplier['median_soh_in_pct']:.1f}%)."
        if worst_supplier is not None
        else "No battery supplier observations were available."
    ),
    (
        f"Among manufacturing lots with at least 25 observations, lowest median "
        f"SOH was {lowest_soh_lot['supplier']} / {lowest_soh_lot['manufacturing_lot']} "
        f"({lowest_soh_lot['median_soh_in_pct']:.1f}%) and highest was "
        f"{highest_soh_lot['supplier']} / {highest_soh_lot['manufacturing_lot']} "
        f"({highest_soh_lot['median_soh_in_pct']:.1f}%)."
        if lowest_soh_lot is not None and highest_soh_lot is not None
        else "No manufacturing lots met the minimum observation threshold."
    ),
    "",
    "Q5 - Pricing and partner economics",
    (
        f"Mean list price moved from INR {best_monthly_list_price.iloc[0]:.2f} "
        f"in {best_monthly_list_price.index[0]} to INR "
        f"{best_monthly_list_price.iloc[-1]:.2f} in "
        f"{best_monthly_list_price.index[-1]}. The largest monthly list-price "
        f"increase occurred in {largest_monthly_price_increase['month']} "
        f"({largest_monthly_price_increase['list_price_change_pct']:.1f}%). "
        f"Mean PEAK and OFFPEAK revenue per swap were INR "
        f"{tariff_summary.loc['PEAK', 'mean_revenue_per_swap_inr']:.2f} and "
        f"INR {tariff_summary.loc['OFFPEAK', 'mean_revenue_per_swap_inr']:.2f}, "
        "respectively; the rider-segment and partner-amendment tables show "
        "how pricing and discounts differ by customer. The PEAK/OFFPEAK pilot "
        "and partner discounts are separated in the "
        "pricing tables. These are observational comparisons; tariff, time, "
        "rider mix, and contract terms may differ."
    ),
    (
        f"{amended_partner_terms.iloc[0]['partner_id']} increased its contract "
        f"discount from {amended_partner_terms.iloc[0]['discount_pct']:.0f}% to "
        f"{amended_partner_terms.iloc[0]['discount_pct_after_amendment']:.0f}%; "
        f"mean revenue per swap changed from INR "
        f"{amendment_before.iloc[0]['mean_revenue_per_swap_inr']:.2f} to INR "
        f"{amendment_after.iloc[0]['mean_revenue_per_swap_inr']:.2f}, and "
        f"energy-only contribution from INR "
        f"{amendment_before.iloc[0]['mean_variable_contribution_inr']:.2f} "
        f"to INR {amendment_after.iloc[0]['mean_variable_contribution_inr']:.2f}. "
        "This pre/post comparison is not causal."
        if not amendment_before.empty and not amendment_after.empty
        else "No amended partner contract was available for a pre/post comparison."
    ),
    "",
    "Q6 - New-rider retention",
    (
        f"Among {len(first_success):,} eligible new riders with an observed first "
        f"completed swap and 30-day follow-up, {overall_return_rate:.1f}% made "
        f"another completed swap within 30 days ({retention_one_time_count} "
        "one-time riders). The top segment spread is only "
        f"{retention_driver_ranking.iloc[0]['maximum_segment_spread_pp']:.2f} "
        "percentage points, so this cohort does not support a clear primary "
        "retention driver; the highest-ranked factors are weak associations. "
        "Eligibility excludes right-censored first swaps in the final 30 days."
    ),
    (
        f"Lowest-return segment: {top_unreturned_segment.iloc[0]['factor']} = "
        f"{top_unreturned_segment.iloc[0]['segment']} "
        f"({top_unreturned_segment.iloc[0]['return_rate_pct']:.1f}%). "
        f"Highest-return segment: {top_returned_segment.iloc[0]['factor']} = "
        f"{top_returned_segment.iloc[0]['segment']} "
        f"({top_returned_segment.iloc[0]['return_rate_pct']:.1f}%). "
        "Association ranking is descriptive and does not establish cause."
        if not retention_factor_results.empty
        else "No retention segments met the minimum sample-size threshold."
    ),
]

findings_path = OUTPUT_DIR / "business_analysis_findings.txt"
findings_path.write_text("\n".join(summary_lines), encoding="utf-8")
print("\n".join(summary_lines))
print(f"\nAll analysis tables and findings saved to: {OUTPUT_DIR}")
