"""
bd_CPS_telework.py

Process CPS Telework Supplement files into feather format.
Telework supplement started October 2022.

Two file formats:
- Oct 2022 - Nov 2023: 30 bytes (includes COVID comparison questions PTCOVR3/PTCOVR4)
- Dec 2023 forward: 22 bytes (COVID questions dropped)

Usage:
    python bd_CPS_telework.py

Output:
    clean/cps_telework2022.ft
    clean/cps_telework2023.ft
    clean/cps_telework2024.ft
"""

import pandas as pd
import numpy as np
import os
import struct

# Path configuration
TELEWORK_PATH = '/home/brian/Documents/CPS/data/Telework/'
OUTPUT_PATH = '/home/brian/Documents/CPS/data/clean/'

# File format definitions
# Format 1: Oct 2022 - Nov 2023 (30 bytes)
FORMAT_V1 = {
    'columns': ['QSTNUM', 'OCCURNUM', 'HRMONTH', 'HRYEAR',
                'PTCOVR1', 'PTCOVR2', 'PTCOVR3', 'PTCOVR4',
                'PXCOVR1', 'PXCOVR2', 'PXCOVR3', 'PXCOVR4'],
    'widths': [5, 2, 2, 4, 2, 3, 2, 2, 2, 2, 2, 2],
    'dtypes': {
        'QSTNUM': 'int32',
        'OCCURNUM': 'int8',
        'HRMONTH': 'int8',
        'HRYEAR': 'int16',
        'PTCOVR1': 'int8',
        'PTCOVR2': 'int16',
        'PTCOVR3': 'int8',
        'PTCOVR4': 'int8',
        'PXCOVR1': 'int8',
        'PXCOVR2': 'int8',
        'PXCOVR3': 'int8',
        'PXCOVR4': 'int8'
    }
}

# Format 2: Dec 2023 forward (22 bytes)
FORMAT_V2 = {
    'columns': ['QSTNUM', 'OCCURNUM', 'HRMONTH', 'HRYEAR',
                'PTCOVR1', 'PTCOVR2', 'PXCOVR1', 'PXCOVR2'],
    'widths': [5, 2, 2, 4, 2, 3, 2, 2],
    'dtypes': {
        'QSTNUM': 'int32',
        'OCCURNUM': 'int8',
        'HRMONTH': 'int8',
        'HRYEAR': 'int16',
        'PTCOVR1': 'int8',
        'PTCOVR2': 'int16',
        'PXCOVR1': 'int8',
        'PXCOVR2': 'int8'
    }
}

# Files by format version
V1_FILES = [
    'oct22cpucvr_pub.dat', 'nov22cpucvr_pub.dat', 'dec22cpucvr_pub.dat',
    'jan23cpucvr_pub.dat', 'feb23cpucvr_pub.dat', 'mar23cpucvr_pub.dat',
    'apr23cpucvr_pub.dat', 'may23cpucvr_pub.dat', 'jun23cpucvr_pub.dat',
    'jul23cpucvr_pub.dat', 'aug23cpucvr_pub.dat', 'sep23cpucvr_pub.dat',
    'oct23cpucvr_pub.dat', 'nov23cpucvr_puf.dat'
]

V2_FILES = [
    'dec23cpucvr_puf.dat',
    'jan24cpucvr_puf.dat', 'feb24cpucvr_puf.dat', 'mar24cpucvr_pub.dat',
    'apr24cpucvr_pub.dat', 'may24cpucvr_puf.dat'
]


def read_telework_file(filepath, fmt):
    """Read a fixed-width telework supplement file."""
    data = []
    with open(filepath, 'rb') as f:
        for line in f:
            # Strip line endings
            line = line.rstrip(b'\r\n')
            if len(line) == 0:
                continue

            # Parse fixed-width fields
            pos = 0
            row = []
            for width in fmt['widths']:
                field = line[pos:pos + width].decode('ascii').strip()
                try:
                    row.append(int(field))
                except ValueError:
                    row.append(-1)
                pos += width
            data.append(row)

    df = pd.DataFrame(data, columns=fmt['columns'])

    # Apply dtypes
    for col, dtype in fmt['dtypes'].items():
        df[col] = df[col].astype(dtype)

    return df


def process_telework_files():
    """Process all telework files and save as annual feather files."""

    all_data = []

    # Process V1 format files (Oct 2022 - Nov 2023)
    print("Processing V1 format files (Oct 2022 - Nov 2023)...")
    for filename in V1_FILES:
        filepath = os.path.join(TELEWORK_PATH, filename)
        if os.path.exists(filepath):
            df = read_telework_file(filepath, FORMAT_V1)
            all_data.append(df)
            print(f"  {filename}: {len(df):,} records")
        else:
            print(f"  {filename}: NOT FOUND")

    # Process V2 format files (Dec 2023+)
    print("\nProcessing V2 format files (Dec 2023+)...")
    for filename in V2_FILES:
        filepath = os.path.join(TELEWORK_PATH, filename)
        if os.path.exists(filepath):
            df = read_telework_file(filepath, FORMAT_V2)
            # Add missing columns for consistency
            df['PTCOVR3'] = np.int8(-1)
            df['PTCOVR4'] = np.int8(-1)
            df['PXCOVR3'] = np.int8(-1)
            df['PXCOVR4'] = np.int8(-1)
            # Reorder columns to match V1
            df = df[FORMAT_V1['columns']]
            all_data.append(df)
            print(f"  {filename}: {len(df):,} records")
        else:
            print(f"  {filename}: NOT FOUND")

    if not all_data:
        print("No files processed!")
        return

    # Combine all data
    combined = pd.concat(all_data, ignore_index=True)
    print(f"\nTotal records: {len(combined):,}")

    # Rename HRMONTH/HRYEAR for consistency with main CPS
    combined = combined.rename(columns={'HRMONTH': 'MONTH', 'HRYEAR': 'YEAR'})

    # Fix 2-digit years to 4-digit
    combined.loc[combined['YEAR'] < 100, 'YEAR'] += 2000

    # Split by year and save
    for year in combined['YEAR'].unique():
        year_data = combined[combined['YEAR'] == year].copy()
        # Drop YEAR column (will come from main CPS data)
        year_data = year_data.drop('YEAR', axis=1)

        output_file = os.path.join(OUTPUT_PATH, f'cps_telework{year}.ft')
        year_data.to_feather(output_file)

        months = sorted(year_data['MONTH'].unique())
        month_str = ', '.join(str(m) for m in months)
        print(f"Saved {output_file}: {len(year_data):,} records (months: {month_str})")


def validate_telework_files():
    """Validate the processed feather files."""
    print("\n" + "="*60)
    print("Validation")
    print("="*60)

    for year in [2022, 2023, 2024]:
        filepath = os.path.join(OUTPUT_PATH, f'cps_telework{year}.ft')
        if not os.path.exists(filepath):
            print(f"\n{year}: File not found")
            continue

        df = pd.read_feather(filepath)
        print(f"\n{year}:")
        print(f"  Records: {len(df):,}")
        print(f"  Months: {sorted(df['MONTH'].unique())}")
        print(f"  Columns: {list(df.columns)}")

        # Telework statistics
        employed = df[df['PTCOVR1'] > 0]
        teleworked = employed[employed['PTCOVR1'] == 1]
        if len(employed) > 0:
            pct = 100 * len(teleworked) / len(employed)
            print(f"  Telework rate: {pct:.1f}% ({len(teleworked):,} / {len(employed):,})")

        # Hours distribution for teleworkers
        if len(teleworked) > 0:
            hours = teleworked[teleworked['PTCOVR2'] >= 0]['PTCOVR2']
            if len(hours) > 0:
                print(f"  Hours teleworked (among teleworkers):")
                print(f"    Mean: {hours.mean():.1f}")
                print(f"    Median: {hours.median():.1f}")


if __name__ == '__main__':
    os.chdir('/home/brian/Documents/CPS/data')
    process_telework_files()
    validate_telework_files()
