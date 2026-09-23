"""
Job Zone Classifier for CPS Occupations

This module assigns O*NET Job Zones to CPS occupations, enabling education
mismatch analysis. Job Zones classify occupations by the preparation level
(education, experience, training) typically needed.

Job Zone Definitions (from O*NET):
- Zone 1: Little or No Preparation Needed (some may require HS diploma)
- Zone 2: Some Preparation Needed (usually require HS diploma)
- Zone 3: Medium Preparation Needed (vocational/associate's degree)
- Zone 4: Considerable Preparation Needed (most require bachelor's)
- Zone 5: Extensive Preparation Needed (most require graduate degree)

The OCCJZ variable represents the employment-weighted average Job Zone (1-5)
for each occupation. Use this to compute education mismatch:

    edu_to_jz = {'LTHS': 1, 'HS': 2, 'SC': 3, 'COLL': 4, 'ADV': 5}
    cps['WORKER_JZ'] = cps['EDUC'].map(edu_to_jz)
    cps['EDUMISMATCH'] = cps['WORKER_JZ'] - cps['OCCJZ']
    # Positive = overqualified, Negative = underqualified

To derive binary BA requirement (similar to NY Fed methodology):
    cps['BA_REQUIRED'] = (cps['OCCJZ'] >= 4).astype(int)

Reference:
    Federal Reserve Bank of New York, College Labor Market.
    https://www.newyorkfed.org/research/college-labor-market

Usage:
    from jz_classifier import generate_annual_jz_lookups

    generate_annual_jz_lookups(
        onet_base_path='/path/to/onet/',
        crosswalk_path='/path/to/crosswalks/',
        output_path='/path/to/output/',
        oews_base_path='/path/to/oews/'
    )
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Import shared functions from pd_dwc_classifier
from pd_dwc_classifier import (
    load_oews_employment,
    load_census_crosswalk,
    onet_soc_to_soc,
    get_period_config,
    get_oews_year,
)


def load_job_zones(onet_path):
    """
    Load O*NET Job Zone data.

    Parameters
    ----------
    onet_path : str or Path
        Path to O*NET database text files

    Returns
    -------
    DataFrame with columns: onet_code, job_zone
    """
    onet_path = Path(onet_path)
    jz_file = onet_path / 'Job Zones.txt'

    if not jz_file.exists():
        raise FileNotFoundError(f"Job Zones file not found: {jz_file}")

    df = pd.read_csv(jz_file, sep='\t')
    df = df.rename(columns={'O*NET-SOC Code': 'onet_code', 'Job Zone': 'job_zone'})

    return df[['onet_code', 'job_zone']]


def classify_job_zones(onet_path):
    """
    Get Job Zone for each O*NET-SOC code.

    Parameters
    ----------
    onet_path : str or Path
        Path to O*NET database text files

    Returns
    -------
    dict : {onet_code: job_zone}
    """
    job_zones = load_job_zones(onet_path)
    return dict(zip(job_zones['onet_code'], job_zones['job_zone']))


def aggregate_jz_to_soc(classifications):
    """
    Aggregate O*NET-SOC Job Zones to SOC level.

    Parameters
    ----------
    classifications : dict
        Output from classify_job_zones()

    Returns
    -------
    DataFrame with columns: soc_code, job_zone
    """
    records = []
    for onet_code, jz in classifications.items():
        soc = onet_soc_to_soc(onet_code)
        records.append({
            'onet_code': onet_code,
            'soc_code': soc,
            'job_zone': jz,
        })

    df = pd.DataFrame(records)

    # Aggregate to SOC level (mean of O*NET subcodes)
    soc_agg = df.groupby('soc_code').agg({
        'job_zone': 'mean',
    }).reset_index()

    return soc_agg


def match_soc_to_jz(census_soc, soc_jz_df, emp_dict=None):
    """
    Get Job Zone for a Census SOC code via prefix matching.

    Parameters
    ----------
    census_soc : str
        SOC code from Census crosswalk
    soc_jz_df : DataFrame
        SOC-level Job Zones from aggregate_jz_to_soc()
    emp_dict : dict, optional
        Employment by SOC code from load_oews_employment()

    Returns
    -------
    float or None : Job Zone (1-5, may be fractional for aggregates)
    """
    if pd.isna(census_soc):
        return None

    census_soc = str(census_soc).strip()

    # Handle combined codes (e.g., "15-1132, 15-1133")
    if ',' in census_soc:
        parts = [s.strip() for s in census_soc.split(',')]
        scores = [match_soc_to_jz(p, soc_jz_df, emp_dict) for p in parts]
        scores = [s for s in scores if s is not None]
        if scores:
            return np.mean(scores)
        return None

    # Handle range codes (e.g., "11-0000 - 13-0000")
    if ' - ' in census_soc:
        census_soc = census_soc.split(' - ')[0].strip()

    # Exact match
    exact = soc_jz_df[soc_jz_df['soc_code'] == census_soc]
    if len(exact) > 0:
        return exact.iloc[0]['job_zone']

    # Prefix matching for aggregate codes
    for trim in [1, 2, 3]:
        if len(census_soc) > trim:
            prefix = census_soc[:-trim]
            matches = soc_jz_df[soc_jz_df['soc_code'].str.startswith(prefix)]
            if len(matches) > 0:
                # Use employment weighting if available
                if emp_dict:
                    total_emp = 0
                    weighted_sum = 0
                    for _, row in matches.iterrows():
                        emp = emp_dict.get(row['soc_code'], 0)
                        total_emp += emp
                        weighted_sum += row['job_zone'] * emp

                    if total_emp > 0:
                        return weighted_sum / total_emp

                # Unweighted average (fallback)
                return matches['job_zone'].mean()

    return None


def create_jz_lookup(onet_path, census_crosswalk, crosswalk_path,
                     onet_version=None, oews_path=None):
    """
    Create Job Zone lookup table for a Census occupation code system.

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
    DataFrame with columns: census_code, occupation_title, job_zone, onet_version
    """
    # Classify O*NET jobs
    classifications = classify_job_zones(onet_path)

    # Aggregate to SOC level
    soc_jz = aggregate_jz_to_soc(classifications)

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

    # Match Census codes to Job Zones
    records = []
    for _, row in census_df.iterrows():
        job_zone = match_soc_to_jz(row['soc_code'], soc_jz, emp_dict)
        record = {
            'census_code': int(row['census_code']),
            'occupation_title': row['census_title'],
            'job_zone': job_zone if job_zone is not None else np.nan,
        }
        if onet_version:
            record['onet_version'] = onet_version
        records.append(record)

    result = pd.DataFrame(records)

    # Print summary
    matched = result['job_zone'].notna().sum()
    total = len(result)
    mean_jz = result['job_zone'].mean()
    ba_required = (result['job_zone'] >= 4).sum()
    print(f"Job Zone Lookup: {matched}/{total} Census codes matched ({100*matched/total:.1f}%)")
    print(f"  Mean Job Zone: {mean_jz:.2f}")
    print(f"  Requires BA (JZ >= 4): {ba_required} occupations ({100*ba_required/total:.1f}%)")

    return result


def generate_annual_jz_lookups(onet_base_path, crosswalk_path, output_path,
                               oews_base_path, start_year=2003, end_year=2025):
    """
    Generate annual Job Zone lookup tables for CPS years.

    Creates one lookup table per year with year-appropriate OEWS employment weights.
    Files are named jz_YYYY.csv.

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
    soc_jz_cache = {}

    print(f"Generating annual Job Zone lookup tables for {start_year}-{end_year}")
    print("=" * 60)

    for year in range(start_year, end_year + 1):
        census_type, onet_subdir, onet_ver = get_period_config(year)
        oews_year = get_oews_year(year)
        oews_dir = f'oesm{str(oews_year)[2:]}nat'
        output_file = f'jz_{year}.csv'

        print(f"\n{year}: {census_type}, O*NET {onet_ver}, OEWS {oews_year}")

        # Load/cache O*NET classifications
        cache_key = (census_type, onet_ver)
        if cache_key not in classification_cache:
            onet_path = onet_base_path / onet_subdir
            classifications = classify_job_zones(onet_path)
            soc_jz = aggregate_jz_to_soc(classifications)
            census_df = load_census_crosswalk(census_type, crosswalk_path)
            classification_cache[cache_key] = classifications
            soc_jz_cache[cache_key] = (soc_jz, census_df, onet_ver)

        soc_jz, census_df, onet_ver = soc_jz_cache[cache_key]

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
            job_zone = match_soc_to_jz(row['soc_code'], soc_jz, emp_dict)
            record = {
                'census_code': int(row['census_code']),
                'occupation_title': row['census_title'],
                'job_zone': job_zone if job_zone is not None else np.nan,
                'onet_version': onet_ver,
                'oews_year': oews_year,
            }
            records.append(record)

        lookup = pd.DataFrame(records)
        lookup.to_csv(output_path / output_file, index=False)

        # Summary stats
        mean_jz = lookup['job_zone'].mean()
        ba_pct = (lookup['job_zone'] >= 4).mean() * 100
        print(f"  Mean Job Zone: {mean_jz:.2f}, Requires BA: {ba_pct:.1f}%")

    print("\n" + "=" * 60)
    print(f"Generated {end_year - start_year + 1} annual Job Zone lookup tables")
    print("=" * 60)


def print_job_zone_distribution(onet_path):
    """
    Print Job Zone distribution for debugging/inspection.

    Parameters
    ----------
    onet_path : str or Path
        Path to O*NET database text files
    """
    job_zones = load_job_zones(onet_path)

    print(f"Total O*NET-SOC codes: {len(job_zones)}")
    print("\nJob Zone Distribution:")

    for jz in range(1, 6):
        count = (job_zones['job_zone'] == jz).sum()
        pct = count / len(job_zones) * 100
        print(f"  Zone {jz}: {count:4d} ({pct:5.1f}%)")

    print(f"\nMean Job Zone: {job_zones['job_zone'].mean():.2f}")


if __name__ == '__main__':
    # Default paths
    ONET_BASE = '/home/brian/Documents/CPS/data/onet/'
    CROSSWALK_PATH = '/home/brian/Documents/CPS_ONET/crosswalks/'
    OUTPUT_PATH = '/home/brian/Documents/CPS_ONET/output/'
    OEWS_BASE = '/home/brian/Documents/CPS_ONET/data/oews/'

    # Show Job Zone distribution for latest O*NET
    print("O*NET 25.1 Job Zone Distribution:")
    print("-" * 40)
    print_job_zone_distribution(ONET_BASE + 'db_25_1_text/')
    print()

    # Generate annual Job Zone lookup tables
    generate_annual_jz_lookups(
        ONET_BASE, CROSSWALK_PATH, OUTPUT_PATH, OEWS_BASE,
        start_year=2003, end_year=2025
    )
