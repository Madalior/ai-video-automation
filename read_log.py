
import sys

try:
    with open("debug_run.log", "r", encoding="utf-8", errors="ignore") as f:
        print(f.read())
except Exception as e:
    print(f"Error reading log: {e}")
