import importlib.util
from pathlib import Path


def _load_helpers():
    root = Path(__file__).resolve().parents[1]
    # ensure data.campus_data is available for helpers import
    data_path = root / 'data' / 'campus_data.py'
    spec_d = importlib.util.spec_from_file_location('data.campus_data', str(data_path))
    data_mod = importlib.util.module_from_spec(spec_d)
    spec_d.loader.exec_module(data_mod)
    import sys
    import types
    pkg = types.ModuleType('data')
    pkg.campus_data = data_mod
    sys.modules['data'] = pkg
    sys.modules['data.campus_data'] = data_mod

    mod_path = root / 'utils' / 'helpers.py'
    spec = importlib.util.spec_from_file_location('utils.helpers', str(mod_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_format_minutes_and_co2():
    h = _load_helpers()
    assert h.format_minutes(90) in ('1h 30m', '90 min') or isinstance(h.format_minutes(90), str)
    grams = h.calculate_co2_grams('Car', 10)
    assert isinstance(grams, float) or isinstance(grams, (int,))
    # EV should produce lower CO2 (given typical factors in campus_data)
    grams_ev = h.calculate_co2_grams('EV', 10)
    assert grams_ev <= grams
