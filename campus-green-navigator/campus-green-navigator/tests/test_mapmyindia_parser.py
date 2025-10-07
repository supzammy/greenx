import importlib.util
from pathlib import Path
import json


def _load_mapmy_module():
    root = Path(__file__).resolve().parents[1]
    mod_path = root / 'api' / 'mapmyindia.py'
    spec = importlib.util.spec_from_file_location('api.mapmyindia', str(mod_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_directions_parses_sample(monkeypatch):
    mod = _load_mapmy_module()
    sample_path = Path(__file__).resolve().parents[0] / 'data' / 'sample_mapmyindia.json'
    sample = json.loads(sample_path.read_text())

    class DummyResp:
        def __init__(self, j):
            self._j = j

        def raise_for_status(self):
            return None

        def json(self):
            return self._j

    def fake_get(*args, **kwargs):
        return DummyResp(sample)

    monkeypatch.setattr('requests.get', fake_get)

    # ensure env vars are set so _get_token_from_env returns creds
    monkeypatch.setenv('MAPMYINDIA_CLIENT_ID', 'dummy_id')
    monkeypatch.setenv('MAPMYINDIA_CLIENT_SECRET', 'dummy_secret')
    # patch the loaded module's fetch_token (requests.post not used in this test)
    monkeypatch.setattr(mod, 'fetch_token', lambda: 'fake-token')

    # Call with explicit lat,lon so geocode is not required in this unit test
    out = mod.directions('28.6,77.1', '28.602,77.102')
    assert 'fast' in out and 'eco' in out
    assert out['fast']['distance_km'] == 2.5
