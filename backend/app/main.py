from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .predictor import (
    FEATURE_METADATA,
    artifact_path,
    load_metrics,
    metadata,
    predict_case,
)


class PredictRequest(BaseModel):
    age: int = Field(ge=FEATURE_METADATA["age"]["min"], le=FEATURE_METADATA["age"]["max"])
    onset_days: int = Field(
        ge=FEATURE_METADATA["onset_days"]["min"],
        le=FEATURE_METADATA["onset_days"]["max"],
    )
    fac_adm: int = Field(
        ge=FEATURE_METADATA["fac_adm"]["min"],
        le=FEATURE_METADATA["fac_adm"]["max"],
    )
    fma_le_adm: int = Field(
        ge=FEATURE_METADATA["fma_le_adm"]["min"],
        le=FEATURE_METADATA["fma_le_adm"]["max"],
    )
    tis_adm: int = Field(
        ge=FEATURE_METADATA["tis_adm"]["min"],
        le=FEATURE_METADATA["tis_adm"]["max"],
    )


app = FastAPI(
    title="Prognosis Demo API",
    version="0.1.0",
    description="Prediction API for the prognosis demo application.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metadata")
def get_metadata():
    return metadata()


@app.get("/metrics")
def get_metrics():
    metrics = load_metrics()
    if metrics is None:
        raise HTTPException(status_code=404, detail="model_metrics.json not found")
    return metrics


@app.post("/predict")
def post_predict(payload: PredictRequest):
    return predict_case(payload.model_dump())


@app.get("/artifacts/{filename}")
def get_artifact(filename: str):
    try:
        path = artifact_path(filename)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"{error.args[0]} not found") from error
    media_type = "image/png" if Path(filename).suffix == ".png" else "application/octet-stream"
    return FileResponse(path, media_type=media_type)

