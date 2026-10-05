"""
Evaluation and Visualization Module for Encrypted Traffic Classifier.
Evaluates trained XGBoost model on the untouched test set, generates
confusion matrix plots, gain-based feature importances, SHAP plots, and JSON report.
"""

import argparse
import json
import os

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
    precision_recall_fscore_support,
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


def top_label_calibration(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    bins: int = 10,
) -> dict:
    """Measure top-label calibration; this does not calibrate the model."""
    if probabilities.ndim != 2 or len(y_true) != probabilities.shape[0]:
        raise ValueError("Expected one probability row per label.")
    if bins < 1:
        raise ValueError("bins must be positive.")
    confidence = np.max(probabilities, axis=1)
    predicted = np.argmax(probabilities, axis=1)
    correct = (predicted == y_true).astype(float)
    calibration_bins = []
    ece = 0.0
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        mask = (confidence >= lower) & (
            confidence <= upper if index == bins - 1 else confidence < upper
        )
        count = int(np.sum(mask))
        accuracy = float(np.mean(correct[mask])) if count else None
        mean_confidence = float(np.mean(confidence[mask])) if count else None
        if count:
            ece += count / len(y_true) * abs(accuracy - mean_confidence)
        calibration_bins.append({
            "lower_confidence": lower,
            "upper_confidence": upper,
            "samples": count,
            "accuracy": accuracy,
            "mean_confidence": mean_confidence,
        })
    one_hot = np.eye(probabilities.shape[1])[y_true.astype(int)]
    brier_score = float(np.mean(np.sum((probabilities - one_hot) ** 2, axis=1)))
    return {
        "definition": "top-label expected calibration error with uniform confidence bins; descriptive only",
        "expected_calibration_error": float(ece),
        "multiclass_brier_score": brier_score,
        "bins": calibration_bins,
    }


def evaluate_feature_ablations(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    feature_columns: list[str],
    model_metadata: dict,
    reports_dir: str,
    baseline_metrics: dict | None = None,
) -> dict:
    """Train held-out feature-group ablations without replacing saved artifacts."""
    if not XGBOOST_INSTALLED:
        raise ModuleNotFoundError("XGBoost is required to run feature ablations.")
    from sklearn.utils.class_weight import compute_sample_weight

    groups = {
        "rate_volume": {
            "flowPktsPerSecond", "flowBytesPerSecond", "bytes_per_pkt",
            "log_bytes_sec", "log_pkts_sec",
        },
        "timing": {
            feature for feature in feature_columns
            if any(token in feature.lower() for token in ("duration", "fiat", "biat", "flowiat", "active", "idle"))
        },
    }
    assigned = set().union(*groups.values())
    groups["remaining"] = set(feature_columns) - assigned
    base_params = dict(model_metadata.get("xgboost_parameters", {}))
    base_params["verbosity"] = 0
    ablations = {}
    weights = compute_sample_weight("balanced", y_train)

    for group_name, excluded in groups.items():
        retained_indices = [index for index, name in enumerate(feature_columns) if name not in excluded]
        if not retained_indices:
            raise ValueError(f"Ablation '{group_name}' would remove every feature.")
        model = XGBClassifier(**base_params)
        model.fit(
            X_train[:, retained_indices],
            y_train,
            sample_weight=weights,
            eval_set=[(X_val[:, retained_indices], y_val)],
            verbose=False,
        )
        partial_probabilities = model.predict_proba(X_test[:, retained_indices])
        number_of_classes = len(model_metadata.get("classes", [])) or int(
            np.max(np.concatenate((y_train, y_val, y_test))) + 1
        )
        probabilities = np.zeros((len(y_test), number_of_classes), dtype=float)
        for local_index, class_id in enumerate(model.classes_):
            probabilities[:, int(class_id)] = partial_probabilities[:, local_index]
        predictions = np.argmax(probabilities, axis=1)
        precision, recall, f1, support = precision_recall_fscore_support(
            y_test, predictions, average=None,
            labels=np.arange(number_of_classes), zero_division=0,
        )
        macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
            y_test, predictions, labels=np.arange(number_of_classes),
            average="macro", zero_division=0,
        )
        ablations[group_name] = {
            "excluded_features": sorted(excluded),
            "retained_features": [feature_columns[index] for index in retained_indices],
            "test_samples": int(len(y_test)),
            "accuracy": float(accuracy_score(y_test, predictions)),
            "macro_precision": float(macro_precision),
            "macro_recall": float(macro_recall),
            "macro_f1": float(macro_f1),
            "log_loss": float(log_loss(
                y_test, probabilities, labels=np.arange(number_of_classes)
            )),
            "per_class": {
                str(index): {
                    "precision": float(precision[index]),
                    "recall": float(recall[index]),
                    "f1": float(f1[index]),
                    "support": int(support[index]),
                }
                for index in range(len(support))
            },
            "split_note": "One existing held-out split; this result is not a repeated-split confidence interval.",
        }
    report = {
        "study": "feature-group ablation",
        "base_model": model_metadata.get("model_name"),
        "test_split_method": model_metadata.get(
            "split_method", "capture grouping not recorded in the checked-in metadata"
        ),
        "full_model_test_metrics": baseline_metrics,
        "artifacts_replaced": False,
        "ablations": ablations,
    }
    os.makedirs(reports_dir, exist_ok=True)
    with open(os.path.join(reports_dir, "ablation_report.json"), "w", encoding="utf-8") as output_file:
        json.dump(report, output_file, indent=4)
    return report


def evaluate_pipeline(
    processed_data_path: str = "../data/processed/processed_data.npz",
    models_dir: str = "../models",
    reports_dir: str = "../reports",
    run_ablations: bool = False,
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

    print("\n==================================================")
    print(" Evaluating XGBoost Model on Untouched Test Set")
    print("==================================================")
    print(f"[+] Test dataset size: {X_test.shape[0]} samples")

    # Evaluate XGBoost Model
    xgb_model = XGBClassifier()
    xgb_model.load_model(model_path)
    y_proba_xgb = xgb_model.predict_proba(X_test)
    y_pred_xgb = np.argmax(y_proba_xgb, axis=1)

    acc_xgb = accuracy_score(y_test, y_pred_xgb)
    class_labels = np.arange(len(classes))
    macro_p_xgb, macro_r_xgb, macro_f1_xgb, _ = precision_recall_fscore_support(
        y_test, y_pred_xgb, labels=class_labels, average="macro", zero_division=0
    )
    weight_p_xgb, weight_r_xgb, weight_f1_xgb, _ = precision_recall_fscore_support(
        y_test, y_pred_xgb, labels=class_labels, average="weighted", zero_division=0
    )
    logloss_xgb = log_loss(y_test, y_proba_xgb, labels=class_labels)
    calibration = top_label_calibration(y_test, y_proba_xgb)

    # Evaluate Random Forest Model if available
    rf_model_path = os.path.join(models_dir, "random_forest_model.joblib")
    rf_metrics = None
    if os.path.exists(rf_model_path):
        rf_model = joblib.load(rf_model_path)
        y_proba_rf = rf_model.predict_proba(X_test)
        y_pred_rf = np.argmax(y_proba_rf, axis=1)

        acc_rf = accuracy_score(y_test, y_pred_rf)
        macro_p_rf, macro_r_rf, macro_f1_rf, _ = precision_recall_fscore_support(
            y_test, y_pred_rf, labels=class_labels, average="macro", zero_division=0
        )
        weight_p_rf, weight_r_rf, weight_f1_rf, _ = precision_recall_fscore_support(
            y_test, y_pred_rf, labels=class_labels, average="weighted", zero_division=0
        )
        logloss_rf = log_loss(y_test, y_proba_rf, labels=class_labels)

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

    print("\n--- Key Test Performance Metrics (XGBoost) ---")
    print(f"  Test Accuracy   : {acc*100:.2f}%")
    print(f"  Macro Precision : {macro_p*100:.2f}%")
    print(f"  Macro Recall    : {macro_r*100:.2f}%")
    print(f"  Macro F1 Score  : {macro_f1*100:.2f}%")
    print(f"  Weighted F1     : {weight_f1*100:.2f}%")
    print(f"  Multi Log Loss  : {test_logloss:.4f}")
    print(f"  Highest F1 Class: '{best_class[0]}' ({best_class[1]['f1_score']*100:.1f}%)")
    print(f"  Lowest F1 Class : '{worst_class[0]}' ({worst_class[1]['f1_score']*100:.1f}%)")

    if rf_metrics:
        print("\n--- Model Comparison on Untouched Test Set ---")
        print("  Metric              | XGBoost     | Random Forest")
        print("  --------------------+-------------+--------------")
        print(f"  Test Accuracy       | {acc*100:.2f}%       | {rf_metrics['accuracy']*100:.2f}%")
        print(f"  Macro Precision     | {macro_p*100:.2f}%       | {rf_metrics['macro_precision']*100:.2f}%")
        print(f"  Macro Recall        | {macro_r*100:.2f}%       | {rf_metrics['macro_recall']*100:.2f}%")
        print(f"  Macro F1 Score      | {macro_f1*100:.2f}%       | {rf_metrics['macro_f1']*100:.2f}%")
        print(f"  Weighted F1         | {weight_f1*100:.2f}%       | {rf_metrics['weighted_f1']*100:.2f}%")
        print(f"  Multi Log Loss      | {test_logloss:.4f}      | {rf_metrics['log_loss']:.4f}")

    # Console Classification Report
    print("\n--- Detailed Per-Class Breakdown ---")
    clf_rep_str = classification_report(
        y_test, y_pred, labels=class_labels, target_names=classes, digits=4, zero_division=0
    )
    print(clf_rep_str)

    os.makedirs(reports_dir, exist_ok=True)

    # 1. Confusion Matrix Plot
    cm = confusion_matrix(y_test, y_pred, labels=class_labels)
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
            print("[+] Calculating SHAP values for explainability...")
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
            "log_loss": float(round(test_logloss, 4)),
            "top_label_expected_calibration_error": calibration["expected_calibration_error"],
            "multiclass_brier_score": calibration["multiclass_brier_score"],
        },
        "calibration": calibration,
        "best_performing_class": {"class": best_class[0], "f1_score": best_class[1]["f1_score"]},
        "worst_performing_class": {"class": worst_class[0], "f1_score": worst_class[1]["f1_score"]},
        "per_class_results": per_class_results,
        "feature_importance_rankings": feat_imp_df.to_dict(orient="records")
    }

    report_path = os.path.join(reports_dir, "classification_report.json")
    with open(report_path, "w") as f:
        json.dump(report_json, f, indent=4)
    print(f"[OK] Full classification report JSON saved to: {os.path.abspath(report_path)}")

    model_card = {
        "model_name": metadata.get("model_name", "XGBoost Encrypted Traffic Classifier"),
        "model_type": "multiclass gradient-boosted decision trees",
        "target_column": metadata.get("target_column", "traffic_type"),
        "classes": classes,
        "features": feature_cols,
        "training_dataset": metadata.get("dataset", "consolidated_traffic_data.csv"),
        "dataset_version": metadata.get("dataset_version", "not recorded"),
        "source_row_count": metadata.get("source_row_count"),
        "source_group_count": metadata.get("source_group_count"),
        "row_counts": {
            "train": metadata.get("training_rows"),
            "validation": metadata.get("validation_rows"),
            "test": int(len(y_test)),
        },
        "capture_count": metadata.get("source_group_count"),
        "group_column": metadata.get("group_column"),
        "group_counts_by_split": metadata.get("group_counts"),
        "group_hashes_by_split": metadata.get("group_hashes_by_split"),
        "class_support_by_split": metadata.get("class_support_by_split"),
        "missing_classes_by_split": metadata.get("missing_classes_by_split"),
        "split_method": metadata.get(
            "split_method",
            "random row-level stratified split; capture/source grouping was not recorded",
        ),
        "training_parameters": metadata.get("xgboost_parameters", {}),
        "test_metrics": report_json["metrics"],
        "per_class_test_metrics": per_class_results,
        "calibration": calibration,
        "known_limitations": [
            (
                "Capture/source identifiers and capture count are unavailable; this row-level split does not establish generalization to independent captures or environments."
                if not metadata.get("group_column")
                else "Grouping prevents rows from the same recorded source capture crossing splits, but does not establish independence across hosts or environments."
            ),
            "Calibration metrics are measurements only; model probabilities have not been calibrated by this evaluation.",
            "No independently sourced external-capture evaluation is represented by this report.",
        ],
    }
    card_path = os.path.join(reports_dir, "model_card.json")
    with open(card_path, "w", encoding="utf-8") as card_file:
        json.dump(model_card, card_file, indent=4)
    print(f"[OK] Model card saved to: {os.path.abspath(card_path)}")
    if run_ablations:
        report_json["feature_ablations"] = evaluate_feature_ablations(
            data["X_train"],
            data["y_train"],
            data["X_val"],
            data["y_val"],
            X_test,
            y_test,
            feature_cols,
            metadata,
            reports_dir,
            report_json["metrics"],
        )

    return report_json


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate traffic classifier model.")
    parser.add_argument("--processed-data", type=str, default="data/processed/processed_data.npz", help="Processed NPZ path")
    parser.add_argument("--models-dir", type=str, default="models", help="Models dir")
    parser.add_argument("--reports-dir", type=str, default="reports", help="Reports dir")
    parser.add_argument("--ablation", action="store_true", help="Run held-out feature-group ablations")
    args = parser.parse_args()

    evaluate_pipeline(
        processed_data_path=args.processed_data,
        models_dir=args.models_dir,
        reports_dir=args.reports_dir,
        run_ablations=args.ablation,
    )
