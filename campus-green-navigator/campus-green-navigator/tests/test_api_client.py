import importlib.util
from pathlib import Path


def _load_client_module():
    root = Path(__file__).resolve().parents[1]
    mod_path = root / 'api' / 'client.py'
    spec = importlib.util.spec_from_file_location('api.client', str(mod_path))
    mod = importlib.util.module_from_spec(spec)
    # Ensure data package is available for imports used by client
    data_mod = _load_campus_data()
    import sys
    import types
    pkg = types.ModuleType('data')
    pkg.campus_data = data_mod
    sys.modules['data'] = pkg
    sys.modules['data.campus_data'] = data_mod
    spec.loader.exec_module(mod)
    return mod


def _load_campus_data():
    root = Path(__file__).resolve().parents[1]
    mod_path = root / 'data' / 'campus_data.py'
    spec = importlib.util.spec_from_file_location('data.campus_data', str(mod_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_client_fallback_to_local():
    client = _load_client_module()
    data = _load_campus_data()
    # pick a route from campus data
    r = data.ROUTES[0]
    resp = client.get_route(r['from'], r['to'])
    assert resp['from_loc'] == r['from']
    assert 'fast' in resp and 'eco' in resp
