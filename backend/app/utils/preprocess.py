import pandas as pd
from typing import List

"""
Simple preprocessing helpers for your backend.

This module should mirror (as much as possible) the preprocessing you used
during training. If your training used an sklearn Pipeline that already
contains preprocessing, you can skip many of these steps and call the pipeline
directly from the model.

Keep this file small — add project-specific transforms as you go.
"""


def basic_preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Basic, safe preprocessing for incoming CSVs or feature DataFrames:
      - drop entirely empty columns
      - fill numeric NaNs with column median
      - fill categorical NaNs with a placeholder string
      - ensure deterministic column order if you expect a fixed schema (optional)
    Adjust this to match the exact preprocessing used in training.
    """
    # drop fully empty columns
    df = df.loc[:, df.notna().any()]

    # numeric columns: fill NaN with median
    num_cols = df.select_dtypes(include=["number"]).columns
    for c in num_cols:
        median = df[c].median()
        if pd.isna(median):
            median = 0
        df[c] = df[c].fillna(median)

    # object / categorical columns: fill NaN with "missing"
    obj_cols = df.select_dtypes(include=["object", "category"]).columns
    for c in obj_cols:
        df[c] = df[c].fillna("missing")

    return df


def features_from_list(features: List[List[float]], column_names: List[str] = None) -> pd.DataFrame:
    """
    Convert raw features (list of lists) into a DataFrame.
    If column_names provided, set them; otherwise columns are auto-indexed.
    """
    df = pd.DataFrame(features)
    if column_names:
        if len(column_names) != df.shape[1]:
            raise ValueError("column_names length must match number of feature columns")
        df.columns = column_names
    return basic_preprocess_dataframe(df)
