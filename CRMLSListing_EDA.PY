import pandas as pd
import matplotlib.pyplot as plt
import os

# 1. Combined dataset
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

print("Top missing values:")
missing_summary.head(25)
print()

cols_to_drop = missing_summary[missing_summary["missing_percent"] == 100].index.tolist()
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
df["ListingKey"].duplicated().sum()


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

#5. Numeric column

numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

print("Numeric columns:")
print(numeric_cols)

if numeric_cols:
    print("Summary statistics:")
    print(df[numeric_cols].describe().T)
    print("There are big discrepancy betwwen list price and close price because lots of data missing in the close price. ")


# 5. important columns for housing EDA

important_numeric = [
    "ListPrice", "ClosePrice", "LivingArea", "BedroomsTotal",
    "BathroomsTotalInteger", "LotSizeSquareFeet", "YearBuilt",
    "DaysOnMarket", "TaxAnnualAmount", "GarageSpaces", "Stories"
]

important_numeric = [col for col in important_numeric if col in df.columns]

if important_numeric:
    print("Important numeric summary:")
    print(df[important_numeric].describe().T)
    print()

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

# 8. Create output folder

output_dir = os.path.join(os.path.dirname(file_path), "eda_output")
os.makedirs(output_dir, exist_ok=True)

# 9. Correlation matrix

corr_cols = [col for col in ["ListPrice", "ClosePrice", "LivingArea", "BedroomsTotal",
                             "BathroomsTotalInteger", "LotSizeSquareFeet",
                             "YearBuilt", "DaysOnMarket"] if col in df.columns]

if len(corr_cols) >= 2:
    corr = df[corr_cols].corr()
    print("Correlation matrix:")
    print(corr)


print("Outputs saved to:", output_dir)