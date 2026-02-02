import pandas as pd
import json

def update_full_isin_mapping():
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    df = pd.read_csv(url)
    
    mapping = dict(zip(df[' ISIN NUMBER'], df['SYMBOL']))
    
    with open("isin_mapping.json", "w") as f:
        json.dump(mapping, f)
    print("Full NSE Master mapping updated!")

update_full_isin_mapping()