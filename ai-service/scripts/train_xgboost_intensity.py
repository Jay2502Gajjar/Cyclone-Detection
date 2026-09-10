#!/usr/bin/env python3
"""
Reproducible XGBoost 24-Hour Cyclone Intensity Regression Training Pipeline.

Objective:
    Predict future maximum sustained surface wind speed in knots at horizon ~24h
    using the 14 strictly observable and derived features from IBTrACS.

Usage:
    python scripts/train_xgboost_intensity.py
"""

import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")  # Headless backend
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

# Set up paths
SCRIPT_DIR = Path(__file__).resolve().parent
AI_SERVICE_DIR = SCRIPT_DIR.parent
DATA_DIR = AI_SERVICE_DIR / "data" / "training"
ARTIFACTS_DIR = AI_SERVICE_DIR / "app" / "artifacts"
REPORTS_DIR = AI_SERVICE_DIR / "reports" / "figures"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def load_dataset() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any], Dict[str, Any]]:
    """Loads pre-generated, verified numpy dataset splits and schema."""
    logger.info("Loading dataset splits from %s", DATA_DIR)

    X_train = np.load(DATA_DIR / "X_train.npy")
    y_train = np.load(DATA_DIR / "y_train.npy")
    X_val = np.load(DATA_DIR / "X_val.npy")
    y_val = np.load(DATA_DIR / "y_val.npy")
    X_test = np.load(DATA_DIR / "X_test.npy")
    y_test = np.load(DATA_DIR / "y_test.npy")

    with open(DATA_DIR / "feature_schema.json", "r", encoding="utf-8") as f:
        schema = json.load(f)

    with open(DATA_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)

    return X_train, y_train, X_val, y_val, X_test, y_test, schema, manifest


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Calculates standard regression metrics."""
    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    rmse = float(np.sqrt(mse))
    r2 = float(r2_score(y_true, y_pred))
    bias = float(np.mean(y_pred - y_true))

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
        "mean_bias": round(bias, 4),
    }


def evaluate_intensity_regimes(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, Any]:
    """
    Evaluates model performance across operational tropical cyclone intensity regimes:
      1. < 34 kt (Depression / Deep Depression)
      2. 34-63 kt (Cyclonic Storm / Severe Cyclonic Storm)
      3. 64-95 kt (Very Severe Cyclonic Storm)
      4. > 95 kt (Extremely Severe / Super Cyclonic Storm)
    """
    bins = [
        ("< 34 kt (Depression)", y_true < 34.0),
        ("34-63 kt (Gale / Storm)", (y_true >= 34.0) & (y_true < 64.0)),
        ("64-95 kt (Hurricane / Very Severe)", (y_true >= 64.0) & (y_true <= 95.0)),
        ("> 95 kt (Extremely Severe / Super)", y_true > 95.0),
    ]

    regime_results = {}
    for label, mask in bins:
        count = int(np.sum(mask))
        if count == 0:
            regime_results[label] = {
                "sample_count": 0,
                "mae": None,
                "rmse": None,
                "bias": None,
                "comment": "No samples in this bin"
            }
            continue

        sub_true = y_true[mask]
        sub_pred = y_pred[mask]
        sub_metrics = calculate_metrics(sub_true, sub_pred)
        sub_metrics["sample_count"] = count
        sub_metrics["actual_mean"] = round(float(np.mean(sub_true)), 2)
        sub_metrics["predicted_mean"] = round(float(np.mean(sub_pred)), 2)
        if count < 30:
            sub_metrics["reliability"] = "Low sample count (<30); interpret with caution"
        else:
            sub_metrics["reliability"] = "Statistically sufficient"
        regime_results[label] = sub_metrics

    return regime_results


def evaluate_rapid_intensification(
    X: np.ndarray,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    wind_idx: int = 2
) -> Dict[str, Any]:
    """
    Evaluates whether the storm experienced rapid intensification (RI: >= 30 kt increase in 24h)
    and how the model performed on those cases.
    """
    current_wind = X[:, wind_idx]
    actual_change = y_true - current_wind
    predicted_change = y_pred - current_wind

    ri_mask = actual_change >= 30.0
    ri_count = int(np.sum(ri_mask))

    if ri_count == 0:
        return {"ri_sample_count": 0, "comment": "No RI events in this set"}

    ri_true = y_true[ri_mask]
    ri_pred = y_pred[ri_mask]
    ri_metrics = calculate_metrics(ri_true, ri_pred)
    ri_metrics["sample_count"] = ri_count
    ri_metrics["actual_mean_delta"] = round(float(np.mean(actual_change[ri_mask])), 2)
    ri_metrics["predicted_mean_delta"] = round(float(np.mean(predicted_change[ri_mask])), 2)
    ri_metrics["underprediction_bias"] = round(float(np.mean(ri_pred - ri_true)), 2)

    return ri_metrics


def generate_evaluation_plots(
    y_val_true: np.ndarray,
    y_val_pred: np.ndarray,
    y_test_true: np.ndarray,
    y_test_pred: np.ndarray,
    feature_names: List[str],
    feature_importances: Dict[str, float],
    output_dir: Path,
) -> None:
    """Generates evaluation figures: predicted vs actual, residuals, and feature importance."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Predicted vs Actual (Test set)
    plt.figure(figsize=(7, 6))
    plt.scatter(y_test_true, y_test_pred, alpha=0.35, color="#1e40af", edgecolors="none", s=25)
    lims = [0, max(max(y_test_true), max(y_test_pred)) + 10]
    plt.plot(lims, lims, color="#dc2626", linestyle="--", linewidth=1.5, label="Ideal 1:1 line")
    plt.xlabel("Actual 24h Wind Speed (knots)", fontsize=11)
    plt.ylabel("Predicted 24h Wind Speed (knots)", fontsize=11)
    plt.title("XGBoost Intensity v1: Predicted vs Actual (Test Set: Seasons >= 2019)", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(output_dir / "predicted_vs_actual.png", dpi=200)
    plt.close()

    # 2. Residual Distribution (Test set)
    residuals = y_test_pred - y_test_true
    plt.figure(figsize=(7, 5))
    plt.hist(residuals, bins=35, color="#2563eb", edgecolor="#1e293b", alpha=0.85)
    plt.axvline(0, color="#dc2626", linestyle="--", linewidth=1.5, label=f"Mean Error: {np.mean(residuals):.2f} kts")
    plt.xlabel("Residual (Predicted - Actual, knots)", fontsize=11)
    plt.ylabel("Sample Count", fontsize=11)
    plt.title("Residual Error Distribution (Test Set)", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "residuals_distribution.png", dpi=200)
    plt.close()

    # 3. Feature Importance Bar Chart
    sorted_features = sorted(feature_importances.items(), key=lambda x: x[1], reverse=True)
    f_names = [x[0] for x in sorted_features]
    f_vals = [x[1] for x in sorted_features]

    plt.figure(figsize=(9, 6))
    bars = plt.barh(range(len(f_names)), f_vals, color="#0284c7", edgecolor="#0f172a", alpha=0.85)
    plt.yticks(range(len(f_names)), f_names, fontsize=10)
    plt.gca().invert_yaxis()
    plt.xlabel("Feature Importance (Gain Metric)", fontsize=11)
    plt.title("XGBoost Feature Importance (Model Importance, Not Physical Causation)", fontsize=12)
    plt.grid(True, linestyle=":", alpha=0.6, axis="x")
    plt.tight_layout()
    plt.savefig(output_dir / "feature_importance.png", dpi=200)
    plt.close()

    logger.info("Saved evaluation plots to %s", output_dir)


def train_and_evaluate():
    """Executes the full XGBoost training, evaluation, and artifact saving pipeline."""
    X_train, y_train, X_val, y_val, X_test, y_test, schema, manifest = load_dataset()
    feature_names = [f["name"] for f in schema["features"]]

    # Phase 2: Defensible Baseline Configuration
    # Objective: reg:squarederror (standard regression), fixed random seed = 42
    config = {
        "n_estimators": 250,
        "max_depth": 5,
        "learning_rate": 0.04,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "min_child_weight": 4,
        "gamma": 0.5,
        "objective": "reg:squarederror",
        "random_state": 42,
        "n_jobs": -1,
        "early_stopping_rounds": 20,
    }

    logger.info("Initializing XGBRegressor with baseline configuration: %s", config)

    model = xgb.XGBRegressor(
        n_estimators=config["n_estimators"],
        max_depth=config["max_depth"],
        learning_rate=config["learning_rate"],
        subsample=config["subsample"],
        colsample_bytree=config["colsample_bytree"],
        min_child_weight=config["min_child_weight"],
        gamma=config["gamma"],
        objective=config["objective"],
        random_state=config["random_state"],
        n_jobs=config["n_jobs"],
        early_stopping_rounds=config["early_stopping_rounds"],
    )

    # Phase 3: Train using validation set for early stopping
    logger.info("Fitting model on X_train (%d samples)...", len(X_train))
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        verbose=25,
    )

    best_iteration = model.best_iteration
    logger.info("Training finished. Best iteration: %d", best_iteration)

    # Phase 4: Predict & Evaluate on Validation and Test sets
    y_train_pred = model.predict(X_train)
    y_val_pred = model.predict(X_val)
    y_test_pred = model.predict(X_test)

    train_metrics = calculate_metrics(y_train, y_train_pred)
    val_metrics = calculate_metrics(y_val, y_val_pred)
    test_metrics = calculate_metrics(y_test, y_test_pred)

    logger.info("=== EVALUATION METRICS ===")
    logger.info("Train: MAE=%.2f kts, RMSE=%.2f kts, R2=%.4f, Bias=%.2f kts",
                train_metrics["mae"], train_metrics["rmse"], train_metrics["r2"], train_metrics["mean_bias"])
    logger.info("Val:   MAE=%.2f kts, RMSE=%.2f kts, R2=%.4f, Bias=%.2f kts",
                val_metrics["mae"], val_metrics["rmse"], val_metrics["r2"], val_metrics["mean_bias"])
    logger.info("Test:  MAE=%.2f kts, RMSE=%.2f kts, R2=%.4f, Bias=%.2f kts",
                test_metrics["mae"], test_metrics["rmse"], test_metrics["r2"], test_metrics["mean_bias"])

    # Phase 5: Regime and RI Analysis
    test_regimes = evaluate_intensity_regimes(y_test, y_test_pred)
    test_ri = evaluate_rapid_intensification(X_test, y_test, y_test_pred, wind_idx=2)

    # Phase 6: Feature Importances
    importances_gain = model.get_booster().get_score(importance_type="gain")
    # Map feature indices (f0, f1...) to real feature names
    named_importances = {}
    for i, name in enumerate(feature_names):
        key = f"f{i}"
        named_importances[name] = round(float(importances_gain.get(key, 0.0)), 4)

    # Save Evaluation Plots
    generate_evaluation_plots(
        y_val_true=y_val,
        y_val_pred=y_val_pred,
        y_test_true=y_test,
        y_test_pred=y_test_pred,
        feature_names=feature_names,
        feature_importances=named_importances,
        output_dir=REPORTS_DIR,
    )

    # Phase 7: Save Model Artifact & Metadata
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    model_artifact_path = ARTIFACTS_DIR / "xgboost_intensity_v1.json"
    model.save_model(model_artifact_path)
    logger.info("Saved XGBoost model to %s", model_artifact_path)

    metadata = {
        "model_name": "XGBoost-Intensity-v1.0",
        "model_type": "xgboost.XGBRegressor",
        "target_description": "Future maximum sustained surface wind speed in knots at horizon ~24h",
        "target_horizon_hours": 24.0,
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "best_iteration": int(best_iteration),
        "hyperparameters": {
            "n_estimators": config["n_estimators"],
            "max_depth": config["max_depth"],
            "learning_rate": config["learning_rate"],
            "subsample": config["subsample"],
            "colsample_bytree": config["colsample_bytree"],
            "min_child_weight": config["min_child_weight"],
            "gamma": config["gamma"],
            "objective": config["objective"],
            "random_state": config["random_state"],
        },
        "dataset_split": {
            "train_seasons": manifest["split_seasons"]["train"],
            "val_seasons": manifest["split_seasons"]["validation"],
            "test_seasons": manifest["split_seasons"]["test"],
            "train_samples": len(X_train),
            "val_samples": len(X_val),
            "test_samples": len(X_test),
        },
        "metrics": {
            "train": train_metrics,
            "validation": val_metrics,
            "test": test_metrics,
        },
        "intensity_regimes_test": test_regimes,
        "rapid_intensification_test": test_ri,
        "feature_importance_gain": named_importances,
        "prediction_ranges": {
            "test_actual": {"min": float(y_test.min()), "max": float(y_test.max()), "mean": float(y_test.mean())},
            "test_predicted": {"min": float(y_test_pred.min()), "max": float(y_test_pred.max()), "mean": float(y_test_pred.mean())},
        },
        "scientific_notes": [
            "Model is an empirical statistical baseline trained strictly on real historical IBTrACS telemetry.",
            "Feature importance reflects gradient-split information gain within this tree ensemble, not physical causality.",
            "No synthetic data, environmental fabrication, or test-set leakage occurred during training or validation."
        ]
    }

    metadata_path = ARTIFACTS_DIR / "xgboost_intensity_v1_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Saved model metadata cleanly to %s", metadata_path)
    return metadata


if __name__ == "__main__":
    train_and_evaluate()
