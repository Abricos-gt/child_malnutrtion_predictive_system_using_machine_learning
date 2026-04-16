import pandas as pd
import numpy as np
import os

# This ensures the script finds the CSVs regardless of where you run it from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TABLES_DIR = os.path.join(BASE_DIR, "who_tables")

def load_who_table(name):
    return pd.read_csv(os.path.join(TABLES_DIR, name))

# Load global tables
wfa_boys = load_who_table("wfa_boys.csv")
wfa_girls = load_who_table("wfa_girls.csv")
hfa_boys = load_who_table("hfa_boys.csv")
hfa_girls = load_who_table("hfa_girls.csv")
wfh_boys = load_who_table("wfh_boys.csv")
wfh_girls = load_who_table("wfh_girls.csv")

def zscore_calc(x, L, M, S):
    if L == 0:
        return np.log(x / M) / S
    return ((x / M) ** L - 1) / (L * S)

def get_lms(df, col, value):
    df = df.copy()
    df["diff"] = (df[col] - value).abs()
    row = df.loc[df["diff"].idxmin()]
    return row["L"], row["M"], row["S"]

def compute_zscores(age, weight, height, gender):
    gender = str(gender).lower()
    wfa = wfa_boys if gender == "male" else wfa_girls
    hfa = hfa_boys if gender == "male" else hfa_girls
    wfh = wfh_boys if gender == "male" else wfh_girls

    # WAZ (Weight-for-Age)
    L, M, S = get_lms(wfa, "Month", age)
    waz = zscore_calc(weight, L, M, S)

    # HAZ (Height-for-Age)
    L, M, S = get_lms(hfa, "Month", age)
    haz = zscore_calc(height, L, M, S)

    # WHZ (Weight-for-Height)
    h_col = "Height_Length" if "Height_Length" in wfh.columns else "Height"
    L, M, S = get_lms(wfh, h_col, height)
    whz = zscore_calc(weight, L, M, S)

    return haz, whz, waz