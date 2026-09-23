"""
AI Exposure Classifier for CPS Occupations

This module classifies occupations by AI exposure based on O*NET work activities,
following the Pew Research Center methodology from their July 2023 analysis
"Which U.S. Workers Are More Exposed to AI on Their Jobs?"

The methodology classifies 41 O*NET work activities into three exposure levels
(high, medium, low), then calculates the relative importance of high-exposure
activities for each occupation.

Classification Logic:
1. Calculate average importance rating for each exposure category
2. Compute relative importance = high_avg / (high_avg + medium_avg + low_avg)
3. Higher relative importance = more AI-exposed occupation

The OCCAI variable represents a continuous score (0-1) where higher values
indicate greater exposure to AI.

Reference:
    Pew Research Center (2023). "Which U.S. Workers Are More Exposed to AI
    on Their Jobs?" July 26, 2023.
    https://www.pewresearch.org/social-trends/2023/07/26/which-u-s-workers-are-more-exposed-to-ai-on-their-jobs/

Usage:
    from ai_classifier import create_ai_lookup

    lookup = create_ai_lookup(
        onet_path='/path/to/onet/db_25_1_text/',
        census_crosswalk='census2018',
        crosswalk_path='/path/to/crosswalks/',
        oews_path='/path/to/oews/oesm20nat/'
    )
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Import shared functions from pd_dwc_classifier
from pd_dwc_classifier import (
    load_onet_data,
    load_oews_employment,
    load_census_crosswalk,
    onet_soc_to_soc,
    get_period_config,
    get_oews_year,
)

# =============================================================================
# Pew Research AI Exposure Classification
# From Pew Research Center methodology tables (July 2023)
# All 41 O*NET work activities classified by AI exposure level
# =============================================================================

# HIGH EXPOSURE activities (16 total)
# Jobs heavy in these activities are most likely to be affected by AI
HIGH_EXPOSURE_ACTIVITIES = {
    '4.A.1.a.1': 'Getting Information',
    '4.A.1.a.2': 'Monitor Processes, Materials, or Surroundings',
    '4.A.2.a.2': 'Processing Information',
    '4.A.2.a.3': 'Evaluating Information to Determine Compliance with Standards',
    '4.A.2.a.4': 'Analyzing Data or Information',
    '4.A.2.b.1': 'Making Decisions and Solving Problems',
    '4.A.2.b.2': 'Thinking Creatively',
    '4.A.2.b.5': 'Scheduling Work and Activities',
    '4.A.3.a.3': 'Controlling Machines and Processes',
    '4.A.3.a.4': 'Operating Vehicles, Mechanized Devices, or Equipment',
    '4.A.3.b.1': 'Interacting With Computers',
    '4.A.3.b.2': 'Drafting, Laying Out, and Specifying Technical Devices, Parts, and Equipment',
    '4.A.3.b.6': 'Documenting/Recording Information',
    '4.A.4.a.8': 'Performing for or Working Directly with the Public',
    '4.A.4.c.1': 'Performing Administrative Activities',
    '4.A.4.c.3': 'Monitoring and Controlling Resources',
}

# MEDIUM EXPOSURE activities (16 total)
MEDIUM_EXPOSURE_ACTIVITIES = {
    '4.A.1.b.1': 'Identifying Objects, Actions, and Events',
    '4.A.1.b.2': 'Inspecting Equipment, Structures, or Material',
    '4.A.1.b.3': 'Estimating the Quantifiable Characteristics of Products, Events, or Information',
    '4.A.2.a.1': 'Judging the Qualities of Things, Services, or People',
    '4.A.2.b.3': 'Updating and Using Relevant Knowledge',
    '4.A.2.b.4': 'Developing Objectives and Strategies',
    '4.A.2.b.6': 'Organizing, Planning, and Prioritizing Work',
    '4.A.4.a.1': 'Interpreting the Meaning of Information for Others',
    '4.A.4.a.2': 'Communicating with Supervisors, Peers, or Subordinates',
    '4.A.4.a.3': 'Communicating with Persons Outside Organization',
    '4.A.4.a.6': 'Selling or Influencing Others',
    '4.A.4.b.1': 'Coordinating the Work and Activities of Others',
    '4.A.4.b.3': 'Training and Teaching Others',
    '4.A.4.b.4': 'Guiding, Directing, and Motivating Subordinates',
    '4.A.4.b.6': 'Provide Consultation and Advice to Others',
    '4.A.4.c.2': 'Staffing Organizational Units',
}

# LOW EXPOSURE activities (9 total)
# Jobs heavy in these activities are least likely to be affected by AI
LOW_EXPOSURE_ACTIVITIES = {
    '4.A.3.a.1': 'Performing General Physical Activities',
    '4.A.3.a.2': 'Handling and Moving Objects',
    '4.A.3.b.4': 'Repairing and Maintaining Mechanical Equipment',
    '4.A.3.b.5': 'Repairing and Maintaining Electronic Equipment',
    '4.A.4.a.4': 'Establishing and Maintaining Interpersonal Relationships',
    '4.A.4.a.5': 'Assisting and Caring for Others',
    '4.A.4.a.7': 'Resolving Conflicts and Negotiating with Others',
    '4.A.4.b.2': 'Developing and Building Teams',
    '4.A.4.b.5': 'Coaching and Developing Others',
}


def get_activity_scores(activities_df):
    """
    Get importance scores for all work activities by O*NET-SOC code.

    Parameters
    ----------
    activities_df : DataFrame
        O*NET Work Activities data

    Returns
    -------
    dict : {onet_code: {element_id: score}}
    """
    # Filter to importance scale only
    mask = activities_df['Scale ID'] == 'IM'
    filtered = activities_df.loc[mask, ['O*NET-SOC Code', 'Element ID', 'Data Value']]

    scores = {}
    for _, row in filtered.iterrows():
        code = row['O*NET-SOC Code']
        if code not in scores:
            scores[code] = {}
        scores[code][row['Element ID']] = row['Data Value']

    return scores


def calculate_ai_exposure(activity_scores):
    """
    Calculate AI exposure score for an occupation based on Pew methodology.

    Parameters
    ----------
    activity_scores : dict
        {element_id: importance_score} for one O*NET-SOC code

    Returns
    -------
    dict with keys:
        - ai_exposure: relative importance of high-exposure activities (0-1)
        - high_avg: average importance of high-exposure activities
        - medium_avg: average importance of medium-exposure activities
        - low_avg: average importance of low-exposure activities
    """
    # Calculate average importance for each category
    high_scores = [activity_scores.get(eid, 0) for eid in HIGH_EXPOSURE_ACTIVITIES.keys()]
    medium_scores = [activity_scores.get(eid, 0) for eid in MEDIUM_EXPOSURE_ACTIVITIES.keys()]
    low_scores = [activity_scores.get(eid, 0) for eid in LOW_EXPOSURE_ACTIVITIES.keys()]

    high_avg = np.mean(high_scores) if high_scores else 0
    medium_avg = np.mean(medium_scores) if medium_scores else 0
    low_avg = np.mean(low_scores) if low_scores else 0

    # Calculate relative importance (normalized)
    total = high_avg + medium_avg + low_avg
    if total > 0:
        ai_exposure = high_avg / total
    else:
        ai_exposure = 0

    return {
        'ai_exposure': ai_exposure,
        'high_avg': high_avg,
        'medium_avg': medium_avg,
        'low_avg': low_avg,
    }


def classify_ai_exposure(onet_path):
    """
    Calculate AI exposure scores for all O*NET-SOC codes.

    Parameters
    ----------
    onet_path : str or Path
        Path to O*NET database text files

    Returns
    -------
    dict : {onet_code: {'ai_exposure': float, 'high_avg': float, ...}}
    """
    _, activities, _ = load_onet_data(onet_path)

    # Get activity scores for all occupations
    all_scores = get_activity_scores(activities)

    results = {}
    for code, scores in all_scores.items():
        results[code] = calculate_ai_exposure(scores)

    return results


def aggregate_ai_to_soc(classifications, emp_dict=None):
    """
    Aggregate O*NET-SOC AI exposure scores to SOC level.

    Parameters
    ----------
    classifications : dict
        Output from classify_ai_exposure()
    emp_dict : dict, optional
        Employment by SOC code for weighting

    Returns
    -------
    DataFrame with columns: soc_code, ai_exposure
    """
    records = []
    for onet_code, result in classifications.items():
        soc = onet_soc_to_soc(onet_code)
        records.append({
            'onet_code': onet_code,
            'soc_code': soc,
            'ai_exposure': result['ai_exposure'],
            'high_avg': result['high_avg'],
            'medium_avg': result['medium_avg'],
            'low_avg': result['low_avg'],
        })

    df = pd.DataFrame(records)

    # Aggregate to SOC level (unweighted mean of O*NET subcodes)
    soc_agg = df.groupby('soc_code').agg({
        'ai_exposure': 'mean',
        'high_avg': 'mean',
        'medium_avg': 'mean',
        'low_avg': 'mean',
    }).reset_index()

    return soc_agg


def match_soc_to_ai(census_soc, soc_ai_df, emp_dict=None):
    """
    Get AI exposure score for a Census SOC code via prefix matching.

    Parameters
    ----------
    census_soc : str
        SOC code from Census crosswalk
    soc_ai_df : DataFrame
        SOC-level AI scores from aggregate_ai_to_soc()
    emp_dict : dict, optional
        Employment by SOC code from load_oews_employment()

    Returns
    -------
    float or None : AI exposure score (0-1)
    """
    if pd.isna(census_soc):
        return None

    census_soc = str(census_soc).strip()

    # Handle combined codes (e.g., "15-1132, 15-1133")
    if ',' in census_soc:
        parts = [s.strip() for s in census_soc.split(',')]
        scores = [match_soc_to_ai(p, soc_ai_df, emp_dict) for p in parts]
        scores = [s for s in scores if s is not None]
        if scores:
            return np.mean(scores)
        return None

    # Handle range codes (e.g., "11-0000 - 13-0000")
    if ' - ' in census_soc:
        census_soc = census_soc.split(' - ')[0].strip()

    # Exact match
    exact = soc_ai_df[soc_ai_df['soc_code'] == census_soc]
    if len(exact) > 0:
        return exact.iloc[0]['ai_exposure']

    # Prefix matching for aggregate codes
    for trim in [1, 2, 3]:
        if len(census_soc) > trim:
            prefix = census_soc[:-trim]
            matches = soc_ai_df[soc_ai_df['soc_code'].str.startswith(prefix)]
            if len(matches) > 0:
                # Use employment weighting if available
                if emp_dict:
                    total_emp = 0
                    weighted_sum = 0
                    for _, row in matches.iterrows():
                        emp = emp_dict.get(row['soc_code'], 0)
                        total_emp += emp
                        weighted_sum += row['ai_exposure'] * emp

                    if total_emp > 0:
                        return weighted_sum / total_emp

                # Unweighted average (fallback)
                return matches['ai_exposure'].mean()

    return None


def create_ai_lookup(onet_path, census_crosswalk, crosswalk_path,
                     onet_version=None, oews_path=None):
    """
    Create AI exposure lookup table for a Census occupation code system.

    Parameters
    ----------
    onet_path : str or Path
        Path to O*NET database text files
    census_crosswalk : str
        One of: 'census2002', 'census2010', 'census2018'
    crosswalk_path : str or Path
        Path to crosswalks directory
    onet_version : str, optional
        O*NET version for metadata (e.g., '25.1')
    oews_path : str or Path, optional
        Path to OEWS data directory for employment weighting

    Returns
    -------
    DataFrame with columns: census_code, occupation_title, ai_exposure, onet_version
    """
    # Classify O*NET jobs
    classifications = classify_ai_exposure(onet_path)

    # Aggregate to SOC level
    soc_ai = aggregate_ai_to_soc(classifications)

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

    # Match Census codes to AI exposure scores
    records = []
    for _, row in census_df.iterrows():
        ai_exposure = match_soc_to_ai(row['soc_code'], soc_ai, emp_dict)
        record = {
            'census_code': int(row['census_code']),
            'occupation_title': row['census_title'],
            'ai_exposure': ai_exposure if ai_exposure is not None else np.nan,
        }
        if onet_version:
            record['onet_version'] = onet_version
        records.append(record)

    result = pd.DataFrame(records)

    # Print summary
    matched = result['ai_exposure'].notna().sum()
    total = len(result)
    high_exposed = (result['ai_exposure'] > 0.4).sum()  # Top quartile roughly
    print(f"AI Exposure Lookup: {matched}/{total} Census codes matched ({100*matched/total:.1f}%)")
    print(f"  High AI exposure (>0.4): {high_exposed} occupations")
    print(f"  Mean AI exposure score: {result['ai_exposure'].mean():.3f}")
    print(f"  Std AI exposure score: {result['ai_exposure'].std():.3f}")

    return result


def generate_annual_ai_lookups(onet_base_path, crosswalk_path, output_path,
                               oews_base_path, start_year=2003, end_year=2025):
    """
    Generate annual AI exposure lookup tables for CPS years.

    Creates one lookup table per year with year-appropriate OEWS employment weights.
    Files are named ai_YYYY.csv.

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
    start_year : int, default 2003
        First CPS year to generate
    end_year : int, default 2025
        Last CPS year to generate
    """
    onet_base_path = Path(onet_base_path)
    output_path = Path(output_path)
    oews_base_path = Path(oews_base_path)
    output_path.mkdir(parents=True, exist_ok=True)

    # Cache classifications by period
    classification_cache = {}
    soc_ai_cache = {}

    print(f"Generating annual AI exposure lookup tables for {start_year}-{end_year}")
    print("=" * 60)

    for year in range(start_year, end_year + 1):
        census_type, onet_subdir, onet_ver = get_period_config(year)
        oews_year = get_oews_year(year)
        oews_dir = f'oesm{str(oews_year)[2:]}nat'
        output_file = f'ai_{year}.csv'

        print(f"\n{year}: {census_type}, O*NET {onet_ver}, OEWS {oews_year}")

        # Load/cache O*NET classifications
        cache_key = (census_type, onet_ver)
        if cache_key not in classification_cache:
            onet_path = onet_base_path / onet_subdir
            classifications = classify_ai_exposure(onet_path)
            soc_ai = aggregate_ai_to_soc(classifications)
            census_df = load_census_crosswalk(census_type, crosswalk_path)
            classification_cache[cache_key] = classifications
            soc_ai_cache[cache_key] = (soc_ai, census_df, onet_ver)

        soc_ai, census_df, onet_ver = soc_ai_cache[cache_key]

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
            ai_exposure = match_soc_to_ai(row['soc_code'], soc_ai, emp_dict)
            record = {
                'census_code': int(row['census_code']),
                'occupation_title': row['census_title'],
                'ai_exposure': ai_exposure if ai_exposure is not None else np.nan,
                'onet_version': onet_ver,
                'oews_year': oews_year,
            }
            records.append(record)

        lookup = pd.DataFrame(records)
        lookup.to_csv(output_path / output_file, index=False)

        # Summary stats
        mean_exp = lookup['ai_exposure'].mean()
        std_exp = lookup['ai_exposure'].std()
        high_exp = (lookup['ai_exposure'] > 0.4).sum()
        print(f"  AI exposure: mean={mean_exp:.3f}, std={std_exp:.3f}, high(>0.4)={high_exp}")

    print("\n" + "=" * 60)
    print(f"Generated {end_year - start_year + 1} annual AI exposure lookup tables")
    print("=" * 60)


def print_exposure_details(onet_path, sample_codes=None):
    """
    Print detailed AI exposure results for debugging/inspection.

    Parameters
    ----------
    onet_path : str or Path
        Path to O*NET database text files
    sample_codes : list, optional
        Specific O*NET-SOC codes to inspect. If None, shows summary stats.
    """
    classifications = classify_ai_exposure(onet_path)

    if sample_codes:
        for code in sample_codes:
            if code in classifications:
                result = classifications[code]
                print(f"\n{code}:")
                print(f"  AI exposure: {result['ai_exposure']:.3f}")
                print(f"  High avg: {result['high_avg']:.2f}, "
                      f"Medium avg: {result['medium_avg']:.2f}, "
                      f"Low avg: {result['low_avg']:.2f}")
            else:
                print(f"\n{code}: Not found")
    else:
        # Summary stats
        exposures = [r['ai_exposure'] for r in classifications.values()]
        print(f"Total O*NET-SOC codes: {len(classifications)}")
        print(f"AI exposure: mean={np.mean(exposures):.3f}, "
              f"std={np.std(exposures):.3f}, "
              f"min={np.min(exposures):.3f}, "
              f"max={np.max(exposures):.3f}")

        # Distribution
        percentiles = [10, 25, 50, 75, 90]
        pct_values = np.percentile(exposures, percentiles)
        print("\nPercentiles:")
        for p, v in zip(percentiles, pct_values):
            print(f"  {p}th: {v:.3f}")


def get_top_bottom_occupations(onet_path, n=10):
    """
    Get the most and least AI-exposed occupations.

    Parameters
    ----------
    onet_path : str or Path
        Path to O*NET database text files
    n : int, default 10
        Number of occupations to show for each category

    Returns
    -------
    tuple of DataFrames: (top_exposed, least_exposed)
    """
    _, activities, _ = load_onet_data(onet_path)
    classifications = classify_ai_exposure(onet_path)

    # Get occupation titles from O*NET
    # Load Occupation Data for titles
    occ_data_path = Path(onet_path) / 'Occupation Data.txt'
    if occ_data_path.exists():
        occ_data = pd.read_csv(occ_data_path, sep='\t')
        titles = dict(zip(occ_data['O*NET-SOC Code'], occ_data['Title']))
    else:
        titles = {}

    records = []
    for code, result in classifications.items():
        records.append({
            'onet_code': code,
            'title': titles.get(code, code),
            'ai_exposure': result['ai_exposure'],
        })

    df = pd.DataFrame(records)
    df = df.sort_values('ai_exposure', ascending=False)

    top = df.head(n)
    bottom = df.tail(n).iloc[::-1]

    return top, bottom


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

    # Generate annual AI exposure lookup tables
    generate_annual_ai_lookups(
        ONET_BASE, CROSSWALK_PATH, OUTPUT_PATH, OEWS_BASE,
        start_year=2003, end_year=2025
    )
