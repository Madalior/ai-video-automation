
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Direct imports - no package structure
import flowchart.character.image_generator as img_gen_module
import flowchart.common.browser_utils

# Test import
print("[TEST] Image generator module imported successfully")

# Create generator instance
gen = img_gen_module.DreaminaGenerator(headless=False, profile_path=os.path.abspath("chrome_data_img_test"))

# Try login
print("[TEST] Attempting login...")
if gen.login():
    print("[SUCCESS] Login successful!")
    gen.close()
else:
    print("[FAILED] Login failed")
    gen.close()
    sys.exit(1)
