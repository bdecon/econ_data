"""
bd_CPS_utils.py

Shared utility functions for bd CPS data processing.

These functions are used by multiple notebooks:
- bd_CPS_revisions_reader.ipynb
- bd_CPS_dd.ipynb (future migration)

January 2026
"""

import struct


def id_dtype(size):
    """
    Infer numpy dtype from fixed-width field size.

    This provides basic integer dtype inference based on field width.
    For special cases (strings, floats, specific variables), handle
    separately in the calling code.

    Parameters
    ----------
    size : int or str
        Field width in characters

    Returns
    -------
    str
        Numpy dtype string: 'int8', 'int16', 'int32', or 'intp'

    Examples
    --------
    >>> id_dtype(2)
    'int8'
    >>> id_dtype(4)
    'int16'
    >>> id_dtype(10)
    'int32'
    >>> id_dtype(12)
    'intp'

    Notes
    -----
    Thresholds match bd_CPS_dd.ipynb:
    - int8:  width 1-2
    - int16: width 3-4
    - int32: width 5-10
    - intp:  width 11+

    This does NOT handle special cases like:
    - String fields (HRSAMPLE, HRSERSUF)
    - Float fields (weights)
    - Specific overrides (GTCO, GESTFIPS)

    Those should be handled in the calling code after this function.
    """
    size = int(size)
    if size >= 11:
        return 'intp'
    elif size >= 5:
        return 'int32'
    elif size >= 3:
        return 'int16'
    else:
        return 'int8'


def create_struct_format(var_dict, width_has_suffix=False):
    """
    Create struct format string from variable dictionary.

    Parameters
    ----------
    var_dict : dict
        Dictionary mapping variable names to location info.
        Expected format: {varname: [start, end, width, ...], ...}
        where start/end are 0-indexed byte positions.

    width_has_suffix : bool, default False
        If True, width is already in struct format (e.g., '4s').
        If False, width is an integer and 's' suffix will be added.

    Returns
    -------
    str
        Struct format string (e.g., '4x8s2x4s')

    Examples
    --------
    >>> d = {'VAR1': [0, 4, 4], 'VAR2': [6, 8, 2]}
    >>> create_struct_format(d, width_has_suffix=False)
    '4s2x2s'

    >>> d = {'VAR1': [0, 4, '4s', 'int16'], 'VAR2': [6, 8, '2s', 'int8']}
    >>> create_struct_format(d, width_has_suffix=True)
    '4s2x2s'

    Notes
    -----
    The function handles zero-width gaps (when variables are adjacent)
    by omitting the skip specification rather than including '0x'.
    """
    # Extract positions - handle both 3-element and 4+ element tuples
    positions = list(var_dict.values())
    start = [p[0] for p in positions]
    end = [p[1] for p in positions]
    width = [p[2] for p in positions]

    # Calculate skip bytes between fields
    prev_ends = [0] + end[:-1]
    skips = [s - e for s, e in zip(start, prev_ends)]

    # Build format string
    parts = []
    for skip, w in zip(skips, width):
        # Add skip if needed (omit if zero)
        if skip > 0:
            parts.append(f'{skip}x')
        # Add width - add 's' suffix if needed
        if width_has_suffix:
            parts.append(w)
        else:
            parts.append(f'{w}s')

    return ''.join(parts)


def create_struct_unpacker(var_dict, width_has_suffix=False):
    """
    Create compiled struct unpacker from variable dictionary.

    This is a convenience function that creates the format string
    and returns a compiled unpacker ready for use.

    Parameters
    ----------
    var_dict : dict
        Dictionary mapping variable names to location info.
        Expected format: {varname: [start, end, width, ...], ...}

    width_has_suffix : bool, default False
        If True, width is already in struct format (e.g., '4s').
        If False, width is an integer and 's' suffix will be added.

    Returns
    -------
    callable
        Compiled struct.unpack_from function

    Examples
    --------
    >>> d = {'VAR1': [0, 4, '4s', 'int16'], 'VAR2': [6, 8, '2s', 'int8']}
    >>> unpacker = create_struct_unpacker(d, width_has_suffix=True)
    >>> unpacker(b'TEST  AB')
    (b'TEST', b'AB')
    """
    fmt = create_struct_format(var_dict, width_has_suffix=width_has_suffix)
    return struct.Struct(fmt).unpack_from


def normalize_weights(df, wgt_vars, divisor=10000):
    """
    Normalize CPS weight variables by dividing by a constant.

    CPS weight variables are stored as integers (multiplied by 10,000
    or similar) and need to be converted to their actual values.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing weight columns
    wgt_vars : list of str
        Column names to normalize
    divisor : int or float, default 10000
        Value to divide weights by

    Returns
    -------
    pandas.DataFrame
        DataFrame with normalized weight columns (modified in place)

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'PWSSWGT': [15000000, 12000000]})
    >>> normalize_weights(df, ['PWSSWGT'])
    >>> df['PWSSWGT'].tolist()
    [1500.0, 1200.0]

    Notes
    -----
    This modifies the DataFrame in place and also returns it for
    method chaining convenience.
    """
    df[wgt_vars] = df[wgt_vars] / divisor
    return df
