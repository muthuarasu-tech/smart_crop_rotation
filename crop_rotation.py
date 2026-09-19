# ============================================================
# crop_rotation.py
# SMART CROP ROTATION - Rule-based Crop Rotation Engine
# ------------------------------------------------------------
# This module contains:
#   1. The crop knowledge base (agronomic facts for each crop)
#   2. The rotation engine (crop-family based recommendation logic)
#   3. Rotation scoring (0-100) with a per-factor breakdown
#   4. Environmental compatibility scoring
#   5. The combined recommendation builder (ML + rules)
#
# IMPORTANT: This is a decision-support / teaching model.
# The scores are academic estimates, NOT official agronomic
# standards. Always validate recommendations with local
# agricultural experts.
# ============================================================

# ------------------------------------------------------------
# 1. CROP KNOWLEDGE BASE
# ------------------------------------------------------------
# Each crop is described with realistic agronomic ranges so the
# synthetic dataset and the scoring logic stay meaningful.

FAMILIES = ["Cereals", "Pulses", "Oilseeds", "Vegetables", "Commercial"]

CROP_KNOWLEDGE = {
    "Rice": {
        "family": "Cereals",
        "nitrogen_fixing": False,
        "seasons": ["Kharif"],
        "ph_min": 5.5, "ph_max": 7.0,
        "n_demand": "High", "p_demand": "Medium", "k_demand": "Medium",
        "temp_min": 24, "temp_max": 34,
        "rain_min": 1000, "rain_max": 1500,
        "hum_lo": 60, "hum_hi": 90,
        "water_req": "High",
        "irrigation_ok": ["Canal", "Rainfed"],
        "duration": "120-130 days",
        "crop_type": "Cereal / staple",
    },
    "Maize": {
        "family": "Cereals",
        "nitrogen_fixing": False,
        "seasons": ["Kharif", "Rabi"],
        "ph_min": 5.5, "ph_max": 7.5,
        "n_demand": "High", "p_demand": "Medium", "k_demand": "High",
        "temp_min": 22, "temp_max": 32,
        "rain_min": 500, "rain_max": 900,
        "hum_lo": 50, "hum_hi": 80,
        "water_req": "Medium",
        "irrigation_ok": ["Rainfed", "Sprinkler", "Canal", "Drip"],
        "duration": "90-110 days",
        "crop_type": "Cereal / grain",
    },
    "Wheat": {
        "family": "Cereals",
        "nitrogen_fixing": False,
        "seasons": ["Rabi"],
        "ph_min": 6.0, "ph_max": 7.5,
        "n_demand": "High", "p_demand": "Medium", "k_demand": "High",
        "temp_min": 12, "temp_max": 25,
        "rain_min": 400, "rain_max": 700,
        "hum_lo": 40, "hum_hi": 65,
        "water_req": "Medium",
        "irrigation_ok": ["Canal", "Sprinkler", "Drip"],
        "duration": "110-130 days",
        "crop_type": "Cereal / staple",
    },
    "Sorghum": {
        "family": "Cereals",
        "nitrogen_fixing": False,
        "seasons": ["Kharif", "Rabi"],
        "ph_min": 5.5, "ph_max": 8.0,
        "n_demand": "Medium", "p_demand": "Medium", "k_demand": "Medium",
        "temp_min": 25, "temp_max": 35,
        "rain_min": 300, "rain_max": 700,
        "hum_lo": 40, "hum_hi": 70,
        "water_req": "Low",
        "irrigation_ok": ["Rainfed", "Canal"],
        "duration": "90-110 days",
        "crop_type": "Cereal / drought tolerant",
    },
    "Black Gram": {
        "family": "Pulses",
        "nitrogen_fixing": True,
        "seasons": ["Kharif", "Zaid"],
        "ph_min": 6.0, "ph_max": 7.5,
        "n_demand": "Low", "p_demand": "Medium", "k_demand": "Low",
        "temp_min": 25, "temp_max": 35,
        "rain_min": 400, "rain_max": 750,
        "hum_lo": 50, "hum_hi": 80,
        "water_req": "Medium",
        "irrigation_ok": ["Rainfed", "Drip", "Canal"],
        "duration": "70-90 days",
        "crop_type": "Pulse / grain legume",
    },
    "Green Gram": {
        "family": "Pulses",
        "nitrogen_fixing": True,
        "seasons": ["Kharif", "Zaid"],
        "ph_min": 6.0, "ph_max": 7.5,
        "n_demand": "Low", "p_demand": "Medium", "k_demand": "Low",
        "temp_min": 25, "temp_max": 35,
        "rain_min": 350, "rain_max": 700,
        "hum_lo": 45, "hum_hi": 75,
        "water_req": "Low",
        "irrigation_ok": ["Rainfed", "Drip", "Canal"],
        "duration": "60-70 days",
        "crop_type": "Pulse / grain legume",
    },
    "Chickpea": {
        "family": "Pulses",
        "nitrogen_fixing": True,
        "seasons": ["Rabi"],
        "ph_min": 6.0, "ph_max": 8.5,
        "n_demand": "Low", "p_demand": "Medium", "k_demand": "Low",
        "temp_min": 15, "temp_max": 28,
        "rain_min": 300, "rain_max": 600,
        "hum_lo": 30, "hum_hi": 55,
        "water_req": "Low",
        "irrigation_ok": ["Rainfed", "Drip"],
        "duration": "100-120 days",
        "crop_type": "Pulse / grain legume",
    },
    "Cowpea": {
        "family": "Pulses",
        "nitrogen_fixing": True,
        "seasons": ["Kharif", "Zaid"],
        "ph_min": 5.5, "ph_max": 7.5,
        "n_demand": "Low", "p_demand": "Medium", "k_demand": "Low",
        "temp_min": 25, "temp_max": 35,
        "rain_min": 400, "rain_max": 700,
        "hum_lo": 45, "hum_hi": 75,
        "water_req": "Low",
        "irrigation_ok": ["Rainfed", "Drip"],
        "duration": "70-90 days",
        "crop_type": "Pulse / grain legume",
    },
    "Groundnut": {
        "family": "Oilseeds",
        "nitrogen_fixing": True,
        "seasons": ["Kharif", "Zaid"],
        "ph_min": 5.5, "ph_max": 7.5,
        "n_demand": "Low", "p_demand": "High", "k_demand": "Low",
        "temp_min": 25, "temp_max": 35,
        "rain_min": 450, "rain_max": 750,
        "hum_lo": 45, "hum_hi": 75,
        "water_req": "Medium",
        "irrigation_ok": ["Rainfed", "Drip", "Canal"],
        "duration": "100-120 days",
        "crop_type": "Oilseed / legume",
    },
    "Sesame": {
        "family": "Oilseeds",
        "nitrogen_fixing": False,
        "seasons": ["Kharif", "Zaid"],
        "ph_min": 5.5, "ph_max": 7.5,
        "n_demand": "Medium", "p_demand": "Medium", "k_demand": "Medium",
        "temp_min": 25, "temp_max": 35,
        "rain_min": 350, "rain_max": 650,
        "hum_lo": 45, "hum_hi": 70,
        "water_req": "Low",
        "irrigation_ok": ["Rainfed", "Drip"],
        "duration": "80-95 days",
        "crop_type": "Oilseed",
    },
    "Sunflower": {
        "family": "Oilseeds",
        "nitrogen_fixing": False,
        "seasons": ["Rabi", "Zaid"],
        "ph_min": 6.0, "ph_max": 7.5,
        "n_demand": "Medium", "p_demand": "High", "k_demand": "Medium",
        "temp_min": 20, "temp_max": 32,
        "rain_min": 350, "rain_max": 600,
        "hum_lo": 45, "hum_hi": 70,
        "water_req": "Medium",
        "irrigation_ok": ["Rainfed", "Sprinkler", "Drip"],
        "duration": "85-100 days",
        "crop_type": "Oilseed",
    },
    "Tomato": {
        "family": "Vegetables",
        "nitrogen_fixing": False,
        "seasons": ["Rabi", "Zaid"],
        "ph_min": 6.0, "ph_max": 7.0,
        "n_demand": "Medium", "p_demand": "High", "k_demand": "High",
        "temp_min": 18, "temp_max": 30,
        "rain_min": 400, "rain_max": 700,
        "hum_lo": 40, "hum_hi": 65,
        "water_req": "Medium",
        "irrigation_ok": ["Drip", "Sprinkler", "Rainfed", "Canal"],
        "duration": "100-120 days",
        "crop_type": "Vegetable / fruit",
    },
    "Brinjal": {
        "family": "Vegetables",
        "nitrogen_fixing": False,
        "seasons": ["Rabi", "Zaid"],
        "ph_min": 5.5, "ph_max": 7.0,
        "n_demand": "Medium", "p_demand": "Medium", "k_demand": "Medium",
        "temp_min": 20, "temp_max": 32,
        "rain_min": 500, "rain_max": 800,
        "hum_lo": 50, "hum_hi": 80,
        "water_req": "Medium",
        "irrigation_ok": ["Drip", "Sprinkler", "Rainfed", "Canal"],
        "duration": "110-130 days",
        "crop_type": "Vegetable / fruit",
    },
    "Chilli": {
        "family": "Vegetables",
        "nitrogen_fixing": False,
        "seasons": ["Kharif", "Rabi", "Zaid"],
        "ph_min": 6.0, "ph_max": 7.5,
        "n_demand": "Medium", "p_demand": "High", "k_demand": "High",
        "temp_min": 20, "temp_max": 32,
        "rain_min": 400, "rain_max": 700,
        "hum_lo": 40, "hum_hi": 65,
        "water_req": "Medium",
        "irrigation_ok": ["Drip", "Sprinkler", "Rainfed", "Canal"],
        "duration": "90-120 days",
        "crop_type": "Vegetable / spice",
    },
    "Onion": {
        "family": "Vegetables",
        "nitrogen_fixing": False,
        "seasons": ["Rabi"],
        "ph_min": 6.0, "ph_max": 7.5,
        "n_demand": "Medium", "p_demand": "Medium", "k_demand": "High",
        "temp_min": 13, "temp_max": 28,
        "rain_min": 350, "rain_max": 600,
        "hum_lo": 40, "hum_hi": 60,
        "water_req": "Medium",
        "irrigation_ok": ["Drip", "Sprinkler", "Canal", "Rainfed"],
        "duration": "100-130 days",
        "crop_type": "Vegetable / bulb",
    },
    "Cotton": {
        "family": "Commercial",
        "nitrogen_fixing": False,
        "seasons": ["Kharif"],
        "ph_min": 6.0, "ph_max": 8.0,
        "n_demand": "High", "p_demand": "High", "k_demand": "High",
        "temp_min": 25, "temp_max": 35,
        "rain_min": 500, "rain_max": 900,
        "hum_lo": 50, "hum_hi": 75,
        "water_req": "Medium",
        "irrigation_ok": ["Rainfed", "Drip", "Sprinkler", "Canal"],
        "duration": "140-180 days",
        "crop_type": "Commercial / fibre",
    },
    "Sugarcane": {
        "family": "Commercial",
        "nitrogen_fixing": False,
        "seasons": ["Kharif", "Rabi"],
        "ph_min": 6.0, "ph_max": 7.5,
        "n_demand": "High", "p_demand": "Medium", "k_demand": "High",
        "temp_min": 25, "temp_max": 35,
        "rain_min": 900, "rain_max": 1500,
        "hum_lo": 60, "hum_hi": 90,
        "water_req": "High",
        "irrigation_ok": ["Canal", "Rainfed"],
        "duration": "300-360 days",
        "crop_type": "Commercial / long duration",
    },
}

# Ordered list of crop display names (used to keep ranking stable)
CROPS = list(CROP_KNOWLEDGE.keys())
SEASONS = ["Kharif", "Rabi", "Zaid"]
IRRIGATIONS = ["Rainfed", "Drip", "Sprinkler", "Canal", "Other"]
WATER_LEVELS = ["Low", "Medium", "High"]
REGIONS = ["North India", "South India", "East India", "West India", "Central India", "North-East India"]
SOIL_TYPES = ["Alluvial", "Black", "Clay", "Loamy", "Red", "Sandy"]

# Known high-value rotation pairs (adds a small bonus, keeps ordering sensible)
CURATED_PAIRS = {
    "Rice": ["Green Gram", "Black Gram", "Groundnut", "Maize", "Cowpea", "Sesame", "Tomato"],
    "Maize": ["Green Gram", "Black Gram", "Groundnut", "Chickpea", "Tomato", "Sunflower"],
    "Wheat": ["Green Gram", "Black Gram", "Groundnut", "Maize", "Sunflower", "Onion"],
    "Sorghum": ["Green Gram", "Black Gram", "Chickpea", "Groundnut", "Sunflower"],
    "Black Gram": ["Maize", "Rice", "Wheat", "Sorghum", "Cotton", "Sugarcane"],
    "Green Gram": ["Maize", "Rice", "Wheat", "Sorghum", "Cotton"],
    "Chickpea": ["Maize", "Wheat", "Sorghum", "Cotton", "Sunflower"],
    "Cowpea": ["Maize", "Rice", "Sorghum", "Sunflower", "Cotton"],
    "Groundnut": ["Rice", "Maize", "Wheat", "Sorghum", "Sunflower", "Chilli"],
    "Sesame": ["Maize", "Wheat", "Sorghum", "Green Gram", "Black Gram"],
    "Sunflower": ["Green Gram", "Black Gram", "Chickpea", "Wheat", "Maize"],
    "Tomato": ["Green Gram", "Black Gram", "Chickpea", "Maize", "Sorghum"],
    "Brinjal": ["Green Gram", "Black Gram", "Chickpea", "Maize", "Sorghum"],
    "Chilli": ["Green Gram", "Black Gram", "Groundnut", "Maize", "Sorghum"],
    "Onion": ["Green Gram", "Black Gram", "Chickpea", "Maize", "Wheat"],
    "Cotton": ["Green Gram", "Black Gram", "Chickpea", "Cowpea", "Maize"],
    "Sugarcane": ["Green Gram", "Black Gram", "Cowpea", "Maize", "Sorghum"],
}


# ------------------------------------------------------------
# 2. SMALL HELPERS
# ------------------------------------------------------------
def nutrient_level(value):
    """Classify an N/P/K ppm value into Low / Medium / High."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "Medium"
    if v < 25:
        return "Low"
    if v <= 55:
        return "Medium"
    return "High"


def get_crop(crop_name):
    """Return the knowledge record for a crop (None-safe)."""
    if not crop_name:
        return None
    return CROP_KNOWLEDGE.get(crop_name)


def get_family(crop_name):
    info = get_crop(crop_name)
    return info["family"] if info else None


def crops_by_family(family):
    return [c for c in CROPS if CROP_KNOWLEDGE[c]["family"] == family]


# ------------------------------------------------------------
# 3. ROTATION SCORE (0-100) WITH BREAKDOWN
# ------------------------------------------------------------
def rotation_score(prev_crop, crop, ph=None, n=None, p=None, k=None,
                   season=None, water_availability=None, disease_level=None):
    """
    Compute a rotation score (0-100) for planting 'crop' after 'prev_crop'.

    Category weights (academic model):
      Family diversity       25
      Soil compatibility     25
      Water suitability      20
      Disease break          15
      Season suitability     15
      --------------------- 100
    """
    info = get_crop(crop)
    if info is None:
        return {"total": 0.0, "breakdown": {}, "label": "N/A"}

    # --- 1. Family diversity (25) ---
    prev_family = get_family(prev_crop)
    if prev_family is None:
        fam = 25.0
    elif info["family"] != prev_family:
        fam = 25.0
    else:
        fam = 6.0  # same family: weak; repeated monoculture is discouraged
    fam = round(fam, 1)

    # --- 2. Soil compatibility (25) ---
    soil = 0.0
    # pH closeness (0-10)
    try:
        ph = float(ph)
    except (TypeError, ValueError):
        ph = None
    if ph is None:
        soil += 7.0
    elif info["ph_min"] <= ph <= info["ph_max"]:
        soil += 10.0
    elif ph < info["ph_min"]:
        soil += 7.0 if (info["ph_min"] - ph) <= 0.5 else (4.0 if (info["ph_min"] - ph) <= 1.0 else 1.5)
    else:
        soil += 7.0 if (ph - info["ph_max"]) <= 0.5 else (4.0 if (ph - info["ph_max"]) <= 1.0 else 1.5)

    # N-P-K demand vs availability (0-15)
    nutrient_ok = 0.0
    for val, demand in ((n, info["n_demand"]), (p, info["p_demand"]), (k, info["k_demand"])):
        level = nutrient_level(val)
        if val is not None:
            if level == demand.lower():
                nutrient_ok += 5.0
            else:
                # tolerable one-step mismatch is still fairly OK
                order = {"low": 0, "medium": 1, "high": 2}
                if abs(order.get(level, 1) - order.get(demand.lower(), 1)) <= 1:
                    nutrient_ok += 2.5
                else:
                    nutrient_ok += 0.5
    nutrient_ok = round(nutrient_ok, 1)
    soil += nutrient_ok
    soil = round(min(soil, 25.0), 1)

    # --- 3. Water suitability (20) ---
    water_map = {
        ("Low", "Low"): 20.0, ("Low", "Medium"): 15.0, ("Low", "High"): 10.0,
        ("Medium", "Low"): 10.0, ("Medium", "Medium"): 20.0, ("Medium", "High"): 15.0,
        ("High", "Low"): 5.0, ("High", "Medium"): 12.0, ("High", "High"): 20.0,
    }
    wreq = info["water_req"].lower()
    wavail = (water_availability or "Medium").lower()
    water = water_map.get((wreq, wavail), 12.0)

    # --- 4. Disease break (15) ---
    dis = (disease_level or "Low").lower()
    if prev_family is None:
        dis_score = 15.0
    elif info["family"] == prev_family:
        dis_score = 3.0 if dis == "high" else (5.0 if dis == "medium" else 6.0)
    else:
        dis_score = 15.0
    dis_score = round(dis_score, 1)

    # --- 5. Season suitability (15) ---
    if season and season in info["seasons"]:
        season_score = 15.0
    elif season == "Zaid" and "Zaid" in info["seasons"]:
        season_score = 15.0
    elif season:
        season_score = 7.0
    else:
        season_score = 12.0

    total = round(fam + soil + water + dis_score + season_score, 1)

    breakdown = {
        "family_diversity": {"max": 25, "score": fam, "label": "Crop Family Diversity"},
        "soil_compatibility": {"max": 25, "score": soil, "label": "Soil Compatibility"},
        "water_suitability": {"max": 20, "score": round(water, 1), "label": "Water Suitability"},
        "disease_break": {"max": 15, "score": dis_score, "label": "Disease Break"},
        "season_suitability": {"max": 15, "score": season_score, "label": "Season Suitability"},
    }

    if total >= 80:
        label = "Excellent"
    elif total >= 65:
        label = "Good"
    elif total >= 50:
        label = "Fair"
    else:
        label = "Poor"

    return {"total": total, "breakdown": breakdown, "label": label}


# ------------------------------------------------------------
# 4. ENVIRONMENTAL COMPATIBILITY (0-100)
# ------------------------------------------------------------
def env_compatibility(crop, temperature=None, rainfall=None, humidity=None,
                      ph=None, season=None):
    """How well the crop fits the entered environment (0-100)."""
    info = get_crop(crop)
    if info is None:
        return 40.0

    score = 0.0

    # Season (30)
    if season and season in info["seasons"]:
        score += 30
    else:
        score += 10

    # Temperature (20)
    try:
        t = float(temperature)
        if info["temp_min"] <= t <= info["temp_max"]:
            score += 20
        elif abs(t - info["temp_min"]) <= 4 or abs(t - info["temp_max"]) <= 4:
            score += 12
        else:
            score += 5
    except (TypeError, ValueError):
        score += 12

    # Rainfall (20)
    try:
        r = float(rainfall)
        if info["rain_min"] <= r <= info["rain_max"]:
            score += 20
        elif abs(r - info["rain_min"]) <= 150 or abs(r - info["rain_max"]) <= 150:
            score += 12
        else:
            score += 6
    except (TypeError, ValueError):
        score += 12

    # pH (15)
    try:
        ph = float(ph)
        if info["ph_min"] <= ph <= info["ph_max"]:
            score += 15
        elif abs(ph - info["ph_min"]) <= 0.5 or abs(ph - info["ph_max"]) <= 0.5:
            score += 10
        elif abs(ph - info["ph_min"]) <= 1 or abs(ph - info["ph_max"]) <= 1:
            score += 6
        else:
            score += 2
    except (TypeError, ValueError):
        score += 9

    # Humidity (15)
    try:
        h = float(humidity)
        if info["hum_lo"] <= h <= info["hum_hi"]:
            score += 15
        elif abs(h - info["hum_lo"]) <= 15 or abs(h - info["hum_hi"]) <= 15:
            score += 9
        else:
            score += 4
    except (TypeError, ValueError):
        score += 9

    return max(5, min(score, 100))


# ------------------------------------------------------------
# 5. NITROGEN MANAGEMENT SUGGESTIONS
# ------------------------------------------------------------
def nitrogen_suggestion(n, recommended_crop, alternative_crop=None):
    """Return a user-friendly nitrogen management message."""
    try:
        n = float(n)
    except (TypeError, ValueError):
        n = None

    helping = alternative_crop or recommended_crop
    is_legume = False
    for probe in (recommended_crop, alternative_crop):
        info = get_crop(probe)
        if info and info["nitrogen_fixing"]:
            is_legume = True
            helping = probe
            break

    if n is None:
        return "Soil nitrogen was not provided; no specific nitrogen advice is given."

    message = ""
    if n < 25:
        message = (f"Soil nitrogen level is LOW ({n}). A nitrogen-fixing crop such as "
                   f"{helping} is preferred because legumes/pulses can add atmospheric "
                   "nitrogen to the soil through biological nitrogen fixation, which may "
                   "reduce the need for synthetic N fertiliser in the next season.")
    elif n <= 55:
        message = (f"Soil nitrogen level is MODERATE ({n}). "
                   "Prefer moderately demanding crops and consider a balanced fertiliser plan.")
    else:
        message = (f"Soil nitrogen level is HIGH ({n}). "
                   "Avoid heavily nitrogen-demanding crops where possible to reduce the risk "
                   "of leaching losses and keep fertiliser use responsible.")

    return message


# ------------------------------------------------------------
# 6. REASON GENERATOR
# ------------------------------------------------------------
def why_this_crop(prev_crop, crop, season, water_availability, ph, n):
    """Build the 'Why this crop?' checklist + free-text reason."""
    info = get_crop(crop)
    checks = []
    reason_parts = []

    prev_family = get_family(prev_crop)

    # Family diversity
    if prev_family and info and info["family"] != prev_family:
        checks.append(
            f"Belongs to the {info['family']} family - adds crop-family diversity "
            f"(previous crop was {prev_family}).")
        reason_parts.append(f"suitable as a rotation crop after {prev_crop}")
    else:
        checks.append("Compatible with the previous crop selection.")

    # Season
    if season and season in info["seasons"]:
        checks.append(f"Suitable for the {season} season.")
    else:
        checks.append("Grows in the selected season.")

    # Soil
    try:
        ph = float(ph)
        if info and info["ph_min"] <= ph <= info["ph_max"]:
            checks.append(f"Compatible with the entered soil pH ({ph}).")
        else:
            checks.append("Tolerates the entered soil conditions.")
    except (TypeError, ValueError):
        checks.append("Compatible with the entered soil conditions.")

    # Water
    if info and water_availability:
        checks.append(f"Its {info['water_req']} water requirement is practical for "
                      f"{water_availability} available water.")

    # Nitrogen
    if info and info["nitrogen_fixing"]:
        checks.append("It is a nitrogen-fixing crop that can help restore soil nitrogen.")
    else:
        checks.append("Its nutrient demand fits typical rotation practice.")

    checks.append("Helps diversify the crop rotation sequence.")

    reason = (f"{crop} is {', '.join(reason_parts) if reason_parts else 'a suitable rotation candidate'} "
              "and is compatible with the provided environmental conditions. "
              "This is a decision-support suggestion, not a guarantee of yield.")
    return checks, reason


# ------------------------------------------------------------
# 7. RECOMMENDATION BUILDER (ML + RULES)
# ------------------------------------------------------------
def build_recommendations(prev_crop, season, env, ml_proba=None, crop_classes=None,
                          n_recommendations=4):
    """
    Combine the ML prediction probabilities with the rule-based rotation
    scores and produce an ordered list of recommendations.

    env: dict with keys ph, n, p, k, rainfall, temperature, humidity,
         water_availability, disease_level, fertilizer_usage, soil_type,
         irrigation, region.

    ml_proba: dict {crop_name: probability} or None.
    """
    candidates = []
    for crop in CROPS:
        if crop == prev_crop:
            continue  # never recommend the exact same crop again

        info = CROP_KNOWLEDGE[crop]
        rot = rotation_score(
            prev_crop, crop,
            ph=env.get("ph"), n=env.get("n"), p=env.get("p"), k=env.get("k"),
            season=season, water_availability=env.get("water_availability"),
            disease_level=env.get("disease_level"))
        envs = env_compatibility(
            crop, temperature=env.get("temperature"), rainfall=env.get("rainfall"),
            humidity=env.get("humidity"), ph=env.get("ph"), season=season)

        # ML probability for this crop
        prob = 0.0
        if ml_proba:
            prob = float(ml_proba.get(crop, 0.0) or 0.0)

        # Bonus for known curated rotation pairs
        curated_bonus = 2.0 if prev_crop in CURATED_PAIRS and crop in CURATED_PAIRS[prev_crop] else 0.0

        # Combine: 45% ML, 40% rotation rules, 15% environment
        final = 0.45 * (prob * 100.0) + 0.40 * rot["total"] + 0.15 * envs + curated_bonus

        candidates.append({
            "crop": crop,
            "family": info["family"],
            "suitability": round(max(0, min(100, float(final))), 1),
            "rotation_score": rot["total"],
            "rotation_label": rot["label"],
            "env_score": round(envs, 1),
            "ml_prob": round(prob * 100.0, 1),
            "water_req": info["water_req"],
            "season_ok": season in info["seasons"],
            "nitrogen_fixing": info["nitrogen_fixing"],
            "duration": info["duration"],
            "breakdown": rot["breakdown"],
        })

    candidates.sort(key=lambda c: (c["suitability"], c["rotation_score"]), reverse=True)

    top = candidates[:n_recommendations] if candidates else []
    return top


def full_recommendation_payload(prev_crop, season, env, ml_proba=None, crop_classes=None,
                                model_name=None):
    """Everything the result page needs for one recommendation request."""
    top = build_recommendations(prev_crop, season, env, ml_proba, crop_classes)

    payload = {
        "top": None,
        "alternatives": [],
        "why_checks": [],
        "reason": "",
        "rotation_breakdown": [],
        "rotation_total": 0,
        "rotation_label": "N/A",
        "nitrogen": nitrogen_suggestion(env.get("n"), top[0]["crop"] if top else None),
        "model_name": model_name,
    }

    if top:
        first = top[0]
        payload["top"] = first
        payload["alternatives"] = top[1:]
        checks, reason = why_this_crop(
            prev_crop, first["crop"], season,
            env.get("water_availability"), env.get("ph"), env.get("n"))
        payload["why_checks"] = checks
        payload["reason"] = reason
        breakdown = first["breakdown"]
        payload["rotation_breakdown"] = [
            {"label": b["label"], "score": b["score"], "max": b["max"]}
            for b in breakdown.values()
        ]
        payload["rotation_total"] = first["rotation_score"]
        payload["rotation_label"] = first["rotation_label"]

    return payload


# ------------------------------------------------------------
# 8. CROP ROTATION TIMELINE / PLAN
# ------------------------------------------------------------
def build_rotation_plan(seed_crop, season, env, years=2):
    """
    Build a visual rotation timeline starting after 'seed_crop'.
    years controls how many future seasons to simulate.
    """
    plan = []
    current_season_index = SEASONS.index(season) if season in SEASONS else 1
    prev_crop = seed_crop

    for step in range(int(years) * 2):
        next_season = SEASONS[current_season_index % 3]
        current_season_index += 1
        recs = build_recommendations(prev_crop, next_season, env, ml_proba=None, n_recommendations=1)
        chosen = recs[0] if recs else None
        if chosen is None:
            break
        plan.append({
            "season_no": step + 1,
            "season": next_season,
            "crop": chosen["crop"],
            "family": chosen["family"],
            "score": chosen["suitability"],
        })
        prev_crop = chosen["crop"]

    return plan


# ============================================================
# Quick self test
# ============================================================
if __name__ == "__main__":
    demo_env = {
        "ph": 6.5, "n": 40, "p": 45, "k": 40,
        "rainfall": 550, "temperature": 28, "humidity": 60,
        "water_availability": "Medium", "disease_level": "Low",
        "fertilizer_usage": "Medium", "soil_type": "Loamy",
        "irrigation": "Drip", "region": "South India",
    }
    recs = build_recommendations("Rice", "Rabi", demo_env)
    for r in recs:
        print(r["crop"], "->", r["suitability"], "| rotation:", r["rotation_score"])
    print("Plan:", [(p["season"], p["crop"]) for p in build_rotation_plan("Rice", "Rabi", demo_env)])