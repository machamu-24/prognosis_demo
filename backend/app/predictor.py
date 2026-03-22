from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


FEATURE_COLUMNS = ["age", "onset_days", "fac_adm", "fma_le_adm", "tis_adm"]
FEATURE_LABELS = {
    "age": "年齢",
    "onset_days": "発症から入院まで日数",
    "fac_adm": "入院時FAC",
    "fma_le_adm": "入院時FMA-LE",
    "tis_adm": "入院時TIS",
}
FEATURE_METADATA = {
    "age": {"label": "年齢", "min": 50, "max": 95, "step": 1},
    "onset_days": {"label": "発症から入院まで日数", "min": 7, "max": 75, "step": 1},
    "fac_adm": {"label": "入院時FAC", "min": 0, "max": 3, "step": 1},
    "fma_le_adm": {"label": "入院時FMA-LE", "min": 0, "max": 34, "step": 1},
    "tis_adm": {"label": "入院時TIS", "min": 0, "max": 23, "step": 1},
}
SAMPLE_CASES = [
    {
        "id": "frail",
        "label": "高齢・重症寄り",
        "values": {
            "age": 87,
            "onset_days": 42,
            "fac_adm": 0,
            "fma_le_adm": 10,
            "tis_adm": 6,
        },
    },
    {
        "id": "borderline",
        "label": "境界症例",
        "values": {
            "age": 72,
            "onset_days": 20,
            "fac_adm": 2,
            "fma_le_adm": 21,
            "tis_adm": 14,
        },
    },
    {
        "id": "promising",
        "label": "改善余地あり",
        "values": {
            "age": 64,
            "onset_days": 14,
            "fac_adm": 3,
            "fma_le_adm": 29,
            "tis_adm": 20,
        },
    },
]
ARTIFACT_FILENAMES = {"model_evaluation.png", "decision_tree.png"}
REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = REPO_ROOT / "dummy_prognosis_data.csv"
LOGISTIC_MODEL_PATH = REPO_ROOT / "logistic_model.joblib"
TREE_MODEL_PATH = REPO_ROOT / "tree_model.joblib"
METRICS_PATH = REPO_ROOT / "model_metrics.json"
TARGET_COLUMN = "independent_walking_discharge"
DATASET_NOTES = [
    "軽症・中等症・重症の3群を混在させています。",
    "年齢、発症から入院まで日数、FAC、FMA-LE、TIS が相関するように生成しています。",
    "退院時歩行自立は複数因子と潜在要因から確率的に生成しています。",
    "測定誤差、少量の欠損、2%のラベル反転を加えて綺麗すぎない PoC データにしています。",
]


def classify_probability(probability: float) -> dict[str, str]:
    if probability < 0.3:
        return {"label": "低い", "tone": "low"}
    if probability < 0.7:
        return {"label": "中間", "tone": "mid"}
    return {"label": "高い", "tone": "high"}


def _to_case_frame(payload: dict) -> pd.DataFrame:
    return pd.DataFrame([{column: payload[column] for column in FEATURE_COLUMNS}])


@lru_cache(maxsize=1)
def load_models():
    return {
        "logistic": joblib.load(LOGISTIC_MODEL_PATH),
        "tree": joblib.load(TREE_MODEL_PATH),
    }


def explain_logistic_case(model, case_df: pd.DataFrame) -> dict:
    imputer = model.named_steps["imputer"]
    scaler = model.named_steps["scaler"]
    classifier = model.named_steps["model"]

    imputed_values = imputer.transform(case_df[FEATURE_COLUMNS])
    scaled_values = scaler.transform(imputed_values)
    coefficients = classifier.coef_[0]
    contributions = scaled_values[0] * coefficients
    intercept = float(classifier.intercept_[0])
    total_logit = intercept + float(contributions.sum())
    total_probability = 1 / (1 + np.exp(-total_logit))

    items = []
    for index, column in enumerate(FEATURE_COLUMNS):
        contribution = float(contributions[index])
        items.append(
            {
                "feature": column,
                "label": FEATURE_LABELS[column],
                "raw_value": float(case_df.iloc[0][column]),
                "scaled_value": float(scaled_values[0][index]),
                "contribution": contribution,
                "direction": "positive" if contribution >= 0 else "negative",
            }
        )

    items.sort(key=lambda item: abs(item["contribution"]), reverse=True)
    return {
        "intercept": intercept,
        "log_odds": total_logit,
        "probability": float(total_probability),
        "items": items,
    }


def predict_case(payload: dict) -> dict:
    models = load_models()
    case_df = _to_case_frame(payload)

    logistic_probability = float(models["logistic"].predict_proba(case_df)[0, 1])
    tree_probability = float(models["tree"].predict_proba(case_df)[0, 1])

    logistic_prediction = int(models["logistic"].predict(case_df)[0])
    tree_prediction = int(models["tree"].predict(case_df)[0])
    explanation = explain_logistic_case(models["logistic"], case_df)

    return {
        "input": payload,
        "logistic": {
            "probability": logistic_probability,
            "prediction": logistic_prediction,
            "band": classify_probability(logistic_probability),
            "explanation": explanation,
        },
        "tree": {
            "probability": tree_probability,
            "prediction": tree_prediction,
            "band": classify_probability(tree_probability),
        },
    }


def load_dataset_overview() -> dict | None:
    if not DATASET_PATH.exists():
        return None

    df = pd.read_csv(DATASET_PATH)
    if df.empty:
        return None

    return {
        "rows": int(len(df)),
        "age_mean": float(df["age"].mean()),
        "age_sd": float(df["age"].std()),
        "onset_days_mean": float(df["onset_days"].mean()),
        "onset_days_sd": float(df["onset_days"].std()),
        "fma_le_mean": float(df["fma_le_adm"].mean()),
        "tis_mean": float(df["tis_adm"].mean()),
        "missing": {
            column: int(df[column].isna().sum())
            for column in ["onset_days", "fma_le_adm", "tis_adm"]
        },
        "notes": DATASET_NOTES,
    }


def load_metrics() -> dict | None:
    if not METRICS_PATH.exists():
        return None
    with METRICS_PATH.open("r", encoding="utf-8") as handle:
        metrics = json.load(handle)

    dataset_overview = load_dataset_overview()
    if dataset_overview is not None:
        metrics["dataset_overview"] = dataset_overview
    return metrics


def metadata() -> dict:
    return {
        "cohort": "入院時FAC 0-3",
        "feature_columns": FEATURE_COLUMNS,
        "features": FEATURE_METADATA,
        "samples": SAMPLE_CASES,
        "artifacts": sorted(ARTIFACT_FILENAMES),
        "disclaimer": "本デモは synthetic data に基づく PoC です。臨床導入には実データ検証が必要です。",
        "dataset_notes": DATASET_NOTES,
    }


def artifact_path(filename: str) -> Path:
    if filename not in ARTIFACT_FILENAMES:
        raise FileNotFoundError(filename)
    path = REPO_ROOT / filename
    if not path.exists():
        raise FileNotFoundError(filename)
    return path
