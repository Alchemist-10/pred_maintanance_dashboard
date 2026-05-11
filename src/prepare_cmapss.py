"""Prepare NASA CMAPSS turbofan data for BI dashboards.

This script reads the NASA CMAPSS text files (e.g., train_FD001.txt),
engineers a few dashboard-friendly metrics, and writes a single flat table
(CSV) that can be consumed by Power BI or Tableau.

The goal is to keep the output simple and explicit:
- unit / cycle identifiers
- RUL (Remaining Useful Life) for the training set
- failure_probability_30: heuristic probability of failure within 30 cycles
- maintenance bucket fields for heatmaps
- component_health_score: blended RUL- and sensor-degradation-based score

Notes
-----
- This script intentionally uses a lightweight, heuristic approach so it can
  run without model training.
- For a "real" probability-of-failure model, replace the heuristic with a
  trained survival model or classifier.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd 


@dataclass(frozen=True)
class CmapssSubset:
    name: str
    train_file: str
    test_file: str
    rul_file: str


SUBSETS: dict[str, CmapssSubset] = {
    "FD001": CmapssSubset("FD001", "train_FD001.txt", "test_FD001.txt", "RUL_FD001.txt"),
    "FD002": CmapssSubset("FD002", "train_FD002.txt", "test_FD002.txt", "RUL_FD002.txt"),
    "FD003": CmapssSubset("FD003", "train_FD003.txt", "test_FD003.txt", "RUL_FD003.txt"),
    "FD004": CmapssSubset("FD004", "train_FD004.txt", "test_FD004.txt", "RUL_FD004.txt"),
}


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _cmapss_columns() -> list[str]:
    cols = ["unit", "cycle", "setting_1", "setting_2", "setting_3"]
    cols += [f"s{i:02d}" for i in range(1, 22)]  # 21 sensors
    return cols


def read_cmapss_table(path: Path) -> pd.DataFrame:
    # NASA CMAPSS files are whitespace separated with occasional trailing spaces.
    df = pd.read_csv(path, sep=r"\s+", header=None, engine="python")

    expected_cols = len(_cmapss_columns())
    if df.shape[1] != expected_cols:
        raise ValueError(
            f"Unexpected column count in {path.name}: got {df.shape[1]}, expected {expected_cols}. "
            "Make sure you are pointing at a CMAPSS train/test text file (train_FD00X.txt)."
        )

    df.columns = _cmapss_columns()
    df["unit"] = df["unit"].astype(int)
    df["cycle"] = df["cycle"].astype(int)
    return df


def add_train_rul(train_df: pd.DataFrame) -> pd.DataFrame:
    max_cycle = train_df.groupby("unit")["cycle"].transform("max")
    train_df = train_df.copy()
    train_df["rul"] = (max_cycle - train_df["cycle"]).astype(int)
    return train_df


def add_failure_probability(train_df: pd.DataFrame, horizon_cycles: int = 30, scale: float = 10.0) -> pd.DataFrame:
    """Heuristic probability of failure within `horizon_cycles`.

    We interpret low RUL as high near-term failure risk.

    p = sigmoid((horizon - RUL) / scale)

    - When RUL == horizon -> p ~= 0.5
    - When RUL << horizon -> p approaches 1
    - When RUL >> horizon -> p approaches 0
    """

    df = train_df.copy()
    x = (horizon_cycles - df["rul"].to_numpy(dtype=float)) / float(scale)
    df[f"failure_probability_{horizon_cycles}"] = _sigmoid(x)
    return df


def add_maintenance_buckets(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["maintenance_due_in_cycles"] = out["rul"].astype(int)

    bins = [-1, 10, 20, 30, 50, 100, 10_000]
    labels = ["0-10", "11-20", "21-30", "31-50", "51-100", "100+"]
    out["maintenance_bucket"] = pd.cut(out["maintenance_due_in_cycles"], bins=bins, labels=labels)

    out["maintenance_flag"] = np.where(out["maintenance_due_in_cycles"] <= 30, "Due <=30", "Not due")
    return out


def add_health_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Add a blended component health score.

    - health_rul: normalized RUL per unit (1.0 at start, 0.0 at failure)
    - health_sensor: normalized deviation from early-life sensor baseline

    component_health_score = mean(health_rul, health_sensor)
    """

    out = df.copy()

    # RUL-based health (simple, intuitive for dashboarding)
    max_rul_unit = out.groupby("unit")["rul"].transform("max").astype(float)
    out["health_rul"] = np.where(max_rul_unit > 0, out["rul"].astype(float) / max_rul_unit, 0.0)
    out["health_rul"] = out["health_rul"].clip(0.0, 1.0)

    sensor_cols = [c for c in out.columns if c.startswith("s")]

    # Baseline: average of first 5 cycles per unit
    baseline = (
        out[out["cycle"] <= 5]
        .groupby("unit")[sensor_cols]
        .mean()
        .rename(columns={c: f"{c}_baseline" for c in sensor_cols})
    )

    out = out.merge(baseline, how="left", left_on="unit", right_index=True)

    baseline_cols = [f"{c}_baseline" for c in sensor_cols]
    delta = out[sensor_cols].to_numpy(dtype=float) - out[baseline_cols].to_numpy(dtype=float)
    delta_norm = np.linalg.norm(delta, axis=1)

    out["sensor_delta_norm"] = delta_norm

    max_delta_unit = out.groupby("unit")["sensor_delta_norm"].transform("max").astype(float)
    out["health_sensor"] = np.where(max_delta_unit > 0, 1.0 - (out["sensor_delta_norm"] / max_delta_unit), 1.0)
    out["health_sensor"] = out["health_sensor"].clip(0.0, 1.0)

    out["component_health_score"] = (out["health_rul"] + out["health_sensor"]) / 2.0

    # Cleanup baseline columns (keep the delta norm as an explainer metric)
    out = out.drop(columns=baseline_cols)
    return out


def prepare_train(dataset_dir: Path, subset: str) -> pd.DataFrame:
    subset_info = SUBSETS[subset]
    train_path = dataset_dir / subset_info.train_file
    if not train_path.exists():
        raise FileNotFoundError(
            f"Missing {train_path}. Download NASA CMAPSS and place files under {dataset_dir}"
        )

    train_df = read_cmapss_table(train_path)
    train_df = add_train_rul(train_df)
    train_df = add_failure_probability(train_df, horizon_cycles=30, scale=10.0)
    train_df = add_maintenance_buckets(train_df)
    train_df = add_health_scores(train_df)

    train_df["subset"] = subset
    train_df["split"] = "train"
    return train_df


def write_output(df: pd.DataFrame, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Prepare NASA CMAPSS dataset for Power BI/Tableau dashboards")
    p.add_argument(
        "--dataset-dir",
        type=Path,
        default=Path("data/raw/cmapss"),
        help="Folder containing CMAPSS text files (train_FD001.txt, etc.). Default: data/raw/cmapss",
    )
    p.add_argument(
        "--subset",
        type=str,
        default="FD001",
        choices=sorted(SUBSETS.keys()),
        help="CMAPSS subset to prepare (FD001..FD004). Default: FD001",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=Path("data/processed/turbofan_dashboard.csv"),
        help="Output CSV path for dashboard ingestion. Default: data/processed/turbofan_dashboard.csv",
    )
    return p


def main() -> None:
    args = build_arg_parser().parse_args()

    df_train = prepare_train(args.dataset_dir, args.subset)

    # Keep output stable: put the dashboard metrics first
    horizon_col = "failure_probability_30"
    first_cols = [
        "subset",
        "split",
        "unit",
        "cycle",
        "rul",
        horizon_col,
        "maintenance_due_in_cycles",
        "maintenance_bucket",
        "maintenance_flag",
        "component_health_score",
        "health_rul",
        "health_sensor",
        "sensor_delta_norm",
        "setting_1",
        "setting_2",
        "setting_3",
    ]
    remaining_cols = [c for c in df_train.columns if c not in first_cols]
    df_out = df_train[first_cols + remaining_cols]

    write_output(df_out, args.out)
    print(f"Wrote {len(df_out):,} rows -> {args.out}")


if __name__ == "__main__":
    main()
