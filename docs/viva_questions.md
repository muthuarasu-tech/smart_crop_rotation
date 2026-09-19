# VIVA Questions & Answers — SMART CROP ROTATION

(30+ common questions with simple BCA-level answers)

---

### Q1. What is crop rotation?
**A.** Crop rotation is the practice of growing different crops in the same field in a planned
sequence instead of the same crop every season. Example: Rice → Green Gram → Groundnut → Maize.

### Q2. Why is crop rotation important?
**A.** It maintains soil fertility (especially nitrogen through legumes), breaks pest and
disease cycles, reduces weed pressure, improves soil structure, and reduces fertiliser costs.

### Q3. Why did you select this project?
**A.** Agriculture is a relatable, real-world domain; the project combines web development,
database design and machine learning — everything I learned in the BCA syllabus — into one
practical, demonstrable system.

### Q4. Why Python?
**A.** Python is beginner-friendly, has excellent libraries for web (Flask), data (Pandas/NumPy)
and ML (Scikit-learn), and integrates everything with a small amount of readable code.

### Q5. Why Flask?
**A.** Flask is a lightweight micro-framework. It is easy to learn, simple to run locally, has
built-in Jinja2 templating, and is enough for this project without the overhead of Django.

### Q6. Why SQLite?
**A.** SQLite is an embedded, file-based, zero-configuration database included in Python's
standard library. No server installation is needed, which is ideal for a student project.

### Q7. What is machine learning?
**A.** Machine learning is a branch of AI where a program learns patterns from data instead of
being explicitly programmed, and uses those patterns to make predictions on new data.

### Q8. Which algorithms did you use?
**A.** Decision Tree, Random Forest, Gradient Boosting (from Scikit-learn), and K-Nearest
Neighbours (KNN).

### Q9. Why Random Forest? / Which was best?
**A.** Random Forest combines many decision trees (ensemble) and usually gives higher accuracy
and less overfitting. In my tests it had the highest F1 score, so it was automatically selected.

### Q10. What is preprocessing?
**A.** Preparing raw data for the model: handling missing values, encoding categorical text into
numbers (one-hot encoding) and scaling numeric columns so all features have a similar range.

### Q11. What is a train-test split?
**A.** Splitting the dataset into a training part (80%) used to teach the model and a testing
part (20%) used to check how well it learned on unseen data.

### Q12. What is accuracy?
**A.** The percentage of test records the model predicted correctly:
`Accuracy = (correct predictions) / (total predictions)`.

### Q13. What is precision?
**A.** Of everything the model *said* was class X, how much was actually class X.
High precision = few false positives.

### Q14. What is recall?
**A.** Of everything that *actually* was class X, how much the model caught.
High recall = few false negatives.

### Q15. What is the F1-score?
**A.** The harmonic mean of precision and recall:
`F1 = 2 * (precision * recall) / (precision + recall)`.
It balances both and is useful when classes are many.

### Q16. What is a confusion matrix?
**A.** A table that shows actual classes vs predicted classes. Diagonal cells are correct
predictions; off-diagonal cells are mistakes, showing which crops get confused.

### Q17. What is overfitting?
**A.** When a model memorises the training data so well that it performs badly on new data.
We avoid it by limiting tree depth, using ensembles and testing on unseen data.

### Q18. How does your system recommend a crop?
**A.** For every candidate crop it computes: ML probability + rotation score + environmental
score, then combines them (45% ML + 40% rotation + 15% environment) and ranks the results.

### Q19. What is the role of soil pH?
**A.** pH measures acidity/alkalinity. Most crops prefer pH 6-7.5; extreme pH blocks nutrient
absorption. The system compares the entered pH with each crop's ideal range.

### Q20. What are NPK values?
**A.** NPK stands for Nitrogen, Phosphorus and Potassium — the three main soil nutrients.
N supports leaves/stem, P supports roots and flowering, K supports overall health and yield.

### Q21. Why are legumes important in rotation?
**A.** Legumes (pulses, groundnut) contain root bacteria that fix atmospheric nitrogen into the
soil, naturally recharging it between heavy-feeding crops.

### Q22. What is one-hot encoding?
**A.** Converting a categorical value like soil type `"Loamy"` into a 0/1 vector where only the
matching column is 1, so the model can use text data mathematically.

### Q23. Why did you use Joblib?
**A.** Joblib efficiently saves (pickles) the entire trained Scikit-learn pipeline to a file, so
the app can reload the model instantly without retraining.

### Q24. How is the Soil Health Score calculated?
**A.** N (20) + P (20) + K (20) + pH (10) + fertiliser management (10) + previous crop effect
(20) = 0-100. Status ranges from Excellent to Needs Attention.

### Q25. How is the Rotation Score calculated?
**A.** Family diversity (25) + soil compatibility (25) + water suitability (20) + disease break
(15) + season suitability (15) = 0-100.

### Q26. How is the Sustainability Score calculated?
**A.** Water efficiency (25) + fertiliser efficiency (25) + crop diversity (20) + soil health
(20) + disease risk (10) = 0-100.

### Q27. Why do you return alternatives, not one crop?
**A.** Farming conditions vary; the farmer needs options. The top crop may be unsuitable for
market, labour or seed availability. Alternatives give practical choices.

### Q28. What is "Explainable AI" in your project?
**A.** Instead of just printing a crop name, the system shows a "Why this crop?" checklist —
season fit, soil compatibility, family diversity, water fit, nitrogen role — so the user
understands the reasoning.

### Q29. What does the REST API do?
**A.** `POST /api/recommend` accepts JSON farm inputs and returns JSON with the recommended crop,
alternatives and all scores — useful for future integration with other applications.

### Q30. How did you validate inputs?
**A.** Two layers: client-side JavaScript (instant feedback) and server-side Python (authoritative
checking). pH must be 0-14, humidity 0-100, temperature 5-45°C, NPK/rainfall/yield ≥ 0.

### Q31. How did you secure passwords?
**A.** Using Werkzeug's `generate_password_hash` (scrypt/pbkdf2) — passwords are stored as
hashes, never as plain text, and checked with `check_password_hash`.

### Q32. What are the limitations of your project?
**A.** The dataset is synthetic; scores are heuristic; no live weather or market data; charts
need internet; and long-duration/intercropping systems are simplified.

### Q33. What is the future scope?
**A.** Live weather/soil APIs, real datasets, market-price optimisation, deep learning, mobile
app, multi-language support, and automatic soil-report parsing.

### Q34. Why is no ML model a "guarantee" of crop success?
**A.** Crop success depends on countless local factors (pests, labour, markets, weather
extremes). ML models learn patterns; they give suggestions, not guarantees. Agriculture advice
must be validated by local experts — the project clearly states this.

### Q35. How would you demo the project to a panel?
**A.** Start the server, open the Home dashboard, click Start Recommendation, fill the form,
submit, and show the top crop + alternatives, the three scores, the "Why this crop?" list, the
timeline, history, analytics charts and the model-performance page.

### Q36. What charts did you use?
**A.** Chart.js: bar charts (NPK, model comparison, crop counts), doughnut (soil health),
radar (sustainability), pie (crop families), line (score trends), plus a colour-coded confusion
matrix table on the model page.

### Q37. Why 80/20 split and stratification?
**A.** 80% is standard for adequate training; 20% is enough unseen data for evaluation.
Stratification keeps the crop-class proportions same in both splits, important for rare crops.

### Q38. What is `predict_proba`?
**A.** A Scikit-learn method that returns the probability of each class instead of just the best
class. The system uses these probabilities inside its weighted ranking formula.

### Q39. Where are model metrics stored?
**A.** In the `model_results` table of SQLite and mirrored in `models/model_metrics.json`,
so the Model page and Analytics can display them without retraining.

### Q40. Can the app run offline?
**A.** Yes, except the Chart.js charts (loaded from a CDN). All logic, database and report pages
work fully offline.