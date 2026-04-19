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