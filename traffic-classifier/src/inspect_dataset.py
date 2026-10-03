"""
Dataset Inspection Script for Encrypted Traffic Classification Pipeline.
Performs thorough discovery on raw dataset files without making destructive modifications.
"""

import argparse
import json
import os

import numpy as np
import pandas as pd


def inspect_dataset(data_path: str, output_report_path: str) -> dict:
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset file not found at: {os.path.abspath(data_path)}")

    print("==================================================")
    print(f" Inspecting Dataset: {os.path.abspath(data_path)}")
    print("==================================================")

    df = pd.read_csv(data_path)
    n_rows, n_cols = df.shape

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

    missing_counts = df.isnull().sum().to_dict()
    total_missing = sum(missing_counts.values())

    inf_counts = {}
    for col in numeric_cols:
        inf_cnt = int(np.isinf(df[col]).sum())
        inf_counts[col] = inf_cnt
    total_inf = sum(inf_counts.values())

    full_duplicates = int(df.duplicated().sum())
    feature_cols = [c for c in df.columns if c != "traffic_type"]
    feature_duplicates = int(df.duplicated(subset=feature_cols).sum())

    # Target discovery
    target_candidates = [col for col in df.columns if "type" in col.lower() or "label" in col.lower() or "class" in col.lower()]
    target_col = target_candidates[0] if target_candidates else df.columns[-1]

    class_counts = df[target_col].value_counts().to_dict()
    total_samples = len(df)
    class_ratios = {k: round(v / total_samples, 4) for k, v in class_counts.items()}

    min_class_cnt = min(class_counts.values())
    max_class_cnt = max(class_counts.values())
    imbalance_ratio = round(max_class_cnt / min_class_cnt, 2)

    # Leakage check: check for identifiers like IP, MAC, Flow ID, timestamps
    identifier_keywords = ["ip", "mac", "flow_id", "timestamp", "port", "src", "dst", "file"]
    potential_leakage_cols = [
        c for c in df.columns if (c.lower() in ["id", "row_id", "flow_id"] or any(kw in c.lower() for kw in identifier_keywords)) and c != target_col
    ]

    report = {
        "dataset_path": os.path.abspath(data_path),
        "shape": [n_rows, n_cols],
        "num_rows": n_rows,
        "num_cols": n_cols,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "total_missing_values": total_missing,
        "missing_values_by_col": missing_counts,
        "total_infinite_values": total_inf,
        "infinite_values_by_col": inf_counts,
        "full_row_duplicates": full_duplicates,
        "feature_only_duplicates": feature_duplicates,
        "target_column": target_col,
        "num_classes": len(class_counts),
        "class_counts": class_counts,
        "class_proportions": class_ratios,
        "imbalance_ratio": imbalance_ratio,
        "potential_identifier_or_leakage_cols": potential_leakage_cols,
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
    }

    # Console Summary Output
    print(f"\n[+] Dataset Shape: {n_rows} rows x {n_cols} columns")
    print(f"[+] Target Column Detected: '{target_col}' ({len(class_counts)} unique classes)")
    print(f"[+] Missing Values: {total_missing}")
    print(f"[+] Infinite Values: {total_inf}")
    print(f"[+] Full-Row Duplicates: {full_duplicates} ({round(full_duplicates/n_rows*100, 2)}%)")
    print(f"[+] Imbalance Ratio (Max/Min Class): {imbalance_ratio}x")
    print("\n--- Class Distribution ---")
    for cls, cnt in class_counts.items():
        print(f"  {cls:<15}: {cnt:>6} ({class_ratios[cls]*100:.2f}%)")

    if potential_leakage_cols:
        print(f"\n[!] WARNING: Potential identifier/leakage columns detected: {potential_leakage_cols}")
    else:
        print("\n[OK] Leakage Audit Passed: No explicit IP, MAC, Port, or ID columns found.")

    if output_report_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_report_path)), exist_ok=True)
        with open(output_report_path, "w") as f:
            json.dump(report, f, indent=4)
        print(f"\n[OK] Detailed inspection report saved to: {os.path.abspath(output_report_path)}")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect encrypted traffic classification dataset.")
    parser.add_argument("--data-path", type=str, default="../consolidated_traffic_data.csv", help="Path to input CSV")
    parser.add_argument("--output-report", type=str, default="reports/dataset_report.json", help="Report JSON path")
    args = parser.parse_args()

    # Handle running from within src/ directory or root directory
    data_path = args.data_path
    if not os.path.exists(data_path) and os.path.exists(os.path.join("..", data_path)):
        data_path = os.path.join("..", data_path)

    inspect_dataset(data_path, args.output_report)
