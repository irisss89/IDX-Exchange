import pandas as pd
import matplotlib.pyplot as plt
import os

# 1. Combined dataset understanding
file_path = r"C:\Users\irisz\OneDrive\桌面\IDX Exchange\Listing\CRMLSListing_combined.csv"
df = pd.read_csv(file_path, encoding="utf-8-sig", low_memory=False)

print("Shape:", df.shape)
print()

print("Column names:")
print(df.columns.tolist())
print()


print("Data types:")
print(df.dtypes)
print()

print("First 5 rows:")
print(df.head())
print()

# 2. Missing values

missing = df.isnull().sum().sort_values(ascending=False)
missing_pct = (df.isnull().mean() * 100).sort_values(ascending=False)

missing_summary = pd.DataFrame({
    "missing_count": missing,
    "missing_percent": missing_pct
})



# flag columns
missing_summary["flag_missing"] = (missing_summary["missing_count"] > 0).astype(int)

# if missing percentage>90 then flag as 1 else 0 
missing_summary["flag_high_missing_90"] = (missing_summary["missing_percent"] > 90).astype(int)

# if missing percentage>100 then flag as 1 else 0 
missing_summary["flag_all_missing_100"] = (missing_summary["missing_percent"] == 100).astype(int)

print("Top missing values:")
print(missing_summary.head(25))
print()


# Missing Column decide to drop 

cols_to_drop = missing_summary[missing_summary["missing_percent"] >= 95].index.tolist()
df = df.drop(columns=cols_to_drop)

print("Dropped columns:")
print(cols_to_drop)
print("New shape:", df.shape)
print()

# 3. Duplicates

duplicate_count = df.duplicated().sum()
print("Duplicate rows:", duplicate_count)

# check duplicate listing keys since it is unique identifier
df["ListingKey"].nunique()
print()

df["ListingKey"].duplicated().sum()

duplicate_keys = df[df["ListingKey"].duplicated(keep=False)].sort_values("ListingKey")
print(duplicate_keys[["ListingKey", "source_file"]].head(20))

# 4. Convert date columns

date_cols = [
    "ListingContractDate",
    "CloseDate",
    "ContractStatusChangeDate",
    "PurchaseContractDate"
]

for col in date_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")


# 5. important numeric columns for housing EDA

important_numeric = [
    "ListPrice", "ClosePrice","OriginalListPrice", "LivingArea","LotSizeAcres", "BedroomsTotal",
    "BathroomsTotalInteger","YearBuilt", "DaysOnMarket"]

important_numeric = [col for col in important_numeric if col in df.columns]

if important_numeric:
    print("Important numeric summary:")
    print(df[important_numeric].describe().T)
    print()


output_dir = r"C:\Users\irisz\OneDrive\桌面\IDX Exchange\Listing\eda_output"
os.makedirs(output_dir, exist_ok=True)

percentile_tables = []
outlier_tables = []

for col in important_numeric:
    # convert to numeric and remove missing values for this column only
    series = pd.to_numeric(df[col], errors="coerce").dropna()

    if len(series) == 0:
        print(f"{col}: no valid data")
        continue

    print("\n" + "=" * 60)
    print(f"{col}")
    print("=" * 60)

    # percentile summary
    percentiles = series.quantile([0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99])
    percentile_df = pd.DataFrame({
        "column": col,
        "percentile": ["1%", "5%", "25%", "50%", "75%", "95%", "99%"],
        "value": percentiles.values
    })
    percentile_tables.append(percentile_df)

    print("Percentile summary:")
    print(percentiles)

    # outlier detection using IQR
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1

    lower_1_5 = q1 - 1.5 * iqr
    upper_1_5 = q3 + 1.5 * iqr

    lower_3 = q1 - 3 * iqr
    upper_3 = q3 + 3 * iqr

    outliers_1_5 = series[(series < lower_1_5) | (series > upper_1_5)]
    extreme_outliers = series[(series < lower_3) | (series > upper_3)]

    outlier_info = pd.DataFrame({
        "column": [col],
        "count_non_missing": [len(series)],
        "Q1": [q1],
        "Q3": [q3],
        "IQR": [iqr],
        "lower_bound_1.5IQR": [lower_1_5],
        "upper_bound_1.5IQR": [upper_1_5],
        "lower_bound_3IQR": [lower_3],
        "upper_bound_3IQR": [upper_3],
        "outlier_count_1.5IQR": [len(outliers_1_5)],
        "extreme_outlier_count_3IQR": [len(extreme_outliers)]
    })
    outlier_tables.append(outlier_info)

    print("\nOutlier summary:")
    print(outlier_info)

    # save extreme outlier rows for later handling
    extreme_rows = df[pd.to_numeric(df[col], errors="coerce").isin(extreme_outliers)]
    extreme_rows.to_csv(os.path.join(output_dir, f"{col}_extreme_outliers.csv"), index=False, encoding="utf-8-sig")

    # histogram
    plt.figure(figsize=(8, 5))
    plt.hist(series, bins=50, edgecolor="black")
    plt.title(f"Histogram of {col}")
    plt.xlabel(col)
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{col}_histogram.png"))
    plt.close()

    # boxplot
    plt.figure(figsize=(8, 5))
    plt.boxplot(series, vert=True)
    plt.title(f"Boxplot of {col}")
    plt.ylabel(col)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{col}_boxplot.png"))
    plt.close()

# combine all percentile summaries
if percentile_tables:
    percentile_summary = pd.concat(percentile_tables, ignore_index=True)
    percentile_summary.to_csv(
        os.path.join(output_dir, "percentile_summary_all_numeric.csv"),
        index=False,
        encoding="utf-8-sig"
    )

# combine all outlier summaries
if outlier_tables:
    outlier_summary = pd.concat(outlier_tables, ignore_index=True)
    outlier_summary.to_csv(
        os.path.join(output_dir, "outlier_summary_all_numeric.csv"),
        index=False,
        encoding="utf-8-sig"
    )

print("\nEDA for important numeric fields is complete.")
print("Results saved to:", output_dir)


# Drop rows only for the important numeric columns we care about

df_numeric_complete = df.dropna(subset=important_numeric)

print("Original shape:", df.shape)
print("After dropping rows with missing important numeric values:", df_numeric_complete.shape)

print(df_numeric_complete[important_numeric].describe().T)

# 7. Categorical summaries

categorical_cols = [
    "City", "CountyOrParish", "PropertyType", "PropertySubType",
    "MlsStatus", "StateOrProvince", "SubdivisionName",
    "ListOfficeName", "BuyerOfficeName"
]

for col in categorical_cols:
    if col in df.columns:
        print(f"Top 10 values for {col}:")
        print(df[col].value_counts(dropna=False).head(10))
        print()

# 9. Correlation matrix

corr_cols = [col for col in ["ListPrice", "ClosePrice", "LivingArea", "BedroomsTotal",
                             "BathroomsTotalInteger", "LotSizeSquareFeet",
                             "YearBuilt", "DaysOnMarket"] if col in df.columns]

if len(corr_cols) >= 2:
    corr = df[corr_cols].corr()
    print("Correlation matrix:")
    print(corr)


print("Outputs saved to:", output_dir)