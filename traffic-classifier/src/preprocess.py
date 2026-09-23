"""
Preprocessing Module for Encrypted Traffic Classification Pipeline.
Cleans raw network flow features, handles duplicates/invalid values,
encodes target labels, and generates stratified Train / Validation / Test splits.
"""

import argparse
import json
import os
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Standard random seed for strict reproducibility
SEED = 42


def preprocess_pipeline(
    data_path: str,
    output_dir: str = "../data/processed",
    models_dir: str = "../models",
    remove_duplicates: bool = True
) -> dict:
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Input file not found: {data_path}")

    print(f"\n==================================================")
    print(f" Preprocessing Data: {os.path.abspath(data_path)}")
    print(f"==================================================")

    df = pd.read_csv(data_path)
    initial_rows, initial_cols = df.shape

    # 1. Identify Target and Feature Columns
    target_col = "traffic_type"
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")

    feature_cols = [c for c in df.columns if c != target_col]

    print(f"[+] Initial dataset: {initial_rows} rows x {initial_cols} columns")

    # 2. Check and Drop Identifier / Leakage Columns
    leakage_cols = []
    dropped_cols_log = {}

    for c in feature_cols:
        if c.lower() in ["flow_id", "src_ip", "dst_ip", "src_port", "dst_port", "timestamp"]:
            leakage_cols.append(c)
            dropped_cols_log[c] = "Explicit identifier / leakage risk"

    if leakage_cols:
        print(f"[!] Dropping leakage/identifier columns: {leakage_cols}")
        df.drop(columns=leakage_cols, inplace=True)
        feature_cols = [c for c in feature_cols if c not in leakage_cols]
    else:
        print(f"[OK] No identifier/leakage columns found. Preserving all {len(feature_cols)} base flow features.")

    # 2b. Domain Feature Engineering (Network Ratios & Log Scaling)
    print(f"[+] Engineering domain-specific flow ratios and log-scaled rate features...")
    df['bytes_per_pkt'] = df['flowBytesPerSecond'] / (df['flowPktsPerSecond'] + 1e-5)
    df['fiat_biat_ratio'] = df['mean_fiat'] / (df['mean_biat'] + 1e-5)
    df['log_duration'] = np.log1p(np.maximum(0, df['duration']))
    df['log_bytes_sec'] = np.log1p(np.maximum(0, df['flowBytesPerSecond']))
    df['log_pkts_sec'] = np.log1p(np.maximum(0, df['flowPktsPerSecond']))

    # Update feature columns list
    feature_cols = [c for c in df.columns if c != target_col]

    # 3. Clean Missing and Infinite Values
    # Replace +/- inf with NaN and then drop or handle
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    null_rows = df.isnull().any(axis=1).sum()

    if null_rows > 0:
        print(f"[!] Dropping {null_rows} rows containing NaN / Inf values.")
        df.dropna(inplace=True)
    else:
        print(f"[OK] Zero NaN / Inf values detected.")

    # 4. Remove Duplicates
    if remove_duplicates:
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            print(f"[!] Removing {duplicate_count} exact duplicate rows to prevent train/test leakage...")
            df.drop_duplicates(inplace=True)
        else:
            print(f"[OK] No exact duplicate rows found.")

    cleaned_rows = len(df)
    print(f"[+] Rows after cleaning & deduplication: {cleaned_rows} (Retained {round(cleaned_rows/initial_rows*100, 2)}%)")

    # 5. Target Encoding
    le = LabelEncoder()
    y_encoded = le.fit_transform(df[target_col])
    X = df[feature_cols].values

    classes = list(le.classes_)
    print(f"[+] Target encoded successfully across {len(classes)} classes.")

    # 6. Stratified Train / Validation / Test Split (70% / 15% / 15%)
    # First split: 70% Train, 30% Temp (Val + Test)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y_encoded, test_size=0.30, random_state=SEED, stratify=y_encoded
    )

    # Second split: 50% of Temp = 15% Validation, 50% of Temp = 15% Test
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=SEED, stratify=y_temp
    )

    print(f"\n--- Stratified Split Summary (Seed={SEED}) ---")
    print(f"  Train Set      : {len(X_train):>6} samples ({len(X_train)/cleaned_rows*100:.1f}%)")
    print(f"  Validation Set : {len(X_val):>6} samples ({len(X_val)/cleaned_rows*100:.1f}%)")
    print(f"  Test Set       : {len(X_test):>6} samples ({len(X_test)/cleaned_rows*100:.1f}%)")

    # 7. Save Artifacts
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)

    # Save datasets as compressed numpy binaries
    np.savez_compressed(
        os.path.join(output_dir, "processed_data.npz"),
        X_train=X_train, y_train=y_train,
        X_val=X_val, y_val=y_val,
        X_test=X_test, y_test=y_test
    )

    # Save Label Encoder
    encoder_path = os.path.join(models_dir, "label_encoder.joblib")
    joblib.dump(le, encoder_path)
    print(f"[OK] LabelEncoder saved to: {os.path.abspath(encoder_path)}")

    # Save Feature Schema and Configuration
    schema = {
        "target_column": target_col,
        "feature_columns": feature_cols,
        "num_features": len(feature_cols),
        "classes": [str(c) for c in classes],
        "num_classes": len(classes),
        "dropped_columns": dropped_cols_log,
        "initial_rows": initial_rows,
        "cleaned_rows": cleaned_rows,
        "random_seed": SEED,
        "split_ratios": {"train": 0.70, "validation": 0.15, "test": 0.15}
    }

    schema_path = os.path.join(models_dir, "feature_schema.json")
    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=4)
    print(f"[OK] Feature schema saved to: {os.path.abspath(schema_path)}")

    return schema


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preprocess dataset for traffic classification.")
    parser.add_argument("--data-path", type=str, default="../consolidated_traffic_data.csv", help="Input CSV path")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Processed data dir")
    parser.add_argument("--models-dir", type=str, default="models", help="Models dir")
    parser.add_argument("--keep-duplicates", action="store_true", help="Do not drop duplicate rows")
    args = parser.parse_args()

    # Smart path resolution for data-path
    data_path = args.data_path
    if not os.path.exists(data_path) and os.path.exists(os.path.join("..", data_path)):
        data_path = os.path.join("..", data_path)

    preprocess_pipeline(
        data_path=data_path,
        output_dir=args.output_dir,
        models_dir=args.models_dir,
        remove_duplicates=not args.keep_duplicates
    )
