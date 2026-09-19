# SMART CROP ROTATION

## Project Report — BCA Final-Year Academic Project

**Title:** Smart Crop Rotation — AI-Based Intelligent Crop Rotation Recommendation System

---

## 1. Abstract

Crop rotation is one of the oldest and most effective sustainable farming practices. Choosing
the right crop for the next season improves soil fertility, breaks pest and disease cycles,
and reduces fertiliser dependence. This project develops a web-based **Smart Crop Rotation
Recommendation System** that tells a farmer which crop to plant in the next season using a
combination of Machine Learning, agricultural rules, soil-nutrient analysis and environmental
conditions. The system recommends one top crop plus three alternatives, and explains every
recommendation with Soil Health, Rotation and Sustainability scores. Recommendations are
explicitly decision-support suggestions, not guaranteed outcomes.

## 2. Introduction

Modern decision-making in agriculture increasingly uses data. Soil test reports, weather,
previous crops and fertiliser records can all guide the next planting decision. However, most
tools give a single crop name without explaining *why*. This project combines:

1. a trained Machine Learning model that predicts likely crops from farm inputs,
2. a rule-based crop rotation engine that encodes agricultural knowledge,
3. a soil health model and a sustainability scoring model,

so that each final recommendation is explained, ranked and stored for future reference.

## 3. Problem Statement

Farmers often repeat the same crop season after season (monocropping). This degrades soil
nutrients, increases pest/disease carryover, and lowers yields. Electronically recommending the
"single best" crop is not enough — the recommendation must respect crop families, soil
balance, water availability and season.

## 4. Existing System

- Farmers rely on experience, habit and local advice.
- Government extension services publish general crop calendars.
- Simple yield-prediction apps recommend crops from only 2-3 inputs (NPK, temperature).
- Most tools do not consider the **previous crop**, crop families, disease history or
  fertiliser use, and none explain the reason.

## 5. Disadvantages of Existing System

- Monocropping continues because rotation awareness is low.
- Minimal input support (no previous crop, disease, irrigation or fertiliser factors).
- No explanation of recommendations.
- No history or analytics; hard to compare options.
- No sustainability or soil-health balance.

## 6. Proposed System

The proposed system is a lightweight web application with:

- A rich input form (17+ farm parameters).
- A machine-learning pipeline (4 classifiers, best selected automatically).
- A rule-based crop rotation engine with a crop-family knowledge base.
- Soil Health, Rotation and Sustainability scores (0-100) with breakdowns.
- "Why this crop?" explainable output, a rotation timeline, history, analytics,
  a model-performance page, a printable report and a REST API.

## 7. Advantages

- Considers rotation, soil, water, season and environment together.
- Explains every recommendation (Explainable AI).
- Trains and selects the best model automatically.
- Lightweight and runs locally on any laptop (8 GB RAM is more than enough).
- Stores history and shows charts.
- Academic transparency: all demo data is clearly labelled as synthetic.

## 8. Objectives

1. Build a synthetic but realistic agricultural dataset (>=500 records).
2. Train and compare Decision Tree, Random Forest, Gradient Boosting and KNN.
3. Select and persist the best model with Joblib.
4. Implement a rule-based rotation engine (crop families, nitrogen, disease, water).
5. Provide top-crop + 3 alternatives with all major scores.
6. Provide explainable reasons and a nitrogen-management suggestion.
7. Store recommendations in SQLite and visualise them with Chart.js.
8. Provide optional login and a REST API.

## 9. Scope

- In-scope: web recommendation, ML, rotation engine, scoring, history, analytics,
  reports, API, authentication.
- Out-of-scope: real-time weather APIs, satellite imagery, IoT sensors, financial
  optimisation, mobile apps, guaranteed yield predictions.

## 10. System Requirements

A web application with a Python/Flask backend and a browser frontend, requiring only Python,
the libraries in `requirements.txt`, and internet for the Chart.js CDN.

## 11. Hardware Requirements

- Windows 11 (or any OS), 8 GB RAM or less is sufficient.
- Processor: any modern x86-64 CPU.
- Storage: ~200 MB free (dependencies + data).
- No GPU needed.

## 12. Software Requirements

- Windows 11, Python 3.11+ , pip, Visual Studio Code, any modern browser
  (Chrome/Edge/Firefox).
- Python packages: Flask, Pandas, NumPy, Scikit-learn, Joblib, Matplotlib, Werkzeug.

## 13. Functional Requirements

- FR1: Register, login and logout.
- FR2: Enter farm inputs and validate them.
- FR3: Generate recommendation (top + 3 alternatives) with scores.
- FR4: Show soil health, rotation and sustainability breakdowns.
- FR5: Show "Why this crop?" reasons and nitrogen advice.
- FR6: Build a multi-season rotation timeline.
- FR7: Save and manage recommendation history (view/delete/clear).
- FR8: Display analytics charts and model performance.
- FR9: Generate a printable report.
- FR10: Expose `POST /api/recommend`.

## 14. Non-Functional Requirements

- NFR1 Usability: simple, agriculture-themed, responsive UI.
- NFR2 Performance: page responses < 2 seconds on a laptop.
- NFR3 Reliability: friendly errors if model/dataset/database missing.
- NFR4 Security: hashed passwords (Werkzeug), no plain-text storage.
- NFR5 Portability: runs on Windows/Linux/macOS with Python 3.11+.
- NFR6 Documentation: report, viva questions, slides provided.

## 15. System Architecture

```
Browser (HTML/CSS/JS + Chart.js)
        │  HTTP requests
        ▼
Flask application (app.py)
   │           │            │
   ▼           ▼            ▼
crop_rotation.py   soil_analysis.py   SQLite database
(rotation engine)  (scores)           (users, history,
   ▲                                   recommendations,
   │ ML probabilities                  model_results)
   ▼
Models: crop_model.pkl (joblib) <- trained by train_model.py
                                      ▲
                                      │
                       data/crop_dataset.csv (scripts/generate_dataset.py)
```

## 16. Data Flow Diagram

```
Farm inputs (form/API) --> Validate --> build env dict
                                          │
            ┌─────────────────────────────┼─────────────────────────┐
            ▼                             ▼                         ▼
    ML pipeline predict_proba      Rotation engine           Soil analysis
    (prob per crop)                (rotation score,          (soil health &
                                    env score, reasons)       sustainability)
            └─────────────────────────────┼─────────────────────────┘
                                          ▼
                  Final rank = 45% ML + 40% rotation + 15% env
                                          ▼
                Top crop + 3 alternatives with scores & reasons
                                          ▼
                         Store to SQLite --> History / Analytics / Report
```

## 17. Use Case Diagram (textual)

- **Actors:** Farmer/User, Admin/Demonstrator.
- **User cases:** Register, Login, Enter farm inputs, Get recommendation, View alternatives,
  View scores, View timeline, Save to history, Delete/clear history, View analytics,
  View model performance, Generate report, Call REST API.
- **Admin cases:** Train models, view metrics.

## 18. ER Diagram (textual)

```
users(id PK, username UNIQUE, password_hash, created_at)
1 ──── 0..N  crop_history(id PK, user_id FK optional, created_at, previous_crop,
                       recommended_crop, soil_type, ph, n, p, k, rainfall,
                       temperature, humidity, season, rotation_score,
                       soil_health, sustainability, model_name)
1 ──── 1  recommendations(id PK, history_id FK, created_at, top_crop,
                          inputs_json, recommendations_json)
model_results(id PK, model_name, accuracy, precision, recall, f1,
              is_best, trained_at)
```

## 19. Database Design

Tables created by `app.py` / `train_model.py`:

- `users` — username, password hash, created_at.
- `crop_history` — one row per recommendation (summary).
- `recommendations` — full input snapshot + alternatives stored as JSON, linked to history.
- `model_results` — performance of every trained model.

SQLite (`database/crop_rotation.db`) is used because it is embedded, file-based,
zero-configuration and part of the Python standard library.

## 20. Module Description

| Module | File | Purpose |
|---|---|---|
| Data generation | `scripts/generate_dataset.py` | Creates the synthetic dataset |
| Knowledge base | `crop_rotation.py` | Crop facts (family, season, pH, NPK, water) |
| Rotation engine | `crop_rotation.py` | Rotation score, env score, reasons, timeline |
| Soil analysis | `soil_analysis.py` | Soil health & sustainability scoring |
| Model training | `train_model.py` | Trains/evaluates 4 models, saves best |
| Web application | `app.py` | Routes, validation, auth, API, DB |
| Templates | `templates/` | HTML pages (Jinja2) |
| Assets | `static/` | CSS + JavaScript |
| Tests | `tests/test_app.py` | 48 automated checks |

## 21. Algorithm

**Overall recommendation scoring:**

```
For every crop C (except previous crop):
    ml_prob[C]  = ML pipeline probability(C)
    rot[C]      = rotation_score(C)      (0-100)
    env[C]      = env_compatibility(C)   (0-100)
    score[C]    = 0.45*ml_prob[C]*100 + 0.40*rot[C] + 0.15*env[C] + curated_bonus

Sort by score descending -> top crop + next 3 = alternatives.
```

**Rotation score (0-100):** family diversity 25 + soil compatibility 25 + water 20 +
disease break 15 + season 15.

**Soil health score (0-100):** N (20) + P (20) + K (20) + pH (10) + fertiliser management
(10) + previous-crop effect (20).

**Sustainability score (0-100):** water efficiency 25 + fertiliser efficiency 25 +
crop diversity 20 + soil health (20% of soil score) + disease risk 10.

## 22. Machine Learning Methodology

1. **Data generation** — realistic synthetic records; labels drawn from each crop's
   agronomic bands; rotation respected (different family most of the time).
2. **Preprocessing** — one-hot encoding for categorical inputs; standard scaling for numeric;
   `ColumnTransformer` + `Pipeline`.
3. **Split** — 80/20 stratified train/test.
4. **Models** — Decision Tree, Random Forest, Gradient Boosting, KNN.
5. **Evaluation** — Accuracy, macro Precision, macro Recall, macro F1, Confusion Matrix.
6. **Selection and persistence** — best F1 model saved via `joblib` to
   `models/crop_model.pkl`; metrics + confusion matrix to `models/model_metrics.json`
   and the `model_results` table.
7. **Runtime use** — `predict_proba` gives a probability per crop which feeds the final
   ranking formula.

Observed demo result (700 synthetic rows): Random Forest ~70.5% F1, Decision Tree ~57.8%,
Gradient Boosting ~60.4%, KNN ~51.3%. **These numbers describe learning on the demo dataset
only, not real farm performance.**

## 23. Crop Rotation Logic

- After a **cereal** (Rice, Maize, Wheat, Sorghum), prefer **pulses/oilseeds** (e.g., Green
  Gram, Black Gram, Groundnut) to add nitrogen.
- After a **legume/pulse**, plant a **cereal** or oilseed to use the fixed nitrogen.
- Never recommend the same crop; strongly penalise the same **family** (disease carryover).
- Legumes boost suitability when soil nitrogen is low (biological nitrogen fixation).
- Water-demanding crops suit high water availability; drought-tolerant crops suit low water.
- Each crop has a seasonal window (Kharif/Rabi/Zaid); season mismatch reduces score.
- Disease history scales the family-diversity penalty.

## 24. Implementation

The application is implemented in Python/Flask with Jinja2 templates, a custom CSS theme,
Chart.js charts, SQLite storage and a Joblib-persisted Scikit-learn pipeline. Validation
happens twice (client JavaScript + server Python) for robustness, and the app degrades
gracefully when the model/dataset/database is missing.

## 25. Testing

- **Unit/sanity:** engine score functions checked with known inputs.
- **Integration:** Flask test client exercises every route.
- **Validation tests:** invalid pH, humidity, empty fields and non-JSON API bodies.
- **Auth tests:** registration, duplicate username, wrong password, login/logout, password
  hashing.
- **Persistence tests:** history save, report, delete, clear.
- **Result:** `48 passed, 0 failed` (`python tests/test_app.py`).

## 26. Results

- The full pipeline runs: dataset generation -> training -> web app.
- The recommendation output includes a ranked crop + 3 alternatives with Suitability,
  Rotation, Soil Compatibility, Water and Season indicators.
- Scores (Soil Health, Rotation, Sustainability) render with per-factor breakdowns and charts.
- History, analytics, model comparison, report and API all verified by automated tests.

## 27. Limitations

- The dataset is synthetic; real soil/weather data would change model behaviour.
- Scores are heuristic and educational, not certified agronomic advice.
- No real-time weather or satellite integration.
- Charts require an internet connection (Chart.js CDN).
- Long-duration crops and intercropping/mixed cropping are simplified.

## 28. Future Enhancement

- Connect to live weather APIs and real soil-test datasets.
- Add deep-learning or ensemble stacking for better accuracy.
- Include economic/market-price optimisation per crop.
- Add multi-language support and a mobile app / Progressive Web App.
- Let farmers upload soil-test PDFs for automatic parsing.
- Add crop-disease image classification.

## 29. Conclusion

Smart Crop Rotation successfully demonstrates how a final-year BCA student can combine web
development, database design and machine learning to solve a meaningful real-world problem.
The system is lightweight, explainable and easy to demonstrate, and clearly separates data,
logic and presentation. All recommendations are framed honestly as decision-support inputs.

## 30. References

1. Flask documentation — https://flask.palletsprojects.com
2. Scikit-learn documentation — https://scikit-learn.org
3. Pandas documentation — https://pandas.pydata.org
4. Chart.js documentation — https://www.chartjs.org
5. Joblib — https://joblib.readthedocs.io
6. Kumar, et al. "Crop Yield Prediction using Machine Learning" (review papers).
7. Yadav, et al. "Crop Rotation System in India" (agronomy review).
8. ICAR / state agriculture department crop-calendar references (season windows).