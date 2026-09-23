# ONET: O*NET Occupation Characteristics for CPS

This module adds O*NET-derived occupation characteristics to CPS data:

| Variable | Description | Range | Methodology |
|----------|-------------|-------|-------------|
| `OCCPD` | Any physical demands | 0-1 | Johnson et al. (2007), Rho (2010) |
| `OCCHPD` | High physical demands | 0-1 | Johnson et al. (2007), Rho (2010) |
| `OCCDWC` | Difficult working conditions | 0-1 | Johnson et al. (2007), Rho (2010) |
| `OCCTLWK` | Telework feasibility | 0-1 | DFLP (Dey et al. 2021) |
| `OCCAI` | AI exposure | 0.30-0.40 | Pew Research (2023) |
| `OCCJZ` | Job Zone (education/preparation level) | 1-5 | O*NET / NY Fed |

All variables use `float16` for space efficiency.

**Coverage**: 2003+ (requires Census 2002+ occupation codes)

## Quick Start

Variables are automatically included in bd CPS annual feather files for 2003+. For standalone use:

```python
from bd_CPS_ONET.cps_onet import add_all_occ_vars
import pandas as pd

cps = pd.read_feather('/path/to/cps2020.ft')
cps = add_all_occ_vars(cps, year=2020)

# Create binary variables:
cps['PD'] = (cps['OCCPD'] > 0.5).astype(int)
cps['TELEWORK'] = (cps['OCCTLWK'] > 0.5).astype(int)
cps['BA_REQUIRED'] = (cps['OCCJZ'] >= 4).astype(int)  # NY Fed method

# For AI exposure, use percentile cutoffs:
threshold = cps['OCCAI'].quantile(0.75)
cps['HIGH_AI'] = (cps['OCCAI'] > threshold).astype(int)

# Education mismatch analysis:
edu_to_jz = {'LTHS': 1, 'HS': 2, 'SC': 3, 'COLL': 4, 'ADV': 5}
cps['WORKER_JZ'] = cps['EDUC'].astype(str).map(edu_to_jz)
cps['EDUMISMATCH'] = cps['WORKER_JZ'] - cps['OCCJZ']
# Positive = overqualified, Negative = underqualified
```

## Files

| File | Purpose |
|------|---------|
| `cps_onet.py` | Integration API for adding variables to CPS data |
| `output/*.csv` | Pre-generated annual lookup tables (2003-2025) |
| `pd_dwc_classifier.py` | Generates PD/DWC lookup tables |
| `telework_classifier.py` | Generates telework lookup tables |
| `ai_classifier.py` | Generates AI exposure lookup tables |
| `jz_classifier.py` | Generates Job Zone lookup tables |
| `crosswalks/` | Census-to-SOC occupation code mappings |

## Occupation Code Periods

| Years | CPS Variable | Census System | O*NET Version |
|-------|--------------|---------------|---------------|
| 2003-2010 | OCC00 | Census 2002 | 14.0 |
| 2011-2019 | OCC10 | Census 2010 | 20.1 |
| 2020+ | OCC18 | Census 2018 | 25.1 |

---

## Regenerating Lookup Tables

The lookup tables can be regenerated from primary sources. This requires downloading O*NET and OEWS data.

### Step 1: Download O*NET Data

Download from the O*NET Resource Center: https://www.onetcenter.org/database.html

You need three versions to cover all CPS years:

| O*NET Version | For CPS Years | Download |
|---------------|---------------|----------|
| 14.0 | 2003-2010 | [Archive](https://www.onetcenter.org/dictionary/14.0/excel/) |
| 20.1 | 2011-2019 | [Archive](https://www.onetcenter.org/dictionary/20.1/excel/) |
| 25.1+ | 2020+ | [Current](https://www.onetcenter.org/database.html#individual-files) |

From each version, you need these files:
- `Abilities.txt`
- `Work Activities.txt`
- `Work Context.txt`
- `Job Zones.txt` (for OCCJZ)

Organize as:
```
/path/to/onet/
├── db_14_0/
│   ├── Abilities.txt
│   ├── Work Activities.txt
│   ├── Work Context.txt
│   └── Job Zones.txt
├── db_20_1_text/
│   └── ...
└── db_25_1_text/
    └── ...
```

### Step 2: Download OEWS Employment Data

Download from BLS: https://www.bls.gov/oes/tables.htm

Under "National," download the Excel file for each year (2003-2024). The classifiers use employment counts to weight SOC codes when aggregating to Census occupation codes.

Organize as:
```
/path/to/oews/
├── oesm03nat/
│   └── national_M2003_dl.xls
├── oesm04nat/
│   └── ...
└── oesm24nat/
    └── ...
```

### Step 3: Update Paths and Run

Edit the paths in each classifier script's `__main__` section:

```python
# In pd_dwc_classifier.py, telework_classifier.py, ai_classifier.py, jz_classifier.py
ONET_BASE = '/path/to/onet/'
OEWS_BASE = '/path/to/oews/'
```

Then run:
```bash
cd bd_CPS_ONET
python pd_dwc_classifier.py      # Generates pd_dwc_*.csv
python telework_classifier.py    # Generates telework_*.csv
python ai_classifier.py          # Generates ai_*.csv
python jz_classifier.py          # Generates jz_*.csv
```

---

## Methodology

### PD/DWC Classification

Based on O*NET importance ratings (1-5 scale). A characteristic is significant when rating >= 4.0.

**High PD** (strenuous physical exertion):
- Abilities: Dynamic/explosive/static/trunk strength, stamina, reaction time, gross body equilibrium
- Work Context: Bending/twisting, kneeling/crouching/stooping/crawling

**Any PD** (general physical requirements):
- Includes High PD elements, plus:
- Work Activities: Performing general physical activities, handling/moving objects
- Work Context: Standing, walking/running, repetitive motions

Note: Repetitive motions (e.g., typing) triggers Any PD, so many office jobs qualify. Use High PD for physically strenuous jobs only.

**DWC** (difficult working conditions):
- Cramped workspace, outdoor labor, non-controlled indoor, extreme temperatures, contaminants, hazardous conditions/equipment, vibration, distracting noise

### Telework (DFLP Methodology)

From Dey, Frazis, Loewenstein, Piccone (2021), BLS Monthly Labor Review.

An occupation is suitable for telework if:
- NO disqualifying conditions (27 physical/environmental factors >= 4.0, conflict factors >= 3.75)
- ALL positive requirements met (computer use >= 3.0, indoor controlled >= 3.0, sitting >= 3.0)

### AI Exposure (Pew Methodology)

From Pew Research Center (July 2023).

All 41 O*NET work activities classified as high/medium/low AI exposure. Score = high_avg / (high + medium + low). Range: 0.30-0.40. Higher = more exposed to AI.

**Interpreting the narrow range**: The 0.30-0.40 range reflects that all occupations have some mix of high/medium/low exposure activities. Use percentile rankings (top 25% = most exposed) rather than raw scores for classification.

**Limitation for longitudinal analysis**: OCCAI is best suited for **cross-sectional analysis**. The classification of work activities into high/medium/low AI exposure was a one-time judgment by Pew analysts in mid-2023, reflecting AI capabilities at that time. This classification does not update as AI capabilities evolve. Consequently:
- OCCAI cannot capture how expanding AI capabilities affect occupations that were not previously exposed
- Longitudinal changes primarily reflect **compositional shifts** (employment moving between occupations) rather than changes in AI's ability to perform job tasks
- For time-series analysis, interpret trends as "share of employment in occupations that were AI-exposed as of 2023"

### Job Zone (O*NET / NY Fed Methodology)

O*NET Job Zones classify occupations by preparation level (education, experience, training):

| Zone | Typical Education | Examples |
|------|-------------------|----------|
| 1 | Little or no preparation | Dishwashers, food prep |
| 2 | HS diploma | Tellers, security guards |
| 3 | Vocational/associate's | Electricians, medical assistants |
| 4 | Bachelor's degree | Accountants, software developers |
| 5 | Graduate degree | Lawyers, physicians |

**Education Mismatch**: Compare worker's education to job's Job Zone to identify overqualification/underqualification.

**Underemployment** (NY Fed method): College graduates in jobs with OCCJZ < 4 are considered underemployed.

---

## References

- Johnson, Mermin, Resseger (2007). "Employment at Older Ages and the Changing Nature of Work"
- Rho (2010). "Hard Work? Patterns in Physically Demanding Labor Among Older Workers"
- Bucknor & Baker (2016). "Still Working Hard"
- Dey et al. (2021). "Teleworking and lost work during the pandemic" BLS Monthly Labor Review
- Pew Research (2023). "Which U.S. Workers Are More Exposed to AI on Their Jobs?"
- Federal Reserve Bank of New York. "The Labor Market for Recent College Graduates"
