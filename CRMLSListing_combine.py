import pandas as pd
import glob
import os

folder = r"C:\Users\irisz\OneDrive\桌面\IDX Exchange\Listing"
files = sorted(glob.glob(os.path.join(folder, "CRMLSListing*.csv")))

df_list = []
bad_files = []

for file in files:
    try:
        try:
            df = pd.read_csv(file, encoding="utf-8")
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file, encoding="cp1252")
            except UnicodeDecodeError:
                df = pd.read_csv(file, encoding="latin1")

        df["source_file"] = os.path.basename(file)
        df_list.append(df)
        print(f"Loaded: {os.path.basename(file)}")

    except Exception as e:
        bad_files.append((file, str(e)))
        print(f"Failed: {os.path.basename(file)} -> {e}")

combined_df = pd.concat(df_list, ignore_index=True)

output_file = os.path.join(folder, "CRMLSListing_combined.csv")
combined_df.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"\nCombined {len(df_list)} files")
print(f"Saved to: {output_file}")

if bad_files:
    print("\nBad files:")
    for f, err in bad_files:
        print(f"{os.path.basename(f)}: {err}")