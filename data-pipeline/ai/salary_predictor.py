"""
Salary Predictor — TechJob AI
Machine Learning module for predicting hidden/negotiable job salaries.

Model: RandomForestRegressor + TargetEncoder (scikit-learn)
Features: title, primary_city, job_level_vi, work_mode, top_skills

Usage:
    Training:   python pipeline/salary_predictor.py --train
    Prediction: python pipeline/salary_predictor.py --predict
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime

import numpy as np
import joblib
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from ai.db_config import sqlalchemy_url

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = sqlalchemy_url()

MODEL_DIR = Path(os.getenv("MODEL_DIR", PROJECT_ROOT / "models"))
MODEL_PATH = MODEL_DIR / "salary_model.joblib"

# Minimum training samples required
MIN_TRAINING_SAMPLES = 30


def _extract_top_skills(skills_json: str, max_skills: int = 5) -> str:
    """Extract top skill names from JSON skills string."""
    if not skills_json:
        return ""
    try:
        if isinstance(skills_json, str):
            skills = json.loads(skills_json)
        else:
            skills = skills_json

        if isinstance(skills, list):
            # Handle both [{skillName: "Python"}] and ["Python"] formats
            names = []
            for s in skills[:max_skills]:
                if isinstance(s, dict):
                    name = s.get("skillName", s.get("skill_name", ""))
                    if name:
                        names.append(name)
                elif isinstance(s, str):
                    names.append(s)
            return ",".join(sorted(names))
    except (json.JSONDecodeError, TypeError):
        pass
    return ""


def _categorize_title(title: str) -> str:
    """Categorize job title into broader groups for better generalization."""
    if not title:
        return "other"
    title_lower = title.lower()

    categories = {
        "backend": ["backend", "back-end", "back end", "server", "api developer"],
        "frontend": ["frontend", "front-end", "front end", "ui developer", "react", "angular", "vue"],
        "fullstack": ["fullstack", "full-stack", "full stack"],
        "mobile": ["mobile", "ios", "android", "flutter", "react native"],
        "data_engineer": ["data engineer", "etl", "data pipeline"],
        "data_analyst": ["data analyst", "business analyst", "bi ", "business intelligence"],
        "data_scientist": ["data scientist", "machine learning", "ml engineer", "ai engineer", "deep learning"],
        "devops": ["devops", "sre", "site reliability", "platform engineer", "infrastructure"],
        "qa_test": ["qa", "test", "quality assurance", "automation test", "sdet"],
        "project_manager": ["project manager", "scrum master", "agile", "delivery manager"],
        "product": ["product manager", "product owner", "product designer"],
        "security": ["security", "cybersecurity", "infosec", "penetration"],
        "cloud": ["cloud", "aws", "azure", "gcp"],
        "database": ["database", "dba", "sql developer"],
        "network": ["network", "system admin", "infrastructure"],
        "designer": ["designer", "ux", "ui/ux"],
        "lead_architect": ["lead", "architect", "principal", "staff engineer", "director", "head of", "cto", "vp"],
    }

    for category, keywords in categories.items():
        for kw in keywords:
            if kw in title_lower:
                return category

    return "other"


# ============================================================
# TRAINING
# ============================================================
def train():
    """Train salary prediction model on jobs with known salaries."""
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import TargetEncoder
    from sklearn.model_selection import cross_val_score
    from sklearn.pipeline import Pipeline

    print(f"{'=' * 60}")
    print(f"  Salary Predictor Training — {datetime.now().isoformat()}")
    print(f"{'=' * 60}")

    engine = create_engine(DATABASE_URL)

    # Fetch training data: jobs with valid salary info
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT f.job_title AS title,
                   COALESCE(f.working_locations->0->>'city', 'unknown') AS primary_city,
                   COALESCE(l.level_name_vi, 'unknown') AS job_level_vi,
                   CASE 
                       WHEN f.type_working_id = 1 THEN 'Toàn thời gian'
                       WHEN f.type_working_id = 2 THEN 'Bán thời gian'
                       WHEN f.type_working_id = 3 THEN 'Hợp đồng'
                       WHEN f.type_working_id = 4 THEN 'Tự do'
                       WHEN f.type_working_id = 5 THEN 'Thực tập'
                       ELSE 'unknown'
                   END AS work_mode,
                   f.skills::text AS skills_json,
                   f.salary_min AS salary_min_vnd,
                   f.salary_max AS salary_max_vnd
            FROM warehouse_warehouse.fact_job_postings f
            LEFT JOIN warehouse_warehouse.dim_job_level l ON f.job_level_id = l.job_level_id
            WHERE f.salary_min IS NOT NULL
              AND f.salary_max IS NOT NULL
              AND f.salary_min > 0
              AND f.salary_max > 0
        """))
        rows = result.fetchall()

    print(f"[INFO] Found {len(rows)} jobs with salary data")

    if len(rows) < MIN_TRAINING_SAMPLES:
        print(f"[WARN] Not enough samples (need {MIN_TRAINING_SAMPLES}). Skipping training.")
        return None

    # Prepare features
    titles = []
    cities = []
    levels = []
    work_modes = []
    top_skills = []
    title_categories = []
    y_min = []
    y_max = []

    for row in rows:
        title, city, level, wm, skills, sal_min, sal_max = row
        titles.append(title or "")
        cities.append(city or "unknown")
        levels.append(level or "unknown")
        work_modes.append(wm or "unknown")
        top_skills.append(_extract_top_skills(skills))
        title_categories.append(_categorize_title(title))
        y_min.append(float(sal_min))
        y_max.append(float(sal_max))

    # Convert to numpy arrays
    X_raw = np.column_stack([title_categories, cities, levels, work_modes, top_skills])
    y_min_arr = np.array(y_min)
    y_max_arr = np.array(y_max)

    # Feature names for reference
    feature_names = ["title_category", "city", "level", "work_mode", "top_skills"]

    # Train model for salary_min
    print("[INFO] Training salary_min model...")
    encoder_min = TargetEncoder(categories="auto", smooth="auto")
    X_encoded_min = encoder_min.fit_transform(X_raw, y_min_arr)

    rf_min = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )
    rf_min.fit(X_encoded_min, y_min_arr)

    # Train model for salary_max
    print("[INFO] Training salary_max model...")
    encoder_max = TargetEncoder(categories="auto", smooth="auto")
    X_encoded_max = encoder_max.fit_transform(X_raw, y_max_arr)

    rf_max = RandomForestRegressor(
        n_estimators=100,
        max_depth=12,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )
    rf_max.fit(X_encoded_max, y_max_arr)

    # Cross-validation scores
    scores_min = cross_val_score(rf_min, X_encoded_min, y_min_arr, cv=5, scoring="r2")
    scores_max = cross_val_score(rf_max, X_encoded_max, y_max_arr, cv=5, scoring="r2")

    print(f"  salary_min R² (5-fold CV): {scores_min.mean():.3f} ± {scores_min.std():.3f}")
    print(f"  salary_max R² (5-fold CV): {scores_max.mean():.3f} ± {scores_max.std():.3f}")

    # Save model bundle
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_bundle = {
        "rf_min": rf_min,
        "rf_max": rf_max,
        "encoder_min": encoder_min,
        "encoder_max": encoder_max,
        "feature_names": feature_names,
        "training_samples": len(rows),
        "r2_min": float(scores_min.mean()),
        "r2_max": float(scores_max.mean()),
        "trained_at": datetime.now().isoformat(),
    }
    joblib.dump(model_bundle, MODEL_PATH)
    print(f"[INFO] Model saved to {MODEL_PATH}")

    print(f"\n{'=' * 60}")
    print(f"  DONE! Training samples: {len(rows)}")
    print(f"{'=' * 60}")

    return model_bundle


# ============================================================
# PREDICTION
# ============================================================
_cached_model = None


def _load_model():
    """Load the trained model (cached in memory)."""
    global _cached_model
    if _cached_model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Salary model not found at {MODEL_PATH}. "
                "Run training first: python pipeline/salary_predictor.py --train"
            )
        _cached_model = joblib.load(MODEL_PATH)
    return _cached_model


def warm_salary_model() -> None:
    """Load the salary model during API startup instead of the first request."""
    _load_model()


def predict_hidden_salary(
    title: str,
    city: str = "unknown",
    level: str = "unknown",
    work_mode: str = "unknown",
    skills: str = "",
) -> dict:
    """
    Predict salary range for a job with hidden/negotiable salary.

    Args:
        title: Job title (e.g., "Senior Backend Developer")
        city: City name (e.g., "Hồ Chí Minh")
        level: Job level (e.g., "Senior", "Junior")
        work_mode: Work mode (office/remote/hybrid)
        skills: Comma-separated skills (e.g., "Python,Java,AWS")

    Returns:
        dict with predicted_min_vnd, predicted_max_vnd, confidence, label
    """
    results = predict_hidden_salaries([{
        "title": title,
        "city": city,
        "level": level,
        "work_mode": work_mode,
        "skills": skills,
    }])
    return results[0] if results else {"error": "Salary prediction failed"}


def predict_hidden_salaries(jobs: list[dict]) -> list[dict]:
    """Predict many salaries in one vectorized model call.

    Loading a job list used to call the Random Forest once per row. A 50-job
    response therefore ran up to 100 separate forest predictions. Encoding and
    predicting the whole matrix once keeps API latency stable.
    """
    if not jobs:
        return []

    try:
        model_bundle = _load_model()
    except FileNotFoundError as exc:
        return [{"error": str(exc)} for _ in jobs]

    rows = []
    for job in jobs:
        rows.append([
            _categorize_title(job.get("title", "")),
            job.get("city") or "unknown",
            job.get("level") or "unknown",
            job.get("work_mode") or "unknown",
            _extract_top_skills(job.get("skills", "")),
        ])

    X_input = np.asarray(rows, dtype=object)
    X_enc_min = model_bundle["encoder_min"].transform(X_input)
    X_enc_max = model_bundle["encoder_max"].transform(X_input)
    predicted_min = model_bundle["rf_min"].predict(X_enc_min)
    predicted_max = model_bundle["rf_max"].predict(X_enc_max)

    avg_r2 = (model_bundle["r2_min"] + model_bundle["r2_max"]) / 2
    confidence = round(max(0, min(1, avg_r2)), 2)
    model_info = {
        "training_samples": model_bundle["training_samples"],
        "trained_at": model_bundle["trained_at"],
    }

    results = []
    for pred_min, pred_max in zip(predicted_min, predicted_max):
        if pred_min > pred_max:
            pred_min, pred_max = pred_max, pred_min

        pred_min = max(0, round(pred_min / 1_000_000) * 1_000_000)
        pred_max = max(pred_min, round(pred_max / 1_000_000) * 1_000_000)
        results.append({
            "predicted_min_vnd": int(pred_min),
            "predicted_max_vnd": int(pred_max),
            "predicted_min_trieu": round(pred_min / 1_000_000, 1),
            "predicted_max_trieu": round(pred_max / 1_000_000, 1),
            "confidence": confidence,
            "label": "AI Predicted",
            "model_info": model_info,
        })

    return results


# Airflow-callable entry point
def run():
    """Entry point for Airflow DAG task."""
    train()


if __name__ == "__main__":
    import sys

    if "--predict" in sys.argv:
        result = predict_hidden_salary(
            title="Senior Backend Developer",
            city="Hồ Chí Minh",
            level="Senior",
            work_mode="hybrid",
            skills="Python,Java,AWS",
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        train()
