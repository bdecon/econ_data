# Plan: PRICEADJ Refactoring for Efficient Monthly Updates

## Current Problem

The `PRICEADJ` variable stores a price deflator relative to the **latest CPS month**. When new CPI data arrives, the base changes, requiring recalculation of PRICEADJ for **all historical observations** (1989-present). This forces a full regeneration of all feather files (~23 years × 5-10 minutes = hours of processing) just to update one column.

### Current Flow
```
bd_CPS_cpi.ipynb          bd_CPS_reader.ipynb
       │                         │
       ▼                         │
  cpi.csv (rebased to latest)    │
       │                         │
       └──────────────────►──────┘
                                 │
                                 ▼
                    For each year 1989-2025:
                      - Read raw .dat files
                      - Parse all columns
                      - Compute PRICEADJ = CPI[latest] / CPI[obs_month]
                      - Write cps{year}.ft
```

**Pain point**: Every month requires ~2+ hours to regenerate all feather files.

---

## Proposed Solutions

### Option A: Store Raw CPI, Compute PRICEADJ at Analysis Time

**Concept**: Don't store PRICEADJ in feather files. Store raw regional CPI levels instead, and provide a utility function to compute real values when needed.

**Changes Required**:
1. Add `CPI_REGIONAL` column to feather files (raw CPI level, e.g., 315.2)
2. Remove `PRICEADJ` column from feather files
3. Create utility function: `add_priceadj(df, target_date=None)` that computes deflators
4. Update `bd_CPS_cpi.ipynb` to maintain a CPI lookup file

**Usage**:
```python
cps = pd.read_feather('cps2020.ft')
cps = add_priceadj(cps)  # Deflates to latest CPI month
# OR
cps = add_priceadj(cps, target_date='2020-01-01')  # Deflates to specific base
```

**Pros**:
- **Zero regeneration needed** when new CPI data arrives
- Flexible base period (can deflate to any month)
- Smaller monthly maintenance overhead

**Cons**:
- Changes existing data schema (breaking change)
- Requires extra function call at analysis time
- Need one-time full regeneration to add CPI_REGIONAL column

**Monthly Update Workflow**: Update CPI lookup file only (~1 second)

---

### Option B: Post-Processing PRICEADJ Update Script (Recommended)

**Concept**: Keep current approach but create a fast script that updates ONLY the PRICEADJ column in existing feather files without regenerating everything else.

**Changes Required**:
1. Create `update_priceadj.py` script/function
2. Create `PRICEADJ/` subfolder with:
   - CPI retrieval logic (refactored from notebook)
   - PRICEADJ update logic

**Implementation**:
```python
# update_priceadj.py
def update_priceadj_all(start_year=1989, end_year=2025):
    """Update PRICEADJ in all feather files to latest CPI base."""
    cpi = get_latest_cpi()  # Fetch from FRED

    for year in range(start_year, end_year + 1):
        path = f'/home/brian/Documents/CPS/data/clean/cps{year}.ft'
        df = pd.read_feather(path)

        # Recalculate PRICEADJ
        latest_cpi = cpi.iloc[-1]
        df['PRICEADJ'] = df['MONTH'].map(
            lambda m: latest_cpi[df.loc[m, 'REGION']] / cpi.loc[m, df.loc[m, 'REGION']]
        )
        # Actually: PRICEADJ = latest_cpi[region] / cpi_at_obs_date[region]
        # This requires YEAR/MONTH/REGION columns which are already present

        df.to_feather(path)
    print(f'Updated PRICEADJ for {start_year}-{end_year}')
```

**Pros**:
- No schema change (backward compatible)
- Much faster than full regeneration (~2-3 minutes vs 2+ hours)
- Simple to implement
- Works with existing feather files immediately

**Cons**:
- Still modifies files in place each month
- Requires keeping YEAR/MONTH/REGION columns in feather files (already present)

**Monthly Update Workflow**:
```bash
python update_priceadj.py  # ~2-3 minutes
```

---

### Option C: Separate CPI Lookup File + Merge at Analysis Time

**Concept**: Remove PRICEADJ from feather files entirely. Maintain a separate CPI file that users merge at load time.

**Changes Required**:
1. Create `cpi_regional.parquet` with columns: DATE, ALL, Northeast, Midwest, South, West
2. Remove PRICEADJ from feather files
3. Provide utility function for merging

**Usage**:
```python
cps = pd.read_feather('cps2020.ft')
cpi = pd.read_parquet('cpi_regional.parquet')
cps = add_priceadj(cps, cpi)  # Merges and computes deflator
```

**Pros**:
- Complete decoupling of CPS data and CPI data
- CPI file can be updated independently
- Most flexible (any base period, easy to use alternative price indices)

**Cons**:
- Breaking schema change
- Extra step for users
- Need to regenerate all files once to remove PRICEADJ

**Monthly Update Workflow**: Update CPI file only (~1 second)

---

### Option D: Store Both Raw CPI and PRICEADJ

**Concept**: Store both CPI_REGIONAL (raw) and PRICEADJ. Monthly updates only touch PRICEADJ.

**Pros**:
- Backward compatible
- Fast monthly updates
- Users can recompute to any base if needed

**Cons**:
- Slightly larger files (~1-2 bytes per observation)
- Redundant data

---

## Recommendation

**Option B (Post-Processing Update Script)** is the best balance of:
- Minimal disruption (no schema change)
- Significant time savings (2 min vs 2+ hours)
- Simple implementation

### Recommended File Structure

```
bd_CPS/
├── PRICEADJ/
│   ├── __init__.py
│   ├── cpi_retrieval.py     # Refactored from bd_CPS_cpi.ipynb
│   ├── update_priceadj.py   # Update script
│   └── cpi_regional.csv     # CPI levels (not rebased) - optional backup
```

### Implementation Steps

1. **Create `PRICEADJ/cpi_retrieval.py`**:
   - Extract FRED download logic from `bd_CPS_cpi.ipynb`
   - Add Cleveland Fed nowcast fallback
   - Return DataFrame with regional CPI levels

2. **Create `PRICEADJ/update_priceadj.py`**:
   - Load latest CPI data
   - Loop through feather files
   - Update PRICEADJ column only
   - Save feather files

3. **Simplify `bd_CPS_cpi.ipynb`**:
   - Convert to thin wrapper that calls the module
   - Or deprecate entirely in favor of the script

4. **Update `bd_CPS_reader.ipynb`**:
   - No changes needed (still produces PRICEADJ during initial generation)
   - PRICEADJ will be updated by the script after initial generation

### Estimated Implementation Time

- `cpi_retrieval.py`: 30 minutes (mostly refactoring existing code)
- `update_priceadj.py`: 1 hour (new implementation)
- Testing: 30 minutes
- **Total: ~2 hours**

### Monthly Maintenance After Implementation

1. Run `update_priceadj.py` (~2 minutes)
2. Done

---

## Alternative: Hybrid Approach (Option A + B)

If you want maximum flexibility for the future:

1. Add `CPI_REGIONAL` column during next full regeneration
2. Keep PRICEADJ as well
3. Use update script for monthly updates
4. Users can recompute PRICEADJ to any base using CPI_REGIONAL

This is slightly more work upfront but provides the most options going forward.

---

## Questions for Decision

1. **Breaking changes acceptable?** If yes, Option A or C provides cleaner architecture.
2. **Want ability to use different base periods?** If yes, need to store raw CPI.
3. **Priority: speed vs simplicity?** Option B is fastest to implement, Option A is cleanest long-term.

---

## Notes

- PRICEADJ is only used for wage/earnings analysis (multiplying nominal values)
- Current feather files already have YEAR, MONTH, REGION columns needed for recalculation
- CPI nowcast fallback is important for months where BLS data isn't yet available
