"""
CPS-O*NET Integration Module

Add occupation-level variables to CPS data based on O*NET job characteristics:
- Physically demanding (PD) and difficult working conditions (DWC)
- Telework feasibility (DFLP methodology)
- AI exposure (Pew Research methodology)
- Job Zone / education requirements (NY Fed methodology)

Usage:
    import pandas as pd
    from cps_onet import add_occ_pd_dwc, add_occ_telework, add_occ_ai, add_occ_jz

    cps = pd.read_feather('cps2015.ft')
    cps = add_occ_pd_dwc(cps, year=2015)
    cps = add_occ_telework(cps, year=2015)
    cps = add_occ_ai(cps, year=2015)
    cps = add_occ_jz(cps, year=2015)
    # Adds columns: OCCPD, OCCHPD, OCCDWC, OCCTLWK, OCCAI, OCCJZ

Variables:
    OCCPD   - Any physical demands (0-1 proportion)
    OCCHPD  - High physical demands (0-1 proportion)
    OCCDWC  - Difficult working conditions (0-1 proportion)
    OCCTLWK - Telework feasibility (0-1 proportion, DFLP methodology)
    OCCAI   - AI exposure (0-1 score, Pew Research methodology)
    OCCJZ   - Job Zone (1-5 scale, education/preparation level)

Values represent the employment-weighted proportion of O*NET subcodes meeting
criteria. Use 1.0 = definitely classified, 0.0 = definitely not, intermediate
values = ambiguous. Create binary variables with: (OCCPD > 0.5).astype(int)

For OCCAI, higher values indicate greater AI exposure. Use percentiles for
classification: top 25% = most exposed, bottom 25% = least exposed.

For OCCJZ, use to compute education mismatch or derive BA requirement:
    cps['BA_REQUIRED'] = (cps['OCCJZ'] >= 4).astype(int)

See also:
    - pd_dwc_classifier.py: Generate PD/DWC lookup tables from O*NET data
    - telework_classifier.py: Generate telework lookup tables from O*NET data
    - ai_classifier.py: Generate AI exposure lookup tables from O*NET data
    - jz_classifier.py: Generate Job Zone lookup tables from O*NET data
    - CLAUDE.md: Project documentation and methodology
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Default paths
DEFAULT_LOOKUP_PATH = Path(__file__).parent / 'output'


def _latest_annual_file(prefix, lookup_path):
    """Find the latest available annual lookup file for a given prefix.

    Parameters
    ----------
    prefix : str
        File prefix (e.g. 'telework', 'ai', 'jz')
    lookup_path : Path or str
        Directory containing lookup files

    Returns
    -------
    str : Filename of latest available file
    """
    lookup_path = Path(lookup_path)
    files = sorted(lookup_path.glob(f'{prefix}_[0-9][0-9][0-9][0-9].csv'))
    if not files:
        raise FileNotFoundError(
            f"No {prefix} lookup files found in {lookup_path}")
    return files[-1].name


def get_occ_var(year):
    """Get occupation variable name for a given CPS year.

    Note: bd CPS provides crosswalked OCC00 for 2000-2002, so we use that
    instead of OCC90 for those years.
    """
    if year <= 1999:
        return 'OCC90'
    elif year <= 2010:
        return 'OCC00'
    elif year <= 2019:
        return 'OCC10'
    else:
        return 'OCC18'


def get_lookup_file(year, lookup_path=None):
    """Get PD/DWC lookup file for a given CPS year.

    Prefers annual lookup files (pd_dwc_YYYY.csv) which use year-specific
    OEWS employment weights. Falls back to period-based files if annual
    files are not available.

    Parameters
    ----------
    year : int
        CPS data year
    lookup_path : Path, optional
        Path to lookup directory (used to check file existence)

    Returns
    -------
    str : Filename of lookup table to use
    """
    if year <= 1999:
        return 'pd_dwc_occ90.csv'  # Not yet available

    # Try annual file first
    annual_file = f'pd_dwc_{year}.csv'
    if lookup_path is not None:
        if (Path(lookup_path) / annual_file).exists():
            return annual_file

    # Fall back to period-based files
    if year <= 2010:
        return 'pd_dwc_occ00.csv'
    elif year <= 2019:
        return 'pd_dwc_occ10.csv'
    else:
        return 'pd_dwc_occ18.csv'


def add_occ_pd_dwc(df, year=None, lookup_path=None):
    """
    Add PD/DWC classification variables to CPS DataFrame.

    Uses annual lookup tables (pd_dwc_YYYY.csv) with year-specific OEWS
    employment weights when available. Falls back to period-based lookup
    tables if annual files don't exist.

    Parameters
    ----------
    df : DataFrame
        CPS data with occupation code variable (OCC00, OCC10, or OCC18)
    year : int, optional
        CPS data year. If not provided, infers from YEAR column or uses OCC10.
        Determines which lookup table and occupation variable to use.
    lookup_path : str or Path, optional
        Path to directory containing PD/DWC lookup files.
        Defaults to 'output/' subdirectory of this module.

    Returns
    -------
    DataFrame with additional columns:
        - OCCPD: Any physical demands (0-1 proportion)
        - OCCHPD: High physical demands (0-1 proportion)
        - OCCDWC: Difficult working conditions (0-1 proportion)

    Values represent the employment-weighted proportion of O*NET subcodes
    meeting criteria:
        - 1.0 = definitely classified (all subcodes agree)
        - 0.0 = definitely NOT classified
        - 0.0 < x < 1.0 = ambiguous (proportion of employment meeting criteria)

    To create binary variables, use a threshold:
        cps['PD_binary'] = (cps['OCCPD'] > 0.5).astype(int)  # majority
        cps['PD_binary'] = (cps['OCCPD'] > 0).astype(int)    # any

    Examples
    --------
    >>> cps = pd.read_feather('cps2015.ft')
    >>> cps = add_occ_pd_dwc(cps, year=2015)
    >>> cps['OCCPD'].mean()  # Average PD proportion
    0.47
    """
    df = df.copy()

    # Determine year
    if year is None:
        if 'YEAR' in df.columns:
            year = df['YEAR'].mode().iloc[0]
        else:
            year = 2015  # Default to OCC10

    # Get occupation variable
    occ_var = get_occ_var(year)

    if lookup_path is None:
        lookup_path = DEFAULT_LOOKUP_PATH
    lookup_path = Path(lookup_path)

    # Get lookup file (prefers annual if available)
    lookup_file = get_lookup_file(year, lookup_path)

    # Check occupation variable exists
    if occ_var not in df.columns:
        available = [c for c in df.columns if 'OCC' in c.upper()]
        raise ValueError(f"Occupation variable '{occ_var}' not found. "
                        f"Available: {available}")

    # Load lookup table
    lookup_file_path = lookup_path / lookup_file
    if not lookup_file_path.exists():
        raise FileNotFoundError(f"Lookup file not found: {lookup_file_path}")

    lookup = pd.read_csv(lookup_file_path)

    # Prepare occupation codes for merge (without modifying original column)
    occ_values = df[occ_var].astype(str) if hasattr(df[occ_var], 'cat') else df[occ_var]
    df['_occ_merge'] = pd.to_numeric(occ_values, errors='coerce')

    # Merge lookup
    lookup = lookup.rename(columns={'census_code': '_occ_merge'})
    merge_cols = ['_occ_merge', 'high_pd', 'any_pd', 'dwc']
    df = df.merge(lookup[merge_cols], on='_occ_merge', how='left')

    # Rename to final variable names
    df['OCCPD'] = df['any_pd']
    df['OCCHPD'] = df['high_pd']
    df['OCCDWC'] = df['dwc']

    # Clean up
    df = df.drop(columns=['_occ_merge', 'high_pd', 'any_pd', 'dwc'])

    return df


def get_telework_lookup_file(year, lookup_path=None):
    """Get telework lookup file for a given CPS year.

    Prefers annual lookup files (telework_YYYY.csv) which use year-specific
    OEWS employment weights. Falls back to the latest available file if the
    requested year is not yet available.

    Parameters
    ----------
    year : int
        CPS data year
    lookup_path : Path, optional
        Path to lookup directory

    Returns
    -------
    str : Filename of telework lookup table to use
    """
    telework_file = f'telework_{year}.csv'
    if lookup_path is not None:
        if (Path(lookup_path) / telework_file).exists():
            return telework_file
        # Fall back to latest available file
        return _latest_annual_file('telework', lookup_path)

    return telework_file


def add_occ_telework(df, year=None, lookup_path=None):
    """
    Add telework feasibility variable to CPS DataFrame.

    Uses DFLP methodology from Dey, Frazis, Loewenstein, Piccone (2021)
    in the BLS Monthly Labor Review, which refined the Dingel & Neiman (2020)
    classification based on actual COVID-era telework patterns.

    Parameters
    ----------
    df : DataFrame
        CPS data with occupation code variable (OCC00, OCC10, or OCC18)
    year : int, optional
        CPS data year. If not provided, infers from YEAR column or uses 2015.
    lookup_path : str or Path, optional
        Path to directory containing telework lookup files.
        Defaults to 'output/' subdirectory of this module.

    Returns
    -------
    DataFrame with additional column:
        - OCCTLWK: Telework feasibility (0-1 proportion)

    Values represent the employment-weighted proportion of O*NET subcodes
    classified as suitable for telework:
        - 1.0 = definitely suitable (all subcodes agree)
        - 0.0 = definitely NOT suitable
        - 0.0 < x < 1.0 = ambiguous (proportion suitable)

    To create binary variable:
        cps['TELEWORK'] = (cps['OCCTLWK'] > 0.5).astype(int)

    Examples
    --------
    >>> cps = pd.read_feather('cps2020.ft')
    >>> cps = add_occ_telework(cps, year=2020)
    >>> cps['OCCTLWK'].mean()  # Average telework feasibility
    0.35
    """
    df = df.copy()

    # Determine year
    if year is None:
        if 'YEAR' in df.columns:
            year = df['YEAR'].mode().iloc[0]
        else:
            year = 2015

    # Get occupation variable
    occ_var = get_occ_var(year)

    if lookup_path is None:
        lookup_path = DEFAULT_LOOKUP_PATH
    lookup_path = Path(lookup_path)

    # Get telework lookup file
    lookup_file = get_telework_lookup_file(year, lookup_path)

    # Check occupation variable exists
    if occ_var not in df.columns:
        available = [c for c in df.columns if 'OCC' in c.upper()]
        raise ValueError(f"Occupation variable '{occ_var}' not found. "
                        f"Available: {available}")

    # Load lookup table
    lookup_file_path = lookup_path / lookup_file
    if not lookup_file_path.exists():
        raise FileNotFoundError(f"Telework lookup file not found: {lookup_file_path}")

    lookup = pd.read_csv(lookup_file_path)

    # Prepare occupation codes for merge (without modifying original column)
    occ_values = df[occ_var].astype(str) if hasattr(df[occ_var], 'cat') else df[occ_var]
    df['_occ_merge'] = pd.to_numeric(occ_values, errors='coerce')

    # Merge lookup
    lookup = lookup.rename(columns={'census_code': '_occ_merge'})
    df = df.merge(lookup[['_occ_merge', 'telework']], on='_occ_merge', how='left')

    # Rename to final variable name
    df['OCCTLWK'] = df['telework']

    # Clean up
    df = df.drop(columns=['_occ_merge', 'telework'])

    return df


def get_ai_lookup_file(year, lookup_path=None):
    """Get AI exposure lookup file for a given CPS year.

    Prefers annual lookup files (ai_YYYY.csv) which use year-specific
    OEWS employment weights. Falls back to the latest available file if the
    requested year is not yet available.

    Parameters
    ----------
    year : int
        CPS data year
    lookup_path : Path, optional
        Path to lookup directory

    Returns
    -------
    str : Filename of AI exposure lookup table to use
    """
    ai_file = f'ai_{year}.csv'
    if lookup_path is not None:
        if (Path(lookup_path) / ai_file).exists():
            return ai_file
        # Fall back to latest available file
        return _latest_annual_file('ai', lookup_path)

    return ai_file


def add_occ_ai(df, year=None, lookup_path=None):
    """
    Add AI exposure variable to CPS DataFrame.

    Uses Pew Research Center methodology (July 2023) which classifies O*NET
    work activities into high, medium, and low AI exposure categories, then
    calculates the relative importance of high-exposure activities.

    Parameters
    ----------
    df : DataFrame
        CPS data with occupation code variable (OCC00, OCC10, or OCC18)
    year : int, optional
        CPS data year. If not provided, infers from YEAR column or uses 2015.
    lookup_path : str or Path, optional
        Path to directory containing AI exposure lookup files.
        Defaults to 'output/' subdirectory of this module.

    Returns
    -------
    DataFrame with additional column:
        - OCCAI: AI exposure score (0-1, higher = more exposed)

    The score represents the relative importance of high-exposure work
    activities in each occupation. Use percentile rankings for classification:
        - Top 25%: most exposed to AI
        - Bottom 25%: least exposed to AI

    Examples
    --------
    >>> cps = pd.read_feather('cps2020.ft')
    >>> cps = add_occ_ai(cps, year=2020)
    >>> cps['OCCAI'].mean()  # Average AI exposure
    0.35
    >>> # Create binary variable using 75th percentile as cutoff
    >>> threshold = cps['OCCAI'].quantile(0.75)
    >>> cps['HIGH_AI'] = (cps['OCCAI'] > threshold).astype(int)
    """
    df = df.copy()

    # Determine year
    if year is None:
        if 'YEAR' in df.columns:
            year = df['YEAR'].mode().iloc[0]
        else:
            year = 2015

    # Get occupation variable
    occ_var = get_occ_var(year)

    if lookup_path is None:
        lookup_path = DEFAULT_LOOKUP_PATH
    lookup_path = Path(lookup_path)

    # Get AI lookup file
    lookup_file = get_ai_lookup_file(year, lookup_path)

    # Check occupation variable exists
    if occ_var not in df.columns:
        available = [c for c in df.columns if 'OCC' in c.upper()]
        raise ValueError(f"Occupation variable '{occ_var}' not found. "
                        f"Available: {available}")

    # Load lookup table
    lookup_file_path = lookup_path / lookup_file
    if not lookup_file_path.exists():
        raise FileNotFoundError(f"AI exposure lookup file not found: {lookup_file_path}")

    lookup = pd.read_csv(lookup_file_path)

    # Prepare occupation codes for merge (without modifying original column)
    occ_values = df[occ_var].astype(str) if hasattr(df[occ_var], 'cat') else df[occ_var]
    df['_occ_merge'] = pd.to_numeric(occ_values, errors='coerce')

    # Merge lookup
    lookup = lookup.rename(columns={'census_code': '_occ_merge'})
    df = df.merge(lookup[['_occ_merge', 'ai_exposure']], on='_occ_merge', how='left')

    # Rename to final variable name
    df['OCCAI'] = df['ai_exposure']

    # Clean up
    df = df.drop(columns=['_occ_merge', 'ai_exposure'])

    return df


def get_jz_lookup_file(year, lookup_path=None):
    """Get Job Zone lookup file for a given CPS year.

    Prefers annual lookup files (jz_YYYY.csv) which use year-specific
    OEWS employment weights. Falls back to the latest available file if the
    requested year is not yet available.

    Parameters
    ----------
    year : int
        CPS data year
    lookup_path : Path, optional
        Path to lookup directory

    Returns
    -------
    str : Filename of Job Zone lookup table to use
    """
    jz_file = f'jz_{year}.csv'
    if lookup_path is not None:
        if (Path(lookup_path) / jz_file).exists():
            return jz_file
        # Fall back to latest available file
        return _latest_annual_file('jz', lookup_path)

    return jz_file


def add_occ_jz(df, year=None, lookup_path=None):
    """
    Add Job Zone variable to CPS DataFrame.

    Uses O*NET Job Zones to classify occupations by preparation level
    (education, experience, training). Enables education mismatch analysis
    following NY Fed College Labor Market methodology.

    Job Zone Definitions:
    - Zone 1: Little or no preparation (some HS)
    - Zone 2: Some preparation (HS diploma)
    - Zone 3: Medium preparation (vocational/associate's)
    - Zone 4: Considerable preparation (bachelor's)
    - Zone 5: Extensive preparation (graduate degree)

    Parameters
    ----------
    df : DataFrame
        CPS data with occupation code variable (OCC00, OCC10, or OCC18)
    year : int, optional
        CPS data year. If not provided, infers from YEAR column or uses 2015.
    lookup_path : str or Path, optional
        Path to directory containing Job Zone lookup files.
        Defaults to 'output/' subdirectory of this module.

    Returns
    -------
    DataFrame with additional column:
        - OCCJZ: Job Zone (1-5 scale, may be fractional for mixed occupations)

    To derive binary BA requirement:
        cps['BA_REQUIRED'] = (cps['OCCJZ'] >= 4).astype(int)

    To compute education mismatch:
        edu_to_jz = {'LTHS': 1, 'HS': 2, 'SC': 3, 'COLL': 4, 'ADV': 5}
        cps['WORKER_JZ'] = cps['EDUC'].map(edu_to_jz)
        cps['EDUMISMATCH'] = cps['WORKER_JZ'] - cps['OCCJZ']
        # Positive = overqualified, Negative = underqualified

    Examples
    --------
    >>> cps = pd.read_feather('cps2020.ft')
    >>> cps = add_occ_jz(cps, year=2020)
    >>> cps['OCCJZ'].mean()  # Average Job Zone
    3.03
    >>> # Underemployment rate for BA holders
    >>> ba_holders = cps[cps['EDUC'].isin(['COLL', 'ADV'])]
    >>> (ba_holders['OCCJZ'] < 4).mean()
    0.32
    """
    df = df.copy()

    # Determine year
    if year is None:
        if 'YEAR' in df.columns:
            year = df['YEAR'].mode().iloc[0]
        else:
            year = 2015

    # Get occupation variable
    occ_var = get_occ_var(year)

    if lookup_path is None:
        lookup_path = DEFAULT_LOOKUP_PATH
    lookup_path = Path(lookup_path)

    # Get JZ lookup file
    lookup_file = get_jz_lookup_file(year, lookup_path)

    # Check occupation variable exists
    if occ_var not in df.columns:
        available = [c for c in df.columns if 'OCC' in c.upper()]
        raise ValueError(f"Occupation variable '{occ_var}' not found. "
                        f"Available: {available}")

    # Load lookup table
    lookup_file_path = lookup_path / lookup_file
    if not lookup_file_path.exists():
        raise FileNotFoundError(f"Job Zone lookup file not found: {lookup_file_path}")

    lookup = pd.read_csv(lookup_file_path)

    # Prepare occupation codes for merge (without modifying original column)
    occ_values = df[occ_var].astype(str) if hasattr(df[occ_var], 'cat') else df[occ_var]
    df['_occ_merge'] = pd.to_numeric(occ_values, errors='coerce')

    # Merge lookup
    lookup = lookup.rename(columns={'census_code': '_occ_merge'})
    df = df.merge(lookup[['_occ_merge', 'job_zone']], on='_occ_merge', how='left')

    # Rename to final variable name
    df['OCCJZ'] = df['job_zone']

    # Clean up
    df = df.drop(columns=['_occ_merge', 'job_zone'])

    return df


def add_all_occ_vars(df, year=None, lookup_path=None):
    """
    Add all O*NET-derived occupation variables to CPS DataFrame.

    Convenience function that adds PD/DWC, telework, AI exposure, and Job Zone
    variables.

    Parameters
    ----------
    df : DataFrame
        CPS data with occupation code variable
    year : int, optional
        CPS data year
    lookup_path : str or Path, optional
        Path to lookup directory

    Returns
    -------
    DataFrame with columns: OCCPD, OCCHPD, OCCDWC, OCCTLWK, OCCAI, OCCJZ
    """
    df = add_occ_pd_dwc(df, year=year, lookup_path=lookup_path)
    df = add_occ_telework(df, year=year, lookup_path=lookup_path)
    df = add_occ_ai(df, year=year, lookup_path=lookup_path)
    df = add_occ_jz(df, year=year, lookup_path=lookup_path)
    return df


# Legacy function for backwards compatibility
def add_pd_dwc(df, year=None, threshold=0.0, lookup_path=None):
    """
    Legacy function - use add_occ_pd_dwc() instead.

    This function is kept for backwards compatibility but is deprecated.
    """
    import warnings
    warnings.warn("add_pd_dwc() is deprecated. Use add_occ_pd_dwc() instead.",
                  DeprecationWarning, stacklevel=2)

    df = add_occ_pd_dwc(df, year=year, lookup_path=lookup_path)

    # Create binary variables for backwards compatibility
    df['PD_HIGH'] = (df['OCCHPD'] > threshold).astype('Int8')
    df['PD_ANY'] = (df['OCCPD'] > threshold).astype('Int8')
    df['DWC'] = (df['OCCDWC'] > threshold).astype('Int8')
    df['PD_DWC'] = ((df['OCCPD'] > threshold) | (df['OCCDWC'] > threshold)).astype('Int8')

    # Add proportion columns with old names
    df['PD_HIGH_PROP'] = df['OCCHPD']
    df['PD_ANY_PROP'] = df['OCCPD']
    df['DWC_PROP'] = df['OCCDWC']
    df['PD_DWC_PROP'] = np.maximum(df['OCCPD'].fillna(0), df['OCCDWC'].fillna(0))

    return df


def pd_dwc_summary(df, weight_col='BASICWGT', employed_only=True, age_min=None, threshold=0.5):
    """
    Calculate weighted PD/DWC estimates from CPS data with PD/DWC variables.

    Parameters
    ----------
    df : DataFrame
        CPS data with OCCPD, OCCHPD, OCCDWC columns
    weight_col : str, default 'BASICWGT'
        Column to use for weighting
    employed_only : bool, default True
        If True, filter to employed workers only
    age_min : int, optional
        If provided, filter to workers age >= age_min
    threshold : float, default 0.5
        Threshold for converting proportions to binary (> threshold = 1)

    Returns
    -------
    dict with weighted estimates for each PD/DWC metric (as percentages)
    """
    df = df.copy()

    # Apply filters
    if employed_only and 'LFS' in df.columns:
        df = df[df['LFS'] == 'Employed']
    if age_min is not None and 'AGE' in df.columns:
        df = df[df['AGE'] >= age_min]

    # Calculate weighted estimates
    total_wt = df[weight_col].sum()
    results = {}

    # Map new variable names
    var_map = {'OCCHPD': 'High PD', 'OCCPD': 'Any PD', 'OCCDWC': 'DWC'}

    for var, label in var_map.items():
        if var in df.columns:
            binary = (df[var] > threshold).astype(int)
            results[label] = (binary * df[weight_col]).sum() / total_wt * 100
        else:
            results[label] = np.nan

    # Add PD or DWC
    if 'OCCPD' in df.columns and 'OCCDWC' in df.columns:
        pd_or_dwc = ((df['OCCPD'] > threshold) | (df['OCCDWC'] > threshold)).astype(int)
        results['PD or DWC'] = (pd_or_dwc * df[weight_col]).sum() / total_wt * 100

    return results


# Convenience function for quick analysis
def analyze_pd_dwc(cps_path, year, threshold=0.5, age_min=58):
    """
    Quick analysis of PD/DWC for a CPS year.

    Parameters
    ----------
    cps_path : str or Path
        Path to CPS feather file
    year : int
        CPS data year
    threshold : float
        PD/DWC classification threshold for summary
    age_min : int
        Minimum age for analysis

    Returns
    -------
    dict with sample size and weighted estimates
    """
    cps = pd.read_feather(cps_path)
    cps = add_occ_pd_dwc(cps, year=year)

    # Filter
    mask = (cps['LFS'] == 'Employed') & (cps['AGE'] >= age_min)
    workers = cps[mask]

    results = pd_dwc_summary(workers, employed_only=False, threshold=threshold)
    results['n_workers'] = len(workers)
    results['year'] = year
    results['threshold'] = threshold
    results['age_min'] = age_min

    return results


# Education to Job Zone mapping
EDUC_TO_JZ = {'LTHS': 1, 'HS': 2, 'SC': 3, 'COLL': 4, 'ADV': 5}


def calc_overqualified_rate(df, weight_col='BASICWGT', educ_filter=None,
                            age_min=None, age_max=None, employed_only=True,
                            method='mismatch', ba_threshold=4.0):
    """
    Calculate weighted overqualification rate for CPS workers.

    Computes the share of workers who are overqualified for their occupation
    based on comparing their education level to the occupation's Job Zone.

    Parameters
    ----------
    df : DataFrame
        CPS data with OCCJZ and EDUC columns. Should be pre-filtered to
        desired month/sample if needed.
    weight_col : str, default 'BASICWGT'
        Column to use for weighting. Use 'PWORWGT' for ORG sample.
    educ_filter : list, optional
        Education levels to include. Default None includes all workers.
        Common filters:
        - ['COLL', 'ADV'] for BA+ holders (NY Fed recent graduate analysis)
        - ['COLL'] for BA only (excludes graduate degrees)
        - ['ADV'] for graduate degree holders only
    age_min : int, optional
        Minimum age (inclusive). Use 22 for recent graduate analysis.
    age_max : int, optional
        Maximum age (inclusive). Use 27 for recent graduate analysis.
    employed_only : bool, default True
        If True, filter to employed workers only (LFS == 'Employed')
    method : str, default 'mismatch'
        How to define overqualification:
        - 'mismatch': WORKER_JZ > OCCJZ (any positive mismatch)
        - 'underemployed': OCCJZ < ba_threshold (job doesn't require BA)
        - 'severe': WORKER_JZ - OCCJZ >= 2 (2+ zone gap)
    ba_threshold : float, default 4.0
        For method='underemployed', threshold below which job is non-college.
        Use 4.0 for strict BA requirement, 3.5 for more lenient.

    Returns
    -------
    dict with:
        - rate: Weighted overqualification rate (0-1)
        - rate_pct: Rate as percentage
        - n_obs: Unweighted observation count
        - n_overqual: Unweighted count of overqualified workers
        - weighted_n: Weighted total
        - weighted_overqual: Weighted overqualified count
        - mean_mismatch: Average education-occupation mismatch
        - mean_occjz: Average Job Zone of occupations

    Examples
    --------
    >>> cps = pd.read_feather('cps2025.ft')
    >>> # NY Fed-style underemployment for recent BA graduates
    >>> result = calc_overqualified_rate(
    ...     cps[cps['MONTH'] == 9],
    ...     educ_filter=['COLL', 'ADV'],
    ...     age_min=22, age_max=27,
    ...     method='underemployed'
    ... )
    >>> print(f"Underemployment rate: {result['rate_pct']:.1f}%")
    Underemployment rate: 42.1%

    >>> # General overqualification for all workers
    >>> result = calc_overqualified_rate(cps, method='mismatch')
    >>> print(f"Overqualified: {result['rate_pct']:.1f}%")

    >>> # Severe mismatch (2+ zone gap)
    >>> result = calc_overqualified_rate(
    ...     cps, educ_filter=['COLL', 'ADV'], method='severe'
    ... )
    """
    df = df.copy()

    # Validate required columns
    if 'OCCJZ' not in df.columns:
        raise ValueError("OCCJZ column not found. Run add_occ_jz() first.")
    if 'EDUC' not in df.columns:
        raise ValueError("EDUC column not found.")

    # Apply filters
    if employed_only and 'LFS' in df.columns:
        df = df[df['LFS'] == 'Employed']

    if educ_filter is not None:
        # Handle categorical EDUC column
        educ_vals = df['EDUC'].astype(str)
        df = df[educ_vals.isin(educ_filter)]

    if age_min is not None and 'AGE' in df.columns:
        df = df[df['AGE'] >= age_min]

    if age_max is not None and 'AGE' in df.columns:
        df = df[df['AGE'] <= age_max]

    # Drop rows with missing OCCJZ or weight
    df = df.dropna(subset=['OCCJZ', weight_col])

    if len(df) == 0:
        return {
            'rate': np.nan,
            'rate_pct': np.nan,
            'n_obs': 0,
            'n_overqual': 0,
            'weighted_n': 0,
            'weighted_overqual': 0,
            'mean_mismatch': np.nan,
            'mean_occjz': np.nan,
        }

    # Compute worker's Job Zone from education
    df['_worker_jz'] = df['EDUC'].astype(str).map(EDUC_TO_JZ)

    # Compute mismatch
    df['_mismatch'] = df['_worker_jz'] - df['OCCJZ']

    # Define overqualified based on method
    if method == 'mismatch':
        # Any positive mismatch (worker's education > job requirement)
        df['_overqual'] = (df['_mismatch'] > 0).astype(int)
    elif method == 'underemployed':
        # NY Fed style: job doesn't require BA (OCCJZ < threshold)
        df['_overqual'] = (df['OCCJZ'] < ba_threshold).astype(int)
    elif method == 'severe':
        # Severe mismatch: 2+ zone gap
        df['_overqual'] = (df['_mismatch'] >= 2).astype(int)
    else:
        raise ValueError(f"Unknown method: {method}. Use 'mismatch', 'underemployed', or 'severe'.")

    # Calculate weighted statistics
    weights = df[weight_col]
    total_weight = weights.sum()
    overqual_weight = (df['_overqual'] * weights).sum()

    rate = overqual_weight / total_weight if total_weight > 0 else np.nan

    # Weighted mean mismatch
    mean_mismatch = (df['_mismatch'] * weights).sum() / total_weight if total_weight > 0 else np.nan
    mean_occjz = (df['OCCJZ'] * weights).sum() / total_weight if total_weight > 0 else np.nan

    return {
        'rate': rate,
        'rate_pct': rate * 100 if not np.isnan(rate) else np.nan,
        'n_obs': len(df),
        'n_overqual': df['_overqual'].sum(),
        'weighted_n': total_weight,
        'weighted_overqual': overqual_weight,
        'mean_mismatch': mean_mismatch,
        'mean_occjz': mean_occjz,
    }


def calc_mismatch_distribution(df, weight_col='BASICWGT', educ_filter=None,
                               age_min=None, age_max=None, employed_only=True):
    """
    Calculate weighted distribution of education-occupation mismatch.

    Returns the share of workers at each mismatch level, from severely
    underqualified (-4) to severely overqualified (+4).

    Parameters
    ----------
    df : DataFrame
        CPS data with OCCJZ and EDUC columns
    weight_col : str, default 'BASICWGT'
        Column to use for weighting
    educ_filter : list, optional
        Education levels to include
    age_min, age_max : int, optional
        Age range filter
    employed_only : bool, default True
        Filter to employed workers

    Returns
    -------
    DataFrame with mismatch levels and weighted shares

    Examples
    --------
    >>> cps = pd.read_feather('cps2025.ft')
    >>> dist = calc_mismatch_distribution(cps[cps['MONTH'] == 9])
    >>> print(dist)
    """
    df = df.copy()

    # Validate required columns
    if 'OCCJZ' not in df.columns:
        raise ValueError("OCCJZ column not found. Run add_occ_jz() first.")
    if 'EDUC' not in df.columns:
        raise ValueError("EDUC column not found.")

    # Apply filters
    if employed_only and 'LFS' in df.columns:
        df = df[df['LFS'] == 'Employed']

    if educ_filter is not None:
        educ_vals = df['EDUC'].astype(str)
        df = df[educ_vals.isin(educ_filter)]

    if age_min is not None and 'AGE' in df.columns:
        df = df[df['AGE'] >= age_min]

    if age_max is not None and 'AGE' in df.columns:
        df = df[df['AGE'] <= age_max]

    # Drop missing
    df = df.dropna(subset=['OCCJZ', weight_col])

    if len(df) == 0:
        return pd.DataFrame(columns=['mismatch', 'weight', 'share', 'label'])

    # Compute mismatch
    df['_worker_jz'] = df['EDUC'].astype(str).map(EDUC_TO_JZ)
    df['_mismatch'] = df['_worker_jz'] - df['OCCJZ']

    # Round to nearest integer for binning (handles fractional OCCJZ)
    df['_mismatch_bin'] = df['_mismatch'].round().astype(int)

    # Aggregate by mismatch level
    result = df.groupby('_mismatch_bin')[weight_col].sum().reset_index()
    result.columns = ['mismatch', 'weight']

    total_weight = result['weight'].sum()
    result['share'] = result['weight'] / total_weight
    result['share_pct'] = result['share'] * 100

    # Add labels
    def mismatch_label(m):
        if m < -1:
            return f'Underqualified ({m})'
        elif m == -1:
            return 'Slightly under (-1)'
        elif m == 0:
            return 'Matched (0)'
        elif m == 1:
            return 'Slightly over (+1)'
        else:
            return f'Overqualified (+{m})'

    result['label'] = result['mismatch'].apply(mismatch_label)

    return result.sort_values('mismatch')


if __name__ == '__main__':
    # Demo usage
    print("CPS-O*NET Integration Module")
    print("="*50)
    print("\nUsage:")
    print("  from cps_onet import add_occ_pd_dwc, add_occ_telework, add_occ_ai, add_occ_jz, add_all_occ_vars")
    print("  cps = pd.read_feather('cps2020.ft')")
    print("  cps = add_all_occ_vars(cps, year=2020)  # adds all variables")
    print("  # Or add individually:")
    print("  # cps = add_occ_pd_dwc(cps, year=2020)")
    print("  # cps = add_occ_telework(cps, year=2020)")
    print("  # cps = add_occ_ai(cps, year=2020)")
    print("  # cps = add_occ_jz(cps, year=2020)")
    print("\nVariables added:")
    print("  OCCPD   - Any physical demands (0-1 proportion)")
    print("  OCCHPD  - High physical demands (0-1 proportion)")
    print("  OCCDWC  - Difficult working conditions (0-1 proportion)")
    print("  OCCTLWK - Telework feasibility (0-1 proportion, DFLP methodology)")
    print("  OCCAI   - AI exposure (0-1 score, Pew Research methodology)")
    print("  OCCJZ   - Job Zone (1-5 scale, preparation/education level)")
    print("\nTo create binary variables:")
    print("  cps['PD'] = (cps['OCCPD'] > 0.5).astype(int)        # majority threshold")
    print("  cps['TELEWORK'] = (cps['OCCTLWK'] > 0.5).astype(int)")
    print("  cps['BA_REQUIRED'] = (cps['OCCJZ'] >= 4).astype(int)  # NY Fed method")
    print("  # For AI exposure, use percentile cutoffs:")
    print("  threshold = cps['OCCAI'].quantile(0.75)")
    print("  cps['HIGH_AI'] = (cps['OCCAI'] > threshold).astype(int)")
    print("\nEducation mismatch analysis:")
    print("  edu_to_jz = {'LTHS': 1, 'HS': 2, 'SC': 3, 'COLL': 4, 'ADV': 5}")
    print("  cps['WORKER_JZ'] = cps['EDUC'].map(edu_to_jz)")
    print("  cps['EDUMISMATCH'] = cps['WORKER_JZ'] - cps['OCCJZ']")
    print("  # Positive = overqualified, Negative = underqualified")
