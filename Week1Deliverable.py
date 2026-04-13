import pandas as pd
import glob
import os
import re
from pathlib import Path
from datetime import date

# Week 1 Deliverable
# - Concatenate all monthly files from January 2024 through
#   the most recently completed calendar month(March)
# - Build two combined datasets: Listings and Sold
# - Filter both to PropertyType == "Residential"
# - Save as new CSVs
# - Print row counts before and after concatenation/filtering

# Use relative path:
# this script should be saved in the main "IDX Exchange" folder
BASE_DIR = Path(__file__).resolve().parent
LISTING_DIR = BASE_DIR / "Listing"
SOLD_DIR = BASE_DIR / "Sold"


def get_most_recent_completed_month():
    """
    Returns the most recently completed calendar month as (year, month).
    Example:
      if today is 2026-04-13, this returns (2026, 3)
    """
    today = date.today()
    if today.month == 1:
        return today.year - 1, 12
    return today.year, today.month - 1


def month_index(year, month):
    """Convert year/month into a comparable integer index."""
    return year * 12 + month


def extract_year_month(filename):
    """
    Extract year and month from a filename.

    Supports patterns like:
    - 202401
    - 2024-01
    - 2024_01

    Examples:
    - CRMLSListing_202401.csv
    - CRMLSSold_2024-01.csv
    """
    name = Path(filename).stem

    # Match YYYYMM
    match = re.search(r"(20\d{2})(0[1-9]|1[0-2])", name)
    if match:
        return int(match.group(1)), int(match.group(2))

    # Match YYYY-MM or YYYY_MM
    match = re.search(r"(20\d{2})[-_](0[1-9]|1[0-2])", name)
    if match:
        return int(match.group(1)), int(match.group(2))

    return None


def read_csv_with_fallback(file_path):
    """Try a few common encodings."""
    try:
        return pd.read_csv(file_path, encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return pd.read_csv(file_path, encoding="cp1252")
        except UnicodeDecodeError:
            return pd.read_csv(file_path, encoding="latin1")


def combine_monthly_files(subfolder_path, file_pattern, output_name):
    """
    Combines monthly CSVs from Jan 2024 through the most recently completed month,
    filters PropertyType to Residential, and saves the result.
    """
    start_year, start_month = 2024, 1
    end_year, end_month = get_most_recent_completed_month()

    start_idx = month_index(start_year, start_month)
    end_idx = month_index(end_year, end_month)

    all_files = sorted(glob.glob(str(subfolder_path / file_pattern)))

    selected_files = []
    skipped_files = []
    bad_files = []
    df_list = []

    print("=" * 70)
    print(f"Processing folder: {subfolder_path.name}")
    print(f"Date range: {start_year}-{start_month:02d} through {end_year}-{end_month:02d}")
    print(f"Matched files found: {len(all_files)}")

    for file in all_files:
        ym = extract_year_month(file)

        if ym is None:
            skipped_files.append((file, "Could not detect YYYYMM or YYYY-MM in filename"))
            continue

        year, month = ym
        idx = month_index(year, month)

        if start_idx <= idx <= end_idx:
            selected_files.append(file)
        else:
            skipped_files.append((file, f"Outside target range: {year}-{month:02d}"))

    print(f"Files selected for concatenation: {len(selected_files)}")

    total_rows_before_concat = 0

    for file in selected_files:
        try:
            df = read_csv_with_fallback(file)
            rows_in_file = len(df)

            # Comment/print confirming row counts before concatenation
            print(f"Loaded: {Path(file).name} | rows before concat: {rows_in_file}")

            total_rows_before_concat += rows_in_file
            df["source_file"] = Path(file).name
            df_list.append(df)

        except Exception as e:
            bad_files.append((file, str(e)))
            print(f"Failed: {Path(file).name} -> {e}")

    if not df_list:
        print("No valid files were loaded. No output created.")
        return

    combined_df = pd.concat(df_list, ignore_index=True)

    # Comment/print confirming row counts after concatenation
    print(f"Total rows before concatenation (sum of monthly files): {total_rows_before_concat}")
    print(f"Rows after concatenation: {len(combined_df)}")

    if "PropertyType" not in combined_df.columns:
        raise KeyError(
            f"'PropertyType' column not found in combined dataset for {subfolder_path.name}"
        )

    rows_before_filter = len(combined_df)

    combined_df = combined_df[
        combined_df["PropertyType"].astype(str).str.strip().str.lower() == "residential"
    ]

    rows_after_filter = len(combined_df)

    print(f"Rows before Residential filter: {rows_before_filter}")
    print(f"Rows after Residential filter: {rows_after_filter}")

    output_file = subfolder_path / output_name
    combined_df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(f"Saved combined file to: {output_file}")

    if skipped_files:
        print("\nSkipped files:")
        for file, reason in skipped_files:
            print(f"  {Path(file).name}: {reason}")

    if bad_files:
        print("\nBad files:")
        for file, err in bad_files:
            print(f"  {Path(file).name}: {err}")


# Build combined listings dataset
combine_monthly_files(
    subfolder_path=LISTING_DIR,
    file_pattern="CRMLSListing*.csv",
    output_name="CRMLSListing_combined_residential.csv"
)


# Build combined sold dataset

combine_monthly_files(
    subfolder_path=SOLD_DIR,
    file_pattern="CRMLSSold*.csv",
    output_name="CRMLSSold_combined_residential.csv"
)
