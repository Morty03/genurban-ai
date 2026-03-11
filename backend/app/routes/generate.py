# routes/generate.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
import math

router = APIRouter()

# ---------- Request / Response models ----------

class LocationModel(BaseModel):
    name: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    # accept other location fields as-is
    extra: Optional[Dict[str, Any]] = None

class GenerativeSeedModel(BaseModel):
    focus: Optional[str] = None
    weights: Optional[Dict[str, float]] = None
    actions: Optional[List[str]] = None
    notes: Optional[str] = None

class GenerateRequest(BaseModel):
    location: Optional[Dict[str, Any]] = None
    scenario_type: Optional[str] = Field(default="balanced")
    time_frame: Optional[int] = Field(default=10)
    density: Optional[str] = Field(default="medium")
    include_climate: Optional[bool] = Field(default=True)
    include_infrastructure: Optional[bool] = Field(default=True)
    generative_seed: Optional[Dict[str, Any]] = None
    # optional pre-run analysis data (if frontend provides it)
    urban_data: Optional[Dict[str, Any]] = None

class ScenarioOut(BaseModel):
    id: str
    title: str
    summary: str
    timeframe: Optional[int]
    scenario_type: Optional[str]
    density: Optional[str]
    metrics: Dict[str, Any]
    recommendations: List[str]
    seed_used: Optional[Dict[str, Any]] = None

# ---------- Helper utilities ----------

def safe_get_mean(metric_obj):
    """Try to extract a numeric mean/score/value from a metric object"""
    if not metric_obj:
        return None
    for key in ("mean", "score", "value"):
        if isinstance(metric_obj.get(key), (int, float)):
            return metric_obj.get(key)
    # if it's already a number
    if isinstance(metric_obj, (int, float)):
        return metric_obj
    return None

def build_base_metrics_from_urban_data(urban_data: Optional[Dict[str, Any]]):
    """
    Return base metrics in normalized 0..1 range for:
    - urban_density
    - vegetation_cover
    - built_up_area
    If no data present, return defaults.
    """
    defaults = {
        "urban_density": 0.5,
        "vegetation_cover": 0.35,
        "built_up_area": 0.45,
    }
    if not urban_data:
        return defaults

    # Try multiple common shapes
    metrics = urban_data.get("metrics") or urban_data.get("raw") or urban_data
    out = {}
    # urban_density
    ud = metrics.get("urban_density") if isinstance(metrics, dict) else None
    veg = metrics.get("vegetation_cover") if isinstance(metrics, dict) else None
    built = metrics.get("built_up_area") if isinstance(metrics, dict) else None

    ud_mean = safe_get_mean(ud)
    veg_mean = safe_get_mean(veg)
    built_mean = safe_get_mean(built)

    out["urban_density"] = float(ud_mean) if ud_mean is not None else defaults["urban_density"]
    out["vegetation_cover"] = float(veg_mean) if veg_mean is not None else defaults["vegetation_cover"]
    out["built_up_area"] = float(built_mean) if built_mean is not None else defaults["built_up_area"]

    # clamp to [0,1]
    for k in out:
        try:
            out[k] = max(0.0, min(1.0, out[k]))
        except Exception:
            out[k] = defaults[k]
    return out

def merge_weights(defaults: Dict[str, float], incoming: Optional[Dict[str, float]]):
    if not incoming:
        return defaults
    merged = defaults.copy()
    for k in defaults.keys():
        if k in incoming and isinstance(incoming[k], (int, float)):
            merged[k] = float(incoming[k])
    # normalize
    s = sum(merged.values()) or 1.0
    for k in merged:
        merged[k] = merged[k] / s
    return merged

def apply_variant(base_metrics: Dict[str, float], weights: Dict[str, float], variant_multiplier: float):
    """
    Create a new metric dict by applying weights and a variant multiplier:
    - variant_multiplier <1 => conservative (dampen change)
    - 1 => baseline
    - >1 => aggressive (amplify weights)
    We'll interpret weights as importance of protecting or reducing certain metric depending on context.
    To synthesize a scenario metric we will nudge the base metric towards a goal:
      - if weight high for vegetation -> try to increase vegetation
      - if weight high for built_up -> try to reduce impervious (decrease built_up)
      - if weight high for density -> increase density (urban_density)
    This is a heuristic generator for demo purposes.
    """
    # copy baseline
    bm = base_metrics.copy()
    out = {}
    # heuristics: determine direction by comparing to neutral thresholds
    # We'll define desired shifts: for vegetation-weight, push vegetation upward;
    # for built_up-weight, push built_up downward; for density-weight, push density upward.
    for k in ("urban_density", "vegetation_cover", "built_up_area"):
        base = bm.get(k, 0.5)
        w = weights.get("density" if k == "urban_density" else ("vegetation" if k == "vegetation_cover" else "built_up"), 1/3)
        # compute delta: variant_multiplier scales the aggressiveness
        # sign: +ve to increase density/vegetation, -ve to reduce built_up
        if k == "built_up_area":
            # want to reduce built_up when weight increases
            delta = - (w - 0.33) * 0.2 * variant_multiplier
        else:
            delta = (w - 0.33) * 0.2 * variant_multiplier
        # incorporate some bounded change
        newv = base + delta
        newv = max(0.0, min(1.0, newv))
        out[k] = round(newv, 4)
    return out

def recommendations_from_actions(actions: List[str]):
    mapping = {
        "protect_green": "Protect existing green spaces and increase urban tree planting.",
        "urban_tree_planting": "Initiate urban tree planting and community green projects.",
        "promote_infill": "Prioritize infill development and higher-density zoning to reduce sprawl.",
        "sustainable_draining": "Implement sustainable urban drainage to reduce flood risk.",
        "reduce_impervious": "Introduce permeable pavements and reduce impervious surfaces.",
        "limit_sprawl": "Adopt growth boundaries and limit low-density expansion.",
        "allow_higher_density": "Support vertical development and transit-oriented development.",
        "improve_drainage": "Upgrade stormwater infrastructure and retention basins.",
        "protect_green_corridors": "Protect green corridors to maintain biodiversity and reduce heat.",
      }
    recs = []
    for a in actions or []:
        if a in mapping:
            recs.append(mapping[a])
    return recs or ["Follow general sustainable urban planning principles."]

# ---------- Main generate endpoint ----------

@router.post("/scenarios", response_model=Dict[str, List[ScenarioOut]])
async def generate_scenarios(payload: GenerateRequest):
    """
    Generate scenario variants. Accepts optional `generative_seed` to guide generation.
    Returns { "scenarios": [ ... ] }
    """
    # Validate location
    if not payload.location:
        raise HTTPException(status_code=400, detail="location is required for scenario generation")

    # get base metrics from supplied urban_data if present (frontend can send analysis result)
    base_metrics = build_base_metrics_from_urban_data(payload.urban_data)

    # defaults for weights (vegetation, built_up, density)
    default_weights = {"vegetation": 0.33, "built_up": 0.33, "density": 0.34}
    seed = payload.generative_seed or {}
    seed_weights = seed.get("weights") if isinstance(seed.get("weights"), dict) else seed.get("weight") if isinstance(seed.get("weight"), dict) else None
    weights = merge_weights(default_weights, seed_weights)

    # If the seed uses keys "urban_density", "vegetation_cover" etc, normalize mapping
    # already handled above; ensure keys present as expected

    # Create three variants with multipliers: conservative, balanced, aggressive
    variants = [
        {"key": "conservative", "title": "Conservative (low-change)", "mult": 0.6},
        {"key": "balanced", "title": "Balanced (moderate)", "mult": 1.0},
        {"key": "aggressive", "title": "Aggressive (high-change)", "mult": 1.4},
    ]

    scenarios: List[Dict[str, Any]] = []
    actions = seed.get("actions") if isinstance(seed.get("actions"), list) else []
    notes = seed.get("notes") if isinstance(seed.get("notes"), str) else ""

    for v in variants:
        metrics = apply_variant(base_metrics, weights, v["mult"])

        # Simple score: compute an overall sustainability score (higher vegetation, lower built_up => better)
        sustainability_score = (metrics["vegetation_cover"] * 0.6) + ((1 - metrics["built_up_area"]) * 0.3) + ((1 - metrics["urban_density"]) * 0.1)
        sustainability_score = round(max(0.0, min(1.0, sustainability_score)), 3)

        # produce human summary
        summary_parts = []
        if actions:
            summary_parts.append("Focus: " + (seed.get("focus") or payload.scenario_type))
            summary_parts.append("Actions: " + (", ".join(actions)))
        if notes:
            summary_parts.append(notes)

        summary = f"{v['title']}: {summary_parts[0] if summary_parts else payload.scenario_type}"
        if len(summary_parts) > 1:
            summary += " — " + " ".join(summary_parts[1:])

        recs = recommendations_from_actions(actions)

        scenario_obj = {
            "id": str(uuid.uuid4()),
            "title": f"{payload.scenario_type.capitalize()} — {v['title']}",
            "summary": summary,
            "timeframe": payload.time_frame,
            "scenario_type": payload.scenario_type,
            "density": payload.density,
            "metrics": metrics,
            "sustainability_score": sustainability_score,
            "recommendations": recs,
            "seed_used": seed,
        }
        scenarios.append(scenario_obj)

    return {"scenarios": scenarios}
