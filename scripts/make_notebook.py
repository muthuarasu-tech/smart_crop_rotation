# ============================================================
# scripts/make_notebook.py
# SMART CROP ROTATION - generates notebooks/model_analysis.ipynb
# Usage: python scripts/make_notebook.py
# ============================================================

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "notebooks", "model_analysis.ipynb")


def code(src):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in src.splitlines()],
    }


def md(src):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in src.splitlines()],
    }


cells = [
    md(
        "# SMART CROP ROTATION - Model Analysis\n"
        "\n"
        "BCA Final-Year Project: *AI-Based Intelligent Crop Rotation Recommendation System*.\n"
        "\n"
        "This notebook loads the demo dataset, explores it, and compares the four classifiers.\n"
        "> Note: metrics describe learning on the **synthetic demo data only** - not real farms."
    ),
    code(
        "import pandas as pd\n"
        "df = pd.read_csv('../data/crop_dataset.csv')\n"
        "print('Shape:', df.shape)\n"
        "df.head()"
    ),
    code(
        "df['recommended_crop'].value_counts().plot(kind='bar', figsize=(10, 4), color='#2E7D32')\n"
        "plt.title('Records per crop')\n"
        "plt.xticks(rotation=45)\n"
        "plt.show()"
    ).update({"metadata": {"tags": []}}) or cells[-1] if False else None,
]

# Rebuild explicitly to avoid cleverness above
cells = [
    md(
        "# SMART CROP ROTATION - Model Analysis\n"
        "\n"
        "BCA Final-Year Project: *AI-Based Intelligent Crop Rotation Recommendation System*.\n"
        "\n"
        "This notebook loads the demo dataset, explores it, and compares the four classifiers.\n"
        "> Note: metrics describe learning on the **synthetic demo data only** - not real farms."
    ),
    code(
        "import pandas as pd\n"
        "df = pd.read_csv('../data/crop_dataset.csv')\n"
        "print('Shape:', df.shape)\n"
        "df.head()"
    ),
    code(
        "import matplotlib.pyplot as plt\n"
        "df['recommended_crop'].value_counts().plot(kind='bar', figsize=(10, 4), color='#2E7D32')\n"
        "plt.title('Records per crop')\n"
        "plt.xticks(rotation=45)\n"
        "plt.show()"
    ),
    code(
        "df[['N', 'P', 'K', 'ph', 'temperature', 'humidity', 'rainfall']].hist(bins=20, figsize=(12, 8))\n"
        "plt.tight_layout()\n"
        "plt.show()"
    ),
    code(
        "from sklearn.compose import ColumnTransformer\n"
        "from sklearn.preprocessing import OneHotEncoder, StandardScaler\n"
        "from sklearn.pipeline import Pipeline\n"
        "from sklearn.model_selection import train_test_split\n"
        "from sklearn.tree import DecisionTreeClassifier\n"
        "from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier\n"
        "from sklearn.neighbors import KNeighborsClassifier\n"
        "from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score\n"
        "\n"
        "cat = ['soil_type', 'previous_crop', 'season', 'water_availability', 'irrigation',\n"
        "       'region', 'disease_level', 'fertilizer_usage']\n"
        "num = ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall', 'previous_yield']\n"
        "feats = num + cat\n"
        "X = df[feats]; y = df['recommended_crop']\n"
        "Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)\n"
        "pre = ColumnTransformer([\n"
        "    ('num', StandardScaler(), num),\n"
        "    ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat)])\n"
        "print('Train:', len(Xtr), 'Test:', len(Xte))"
    ),
    code(
        "models = {\n"
        "    'Decision Tree': DecisionTreeClassifier(max_depth=8, class_weight='balanced', random_state=42),\n"
        "    'Random Forest': RandomForestClassifier(n_estimators=200, class_weight='balanced', n_jobs=-1, random_state=42),\n"
        "    'Gradient Boosting': GradientBoostingClassifier(n_estimators=150, max_depth=4, random_state=42),\n"
        "    'KNN': KNeighborsClassifier(n_neighbors=5),\n"
        "}\n"
        "results = {}\n"
        "for name, clf in models.items():\n"
        "    pipe = Pipeline([('pre', pre), ('clf', clf)])\n"
        "    pipe.fit(Xtr, ytr)\n"
        "    p = pipe.predict(Xte)\n"
        "    results[name] = {\n"
        "        'accuracy': accuracy_score(yte, p),\n"
        "        'precision': precision_score(yte, p, average='macro', zero_division=0),\n"
        "        'recall': recall_score(yte, p, average='macro', zero_division=0),\n"
        "        'f1': f1_score(yte, p, average='macro', zero_division=0),\n"
        "    }\n"
        "pd.DataFrame(results).T.round(3)"
    ),
    code(
        "pd.DataFrame(results).T.plot(kind='bar', figsize=(10, 5), colormap='Greens')\n"
        "plt.title('Model comparison (demo dataset)')\n"
        "plt.ylabel('score')\n"
        "plt.xticks(rotation=0)\n"
        "plt.ylim(0, 1)\n"
        "plt.legend(loc='lower right')\n"
        "plt.show()"
    ),
    md(
        "**Conclusion:** Random Forest gives the best balance of Precision / Recall / F1 on this\n"
        "demo dataset, so `train_model.py` selects and saves it automatically with Joblib.\n"
        "\n"
        "**Disclaimer:** the dataset is synthetic; these numbers are *not* claims about real\n"
        "agricultural performance."
    ),
]

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(nb, fh, indent=1)
print("[OK] Notebook written to", OUT)