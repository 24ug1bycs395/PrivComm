"""
Evaluation and Visualization Module for Encrypted Traffic Classifier.
Evaluates trained XGBoost model on the untouched test set, generates
confusion matrix plots, gain-based feature importances, SHAP plots, and JSON report.
"""

import argparse
import json
import os
import sys
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    log_loss,
    precision_recall_fscore_support
)
try:
    from xgboost import XGBClassifier
    XGBOOST_INSTALLED = True
except ImportError:
    XGBOOST_INSTALLED = False
    XGBClassifier = None

# SHAP optional import
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False


def evaluate_pipeline(
    processed_data_path: str = "../data/processed/processed_data.npz",
    models_dir: str = "../models",
    reports_dir: str = "../reports"
) -> dict:
    # Smart path resolution for running from root or src/
    if not os.path.exists(processed_data_path):
        if os.path.exists(os.path.join("data", "processed", "processed_data.npz")):
            processed_data_path = os.path.join("data", "processed", "processed_data.npz")
        elif os.path.exists(os.path.join("..", "data", "processed", "processed_data.npz")):
            processed_data_path = os.path.join("..", "data", "processed", "processed_data.npz")

    if not os.path.exists(models_dir) and os.path.exists("models"):
        models_dir = "models"
    elif not os.path.exists(models_dir) and os.path.exists(os.path.join("..", "models")):
        models_dir = os.path.join("..", "models")

    if not os.path.exists(reports_dir) and os.path.exists("reports"):
        reports_dir = "reports"

    if not os.path.exists(processed_data_path):
        raise FileNotFoundError(f"Processed dataset not found at: {processed_data_path}")

    model_path = os.path.join(models_dir, "xgboost_traffic_classifier.json")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at: {model_path}")

    encoder_path = os.path.join(models_dir, "label_encoder.joblib")
    le = joblib.load(encoder_path)
    classes = list(le.classes_)

    metadata_path = os.path.join(models_dir, "model_metadata.json")
    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    feature_cols = metadata["feature_columns"]

    # Load test split
    data = np.load(processed_data_path)
    X_test, y_test = data["X_test"], data["y_test"]

    print(f"\n==================================================")
    print(f" Evaluating XGBoost Model on Untouched Test Set")
    print(f"==================================================")
    print(f"[+] Test dataset size: {X_test.shape[0]} samples")

    # Evaluate XGBoost Model
    xgb_model = XGBClassifier()
    xgb_model.load_model(model_path)
    y_proba_xgb = xgb_model.predict_proba(X_test)
    y_pred_xgb = np.argmax(y_proba_xgb, axis=1)

    acc_xgb = accuracy_score(y_test, y_pred_xgb)
    macro_p_xgb, macro_r_xgb, macro_f1_xgb, _ = precision_recall_fscore_support(y_test, y_pred_xgb, average="macro")
    weight_p_xgb, weight_r_xgb, weight_f1_xgb, _ = precision_recall_fscore_support(y_test, y_pred_xgb, average="weighted")
    logloss_xgb = log_loss(y_test, y_proba_xgb)

    # Evaluate Random Forest Model if available
    rf_model_path = os.path.join(models_dir, "random_forest_model.joblib")
    rf_metrics = None
    if os.path.exists(rf_model_path):
        rf_model = joblib.load(rf_model_path)
        y_proba_rf = rf_model.predict_proba(X_test)
        y_pred_rf = np.argmax(y_proba_rf, axis=1)

        acc_rf = accuracy_score(y_test, y_pred_rf)
        macro_p_rf, macro_r_rf, macro_f1_rf, _ = precision_recall_fscore_support(y_test, y_pred_rf, average="macro")
        weight_p_rf, weight_r_rf, weight_f1_rf, _ = precision_recall_fscore_support(y_test, y_pred_rf, average="weighted")
        logloss_rf = log_loss(y_test, y_proba_rf)

        rf_metrics = {
            "accuracy": float(round(acc_rf, 4)),
            "macro_precision": float(round(macro_p_rf, 4)),
            "macro_recall": float(round(macro_r_rf, 4)),
            "macro_f1": float(round(macro_f1_rf, 4)),
            "weighted_f1": float(round(weight_f1_rf, 4)),
            "log_loss": float(round(logloss_rf, 4))
        }

    # Per-class metrics for primary model (XGBoost)
    per_cls_p, per_cls_r, per_cls_f1, per_cls_supp = precision_recall_fscore_support(
        y_test, y_pred_xgb, average=None, labels=range(len(classes))
    )

    acc = acc_xgb
    macro_p, macro_r, macro_f1 = macro_p_xgb, macro_r_xgb, macro_f1_xgb
    weight_f1 = weight_f1_xgb
    test_logloss = logloss_xgb
    y_pred = y_pred_xgb

    per_class_results = {}
    for idx, cls_name in enumerate(classes):
        per_class_results[cls_name] = {
            "precision": float(round(per_cls_p[idx], 4)),
            "recall": float(round(per_cls_r[idx], 4)),
            "f1_score": float(round(per_cls_f1[idx], 4)),
            "support": int(per_cls_supp[idx])
        }

    # Best and Worst performing classes by F1 score
    sorted_classes = sorted(per_class_results.items(), key=lambda x: x[1]["f1_score"], reverse=True)
    best_class = sorted_classes[0]
    worst_class = sorted_classes[-1]

    print(f"\n--- Key Test Performance Metrics (XGBoost) ---")
    print(f"  Test Accuracy   : {acc*100:.2f}%")
    print(f"  Macro Precision : {macro_p*100:.2f}%")
    print(f"  Macro Recall    : {macro_r*100:.2f}%")
    print(f"  Macro F1 Score  : {macro_f1*100:.2f}%")
    print(f"  Weighted F1     : {weight_f1*100:.2f}%")
    print(f"  Multi Log Loss  : {test_logloss:.4f}")
    print(f"  Highest F1 Class: '{best_class[0]}' ({best_class[1]['f1_score']*100:.1f}%)")
    print(f"  Lowest F1 Class : '{worst_class[0]}' ({worst_class[1]['f1_score']*100:.1f}%)")

    if rf_metrics:
        print(f"\n--- Model Comparison on Untouched Test Set ---")
        print(f"  Metric              | XGBoost     | Random Forest")
        print(f"  --------------------+-------------+--------------")
        print(f"  Test Accuracy       | {acc*100:.2f}%       | {rf_metrics['accuracy']*100:.2f}%")
        print(f"  Macro Precision     | {macro_p*100:.2f}%       | {rf_metrics['macro_precision']*100:.2f}%")
        print(f"  Macro Recall        | {macro_r*100:.2f}%       | {rf_metrics['macro_recall']*100:.2f}%")
        print(f"  Macro F1 Score      | {macro_f1*100:.2f}%       | {rf_metrics['macro_f1']*100:.2f}%")
        print(f"  Weighted F1         | {weight_f1*100:.2f}%       | {rf_metrics['weighted_f1']*100:.2f}%")
        print(f"  Multi Log Loss      | {test_logloss:.4f}      | {rf_metrics['log_loss']:.4f}")

    # Console Classification Report
    print(f"\n--- Detailed Per-Class Breakdown ---")
    clf_rep_str = classification_report(y_test, y_pred, target_names=classes, digits=4)
    print(clf_rep_str)

    os.makedirs(reports_dir, exist_ok=True)

    # 1. Confusion Matrix Plot
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(12, 10))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=classes, yticklabels=classes,
        cbar=True
    )
    plt.title("XGBoost Encrypted Traffic Classification - Confusion Matrix", fontsize=14, pad=15)
    plt.xlabel("Predicted Traffic Class", fontsize=12)
    plt.ylabel("Actual Traffic Class", fontsize=12)
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()

    cm_path = os.path.join(reports_dir, "confusion_matrix.png")
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"[OK] Confusion Matrix saved to: {os.path.abspath(cm_path)}")

    # 2. XGBoost Feature Importance Plot (Gain-based)
    importances = xgb_model.feature_importances_
    feat_imp_df = pd.DataFrame({"feature": feature_cols, "importance": importances})
    feat_imp_df = feat_imp_df.sort_values(by="importance", ascending=False).reset_index(drop=True)

    plt.figure(figsize=(10, 8))
    sns.barplot(x="importance", y="feature", data=feat_imp_df, palette="viridis")
    plt.title("XGBoost Feature Importance (Gain)", fontsize=14, pad=15)
    plt.xlabel("Relative Importance Score", fontsize=12)
    plt.ylabel("Flow Feature", fontsize=12)
    plt.tight_layout()

    fi_path = os.path.join(reports_dir, "feature_importance.png")
    plt.savefig(fi_path, dpi=300)
    plt.close()
    print(f"[OK] Feature Importance plot saved to: {os.path.abspath(fi_path)}")

    # 3. Optional SHAP Feature Explanations Plot
    shap_path = None
    if SHAP_AVAILABLE:
        try:
            print(f"[+] Calculating SHAP values for explainability...")
            explainer = shap.TreeExplainer(xgb_model)
            # Use sample of test set for fast SHAP calculation
            sample_size = min(500, len(X_test))
            X_sample = X_test[:sample_size]
            shap_values = explainer.shap_values(X_sample)

            plt.figure(figsize=(12, 8))
            shap.summary_plot(shap_values, X_sample, feature_names=feature_cols, class_names=classes, show=False)
            plt.title("SHAP Beeswarm Summary Plot by Traffic Class", fontsize=14, pad=15)
            plt.tight_layout()
            shap_path = os.path.join(reports_dir, "shap_summary.png")
            plt.savefig(shap_path, dpi=300, bbox_inches="tight")
            plt.close()
            print(f"[OK] SHAP summary plot saved to: {os.path.abspath(shap_path)}")
        except Exception as e:
            print(f"[!] SHAP plot generation skipped due to error: {e}")

    # 4. Save JSON Report
    report_json = {
        "model_name": metadata["model_name"],
        "num_test_samples": len(X_test),
        "metrics": {
            "accuracy": float(round(acc, 4)),
            "macro_precision": float(round(macro_p, 4)),
            "macro_recall": float(round(macro_r, 4)),
            "macro_f1": float(round(macro_f1, 4)),
            "weighted_f1": float(round(weight_f1, 4)),
            "log_loss": float(round(test_logloss, 4))
        },
        "best_performing_class": {"class": best_class[0], "f1_score": best_class[1]["f1_score"]},
        "worst_performing_class": {"class": worst_class[0], "f1_score": worst_class[1]["f1_score"]},
        "per_class_results": per_class_results,
        "feature_importance_rankings": feat_imp_df.to_dict(orient="records")
    }

    report_path = os.path.join(reports_dir, "classification_report.json")
    with open(report_path, "w") as f:
        json.dump(report_json, f, indent=4)
    print(f"[OK] Full classification report JSON saved to: {os.path.abspath(report_path)}")

    return report_json


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate traffic classifier model.")
    parser.add_argument("--processed-data", type=str, default="data/processed/processed_data.npz", help="Processed NPZ path")
    parser.add_argument("--models-dir", type=str, default="models", help="Models dir")
    parser.add_argument("--reports-dir", type=str, default="reports", help="Reports dir")
    args = parser.parse_args()

    evaluate_pipeline(
        processed_data_path=args.processed_data,
        models_dir=args.models_dir,
        reports_dir=args.reports_dir
    )
