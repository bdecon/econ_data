import os
import sys

print("=" * 70)
print("Regenerating 1994 CPS Data (Step 2 of 4)")
print("=" * 70)
print("\nPlease follow these steps in Jupyter Notebook:\n")
print("1. Open: http://localhost:8888")
print("2. Navigate to: econ_data/bd_CPS/bd_CPS_reader.ipynb")
print("3. Run cells 1-10 to load all functions")
print("4. In a new cell, run: cps_to_feather([1994])")
print("   (This will take about 5-10 minutes)")
print("5. Then run: cps_to_feather([1995])")
print("   (This will take another 5-10 minutes)")
print("\nAlternatively, you can run both at once:")
print("   cps_to_feather([1994, 1995])")
print("\n" + "=" * 70)
