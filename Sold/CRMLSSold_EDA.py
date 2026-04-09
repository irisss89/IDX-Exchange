import pandas as pd
import matplotlib.pyplot as plt
import os

# 1. Combined dataset
file_path = r"C:\Users\irisz\OneDrive\桌面\IDX Exchange\Sold\CRMLSSold_combined.csv"
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

#close price investigation
print("Median ClosePrice:", df["ClosePrice"].median())
print("Average ClosePrice:", df["ClosePrice"].mean())

# Check property categories 
df['PropertyType'].unique() 
# Filter residential 
df = df[df.PropertyType == 'Residential'] 
print(df["PropertyType"].value_counts(dropna=False))
df_residential = df[df["PropertyType"] == "Residential"].copy()
print(df_residential.shape)
print(df_residential.isnull().sum().sort_values(ascending=False))

missing_check = pd.DataFrame({
    "missing_count": df_residential.isnull().sum(),
    "missing_percent": df_residential.isnull().mean() * 100
}).sort_values("missing_percent", ascending=False)

print(missing_check)



# Validate completeness 
df.isnull().sum() 




# 2. Missing values
missing_count = df.isnull().sum()
missing_percent = df.isnull().mean() * 100

missing_summary = pd.DataFrame({
    "missing_count": missing_count,
    "missing_percent": missing_percent
}).sort_values("missing_percent", ascending=False)

# flag columns with >90% missing
missing_summary["flag_gt_90_missing"] = (missing_summary["missing_percent"] > 90).astype(int)

print("Top missing values:")
print(missing_summary.head(20))
print()

# choose core fields that should be retained even if partially missing
core_fields = [
    "ListingKey",
    "ListingId",
    "PropertyType",
    "PropertySubType",
    "City",
    "StateOrProvince",
    "PostalCode",
    "BedroomsTotal",
    "BathroomsTotalInteger",
    "LivingArea",
    "LotSizeAcres",
    "YearBuilt",
    "ListPrice",
    "ClosePrice",
    "OriginalListPrice",
    "DaysOnMarket",
    "CloseDate",
    "ListingContractDate",
    "CountyOrParish",
    "MlsStatus",
    "UnparsedAddress"
]

core_fields = [col for col in core_fields if col in df.columns]

# decide what to drop vs retain
cols_to_drop = [
    col for col in missing_summary.index
    if (missing_summary.loc[col, "missing_percent"] > 90) and (col not in core_fields)
]

cols_to_retain = [col for col in df.columns if col not in cols_to_drop]

print("Columns with >90% missing:")
print(missing_summary[missing_summary["flag_gt_90_missing"] == 1])
print()

print("Core fields retained even if partially missing:")
print(core_fields)
print()

print("Columns to drop:")
print(cols_to_drop)
print(f"Number of columns to drop: {len(cols_to_drop)}")
print()

print("Number of columns to retain:", len(cols_to_retain))
print()

