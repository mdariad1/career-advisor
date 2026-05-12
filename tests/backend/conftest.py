import sys
import os

# Make sure 'app' resolves to backend/app when running tests from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))
