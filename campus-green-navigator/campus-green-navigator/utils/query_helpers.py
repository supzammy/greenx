"""Small helpers to parse query params for the app.

These are kept intentionally tiny and pure so they can be unit tested without
running a full Streamlit script.
"""

from typing import Optional, Mapping


def parse_highlight_params(params: Mapping) -> Optional[str]:
    """Return the highlight value from a query-params-like mapping.

    Accepts the form returned by Streamlit's `experimental_get_query_params()`
    which maps str -> list[str]. Also accepts simple dicts produced in tests.
    """
    if not params:
        return None
    val = params.get('highlight')
    if isinstance(val, list) and val:
        return val[0]
    if isinstance(val, str) and val:
        return val
    return None


def parse_highlight_from_streamlit(st) -> Optional[str]:
    """Read query params from a Streamlit object and parse highlight.

    Returns None if the Streamlit API is unavailable.
    """
    try:
        # new API is st.query_params (dict-like), older versions had experimental_get_query_params
        params = None
        if hasattr(st, 'query_params'):
            params = st.query_params
        elif hasattr(st, 'experimental_get_query_params'):
            params = st.experimental_get_query_params()
        return parse_highlight_params(params)
    except Exception:
        return None
