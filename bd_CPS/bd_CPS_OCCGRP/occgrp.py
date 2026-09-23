"""
OCCGRP: Class-Relevant Occupation Group Variable

Creates a 10-category occupation classification based on OCC18 (2018 Census codes)
with class-relevant splits of the Sales category.

Categories:
    1: Managers           - All management + retail supervisors
    2: STEM Professionals - Computer, engineering, sciences
    3: Health Professionals - Healthcare practitioners/technical
    4: Business/Legal/Prof Sales - Business ops, legal, insurance/real estate/B2B sales
    5: Education/Social/Arts - Teachers, social workers, artists
    6: Skilled Blue-Collar - Construction, mechanics, protective
    7: Office/Clerical    - Admin support, misc sales
    8: Production/Transport - Factory, warehouse, drivers
    9: Service Workers    - Food, cleaning, personal care, cashiers/retail
   10: Agriculture        - Farming, fishing, forestry

Design notes:
- Managers unified despite wage heterogeneity (authority/power is the defining feature)
- Sales split by skill/class:
  - High-skill (insurance, real estate, B2B) → Business/Legal (#4)
  - Low-skill (cashiers, retail) → Service Workers (#9)
  - Retail supervisors → Managers (#1)
- Stock clerks (9645) kept in Office/Clerical per OCC03M fix (reverting BLS 2020 change)

Author: Generated for bd_CPS project
Date: January 2026
"""

import numpy as np
import pandas as pd

# Category labels
OCCGRP_LABELS = {
    1: 'Managers',
    2: 'STEM Professionals',
    3: 'Health Professionals',
    4: 'Business/Legal/Prof Sales',
    5: 'Education/Social/Arts',
    6: 'Skilled Blue-Collar',
    7: 'Office/Clerical',
    8: 'Production/Transport',
    9: 'Service Workers',
    10: 'Agriculture'
}

# High-skill sales codes (→ Business/Legal, category 4)
HIGH_SKILL_SALES = {
    4710,  # First-line supervisors of non-retail sales workers
    4800,  # Advertising sales agents
    4810,  # Insurance sales agents
    4820,  # Securities, commodities, and financial services sales agents
    4840,  # Sales representatives, wholesale and manufacturing
    4850,  # Sales representatives of services, except advertising, insurance, financial services, and travel
    4920,  # Real estate brokers and sales agents
    4930,  # Sales engineers
}

# Low-skill sales codes (→ Service Workers, category 9)
LOW_SKILL_SALES = {
    4720,  # Cashiers
    4740,  # Counter and rental clerks
    4760,  # Retail salespersons
    4940,  # Telemarketers
    4950,  # Door-to-door sales workers, news and street vendors, and related workers
}

# Misc sales codes (→ Office/Clerical, category 7)
MISC_SALES = {
    4750,  # Parts salespersons
    4830,  # Travel agents
    4900,  # Models, demonstrators, and product promoters
    4965,  # Sales and related workers, all other
}


def assign_occgrp_from_occ18(occ18_series):
    """
    Assign OCCGRP category based on OCC18 (2018 Census occupation codes).

    Parameters
    ----------
    occ18_series : pd.Series
        OCC18 occupation codes

    Returns
    -------
    pd.Series
        OCCGRP category (1-10) as categorical
    """
    # Convert to numeric (OCC18 may be stored as categorical)
    if hasattr(occ18_series, 'cat'):
        occ = pd.to_numeric(occ18_series, errors='coerce').values
    else:
        occ = occ18_series.values
    result = np.full(len(occ), np.nan, dtype='float32')

    # Category 1: MANAGERS
    # OCC18 10-440 (all of OCC03D=1) + retail supervisors (4700)
    mask = ((occ >= 10) & (occ <= 440)) | (occ == 4700)
    result[mask] = 1

    # Category 2: STEM PROFESSIONALS
    # Computer/Mathematical (1005-1240)
    # Architecture/Engineering (1305-1560)
    # Life/Physical/Social Science (1600-1980)
    mask = (((occ >= 1005) & (occ <= 1240)) |
            ((occ >= 1305) & (occ <= 1560)) |
            ((occ >= 1600) & (occ <= 1980)))
    result[mask] = 2

    # Category 3: HEALTH PROFESSIONALS
    # Healthcare Practitioners/Technical (3000-3550)
    mask = (occ >= 3000) & (occ <= 3550)
    result[mask] = 3

    # Category 4: BUSINESS/LEGAL/PROFESSIONAL SALES
    # Business/Financial Operations (500-960)
    # Legal (2100-2180)
    # Plus high-skill sales
    mask = (((occ >= 500) & (occ <= 960)) |
            ((occ >= 2100) & (occ <= 2180)) |
            np.isin(occ, list(HIGH_SKILL_SALES)))
    result[mask] = 4

    # Category 5: EDUCATION/SOCIAL/ARTS
    # Community/Social Service (2001-2060)
    # Education/Training/Library (2205-2555)
    # Arts/Design/Entertainment (2600-2960)
    mask = (((occ >= 2001) & (occ <= 2060)) |
            ((occ >= 2205) & (occ <= 2555)) |
            ((occ >= 2600) & (occ <= 2960)))
    result[mask] = 5

    # Category 6: SKILLED BLUE-COLLAR
    # Protective Service (3700-3960)
    # Construction/Extraction (6200-6950)
    # Installation/Maintenance/Repair (7000-7640)
    mask = (((occ >= 3700) & (occ <= 3960)) |
            ((occ >= 6200) & (occ <= 6950)) |
            ((occ >= 7000) & (occ <= 7640)))
    result[mask] = 6

    # Category 7: OFFICE/CLERICAL
    # Office/Administrative Support (5000-5940)
    # Plus stock clerks (9645) - kept here per OCC03M fix
    # Plus misc sales
    mask = (((occ >= 5000) & (occ <= 5940)) |
            (occ == 9645) |
            np.isin(occ, list(MISC_SALES)))
    result[mask] = 7

    # Category 8: PRODUCTION/TRANSPORT
    # Production (7700-8990)
    # Transportation/Material Moving (9005-9760)
    # EXCEPT stock clerks (9645) which go to Office/Clerical
    mask = (((occ >= 7700) & (occ <= 8990)) |
            (((occ >= 9005) & (occ <= 9760)) & (occ != 9645)))
    result[mask] = 8

    # Category 9: SERVICE WORKERS
    # Healthcare Support (3601-3655)
    # Food Preparation/Serving (4000-4160)
    # Building/Grounds Cleaning (4200-4255)
    # Personal Care/Service (4330-4655)
    # Plus low-skill sales
    mask = (((occ >= 3601) & (occ <= 3655)) |
            ((occ >= 4000) & (occ <= 4160)) |
            ((occ >= 4200) & (occ <= 4255)) |
            ((occ >= 4330) & (occ <= 4655)) |
            np.isin(occ, list(LOW_SKILL_SALES)))
    result[mask] = 9

    # Category 10: AGRICULTURE
    # Farming/Fishing/Forestry (6005-6130)
    mask = (occ >= 6005) & (occ <= 6130)
    result[mask] = 10

    # Convert to categorical
    return pd.Categorical(result, categories=list(range(1, 11)), ordered=True)


def assign_occgrp_from_occ10(occ10_series):
    """
    Assign OCCGRP category based on OCC10 (2010 Census occupation codes).

    OCC10 codes are very similar to OCC18. Key differences:
    - Stock Clerks: OCC10=5620 (Office/Admin range) → Office/Clerical (7)
    - A few codes that split in 2018 are assigned to primary category

    Parameters
    ----------
    occ10_series : pd.Series
        OCC10 occupation codes

    Returns
    -------
    pd.Series
        OCCGRP category (1-10) as categorical
    """
    # Convert to numeric (OCC10 may be stored as categorical)
    if hasattr(occ10_series, 'cat'):
        occ = pd.to_numeric(occ10_series, errors='coerce').values
    else:
        occ = occ10_series.values
    result = np.full(len(occ), np.nan, dtype='float32')

    # Category 1: MANAGERS
    # OCC10 10-430 + retail supervisors (4700)
    # Note: OCC10 max is 430 vs OCC18 max 440
    mask = ((occ >= 10) & (occ <= 430)) | (occ == 4700)
    result[mask] = 1

    # Category 2: STEM PROFESSIONALS
    # Computer/Mathematical (1005-1240)
    # Architecture/Engineering (1300-1560) - OCC10 starts at 1300 vs 1305
    # Life/Physical/Social Science (1600-1965) - OCC10 max 1965 vs 1980
    mask = (((occ >= 1005) & (occ <= 1240)) |
            ((occ >= 1300) & (occ <= 1560)) |
            ((occ >= 1600) & (occ <= 1965)))
    result[mask] = 2

    # Category 3: HEALTH PROFESSIONALS
    # Healthcare Practitioners/Technical (3000-3540)
    # Note: OCC10=3540 (Other Healthcare) stays in Health (split to STEM in OCC18)
    mask = (occ >= 3000) & (occ <= 3540)
    result[mask] = 3

    # Category 4: BUSINESS/LEGAL/PROFESSIONAL SALES
    # Business/Financial Operations (500-960)
    # Legal (2100-2160) - OCC10 includes 2160 (split in OCC18)
    # Plus high-skill sales (same codes as OCC18)
    mask = (((occ >= 500) & (occ <= 960)) |
            ((occ >= 2100) & (occ <= 2160)) |
            np.isin(occ, list(HIGH_SKILL_SALES)))
    result[mask] = 4

    # Category 5: EDUCATION/SOCIAL/ARTS
    # Community/Social Service (2000-2060) - OCC10 starts at 2000 vs 2001
    # Education/Training/Library (2200-2550) - OCC10: 2200-2550
    # Arts/Design/Entertainment (2600-2960)
    mask = (((occ >= 2000) & (occ <= 2060)) |
            ((occ >= 2200) & (occ <= 2550)) |
            ((occ >= 2600) & (occ <= 2960)))
    result[mask] = 5

    # Category 6: SKILLED BLUE-COLLAR
    # Protective Service (3700-3960)
    # Construction/Extraction (6200-6940) - OCC10 max 6940 vs 6950
    # Installation/Maintenance/Repair (7000-7630) - OCC10 max 7630 vs 7640
    mask = (((occ >= 3700) & (occ <= 3960)) |
            ((occ >= 6200) & (occ <= 6940)) |
            ((occ >= 7000) & (occ <= 7630)))
    result[mask] = 6

    # Category 7: OFFICE/CLERICAL
    # Office/Administrative Support (5000-5940)
    # PLUS Stock Clerks (5620) - key difference from OCC18!
    # Plus misc sales (same codes as OCC18)
    # Note: 5620 is already in the 5000-5940 range, so no special handling needed
    mask = (((occ >= 5000) & (occ <= 5940)) |
            np.isin(occ, list(MISC_SALES)))
    result[mask] = 7

    # Category 8: PRODUCTION/TRANSPORT
    # Production (7700-8965) - OCC10 max 8965 vs 8990
    # Transportation/Material Moving (9000-9750) - OCC10: 9000-9750
    # Note: OCC10=9510 (Crane Operators) stays in Production/Transport
    mask = (((occ >= 7700) & (occ <= 8965)) |
            ((occ >= 9000) & (occ <= 9750)))
    result[mask] = 8

    # Category 9: SERVICE WORKERS
    # Healthcare Support (3600-3655)
    # Food Preparation/Serving (4000-4160)
    # Building/Grounds Cleaning (4200-4250) - OCC10 max 4250 vs 4255
    # Personal Care/Service (4300-4650) - OCC10: 4300-4650
    # Plus low-skill sales (same codes as OCC18)
    mask = (((occ >= 3600) & (occ <= 3655)) |
            ((occ >= 4000) & (occ <= 4160)) |
            ((occ >= 4200) & (occ <= 4250)) |
            ((occ >= 4300) & (occ <= 4650)) |
            np.isin(occ, list(LOW_SKILL_SALES)))
    result[mask] = 9

    # Category 10: AGRICULTURE
    # Farming/Fishing/Forestry (6005-6130)
    mask = (occ >= 6005) & (occ <= 6130)
    result[mask] = 10

    # Convert to categorical
    return pd.Categorical(result, categories=list(range(1, 11)), ordered=True)


def assign_occgrp_from_occ00(occ00_series):
    """
    Assign OCCGRP category based on OCC00 (2002 Census occupation codes).

    OCC00 codes are very similar to OCC10. Key differences from OCC10:
    - Some categories have slightly different max codes
    - Agriculture starts at 6000 vs 6005

    Parameters
    ----------
    occ00_series : pd.Series
        OCC00 occupation codes

    Returns
    -------
    pd.Series
        OCCGRP category (1-10) as categorical
    """
    # Convert to numeric (OCC00 may be stored as categorical)
    if hasattr(occ00_series, 'cat'):
        occ = pd.to_numeric(occ00_series, errors='coerce').values
    else:
        occ = occ00_series.values
    result = np.full(len(occ), np.nan, dtype='float32')

    # Category 1: MANAGERS
    # OCC00 10-430 + retail supervisors (4700)
    mask = ((occ >= 10) & (occ <= 430)) | (occ == 4700)
    result[mask] = 1

    # Category 2: STEM PROFESSIONALS
    # Computer/Mathematical (1000-1240) - OCC00 starts at 1000 vs 1005
    # Architecture/Engineering (1300-1560)
    # Life/Physical/Social Science (1600-1960) - OCC00 max 1960 vs 1965
    mask = (((occ >= 1000) & (occ <= 1240)) |
            ((occ >= 1300) & (occ <= 1560)) |
            ((occ >= 1600) & (occ <= 1960)))
    result[mask] = 2

    # Category 3: HEALTH PROFESSIONALS
    # Healthcare Practitioners/Technical (3000-3540)
    mask = (occ >= 3000) & (occ <= 3540)
    result[mask] = 3

    # Category 4: BUSINESS/LEGAL/PROFESSIONAL SALES
    # Business/Financial Operations (500-950) - OCC00 max 950 vs 960
    # Legal (2100-2150) - OCC00 max 2150 vs 2160
    # Plus high-skill sales (same codes)
    mask = (((occ >= 500) & (occ <= 950)) |
            ((occ >= 2100) & (occ <= 2150)) |
            np.isin(occ, list(HIGH_SKILL_SALES)))
    result[mask] = 4

    # Category 5: EDUCATION/SOCIAL/ARTS
    # Community/Social Service (2000-2060)
    # Education/Training/Library (2200-2550)
    # Arts/Design/Entertainment (2600-2960)
    mask = (((occ >= 2000) & (occ <= 2060)) |
            ((occ >= 2200) & (occ <= 2550)) |
            ((occ >= 2600) & (occ <= 2960)))
    result[mask] = 5

    # Category 6: SKILLED BLUE-COLLAR
    # Protective Service (3700-3950) - OCC00 max 3950 vs 3960
    # Construction/Extraction (6200-6940)
    # Installation/Maintenance/Repair (7000-7620) - OCC00 max 7620 vs 7630
    mask = (((occ >= 3700) & (occ <= 3950)) |
            ((occ >= 6200) & (occ <= 6940)) |
            ((occ >= 7000) & (occ <= 7620)))
    result[mask] = 6

    # Category 7: OFFICE/CLERICAL
    # Office/Administrative Support (5000-5930) - OCC00 max 5930 vs 5940
    # Stock Clerks (5620) is in this range
    # Plus misc sales (note: OCC00 uses 4960 instead of 4965 for "Sales, All Other")
    misc_sales_occ00 = {4750, 4830, 4900, 4960}  # OCC00 versions of MISC_SALES
    mask = (((occ >= 5000) & (occ <= 5930)) |
            np.isin(occ, list(misc_sales_occ00)))
    result[mask] = 7

    # Category 8: PRODUCTION/TRANSPORT
    # Production (7700-8960) - OCC00 max 8960 vs 8965
    # Transportation/Material Moving (9000-9750)
    mask = (((occ >= 7700) & (occ <= 8960)) |
            ((occ >= 9000) & (occ <= 9750)))
    result[mask] = 8

    # Category 9: SERVICE WORKERS
    # Healthcare Support (3600-3650) - OCC00 max 3650 vs 3655
    # Food Preparation/Serving (4000-4160)
    # Building/Grounds Cleaning (4200-4250)
    # Personal Care/Service (4300-4650)
    # Plus low-skill sales
    mask = (((occ >= 3600) & (occ <= 3650)) |
            ((occ >= 4000) & (occ <= 4160)) |
            ((occ >= 4200) & (occ <= 4250)) |
            ((occ >= 4300) & (occ <= 4650)) |
            np.isin(occ, list(LOW_SKILL_SALES)))
    result[mask] = 9

    # Category 10: AGRICULTURE
    # Farming/Fishing/Forestry (6000-6130) - OCC00 starts at 6000 vs 6005
    mask = (occ >= 6000) & (occ <= 6130)
    result[mask] = 10

    # Convert to categorical
    return pd.Categorical(result, categories=list(range(1, 11)), ordered=True)


def assign_occgrp_from_occ90(occ90_series):
    """
    Assign OCCGRP category based on OCC90 (1990 Census occupation codes).

    OCC90 codes (1992-1999) have a different structure from OCC00+.
    Key mappings:
    - 3-22: Executive/Managerial → Managers
    - 23-37: Management-related (accountants, etc.) → Business/Legal
    - 43-68, 69-83, 166-173: Engineers, scientists → STEM
    - 84-106, 143-154: Health professionals → Health
    - 113-159 (excl therapists), 164-165, 183-199: Education/Arts → Education/Social/Arts
    - 174-177: Social workers → Education/Social/Arts
    - 178-179: Lawyers → Business/Legal
    - 203-208: Health technicians → Health
    - 213-235: Engineering/science technicians → STEM
    - 243: Sales supervisors → Managers
    - 253-269: Business/wholesale sales → Business/Legal
    - 274-285: Retail sales, cashiers → Service Workers
    - 303-389: Admin support → Office/Clerical
    - 403-472: Service occupations (split between Service Workers and Skilled Blue-Collar)
    - 473-499: Agriculture
    - 503-617: Production/craft → split between Skilled Blue-Collar and Production
    - 628-889: Operators, transport → Production/Transport

    Parameters
    ----------
    occ90_series : pd.Series
        OCC90 occupation codes

    Returns
    -------
    pd.Series
        OCCGRP category (1-10) as categorical
    """
    # Convert to numeric
    if hasattr(occ90_series, 'cat'):
        occ = pd.to_numeric(occ90_series, errors='coerce').values
    else:
        occ = occ90_series.values
    result = np.full(len(occ), np.nan, dtype='float32')

    # Category 1: MANAGERS
    # Executive/administrative/managerial (3-22)
    # Sales supervisors/proprietors (243)
    mask = ((occ >= 3) & (occ <= 22)) | (occ == 243)
    result[mask] = 1

    # Category 2: STEM PROFESSIONALS
    # Engineers (43-59)
    # Computer programmers (63)
    # Math/computer scientists (64-68)
    # Natural scientists (69-83)
    # Social scientists (166-173)
    # Engineering/science technicians (213-235)
    mask = (((occ >= 43) & (occ <= 59)) |
            (occ == 63) |
            ((occ >= 64) & (occ <= 68)) |
            ((occ >= 69) & (occ <= 83)) |
            ((occ >= 166) & (occ <= 173)) |
            ((occ >= 213) & (occ <= 235)))
    result[mask] = 2

    # Category 3: HEALTH PROFESSIONALS
    # Health diagnosing (84-89)
    # Health assessment/treating (95-106)
    # Therapists (143-154)
    # Health technicians (203-208)
    mask = (((occ >= 84) & (occ <= 89)) |
            ((occ >= 95) & (occ <= 106)) |
            ((occ >= 143) & (occ <= 154)) |
            ((occ >= 203) & (occ <= 208)))
    result[mask] = 3

    # Category 4: BUSINESS/LEGAL/PROFESSIONAL SALES
    # Management-related occupations (23-37): accountants, HR, etc.
    # Lawyers/judges (178-179)
    # Sales reps, finance/business (253-259)
    # Sales reps, commodities/wholesale (263-269)
    mask = (((occ >= 23) & (occ <= 37)) |
            ((occ >= 178) & (occ <= 179)) |
            ((occ >= 253) & (occ <= 259)) |
            ((occ >= 263) & (occ <= 269)))
    result[mask] = 4

    # Category 5: EDUCATION/SOCIAL/ARTS
    # Teachers, except postsecondary (113-142)
    # Counselors (155-163) - vocational and educational counselors
    # Librarians/archivists (164-165)
    # Social/recreation workers (174-177)
    # Writers/artists/entertainers (183-199)
    mask = (((occ >= 113) & (occ <= 142)) |
            ((occ >= 155) & (occ <= 165)) |
            ((occ >= 174) & (occ <= 177)) |
            ((occ >= 183) & (occ <= 199)))
    result[mask] = 5

    # Category 6: SKILLED BLUE-COLLAR
    # Protective service (413-427)
    # Mechanics and repairers (503-549)
    # Construction trades (553-599) - includes supervisors (553-557) and trades (558-599)
    # Extractive occupations (613-617)
    mask = (((occ >= 413) & (occ <= 427)) |
            ((occ >= 503) & (occ <= 549)) |
            ((occ >= 553) & (occ <= 599)) |
            ((occ >= 613) & (occ <= 617)))
    result[mask] = 6

    # Category 7: OFFICE/CLERICAL
    # Administrative support (303-389)
    # Sales counter clerks (275) - moved from retail
    mask = ((occ >= 303) & (occ <= 389)) | (occ == 275)
    result[mask] = 7

    # Category 8: PRODUCTION/TRANSPORT
    # Precision production (628-699)
    # Machine operators (703-799)
    # Transportation (803-889)
    mask = (((occ >= 628) & (occ <= 699)) |
            ((occ >= 703) & (occ <= 799)) |
            ((occ >= 803) & (occ <= 889)))
    result[mask] = 8

    # Category 9: SERVICE WORKERS
    # Private household (403-407)
    # Food preparation (433-444)
    # Health aides (445-447)
    # Cleaning/building services (448-455)
    # Personal services (456-472, excluding 413-427 protective)
    # Retail sales (274, 276-278) - cashiers, retail salespersons
    # Other sales (283-285)
    mask = (((occ >= 403) & (occ <= 412)) |  # Private household, cleaning
            ((occ >= 433) & (occ <= 444)) |  # Food prep
            ((occ >= 445) & (occ <= 447)) |  # Health aides
            ((occ >= 448) & (occ <= 455)) |  # Cleaning/building
            ((occ >= 456) & (occ <= 472)) |  # Personal services
            (occ == 274) |                    # Sales supervisors retail (low-skill part)
            ((occ >= 276) & (occ <= 278)) |  # Cashiers, retail
            ((occ >= 283) & (occ <= 285)))   # Other sales
    result[mask] = 9

    # Category 10: AGRICULTURE
    # Farm operators/managers (473-485) - NOTE: 486 moved to Service Workers
    # Other agricultural (487-499)
    mask = (((occ >= 473) & (occ <= 485)) |
            ((occ >= 487) & (occ <= 499)))
    result[mask] = 10

    # =========================================================================
    # SPECIFIC CODE OVERRIDES (based on dual-coded 2000-2002 analysis)
    # These codes are reassigned to match their OCC00 classifications
    # =========================================================================

    # NOTE: OCC90=473 (Farmers) intentionally KEPT in Agriculture
    # Although 91% map to OCC00=210 (Farm managers), moving them to Managers
    # inflates the 1990s Manager share and worsens the transition break.
    # Better to have a documented break in Agriculture than artificial inflation.

    # OCC90=486 (Groundskeepers and gardeners) → Service Workers
    # 87% map to OCC00=4250 (Grounds maintenance workers)
    result[occ == 486] = 9

    # OCC90=877 (Stock handlers and baggers) → Office/Clerical
    # 61% map to OCC00=5620 (Stock clerks) - matches our 2020 fix
    result[occ == 877] = 7

    # OCC90=387 (Teacher aides) → Education/Social/Arts
    # 85% map to OCC00=2540 (Teacher assistants)
    result[occ == 387] = 5

    # OCC90=154 (Miscellaneous therapists) → Education/Social/Arts
    # 78% map to OCC00=2200 (Postsecondary teachers) - psychologists, etc.
    result[occ == 154] = 5

    # OCC90=37 (Management-related occupations, n.e.c.) → Office/Clerical
    # 74% map to OCC00=5700 (Secretaries and administrative assistants)
    result[occ == 37] = 7

    # OCC90=234 (Legal assistants) → Business/Legal (BUG FIX)
    # Was incorrectly in 213-235 range assigned to STEM
    # 88% map to OCC00=2140/2150 (Paralegals/Legal support)
    result[occ == 234] = 4

    # OCC90=263 (Sales reps, except scientific) → Service Workers
    # 88% map to OCC00=4760 (Retail salespersons)
    result[occ == 263] = 9

    # OCC90=264 (Sales workers, other commodities) → Service Workers
    # 87% map to OCC00=4760 (Retail salespersons)
    result[occ == 264] = 9

    # OCC90=268 (Sales reps, n.e.c.) → Service Workers
    # 80% map to OCC00=4760 (Retail salespersons)
    result[occ == 268] = 9

    # OCC90=869 (Construction laborers) → Skilled Blue-Collar
    # 87% map to Skilled Blue-Collar categories in OCC00
    result[occ == 869] = 6

    # OCC90=844 (Operating engineers) → Skilled Blue-Collar
    # 90% map to Skilled Blue-Collar categories in OCC00
    result[occ == 844] = 6

    # Convert to categorical
    return pd.Categorical(result, categories=list(range(1, 11)), ordered=True)


def assign_occgrp_from_occ80(occ80_series):
    """
    Assign OCCGRP category based on OCC80 (1980 Census occupation codes).

    OCC80 codes (1989-1991) have a similar structure to OCC90 but with some
    classification differences. This mapping uses direct code ranges with
    specific overrides based on how codes map forward to OCC90.

    Parameters
    ----------
    occ80_series : pd.Series
        OCC80 occupation codes

    Returns
    -------
    pd.Series
        OCCGRP category (1-10) as categorical
    """
    # Convert to numeric
    if hasattr(occ80_series, 'cat'):
        occ = pd.to_numeric(occ80_series, errors='coerce').values
    else:
        occ = occ80_series.values
    result = np.full(len(occ), np.nan, dtype='float32')

    # Category 1: MANAGERS
    # Executive/administrative/managerial (3-22)
    # Sales supervisors/proprietors (243)
    mask = ((occ >= 3) & (occ <= 22)) | (occ == 243)
    result[mask] = 1

    # Category 2: STEM PROFESSIONALS
    # Engineers (43-59)
    # Computer programmers (63)
    # Math/computer scientists (64-68)
    # Natural scientists (69-83)
    # Social scientists (166-173)
    # Engineering/science technicians (213-235)
    mask = (((occ >= 43) & (occ <= 59)) |
            (occ == 63) |
            ((occ >= 64) & (occ <= 68)) |
            ((occ >= 69) & (occ <= 83)) |
            ((occ >= 166) & (occ <= 173)) |
            ((occ >= 213) & (occ <= 235)))
    result[mask] = 2

    # Category 3: HEALTH PROFESSIONALS
    # Health diagnosing (84-89)
    # Health assessment/treating (95-106)
    # Therapists (143-154)
    # Health technicians (203-208)
    mask = (((occ >= 84) & (occ <= 89)) |
            ((occ >= 95) & (occ <= 106)) |
            ((occ >= 143) & (occ <= 154)) |
            ((occ >= 203) & (occ <= 208)))
    result[mask] = 3

    # Category 4: BUSINESS/LEGAL/PROFESSIONAL SALES
    # Management-related occupations (23-37): accountants, HR, etc.
    # Lawyers/judges (178-179)
    # Sales reps, finance/business (253-259)
    mask = (((occ >= 23) & (occ <= 37)) |
            ((occ >= 178) & (occ <= 179)) |
            ((occ >= 253) & (occ <= 259)))
    result[mask] = 4

    # Category 5: EDUCATION/SOCIAL/ARTS
    # Teachers (113-142)
    # Counselors (155-163)
    # Librarians/archivists (164-165)
    # Social/recreation workers (174-177)
    # Writers/artists/entertainers (183-199)
    mask = (((occ >= 113) & (occ <= 142)) |
            ((occ >= 155) & (occ <= 165)) |
            ((occ >= 174) & (occ <= 177)) |
            ((occ >= 183) & (occ <= 199)))
    result[mask] = 5

    # Category 6: SKILLED BLUE-COLLAR
    # Protective service (413-427)
    # Mechanics and repairers (503-549)
    # Construction trades (553-599)
    # Extractive occupations (613-617)
    mask = (((occ >= 413) & (occ <= 427)) |
            ((occ >= 503) & (occ <= 549)) |
            ((occ >= 553) & (occ <= 599)) |
            ((occ >= 613) & (occ <= 617)))
    result[mask] = 6

    # Category 7: OFFICE/CLERICAL
    # Administrative support (303-389)
    mask = (occ >= 303) & (occ <= 389)
    result[mask] = 7

    # Category 8: PRODUCTION/TRANSPORT
    # Precision production (628-699)
    # Machine operators (703-799)
    # Transportation (803-889)
    mask = (((occ >= 628) & (occ <= 699)) |
            ((occ >= 703) & (occ <= 799)) |
            ((occ >= 803) & (occ <= 889)))
    result[mask] = 8

    # Category 9: SERVICE WORKERS
    # Private household (403-412)
    # Food preparation (433-444)
    # Health aides (445-447)
    # Cleaning/building services (448-472)
    # Retail sales, cashiers (263-285)
    mask = (((occ >= 403) & (occ <= 412)) |
            ((occ >= 433) & (occ <= 444)) |
            ((occ >= 445) & (occ <= 447)) |
            ((occ >= 448) & (occ <= 472)) |
            ((occ >= 263) & (occ <= 285)))
    result[mask] = 9

    # Category 10: AGRICULTURE
    # Farm operators/managers (473-489)
    # Other agricultural (494-499)
    # NOTE: Unlike OCC90, we do NOT remap 486 (groundskeepers) to Service Workers
    # for OCC80, as this causes worse transition breaks at Jan 1992.
    mask = ((occ >= 473) & (occ <= 489)) | ((occ >= 494) & (occ <= 499))
    result[mask] = 10

    # =========================================================================
    # SPECIFIC CODE OVERRIDES (based on OCC90 dual-coded analysis)
    # Apply same remappings as OCC90 where the codes are equivalent
    # =========================================================================

    # OCC80=37 (Management-related occupations, n.e.c.) → Office/Clerical
    # Same logic as OCC90=37: many map to secretaries/admin assistants
    result[occ == 37] = 7

    # OCC80=234 (Legal assistants) → Business/Legal
    # Same as OCC90=234: paralegals belong in Business/Legal, not STEM
    result[occ == 234] = 4

    # OCC80=387 (Teacher aides) → Education/Social/Arts
    # Same as OCC90=387: teacher assistants belong in Education
    result[occ == 387] = 5

    # OCC80=844 (Operating engineers) → Skilled Blue-Collar
    # Same as OCC90=844: construction equipment operators
    result[occ == 844] = 6

    # OCC80=869 (Construction laborers) → Skilled Blue-Collar
    # Same as OCC90=869: construction workers
    result[occ == 869] = 6

    # OCC80=877 (Stock handlers and baggers) → Office/Clerical
    # Same as OCC90=877: stock clerks (matches our 2020 fix)
    result[occ == 877] = 7

    # NOTE: OCC80=486 (Groundskeepers) intentionally KEPT in Agriculture
    # Unlike OCC90, remapping 486 to Service Workers for OCC80 causes
    # larger transition breaks at Jan 1992. Better to document the
    # Agriculture break (-0.50pp) than create a larger Service break.

    # Convert to categorical
    return pd.Categorical(result, categories=list(range(1, 11)), ordered=True)


def add_occgrp(df, year=None):
    """
    Add OCCGRP variable to a CPS dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        CPS data with occupation codes
    year : int, optional
        Year of the data (determines which OCC variable to use)
        If not provided, infers from YEAR column or available OCC variables

    Returns
    -------
    pd.DataFrame
        DataFrame with OCCGRP column added
    """
    # Determine which occupation variable to use
    if year is None:
        if 'YEAR' in df.columns:
            year = df['YEAR'].mode().iloc[0] if len(df['YEAR'].mode()) > 0 else None

    # Phase 1: OCC18 (2020+)
    if 'OCC18' in df.columns and (year is None or year >= 2020):
        df = df.copy()
        df['OCCGRP'] = assign_occgrp_from_occ18(df['OCC18'])
        return df

    # Phase 2: OCC10 (2011-2019)
    if 'OCC10' in df.columns and (year is None or (2011 <= year <= 2019)):
        df = df.copy()
        df['OCCGRP'] = assign_occgrp_from_occ10(df['OCC10'])
        return df

    # Phase 3: OCC00 (2000-2010) - includes dual-coding period 2000-2002
    if 'OCC00' in df.columns and (year is None or (2000 <= year <= 2010)):
        df = df.copy()
        df['OCCGRP'] = assign_occgrp_from_occ00(df['OCC00'])
        return df

    # Phase 4: OCC90 (1992-1999)
    if 'OCC90' in df.columns and (year is None or (1992 <= year <= 1999)):
        df = df.copy()
        df['OCCGRP'] = assign_occgrp_from_occ90(df['OCC90'])
        return df

    # Phase 5: OCC80 (1989-1991)
    if 'OCC80' in df.columns and (year is None or (1989 <= year <= 1991)):
        df = df.copy()
        df['OCCGRP'] = assign_occgrp_from_occ80(df['OCC80'])
        return df

    raise ValueError("Could not determine appropriate occupation variable. "
                    "Ensure OCC18 (2020+), OCC10 (2011-2019), OCC00 (2000-2010), "
                    "OCC90 (1992-1999), or OCC80 (1989-1991) is present.")


def get_occgrp_label(code):
    """Get label for an OCCGRP code."""
    return OCCGRP_LABELS.get(code, 'Unknown')


def validate_occgrp(df, verbose=True):
    """
    Validate OCCGRP assignment by checking coverage and distribution.

    Parameters
    ----------
    df : pd.DataFrame
        CPS data with OCCGRP column
    verbose : bool
        If True, print validation results

    Returns
    -------
    dict
        Validation statistics
    """
    if 'OCCGRP' not in df.columns:
        raise ValueError("OCCGRP column not found")

    # Filter to employed with valid occupation
    if 'LFS' in df.columns:
        employed = df[df['LFS'] == 'Employed']
    else:
        employed = df

    total = len(employed)
    missing = employed['OCCGRP'].isna().sum()
    coverage = 1 - (missing / total) if total > 0 else 0

    # Distribution
    dist = employed['OCCGRP'].value_counts(normalize=True).sort_index()

    if verbose:
        print(f"OCCGRP Validation")
        print(f"=" * 50)
        print(f"Total employed: {total:,}")
        print(f"Missing OCCGRP: {missing:,} ({100*missing/total:.2f}%)")
        print(f"Coverage: {100*coverage:.2f}%")
        print()
        print("Distribution:")
        for code, pct in dist.items():
            label = OCCGRP_LABELS.get(int(code), 'Unknown')
            print(f"  {int(code):2d}. {label:25s} {100*pct:5.1f}%")

    return {
        'total': total,
        'missing': missing,
        'coverage': coverage,
        'distribution': dist.to_dict()
    }


if __name__ == '__main__':
    # Test with 2024 CPS data
    import sys

    print("Testing OCCGRP assignment...")

    # Load 2024 CPS data
    df = pd.read_feather('/home/brian/Documents/CPS/data/clean/cps2024.ft')
    print(f"Loaded {len(df):,} records from CPS 2024")

    # Add OCCGRP
    df = add_occgrp(df, year=2024)

    # Validate
    stats = validate_occgrp(df, verbose=True)

    # Check specific codes
    print("\nSpot checks:")

    # Stock clerks (9645) should be in Office/Clerical (7)
    stock_clerks = df[df['OCC18'] == 9645]
    if len(stock_clerks) > 0:
        sc_grp = stock_clerks['OCCGRP'].mode().iloc[0]
        print(f"  Stock clerks (9645): OCCGRP={int(sc_grp)} (expected 7)")

    # Retail supervisors (4700) should be in Managers (1)
    retail_sup = df[df['OCC18'] == 4700]
    if len(retail_sup) > 0:
        rs_grp = retail_sup['OCCGRP'].mode().iloc[0]
        print(f"  Retail supervisors (4700): OCCGRP={int(rs_grp)} (expected 1)")

    # Cashiers (4720) should be in Service Workers (9)
    cashiers = df[df['OCC18'] == 4720]
    if len(cashiers) > 0:
        c_grp = cashiers['OCCGRP'].mode().iloc[0]
        print(f"  Cashiers (4720): OCCGRP={int(c_grp)} (expected 9)")

    # Insurance agents (4810) should be in Business/Legal (4)
    ins_agents = df[df['OCC18'] == 4810]
    if len(ins_agents) > 0:
        ia_grp = ins_agents['OCCGRP'].mode().iloc[0]
        print(f"  Insurance agents (4810): OCCGRP={int(ia_grp)} (expected 4)")

    print("\nDone.")
