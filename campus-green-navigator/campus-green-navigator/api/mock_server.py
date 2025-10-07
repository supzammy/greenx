from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
from data import campus_data
import pandas as pd
import numpy as np

app = FastAPI(title="Campus Green Navigator - Mock API")


class RouteResponse(BaseModel):
    from_loc: str
    to_loc: str
    fast: Dict[str, Any]
    eco: Dict[str, Any]


@app.get("/route", response_model=RouteResponse)
def get_route(start: str, end: str):
    """Return fast/eco route between campus locations using local campus_data."""
    # try to find matching route
    for r in campus_data.ROUTES:
        if (r["from"] == start and r["to"] == end) or (r["from"] == end and r["to"] == start):
            return {
                "from_loc": start,
                "to_loc": end,
                "fast": r["fast"],
                "eco": r["eco"],
            }
    raise HTTPException(status_code=404, detail="Route not found")


class ParkingRow(BaseModel):
    hour: str
    predicted_occupancy: float
    uncertainty_std: float


@app.get("/parking")
def get_parking(hours: int = 6):
    """Return a simple next-N-hour occupancy forecast using the existing ML code (synthetic data).
    If the model isn't trained/available, return a simple sinusoidal mock.
    """
    try:
        # generate features for next `hours` and call the model if available
        now = pd.Timestamp.now()
        rows = []
        for i in range(hours):
            t = now + pd.Timedelta(hours=i)
            hour = t.hour
            weekday = t.weekday()
            hour_sin = np.sin(2 * np.pi * hour / 24.0)
            hour_cos = np.cos(2 * np.pi * hour / 24.0)
            day_sin = np.sin(2 * np.pi * weekday / 7.0)
            day_cos = np.cos(2 * np.pi * weekday / 7.0)
            is_weekend = int(weekday >= 5)
            is_exam = 0
            rows.append({
                "hour_sin": hour_sin,
                "hour_cos": hour_cos,
                "day_sin": day_sin,
                "day_cos": day_cos,
                "is_weekend": is_weekend,
                "is_exam": is_exam,
                "hour_str": t.strftime("%Y-%m-%d %H:%M"),
            })
        X_df = pd.DataFrame(rows)
        # try to load model
        from joblib import load
        import os

        model_path = os.path.join(os.path.dirname(__file__), "..", "ml", "parking_model.joblib")
        model_path = os.path.abspath(model_path)
        if os.path.exists(model_path):
            model = load(model_path)
            preds = model.predict(X_df[["hour_sin", "hour_cos", "day_sin", "day_cos", "is_weekend", "is_exam"]])
            try:
                all_preds = np.vstack([est.predict(X_df[["hour_sin", "hour_cos", "day_sin", "day_cos", "is_weekend", "is_exam"]].to_numpy()) for est in model.estimators_])
                stds = np.std(all_preds, axis=0)
            except Exception:
                stds = np.zeros_like(preds)
            out = []
            for i in range(len(preds)):
                out.append({
                    "hour": X_df.loc[i, "hour_str"],
                    "predicted_occupancy": float(preds[i]),
                    "uncertainty_std": float(stds[i]),
                })
            return {"hours": out}
        else:
            # fallback sinusoidal mock
            out = []
            for i in range(hours):
                val = 0.5 + 0.4 * np.sin(2 * np.pi * (i % 24) / 24.0)
                out.append({"hour": X_df.loc[i, "hour_str"], "predicted_occupancy": float(val), "uncertainty_std": 0.05})
            return {"hours": out}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
