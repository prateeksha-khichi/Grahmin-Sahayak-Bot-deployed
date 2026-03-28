"""
Run this script to diagnose what's wrong with your model.
It will show you exactly what the training data looks like
and why the model is predicting backwards.
"""

from pathlib import Path
import joblib
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
model_path = BASE_DIR / "models" / "loan_eligibility" / "loan_eligibility_model.pkl"
model = joblib.load(model_path)

print("=" * 60)
print("MODEL DIAGNOSTICS")
print("=" * 60)

# ── 1. Feature names ──────────────────────────────────────────
print("\n📋 Feature names model was trained with:")
for i, name in enumerate(model.feature_names_in_):
    print(f"   [{i}] {name}")

# ── 2. Class labels ───────────────────────────────────────────
print(f"\n🏷  Classes: {model.classes_}")
print(f"   → predict_proba index 0 = class {model.classes_[0]}")
print(f"   → predict_proba index 1 = class {model.classes_[1]}")
print(f"   → We assume class 1 = Approved. Is that correct?")

# ── 3. Feature importances ────────────────────────────────────
print("\n📊 Feature importances (what the model actually cares about):")
importances = model.feature_importances_
for name, imp in sorted(zip(model.feature_names_in_, importances), key=lambda x: -x[1]):
    bar = "█" * int(imp * 50)
    print(f"   {name:<30} {imp:.4f}  {bar}")

# ── 4. Try approved case manually ────────────────────────────
print("\n🧪 Manual prediction — STRONG profile (should approve):")
strong = pd.DataFrame([{
    "no_of_dependents":         1,
    "education":                1,       # Graduate
    "self_employed":            0,       # No
    "income_annum":             1200000,
    "loan_amount":              3000000,
    "loan_term":                120,
    "cibil_score":              780,
    "residential_assets_value": 8000000,
    "commercial_assets_value":  2000000,
    "luxury_assets_value":      500000,
    "bank_asset_value":         300000,
}])
pred = model.predict(strong)[0]
proba = model.predict_proba(strong)[0]
print(f"   Raw prediction: {pred}")
print(f"   Probabilities:  class {model.classes_[0]}={proba[0]:.2%}  class {model.classes_[1]}={proba[1]:.2%}")

print("\n🧪 Manual prediction — WEAK profile (should reject):")
weak = pd.DataFrame([{
    "no_of_dependents":         4,
    "education":                0,       # Not Graduate
    "self_employed":            1,       # Yes
    "income_annum":             200000,
    "loan_amount":              5000000,
    "loan_term":                60,
    "cibil_score":              450,
    "residential_assets_value": 500000,
    "commercial_assets_value":  0,
    "luxury_assets_value":      0,
    "bank_asset_value":         20000,
}])
pred2 = model.predict(weak)[0]
proba2 = model.predict_proba(weak)[0]
print(f"   Raw prediction: {pred2}")
print(f"   Probabilities:  class {model.classes_[0]}={proba2[0]:.2%}  class {model.classes_[1]}={proba2[1]:.2%}")

# ── 5. Check training data if available ──────────────────────
print("\n📂 Looking for training data CSV...")
possible_paths = list(BASE_DIR.rglob("*.csv"))
if possible_paths:
    for p in possible_paths:
        print(f"   Found: {p}")
    # Load the first one
    df = pd.read_csv(possible_paths[0])
    print(f"\n📊 Training data shape: {df.shape}")
    print(f"\n📋 Columns: {list(df.columns)}")

    # Find the target column
    target_col = None
    for col in df.columns:
        if "status" in col.lower() or "approv" in col.lower() or "loan_status" in col.lower() or "eligible" in col.lower():
            target_col = col
            break

    if target_col:
        print(f"\n🎯 Target column: '{target_col}'")
        print(f"   Value counts:\n{df[target_col].value_counts()}")
        print(f"\n   ⚠️  Check: which value means APPROVED?")
        print(f"   If '1' or 'Approved' is the minority class, model may be flipped.")

        # Show approved vs rejected profile averages
        approved_mask = df[target_col].isin([1, "Approved", "approved", "Y", "Yes"])
        print(f"\n📈 Average income — Approved: ₹{df[approved_mask]['income_annum'].mean():,.0f}")
        print(f"📈 Average income — Rejected: ₹{df[~approved_mask]['income_annum'].mean():,.0f}")
        print(f"📈 Average CIBIL  — Approved: {df[approved_mask]['cibil_score'].mean():.0f}")
        print(f"📈 Average CIBIL  — Rejected: {df[~approved_mask]['cibil_score'].mean():.0f}")
    else:
        print(f"   ⚠️  Could not auto-detect target column. Columns are: {list(df.columns)}")
else:
    print("   No CSV found. Paste your training data path manually.")

print("\n" + "=" * 60)
print("WHAT TO LOOK FOR:")
print("=" * 60)
print("""
1. Classes output: if classes = [0, 1], then class 1 = Approved ✅
   If classes = ['Approved', 'Rejected'], check which index is which.

2. If strong profile gets high probability for class 0 → labels are FLIPPED
   in your training data (0=Approved, 1=Rejected instead of normal).

3. Feature importances: CIBIL score should be the #1 most important feature.
   If it's near the bottom, your training data had issues.

4. Training data averages: Approved group should have HIGHER income and CIBIL
   than Rejected. If it's reversed, labels were encoded backwards.
""")