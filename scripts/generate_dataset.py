# ============================================================
# generate_dataset.py
# SMART CROP ROTATION - Synthetic dataset generator
# ------------------------------------------------------------
# Creates data/crop_dataset.csv with ~700 meaningful records.
# The data is NOT random noise: labels are sampled from each
# crop's agronomic compatibility band, and rotation logic is
# respected (recommended crop family differs from the previous
# crop most of the time).
#
# Usage:  python generate_dataset.py
# ============================================================

import csv
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crop_rotation import CROP_KNOWLEDGE, CROPS, REGIONS, SOIL_TYPES, SEASONS

random.seed(42)

TARGET_ROWS = 700
MIN_PER_CROP = 20

NUMERIC_KEYS = ["temperature", "humidity", "ph", "rainfall", "previous_yield"]
N_P_K = ["n", "p", "k"]


def sample_in_range(lo, hi):
    return round(random.uniform(lo, hi), 1)


def demand_to_range(demand):
    """Map a crop nutrient demand label to a plausible ppm band."""
    bands = {
        "Low": (18, 42),
        "Medium": (35, 68),
        "High": (52, 92),
    }
    return bands.get(demand, (25, 55))


def pick_crop(prev_crop, season, n_val):
    """Choose a recommended crop consistent with season + rotation logic."""
    candidates = []
    legumes = [c for c in CROPS if CROP_KNOWLEDGE[c]["nitrogen_fixing"]]
    for c in CROPS:
        info = CROP_KNOWLEDGE[c]
        if season not in info["seasons"]:
            continue

        # Strongly prefer a different family than the previous crop (rotation)
        if info["family"] != CROP_KNOWLEDGE[prev_crop]["family"]:
            candidates.append(c)

    # If soil N is low, bias toward nitrogen-fixing crops
    weights = []
    for c in candidates:
        w = 1.0
        if c in legumes and n_val < 35:
            w += 2.0
        if c in CROPS:
            pass
        weights.append(w)

    if candidates:
        return random.choices(candidates, weights=weights, k=1)[0]
    # fallback: any crop that fits season
    return random.choice([c for c in CROPS if season in CROP_KNOWLEDGE[c]["seasons"]])


def make_row(prev_crop=None, season=None, crop=None):
    """Build one realistic record."""
    prev_crop = prev_crop or random.choice(CROPS)
    season = season or random.choices(SEASONS, weights=[0.42, 0.42, 0.16], k=1)[0]
    info = CROP_KNOWLEDGE[crop] if crop else None

    # ----- environment (before crop choice) -----
    soil_type = random.choice(SOIL_TYPES)
    region = random.choice(REGIONS)

    # Slight season/region influence on temperature
    base_temp = random.uniform(22, 30)
    if season == "Rabi":
        base_temp -= random.uniform(4, 8)
    elif season == "Zaid":
        base_temp += random.uniform(2, 4)

    disease_level = random.choices(["Low", "Medium", "High"], weights=[0.40, 0.36, 0.24], k=1)[0]
    fertilizer_usage = random.choices(["Low", "Medium", "High"], weights=[0.30, 0.45, 0.25], k=1)[0]

    # ---- choose the crop first (so irrigation can be drawn from its options) ----
    n_hint = random.uniform(15, 90)
    if crop is None:
        crop = pick_crop(prev_crop, season, n_hint)
    info = CROP_KNOWLEDGE[crop]

    irrigation = random.choice(info["irrigation_ok"] or ["Rainfed", "Drip", "Sprinkler", "Canal"])

    # ----- sample environment inside the crop's compatibility band ----
    temperature = round(min(max(base_temp, info["temp_min"]),
                            max(info["temp_max"], base_temp)), 1)
    # make temperature centred near the crop's preferred centre
    t_centre = (info["temp_min"] + info["temp_max"]) / 2
    temperature = round(t_centre + random.uniform(-3, 3), 1)
    temperature = round(max(info["temp_min"] - 1, min(temperature, info["temp_max"] + 1)), 1)

    ph = round(random.uniform(info["ph_min"], info["ph_max"]), 1)
    rainfall = round(random.uniform(info["rain_min"], info["rain_max"]))
    humidity = round(random.uniform(info["hum_lo"], info["hum_hi"]))

    nv = random.uniform(*demand_to_range(info["n_demand"]))
    pv = random.uniform(*demand_to_range(info["p_demand"]))
    kv = random.uniform(*demand_to_range(info["k_demand"]))
    n, p, k = round(nv), round(pv), round(kv)

    # water availability consistent with rainfall + crop water need
    wreq = info["water_req"].lower()
    if rainfall >= info["rain_max"] * 0.85 and wreq in ("medium", "high"):
        water_availability = random.choice(["High", "High", "Medium"])
    elif rainfall <= info["rain_min"] * 1.15 and wreq in ("medium", "low"):
        water_availability = random.choice(["Low", "Medium"])
    else:
        water_availability = random.choice(["Low", "Medium", "High"])

    # previous yield affected by disease + compatibility
    prev_yield = round(random.uniform(1.0, 8.0), 1)
    if disease_level == "High":
        prev_yield = round(prev_yield * random.uniform(0.4, 0.7), 1)
    elif disease_level == "Medium":
        prev_yield = round(prev_yield * random.uniform(0.7, 0.9), 1)

    return {
        "N": n, "P": p, "K": k,
        "temperature": temperature,
        "humidity": humidity,
        "ph": ph,
        "rainfall": rainfall,
        "soil_type": soil_type,
        "previous_crop": prev_crop,
        "season": season,
        "water_availability": water_availability,
        "irrigation": irrigation,
        "region": region,
        "previous_yield": prev_yield,
        "disease_level": disease_level,
        "fertilizer_usage": fertilizer_usage,
        "recommended_crop": crop,
    }


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(root, "data")
    os.makedirs(data_dir, exist_ok=True)
    out_path = os.path.join(data_dir, "crop_dataset.csv")

    rows = [make_row() for _ in range(TARGET_ROWS)]

    # Guarantee a minimum number of records per crop
    counts = {}
    for r in rows:
        counts[r["recommended_crop"]] = counts.get(r["recommended_crop"], 0) + 1
    for crop in CROPS:
        need = MIN_PER_CROP - counts.get(crop, 0)
        for _ in range(max(0, need)):
            rows.append(make_row(prev_crop=random.choice(CROPS),
                                 season=random.choice(CROP_KNOWLEDGE[crop]["seasons"]),
                                 crop=crop))

    random.shuffle(rows)

    columns = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall",
               "soil_type", "previous_crop", "season", "water_availability",
               "irrigation", "region", "previous_yield", "disease_level",
               "fertilizer_usage", "recommended_crop"]

    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    final_counts = {}
    for r in rows:
        final_counts[r["recommended_crop"]] = final_counts.get(r["recommended_crop"], 0) + 1

    print(f"[OK] Wrote {len(rows)} records to {out_path}")
    print("[OK] Records per crop:")
    for c in sorted(final_counts):
        print(f"     {c:12s} -> {final_counts[c]}")


if __name__ == "__main__":
    main()