# ============================================================
# scripts/smoke_server.py
# SMART CROP ROTATION - real server smoke test
# ------------------------------------------------------------
# Boots the actual Flask dev server (python app.py), waits for
# startup, then exercises pages and the API over HTTP.
#
# Usage: python scripts/smoke_server.py
# ============================================================

import json
import os
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "http://127.0.0.1:5000"


def request(path, method="GET", body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    if body:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status, resp.read()


def main():
    env = dict(os.environ)
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )

    ok = True

    def check(name, status, expected):
        nonlocal ok
        good = status == expected
        ok = ok and good
        print(f"  [{'PASS' if good else 'FAIL'}] {name} -> {status}")

    try:
        # wait for server
        alive = False
        for _ in range(60):
            try:
                request("/api/health")
                alive = True
                break
            except Exception:
                time.sleep(0.5)
        check("server started", 200 if alive else 0, 200)

        check("GET /", request("/")[0], 200)
        check("GET /recommend", request("/recommend")[0], 200)
        check("GET /history", request("/history")[0], 200)
        check("GET /analytics", request("/analytics")[0], 200)
        check("GET /model", request("/model")[0], 200)
        check("GET /about", request("/about")[0], 200)
        check("GET /login", request("/login")[0], 200)
        check("GET /register", request("/register")[0], 200)

        payload = {
            "previous_crop": "Rice",
            "season": "Kharif",
            "soil_type": "Loamy",
            "ph": 6.5,
            "n": 40, "p": 45, "k": 40,
            "rainfall": 600, "temperature": 28, "humidity": 65,
            "water_availability": "Medium",
            "irrigation": "Drip",
            "region": "South India",
            "previous_yield": 3.5,
            "disease_level": "Low",
            "fertilizer_usage": "Medium",
            "target_season": "Rabi",
        }
        status, raw = request("/api/recommend", method="POST", body=payload)
        body = json.loads(raw.decode())
        check("POST /api/recommend", status, 200)
        check("api top crop present", isinstance(body.get("recommended_crop"), str), True)

        print("=" * 55)
        print("Server smoke test:", "OK" if ok else "FAILED")
        print("Sample API result ->", body.get("recommended_crop"),
              "| soil:", body.get("soil_health_score"),
              "| rotation:", body.get("rotation_score"),
              "| sustainability:", body.get("sustainability_score"))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())