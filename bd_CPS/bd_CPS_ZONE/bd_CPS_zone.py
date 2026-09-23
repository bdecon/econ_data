"""
bd_CPS_zone.py - Geographic zone assignment for CPS microdata

This module provides the ZONE variable, which assigns CPS observations to
70 geographic zones optimized for labor market analysis.

ZONE is available Sep 1995+ (30 years of complete data).
Pre-Sep 1995 excluded due to MSA suppression during Jun-Aug 1995.

Era boundaries (renumbered January 2026):
- ERA1: Sep 1995 - Apr 2004 (MSA/PMSA codes)
- ERA2: May 2004 - Jul 2015 (2003 CBSA codes)
- ERA3: Aug 2015 - Jul 2026 (2013 CBSA codes)
- ERA4: Aug 2026+ (2020 CBSA codes)

Usage:
    from bd_CPS_zone import assign_zone, ZONE_CATEGORIES, ZONEERA_CATEGORIES

    zone_result, zoneera = assign_zone(dfm, date)
    if zone_result is not None:
        dfm['ZONE'] = zone_result
        dfm['ZONEERA'] = zoneera

See CPSZ/CLAUDE.md for full documentation.
"""

import pandas as pd
import numpy as np

# =============================================================================
# ZONE: CPS Geographic Zone - Geographic zones for labor market analysis
# =============================================================================
# Renamed from CPSZ to ZONE (January 2026)
# Available Sep 1995+ (ERA1-ERA4); NaN for dates before Sep 1995

# Complete list of zone categories (70 total)
ZONE_CATEGORIES = [
    # 25 Metro zones
    'ALBUQUERQUE_METRO', 'ATLANTA_METRO', 'BAYAREA_METRO', 'BOSTON_METRO',
    'CHICAGO_METRO', 'DALLAS_METRO', 'DC_METRO', 'DENVER_METRO', 'DETROIT_METRO',
    'HOUSTON_METRO', 'KANSASCITY_METRO', 'LA_METRO', 'MIAMI_METRO',
    'MINNEAPOLIS_METRO', 'NYC_CITY', 'NY_METRO', 'ORLANDO_METRO', 'PHILLY_METRO',
    'PHOENIX_METRO', 'PORTLAND_METRO', 'RIVERSIDE_METRO', 'SANDIEGO_METRO',
    'SEATTLE_METRO', 'STLOUIS_METRO', 'TAMPA_METRO',
    # 25 Standalone states
    'AK', 'AL', 'AR', 'CT', 'HI', 'IA', 'ID', 'KY', 'LA', 'MS', 'MT', 'NC', 'ND',
    'NE', 'NV', 'OH', 'OK', 'RI', 'SC', 'SD', 'TN', 'UT', 'VT', 'WV', 'WY',
    # 16 State balance zones
    'CA_BALANCE', 'FL_BALANCE', 'GA_BALANCE', 'IN_BALANCE', 'KS_BALANCE',
    'MA_BALANCE', 'MI_BALANCE', 'MN_BALANCE', 'NJ_BALANCE', 'NY_BALANCE',
    'OR_BALANCE', 'PA_BALANCE', 'TX_BALANCE', 'VA_BALANCE', 'WA_BALANCE', 'WI_BALANCE',
    # 4 Combined remainder zones
    'MD_DE_BALANCE', 'MO_IL_BALANCE', 'MOUNTAIN_BALANCE', 'NH_ME',
]

# ZONEERA categories
ZONEERA_CATEGORIES = ['ERA1', 'ERA2', 'ERA3', 'ERA4']

# =============================================================================
# ERA1: Pre-CBSA MSA Mapping (Sep 1995 - April 2004)
# =============================================================================
# Uses 4-digit MSA/PMSA codes from 1990 and 1993 OMB definitions
# Both code sets included to handle 1995-1996 transition
# Note: Jun-Aug 1995 excluded from ZONE (MSA suppressed during redesign)

ZONEMSAMap = {
    # NYC CMSA - both eras (split by state/MPCSTAT like post-2004)
    5600: 'NYC_AREA', 5380: 'NYC_AREA', 5640: 'NYC_AREA', 3640: 'NYC_AREA',
    875: 'NYC_AREA', 5190: 'NYC_AREA', 8480: 'NYC_AREA', 5015: 'NYC_AREA',
    5660: 'NYC_AREA', 2281: 'NYC_AREA',  # 1993+ Newburgh, Dutchess
    5950: 'NYC_AREA',  # 1990 Orange County NY

    # LA CMSA - both eras
    4480: 'LA_METRO', 5945: 'LA_METRO', 8735: 'LA_METRO',  # 1993+
    360: 'LA_METRO', 6000: 'LA_METRO',  # 1990 Anaheim-Santa Ana, Oxnard-Ventura
    6780: 'RIVERSIDE_METRO',

    # Chicago CMSA - both eras
    1600: 'CHICAGO_METRO', 3740: 'CHICAGO_METRO',  # 1993+ Kankakee
    3965: 'CHICAGO_METRO', 620: 'CHICAGO_METRO', 3690: 'CHICAGO_METRO',  # 1990

    # Bay Area CMSA
    7360: 'BAYAREA_METRO', 5775: 'BAYAREA_METRO', 7400: 'BAYAREA_METRO',
    7500: 'BAYAREA_METRO', 8720: 'BAYAREA_METRO', 7485: 'BAYAREA_METRO',

    # Other CMSAs
    6160: 'PHILLY_METRO', 9160: 'PHILLY_METRO',
    8840: 'DC_METRO',
    2160: 'DETROIT_METRO', 440: 'DETROIT_METRO', 2640: 'DETROIT_METRO',
    1920: 'DALLAS_METRO', 2800: 'DALLAS_METRO',
    3360: 'HOUSTON_METRO', 1145: 'HOUSTON_METRO', 2920: 'HOUSTON_METRO',
    1120: 'BOSTON_METRO', 1200: 'BOSTON_METRO', 4160: 'BOSTON_METRO',
    4560: 'BOSTON_METRO', 5350: 'BOSTON_METRO',
    5000: 'MIAMI_METRO', 2680: 'MIAMI_METRO', 8960: 'MIAMI_METRO',
    7600: 'SEATTLE_METRO', 8200: 'SEATTLE_METRO', 1150: 'SEATTLE_METRO',
    6440: 'PORTLAND_METRO', 7080: 'PORTLAND_METRO',
    2080: 'DENVER_METRO', 1125: 'DENVER_METRO', 2670: 'DENVER_METRO', 3060: 'DENVER_METRO',

    # Standalone MSAs (not in CMSAs)
    520: 'ATLANTA_METRO', 6200: 'PHOENIX_METRO', 5120: 'MINNEAPOLIS_METRO',
    7320: 'SANDIEGO_METRO', 8280: 'TAMPA_METRO', 7040: 'STLOUIS_METRO',
    3760: 'KANSASCITY_METRO', 200: 'ALBUQUERQUE_METRO', 5960: 'ORLANDO_METRO',
}

# =============================================================================
# ERA2+: CBSA Mapping (May 2004 onward)
# =============================================================================
# Metro zones by CBSA code (including historical codes for ERA2)
# Note: NYC (35620) is handled separately - split into NYC_CITY and NY_METRO
# NJ portion of NYC metro goes to NJ_BALANCE
ZONEMetroMap = {
    # Current codes (ERA3+)
    47900: 'DC_METRO', 31080: 'LA_METRO',
    16980: 'CHICAGO_METRO', 14460: 'BOSTON_METRO', 37980: 'PHILLY_METRO',
    19100: 'DALLAS_METRO', 26420: 'HOUSTON_METRO', 12060: 'ATLANTA_METRO',
    33100: 'MIAMI_METRO', 41860: 'BAYAREA_METRO', 41940: 'BAYAREA_METRO', 42660: 'SEATTLE_METRO',
    38060: 'PHOENIX_METRO', 19820: 'DETROIT_METRO',
    40140: 'RIVERSIDE_METRO', 38900: 'PORTLAND_METRO',
    33460: 'MINNEAPOLIS_METRO', 41740: 'SANDIEGO_METRO', 10740: 'ALBUQUERQUE_METRO',
    45300: 'TAMPA_METRO', 36740: 'ORLANDO_METRO', 28140: 'KANSASCITY_METRO',
    19740: 'DENVER_METRO', 41180: 'STLOUIS_METRO',
    # Historical codes (ERA2 only, pre-Aug 2015)
    31100: 'LA_METRO', 71650: 'BOSTON_METRO', 26180: 'HI',
    # REMOVED: 29820 (Las Vegas) - NV now standalone
    # REMOVED: 14260 (Boise) - ID now standalone
}

# States where we carve out metros (used by shapefile generation)
# Note: Suppressed observations now assigned to balance zones (Jan 2026)
# Note: ID and NV removed (now standalone states)
ZONEStatesWithCarveouts = {
    'NY', 'NJ', 'DC', 'VA', 'MD', 'CA', 'IL', 'IN', 'WI', 'MA', 'NH',
    'PA', 'DE', 'TX', 'GA', 'FL', 'WA', 'OR', 'AZ', 'MI',
    'MN', 'NM', 'KS', 'MO', 'CO', 'HI'
}

# States where entire state is one zone (no ambiguity even if METSTAT is missing)
ZONESpecialNoAmbiguity = {'DC', 'HI'}

# Combined remainder zones - small state remainders grouped together
# Updated Jan 2026: NY/NJ split, VT standalone, NV standalone, AZ→MOUNTAIN
# Updated Jan 2026: UPPER_MIDWEST split into MN_BALANCE + WI_BALANCE
ZONERemainderCombos = {
    # ('NY', 'NJ'): REMOVED - now NY_BALANCE and NJ_BALANCE separately
    ('MD', 'DE'): 'MD_DE_BALANCE',
    ('ME', 'NH'): 'NH_ME',           # VT now standalone
    # ('WI', 'MN'): REMOVED - now MN_BALANCE and WI_BALANCE separately
    ('MO', 'IL'): 'MO_IL_BALANCE',
    # ('AZ', 'NV'): REMOVED - NV now standalone
    ('CO', 'NM', 'AZ'): 'MOUNTAIN_BALANCE',  # AZ joined from former SOUTHWEST
}

# Standalone states - no metro carve-outs, not combined with others
# Updated Jan 2026: Added ID, NV (folded metros), VT (split from NORTHERN_NE)
ZONEStandaloneStates = {
    'AK', 'AL', 'AR', 'CT', 'IA', 'ID', 'KY', 'LA', 'MS', 'MT',
    'NC', 'ND', 'NE', 'NV', 'OH', 'OK', 'SC', 'SD', 'TN', 'UT', 'VT', 'WV', 'WY'
}

# =============================================================================
# ERA Transitions Configuration
# =============================================================================
# Defines when each ERA starts and how transitions occur.
# - 'hard': All observations switch at once on the specified date
# - 'phased': 16-month MIS rotation phase-in (verified against ERA2→ERA3)
#
# Phased transitions follow CPS 4-8-4 rotation pattern:
# - Months 0-3: MIS 1-4 transition (new entrants, one per month)
# - Months 4-11: Gap (MIS 1-4 on new era, MIS 5-8 on old era)
# - Months 12-15: MIS 5-8 transition (returning cohort, one per month)

ERA_TRANSITIONS = [
    {
        'to_era': 'ERA1',
        'type': 'hard',
        'date': (1995, 9, 1),  # Sep 1995 - ZONE variable starts
    },
    {
        'to_era': 'ERA2',
        'type': 'hard',
        'date': (2004, 5, 1),  # May 2004 - MSA→CBSA instant switch
    },
    {
        'to_era': 'ERA3',
        'type': 'phased',
        'phase_start': (2014, 5, 1),   # May 2014 - first MIS transitions
        'phase_end': (2015, 8, 1),     # Aug 2015 - last MIS transitions
    },
    {
        'to_era': 'ERA4',
        'type': 'phased',
        'phase_start': (2025, 5, 1),   # May 2025 - first MIS transitions
        'phase_end': (2026, 8, 1),     # Aug 2026 - last MIS transitions
    },
]


def _mis_has_transitioned(mis, months_into_phase):
    """
    Determine if MIS group has transitioned given months into phase-in.

    The 16-month pattern (verified against ERA2→ERA3 actual data):
    - Months 0-3: MIS 1-4 transition (one per month)
    - Months 4-11: Gap (first cohort out of sample for 8 months)
    - Months 12-15: MIS 5-8 transition (one per month as they return)

    Parameters
    ----------
    mis : int
        Month-in-sample rotation group (1-8)
    months_into_phase : int
        Months since phase-in started (0 = first month of phase-in)

    Returns
    -------
    bool
        True if this MIS group has transitioned to the new era
    """
    if mis <= 4:
        # First-time participants: transition in months 0-3
        return months_into_phase >= (mis - 1)
    else:
        # Returning participants: transition in months 12-15
        return months_into_phase >= (mis - 5) + 12


def _get_zoneera(year, month, mis):
    """
    Determine ZONEERA for a single observation based on date and MIS.

    Parameters
    ----------
    year : int
        Survey year
    month : int
        Survey month (1-12)
    mis : int
        Month-in-sample rotation group (1-8)

    Returns
    -------
    str or None
        Era identifier ('ERA1', 'ERA2', 'ERA3', 'ERA4') or None if before ZONE starts
    """
    current_era = None

    for trans in ERA_TRANSITIONS:
        if trans['type'] == 'hard':
            ty, tm, td = trans['date']
            if (year, month) >= (ty, tm):
                current_era = trans['to_era']

        elif trans['type'] == 'phased':
            sy, sm, sd = trans['phase_start']
            ey, em, ed = trans['phase_end']

            if (year, month) >= (ey, em):
                # After phase-in complete: all observations on new era
                current_era = trans['to_era']
            elif (year, month) >= (sy, sm):
                # During phase-in: check MIS
                months_in = (year - sy) * 12 + (month - sm)
                if _mis_has_transitioned(mis, months_in):
                    current_era = trans['to_era']
                # else: keep previous era

    return current_era


def assign_zone(dfm, date):
    """
    Assign geographic ZONE and ZONEERA based on date and MIS.

    Parameters
    ----------
    dfm : pd.DataFrame
        DataFrame with geographic columns:
        - ERA1 (Sep 1995-Apr 2004): STATE, MSA, MPCSTAT, MIS
        - ERA2+ (May 2004+): STATE, CBSA, MPCSTAT, METSTAT, MIS
    date : pd.Timestamp
        Date of the CPS survey month

    Returns
    -------
    tuple (pd.Categorical or None, pd.Categorical or None)
        (ZONE series, ZONEERA series) - both None for dates before Sep 1995

    Notes
    -----
    ZONE/ZONEERA start Sep 1995, providing 30 years of complete data.
    Pre-Sep 1995 returns (None, None) for consistent schema with no valid data.

    Era boundaries (renumbered Jan 2026):
    - ERA1: Sep 1995 - Apr 2004 (MSA codes)
    - ERA2: May 2004 - Aug 2015 (2003 CBSA)
    - ERA3: Aug 2015 - Aug 2026 (2013 CBSA)
    - ERA4: Aug 2026+ (2020 CBSA)

    During phased transitions (ERA2→ERA3, ERA3→ERA4), ZONEERA is assigned
    per-observation based on MIS rotation group. The 16-month phase-in
    pattern follows the CPS 4-8-4 rotation design.
    """
    # ZONE available from Sep 1995 onward (30 years of complete data)
    # Pre-Sep 1995: Return None for both (consistent schema, no valid data)
    if date < pd.to_datetime('1995-09-01'):
        return None, None

    # Determine ZONEERA per observation using MIS
    year = date.year
    month = date.month

    # Get MIS as integer, defaulting to 1 if missing (conservative: assigns to new era first)
    if 'MIS' in dfm.columns:
        mis_values = pd.to_numeric(dfm['MIS'], errors='coerce').fillna(1).astype(int)
    else:
        mis_values = pd.Series([1] * len(dfm), index=dfm.index)

    # Compute ZONEERA for each observation
    zoneera = mis_values.apply(lambda mis: _get_zoneera(year, month, mis))
    zoneera = pd.Categorical(zoneera, categories=ZONEERA_CATEGORIES)

    # =========================================================================
    # ERA1: Pre-CBSA (Sep 1995 - April 2004) - uses MSA codes
    # =========================================================================
    if date < pd.to_datetime('2004-05-01'):
        # Check if MSA column exists
        if 'MSA' not in dfm.columns:
            return None, None

        msa_num = pd.to_numeric(dfm['MSA'].astype(str), errors='coerce').fillna(0).astype(int)

        # Initialize ZONE
        zone = pd.Series([None] * len(dfm), index=dfm.index, dtype=object)

        # MSA=-1 means no geographic identification - cannot assign (primarily 1995)
        unidentified = (msa_num == -1)

        # 1. Standalone states: entire state is one zone (MSA doesn't matter)
        # These work even with MSA=-1 since the whole state = one zone
        zone.loc[dfm['STATE'] == 'HI'] = 'HI'
        zone.loc[dfm['STATE'] == 'CT'] = 'CT'
        zone.loc[dfm['STATE'] == 'RI'] = 'RI'
        zone.loc[dfm['STATE'] == 'DC'] = 'DC_METRO'
        for st in ZONEStandaloneStates:
            zone.loc[dfm['STATE'] == st] = st

        # 2. Metro zones by MSA code
        for msa_code, zone_name in ZONEMSAMap.items():
            msa_mask = (msa_num == msa_code) & zone.isna() & ~unidentified
            zone.loc[msa_mask] = zone_name

        # 3. NYC special case: split by state (same logic as post-2004)
        nyc_msa_mask = zone.eq('NYC_AREA')
        nyc_ny_mask = nyc_msa_mask & (dfm['STATE'] == 'NY')
        nyc_city_mask = nyc_ny_mask & (dfm['MPCSTAT'] == 'Principal City')
        zone.loc[nyc_city_mask] = 'NYC_CITY'
        zone.loc[nyc_ny_mask & ~nyc_city_mask] = 'NY_METRO'
        zone.loc[nyc_msa_mask & (dfm['STATE'] == 'NJ')] = 'NJ_BALANCE'
        zone.loc[nyc_msa_mask & (dfm['STATE'] == 'PA')] = 'PA_BALANCE'

        # 4. Combined remainder zones
        for states_tuple, zone_name in ZONERemainderCombos.items():
            combo_mask = dfm['STATE'].isin(states_tuple) & zone.isna() & ~unidentified
            zone.loc[combo_mask] = zone_name

        # 5. State balance zones (remaining assigned observations)
        balance_mask = zone.isna() & ~unidentified
        zone.loc[balance_mask] = dfm.loc[balance_mask, 'STATE'].astype(str) + '_BALANCE'

        # unidentified (MSA=-1) remains NaN
        return pd.Categorical(zone, categories=ZONE_CATEGORIES), zoneera

    # =========================================================================
    # ERA2+: CBSA era (May 2004 onward)
    # =========================================================================

    # Convert CBSA to numeric for comparison
    cbsa_num = pd.to_numeric(dfm['CBSA'].astype(str), errors='coerce').fillna(0).astype(int)

    # Initialize ZONE
    zone = pd.Series([None] * len(dfm), index=dfm.index, dtype=object)

    # 2. Special cases: entire state is one zone (takes precedence)
    zone.loc[dfm['STATE'] == 'HI'] = 'HI'
    zone.loc[dfm['STATE'] == 'CT'] = 'CT'
    zone.loc[dfm['STATE'] == 'RI'] = 'RI'
    zone.loc[dfm['STATE'] == 'DC'] = 'DC_METRO'
    # Added Jan 2026: Standalone states from Tier 1 changes
    zone.loc[dfm['STATE'] == 'VT'] = 'VT'
    zone.loc[dfm['STATE'] == 'NV'] = 'NV'
    zone.loc[dfm['STATE'] == 'ID'] = 'ID'

    # 3. Metro zones by CBSA code
    for cbsa_code, zone_name in ZONEMetroMap.items():
        cbsa_mask = (cbsa_num == cbsa_code) & zone.isna()
        zone.loc[cbsa_mask] = zone_name

    # 3.5 NYC special case: split by state
    # NYC_CITY = 5 boroughs (NY + Principal City)
    # NY_METRO = NY suburbs in NYC CBSA (not principal city)
    # NJ portion of NYC CBSA → falls through to NJ_BALANCE via remainder logic
    nyc_cbsa_mask = (cbsa_num == 35620) & zone.isna()
    nyc_ny_mask = nyc_cbsa_mask & (dfm['STATE'] == 'NY')
    nyc_city_mask = nyc_ny_mask & (dfm['MPCSTAT'] == 'Principal City')
    zone.loc[nyc_city_mask] = 'NYC_CITY'
    zone.loc[nyc_ny_mask & ~nyc_city_mask] = 'NY_METRO'
    # NJ portion (nyc_cbsa_mask & STATE='NJ') remains unassigned here,
    # will be picked up by NJ_BALANCE in step 6

    # 4. Standalone states (no carve-outs)
    standalone_mask = dfm['STATE'].isin(ZONEStandaloneStates) & zone.isna()
    zone.loc[standalone_mask] = dfm.loc[standalone_mask, 'STATE'].astype(str)

    # 5. Combined remainder zones
    for states_tuple, zone_name in ZONERemainderCombos.items():
        combo_mask = dfm['STATE'].isin(states_tuple) & zone.isna()
        zone.loc[combo_mask] = zone_name

    # 6. State balance zones (all remaining unassigned observations)
    balance_mask = zone.isna()
    zone.loc[balance_mask] = dfm.loc[balance_mask, 'STATE'].astype(str) + '_BALANCE'

    return pd.Categorical(zone, categories=ZONE_CATEGORIES), zoneera
