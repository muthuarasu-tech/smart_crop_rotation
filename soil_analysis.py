# ============================================================
# soil_analysis.py
# SMART CROP ROTATION - Soil Health & Sustainability Scoring
# ------------------------------------------------------------
# Provides:
#   1. Soil Health Score (0-100) with status + explanation
#   2. Sustainability Score (0-100) with factor breakdown
#
# NOTE: These are academic scoring models for the project only.
# They are NOT official soil-test or sustainability standards.
# ============================================================

from crop_rotation import nutrient_level, get_crop, get_family

# ------------------------------------------------------------
# Reference (approximate) ideal ranges used for scoring
# ------------------------------------------------------------
IDEAL = {
    "N": {"low": 0, "ok": 25, "high": 55, "max": 100},
    "P": {"low": 0, "ok": 25, "high": 55, "max": 100},
    "K": {"low": 0, "ok": 25, "high": 55, "max": 100},
}
IDEAL_PH = 6.5
PH_RANGE = (5.5, 7.5)


def _npk_fit_score(value, key):
    """How close an N/P/K value is to the ideal band (0-30 each)."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 15.0
    ideal = IDEAL[key]
    if ideal["ok"] <= v <= ideal["high"]:
        return 30.0
    if v < ideal["low"]:
        return 5.0
    if v > ideal["max"]:
        return 12.0
    # between low and ok
    ratio = (v - ideal["low"]) / max(1e-6, ideal["ok"] - ideal["low"])
    return 12.0 + 18.0 * max(0.0, min(1.0, ratio))


def _ph_score(ph):
    try:
        v = float(ph)
    except (TypeError, ValueError):
        return 5.0
    if PH_RANGE[0] <= v <= PH_RANGE[1]:
        return 10.0
    if 5.0 <= v <= 8.5:
        return 5.0
    return 1.5


# ------------------------------------------------------------
# 1. SOIL HEALTH SCORE  (0-100)
# ------------------------------------------------------------
def soil_health_score(n=None, p=None, k=None, ph=None,
                      previous_crop=None, fertilizer_usage="Medium"):
    """
    Returns a dict:
      score, status, breakdown, suggestions
    Factors:
      - N, P, K (20 points each = 60)
      - pH    (10)
      - Fertilizer management (10)
      - Previous crop / cover (20)
    """
    breakdown = []
    score = 0.0

    for key in ("N", "P", "K"):
        val = {"N": n, "P": p, "K": k}[key]
        fit = _npk_fit_score(val, key)
        score += fit
        level = nutrient_level(val)
        breakdown.append({
            "label": f"{key} Level",
            "score": round(fit, 1),
            "max": 20,
            "note": f"{level} ({val if val is not None else 'N/A'})",
        })

    ph_s = _ph_score(ph)
    score += ph_s
    try:
        ph_v = float(ph)
        if abs(ph_v - IDEAL_PH) <= 0.5:
            ph_note = "Near-neutral, ideal for most crops"
        elif PH_RANGE[0] <= ph_v <= PH_RANGE[1]:
            ph_note = "Within typical crop range"
        else:
            ph_note = "Outside the ideal range - consider liming/amendment"
    except (TypeError, ValueError):
        ph_note = "Not provided"
    breakdown.append({
        "label": "Soil pH",
        "score": round(ph_s, 1),
        "max": 10,
        "note": f"{ph_note} (pH {ph})",
    })

    # Fertilizer management (10)
    fert = (fertilizer_usage or "Medium").lower()
    fert_factor = {"low": 8.0, "medium": 6.0, "high": 3.0}.get(fert, 6.0)
    # If NPK already high but fertiliser also high -> over-application risk
    if (nutrient_level(n) == "High" or nutrient_level(p) == "High") and fert == "high":
        fert_factor = 2.0
    score += fert_factor
    breakdown.append({
        "label": "Fertiliser Management",
        "score": round(fert_factor, 1),
        "max": 10,
        "note": f"{fertilizer_usage} usage",
    })

    # Previous crop factor (20)
    prev_factor = 12.0
    prev_family = get_family(previous_crop)
    if prev_family:
        if prev_family == "Pulses":
            prev_factor = 20.0  # legumes enrich soil
        elif prev_family == "Vegetables":
            prev_factor = 12.0
        elif prev_family == "Commercial":
            prev_factor = 9.0  # heavy feeders
        else:
            prev_factor = 14.0
    score += prev_factor
    breakdown.append({
        "label": "Previous Crop Effect",
        "score": round(prev_factor, 1),
        "max": 20,
        "note": previous_crop or "No data",
    })

    score = round(max(0.0, min(100.0, score)), 1)

    if score >= 80:
        status = "Excellent"
    elif score >= 65:
        status = "Good"
    elif score >= 50:
        status = "Moderate"
    else:
        status = "Needs Attention"

    suggestions = []
    try:
        if float(n) < 25:
            suggestions.append("Nitrogen is low - prefer a legume (pulse) crop in the next rotation.")
        if float(p) < 25:
            suggestions.append("Phosphorus is low - plan phosphorus application with the next crop.")
        if float(k) < 25:
            suggestions.append("Potassium is low - include K in the fertiliser schedule.")
    except (TypeError, ValueError):
        pass
    try:
        ph_v = float(ph)
        if ph_v < 5.5:
            suggestions.append("Soil is acidic - consider lime/soil amendment before planting.")
        elif ph_v > 7.5:
            suggestions.append("Soil is alkaline - choose crops tolerant to alkaline soil.")
    except (TypeError, ValueError):
        pass
    if not suggestions:
        suggestions.append("Soil nutrient levels are reasonably balanced for the next season.")

    return {
        "score": score,
        "status": status,
        "breakdown": breakdown,
        "suggestions": suggestions,
    }


def soil_health_status(score):
    if score >= 80:
        return "Excellent"
    if score >= 65:
        return "Good"
    if score >= 50:
        return "Moderate"
    return "Needs Attention"


# ------------------------------------------------------------
# 2. SUSTAINABILITY SCORE  (0-100)
# ------------------------------------------------------------
def sustainability_score(crop=None, water_availability="Medium",
                         fertilizer_usage="Medium", soil_health_score_value=60,
                         disease_level="Low", previous_crop=None):
    """
    Academic sustainability estimate 0-100 weighing:
      Water efficiency (25), fertiliser efficiency (25),
      crop diversity (20), soil health (20), disease risk (10)
    """
    breakdown = []

    info = get_crop(crop) if crop else None

    # Water efficiency (25)
    wavail = (water_availability or "Medium").lower()
    if info:
        wreq = info["water_req"].lower()
        if wreq == "low":
            water_s = 25.0 if wavail in ("low", "medium") else 18.0
        elif wreq == "high":
            water_s = 8.0 if wavail != "high" else 15.0
        else:
            water_s = 22.0 if wavail == "medium" else (18.0 if wavail == "high" else 12.0)
    else:
        water_s = 16.0
    breakdown.append({
        "label": "Water Efficiency",
        "score": round(water_s, 1), "max": 25,
        "note": f"{crop or 'N/A'} / {water_availability} water",
    })

    # Fertiliser efficiency (25)
    fert = (fertilizer_usage or "medium").lower()
    fert_s = {"low": 25.0, "medium": 19.0, "high": 10.0}.get(fert, 19.0)
    if info and info["nitrogen_fixing"]:
        fert_s = min(25.0, fert_s + 4.0)  # legumes reduce N fertiliser need
    breakdown.append({
        "label": "Fertiliser Efficiency",
        "score": round(fert_s, 1), "max": 25,
        "note": f"{fertilizer_usage} usage",
    })

    # Crop diversity (20)
    prev_family = get_family(previous_crop)
    diversity_s = 20.0
    if info and prev_family:
        if info["family"] != prev_family:
            diversity_s = 20.0
        else:
            diversity_s = 8.0
    breakdown.append({
        "label": "Crop Diversity",
        "score": round(diversity_s, 1), "max": 20,
        "note": "Different family vs previous crop" if diversity_s >= 15 else "Same family as previous crop",
    })

    # Soil health (20)
    try:
        shv = float(soil_health_score_value)
    except (TypeError, ValueError):
        shv = 60.0
    soil_s = round(shv * 0.20, 1)
    breakdown.append({
        "label": "Soil Health",
        "score": round(soil_s, 1), "max": 20,
        "note": f"Soil health {shv:.0f}/100",
    })

    # Disease risk (10)
    dis = (disease_level or "low").lower()
    dis_s = {"low": 10.0, "medium": 7.0, "high": 4.0}.get(dis, 10.0)
    if info and prev_family and info["family"] == prev_family:
        dis_s = min(dis_s, 5.0)  # same family raises disease carryover risk
    breakdown.append({
        "label": "Disease Risk",
        "score": round(dis_s, 1), "max": 10,
        "note": f"{disease_level} disease level",
    })

    total = round(sum(b["score"] for b in breakdown), 1)
    total = round(max(0.0, min(100.0, total)), 1)

    if total >= 80:
        label = "High Sustainability"
    elif total >= 60:
        label = "Moderate Sustainability"
    else:
        label = "Needs Improvement"

    return {"score": total, "label": label, "breakdown": breakdown}


# ------------------------------------------------------------
# Quick self test
# ------------------------------------------------------------
if __name__ == "__main__":
    sh = soil_health_score(n=45, p=40, k=35, ph=6.5,
                           previous_crop="Rice", fertilizer_usage="Medium")
    print("Soil health:", sh["score"], sh["status"], sh["suggestions"])
    sus = sustainability_score(crop="Green Gram", water_availability="Medium",
                               fertilizer_usage="Medium",
                               soil_health_score_value=sh["score"],
                               disease_level="Low", previous_crop="Rice")
    print("Sustainability:", sus["score"], sus["label"])