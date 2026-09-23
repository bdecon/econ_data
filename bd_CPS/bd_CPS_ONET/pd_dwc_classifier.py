"""
PD/DWC Classifier for CPS Occupations

This module classifies occupations as Physically Demanding (PD) or having
Difficult Working Conditions (DWC) based on O*NET data, following the methodology
from Johnson, Mermin, Resseger (2007), Rho (2010), and Bucknor & Baker (2016).

Employment weighting (optional) uses BLS OEWS data to weight SOC codes by
actual employment when aggregating to Census occupation codes. This improves
accuracy for occupations that map to multiple SOC codes with unequal employment.

Usage:
    from pd_dwc_classifier import create_pd_dwc_lookup

    # Create lookup table for OCC10 period (2011-2019)
    lookup = create_pd_dwc_lookup(
        onet_path='/path/to/onet/db_20_1_text/',
        census_crosswalk='census2010',
        crosswalk_path='/path/to/crosswalks/',
        oews_path='/path/to/oews/oesm20nat/'  # Optional: enables employment weighting
    )
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Threshold: importance/context score >= 4.0 (on 1-5 scale)
THRESHOLD = 4.0

# High PD elements (Abilities - Scale ID 'IM' for importance)
HIGH_PD_ABILITIES = [
    'Static Strength',
    'Explosive Strength',
    'Dynamic Strength',
    'Trunk Strength',
    'Stamina',
    'Reaction Time',
    'Gross Body Equilibrium'
]

# Any PD - Work Activities (Scale ID 'IM')
PD_ACTIVITIES = [
    'Performing General Physical Activities',
    'Handling and Moving Objects'
]

# Any PD and High PD - Work Context (Scale ID 'CX')
PD_CONTEXT = [
    'Spend Time Standing',
    'Spend Time Walking and Running',
    'Spend Time Making Repetitive Motions'
]

HIGH_PD_CONTEXT = [
    'Spend Time Bending or Twisting the Body',
    'Spend Time Kneeling, Crouching, Stooping, or Crawling'
]

# DWC - Work Context (Scale ID 'CX')
DWC_CONTEXT = [
    'Cramped Work Space, Awkward Positions',
    'Outdoors, Exposed to Weather',
    'Outdoors, Under Cover',
    'Indoors, Not Environmentally Controlled',
    'Very Hot or Cold Temperatures',
    'Exposed to Contaminants',
    'Exposed to Hazardous Conditions',
    'Exposed to Hazardous Equipment',
    'Exposed to Whole Body Vibration',
    'Sounds, Noise Levels Are Distracting or Uncomfortable'
]


def load_onet_data(onet_path):
    """Load O*NET data files (Abilities, Work Activities, Work Context)."""
    onet_path = Path(onet_path)

    abilities = pd.read_csv(onet_path / 'Abilities.txt', sep='\t')
    activities = pd.read_csv(onet_path / 'Work Activities.txt', sep='\t')
    context = pd.read_csv(onet_path / 'Work Context.txt', sep='\t')

    return abilities, activities, context


def _filter_detailed_by_soc_pattern(df):
    """Filter OEWS data to detailed SOC codes using code pattern.

    Used for older OEWS files that don't have a 'detailed' group marker.
    Detailed SOC codes are 6-digit codes (XX-XXXX) that don't end in 000 or 0000.
    """
    # Match 6-digit SOC pattern
    mask = df['OCC_CODE'].astype(str).str.match(r'^\d{2}-\d{4}$')
    df = df[mask]
    # Exclude aggregate codes (ending in 000 or 0000)
    df = df[~df['OCC_CODE'].astype(str).str.endswith('0000')]
    df = df[~df['OCC_CODE'].astype(str).str.endswith('000')]
    return df


def load_oews_employment(oews_path):
    """
    Load BLS OEWS employment data.

    Parameters
    ----------
    oews_path : str or Path
        Path to OEWS data directory (e.g., 'data/oews/oesm24nat/')

    Returns
    -------
    dict : {soc_code: employment_count}
    """
    oews_path = Path(oews_path)

    # Find the Excel file in the directory (try .xlsx first, then .xls)
    xlsx_files = list(oews_path.glob('*.xlsx'))
    if not xlsx_files:
        xlsx_files = list(oews_path.glob('*.xls'))
    if not xlsx_files:
        raise FileNotFoundError(f"No OEWS Excel file found in {oews_path}")

    # Skip field_descriptions files
    data_files = [f for f in xlsx_files if 'field' not in f.name.lower()]
    if not data_files:
        data_files = xlsx_files

    df = pd.read_excel(data_files[0])

    # Normalize column names to uppercase (some years have lowercase)
    df.columns = df.columns.str.upper()

    # Handle different column names across OEWS years
    # Column may be named 'O_GROUP', 'OCC_GROUP', or 'GROUP' depending on year
    group_col = None
    for col_name in ['O_GROUP', 'OCC_GROUP', 'GROUP']:
        if col_name in df.columns:
            group_col = col_name
            break

    # Filter to detailed occupations only (6-digit SOC codes)
    if group_col and group_col in df.columns:
        detailed_mask = df[group_col].astype(str).str.lower() == 'detailed'
        if detailed_mask.any():
            df = df[detailed_mask]
        else:
            # Fall back to filtering by SOC code pattern for older files
            df = _filter_detailed_by_soc_pattern(df)
    else:
        # No group column - filter by SOC code pattern
        df = _filter_detailed_by_soc_pattern(df)

    # Create employment dictionary
    emp_dict = {}
    for _, row in df.iterrows():
        soc_code = row['OCC_CODE']
        emp = row['TOT_EMP']
        # Handle non-numeric values like '*' or '#'
        if isinstance(emp, (int, float)) and not pd.isna(emp):
            emp_dict[soc_code] = float(emp)
        else:
            emp_dict[soc_code] = 0

    return emp_dict


def get_jobs_meeting_criteria(df, scale_id, elements, threshold=THRESHOLD):
    """Return set of O*NET-SOC codes meeting criteria."""
    mask = (
        (df['Scale ID'] == scale_id) &
        (df['Element Name'].isin(elements)) &
        (df['Data Value'] >= threshold)
    )
    return set(df.loc[mask, 'O*NET-SOC Code'].unique())


def classify_onet_jobs(onet_path):
    """
    Classify O*NET-SOC codes as PD/DWC.

    Returns dict with sets of O*NET-SOC codes for each category.
    """
    abilities, activities, context = load_onet_data(onet_path)

    # High PD jobs
    high_pd_from_abilities = get_jobs_meeting_criteria(abilities, 'IM', HIGH_PD_ABILITIES)
    high_pd_from_context = get_jobs_meeting_criteria(context, 'CX', HIGH_PD_CONTEXT)
    high_pd_jobs = high_pd_from_abilities | high_pd_from_context

    # Any PD jobs (includes high PD)
    pd_from_activities = get_jobs_meeting_criteria(activities, 'IM', PD_ACTIVITIES)
    pd_from_context = get_jobs_meeting_criteria(context, 'CX', PD_CONTEXT)
    any_pd_jobs = pd_from_activities | pd_from_context | high_pd_jobs

    # DWC jobs
    dwc_jobs = get_jobs_meeting_criteria(context, 'CX', DWC_CONTEXT)

    # Difficult jobs (PD or DWC)
    difficult_jobs = any_pd_jobs | dwc_jobs

    return {
        'high_pd': high_pd_jobs,
        'any_pd': any_pd_jobs,
        'dwc': dwc_jobs,
        'difficult': difficult_jobs
    }


def onet_soc_to_soc(onet_code):
    """Extract standard SOC code from O*NET-SOC code (e.g., 11-1011.00 -> 11-1011)."""
    return str(onet_code).split('.')[0]


def aggregate_to_soc(onet_codes, classifications):
    """
    Aggregate O*NET-SOC classifications to SOC level.

    Returns DataFrame with proportion of O*NET subcodes meeting each criterion.
    """
    records = []
    for code in onet_codes:
        soc = onet_soc_to_soc(code)
        records.append({
            'onet_code': code,
            'soc_code': soc,
            'high_pd': 1 if code in classifications['high_pd'] else 0,
            'any_pd': 1 if code in classifications['any_pd'] else 0,
            'dwc': 1 if code in classifications['dwc'] else 0,
            'difficult': 1 if code in classifications['difficult'] else 0
        })

    df = pd.DataFrame(records)

    # Aggregate to SOC level
    soc_agg = df.groupby('soc_code').agg({
        'high_pd': 'mean',
        'any_pd': 'mean',
        'dwc': 'mean',
        'difficult': 'mean'
    }).reset_index()

    return soc_agg


def load_census_crosswalk(crosswalk_type, crosswalk_path):
    """
    Load Census occupation to SOC crosswalk.

    Parameters
    ----------
    crosswalk_type : str
        One of: 'census2002', 'census2010', 'census2018'
    crosswalk_path : str or Path
        Path to crosswalks directory

    Returns
    -------
    DataFrame with columns: census_code, census_title, soc_code
    """
    crosswalk_path = Path(crosswalk_path)

    if crosswalk_type == 'census2002':
        df = pd.read_excel(
            crosswalk_path / '2002-census-occupation-codes.xls',
            header=None, skiprows=2
        )
        df.columns = ['group', 'census_title', 'census_code', 'soc_code']
        df['census_code'] = pd.to_numeric(df['census_code'], errors='coerce')
        df = df.dropna(subset=['census_code'])
        df = df[['census_title', 'census_code', 'soc_code']]

    elif crosswalk_type == 'census2010':
        df = pd.read_excel(
            crosswalk_path / 'cenocc2010.xlsx',
            skiprows=5
        )
        df.columns = ['census_title', 'census_code', 'soc_code']
        df['census_code'] = pd.to_numeric(df['census_code'], errors='coerce')
        df = df.dropna(subset=['census_code'])

    elif crosswalk_type == 'census2018':
        df = pd.read_excel(
            crosswalk_path / '2018-occupation-code-list-and-crosswalk.xlsx',
            sheet_name='2018 Census Occ Code List',
            header=None, skiprows=4
        )
        df.columns = ['group', 'census_title', 'census_code', 'soc_code']
        df['census_code'] = pd.to_numeric(df['census_code'], errors='coerce')
        df = df.dropna(subset=['census_code'])
        df = df[['census_title', 'census_code', 'soc_code']]
    else:
        raise ValueError(f"Unknown crosswalk type: {crosswalk_type}")

    df['census_code'] = df['census_code'].astype(int)
    return df


def match_soc_to_flags(census_soc, soc_pd_df, emp_dict=None):
    """
    Get PD/DWC flags for a Census SOC code via prefix matching.

    Parameters
    ----------
    census_soc : str
        SOC code from Census crosswalk
    soc_pd_df : DataFrame
        SOC-level PD/DWC flags from aggregate_to_soc()
    emp_dict : dict, optional
        Employment by SOC code from load_oews_employment().
        If provided, uses employment-weighted averages.

    Handles:
    - Exact matches
    - Aggregate codes (ending in 0) via prefix matching
    - Combined codes (with commas or dashes)
    - Employment weighting when emp_dict is provided
    """
    if pd.isna(census_soc):
        return None

    census_soc = str(census_soc).strip()

    # Handle combined codes (e.g., "15-1132, 15-1133")
    if ',' in census_soc:
        parts = [s.strip() for s in census_soc.split(',')]
        flags = [match_soc_to_flags(p, soc_pd_df, emp_dict) for p in parts]
        flags = [f for f in flags if f is not None]
        if flags:
            return {k: np.mean([f[k] for f in flags]) for k in flags[0].keys()}
        return None

    # Handle range codes (e.g., "11-0000 - 13-0000")
    if ' - ' in census_soc:
        # Just use first part for matching
        census_soc = census_soc.split(' - ')[0].strip()

    # Exact match
    exact = soc_pd_df[soc_pd_df['soc_code'] == census_soc]
    if len(exact) > 0:
        row = exact.iloc[0]
        return {'high_pd': row['high_pd'], 'any_pd': row['any_pd'],
                'dwc': row['dwc'], 'difficult': row['difficult']}

    # Prefix matching for aggregate codes
    for trim in [1, 2, 3]:
        if len(census_soc) > trim:
            prefix = census_soc[:-trim]
            matches = soc_pd_df[soc_pd_df['soc_code'].str.startswith(prefix)]
            if len(matches) > 0:
                # Use employment weighting if available
                if emp_dict:
                    total_emp = 0
                    weighted_sums = {'high_pd': 0, 'any_pd': 0, 'dwc': 0, 'difficult': 0}
                    for _, row in matches.iterrows():
                        emp = emp_dict.get(row['soc_code'], 0)
                        total_emp += emp
                        for key in weighted_sums:
                            weighted_sums[key] += row[key] * emp

                    if total_emp > 0:
                        return {k: v / total_emp for k, v in weighted_sums.items()}
                    # Fall back to unweighted if no employment data

                # Unweighted average (fallback or when emp_dict is None)
                return {
                    'high_pd': matches['high_pd'].mean(),
                    'any_pd': matches['any_pd'].mean(),
                    'dwc': matches['dwc'].mean(),
                    'difficult': matches['difficult'].mean()
                }

    return None


def create_pd_dwc_lookup(onet_path, census_crosswalk, crosswalk_path, onet_version=None,
                         oews_path=None):
    """
    Create PD/DWC lookup table for a Census occupation code system.

    Parameters
    ----------
    onet_path : str or Path
        Path to O*NET database text files
    census_crosswalk : str
        One of: 'census2002', 'census2010', 'census2018'
    crosswalk_path : str or Path
        Path to crosswalks directory
    onet_version : str, optional
        O*NET version for metadata (e.g., '20.1')
    oews_path : str or Path, optional
        Path to OEWS data directory (e.g., 'data/oews/oesm20nat/').
        If provided, uses employment-weighted aggregation.

    Returns
    -------
    DataFrame with columns: census_code, occupation_title, high_pd, any_pd, dwc, difficult, onet_version
    """
    # Load and classify O*NET jobs
    abilities, activities, context = load_onet_data(onet_path)
    classifications = classify_onet_jobs(onet_path)

    # Get all O*NET-SOC codes
    all_onet_codes = set(abilities['O*NET-SOC Code'].unique())

    # Aggregate to SOC level
    soc_pd = aggregate_to_soc(all_onet_codes, classifications)

    # Load Census crosswalk
    census_df = load_census_crosswalk(census_crosswalk, crosswalk_path)

    # Load OEWS employment data if provided
    emp_dict = None
    if oews_path:
        try:
            emp_dict = load_oews_employment(oews_path)
            print(f"  Employment weighting: enabled ({len(emp_dict)} SOC codes)")
        except FileNotFoundError as e:
            print(f"  Employment weighting: disabled ({e})")

    # Match Census codes to SOC flags
    records = []
    for _, row in census_df.iterrows():
        flags = match_soc_to_flags(row['soc_code'], soc_pd, emp_dict)
        record = {
            'census_code': int(row['census_code']),
            'occupation_title': row['census_title'],
        }
        if flags:
            record.update(flags)
        else:
            record.update({'high_pd': np.nan, 'any_pd': np.nan,
                          'dwc': np.nan, 'difficult': np.nan})
        if onet_version:
            record['onet_version'] = onet_version
        records.append(record)

    result = pd.DataFrame(records)

    # Print summary
    matched = result['any_pd'].notna().sum()
    total = len(result)
    print(f"PD/DWC Lookup: {matched}/{total} Census codes matched ({100*matched/total:.1f}%)")
    print(f"  High PD jobs: {(result['high_pd'] > 0).sum()}")
    print(f"  Any PD jobs: {(result['any_pd'] > 0).sum()}")
    print(f"  DWC jobs: {(result['dwc'] > 0).sum()}")

    return result


def load_offshorability(dorn_path, census_type):
    """
    Load offshorability data from Dorn crosswalks.

    Maps Census occupation codes to occ1990dd, then merges offshorability scores.
    Based on Autor & Dorn (2013) methodology.

    Parameters
    ----------
    dorn_path : str or Path
        Path to directory containing Dorn's crosswalk files
    census_type : str
        One of: 'census2002', 'census2010', 'census2018'

    Returns
    -------
    DataFrame with columns: census_code, occ1990dd, offshorability
    """
    dorn_path = Path(dorn_path)

    # Load offshorability data (at occ1990dd level)
    offshore_file = dorn_path / 'occ1990dd_task_offshore.dta'
    if not offshore_file.exists():
        print(f"  Offshorability: disabled (file not found: {offshore_file})")
        return None

    offshore = pd.read_stata(offshore_file)
    offshore = offshore.rename(columns={'task_offshorability': 'offshorability'})

    # Load appropriate Census -> occ1990dd crosswalk
    if census_type == 'census2002':
        # Census 2000 codes (Dorn) = Census 2002 codes (CPS) / 10
        cw_file = dorn_path / 'occ2000_occ1990dd.dta'
        if not cw_file.exists():
            print(f"  Offshorability: disabled (crosswalk not found: {cw_file})")
            return None
        cw = pd.read_stata(cw_file)
        cw['census_code'] = (cw['occ'] * 10).astype(int)

    elif census_type == 'census2010':
        cw_file = dorn_path / 'occ2010_occ1990dd.dta'
        if not cw_file.exists():
            print(f"  Offshorability: disabled (crosswalk not found: {cw_file})")
            return None
        cw = pd.read_stata(cw_file)
        # Census 2010 codes in Dorn are strings like '0010', convert to int
        cw['census_code'] = cw['occ'].astype(str).str.lstrip('0').replace('', '0').astype(int)

    elif census_type == 'census2018':
        # Dorn doesn't have Census 2018 crosswalk - use Census 2010 as approximation
        # Most codes are similar between 2010 and 2018
        cw_file = dorn_path / 'occ2010_occ1990dd.dta'
        if not cw_file.exists():
            print(f"  Offshorability: disabled (crosswalk not found: {cw_file})")
            return None
        cw = pd.read_stata(cw_file)
        cw['census_code'] = cw['occ'].astype(str).str.lstrip('0').replace('', '0').astype(int)
        print(f"  Offshorability: using Census 2010 crosswalk as proxy for Census 2018")
    else:
        return None

    # Merge crosswalk with offshorability
    result = cw[['census_code', 'occ1990dd']].merge(
        offshore[['occ1990dd', 'offshorability']],
        on='occ1990dd',
        how='left'
    )

    return result


def get_period_config(year):
    """
    Get O*NET and Census crosswalk configuration for a CPS year.

    Returns
    -------
    tuple : (census_type, onet_subdir, onet_version)
    """
    if year <= 2010:
        return ('census2002', 'db_14_0', '14.0')
    elif year <= 2019:
        return ('census2010', 'db_20_1_text', '20.1')
    else:
        return ('census2018', 'db_25_1_text', '25.1')


def get_oews_year(cps_year):
    """
    Get the appropriate OEWS year for a CPS year.

    Handles SOC system transitions:
    - OEWS 2003-2009 use SOC 2000 (compatible with OCC00/Census 2002)
    - OEWS 2010-2017 use SOC 2010 (compatible with OCC10/Census 2010)
    - OEWS 2018+ use SOC 2018 (compatible with OCC18/Census 2018)

    For misaligned years, uses the last compatible OEWS:
    - CPS 2010 uses OCC00 (SOC 2000), but OEWS 2010 switched to SOC 2010 → use OEWS 2009
    - CPS 2018-2019 use OCC10 (SOC 2010), but OEWS 2018+ use SOC 2018 → use OEWS 2017

    Parameters
    ----------
    cps_year : int
        CPS data year (2003-2025+)

    Returns
    -------
    int : OEWS year to use
    """
    if cps_year <= 2009:
        # OCC00 period, OEWS uses SOC 2000 - direct match
        return cps_year
    elif cps_year == 2010:
        # OCC00 period, but OEWS 2010 switched to SOC 2010 - use 2009
        return 2009
    elif cps_year <= 2017:
        # OCC10 period, OEWS uses SOC 2010 - direct match
        return cps_year
    elif cps_year <= 2019:
        # OCC10 period, but OEWS 2018+ use SOC 2018 - use 2017
        return 2017
    else:
        # OCC18 period, OEWS uses SOC 2018 - direct match (or prior year if not available)
        # Use min of cps_year and latest available (2024)
        return min(cps_year, 2024)


def generate_annual_lookups(onet_base_path, crosswalk_path, output_path, oews_base_path,
                            dorn_path=None, start_year=2003, end_year=2025):
    """
    Generate annual PD/DWC lookup tables for CPS years.

    Creates one lookup table per year with year-appropriate OEWS employment weights.
    Files are named pd_dwc_YYYY.csv (e.g., pd_dwc_2015.csv).

    Parameters
    ----------
    onet_base_path : str or Path
        Base path containing O*NET version directories
    crosswalk_path : str or Path
        Path to crosswalks directory
    output_path : str or Path
        Path for output CSV files
    oews_base_path : str or Path
        Base path containing OEWS data directories
    dorn_path : str or Path, optional
        Path to Dorn crosswalk files directory
    start_year : int, default 2003
        First CPS year to generate
    end_year : int, default 2024
        Last CPS year to generate
    """
    onet_base_path = Path(onet_base_path)
    output_path = Path(output_path)
    oews_base_path = Path(oews_base_path)
    output_path.mkdir(parents=True, exist_ok=True)

    # Cache O*NET classifications and offshorability by period to avoid reloading
    onet_cache = {}
    offshore_cache = {}

    print(f"Generating annual lookup tables for {start_year}-{end_year}")
    print("=" * 60)

    for year in range(start_year, end_year + 1):
        census_type, onet_subdir, onet_ver = get_period_config(year)
        oews_year = get_oews_year(year)
        oews_dir = f'oesm{str(oews_year)[2:]}nat'
        output_file = f'pd_dwc_{year}.csv'

        print(f"\n{year}: {census_type}, O*NET {onet_ver}, OEWS {oews_year}")

        # Load O*NET data (cached by period)
        cache_key = (census_type, onet_ver)
        if cache_key not in onet_cache:
            onet_path = onet_base_path / onet_subdir
            abilities, activities, context = load_onet_data(onet_path)
            classifications = classify_onet_jobs(onet_path)
            all_onet_codes = set(abilities['O*NET-SOC Code'].unique())
            soc_pd = aggregate_to_soc(all_onet_codes, classifications)
            census_df = load_census_crosswalk(census_type, crosswalk_path)
            onet_cache[cache_key] = (soc_pd, census_df, onet_ver)

            # Cache offshorability too
            if dorn_path:
                offshore_cache[census_type] = load_offshorability(dorn_path, census_type)

        soc_pd, census_df, onet_ver = onet_cache[cache_key]

        # Load OEWS for this year
        oews_path = oews_base_path / oews_dir
        emp_dict = None
        if oews_path.exists():
            try:
                emp_dict = load_oews_employment(oews_path)
            except Exception as e:
                print(f"  Warning: Could not load OEWS {oews_year}: {e}")

        # Build lookup table
        records = []
        for _, row in census_df.iterrows():
            flags = match_soc_to_flags(row['soc_code'], soc_pd, emp_dict)
            record = {
                'census_code': int(row['census_code']),
                'occupation_title': row['census_title'],
            }
            if flags:
                record.update(flags)
            else:
                record.update({'high_pd': np.nan, 'any_pd': np.nan,
                              'dwc': np.nan, 'difficult': np.nan})
            record['onet_version'] = onet_ver
            record['oews_year'] = oews_year
            records.append(record)

        lookup = pd.DataFrame(records)

        # Add offshorability
        if dorn_path and census_type in offshore_cache:
            offshore_df = offshore_cache[census_type]
            if offshore_df is not None:
                lookup = lookup.merge(
                    offshore_df[['census_code', 'offshorability']],
                    on='census_code',
                    how='left'
                )

        lookup.to_csv(output_path / output_file, index=False)

    print("\n" + "=" * 60)
    print(f"Generated {end_year - start_year + 1} annual lookup tables")
    print("=" * 60)


def generate_all_lookups(onet_base_path, crosswalk_path, output_path, oews_base_path=None,
                         dorn_path=None):
    """
    Generate PD/DWC lookup tables for all Census occupation code periods.

    NOTE: This function generates period-based lookup tables (one per occupation
    code period). For annual lookup tables with year-specific OEWS weights,
    use generate_annual_lookups() instead.

    Parameters
    ----------
    onet_base_path : str or Path
        Base path containing O*NET version directories
    crosswalk_path : str or Path
        Path to crosswalks directory
    output_path : str or Path
        Path for output CSV files
    oews_base_path : str or Path, optional
        Base path containing OEWS data directories.
        If provided, enables employment-weighted aggregation.
    dorn_path : str or Path, optional
        Path to Dorn crosswalk files directory.
        If provided, adds offshorability measure from Autor & Dorn (2013).

    Creates:
    - pd_dwc_occ00.csv (Census 2002 codes, for CPS 2003-2010)
    - pd_dwc_occ10.csv (Census 2010 codes, for CPS 2011-2019)
    - pd_dwc_occ18.csv (Census 2018 codes, for CPS 2020+)
    """
    onet_base_path = Path(onet_base_path)
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    if oews_base_path:
        oews_base_path = Path(oews_base_path)

    # Configuration: (Census crosswalk, O*NET path, O*NET version, OEWS dir, output file)
    # OEWS years chosen as period midpoints for employment weighting:
    #   OCC00 (2003-2010): OEWS 2006 (midpoint)
    #   OCC10 (2011-2019): OEWS 2015 (midpoint)
    #   OCC18 (2020+):     OEWS 2022 (recent, stable)
    configs = [
        ('census2002', onet_base_path / 'db_14_0', '14.0', 'oesm06nat', 'pd_dwc_occ00.csv'),
        ('census2010', onet_base_path / 'db_20_1_text', '20.1', 'oesm15nat', 'pd_dwc_occ10.csv'),
        ('census2018', onet_base_path / 'db_25_1_text', '25.1', 'oesm22nat', 'pd_dwc_occ18.csv'),
    ]

    for census_type, onet_path, onet_ver, oews_dir, output_file in configs:
        print(f"\n{'='*60}")
        print(f"Generating {output_file}")
        print(f"  O*NET version: {onet_ver}")
        print(f"  Census crosswalk: {census_type}")
        print(f"{'='*60}")

        # Determine OEWS path
        oews_path = None
        if oews_base_path:
            oews_path = oews_base_path / oews_dir
            if not oews_path.exists():
                print(f"  Warning: OEWS path not found: {oews_path}")
                oews_path = None

        lookup = create_pd_dwc_lookup(
            onet_path=onet_path,
            census_crosswalk=census_type,
            crosswalk_path=crosswalk_path,
            onet_version=onet_ver,
            oews_path=oews_path
        )

        # Add offshorability if Dorn path provided
        if dorn_path:
            offshore_df = load_offshorability(dorn_path, census_type)
            if offshore_df is not None:
                lookup = lookup.merge(
                    offshore_df[['census_code', 'offshorability']],
                    on='census_code',
                    how='left'
                )
                matched = lookup['offshorability'].notna().sum()
                print(f"  Offshorability: {matched}/{len(lookup)} codes matched")

        lookup.to_csv(output_path / output_file, index=False)
        print(f"Saved: {output_path / output_file}")

    print("\n" + "="*60)
    print("All lookup tables generated successfully!")
    print("="*60)


if __name__ == '__main__':
    # Default paths - update these before running
    # O*NET: Download from https://www.onetcenter.org/database.html
    ONET_BASE = '/path/to/onet/'
    # OEWS: Download from https://www.bls.gov/oes/tables.htm
    OEWS_BASE = '/path/to/oews/'
    # Local paths relative to this script
    SCRIPT_DIR = Path(__file__).parent
    CROSSWALK_PATH = str(SCRIPT_DIR / 'crosswalks/')
    OUTPUT_PATH = str(SCRIPT_DIR / 'output/')

    # Generate annual lookup tables (2003-2025)
    generate_annual_lookups(ONET_BASE, CROSSWALK_PATH, OUTPUT_PATH, OEWS_BASE)
