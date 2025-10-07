from utils.query_helpers import parse_highlight_params


def test_parse_highlight_params_list_and_str():
    # Streamlit-style mapping (str -> list[str])
    params = {'highlight': ['fast']}
    assert parse_highlight_params(params) == 'fast'

    # simple mapping (str)
    params2 = {'highlight': 'eco'}
    assert parse_highlight_params(params2) == 'eco'

    # missing or empty
    assert parse_highlight_params({}) is None
    assert parse_highlight_params({'highlight': []}) is None
