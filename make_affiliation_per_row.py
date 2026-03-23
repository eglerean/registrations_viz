"""
Joins registrations.csv with affiliation_map.csv to produce
affiliation_per_row.csv — one row per registration, two columns:
  original  : raw affiliation string from registrations.csv
  fixed     : consolidated name from affiliation_map.csv
"""

import pandas as pd

reg = pd.read_csv("registrations.csv", sep=";")
reg.columns = reg.columns.str.strip()
reg["Affiliation or university"] = (
    reg["Affiliation or university"].astype(str).str.strip().replace("nan", "")
)

aff_map = pd.read_csv("affiliation_map.csv")  # columns: original, fixed

result = (
    reg[["Affiliation or university"]]
    .rename(columns={"Affiliation or university": "original"})
    .merge(aff_map, on="original", how="left")
)
result.loc[result["original"] == "", "fixed"] = ""
result["fixed"] = result["fixed"].fillna(result["original"])  # fallback: keep raw

result.to_csv("affiliation_per_row.csv", index=False)
print(f"Saved affiliation_per_row.csv  ({len(result)} rows)")
