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

# Rule-based metadata detection
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