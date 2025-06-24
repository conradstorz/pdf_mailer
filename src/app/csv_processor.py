from pathlib import Path
import json
import re
import pandas as panda
from loguru import logger   

@logger.catch
def process_simple_summary_csv(in_f: Path):
    """Scan file and compute sums for 2 columns"""
    empty_df = panda.DataFrame()
    FORMATTING_FILE = Path("src/app/formatting.json")
    # load input CSV into DataFrame
    try:
        df = panda.read_csv(in_f)
        logger.debug(f"Read CSV file {in_f} with {len(df)} rows and {len(df.columns)} columns.")
    except Exception as e:
        logger.error(f"Problem using pandas to read {in_f}: {e}")
        return empty_df

    # ── begin resilient formatting-file load ───────────────────────────────────
    logger.debug(f"Attempting to read formatting file at {FORMATTING_FILE}")
    try:
        with open(FORMATTING_FILE) as json_data:
            column_details = json.load(json_data)
        logger.info(f"Loaded column formatting from {FORMATTING_FILE}")
    except FileNotFoundError:
        logger.warning(f"Formatting file not found: {FORMATTING_FILE}. Proceeding without it.")
        column_details = {}
    except Exception as e:
        logger.error(f"Error reading formatting file: {e}. Proceeding without formatting.")
        column_details = {}
    # ── end resilient formatting-file load ─────────────────────────────────────

    DAYS = 30

    # clean and convert numeric strings in "Surch" column
    try:
        cleaned = df["Surch"].replace(r"[\$,)]", "", regex=True)
        df["Surch"] = cleaned.astype(float)
    except KeyError as e:
        logger.error(f"KeyError in dataframe during Surch cleanup: {e}")
        return empty_df

    # clean and convert numeric strings in "Settlement" column
    try:
        settled = df["Settlement"].replace(r"[\$,)]", "", regex=True)
        df["Settlement"] = settled.astype(float)
    except KeyError as e:
        logger.error(f"KeyError in dataframe during Settlement cleanup: {e}")
        return empty_df

    # convert "WD Trxs" to float
    try:
        df["WD Trxs"] = df["WD Trxs"].astype(float)
    except KeyError as e:
        logger.error(f"KeyError in dataframe converting WD Trxs: {e}")
        return empty_df

    # surcharge per withdrawal calculation
    def calc(row):
        """Calculate the surcharge earned per withdrawal."""
        wd = row["WD Trxs"]
        return round(row["Surch"] / wd, 2) if wd > 0 else 0
    try:
        df["Surcharge amt"] = df.apply(calc, axis=1)
    except KeyError as e:
        logger.error(f"KeyError in dataframe during Surcharge amt calculation: {e}")
        return empty_df

    # average withdrawal amount calculation
    def avgWD(row):
        """Calculate the average amount of withdrawals."""
        wd = row["WD Trxs"]
        return round(row["Settlement"] / wd, 2) if wd > 0 else 0
    try:
        df["Average WD amount"] = df.apply(avgWD, axis=1)
    except KeyError as e:
        logger.error(f"KeyError in dataframe during Average WD amount calculation: {e}")
        return empty_df

    # daily average withdrawal over DAYS period
    def DailyWD(row):
        """Assuming {DAYS} days in report data calculate daily withdrawal total."""
        return round(row["Settlement"] / DAYS, 2)
    try:
        df["Daily Vault AVG"] = df.apply(DailyWD, axis=1)
    except KeyError as e:
        logger.error(f"KeyError in dataframe during Daily Vault AVG calculation: {e}")
        return empty_df

    # extract commission rate from Group column when it contains "Commission"
    try:
        def extract_commission_rate(val):
            if isinstance(val, str) and "Commission" in val:
                m = re.search(r"([-]?\d+(?:\.\d+)?)", val)
                return float(m.group(1)) if m else 0.0
            return 0.0
        df["Commission"] = df["Group"].apply(extract_commission_rate)
        logger.debug("Extracted commission rate into 'Commission' column.")
    except KeyError:
        logger.warning("'Group' column not found; 'Commission' column initialized to 0.")
        df["Commission"] = 0.0

    # multiply commission rate by number of surcharge withdrawals to get total commission
    try:
        df["Commission"] = df["Commission"] * df["Surcharge WDs"]
        logger.debug("Computed total Commission as commission rate * 'Surcharge WDs'.")
    except KeyError as e:
        logger.error(f"Error computing total Commission: {e}")
        # leave Commission as-is if missing

    # work is finished. Drop unneeded columns from output
    # remove 'Terminal' and 'Group' along with 'Settlement Date'
    df = df.drop(["Settlement Date", "Terminal", "Group"], axis=1)
    logger.debug("Dropped 'Settlement Date', 'Terminal', and 'Group' columns.")

    # sort the data
    df = df.sort_values("Surch", ascending=False)
    logger.debug("Sorted dataframe by 'Surch' in descending order.")

    return df
