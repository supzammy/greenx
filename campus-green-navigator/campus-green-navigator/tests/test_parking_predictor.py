import importlib.util
from pathlib import Path
import os


def _load_parking_module():
    root = Path(__file__).resolve().parents[1]
    mod_path = root / 'ml' / 'parking_predictor.py'
    spec = importlib.util.spec_from_file_location('ml.parking_predictor', str(mod_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_generate_and_train(tmp_path):
    mod = _load_parking_module()
    # generate a very small synthetic dataset
    df = mod.generate_synthetic_parking(days=2)
    assert not df.empty

    model_file = tmp_path / 'test_parking_model.joblib'
    info = mod.train_model(df, model_path=str(model_file))
    assert isinstance(info, dict)
    assert 'model_path' in info
    assert os.path.exists(str(model_file))
