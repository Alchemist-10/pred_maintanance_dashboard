"""Optional ML inference utilities for CMAPSS.

Pairs with `src/train.py` (ridge regression baseline). This module can be used
from notebooks or as a small CLI to score a CMAPSS table.

Usage
-----
python src/inference.py --model data/models/rul_ridge.npz --input train_FD001.txt/train_FD001.txt --out data/processed/predictions.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import feature_engineering as fe
import preprocessing as pp
from train import RidgeModel, load_model


def predict_rul(model: RidgeModel, df: pd.DataFrame) -> np.ndarray:
    """Predict RUL for each row of `df` using a trained `RidgeModel`."""

    fm = fe.to_feature_matrix(df, feature_cols=model.feature_names)
    X = fm.X

    # Standardize using training stats
    X_std = (X - model.x_mean) / model.x_std
    y_pred = X_std @ model.coef + model.intercept

    return y_pred


def score_file(model_path: Path, input_path: Path, rolling_window: int = 5) -> pd.DataFrame:
    model = load_model(model_path)

    df = pp.read_cmapss_table(input_path)
    df = df.sort_values(["unit", "cycle"], kind="mergesort")
    df = fe.add_rolling_features(df, window=rolling_window)

    pred = predict_rul(model, df)

    out = df[["unit", "cycle"]].copy()
    out["pred_rul"] = pred
    return out


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run baseline RUL inference using the ridge regression model")
    p.add_argument("--model", type=Path, required=True, help="Path to model .npz produced by src/train.py")
    p.add_argument(
        "--input",
        type=Path,
        default=Path("train_FD001.txt/train_FD001.txt"),
        help="CMAPSS train/test file to score. Default: train_FD001.txt/train_FD001.txt",
    )
    p.add_argument(
        "--rolling-window",
        type=int,
        default=5,
        help="Rolling window for feature engineering. Must match training. Default: 5",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=Path("data/processed/predictions.csv"),
        help="Output CSV path. Default: data/processed/predictions.csv",
    )
    return p


def main() -> None:
    args = build_arg_parser().parse_args()

    df_out = score_file(args.model, args.input, rolling_window=args.rolling_window)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(args.out, index=False)

    print(f"Wrote {len(df_out):,} predictions -> {args.out}")


if __name__ == "__main__":
    main()
