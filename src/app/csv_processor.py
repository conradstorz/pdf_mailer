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

    # clean and convert numeric strings in "Surch" and "Settlement" columns
    for col in ["Surch", "Settlement"]:
        if col in df.columns:
            df[col] = df[col].replace(r"[\$,)]", "", regex=True).astype(float)
        else:
            logger.error(f"Column '{col}' not found in dataframe during cleanup.")
            return empty_df

    # convert "WD Trxs" to float, handle missing column gracefully
    if "WD Trxs" in df.columns:
        df["WD Trxs"] = df["WD Trxs"].astype(float)
    else:
        logger.error("Column 'WD Trxs' not found in dataframe.")
        return empty_df

    # surcharge per withdrawal calculation
    if "Surch" in df.columns and "WD Trxs" in df.columns:
        df["Surcharge amt"] = df.apply(
            lambda row: round(row["Surch"] / row["WD Trxs"], 2) if row["WD Trxs"] > 0 else 0,
            axis=1
        )
    else:
        logger.error("Required columns 'Surch' or 'WD Trxs' not found in dataframe during Surcharge amt calculation.")
        return empty_df

    # average withdrawal amount calculation
    if "Settlement" in df.columns and "WD Trxs" in df.columns:
        df["Average WD amount"] = df.apply(
            lambda row: round(row["Settlement"] / row["WD Trxs"], 2) if row["WD Trxs"] > 0 else 0,
            axis=1
        )
    else:
        logger.error("Required columns 'Settlement' or 'WD Trxs' not found in dataframe during Average WD amount calculation.")
        return empty_df

    # daily average withdrawal over DAYS period
    if "Settlement" in df.columns:
        df["Daily Vault AVG"] = df.apply(
            lambda row: round(row["Settlement"] / DAYS, 2),
            axis=1
        )
    else:
        logger.error("Column 'Settlement' not found in dataframe during Daily Vault AVG calculation.")
        return empty_df

    # extract commission rate from Group column when it contains "Commission"
    if "Group" in df.columns:
        def extract_commission_rate(val):
            if isinstance(val, str) and "Commission" in val:
                m = re.search(r"([-]?\d+(?:\.\d+)?)", val)
                return float(m.group(1)) if m else 0.0
            return 0.0
        df["Commission"] = df["Group"].apply(extract_commission_rate)
        logger.debug("Extracted commission rate into 'Commission' column.")
    else:
        logger.warning("'Group' column not found; 'Commission' column initialized to 0.")
        df["Commission"] = 0.0

    # multiply commission rate by number of surcharge withdrawals to get total commission
    if "Surcharge WDs" in df.columns:
        df["Commission"] = df["Commission"] * df["Surcharge WDs"]
        logger.debug("Computed total Commission as commission rate * 'Surcharge WDs'.")
    else:
        logger.error("Column 'Surcharge WDs' not found in dataframe during Commission calculation. Leaving 'Commission' as-is.")

    # work is finished. Drop unneeded columns from output
    # remove 'Terminal' and 'Group' along with 'Settlement Date'
    df = df.drop(["Settlement Date", "Terminal", "Group"], axis=1)
    logger.debug("Dropped 'Settlement Date', 'Terminal', and 'Group' columns.")

    # sort the data
    df = df.sort_values("Surch", ascending=False)
    logger.debug("Sorted dataframe by 'Surch' in descending order.")

    return df
