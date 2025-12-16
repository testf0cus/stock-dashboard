import sys
import os

# Add current dir to sys.path
sys.path.append(os.getcwd())

try:
    from macro_data import fetch_high_yield_spread
    print("Import SUCCESS")
except ImportError as e:
    print(f"Import FAILED: {e}")
except Exception as e:
    print(f"Other Error: {e}")
