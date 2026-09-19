# ============================================================
# app.py
# SMART CROP ROTATION - Flask web application
# ------------------------------------------------------------
# Combines:
#   - ML recommendation pipeline (joblib)
#   - Rule-based crop rotation engine (crop_rotation.py)
#   - Soil health & sustainability scoring (soil_analysis.py)
#   - SQLite storage for users, history and model results
#
# Run:  python app.py   ->  http://127.0.0.1:5000
# ============================================================

import json
import os
import sqlite3
from datetime import datetime
from functools import wraps

import joblib
import pandas as pd
from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from crop_rotation import (CROP_KNOWLEDGE, CROPS, IRRIGATIONS, REGIONS,
                           SEASONS, SOIL_TYPES, WATER_LEVELS,
                           build_recommendations, build_rotation_plan,
                           full_recommendation_payload, get_crop, get_family)
from soil_analysis import soil_health_score, sustainability_score

# ------------------------------------------------------------
# App setup
# ------------------------------------------------------------
ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, "database", "crop_rotation.db")
MODEL_PKL = os.path.join(ROOT, "models", "crop_model.pkl")
METRICS_JSON = os.path.join(ROOT, "models", "model_metrics.json")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "smart-crop-rotation-demo-key")


# ------------------------------------------------------------
# Database helpers
# ------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    # Users table (role column added for host/admin support)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL
        );
    """)
    # Migrate older databases that lack the role column
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "role" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS crop_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            previous_crop TEXT,
            recommended_crop TEXT,
            soil_type TEXT,
            ph REAL,
            n REAL,
            p REAL,
            k REAL,
            rainfall REAL,
            temperature REAL,
            humidity REAL,
            season TEXT,
            rotation_score INTEGER,
            soil_health INTEGER,
            sustainability INTEGER,
            model_name TEXT
        );
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            history_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            top_crop TEXT,
            inputs_json TEXT,
            recommendations_json TEXT,
            FOREIGN KEY (history_id) REFERENCES crop_history(id)
        );
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
    conn.close()


def save_history(data, payload):
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO crop_history
        (created_at, previous_crop, recommended_crop, soil_type, ph, n, p, k,
         rainfall, temperature, humidity, season, rotation_score, soil_health,
         sustainability, model_name)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.get("previous_crop"), data.get("recommended_crop"),
        data.get("soil_type"), data.get("ph"), data.get("n"), data.get("p"),
        data.get("k"), data.get("rainfall"), data.get("temperature"),
        data.get("humidity"), data.get("season"),
        int(data.get("rotation_score") or 0),
        int(data.get("soil_health_score") or 0),
        int(data.get("sustainability_score") or 0),
        data.get("model_name"),
    ))
    history_id = cur.lastrowid

    conn.execute("""
        INSERT INTO recommendations
        (history_id, created_at, top_crop, inputs_json, recommendations_json)
        VALUES (?,?,?,?,?)
    """, (
        history_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data.get("recommended_crop"),
        json.dumps(data.get("inputs", {}), default=str),
        json.dumps(payload, default=str),
    ))
    conn.commit()
    conn.close()
    return history_id


# ------------------------------------------------------------
# Model loading
# ------------------------------------------------------------
def load_model():
    bundle = None
    if os.path.exists(MODEL_PKL):
        try:
            bundle = joblib.load(MODEL_PKL)
        except Exception as exc:  # noqa: BLE001 - show a friendly message
            flash(f"Model file could not be loaded: {exc}", "warning")
            bundle = None
    return bundle


MODEL_BUNDLE = load_model()


def ml_probabilities(env_inputs):
    """Return {crop: probability} using the trained pipeline, or None."""
    if not MODEL_BUNDLE or not MODEL_BUNDLE.get("pipeline"):
        return None
    try:
        cols = MODEL_BUNDLE["feature_columns"]
        lowered = {k.lower(): v for k, v in env_inputs.items()}
        row = {}
        for col in cols:
            if col in env_inputs:
                row[col] = env_inputs[col]
            elif col.lower() in lowered:
                row[col] = lowered[col.lower()]
            else:
                row[col] = None
        df = pd.DataFrame([row])[cols]
        pipeline = MODEL_BUNDLE["pipeline"]
        proba = pipeline.predict_proba(df)[0]
        classes = list(pipeline.classes_)
        return {cls: float(p) for cls, p in zip(classes, proba)}
    except Exception as exc:  # noqa: BLE001
        app.logger.warning("ML prediction failed, using rule engine only: %s", exc)
        return None


# ------------------------------------------------------------
# Input validation
# ------------------------------------------------------------
def _to_float(form, key, label, lo=None, hi=None, required=True, errors=None):
    raw = form.get(key)
    if raw is None:
        raw = ""
    elif not isinstance(raw, str):
        raw = str(raw)
    raw = raw.strip()
    if raw == "":
        if required:
            errors[key] = f"{label} is required."
        return None
    try:
        v = float(raw)
    except ValueError:
        errors[key] = f"{label} must be a number."
        return None
    if lo is not None and v < lo:
        errors[key] = f"{label} must be >= {lo}."
        return None
    if hi is not None and v > hi:
        errors[key] = f"{label} must be <= {hi}."
        return None
    return v


def _choice(form, key, label, allowed, required=True, errors=None):
    val = form.get(key)
    if val is None:
        val = ""
    elif not isinstance(val, str):
        val = str(val)
    val = val.strip()
    if val == "":
        if required:
            errors[key] = f"{label} is required."
        return None
    if val not in allowed:
        errors[key] = f"{label} has an invalid value."
        return None
    return val


def parse_and_validate(form):
    """Validate the whole recommendation form."""
    errors = {}

    data = {
        "previous_crop": _choice(form, "previous_crop", "Previous Crop", CROPS, True, errors),
        "season": _choice(form, "season", "Season", SEASONS, True, errors),
        "soil_type": _choice(form, "soil_type", "Soil Type", SOIL_TYPES, True, errors),
        "water_availability": _choice(form, "water_availability", "Water Availability", WATER_LEVELS, True, errors),
        "irrigation": _choice(form, "irrigation", "Irrigation", IRRIGATIONS, True, errors),
        "region": _choice(form, "region", "Region", REGIONS, True, errors),
        "disease_level": _choice(form, "disease_level", "Disease Level", ["Low", "Medium", "High"], True, errors),
        "fertilizer_usage": _choice(form, "fertilizer_usage", "Fertilizer Usage", ["Low", "Medium", "High"], True, errors),
        "target_season": _choice(form, "target_season", "Target Season", SEASONS, True, errors),
        "ph": _to_float(form, "ph", "Soil pH", 0, 14, True, errors),
        "n": _to_float(form, "n", "Nitrogen (N)", 0, None, True, errors),
        "p": _to_float(form, "p", "Phosphorus (P)", 0, None, True, errors),
        "k": _to_float(form, "k", "Potassium (K)", 0, None, True, errors),
        "rainfall": _to_float(form, "rainfall", "Rainfall", 0, None, True, errors),
        "temperature": _to_float(form, "temperature", "Temperature", 5, 45, True, errors),
        "humidity": _to_float(form, "humidity", "Humidity", 0, 100, True, errors),
        "previous_yield": _to_float(form, "previous_yield", "Previous Yield", 0, None, True, errors),
    }

    return data, errors


def env_from_data(data):
    """Build the environment dict used by the engines."""
    return {
        "ph": data.get("ph"), "n": data.get("n"), "p": data.get("p"),
        "k": data.get("k"), "rainfall": data.get("rainfall"),
        "temperature": data.get("temperature"), "humidity": data.get("humidity"),
        "water_availability": data.get("water_availability"),
        "disease_level": data.get("disease_level"),
        "fertilizer_usage": data.get("fertilizer_usage"),
        "soil_type": data.get("soil_type"),
        "irrigation": data.get("irrigation"),
        "region": data.get("region"),
    }


def build_full_result(data):
    """Run all engines and return everything the result page needs."""
    prev_crop = data["previous_crop"]
    season = data["target_season"] or data["season"]
    env = env_from_data(data)

    ml_proba = ml_probabilities(data)  # NOTE: data keys mirror feature names
    usable_proba = ml_proba if ml_proba else None

    payload = full_recommendation_payload(
        prev_crop, season, env,
        ml_proba=usable_proba,
        crop_classes=None,
        model_name=(MODEL_BUNDLE or {}).get("model_name"))

    top_crop = payload["top"]["crop"] if payload["top"] else (CROPS[0])
    top_info = get_crop(top_crop)

    prev_family = get_family(prev_crop)

    sh = soil_health_score(n=data.get("n"), p=data.get("p"), k=data.get("k"),
                           ph=data.get("ph"), previous_crop=prev_crop,
                           fertilizer_usage=data.get("fertilizer_usage"))
    sus = sustainability_score(crop=top_crop,
                              water_availability=data.get("water_availability"),
                              fertilizer_usage=data.get("fertilizer_usage"),
                              soil_health_score_value=sh["score"],
                              disease_level=data.get("disease_level"),
                              previous_crop=prev_crop)

    plan = build_rotation_plan(prev_crop, season, env, years=2)

    result = {
        "payload": payload,
        "prev_family": get_family(prev_crop),
        "top_crop": top_crop,
        "top_family": top_info["family"] if top_info else None,
        "top_water_req": top_info["water_req"] if top_info else None,
        "top_duration": top_info["duration"] if top_info else None,
        "soil_health": sh,
        "sustainability": sus,
        "plan": plan,
        "model_name": (MODEL_BUNDLE or {}).get("model_name"),
        "ml_available": MODEL_BUNDLE is not None,
        "inputs": data,
        "env": env,
    }
    return result


# ------------------------------------------------------------
# Auth helpers
# ------------------------------------------------------------
def logged_in():
    return session.get("user") is not None


def login_required(view):
    """Restrict a route to logged-in users only."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not logged_in():
            flash("Please login to access this feature.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def is_host():
    """True when the logged-in user is the system host/admin."""
    if not logged_in():
        return False
    return session.get("user_role") == "host"


@app.context_processor
def inject_globals():
    return {
        "current_user": session.get("user"),
        "logged_in": logged_in(),
        "crops": CROPS,
    }


# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------
@app.route("/")
def index():
    """Home dashboard."""
    conn = get_db()
    latest = conn.execute(
        "SELECT * FROM crop_history ORDER BY id DESC LIMIT 1").fetchone()
    history_count = conn.execute(
        "SELECT COUNT(*) AS c FROM crop_history").fetchone()["c"]
    conn.close()
    return render_template("index.html", latest=latest, history_count=history_count)


@app.route("/recommend", methods=["GET", "POST"])
@login_required
def recommend():
    """Recommendation form + processing."""
    data = errors = result = None

    if request.method == "POST":
        data, errors = parse_and_validate(request.form)
        if errors:
            # keep previously entered values so the form is not wiped
            data = dict(request.form)
        else:
            result = build_full_result(data)
            history_id = save_history({
                **result,
                "recommended_crop": result["top_crop"],
                "rotation_score": result["payload"]["rotation_total"],
                "soil_health_score": result["soil_health"]["score"],
                "sustainability_score": result["sustainability"]["score"],
                "model_name": result["model_name"],
            }, result["payload"])
            result["history_id"] = history_id
            return render_template("result.html", result=result)

    return render_template("recommend.html", data=data, errors=errors or {})


@app.route("/history")
@login_required
def history():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM crop_history ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("history.html", rows=rows)


@app.route("/history/delete/<int:history_id>", methods=["POST"])
@login_required
def delete_history(history_id):
    conn = get_db()
    conn.execute("DELETE FROM recommendations WHERE history_id = ?", (history_id,))
    conn.execute("DELETE FROM crop_history WHERE id = ?", (history_id,))
    conn.commit()
    conn.close()
    flash("Recommendation history deleted.", "success")
    return redirect(url_for("history"))


@app.route("/history/clear", methods=["POST"])
@login_required
def clear_history():
    conn = get_db()
    conn.execute("DELETE FROM recommendations")
    conn.execute("DELETE FROM crop_history")
    conn.commit()
    conn.close()
    flash("Recommendation history cleared.", "success")
    return redirect(url_for("history"))


@app.route("/report/<int:history_id>")
@login_required
def report(history_id):
    """Print-friendly recommendation report."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM crop_history WHERE id = ?", (history_id,)).fetchone()
    rec = conn.execute(
        "SELECT * FROM recommendations WHERE history_id = ?",
        (history_id,)).fetchone()
    conn.close()

    if row is None or rec is None:
        abort(404)

    inputs = json.loads(rec["inputs_json"])
    inputs["ph"] = float(inputs.get("ph") or 0)
    data = {
        **inputs,
        "previous_crop": row["previous_crop"],
        "target_season": row["season"],
    }
    result = build_full_result(data)
    return render_template("report.html", result=result, history=row, rec=rec)


@app.route("/analytics")
@login_required
def analytics():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM crop_history ORDER BY id DESC LIMIT 10").fetchall()
    models = conn.execute(
        "SELECT * FROM model_results ORDER BY is_best DESC, f1 DESC").fetchall()
    conn.close()

    crops_chart = {}
    for r in rows:
        crops_chart[r["recommended_crop"]] = crops_chart.get(r["recommended_crop"], 0) + 1

    families_chart = {}
    for r in rows:
        fam = get_family(r["recommended_crop"]) or "N/A"
        families_chart[fam] = families_chart.get(fam, 0) + 1

    series = [{"label": r["created_at"], "n": r["n"], "p": r["p"], "k": r["k"],
               "sustainability": r["sustainability"], "soil_health": r["soil_health"],
               "rotation": r["rotation_score"]} for r in rows]

    return render_template("analytics.html", series=series,
                           crops_chart=crops_chart, families_chart=families_chart,
                           models=[dict(m) for m in models])


@app.route("/model")
@login_required
def model_page():
    """Model performance page."""
    metrics = {}
    cm_labels = []
    cm_matrix = []
    cm_json = None
    if os.path.exists(METRICS_JSON):
        try:
            with open(METRICS_JSON, "r", encoding="utf-8") as fh:
                cm_json = json.load(fh)
            metrics = cm_json.get("metrics", {})
            cm_labels = cm_json.get("confusion_matrix", {}).get("labels", [])
            cm_matrix = cm_json.get("confusion_matrix", {}).get("matrix", [])
        except Exception as exc:  # noqa: BLE001
            flash(f"Could not read metrics file: {exc}", "warning")

    conn = get_db()
    models = conn.execute(
        "SELECT * FROM model_results ORDER BY is_best DESC, f1 DESC").fetchall()
    conn.close()

    return render_template("model.html", metrics=metrics, models=[dict(m) for m in models],
                           cm_labels=cm_labels, cm_matrix=cm_matrix,
                           cm_json=cm_json)


@app.route("/about")
def about():
    return render_template("about.html")


# ----- Authentication -----
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""
        error = None
        if len(username) < 3:
            error = "Username must be at least 3 characters."
        elif len(password) < 4:
            error = "Password must be at least 4 characters."
        elif password != confirm:
            error = "Passwords do not match."
        if error is None:
            conn = get_db()
            exists = conn.execute(
                "SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            if exists:
                error = "Username already exists."
            else:
                # The very first registered account becomes the system host.
                is_first = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"] == 0
                role = "host" if is_first else "user"
                conn.execute("INSERT INTO users (username, password_hash, role, created_at)"
                             " VALUES (?,?,?,?)",
                             (username, generate_password_hash(password), role,
                              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                flash("Account created. Please login.", "success")
                return redirect(url_for("login"))
            conn.close()
        flash(error, "danger")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user"] = user["username"]
            session["user_id"] = user["id"]
            session["user_role"] = user["role"]
            flash("Logged in successfully.", "success")
            return redirect(url_for("index"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


# ------------------------------------------------------------
# REST API
# ------------------------------------------------------------
@app.route("/api/health")
def api_health():
    return jsonify({
        "status": "ok",
        "model_loaded": MODEL_BUNDLE is not None,
        "model_name": (MODEL_BUNDLE or {}).get("model_name"),
        "crops_supported": len(CROPS),
    })


@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    """POST /api/recommend with JSON body (see README)."""
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    class FakeForm:
        def get(self, key, default=None):
            return body.get(key, default)

    form = FakeForm()
    data, errors = parse_and_validate(form)

    if errors:
        return jsonify({"error": "Invalid input", "details": errors}), 422

    result = build_full_result(data)
    payload = result["payload"]
    top = payload["top"] or {}
    return jsonify({
        "recommended_crop": top.get("crop"),
        "alternatives": [
            {
                "crop": alt["crop"],
                "suitability": alt["suitability"],
                "rotation_score": alt["rotation_score"],
                "water_requirement": alt["water_req"],
                "reason": f"Alternative #{i+1} rotation candidate",
            }
            for i, alt in enumerate(payload["alternatives"])
        ],
        "rotation_score": payload["rotation_total"],
        "rotation_label": payload["rotation_label"],
        "soil_health_score": result["soil_health"]["score"],
        "soil_health_status": result["soil_health"]["status"],
        "sustainability_score": result["sustainability"]["score"],
        "sustainability_label": result["sustainability"]["label"],
        "reasons": payload["why_checks"],
        "nitrogen_suggestion": payload["nitrogen"],
        "model": result["model_name"],
    })


# ----- Error handlers -----
@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", message="The requested page was not found."), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", message="An internal error occurred. Please try again."), 500


# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------
def create_app():
    init_db()
    return app


if __name__ == "__main__":
    try:
        init_db()
        print("=" * 55)
        print("  SMART CROP ROTATION - Flask Application")
        print("  Open:  http://127.0.0.1:5000")
        if MODEL_BUNDLE:
            print(f"  Model: {MODEL_BUNDLE.get('model_name')} loaded")
        else:
            print("  WARNING: model not found - run `python train_model.py`")
        print("=" * 55)
        app.run(debug=True, use_reloader=False)
    except Exception as exc:  # noqa: BLE001
        print(f"[FATAL] Could not start: {exc}")
        raise SystemExit(1)