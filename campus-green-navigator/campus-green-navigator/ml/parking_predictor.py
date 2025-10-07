# ml/parking_predictor.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import joblib
import os
from datetime import datetime, timedelta

def generate_synthetic_parking(days=30, seed=42):
    rng = np.random.default_rng(seed)
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - pd.Timedelta(days=days)
    rows = []
    for d in range(days):
        date = start + timedelta(days=d)
        is_exam = (d % 30) in (10, 11, 12)
        for h in range(24):
            dt = date + timedelta(hours=h)
            base = 0.2
            if 8 <= h <= 10 or 14 <= h <= 16:
                base += 0.5
            if h < 6 or h >= 22:
                base -= 0.15
            if dt.weekday() >= 5:
                base -= 0.25
            if is_exam:
                base -= 0.4
            noise = rng.normal(0, 0.05)
            occ = np.clip(base + noise, 0.0, 1.0)
            rows.append({
                "datetime": dt,
                "hour": h,
                "weekday": dt.weekday(),
                "is_weekend": int(dt.weekday() >= 5),
                "is_exam": int(is_exam),
                "occupancy": occ
            })
    df = pd.DataFrame(rows)
    return df

def add_time_features(df):
    df = df.copy()
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24.0)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24.0)
    df["day_sin"] = np.sin(2 * np.pi * df["weekday"] / 7.0)
    df["day_cos"] = np.cos(2 * np.pi * df["weekday"] / 7.0)
    return df

def train_model(df, model_path="ml/parking_model.joblib"):
    df = add_time_features(df)
    X = df[["hour_sin", "hour_cos", "day_sin", "day_cos", "is_weekend", "is_exam"]]
    y = df["occupancy"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    os.makedirs(os.path.dirname(model_path) or ".", exist_ok=True)
    joblib.dump(model, model_path)
    return {"model_path": model_path, "mae": mae, "model": model}
