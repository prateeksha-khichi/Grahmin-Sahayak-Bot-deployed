"""
Model Feature Analyzer - Find out what your model REALLY expects
"""

import pandas as pd
import joblib
import numpy as np
from pathlib import Path

print("=" * 80)
print("MODEL FEATURE ANALYSIS")
print("=" * 80)

# Load model
model_path = Path("models/loan_eligibility/loan_eligibility_model.pkl")
model = joblib.load(model_path)

print(f"\n✅ Model loaded: {type(model).__name__}")
print(f"✅ Number of features: {model.n_features_in_}")

# Try to get feature names
try:
    feature_names = model.feature_names_in_
    print(f"\n📋 ACTUAL FEATURE NAMES FROM MODEL:")
    for i, name in enumerate(feature_names, 1):
        print(f"  {i}. {name}")
except:
    print("\n⚠️ Model doesn't have feature names stored")

# Check if we have the training data
print("\n" + "=" * 80)
print("CHECKING TRAINING DATA")
print("=" * 80)

data_files = [
    "data/loan_data.csv",
    "data/loan_eligibility.csv",
    "data/train.csv",
    "models/loan_eligibility/training_data.csv"
]

training_data = None
for file_path in data_files:
    if Path(file_path).exists():
        print(f"\n✅ Found data file: {file_path}")
        training_data = pd.read_csv(file_path)
        break

if training_data is not None:
    print(f"\n📊 Training data shape: {training_data.shape}")
    print(f"\n📋 COLUMNS IN TRAINING DATA:")
    for i, col in enumerate(training_data.columns, 1):
        print(f"  {i}. {col}")
    
    # Show sample data
    print(f"\n📄 SAMPLE DATA (first 3 rows):")
    print(training_data.head(3))
    
    # Check unique values for categorical columns
    print(f"\n📊 UNIQUE VALUES:")
    
    categorical_cols = training_data.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        unique_vals = training_data[col].unique()
        print(f"\n  {col}:")
        for val in unique_vals[:10]:  # Show first 10
            print(f"    - {val}")
else:
    print("\n❌ No training data file found")
    print("Please provide the path to your training CSV file")

# Try to understand the model's decision
print("\n" + "=" * 80)
print("TESTING DIFFERENT PROFILES")
print("=" * 80)

# Your rejected case
rejected_case = np.array([[
    3,          # dependents
    0,          # education (Not Graduate)
    1,          # self_employed (Yes)
    400000,     # income_annum
    1500000,    # loan_amount
    180,        # loan_term
    800,        # cibil_score
    2000000,    # residential_assets
    0,          # commercial_assets
    100000,     # luxury_assets
    60000       # bank_assets
]])

# Test different variations
test_cases = [
    ("Original (rejected)", rejected_case),
    ("Higher Income (8L)", np.array([[3, 0, 1, 800000, 1500000, 180, 800, 2000000, 0, 100000, 60000]])),
    ("Lower Loan (10L)", np.array([[3, 0, 1, 400000, 1000000, 180, 800, 2000000, 0, 100000, 60000]])),
    ("Longer Term (360)", np.array([[3, 0, 1, 400000, 1500000, 360, 800, 2000000, 0, 100000, 60000]])),
    ("Zero Dependents", np.array([[0, 0, 1, 400000, 1500000, 180, 800, 2000000, 0, 100000, 60000]])),
    ("Graduate + High Income", np.array([[2, 1, 1, 600000, 4000000, 240, 800, 2000000, 500000, 300000, 100000]])),
]

print("\nFeature order being used:")
print("1. dependents, 2. education, 3. self_employed, 4. income_annum,")
print("5. loan_amount, 6. loan_term, 7. cibil_score, 8. residential_assets,")
print("9. commercial_assets, 10. luxury_assets, 11. bank_assets")

for name, features in test_cases:
    try:
        pred = model.predict(features)[0]
        prob = model.predict_proba(features)[0]
        
        result = "✅ APPROVED" if pred == 1 else "❌ REJECTED"
        print(f"\n{name}:")
        print(f"  Result: {result}")
        print(f"  Confidence: Reject={prob[0]:.1%}, Approve={prob[1]:.1%}")
        print(f"  Features: {features[0]}")
    except Exception as e:
        print(f"\n{name}: ERROR - {e}")

# Check feature importances
print("\n" + "=" * 80)
print("FEATURE IMPORTANCES")
print("=" * 80)

try:
    importances = model.feature_importances_
    feature_list = [
        'dependents', 'education', 'self_employed', 'income_annum',
        'loan_amount', 'loan_term', 'cibil_score', 'residential_assets',
        'commercial_assets', 'luxury_assets', 'bank_assets'
    ]
    
    # Sort by importance
    sorted_idx = np.argsort(importances)[::-1]
    
    print("\nMost important features (top to bottom):")
    for i, idx in enumerate(sorted_idx, 1):
        print(f"  {i}. {feature_list[idx]}: {importances[idx]:.4f}")
    
    # Highlight critical features
    print("\n🔍 CRITICAL FEATURES (importance > 0.10):")
    for idx in sorted_idx:
        if importances[idx] > 0.10:
            print(f"  ⚠️ {feature_list[idx]}: {importances[idx]:.4f}")

except Exception as e:
    print(f"Cannot get feature importances: {e}")

# Final diagnosis
print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

print("""
Based on the analysis:

1. Your model is rejecting at 91% confidence
2. Even changing education doesn't help much
3. This suggests the model learned patterns we need to understand

POSSIBLE ISSUES:
❌ Feature order mismatch
❌ Feature scaling/encoding mismatch  
❌ Model expects different value ranges
❌ Model trained on different data distribution

NEXT STEPS:
1. Check the ACTUAL training data CSV
2. Compare feature names in training data vs what we're sending
3. Check if features were scaled/normalized during training
4. Verify the exact preprocessing used during training
""")

print("\n" + "=" * 80)
print("ACTION REQUIRED")
print("=" * 80)
print("""
Please provide:
1. The CSV file used to train this model
2. The training script (if available)
3. Any preprocessing/encoding scripts

This will help us match the exact format your model expects!
""")