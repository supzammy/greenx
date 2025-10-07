import importlib.util
import streamlit as st
from pathlib import Path


def _load_points_module():
    # load module by file path to avoid package import issues under pytest
    root = Path(__file__).resolve().parents[1]
    mod_path = root / 'components' / 'points_system.py'
    spec = importlib.util.spec_from_file_location('components.points_system', str(mod_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def setup_function():
    # Ensure a clean session state before each test
    try:
        st.session_state.clear()
    except Exception:
        # If session_state isn't present, ensure the object exists
        try:
            st.session_state.update({})
        except Exception:
            # Fallback: create attribute
            st.session_state = {}


def test_init_points_sets_defaults():
    mod = _load_points_module()
    # ensure no keys
    if 'points' in st.session_state:
        del st.session_state['points']
    if 'history' in st.session_state:
        del st.session_state['history']

    mod.init_points()
    assert 'points' in st.session_state
    assert isinstance(st.session_state.points, int)
    assert st.session_state.points == 0
    assert 'history' in st.session_state
    assert isinstance(st.session_state.history, list)


def test_calculate_points_basic():
    mod = _load_points_module()
    # CO2 savings 2000 g (2 kg) -> base = 4, extra_minutes=0 -> raw=4 -> min 10 => 10
    pts = mod.calculate_points(2000.0, 0)
    assert pts == 10

    # Large CO2 savings should increase points
    pts2 = mod.calculate_points(10000.0, 0)  # 10 kg -> base 20 -> points 20
    assert pts2 >= 20


def test_add_and_redeem_flow():
    mod = _load_points_module()
    mod.init_points()
    # add some points
    mod.add_points(120, reason='test bonus')
    assert st.session_state.points >= 120
    assert st.session_state.history[-1]['reason'] == 'test bonus'

    # redeem a valid reward
    ok, msg = mod.redeem_reward('Free Coffee')
    assert ok is True
    assert 'Redeemed Free Coffee' in msg or 'Redeemed' in msg

    # redeem invalid reward
    ok2, msg2 = mod.redeem_reward('Nonexistent')
    assert ok2 is False
    assert msg2 == 'Invalid reward.'
