# ============================================================
# tests/test_app.py
# SMART CROP ROTATION - automated end-to-end checks
# ------------------------------------------------------------
# Uses Flask's test client (no browser / port needed).
#
# Run:  .\\venv\\Scripts\\python.exe tests\\test_app.py
# ============================================================

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module  # noqa: E402

# Use a temporary database so tests do not pollute real history
_TMP_DB = os.path.join(tempfile.gettempdir(), "scr_test_crop_rotation.db")
if os.path.exists(_TMP_DB):
    os.remove(_TMP_DB)
app_module.DB_PATH = _TMP_DB

TEST_APP = app_module.create_app()
TEST_APP.config["TESTING"] = True
TEST_CLIENT = TEST_APP.test_client()

VALID_INPUT = {
    "previous_crop": "Rice",
    "season": "Kharif",
    "soil_type": "Loamy",
    "ph": "6.5",
    "n": "40",
    "p": "45",
    "k": "40",
    "rainfall": "600",
    "temperature": "28",
    "humidity": "65",
    "water_availability": "Medium",
    "irrigation": "Drip",
    "region": "South India",
    "previous_yield": "3.5",
    "disease_level": "Low",
    "fertilizer_usage": "Medium",
    "target_season": "Rabi",
}

PASSED = 0
FAILED = 0


def check(name, condition, extra=""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [PASS] {name}")
    else:
        FAILED += 1
        print(f"  [FAIL] {name} {extra}")


def main():
    print("=" * 60)
    print("SMART CROP ROTATION - automated checks")
    print("=" * 60)

    # ---- Authenticate first: features are login-gated by design.
    # The very first registered account becomes the host, so this also
    # exercises the first-user / host bootstrap path.
    r = TEST_CLIENT.post("/register", data={
        "username": "host1", "password": "pass123", "confirm": "pass123",
    }, follow_redirects=True)
    check("register host (first user) works", b"Account created" in r.data)
    r = TEST_CLIENT.post("/login", data={
        "username": "host1", "password": "pass123",
    }, follow_redirects=True)
    check("login as host works", b"Logged in successfully" in r.data)

    # ---- Pages load ----
    for route, expect in [
        ("/", 200), ("/recommend", 200), ("/history", 200),
        ("/analytics", 200), ("/model", 200), ("/about", 200),
        ("/login", 200), ("/register", 200),
        ("/api/health", 200),
    ]:
        r = TEST_CLIENT.get(route)
        check(f"GET {route} -> {r.status_code}", r.status_code == expect)

    # health JSON
    r = TEST_CLIENT.get("/api/health")
    body = r.get_json()
    check("api/health reports ok", body and body.get("status") == "ok")
    check("api/health model info", isinstance(body.get("model_name"), str))

    # ---- Form validation ----
    bad = dict(VALID_INPUT, ph="99")
    r = TEST_CLIENT.post("/recommend", data=bad)
    check("invalid pH rejected", b"must be between 0 and 14" in r.data or b"pH" in r.data)
    bad2 = dict(VALID_INPUT, humidity="150")
    r = TEST_CLIENT.post("/recommend", data=bad2)
    check("invalid humidity rejected", b"Humidity" in r.data)
    bad3 = dict(VALID_INPUT, previous_crop="")
    r = TEST_CLIENT.post("/recommend", data=bad3)
    check("empty select rejected", b"required" in r.data)
    bad4 = {k: v for k, v in VALID_INPUT.items() if k != "n"}
    r = TEST_CLIENT.post("/recommend", data=bad4)
    check("missing numeric field rejected", b"required" in r.data)

    # ---- Valid recommendation ----
    r = TEST_CLIENT.post("/recommend", data=VALID_INPUT)
    html = r.data.decode("utf-8", "ignore")
    check("valid recommend -> 200", r.status_code == 200)
    check("result shows TOP RECOMMENDATION", "TOP RECOMMENDATION" in html)
    check("result shows alternatives", "Alternative Crops" in html)
    check("result shows Why section", "Why" in html and "" in html)
    check("result shows nitrogen note", "Nitrogen Management" in html)
    check("result shows timeline", "Crop Rotation Timeline" in html)
    check("result shows soil health", "Soil Health" in html)
    check("result shows sustainability", "Sustainability" in html)
    check("result shows disclaimer", "decision-support" in html.lower())

    # history_id should be in db
    import sqlite3
    conn = sqlite3.connect(_TMP_DB)
    n_hist = conn.execute("SELECT COUNT(*) FROM crop_history").fetchone()[0]
    n_rec = conn.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0]
    conn.close()
    check("history row saved", n_hist == 1)
    check("recommendation snapshot saved", n_rec == 1)

    hist_id = 1

    # ---- Report page ----
    r = TEST_CLIENT.get(f"/report/{hist_id}")
    check("report page -> 200", r.status_code == 200)
    check("report lists scores", b"Rotation Score" in r.data)

    # ---- History page ----
    r = TEST_CLIENT.get("/history")
    check("history lists record", b"Green" in r.data or b"Rice" in r.data or b"Gram" in r.data)

    # ---- API ----
    api_input = {
        "previous_crop": "Rice", "soil_type": "Loamy", "ph": 6.5,
        "nitrogen": 50, "phosphorus": 40, "potassium": 40,
        "rainfall": 800, "temperature": 28, "humidity": 70,
        "season": "Kharif", "target_season": "Rabi",
        "water_availability": "Medium", "irrigation": "Drip",
        "region": "South India", "previous_yield": 3.5,
        "disease_level": "Low", "fertilizer_usage": "Medium",
    }
    # API uses names matching the form fields; translate document example too
    api_input_form = {
        **VALID_INPUT,
        "n": api_input["nitrogen"], "p": api_input["phosphorus"],
        "k": api_input["potassium"],
    }
    r = TEST_CLIENT.post("/api/recommend", json=api_input_form)
    body = r.get_json()
    check("api/recommend -> 200", r.status_code == 200)
    check("api returns recommended_crop", isinstance(body.get("recommended_crop"), str))
    check("api returns alternatives list", isinstance(body.get("alternatives"), list) and len(body["alternatives"]) == 3)
    check("api returns rotation_score", isinstance(body.get("rotation_score"), (int, float)))
    check("api returns soil_health_score", isinstance(body.get("soil_health_score"), (int, float)))
    check("api returns sustainability_score", isinstance(body.get("sustainability_score"), (int, float)))
    check("api returns reasons list", isinstance(body.get("reasons"), list) and len(body["reasons"]) > 0)

    r = TEST_CLIENT.post("/api/recommend", json={"ph": 99, "previous_crop": "Rice"})
    check("api invalid pH -> 422", r.status_code == 422)
    r = TEST_CLIENT.post("/api/recommend", data="not json")
    check("api non-json -> 400", r.status_code == 400)

    # ---- Auth flow ----
    r = TEST_CLIENT.post("/register", data={
        "username": "farmer1", "password": "pass123", "confirm": "pass123",
    }, follow_redirects=True)
    check("register works", b"Account created" in r.data)
    r = TEST_CLIENT.post("/register", data={
        "username": "farmer1", "password": "pass123", "confirm": "pass123",
    }, follow_redirects=True)
    check("duplicate username rejected", b"already exists" in r.data)
    r = TEST_CLIENT.post("/login", data={
        "username": "farmer1", "password": "wrong",
    }, follow_redirects=True)
    check("wrong password rejected", b"Invalid username or password" in r.data)
    r = TEST_CLIENT.post("/login", data={
        "username": "farmer1", "password": "pass123",
    }, follow_redirects=True)
    check("login works", b"Logged in successfully" in r.data)
    with TEST_CLIENT.session_transaction() as flask_session:
        check("session user set", flask_session.get("user") == "farmer1")

    # passwords not stored in plain text
    conn = sqlite3.connect(_TMP_DB)
    row = conn.execute("SELECT password_hash FROM users WHERE username='farmer1'").fetchone()[0]
    conn.close()
    check("password is hashed", row != "pass123" and row.startswith("scrypt") or row.startswith("pbkdf2"))

    r = TEST_CLIENT.get("/logout", follow_redirects=True)
    check("logout works", b"logged out" in r.data)

    # log back in for the remaining authenticated CRUD checks
    r = TEST_CLIENT.post("/login", data={
        "username": "farmer1", "password": "pass123",
    }, follow_redirects=True)
    check("re-login before history CRUD", r.status_code == 200)

    # ---- History delete / clear ----
    r = TEST_CLIENT.post(f"/history/delete/{hist_id}", follow_redirects=True)
    conn = sqlite3.connect(_TMP_DB)
    n_hist = conn.execute("SELECT COUNT(*) FROM crop_history").fetchone()[0]
    conn.close()
    check("history delete works", n_hist == 0)

    # add one again then clear
    TEST_CLIENT.post("/recommend", data=VALID_INPUT)
    r = TEST_CLIENT.post("/history/clear", follow_redirects=True)
    conn = sqlite3.connect(_TMP_DB)
    n_hist = conn.execute("SELECT COUNT(*) FROM crop_history").fetchone()[0]
    n_rec = conn.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0]
    conn.close()
    check("history clear works", n_hist == 0 and n_rec == 0)

    # ---- Error pages ----
    r = TEST_CLIENT.get("/does-not-exist")
    check("404 page", r.status_code == 404)

    print("=" * 60)
    print(f"RESULT: {PASSED} passed, {FAILED} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())