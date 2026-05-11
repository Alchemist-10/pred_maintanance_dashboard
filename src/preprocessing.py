"""Preprocessing utilities for the NASA CMAPSS turbofan dataset.

This module contains lightweight, dependency-minimal helpers (NumPy/Pandas only)
that you can reuse across notebooks, training scripts, and dashboard pipelines.

Design goals:
- Keep functions import-safe (no work at import time)
- Prefer explicit DataFrame inputs/outputs
- Avoid heavy ML dependencies (scikit-learn) to match this repo's requirements
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


def cmapss_columns() -> list[str]:
    """Return the canonical CMAPSS column names for train/test text files."""

    cols = ["unit", "cycle", "setting_1", "setting_2", "setting_3"]
    cols += [f"s{i:02d}" for i in range(1, 22)]  # 21 sensors
    return cols


def read_cmapss_table(path: Path) -> pd.DataFrame:
    """Read a CMAPSS train/test file into a typed DataFrame.

    The NASA CMAPSS files are whitespace separated with occasional trailing spaces.
    """

    df = pd.read_csv(path, sep=r"\s+", header=None, engine="python")

    expected_cols = len(cmapss_columns())
    if df.shape[1] < expected_cols:
        raise ValueError(
            f"Unexpected column count in {path.name}: got {df.shape[1]}, expected {expected_cols}. "
            "Make sure you are pointing at a CMAPSS train/test text file (train_FD00X.txt)."
        )

    # Some CMAPSS mirrors include extra trailing blank columns.
    if df.shape[1] > expected_cols:
        extra = df.iloc[:, expected_cols:]
        if extra.isna().all().all():
            df = df.iloc[:, :expected_cols]
        else:
            raise ValueError(
                f"Unexpected column count in {path.name}: got {df.shape[1]}, expected {expected_cols}. "
                "Extra columns are not empty; this doesn't look like a standard CMAPSS file."
            )

    df.columns = cmapss_columns()
    df["unit"] = df["unit"].astype(int)
    df["cycle"] = df["cycle"].astype(int)
    return df


def add_train_rul(train_df: pd.DataFrame) -> pd.DataFrame:
    """Add `rul` column for training data (max_cycle - cycle per unit)."""

    max_cycle = train_df.groupby("unit")["cycle"].transform("max")
    out = train_df.copy()
    out["rul"] = (max_cycle - out["cycle"]).astype(int)
    return out


def train_val_split_by_unit(
    df: pd.DataFrame,
    val_fraction: float = 0.2,
    seed: int = 0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a frame into train/val sets by *unit* (prevents leakage across cycles)."""

    if not 0.0 < val_fraction < 1.0:
        raise ValueError("val_fraction must be in (0, 1)")

    units = df["unit"].dropna().astype(int).unique()
    rng = np.random.default_rng(seed)
    rng.shuffle(units)

    n_val = max(1, int(round(len(units) * val_fraction)))
    val_units = set(units[:n_val].tolist())

    is_val = df["unit"].astype(int).isin(val_units)
    return df.loc[~is_val].copy(), df.loc[is_val].copy()


@dataclass(frozen=True)
class StandardizationStats:
    mean: dict[str, float]
    std: dict[str, float]


def standardize_columns(
    df: pd.DataFrame,
    columns: Iterable[str],
    stats: StandardizationStats | None = None,
    eps: float = 1e-12,
) -> tuple[pd.DataFrame, StandardizationStats]:
    """Z-score standardize selected columns.

    If `stats` is provided, it will be reused (e.g., val/test standardization).
    Returns a new DataFrame and the stats used.
    """

    cols = list(columns)
    out = df.copy()

    if stats is None:
        mean = {c: float(pd.to_numeric(out[c], errors="coerce").mean()) for c in cols}
        std = {c: float(pd.to_numeric(out[c], errors="coerce").std(ddof=0)) for c in cols}
        stats = StandardizationStats(mean=mean, std=std)

    for c in cols:
        mu = stats.mean[c]
        sigma = stats.std[c]
        denom = sigma if abs(sigma) > eps else 1.0
        out[c] = (pd.to_numeric(out[c], errors="coerce") - mu) / denom

    return out, stats
