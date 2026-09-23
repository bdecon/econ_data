#!/usr/bin/env python3
"""
HHID Collision Fix Runner Script

Regenerates 1994-1995 CPS data files after the QSTNUM fix in bd_CPS_reader.ipynb.

Steps:
  2. Regenerate feather files with fixed QSTNUM (first pass, without correct CPSID)
  3. Rebuild CPSID pickle files (qstnum_map.pkl, CPSID_89-93.pkl, CPS_unique_ids.pkl)
  4. Regenerate feather files with corrected CPSIDs (second pass)
  5. Verify results

Usage: python3 run_hhid_fix.py
"""

import sys
import os
import pickle
import warnings
import time

warnings.filterwarnings('ignore')

# Add notebook directory to sys.path for module imports (bd_CPS_details, etc.)
notebook_dir = '/home/brian/Documents/econ_data/bd_CPS'
sys.path.insert(0, notebook_dir)

import nbformat

data_dir = '/home/brian/Documents/CPS/data'


def get_code_cells(notebook_path):
    """Read a notebook and return only its code cells."""
    nb = nbformat.read(notebook_path, as_version=4)
    return [cell for cell in nb.cells if cell.cell_type == 'code']


def exec_cell(cell_source, namespace, label=""):
    """Execute a cell's source code in the given namespace."""
    if cell_source.strip():
        exec(compile(cell_source, f'<{label}>', 'exec'), namespace)


def load_reader_env():
    """Load reader notebook environment (cells 0-9: imports, settings, functions)."""
    reader_cells = get_code_cells(
        os.path.join(notebook_dir, 'bd_CPS_reader.ipynb'))
    ns = {}
    for i in range(10):
        print(f'  Loading reader cell {i}...')
        exec_cell(reader_cells[i].source, ns, f'reader-{i}')
    return ns


# =====================================================================
# STEP 2: Regenerate 1994-1995 feather files (first pass)
# =====================================================================
print('=' * 60)
print('STEP 2: Regenerate 1994-1995 feather files (first pass)')
print('=' * 60)
t0 = time.time()

ns_reader = load_reader_env()

print('\n  Running cps_to_feather([1994, 1995])...')
ns_reader['cps_to_feather']([1994, 1995])
print(f'  Step 2 complete ({time.time() - t0:.0f}s).\n')


# =====================================================================
# STEP 3: Rebuild CPSID pickle files
# =====================================================================
print('=' * 60)
print('STEP 3: Rebuild CPSID pickle files')
print('=' * 60)
t0 = time.time()

os.chdir(data_dir)

# 3a. Back up and delete files that need regeneration
import pandas as pd

for fname in ['qstnum_map.pkl', 'CPSID_89-93.pkl']:
    if os.path.isfile(fname):
        os.rename(fname, fname + '.bak')
        print(f'  Backed up and removed {fname}')

# 3b. Remove May 1995 entry from CPS_unique_ids.pkl
ids_file = 'CPS_unique_ids.pkl'
cps_ids = pickle.load(open(ids_file, 'rb'))
may95 = pd.to_datetime('1995-05-01')
if may95 in cps_ids:
    del cps_ids[may95]
    with open(ids_file, 'wb') as f:
        pickle.dump(cps_ids, f)
    print(f'  Deleted May 1995 entry from {ids_file}')

# 3c. Run id notebook cells to regenerate pickle files
id_cells = get_code_cells(
    os.path.join(notebook_dir, 'bd_CPS_id.ipynb'))

ns_id = {}

# code_cells[0] = cell-1: imports + setup (loads modified cps_ids_full)
print('\n  Loading id notebook setup...')
exec_cell(id_cells[0].source, ns_id, 'id-setup')

# code_cells[3] = cell-4: return_dd_parser + id2_gen
print('  Loading id notebook helpers...')
exec_cell(id_cells[3].source, ns_id, 'id-helpers')

# Override raw_monthly_data_file_list to only include may95pub.dat
# (cell-5 would pick up all missing months including 2025+; we only need May 1995)
ns_id['raw_monthly_data_file_list'] = ['may95pub.dat']
print(f'  Set raw_monthly_data_file_list = {ns_id["raw_monthly_data_file_list"]}')

# code_cells[7] = cell-8: qstnum_map regeneration
print('\n  Regenerating qstnum_map.pkl...')
exec_cell(id_cells[7].source, ns_id, 'id-qstnum')

# code_cells[8] = cell-9: main ID generation loop (for May 1995)
print('\n  Regenerating May 1995 CPSID entry...')
exec_cell(id_cells[8].source, ns_id, 'id-main')

# code_cells[11] = cell-13: CPSID_89-93.pkl regeneration
print('\n  Regenerating CPSID_89-93.pkl...')
exec_cell(id_cells[11].source, ns_id, 'id-early')

# Clean up backup files
for fname in ['qstnum_map.pkl', 'CPSID_89-93.pkl']:
    bak = fname + '.bak'
    if os.path.isfile(bak):
        os.remove(bak)
        print(f'  Removed backup {bak}')

print(f'  Step 3 complete ({time.time() - t0:.0f}s).\n')


# =====================================================================
# STEP 4: Regenerate 1994-1995 feather files (second pass with CPSIDs)
# =====================================================================
print('=' * 60)
print('STEP 4: Regenerate 1994-1995 feather files (second pass)')
print('=' * 60)
t0 = time.time()

# Reload the entire reader environment so it picks up the new CPSID pickles
print('  Reloading reader environment with new CPSID dictionaries...')
ns_reader = load_reader_env()

print('\n  Running cps_to_feather([1994, 1995])...')
ns_reader['cps_to_feather']([1994, 1995])
print(f'  Step 4 complete ({time.time() - t0:.0f}s).\n')


# =====================================================================
# VERIFICATION
# =====================================================================
print('=' * 60)
print('VERIFICATION')
print('=' * 60)

import numpy as np

os.chdir(data_dir)

# 1. Check no more merged households
print('\n--- Merged household check ---')
df95 = pd.read_feather('clean/cps1995.ft')
for month in [1, 5, 6]:
    m = df95[df95['MONTH'] == month]
    max_hh_size = m.groupby('QSTNUM').size().max()
    hh_wgt_var = m.groupby('QSTNUM')['HHWGT'].nunique()
    merged = (hh_wgt_var > 1).sum()
    print(f'  Month {month}: max HH size={max_hh_size}, merged QSTNUMs={merged}')

# 2. Check household-level HHWGT totals
print('\n--- HHWGT totals (should be ~98-100M) ---')
for month in [1, 5, 6]:
    m = df95[df95['MONTH'] == month]
    hh_level = m.groupby('QSTNUM').first()
    total = hh_level['HHWGT'].sum() / 1e6
    print(f'  Month {month}: HH-level HHWGT = {total:.1f}M')

# 3. Check OCCURNUM sanity
print('\n--- OCCURNUM max (should be ~15) ---')
df94 = pd.read_feather('clean/cps1994.ft')
print(f"  Max OCCURNUM 1994: {df94['OCCURNUM'].max()}")
print(f"  Max OCCURNUM 1995: {df95['OCCURNUM'].max()}")

# 4. Check CPSID coverage
print('\n--- CPSID coverage ---')
for year in [1994, 1995]:
    df = pd.read_feather(f'clean/cps{year}.ft')
    for month in sorted(df['MONTH'].unique()):
        m = df[df['MONTH'] == month]
        has_cpsid = m['CPSID'].notna().sum()
        total = len(m)
        pct = has_cpsid / total * 100
        print(f'  {year}-{month:02d}: {has_cpsid}/{total} ({pct:.1f}%) have CPSID')

print('\nAll done!')
