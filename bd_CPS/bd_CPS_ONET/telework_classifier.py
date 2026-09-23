"""
Telework Feasibility Classifier for CPS Occupations

This module classifies occupations by telework feasibility based on O*NET data,
following the DFLP methodology from Dey, Frazis, Loewenstein, and Piccone (2021)
in the BLS Monthly Labor Review.

The DFLP methodology refines Dingel & Neiman (2020) based on actual COVID-era
telework patterns observed in the CPS.

Classification Logic:
- An occupation starts as "suitable for telework"
- It becomes "not suitable" if ANY disqualifying condition is met
- It must ALSO meet ALL THREE positive requirements to remain suitable

Reference:
    Dey, Frazis, Loewenstein, Piccone (2021). "Teleworking and lost work during
    the pandemic: new evidence from the CPS." Monthly Labor Review, July 2021.
    https://doi.org/10.21916/mlr.2021.15

Usage:
    from telework_classifier import create_telework_lookup

    lookup = create_telework_lookup(
        onet_path='/path/to/onet/db_20_1_text/',
        census_crosswalk='census2010',
        crosswalk_path='/path/to/crosswalks/',
        oews_path='/path/to/oews/oesm15nat/'
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
# DFLP Telework Classification Criteria
# From BLS Monthly Labor Review Appendix Table 1
# =============================================================================

# Disqualifying conditions: if score >= cutoff, NOT suitable for telework
# These are Work Activities (Scale ID 'IM' for importance)
DISQUALIFY_ACTIVITIES = {
    'Performing General Physical Activities': 4.00,
    'Handling and Moving Objects': 4.00,
    'Controlling Machines and Processes': 4.00,
    'Operating Vehicles, Mechanized Devices, or Equipment': 4.00,
    'Repairing and Maintaining Mechanical Equipment': 4.00,
    'Repairing and Maintaining Electronic Equipment': 4.00,
}

# Disqualifying conditions: Work Context (Scale ID 'CX')
DISQUALIFY_CONTEXT = {
    # Work settings
    'Outdoors, Exposed to Weather': 4.00,
    'Outdoors, Under Cover': 4.00,
    'In an Open Vehicle or Equipment': 4.00,
    # Job hazards
    'Exposed to High Places': 4.00,
    'Exposed to Hazardous Conditions': 4.00,
    'Exposed to Hazardous Equipment': 4.00,
    'Exposed to Minor Burns, Cuts, Bites, or Stings': 4.00,
    # Body positioning
    'Spend Time Standing': 4.00,
    'Spend Time Climbing Ladders, Scaffolds, or Poles': 4.00,
    'Spend Time Walking and Running': 4.00,
    'Spend Time Kneeling, Crouching, Stooping, or Crawling': 4.00,
    'Spend Time Keeping or Regaining Balance': 4.00,
    'Spend Time Using Your Hands to Handle, Control, or Feel Objects, Tools, or Controls': 4.00,
    'Spend Time Bending or Twisting the Body': 4.00,
    # Environmental conditions
    'Sounds, Noise Levels Are Distracting or Uncomfortable': 4.00,
    'Very Hot or Cold Temperatures': 4.00,
    'Exposed to Contaminants': 4.00,
    'Exposed to Whole Body Vibration': 4.00,
    # Conflictual contact (lower threshold)
    'Frequency of Conflict Situations': 3.75,
    'Deal With Unpleasant or Angry People': 3.75,
    'Deal With Physically Aggressive People': 3.75,
}

# Positive requirements: ALL must be >= cutoff to remain suitable
# Note: "Interacting With Computers" is a Work Activity (Scale ID 'IM')
#       The other two are Work Context (Scale ID 'CX')
REQUIRE_ACTIVITIES = {
    'Interacting With Computers': 3.00,
}

REQUIRE_CONTEXT = {
    'Indoors, Environmentally Controlled': 3.00,
    'Spend Time Sitting': 3.00,
}


def get_element_scores(df, scale_id, elements):
    """
    Get scores for specified elements from O*NET data.

    Returns dict: {onet_code: {element_name: score}}
    """
    mask = (df['Scale ID'] == scale_id) & (df['Element Name'].isin(elements))
    filtered = df.loc[mask, ['O*NET-SOC Code', 'Element Name', 'Data Value']]

    scores = {}
    for _, row in filtered.iterrows():
        code = row['O*NET-SOC Code']
        if code not in scores:
            scores[code] = {}
        scores[code][row['Element Name']] = row['Data Value']

    return scores


def classify_telework(onet_path):
    """
    Classify O*NET-SOC codes for telework feasibility using DFLP methodology.

    Returns dict: {onet_code: {'telework': 0 or 1, 'disqualified_by': list, 'missing_requirements': list}}
    """
    abilities, activities, context = load_onet_data(onet_path)

    # Get all unique O*NET-SOC codes
    all_codes = set(activities['O*NET-SOC Code'].unique()) | set(context['O*NET-SOC Code'].unique())

    # Get scores for all relevant elements
    # Disqualifying conditions
    disqualify_activity_scores = get_element_scores(activities, 'IM', DISQUALIFY_ACTIVITIES.keys())
    disqualify_context_scores = get_element_scores(context, 'CX', DISQUALIFY_CONTEXT.keys())

    # Positive requirements
    require_activity_scores = get_element_scores(activities, 'IM', REQUIRE_ACTIVITIES.keys())
    require_context_scores = get_element_scores(context, 'CX', REQUIRE_CONTEXT.keys())

    results = {}
    for code in all_codes:
        disqualified_by = []
        missing_requirements = []

        # Check disqualifying activities
        code_disq_activities = disqualify_activity_scores.get(code, {})
        for element, threshold in DISQUALIFY_ACTIVITIES.items():
            score = code_disq_activities.get(element, 0)
            if score >= threshold:
                disqualified_by.append(element)

        # Check disqualifying context
        code_disq_context = disqualify_context_scores.get(code, {})
        for element, threshold in DISQUALIFY_CONTEXT.items():
            score = code_disq_context.get(element, 0)
            if score >= threshold:
                disqualified_by.append(element)

        # Check positive requirements - activities (all must be met)
        code_req_activities = require_activity_scores.get(code, {})
        for element, threshold in REQUIRE_ACTIVITIES.items():
            score = code_req_activities.get(element, 0)
            if score < threshold:
                missing_requirements.append(element)

        # Check positive requirements - context (all must be met)
        code_req_context = require_context_scores.get(code, {})
        for element, threshold in REQUIRE_CONTEXT.items():
            score = code_req_context.get(element, 0)
            if score < threshold:
                missing_requirements.append(element)

        # Telework suitable if no disqualifications AND all requirements met
        telework = 1 if (len(disqualified_by) == 0 and len(missing_requirements) == 0) else 0

        results[code] = {
            'telework': telework,
            'disqualified_by': disqualified_by,
            'missing_requirements': missing_requirements
        }

    return results


def aggregate_telework_to_soc(classifications, emp_dict=None):
    """
    Aggregate O*NET-SOC telework classifications to SOC level.

    Parameters
    ----------
    classifications : dict
        Output from classify_telework()
    emp_dict : dict, optional
        Employment by SOC code for weighting

    Returns
    -------
    DataFrame with columns: soc_code, telework (proportion)
    """
    records = []
    for onet_code, result in classifications.items():
        soc = onet_soc_to_soc(onet_code)
        records.append({
            'onet_code': onet_code,
            'soc_code': soc,
            'telework': result['telework']
        })

    df = pd.DataFrame(records)

    # Aggregate to SOC level (unweighted mean of O*NET subcodes)
    soc_agg = df.groupby('soc_code').agg({
        'telework': 'mean'
    }).reset_index()

    return soc_agg


def match_soc_to_telework(census_soc, soc_telework_df, emp_dict=None):
    """
    Get telework score for a Census SOC code via prefix matching.

    Parameters
    ----------
    census_soc : str
        SOC code from Census crosswalk
    soc_telework_df : DataFrame
        SOC-level telework scores from aggregate_telework_to_soc()
    emp_dict : dict, optional
        Employment by SOC code from load_oews_employment()

    Returns
    -------
    float or None : telework proportion (0-1)
    """
    if pd.isna(census_soc):
        return None

    census_soc = str(census_soc).strip()

    # Handle combined codes (e.g., "15-1132, 15-1133")
    if ',' in census_soc:
        parts = [s.strip() for s in census_soc.split(',')]
        scores = [match_soc_to_telework(p, soc_telework_df, emp_dict) for p in parts]
        scores = [s for s in scores if s is not None]
        if scores:
            return np.mean(scores)
        return None

    # Handle range codes (e.g., "11-0000 - 13-0000")
    if ' - ' in census_soc:
        census_soc = census_soc.split(' - ')[0].strip()

    # Exact match
    exact = soc_telework_df[soc_telework_df['soc_code'] == census_soc]
    if len(exact) > 0:
        return exact.iloc[0]['telework']

    # Prefix matching for aggregate codes
    for trim in [1, 2, 3]:
        if len(census_soc) > trim:
            prefix = census_soc[:-trim]
            matches = soc_telework_df[soc_telework_df['soc_code'].str.startswith(prefix)]
            if len(matches) > 0:
                # Use employment weighting if available
                if emp_dict:
                    total_emp = 0
                    weighted_sum = 0
                    for _, row in matches.iterrows():
                        emp = emp_dict.get(row['soc_code'], 0)
                        total_emp += emp
                        weighted_sum += row['telework'] * emp

                    if total_emp > 0:
                        return weighted_sum / total_emp

                # Unweighted average (fallback)
                return matches['telework'].mean()

    return None


def create_telework_lookup(onet_path, census_crosswalk, crosswalk_path,
                           onet_version=None, oews_path=None):
    """
    Create telework feasibility lookup table for a Census occupation code system.

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
        Path to OEWS data directory for employment weighting

    Returns
    -------
    DataFrame with columns: census_code, occupation_title, telework, onet_version
    """
    # Classify O*NET jobs
    classifications = classify_telework(onet_path)

    # Aggregate to SOC level
    soc_telework = aggregate_telework_to_soc(classifications)

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

    # Match Census codes to telework scores
    records = []
    for _, row in census_df.iterrows():
        telework = match_soc_to_telework(row['soc_code'], soc_telework, emp_dict)
        record = {
            'census_code': int(row['census_code']),
            'occupation_title': row['census_title'],
            'telework': telework if telework is not None else np.nan,
        }
        if onet_version:
            record['onet_version'] = onet_version
        records.append(record)

    result = pd.DataFrame(records)

    # Print summary
    matched = result['telework'].notna().sum()
    total = len(result)
    suitable = (result['telework'] > 0.5).sum()
    print(f"Telework Lookup: {matched}/{total} Census codes matched ({100*matched/total:.1f}%)")
    print(f"  Suitable for telework (>50%): {suitable} occupations")
    print(f"  Mean telework score: {result['telework'].mean():.3f}")

    return result


def generate_annual_telework_lookups(onet_base_path, crosswalk_path, output_path,
                                     oews_base_path, start_year=2003, end_year=2025):
    """
    Generate annual telework lookup tables for CPS years.

    Creates one lookup table per year with year-appropriate OEWS employment weights.
    Files are named telework_YYYY.csv.

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
    soc_telework_cache = {}

    print(f"Generating annual telework lookup tables for {start_year}-{end_year}")
    print("=" * 60)

    for year in range(start_year, end_year + 1):
        census_type, onet_subdir, onet_ver = get_period_config(year)
        oews_year = get_oews_year(year)
        oews_dir = f'oesm{str(oews_year)[2:]}nat'
        output_file = f'telework_{year}.csv'

        print(f"\n{year}: {census_type}, O*NET {onet_ver}, OEWS {oews_year}")

        # Load/cache O*NET classifications
        cache_key = (census_type, onet_ver)
        if cache_key not in classification_cache:
            onet_path = onet_base_path / onet_subdir
            classifications = classify_telework(onet_path)
            soc_telework = aggregate_telework_to_soc(classifications)
            census_df = load_census_crosswalk(census_type, crosswalk_path)
            classification_cache[cache_key] = classifications
            soc_telework_cache[cache_key] = (soc_telework, census_df, onet_ver)

        soc_telework, census_df, onet_ver = soc_telework_cache[cache_key]

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
            telework = match_soc_to_telework(row['soc_code'], soc_telework, emp_dict)
            record = {
                'census_code': int(row['census_code']),
                'occupation_title': row['census_title'],
                'telework': telework if telework is not None else np.nan,
                'onet_version': onet_ver,
                'oews_year': oews_year,
            }
            records.append(record)

        lookup = pd.DataFrame(records)
        lookup.to_csv(output_path / output_file, index=False)

        # Summary stats
        suitable = (lookup['telework'] > 0.5).sum()
        print(f"  Suitable for telework (>50%): {suitable}/{len(lookup)}")

    print("\n" + "=" * 60)
    print(f"Generated {end_year - start_year + 1} annual telework lookup tables")
    print("=" * 60)


def print_classification_details(onet_path, sample_codes=None):
    """
    Print detailed classification results for debugging/inspection.

    Parameters
    ----------
    onet_path : str or Path
        Path to O*NET database text files
    sample_codes : list, optional
        Specific O*NET-SOC codes to inspect. If None, shows summary stats.
    """
    classifications = classify_telework(onet_path)

    if sample_codes:
        for code in sample_codes:
            if code in classifications:
                result = classifications[code]
                print(f"\n{code}:")
                print(f"  Telework suitable: {result['telework']}")
                if result['disqualified_by']:
                    print(f"  Disqualified by: {result['disqualified_by']}")
                if result['missing_requirements']:
                    print(f"  Missing requirements: {result['missing_requirements']}")
            else:
                print(f"\n{code}: Not found")
    else:
        # Summary stats
        suitable = sum(1 for r in classifications.values() if r['telework'] == 1)
        total = len(classifications)
        print(f"Total O*NET-SOC codes: {total}")
        print(f"Suitable for telework: {suitable} ({100*suitable/total:.1f}%)")
        print(f"Not suitable: {total - suitable} ({100*(total-suitable)/total:.1f}%)")

        # Most common disqualifiers
        disqualifier_counts = {}
        for result in classifications.values():
            for dq in result['disqualified_by']:
                disqualifier_counts[dq] = disqualifier_counts.get(dq, 0) + 1

        print("\nMost common disqualifiers:")
        for dq, count in sorted(disqualifier_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"  {dq}: {count}")


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

    # Generate annual telework lookup tables
    generate_annual_telework_lookups(
        ONET_BASE, CROSSWALK_PATH, OUTPUT_PATH, OEWS_BASE,
        start_year=2003, end_year=2025
    )
