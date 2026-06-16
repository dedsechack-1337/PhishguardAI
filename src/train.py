"""
Training pipeline for PhishGuard AI URL classification models.

Trains a Random Forest classifier on extracted URL features (always
available, no extra dependencies), and optionally also trains XGBoost
if it's installed (pip install -r requirements-dev.txt) for comparison.

Saves the best model plus a lightweight "explainer" artifact (feature
means/stds + global feature importances) used by predict.py to generate
per-prediction explanations WITHOUT depending on the heavy `shap` package
(which pulls in numba/llvmlite/scipy, ~340MB).
"""

import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report, roc_auc_score, confusion_matrix, accuracy_score
)

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

from feature_extraction import extract_features_batch

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "urls_dataset.csv")
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")


def load_and_featurize(path: str):
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} rows from {path}")

    X = extract_features_batch(df["url"].tolist())
    y = df["label"].values

    return X, y


def train_random_forest(X_train, y_train):
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


def train_xgboost(X_train, y_train):
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


def evaluate(model, X_test, y_test, name: str):
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, preds)
    auc = roc_auc_score(y_test, probs)

    print(f"\n=== {name} ===")
    print(f"Accuracy: {acc:.4f}")
    print(f"ROC-AUC : {auc:.4f}")
    print(classification_report(y_test, preds, target_names=["legit", "phishing"]))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, preds))

    return {"accuracy": acc, "auc": auc}


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)

    X, y = load_and_featurize(DATA_PATH)
    feature_names = X.columns.tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\nTrain size: {len(X_train)} | Test size: {len(X_test)}")
    print(f"Features ({len(feature_names)}): {feature_names}")

    # --- Train models ---
    rf_model = train_random_forest(X_train, y_train)
    rf_metrics = evaluate(rf_model, X_test, y_test, "Random Forest")

    best_model, best_name, best_metrics = rf_model, "random_forest", rf_metrics

    if XGBOOST_AVAILABLE:
        xgb_model = train_xgboost(X_train, y_train)
        xgb_metrics = evaluate(xgb_model, X_test, y_test, "XGBoost")

        if xgb_metrics["auc"] > rf_metrics["auc"]:
            best_model, best_name, best_metrics = xgb_model, "xgboost", xgb_metrics
    else:
        xgb_model = None
        print("\n(XGBoost not installed — skipping. "
              "Install requirements-dev.txt to enable it. "
              "Random Forest is used by default and performs well.)")

    print(f"\nBest model: {best_name} (AUC={best_metrics['auc']:.4f})")

    # --- Save models + metadata ---
    joblib.dump(rf_model, os.path.join(MODELS_DIR, "random_forest.joblib"))
    if xgb_model is not None:
        joblib.dump(xgb_model, os.path.join(MODELS_DIR, "xgboost.joblib"))
    joblib.dump(feature_names, os.path.join(MODELS_DIR, "feature_names.joblib"))

    with open(os.path.join(MODELS_DIR, "best_model.txt"), "w") as f:
        f.write(best_name)

    # --- Build lightweight explainer artifact ---
    # Stores per-feature mean/std (from training data) and the model's
    # global feature_importances_. At inference time, predict.py combines
    # these with the model's prediction to produce per-URL explanations:
    # a feature "matters" for this prediction if (a) the model considers
    # it globally important, AND (b) this URL's value for that feature is
    # unusually high/low relative to the training distribution.
    print("\nBuilding lightweight explainer artifact...")
    # Direction: sign of correlation between each feature and the phishing
    # label (1=phishing). Positive correlation -> higher feature value
    # pushes toward "phishing"; negative -> higher value pushes toward
    # "legitimate". Combined with feature_importances_ and per-sample
    # z-scores, this lets predict.py approximate "why" without SHAP.
    corr_with_label = X_train.apply(lambda col: col.corr(pd.Series(y_train, index=col.index)))
    corr_with_label = corr_with_label.fillna(0.0)

    explainer = {
        "feature_means": X_train.mean().to_dict(),
        "feature_stds": X_train.std().replace(0, 1).to_dict(),
        "feature_importances": dict(zip(feature_names, best_model.feature_importances_.tolist())),
        "feature_directions": {
            k: (1 if v >= 0 else -1) for k, v in corr_with_label.to_dict().items()
        },
    }
    joblib.dump(explainer, os.path.join(MODELS_DIR, "explainer.joblib"))

    print("\nAll models and artifacts saved to:", MODELS_DIR)


if __name__ == "__main__":
    main()
