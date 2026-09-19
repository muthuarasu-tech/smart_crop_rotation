# ============================================================
# train_model.py
# SMART CROP ROTATION - Model training & evaluation
# ------------------------------------------------------------
#  1. Loads data/crop_dataset.csv
#  2. Preprocesses (encoding + scaling)
#  3. Trains 4 classifiers: Decision Tree, Random Forest,
#     Gradient Boosting, K-Nearest Neighbours
#  4. Evaluates with Accuracy / Precision / Recall / F1
#  5. Saves the best pipeline to models/crop_model.pkl (joblib)
#  6. Stores all metrics in database/crop_rotation.db
#
# Usage:  python train_model.py
#
# NOTE: reported metrics describe learning on the bundled training
# dataset; accuracy on real farm data may differ.
# ============================================================

import json
import os
import sqlite3
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score, precision_score,
                             recall_score)
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_CSV = os.path.join(ROOT, "data", "crop_dataset.csv")
MODEL_PKL = os.path.join(ROOT, "models", "crop_model.pkl")
METRICS_JSON = os.path.join(ROOT, "models", "model_metrics.json")
DB_PATH = os.path.join(ROOT, "database", "crop_rotation.db")
RANDOM_STATE = 42

FEATURE_COLS = [
    "N", "P", "K",
    "temperature", "humidity", "ph", "rainfall", "previous_yield",
    "soil_type", "previous_crop", "season", "water_availability",
    "irrigation", "region", "disease_level", "fertilizer_usage",
]
CAT_COLS = ["soil_type", "previous_crop", "season", "water_availability",
            "irrigation", "region", "disease_level", "fertilizer_usage"]
NUM_COLS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall",
            "previous_yield"]
TARGET = "recommended_crop"


def ensure_db():
    """Create tables if the database does not exist yet."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS model_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            accuracy REAL NOT NULL,
            precision REAL NOT NULL,
            recall REAL NOT NULL,
            f1 REAL NOT NULL,
            is_best INTEGER DEFAULT 0,
            trained_at TEXT NOT NULL
        );
    """)
    conn.commit()
    return conn


def append_metrics(conn, name, accuracy, precision, recall, f1, is_best):
    conn.execute(
        "DELETE FROM model_results WHERE model_name = ?", (name,))
    conn.execute(
        """INSERT INTO model_results
           (model_name, accuracy, precision, recall, f1, is_best, trained_at)
           VALUES (?,?,?,?,?,?,?)""",
        (name, accuracy, precision, recall, f1, 1 if is_best else 0,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()


def main():
    print("[1/6] Loading dataset ...")
    if not os.path.exists(DATA_CSV):
        print("ERROR: dataset not found. Run:")
        print("       python scripts/generate_dataset.py")
        return
    df = pd.read_csv(DATA_CSV)
    print(f"       Loaded {len(df)} rows x {df.shape[1]} columns")

    # Basic sanity checks
    df = df.dropna(subset=FEATURE_COLS + [TARGET]).copy()
    df = df[df[TARGET].isin(
        (lambda xs: [f for f in xs if str(f) != 'nan'])(df[TARGET].dropna().unique()))]
    print(f"       Cleaned to {len(df)} usable rows")

    X = df[FEATURE_COLS].copy()
    y = df[TARGET].copy()

    print("[2/6] Splitting into 80% train / 20% test ...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y)
    print(f"       Train: {len(X_train)} rows, Test: {len(X_test)} rows")

    print("[3/6] Building preprocessing pipeline ...")
    preprocessor = ColumnTransformer(
        transformers=[(
            "num", StandardScaler(), NUM_COLS), (
            "cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CAT_COLS)])

    print("[4/6] Training 4 classifiers ...")
    models = {
        "Decision Tree": DecisionTreeClassifier(
            max_depth=8, min_samples_split=4, class_weight="balanced",
            random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, max_depth=None, min_samples_split=2,
            class_weight="balanced", n_jobs=-1, random_state=RANDOM_STATE),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=150, learning_rate=0.1, max_depth=4,
            random_state=RANDOM_STATE),
        "KNN": KNeighborsClassifier(n_neighbors=5),
    }

    all_metrics = {}
    best_name, best_f1, best_pipe = None, -1.0, None
    best_cm = None

    for name, clf in models.items():
        pipe = Pipeline(steps=[("pre", preprocessor), ("clf", clf)])
        pipe.fit(X_train, y_train)

        preds = pipe.predict(X_test)
        acc = accuracy_score(y_test, preds)
        prec = precision_score(y_test, preds, average="macro", zero_division=0)
        rec = recall_score(y_test, preds, average="macro", zero_division=0)
        f1 = f1_score(y_test, preds, average="macro", zero_division=0)

        all_metrics[name] = {
            "accuracy": round(float(acc) * 100, 2),
            "precision": round(float(prec) * 100, 2),
            "recall": round(float(rec) * 100, 2),
            "f1": round(float(f1) * 100, 2),
        }
        print(f"       {name:18s} acc={acc*100:.1f}%  "
              f"prec={prec*100:.1f}%  rec={rec*100:.1f}%  f1={f1*100:.1f}%")

        if f1 > best_f1:
            best_f1, best_name, best_pipe = f1, name, pipe
            best_cm = confusion_matrix(y_test, preds)

    print(f"[5/6] Best model: {best_name} (F1 = {best_f1*100:.1f}%)")

    # ---- save best pipeline bundle ----
    bundle = {
        "pipeline": best_pipe,
        "model_name": best_name,
        "classes": sorted(best_pipe.classes_.tolist()),
        "feature_columns": FEATURE_COLS,
        "cat_columns": CAT_COLS,
        "num_columns": NUM_COLS,
        "target_column": TARGET,
        "trained_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_rows": int(len(df)),
        "test_accuracy": all_metrics[best_name]["accuracy"],
    }
    os.makedirs(os.path.dirname(MODEL_PKL), exist_ok=True)
    joblib.dump(bundle, MODEL_PKL)
    print(f"       Saved -> {MODEL_PKL}")

    # ---- save metrics + confusion matrix ----
    os.makedirs(os.path.dirname(METRICS_JSON), exist_ok=True)
    with open(METRICS_JSON, "w", encoding="utf-8") as fh:
        json.dump({
            "trained_at": bundle["trained_at"],
            "dataset_rows": bundle["dataset_rows"],
            "best_model": best_name,
            "metrics": all_metrics,
            "confusion_matrix": {
                "labels": sorted(best_pipe.classes_.tolist()),
                "matrix": [[int(x) for x in row] for row in best_cm],
            },
            "notes": "Model performance metrics are computed on the "
                     "bundled training dataset; accuracy on real farm "
                     "data may differ.",
        }, fh, indent=2)
    print(f"       Saved -> {METRICS_JSON}")

    print("[6/6] Writing model performance into SQLite ...")
    conn = ensure_db()
    for name, m in all_metrics.items():
        append_metrics(conn, name, m["accuracy"] / 100.0,
                       m["precision"] / 100.0, m["recall"] / 100.0,
                       m["f1"] / 100.0, is_best=(name == best_name))
    conn.close()

    print("\n[OK] Training complete.")
    print("     Disclaimer: the dataset is synthetic. Accuracy values are")
    print("     NOT claims about real-world farm performance.")


if __name__ == "__main__":
    main()