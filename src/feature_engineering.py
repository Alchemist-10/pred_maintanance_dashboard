"""Feature engineering for CMAPSS turbofan predictive maintenance.

This module keeps feature creation simple and Pandas-first.

Notes
-----
- The dashboard pipeline in `src/prepare_cmapss.py` is heuristic and does not
  require ML features.
- These helpers are intended for the optional ML extension of the project.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


def sensor_columns(df: pd.DataFrame) -> list[str]:
    """Return sensor columns present in the DataFrame (s01..s21)."""

    return [c for c in df.columns if c.startswith("s")]


def add_rolling_features(
    df: pd.DataFrame,
    columns: Iterable[str] | None = None,
    window: int = 5,
    group_key: str = "unit",
) -> pd.DataFrame:
    """Add rolling mean/std features per unit.

    Produces columns like: `{col}_roll_mean_{window}`, `{col}_roll_std_{window}`.

    The function assumes the data within each unit is already sorted by cycle.
    """

    if window <= 1:
        raise ValueError("window must be > 1")

    cols = list(columns) if columns is not None else sensor_columns(df)
    out = df.copy()

    grouped = out.groupby(group_key, sort=False)
    for c in cols:
        roll = grouped[c].rolling(window=window, min_periods=1)
        out[f"{c}_roll_mean_{window}"] = roll.mean().reset_index(level=0, drop=True)
        out[f"{c}_roll_std_{window}"] = roll.std(ddof=0).reset_index(level=0, drop=True).fillna(0.0)

    return out


@dataclass(frozen=True)
class FeatureMatrix:
    X: np.ndarray
    feature_names: list[str]


def to_feature_matrix(
    df: pd.DataFrame,
    feature_cols: Iterable[str] | None = None,
    drop_na: bool = True,
) -> FeatureMatrix:
    """Convert a DataFrame to a dense NumPy feature matrix."""

    if feature_cols is None:
        # Default: settings + sensors (raw). Rolling features can be added upstream.
        feature_cols = [c for c in df.columns if c.startswith("setting_") or c.startswith("s")]

    cols = list(feature_cols)
    mat = df[cols].apply(pd.to_numeric, errors="coerce")
    if drop_na:
        mat = mat.fillna(0.0)

    return FeatureMatrix(X=mat.to_numpy(dtype=float), feature_names=cols)
