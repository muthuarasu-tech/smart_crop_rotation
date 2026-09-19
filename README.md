# SMART CROP ROTATION

### AI-Based Intelligent Crop Rotation Recommendation System

Smart Crop Rotation is a decision-support platform that helps farmers decide **which crop to
plant next season** by combining Machine Learning, agriculture/rotation rules, soil-nutrient
analysis, and environmental conditions — with explainable, human-readable recommendations.

---

## ⚡ Quick Start (Windows, easiest)

**Double-click `RUNME.bat`** in the project folder. It will, on first run only:

1. Create a Python virtual environment (`venv`)
2. Install dependencies from `requirements.txt`
3. Train the model (`train_model.py`) if `models\crop_model.pkl` is missing
4. Launch the app and open your browser at **http://127.0.0.1:5000**

First registered user becomes the **host**; everyone else needs a normal account to log in.

Manual equivalent (same four steps):

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python train_model.py
python app.py
```

---

## 1. Features

| Feature | Description |
|---|---|
| Crop Recommendation | Top crop + 3 alternatives with Suitability %, Rotation, Soil and Season scores |
| Machine Learning | Decision Tree, Random Forest, Gradient Boosting, KNN (best model auto-selected) |
| Crop Rotation Engine | Rule-based: crop families, nitrogen fixation, disease break, water, season |
| Soil Health Score | 0-100 with breakdown (N, P, K, pH, fertiliser, previous crop) |
| Sustainability Score | 0-100 with water, fertiliser, diversity, soil, disease factors |
| Explainable AI | "Why this crop?" checklist for every recommendation |
| Nitrogen Management | Automatic nitrogen advice based on soil N level |
| Rotation Timeline | Visual multi-season rotation plan |
| History | SQLite storage with view / delete / clear |
| Analytics | Chart.js charts: NPK, model comparison, score trends, crop-family mix |
| Model Page | Accuracy / Precision / Recall / F1 comparison + confusion matrix |
| Report | Printable recommendation report (browser print / save as PDF) |
| REST API | `POST /api/recommend` JSON endpoint |
| Login System | Simple register / login / logout with hashed passwords (Werkzeug) |

> **Important:** Scores and recommendations are decision-support suggestions generated from
> the bundled training dataset. They are NOT guarantees of agricultural results. Always
> validate with local agronomic experts.

---

## 2. Project Structure

```
smart_crop_rotation/
├── app.py                        # Flask web application (all routes)
├── train_model.py                # ML training + evaluation + model saving
├── crop_rotation.py              # Crop knowledge base + rotation engine + scoring
├── soil_analysis.py              # Soil health + sustainability scores
├── requirements.txt
├── README.md
│
├── data/
│   └── crop_dataset.csv          # ~700 synthetic records (17 crops)
├── scripts/
│   └── generate_dataset.py       # Creates the synthetic dataset
├── models/
│   ├── crop_model.pkl            # Saved best pipeline (joblib)
│   └── model_metrics.json        # Metrics + confusion matrix
├── database/
│   └── crop_rotation.db          # SQLite database
├── templates/                    # HTML pages (Jinja2)
├── static/
│   ├── css/style.css
│   ├── js/script.js
│   └── images/
├── notebooks/
│   └── model_analysis.ipynb      # Exploration notebook
├── tests/
│   └── test_app.py               # Automated end-to-end tests
└── docs/
    ├── project_report.md         # Full 30-section BCA documentation
    ├── viva_questions.md         # 30+ viva Q&A
    ├── slides.md                 # 20-slide presentation content
    └── generate_presentation.py  # Optional PPTX generator (python-pptx)
```

---

## 3. Installation (Windows 11)

Requirements: **Python 3.11 or newer** (tested with 3.11-3.14), Visual Studio Code, internet
for the first install (packages + Chart.js CDN for charts).

```powershell
# 1. Open a terminal inside the project folder
cd smart_crop_rotation

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional but recommended) generate a fresh dataset
python scripts\generate_dataset.py

# 5. Train the machine learning models
python train_model.py

# 6. Start the Flask application
python app.py
```

Open your browser and go to: **http://127.0.0.1:5000**

> First screen = Home dashboard. Use **Start Recommendation** to run the recommendation form.
>
> The Home/Recommend/Analytics pages need internet access only for the Chart.js CDN.
> The app logic itself is fully local.

To stop the server: press `Ctrl + C` in the terminal.

---

## 4. Run with a one-line script

```powershell
venv\Scripts\activate
python scripts\generate_dataset.py; python train_model.py; python app.py
```

---

## 5. Running the tests

```powershell
venv\Scripts\activate
python tests\test_app.py            # 48 integration checks (isolated temp database)
python scripts\smoke_server.py      # boots the real server on :5000 and checks it
```

Expected output: `RESULT: 48 passed, 0 failed` and `Server smoke test: OK`.

---

## 6. REST API

```powershell
# Health check
curl http://127.0.0.1:5000/api/health

# Recommendation
curl -X POST http://127.0.0.1:5000/api/recommend ^
  -H "Content-Type: application/json" ^
  -d "{\"previous_crop\":\"Rice\",\"soil_type\":\"Loamy\",\"ph\":6.5,\"nitrogen\":50,\"phosphorus\":40,\"potassium\":40,\"rainfall\":800,\"temperature\":28,\"humidity\":70,\"season\":\"Kharif\",\"target_season\":\"Rabi\",\"water_availability\":\"Medium\",\"irrigation\":\"Drip\",\"region\":\"South India\",\"previous_yield\":3.5,\"disease_level\":\"Low\",\"fertilizer_usage\":\"Medium\"}"
```

Response:

```json
{
  "recommended_crop": "Green Gram",
  "alternatives": [ ... 3 objects ... ],
  "rotation_score": 88,
  "rotation_label": "Excellent",
  "soil_health_score": 85,
  "soil_health_status": "Good",
  "sustainability_score": 82,
  "sustainability_label": "High Sustainability",
  "reasons": [ "...", "..." ],
  "nitrogen_suggestion": "...",
  "model": "Random Forest"
}
```

---

## 7. Machine Learning details

- **Dataset:** ~700 synthetic records, 17 crops, 16 input features (created with realistic
  agronomic relationships, not random noise).
- **Preprocessing:** one-hot encoding (categorical) + standard scaling (numeric) inside a
  `ColumnTransformer` / `Pipeline`.
- **Split:** 80% train / 20% test (stratified).
- **Algorithms:** Decision Tree, Random Forest, Gradient Boosting, KNN.
- **Metrics:** Accuracy, Precision (macro), Recall (macro), F1 (macro), Confusion Matrix.
- **Selection:** the best F1 model is saved as `models/crop_model.pkl` (joblib).

The final production ranking combines **45% ML prediction + 40% rotation rules + 15%
environment matching**.

---

## 8. Sample fields

- Previous Crop (17 crops across Cereals / Pulses / Oilseeds / Vegetables / Commercial)
- Season & Target Season (Kharif / Rabi / Zaid)
- Soil Type, Soil pH, N, P, K
- Rainfall, Temperature, Humidity
- Water Availability (Low/Medium/High), Irrigation, Region
- Previous Yield, Disease Level, Fertiliser Usage

---

## 9. Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside the activated venv |
| Model page is empty | Run `python train_model.py` first |
| `data/crop_dataset.csv` missing | Run `python scripts\generate_dataset.py` |
| Charts do not appear | Either the CDN is blocked, or no history/model data exists yet — numbers are still shown in tables |
| Port 5000 already in use | In `app.py`, add `app.run(debug=True, port=8000)` |

---

## 10. BCA assessment notes

- Fully original implementation (no copied project).
- Lightweight: pure Python standard library + Flask + Scikit-learn.
- All data is **synthetic/demo** and clearly labelled as such.
- Comprehensive docs: `docs/project_report.md`, `docs/viva_questions.md`, `docs/slides.md`.
- Presentation generator: `docs/generate_presentation.py` (needs `pip install python-pptx`).