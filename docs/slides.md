# SMART CROP ROTATION — Presentation Content (20 Slides)

Use these points for the PowerPoint. Alternatively run
`docs/generate_presentation.py` (needs `pip install python-pptx`) to generate
`docs/smart_crop_rotation_presentation.pptx` automatically.

---

**Slide 1 — Title**
- SMART CROP ROTATION
- AI-Based Intelligent Crop Rotation Recommendation System
- BCA Final-Year Project
- Your Name | College | Year

**Slide 2 — Introduction**
- Farmers need to decide "what to grow next season?"
- Decision depends on soil, season, water, weather and previous crop.
- This project recommends the best next crop using ML + agriculture rules.

**Slide 3 — Problem Statement**
- Repeating the same crop degrades soil and increases diseases.
- Existing tools recommend one crop without explanation.
- They ignore the previous crop, crop families, disease and fertiliser history.

**Slide 4 — Existing System**
- Experience-based decisions and generic crop calendars.
- Simple apps using only 2-3 inputs.
- No explanation, no history, no rotation logic.

**Slide 5 — Proposed System**
- Web app with 17 farm inputs.
- ML + rule-based rotation engine combined.
- Top crop + 3 alternatives, all explained.

**Slide 6 — Objectives**
- Train and compare 4 ML models.
- Build a crop rotation engine.
- Compute Soil Health, Rotation, Sustainability scores.
- Explainable recommendations, history, analytics, report.

**Slide 7 — Technologies Used**
- Frontend: HTML, CSS, JavaScript, Chart.js
- Backend: Python, Flask
- Data: Pandas, NumPy
- ML: Scikit-learn (Joblib for model saving)
- Database: SQLite

**Slide 8 — System Architecture**
- Browser -> Flask -> (rotation engine, soil analysis, SQLite, ML model)

**Slide 9 — Modules**
- Data generation, ML training, Rotation engine, Soil analysis, Web app,
  History, Analytics, Reports, API.

**Slide 10 — Dataset**
- ~700 synthetic records, 17 crops, 16 features.
- Generated with realistic agronomic relationships, not random noise.

**Slide 11 — Machine Learning**
- Decision Tree, Random Forest, Gradient Boosting, KNN.
- 80/20 train-test split; metrics: Accuracy, Precision, Recall, F1.
- Best model auto-selected (Random Forest) and saved with Joblib.

**Slide 12 — Crop Rotation Algorithm**
- Final score = 45% ML + 40% rotation rules + 15% environment.
- Rotation score = family 25 + soil 25 + water 20 + disease 15 + season 15.

**Slide 13 — Soil Health Analysis**
- Soil Health Score 0-100 from N, P, K, pH, fertiliser, previous crop.
- Sustainability Score 0-100 from water, fertiliser, diversity, soil, disease.

**Slide 14 — UI Screenshots**
- Home dashboard, recommendation form, result page, history, analytics.

**Slide 15 — Recommendation Result**
- Example: Previous Crop = Rice -> Recommended = Green Gram
- Plus 3 alternatives with scores and "Why this crop?" reasons.

**Slide 16 — Model Performance**
- Table + chart comparing the 4 models; confusion matrix.
- Labelled as trained on synthetic demo data.

**Slide 17 — Advantages**
- Explainable, lightweight, easy to demo.
- Combines ML, rules and soil analysis.
- History, analytics and REST API included.

**Slide 18 — Future Enhancement**
- Live weather/soil APIs, real datasets, market-price optimisation,
  mobile app, multi-language support.

**Slide 19 — Conclusion**
- Successful integration of web + DB + ML for a real problem.
- Honest decision-support system, not a guaranteed-yield tool.

**Slide 20 — Thank You**
- Questions?