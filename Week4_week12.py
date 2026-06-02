import pandas as pd
import glob
import os
import re
from pathlib import Path
from datetime import date


# =========================================================
# Week 1 Deliverable
# - Concatenate all monthly files from January 2024 through
#   the most recently completed calendar month(March)
# - Build two combined datasets: Listings and Sold
# - Filter both to PropertyType == "Residential"
# - Save as new CSVs
# - Print row counts before and after concatenation/filtering
# =========================================================

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


# =========================================================
# Build combined listings dataset
# =========================================================
combine_monthly_files(
    subfolder_path=LISTING_DIR,
    file_pattern="CRMLSListing*.csv",
    output_name="CRMLSListing_combined_residential.csv"
)

# =========================================================
# Build combined sold dataset
# =========================================================
combine_monthly_files(
    subfolder_path=SOLD_DIR,
    file_pattern="CRMLSSold*.csv",
    output_name="CRMLSSold_combined_residential.csv"
)


import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# =========================================================
# Week 2 and week3 Analysis Script
# Submit a .py script documenting unique property types found, the filtering logic applied, and a null-count summary table.
# Include a missing value report flagging any columns above 90% null. Produce a numeric distribution summary (min, max, mean, median, percentiles) for ClosePrice, LivingArea, and DaysOnMarket. 
# Save the filtered dataset as a new CSV. 
# =========================================================


BASE_DIR = Path(__file__).resolve().parent

LISTING_FILE = BASE_DIR / "Listing" / "CRMLSListing_combined_residential.csv"
SOLD_FILE = BASE_DIR / "Sold" / "CRMLSSold_combined_residential.csv"

KEY_NUMERIC_FIELDS = [
    "ClosePrice",
    "ListPrice",
    "OriginalListPrice",
    "LivingArea",
    "LotSizeAcres",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "DaysOnMarket",
    "YearBuilt",
]

# Core fields to retain even if partially missing
CORE_FIELDS = {
    "PropertyType",
    "ClosePrice",
    "ListPrice",
    "OriginalListPrice",
    "LivingArea",
    "LotSizeAcres",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "DaysOnMarket",
    "YearBuilt",
    "ListingId",
    "StandardStatus",
    "City",
    "PostalCode",
    "Latitude",
    "Longitude",
    "CloseDate",
    "ListingContractDate",
}

METADATA_KEYWORDS = [
    "source_file",
    "listingkey",
    "media",
    "photo",
    "photos",
    "virtualtour",
    "internet",
    "url",
    "web",
    "timestamp",
    "guid",
    "modification",
    "originating",
    "officephone",
    "agentphone",
    "buyeragent",
    "selleragent",
    "coagent",
    "cooffice",
    "mls",
]


def classify_field(col_name):
    col = str(col_name).lower()
    for kw in METADATA_KEYWORDS:
        if kw in col:
            return "Metadata"
    return "Market/Analysis"


def build_dataset_summary(df, dataset_name):
    return pd.DataFrame([{
        "dataset": dataset_name,
        "row_count": df.shape[0],
        "column_count": df.shape[1]
    }])


def build_dtype_summary(df):
    return pd.DataFrame({
        "column": df.columns,
        "dtype": df.dtypes.astype(str).values,
        "field_group": [classify_field(c) for c in df.columns]
    }).sort_values(["field_group", "column"]).reset_index(drop=True)


def build_missing_summary(df):
    summary = pd.DataFrame({
        "column": df.columns,
        "missing_count": df.isnull().sum().values,
        "missing_percent": (df.isnull().mean() * 100).round(2).values,
        "dtype": df.dtypes.astype(str).values,
        "field_group": [classify_field(c) for c in df.columns]
    }).sort_values("missing_percent", ascending=False).reset_index(drop=True)

    summary["flag_above_90pct_missing"] = summary["missing_percent"] > 90

    def decide_action(row):
        if row["column"] in CORE_FIELDS:
            return "Retain (core field)"
        elif row["missing_percent"] > 90:
            return "Drop candidate"
        else:
            return "Retain"

    summary["recommended_action"] = summary.apply(decide_action, axis=1)
    return summary

def numeric_distribution_summary(df, columns):
    rows = []

    for col in columns:
        if col not in df.columns:
            rows.append({
                "column": col,
                "non_null_count": 0,
                "min": None,
                "p1": None,
                "p5": None,
                "p25": None,
                "median": None,
                "mean": None,
                "p75": None,
                "p95": None,
                "p99": None,
                "max": None,
                "note": "Column not found"
            })
            continue

        series = pd.to_numeric(df[col], errors="coerce").dropna()

        if len(series) == 0:
            rows.append({
                "column": col,
                "non_null_count": 0,
                "min": None,
                "p1": None,
                "p5": None,
                "p25": None,
                "median": None,
                "mean": None,
                "p75": None,
                "p95": None,
                "p99": None,
                "max": None,
                "note": "No numeric values"
            })
            continue

        rows.append({
            "column": col,
            "non_null_count": len(series),
            "min": series.min(),
            "p1": series.quantile(0.01),
            "p5": series.quantile(0.05),
            "p25": series.quantile(0.25),
            "median": series.median(),
            "mean": round(series.mean(), 4),
            "p75": series.quantile(0.75),
            "p95": series.quantile(0.95),
            "p99": series.quantile(0.99),
            "max": series.max(),
            "note": ""
        })

    return pd.DataFrame(rows)


def identify_outliers_iqr(df, columns):
    rows = []

    for col in columns:
        if col not in df.columns:
            rows.append({
                "column": col,
                "non_null_count": 0,
                "lower_bound": None,
                "upper_bound": None,
                "outlier_count": None,
                "outlier_percent": None,
                "note": "Column not found"
            })
            continue

        series = pd.to_numeric(df[col], errors="coerce").dropna()

        if len(series) == 0:
            rows.append({
                "column": col,
                "non_null_count": 0,
                "lower_bound": None,
                "upper_bound": None,
                "outlier_count": None,
                "outlier_percent": None,
                "note": "No numeric values"
            })
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = series[(series < lower_bound) | (series > upper_bound)]

        rows.append({
            "column": col,
            "non_null_count": len(series),
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "outlier_count": len(outliers),
            "outlier_percent": round(len(outliers) / len(series) * 100, 2),
            "note": ""
        })

    return pd.DataFrame(rows)


def save_plots(df, dataset_name, output_dir, columns):
    plot_dir = output_dir / f"{dataset_name}_plots"
    plot_dir.mkdir(exist_ok=True)

    for col in columns:
        if col not in df.columns:
            continue

        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(series) == 0:
            continue

        # -----------------------------
        # Full histogram
        # -----------------------------
        plt.figure(figsize=(8, 5))
        plt.hist(series, bins=30)
        plt.title(f"{dataset_name} Histogram - {col} (Full Range)")
        plt.xlabel(col)
        plt.ylabel("Frequency")
        plt.tight_layout()
        plt.savefig(plot_dir / f"{dataset_name}_{col}_histogram_full.png", dpi=150)
        plt.close()

        # -----------------------------
        # Zoomed histogram: cap at 99th percentile
        # -----------------------------
        upper_99 = series.quantile(0.99)
        series_zoom = series[series <= upper_99]

        plt.figure(figsize=(8, 5))
        plt.hist(series_zoom, bins=30)
        plt.title(f"{dataset_name} Histogram - {col} (Up to 99th Percentile)")
        plt.xlabel(col)
        plt.ylabel("Frequency")
        plt.xlim(series_zoom.min(), upper_99)
        plt.tight_layout()
        plt.savefig(plot_dir / f"{dataset_name}_{col}_histogram_zoom_p99.png", dpi=150)
        plt.close()

        # -----------------------------
        # Log-scale histogram for highly skewed variables
        # -----------------------------
        if (series > 0).all():
            plt.figure(figsize=(8, 5))
            plt.hist(series, bins=30)
            plt.xscale("log")
            plt.title(f"{dataset_name} Histogram - {col} (Log X-axis)")
            plt.xlabel(col)
            plt.ylabel("Frequency")
            plt.tight_layout()
            plt.savefig(plot_dir / f"{dataset_name}_{col}_histogram_logx.png", dpi=150)
            plt.close()

        # -----------------------------
        # Full boxplot
        # -----------------------------
        plt.figure(figsize=(8, 5))
        plt.boxplot(series, vert=True)
        plt.title(f"{dataset_name} Boxplot - {col} (Full Range)")
        plt.ylabel(col)
        plt.tight_layout()
        plt.savefig(plot_dir / f"{dataset_name}_{col}_boxplot_full.png", dpi=150)
        plt.close()

        # -----------------------------
        # Zoomed boxplot: up to 99th percentile
        # -----------------------------
        plt.figure(figsize=(8, 5))
        plt.boxplot(series_zoom, vert=True)
        plt.title(f"{dataset_name} Boxplot - {col} (Up to 99th Percentile)")
        plt.ylabel(col)
        plt.tight_layout()
        plt.savefig(plot_dir / f"{dataset_name}_{col}_boxplot_zoom_p99.png", dpi=150)
        plt.close()

def process_file(input_file, output_file, dataset_name):
    print("=" * 100)
    print(f"Dataset: {dataset_name}")
    print(f"Input file: {input_file}")

    df = pd.read_csv(input_file, encoding="utf-8-sig")

    # ---------------------------------------------------------
    # Dataset understanding before filtering
    # ---------------------------------------------------------
    print("\nDataset Understanding")
    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")

    dtype_summary = build_dtype_summary(df)
    print("\nColumn data types (first 20 rows shown):")
    print(dtype_summary.head(20).to_string(index=False))

    # ---------------------------------------------------------
    # Unique property types found
    # ---------------------------------------------------------
    if "PropertyType" not in df.columns:
        raise KeyError(f"'PropertyType' column not found in {dataset_name} dataset.")

    property_types = (
        df["PropertyType"]
        .astype(str)
        .str.strip()
        .replace("nan", pd.NA)
        .dropna()
        .unique()
    )

    print("\nUnique property types found:")
    for pt in sorted(property_types):
        print(f" - {pt}")

    # ---------------------------------------------------------
    # Filtering logic
    # ---------------------------------------------------------
    print("\nFiltering logic applied:")
    print('Keep rows where PropertyType.strip().lower() == "residential"')

    filtered_df = df[
        df["PropertyType"].astype(str).str.strip().str.lower() == "residential"
    ].copy()

    print(f"Rows before filtering: {len(df)}")
    print(f"Rows after filtering:  {len(filtered_df)}")

    # ---------------------------------------------------------
    # Missing value analysis on filtered dataset
    # ---------------------------------------------------------
    missing_summary = build_missing_summary(filtered_df)
    high_missing = missing_summary[missing_summary["flag_above_90pct_missing"]].copy()

    # Drop columns with >90% missing, except core fields
    drop_cols = high_missing.loc[
        ~high_missing["column"].isin(CORE_FIELDS),
        "column"
    ].tolist()

    filtered_df = filtered_df.drop(columns=drop_cols)

    print("\nDropped columns with >90% missing:")
    if drop_cols:
        for col in drop_cols:
            print(f" - {col}")
    else:
        print("None")

    # Rebuild missing summary after dropping columns
    missing_summary = build_missing_summary(filtered_df)
    high_missing = missing_summary[missing_summary["flag_above_90pct_missing"]].copy()

    print("\nHigh-missing columns (>90% missing) after dropping:")
    if len(high_missing) > 0:
        print(high_missing[["column", "missing_percent", "recommended_action"]].to_string(index=False))
    else:
        print("None")

    print("\nMissing value summary (top 20 by missing percent):")
    print(missing_summary.head(20)[
        ["column", "missing_count", "missing_percent", "recommended_action"]
    ].to_string(index=False))

    # ---------------------------------------------------------
    # Numeric distribution review
    # ---------------------------------------------------------
    numeric_summary = numeric_distribution_summary(filtered_df, KEY_NUMERIC_FIELDS)
    outlier_summary = identify_outliers_iqr(filtered_df, KEY_NUMERIC_FIELDS)

    print("\nNumeric distribution summary:")
    print(numeric_summary.to_string(index=False))

    print("\nExtreme outlier summary (IQR rule):")
    print(outlier_summary.to_string(index=False))

    # ---------------------------------------------------------
    # Save filtered dataset
    # ---------------------------------------------------------
    filtered_df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"\nSaved filtered dataset to: {output_file}")

    # ---------------------------------------------------------
    # Save analysis outputs
    # ---------------------------------------------------------
    output_dir = output_file.parent

    build_dataset_summary(filtered_df, dataset_name).to_csv(
        output_dir / f"{dataset_name}_dataset_summary.csv",
        index=False,
        encoding="utf-8-sig"
    )

    dtype_summary.to_csv(
        output_dir / f"{dataset_name}_column_dtypes_and_groups.csv",
        index=False,
        encoding="utf-8-sig"
    )

    missing_summary.to_csv(
        output_dir / f"{dataset_name}_missing_value_summary.csv",
        index=False,
        encoding="utf-8-sig"
    )

    high_missing.to_csv(
        output_dir / f"{dataset_name}_high_missing_columns.csv",
        index=False,
        encoding="utf-8-sig"
    )

    numeric_summary.to_csv(
        output_dir / f"{dataset_name}_numeric_distribution_summary.csv",
        index=False,
        encoding="utf-8-sig"
    )

    outlier_summary.to_csv(
        output_dir / f"{dataset_name}_outlier_summary.csv",
        index=False,
        encoding="utf-8-sig"
    )

    save_plots(filtered_df, dataset_name, output_dir, KEY_NUMERIC_FIELDS)
    print(f"Saved analysis CSVs and plots in: {output_dir}")


def main():
    process_file(
        input_file=LISTING_FILE,
        output_file=BASE_DIR / "Listing" / "CRMLSListing_filtered_residential.csv",
        dataset_name="Listing"
    )

    process_file(
        input_file=SOLD_FILE,
        output_file=BASE_DIR / "Sold" / "CRMLSSold_filtered_residential.csv",
        dataset_name="Sold"
    )


if __name__ == "__main__":
    main()

##week3 continue task
##Submit a .py script that: (1) fetches the MORTGAGE30US series directly from FRED, (2) resamples it to 
##monthly averages, (3) merges it onto both the combined sold and listings datasets using a year_monthkey, and (4) includes a validation check confirming no null rate values exist after the merge. Save both enriched datasets as new CSVs.

# Step 1 – Fetch the mortgage rate data from FRED 
import pandas as pd 
url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US" 
mortgage = pd.read_csv(url, parse_dates=['observation_date']) 
mortgage.columns = ['date', 'rate_30yr_fixed'] 
print(mortgage.head(10))

# Step 2 – Resample weekly rates to monthly averages 
mortgage['year_month'] = mortgage['date'].dt.to_period('M') 
mortgage_monthly = ( 
mortgage.groupby('year_month')['rate_30yr_fixed'] 
.mean() 
.reset_index() 
) 
print(mortgage.head(10))


# Step 3 – Create a matching year_month key on the MLS datasets 
# Sold dataset — key off CloseDate 

sold = pd.read_csv(r"Sold\CRMLSSold_combined_residential.csv")
print(sold.head())

sold['year_month'] = pd.to_datetime(sold['CloseDate']).dt.to_period('M') 
print(sold.head())

# Listings dataset — key off ListingContractDate 
listings=pd.read_csv(r"Listing\CRMLSListing_combined_residential.csv")
print(listings.head())
listings['year_month'] = pd.to_datetime( 
listings['ListingContractDate'] 
).dt.to_period('M')
print(listings.head(10))

# Step 4 – Merge 
sold_with_rates = sold.merge(mortgage_monthly, on='year_month', how='left') 
listings_with_rates = listings.merge(mortgage_monthly, on='year_month', how='left') 
# Step 5 – Validate the merge 
# Check for any unmatched rows (rate should not be null) 
print(sold_with_rates['rate_30yr_fixed'].isnull().sum()) 
print(listings_with_rates['rate_30yr_fixed'].isnull().sum()) 
# Preview 
print( 
sold_with_rates[ 
['CloseDate', 'year_month', 'ClosePrice', 'rate_30yr_fixed'] 
].head() 
)
# Step 6 – Save both enriched datasets as new CSVs
sold_with_rates.to_csv(
    r"Sold\CRMLSSold_combined_residential_with_rates.csv",
    index=False
)

listings_with_rates.to_csv(
    r"Listing\CRMLSListing_combined_residential_with_rates.csv",
    index=False
)

print("Saved sold dataset with rates.")
print("Saved listings dataset with rates.")



# =========================================================
# Week 4 and week5 Analysis Script
# Submit a cleaned, analysis-ready dataset as a CSV, plus a .py script documenting every transformation made and why. 
# Include before/after row counts, data type confirmations, date consistency flag counts, and a geographic data quality summary noting any invalid coordinate records. 
# =========================================================
sold_df = pd.read_csv(r"Sold\CRMLSSold_combined_residential_with_rates.csv")
listings_df = pd.read_csv(r"Listing\CRMLSListing_combined_residential_with_rates.csv")

print(sold_df.head())
print(listings_df.head())

print(sold_df.info())
print(listings_df.info())

#Convert date fields to datetime format (CloseDate, PurchaseContractDate, ListingContractDate, ContractStatusChangeDate) 

date_columns = [
    'CloseDate',
    'PurchaseContractDate',
    'ListingContractDate',
    'ContractStatusChangeDate'
]

for col in date_columns:
    if col in sold_with_rates.columns:
        sold_with_rates[col] = pd.to_datetime(sold_with_rates[col], errors='coerce')
                                                                                                                                                                                                                                                                                                      
    if col in listings_with_rates.columns:
        listings_with_rates[col] = pd.to_datetime(listings_with_rates[col], errors='coerce')

## Verify date conversion worked or not 
print(sold_with_rates[['CloseDate', 'PurchaseContractDate','ListingContractDate','ContractStatusChangeDate']].dtypes)
print(listings_with_rates[['CloseDate', 'PurchaseContractDate','ListingContractDate','ContractStatusChangeDate']].dtypes)

# Remove unnecessary or redundant columns. Remove the .1 duplicate columns
def drop_dot1_columns(df):
    cols_to_drop = [col for col in df.columns if col.endswith('.1')]
    return df.drop(columns=cols_to_drop)

sold_with_rates = drop_dot1_columns(sold_with_rates)
listings_with_rates = drop_dot1_columns(listings_with_rates)




# check columns names after drop 
print(list(sold_with_rates.columns))
print(list(listings_with_rates.columns))

# check number of columns remains
print("Sold columns:", len(sold_with_rates.columns))
print("Listings columns:", len(listings_with_rates.columns))

# Confirm no .1 columns remain
print([col for col in sold_with_rates.columns if col.endswith('.1')])
print([col for col in listings_with_rates.columns if col.endswith('.1')])


# Before cleaning
sold_rows_before, sold_cols_before = sold_df.shape
list_rows_before, list_cols_before = listings_df.shape


# clean dataset with missing values, and numeric was properly typd and remove invalid numeric values

def clean_dataset(df):

    # -----------------------------
    # 1. Ensure numeric fields are properly typed
    # -----------------------------
    numeric_cols = [
        'ClosePrice',
        'LivingArea',
        'DaysOnMarket',
        'BedroomsTotal',
        'BathroomsTotalInteger',
        'LotSizeSquareFeet',
        'YearBuilt',
        'rate_30yr_fixed'
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # -----------------------------
    # 2. Flag invalid values
    # -----------------------------
    if 'ClosePrice' in df.columns:
        df['flag_invalid_closeprice'] = df['ClosePrice'] <= 0

    if 'LivingArea' in df.columns:
        df['flag_invalid_livingarea'] = df['LivingArea'] <= 0

    if 'DaysOnMarket' in df.columns:
        df['flag_invalid_dom'] = df['DaysOnMarket'] < 0

    if 'BedroomsTotal' in df.columns:
        df['flag_invalid_bedrooms'] = df['BedroomsTotal'] < 0

    if 'BathroomsTotalInteger' in df.columns:
        df['flag_invalid_bathrooms'] = df['BathroomsTotalInteger'] < 0

    # -----------------------------
    # 3. Remove invalid rows
    # (keep rows where values are valid OR missing)
    # -----------------------------
    if 'ClosePrice' in df.columns:
        df = df[df['ClosePrice'].isna() | (df['ClosePrice'] > 0)]

    if 'LivingArea' in df.columns:
        df = df[df['LivingArea'].isna() | (df['LivingArea'] > 0)]

    if 'DaysOnMarket' in df.columns:
        df = df[df['DaysOnMarket'].isna() | (df['DaysOnMarket'] >= 0)]

    if 'BedroomsTotal' in df.columns:
        df = df[df['BedroomsTotal'].isna() | (df['BedroomsTotal'] >= 0)]

    if 'BathroomsTotalInteger' in df.columns:
        df = df[df['BathroomsTotalInteger'].isna() | (df['BathroomsTotalInteger'] >= 0)]

    # -----------------------------
    # 4. Handle missing values
    # -----------------------------

    # Drop rows missing critical fields (only for SOLD dataset ideally)
    if 'ClosePrice' in df.columns:
        df = df.dropna(subset=['ClosePrice'])

    if 'LivingArea' in df.columns:
        df = df.dropna(subset=['LivingArea'])

    # Fill remaining numeric NaNs with median
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())

    # Fill categorical NaNs with "Unknown"
    cat_cols = df.select_dtypes(include='object').columns
    df[cat_cols] = df[cat_cols].fillna('Unknown')

    return df

sold_with_rates = clean_dataset(sold_with_rates)
listings_with_rates = clean_dataset(listings_with_rates)

## Additionally remove columns from the dataset because agent name reduadancy and address detial 

cols_to_drop = [

    'BuyerAgentMlsId',

   # don't need that detailed information
    'StreetNumberNumeric'

]

sold_with_rates = sold_with_rates.drop(columns=cols_to_drop, errors='ignore')

print(sold_with_rates.isnull().sum().head(10))
print(listings_with_rates.isnull().sum().head(10))


# =========================================================
# Date Consistency Checks + Geographic Data Checks
# =========================================================

def add_date_geo_quality_flags(df):
    df = df.copy()

    # -----------------------------
    # 1. Date Consistency Checks
    # -----------------------------

    # ListingContractDate should be before CloseDate
    if {'ListingContractDate', 'CloseDate'}.issubset(df.columns):
        df['listing_after_close_flag'] = (
            df['ListingContractDate'].notna()
            & df['CloseDate'].notna()
            & (df['ListingContractDate'] > df['CloseDate'])
        )
    else:
        df['listing_after_close_flag'] = False

    # PurchaseContractDate should be before CloseDate
    if {'PurchaseContractDate', 'CloseDate'}.issubset(df.columns):
        df['purchase_after_close_flag'] = (
            df['PurchaseContractDate'].notna()
            & df['CloseDate'].notna()
            & (df['PurchaseContractDate'] > df['CloseDate'])
        )
    else:
        df['purchase_after_close_flag'] = False

    # ListingContractDate should be before PurchaseContractDate
    if {'ListingContractDate', 'PurchaseContractDate'}.issubset(df.columns):
        df['negative_timeline_flag'] = (
            df['ListingContractDate'].notna()
            & df['PurchaseContractDate'].notna()
            & (df['ListingContractDate'] > df['PurchaseContractDate'])
        )
    else:
        df['negative_timeline_flag'] = False

    # -----------------------------
    # 2. Geographic Data Checks
    # -----------------------------

    if {'Latitude', 'Longitude'}.issubset(df.columns):

        df['missing_coordinates_flag'] = (
            df['Latitude'].isna() | df['Longitude'].isna()
        )

        df['zero_coordinates_flag'] = (
            (df['Latitude'] == 0) | (df['Longitude'] == 0)
        )

        # California longitudes should be negative
        df['positive_longitude_flag'] = df['Longitude'] > 0

        # Approximate valid California coordinate bounds
        df['implausible_coordinates_flag'] = (
            (df['Latitude'] < 32) |
            (df['Latitude'] > 42.5) |
            (df['Longitude'] < -125) |
            (df['Longitude'] > -113)
        )

    else:
        df['missing_coordinates_flag'] = False
        df['zero_coordinates_flag'] = False
        df['positive_longitude_flag'] = False
        df['implausible_coordinates_flag'] = False

    return df


sold_with_rates = add_date_geo_quality_flags(sold_with_rates)
listings_with_rates = add_date_geo_quality_flags(listings_with_rates)

sold_rows_after, sold_cols_after = sold_with_rates.shape
list_rows_after, list_cols_after = listings_with_rates.shape

print(f"Sold rows: {sold_rows_before} → {sold_rows_after}")
print(f"Sold columns: {sold_cols_before} → {sold_cols_after}")

print(f"Listings rows: {list_rows_before} → {list_rows_after}")
print(f"Listings columns: {list_cols_before} → {list_cols_after}")










# --------------------------------------------
## Week 6
# Submit a .py script demonstrating all engineered metrics (price ratio, close-to-original-list ratio, PPSF, days on market, YrMo, listing-to-contract days, contract-to-close days), with a sample output table showing the new columns populated correctly. 
# Include at least one segmented summary table grouped by PropertyType or CountyOrParish. 
# ---------------------------------------------

# Key Metrics Creation


def add_key_metrics(df):
    df = df.copy()

    # Price Ratio / Close to Original List Ratio
    if {'ClosePrice', 'OriginalListPrice'}.issubset(df.columns):
        df['price_ratio'] = df['ClosePrice'] / df['OriginalListPrice']
        df['close_to_original_list_ratio'] = df['ClosePrice'] / df['OriginalListPrice']

    # Price Per Sq Ft
    if {'ClosePrice', 'LivingArea'}.issubset(df.columns):
        df['price_per_sqft'] = df['ClosePrice'] / df['LivingArea']

    # Year / Month / YrMo from CloseDate
    if 'CloseDate' in df.columns:
        df['close_year'] = df['CloseDate'].dt.year
        df['close_month'] = df['CloseDate'].dt.month
        df['close_yrmo'] = df['CloseDate'].dt.to_period('M').astype(str)

    # Listing to Contract Days
    if {'PurchaseContractDate', 'ListingContractDate'}.issubset(df.columns):
        df['listing_to_contract_days'] = (
            df['PurchaseContractDate'] - df['ListingContractDate']
        ).dt.days

    # Contract to Close Days
    if {'CloseDate', 'PurchaseContractDate'}.issubset(df.columns):
        df['contract_to_close_days'] = (
            df['CloseDate'] - df['PurchaseContractDate']
        ).dt.days

    return df


sold_with_rates = add_key_metrics(sold_with_rates)
listings_with_rates = add_key_metrics(listings_with_rates)



# Sample Output Table

metric_sample_cols = [
    'ClosePrice',
    'OriginalListPrice',
    'LivingArea',
    'DaysOnMarket',
    'CloseDate',
    'ListingContractDate',
    'PurchaseContractDate',
    'price_ratio',
    'price_per_sqft',
    'close_year',
    'close_month',
    'close_yrmo',
    'close_to_original_list_ratio',
    'listing_to_contract_days',
    'contract_to_close_days'
]

metric_sample_cols = [
    col for col in metric_sample_cols 
    if col in sold_with_rates.columns
]

print("\n=== SAMPLE KEY METRICS OUTPUT: SOLD DATASET ===")
print(sold_with_rates[metric_sample_cols].head(10))



# Use group by function to make the Summary 


def summarize_by_group(df, group_cols):

    metrics = [
        'ClosePrice',
        'price_per_sqft',
        'price_ratio',
        'DaysOnMarket',
        'listing_to_contract_days',
        'contract_to_close_days',
        'rate_30yr_fixed'
    ]

    metrics = [col for col in metrics if col in df.columns]

    summary = (
        df.groupby(group_cols)[metrics]
        .agg(['count', 'mean', 'median'])
    )

    # Flatten multi-index columns
    summary.columns = ['_'.join(col).strip() for col in summary.columns]

    return summary.reset_index()

print("\n=== Property Type Summary ===")

property_summary = summarize_by_group(
    sold_with_rates,
    ['PropertyType', 'PropertySubType']
)

print(property_summary.head(10))

print("\n=== Office Performance Summary ===")

office_summary = summarize_by_group(
    sold_with_rates,
    ['ListOfficeName', 'BuyerOfficeName']
)

print(office_summary.head(10))

top_negotiation = property_summary.sort_values(
    'price_ratio_mean',
    ascending=False
)

print("\n=== Top Property Types by Price Ratio ===")
print(top_negotiation.head(10))

# --------------------------------------------
## Week 7
# Submit a .py script applying IQR filtering to key numeric fields (ClosePrice, LivingArea, DaysOnMarket). 
# Add outlier flag columns rather than deleting records outright. Save both a full flagged dataset and a clean filtered dataset. 
# Include a written comparison of dataset size and median values before and after filtering. 
# ---------------------------------------------


# IQR Outlier Filtering function


iqr_fields = ['ClosePrice', 'LivingArea', 'DaysOnMarket']

def add_iqr_outlier_flags(df, fields):
    df = df.copy()

    for col in fields:
        if col in df.columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
             

            lower_bound = max(0, q1 - 1.5 * iqr)  # I add max function here to make sure the result is positive to match with relaity
            upper_bound =  q3 + 1.5 * iqr

            df[f'{col}_outlier_flag'] = (
                (df[col] < lower_bound) |
                (df[col] > upper_bound)
            )

            print(f"{col}: lower={lower_bound:.2f}, upper={upper_bound:.2f}")

    return df


sold_flagged = add_iqr_outlier_flags(sold_with_rates, iqr_fields)
listings_flagged = add_iqr_outlier_flags(listings_with_rates, iqr_fields)

print("\n=== Sold flagged Filtered without remove ===")
print(pd.DataFrame(sold_flagged.head(10)))

print("\n=== list flagged Filtered without remove ===")
print(listings_flagged.head(10))

#  clean filtered datasets without deleting from the flagged versions

outlier_flag_cols = [
    f'{col}_outlier_flag'
    for col in iqr_fields
    if f'{col}_outlier_flag' in sold_flagged.columns
]

sold_clean_filtered = sold_flagged[
    ~sold_flagged[outlier_flag_cols].any(axis=1)
].copy()

outlier_flag_cols_listings = [
    f'{col}_outlier_flag'
    for col in iqr_fields
    if f'{col}_outlier_flag' in listings_flagged.columns
]

listings_clean_filtered = listings_flagged[
    ~listings_flagged[outlier_flag_cols_listings].any(axis=1)
].copy()



# Dataset Size + Median Comparison

def compare_before_after(original_df, filtered_df, dataset_name):
    print(f"\n=== {dataset_name}: Before vs After IQR Filtering ===")
    print(f"Rows before: {original_df.shape[0]}")
    print(f"Rows after: {filtered_df.shape[0]}")
    print(f"Rows removed from clean dataset: {original_df.shape[0] - filtered_df.shape[0]}")
    print(f"Columns in flagged dataset: {original_df.shape[1]} → {filtered_df.shape[1]}")

    for col in iqr_fields:
        if col in original_df.columns and col in filtered_df.columns:
            before_median = original_df[col].median()
            after_median = filtered_df[col].median()
            print(f"{col} median before: {before_median:.2f}")
            print(f"{col} median after:  {after_median:.2f}")


compare_before_after(sold_flagged, sold_clean_filtered, "Sold Dataset")
compare_before_after(listings_flagged, listings_clean_filtered, "Listings Dataset")



# Save Full Flagged + Clean Filtered Datasets


sold_flagged.to_csv("sold_with_rates_flagged_outliers.csv", index=False)
sold_clean_filtered.to_csv("sold_with_rates_clean_filtered.csv", index=False)

listings_flagged.to_csv("listings_with_rates_flagged_outliers.csv", index=False)
listings_clean_filtered.to_csv("listings_with_rates_clean_filtered.csv", index=False)

# =========================================================
# Tableau Dashboard Source Dataset
# Source: sold_clean_filtered
# =========================================================

tableau_df = sold_clean_filtered.copy()

# -----------------------------
# Convert date fields
# -----------------------------
date_cols = [
    'CloseDate',
    'ListingContractDate',
    'PurchaseContractDate'
]

for col in date_cols:
    if col in tableau_df.columns:
        tableau_df[col] = pd.to_datetime(
            tableau_df[col],
            errors='coerce'
        )

# -----------------------------
# Create Tableau-friendly fields
# -----------------------------

# Monthly timeline
tableau_df['month_date'] = (
    tableau_df['CloseDate']
    .dt.to_period('M')
    .dt.to_timestamp()
)

# Year / Month
tableau_df['year'] = tableau_df['CloseDate'].dt.year
tableau_df['month'] = tableau_df['CloseDate'].dt.month
tableau_df['month_name'] = tableau_df['CloseDate'].dt.month_name()

# Luxury segmentation
luxury_threshold = tableau_df['ClosePrice'].quantile(0.90)

tableau_df['luxury_segment'] = tableau_df['ClosePrice'].apply(
    lambda x: 'Luxury'
    if x >= luxury_threshold
    else 'Non-Luxury'
)

# New listing flag
tableau_df['new_listing_flag'] = 1

# Closed sale flag
tableau_df['closed_sale_flag'] = 1



# Pending sale flag
tableau_df['pending_sale_flag'] = (
    tableau_df['PurchaseContractDate']
    .notna()
    .astype(int)
)

# -----------------------------
# Keep important dashboard fields
# -----------------------------
tableau_columns = [

    # Time
    'month_date',
    'year',
    'month',
    'month_name',

    # Geography
    'City',
    'CountyOrParish',
    'PostalCode',
    'Latitude',
    'Longitude',

    # Property
    'PropertyType',
    'PropertySubType',
    'luxury_segment',

    # Pricing
    'ClosePrice',
    'OriginalListPrice',
    'ListPrice',
    'price_ratio',
    'close_to_original_list_ratio',
    'price_per_sqft',

    # Market activity
    'DaysOnMarket',
    'listing_to_contract_days',
    'contract_to_close_days',

    # Volume flags
    'new_listing_flag',
    'closed_sale_flag',
    'pending_sale_flag',

    # Rates
    'rate_30yr_fixed'
]

tableau_columns = [
    col for col in tableau_columns
    if col in tableau_df.columns
]

tableau_df = tableau_df[tableau_columns]

# -----------------------------
# Save Tableau source file
# -----------------------------
tableau_df.to_csv(
    "market_analysis_tableau_source.csv",
    index=False
)

# -----------------------------
# Preview
# -----------------------------
print("\n=== Tableau Dashboard Dataset Preview ===")

print(
    tableau_df
    .head(20)
    .round(2)
    .to_string(index=False)
)

print("\nSaved:")
print("market_analysis_tableau_source.csv")

