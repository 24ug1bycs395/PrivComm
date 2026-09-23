"""
Training Script for XGBoost Encrypted Traffic Multiclass Classifier.
Trains baseline XGBoost model with early stopping on validation set,
trains comparison baseline models (Random Forest, Logistic Regression),
and exports trained model artifacts and metadata.
"""

import argparse
import datetime
import json
import os
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
try:
    from xgboost import XGBClassifier
    XGBOOST_INSTALLED = True
except ImportError:
    XGBOOST_INSTALLED = False
    XGBClassifier = None

SEED = 42


def train_models(
    processed_data_path: str = "../data/processed/processed_data.npz",
    models_dir: str = "../models",
    n_estimators: int = 300,
    max_depth: int = 6,
    learning_rate: float = 0.1,
    run_comparison: bool = True
) -> dict:
    # Smart path resolution for running from root or src/
    if not os.path.exists(processed_data_path):
        if os.path.exists(os.path.join("data", "processed", "processed_data.npz")):
            processed_data_path = os.path.join("data", "processed", "processed_data.npz")
        elif os.path.exists(os.path.join("..", "data", "processed", "processed_data.npz")):
            processed_data_path = os.path.join("..", "data", "processed", "processed_data.npz")

    if not os.path.exists(models_dir) and os.path.exists("models"):
        models_dir = "models"

    if not os.path.exists(processed_data_path):
        raise FileNotFoundError(f"Processed dataset not found at: {processed_data_path}. Run preprocess.py first.")

    schema_path = os.path.join(models_dir, "feature_schema.json")
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Feature schema not found at: {schema_path}.")

    with open(schema_path, "r") as f:
        schema = json.load(f)

    # Load data splits
    data = np.load(processed_data_path)
    X_train, y_train = data["X_train"], data["y_train"]
    X_val, y_val = data["X_val"], data["y_val"]
    X_test, y_test = data["X_test"], data["y_test"]

    print(f"\n==================================================")
    print(f" Training XGBoost Encrypted Traffic Classifier")
    print(f"==================================================")
    print(f"[+] Train shape: {X_train.shape}, Validation shape: {X_val.shape}, Test shape: {X_test.shape}")
    print(f"[+] Number of classes: {schema['num_classes']}")

    if not XGBOOST_INSTALLED:
        raise ModuleNotFoundError(
            "XGBoost is not installed in your Python environment.\n"
            "Please run: pip install xgboost\n"
            "Then re-run: python src/train.py"
        )
    from sklearn.utils.class_weight import compute_sample_weight
    sample_weights = compute_sample_weight("balanced", y_train)

    xgb_params = {
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "learning_rate": learning_rate,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "objective": "multi:softprob",
        "num_class": schema["num_classes"],
        "eval_metric": "mlogloss",
        "random_state": SEED,
        "tree_method": "hist",
        "early_stopping_rounds": 20
    }

    print(f"\n[+] Initializing XGBClassifier with hyperparameter configuration:")
    for k, v in xgb_params.items():
        print(f"    - {k}: {v}")

    xgb_model = XGBClassifier(**xgb_params)

    print(f"\n[+] Fitting XGBoost with balanced class sample weighting & early stopping...")
    xgb_model.fit(
        X_train,
        y_train,
        sample_weight=sample_weights,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        verbose=50
    )

    best_iteration = getattr(xgb_model, "best_iteration", xgb_params["n_estimators"])
    print(f"[OK] XGBoost training finished! Best iteration: {best_iteration}")

    # Save XGBoost Model
    xgb_model_path = os.path.join(models_dir, "xgboost_traffic_classifier.json")
    xgb_model.save_model(xgb_model_path)
    print(f"[OK] XGBoost model saved to: {os.path.abspath(xgb_model_path)}")

    # Also save as joblib for sklearn pipeline compatibility
    xgb_joblib_path = os.path.join(models_dir, "xgboost_traffic_classifier.joblib")
    joblib.dump(xgb_model, xgb_joblib_path)

    comparison_results = {}

    # 2. Dedicated Model Training: Random Forest Classifier
    if run_comparison:
        print(f"\n[+] Training Dedicated Comparison Model: Random Forest Classifier...")
        rf_model = RandomForestClassifier(
            n_estimators=300,
            max_depth=20,
            class_weight="balanced",
            random_state=SEED,
            n_jobs=-1
        )
        rf_model.fit(X_train, y_train)
        rf_val_acc = rf_model.score(X_val, y_val)
        rf_model_path = os.path.join(models_dir, "random_forest_model.joblib")
        joblib.dump(rf_model, rf_model_path)
        comparison_results["random_forest"] = {"val_accuracy": float(rf_val_acc)}
        print(f"[OK] Random Forest Model saved to: {os.path.abspath(rf_model_path)}")
        print(f"    - Random Forest Validation Accuracy: {rf_val_acc*100:.2f}%")

        print(f"\n[+] Training Comparison Model: Logistic Regression...")
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)

        lr_model = LogisticRegression(max_iter=500, random_state=SEED)
        lr_model.fit(X_train_scaled, y_train)
        lr_val_acc = lr_model.score(X_val_scaled, y_val)
        comparison_results["logistic_regression"] = {"val_accuracy": float(lr_val_acc)}
        joblib.dump(scaler, os.path.join(models_dir, "scaler.joblib"))
        joblib.dump(lr_model, os.path.join(models_dir, "logistic_regression_model.joblib"))
        print(f"    - Logistic Regression Validation Accuracy: {lr_val_acc*100:.2f}%")

    # 3. Create Model Metadata File
    metadata = {
        "model_name": "XGBoost Encrypted Traffic Classifier",
        "dataset": "consolidated_traffic_data.csv",
        "target_column": schema["target_column"],
        "num_features": schema["num_features"],
        "feature_columns": schema["feature_columns"],
        "classes": schema["classes"],
        "num_classes": schema["num_classes"],
        "random_seed": SEED,
        "training_timestamp": datetime.datetime.now().isoformat(),
        "xgboost_parameters": xgb_params,
        "best_iteration": int(best_iteration),
        "dataset_split": schema["split_ratios"],
        "comparison_models": comparison_results
    }

    metadata_path = os.path.join(models_dir, "model_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=4)
    print(f"[OK] Model metadata saved to: {os.path.abspath(metadata_path)}")

    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train XGBoost traffic classifier.")
    parser.add_argument("--processed-data", type=str, default="data/processed/processed_data.npz", help="Processed NPZ path")
    parser.add_argument("--models-dir", type=str, default="models", help="Models output dir")
    parser.add_argument("--n-estimators", type=int, default=400, help="Number of trees")
    parser.add_argument("--max-depth", type=int, default=8, help="Tree max depth")
    parser.add_argument("--learning-rate", type=float, default=0.08, help="Learning rate")
    parser.add_argument("--skip-comparison", action="store_true", help="Skip RF and LR comparison models")
    args = parser.parse_args()

    train_models(
        processed_data_path=args.processed_data,
        models_dir=args.models_dir,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=args.learning_rate,
        run_comparison=not args.skip_comparison
    )
