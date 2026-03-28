"""
Debug Script - Test the exact case that was rejected
"""

import numpy as np
import joblib
from pathlib import Path

# Your actual test case from the bot
test_case = {
    "no_of_dependents": 3,
    "education": "No",  # This is the issue! "No" instead of "Not Graduate"
    "self_employed": "Yes",
    "income_annum": 400000,
    "loan_amount": 1500000,
    "loan_term": 180,
    "cibil_score": 800,
    "residential_assets_value": 2000000,
    "commercial_assets_value": 0,
    "luxury_assets_value": 100000,
    "bank_asset_value": 60000
}

print("=" * 70)
print("DEBUGGING LOAN REJECTION")
print("=" * 70)
print("\nUser Input:")
for key, value in test_case.items():
    print(f"  {key}: {value}")

# Check education value
print("\n" + "=" * 70)
print("ISSUE FOUND!")
print("=" * 70)
print(f"\nEducation value: '{test_case['education']}'")
print("Expected values: 'Graduate' or 'Not Graduate'")
print("User typed: 'No' (which is WRONG!)")
print("\n⚠️ The bot should only accept 'Graduate' or 'Not Graduate'")
print("⚠️ But user typed 'No' which got accepted")

# Prepare features as the model expects
def prepare_features(data):
    """Prepare features exactly as model expects"""
    
    # Education encoding
    education_raw = str(data.get("education", "Graduate")).lower()
    if "graduate" in education_raw or "grad" in education_raw:
        education = 1
    else:
        education = 0
    
    # Self employed encoding
    self_employed_raw = str(data.get("self_employed", "No")).lower()
    if "yes" in self_employed_raw or "self" in self_employed_raw:
        self_employed = 1
    else:
        self_employed = 0
    
    # Build feature array
    features = np.array([[
        data.get("no_of_dependents", 0),
        education,
        self_employed,
        data.get("income_annum", 0),
        data.get("loan_amount", 0),
        data.get("loan_term", 240),
        data.get("cibil_score", 650),
        data.get("residential_assets_value", 0),
        data.get("commercial_assets_value", 0),
        data.get("luxury_assets_value", 0),
        data.get("bank_asset_value", 0)
    ]])
    
    return features, education, self_employed

features, education_encoded, self_employed_encoded = prepare_features(test_case)

print("\n" + "=" * 70)
print("ENCODED FEATURES")
print("=" * 70)
print(f"\nEducation: '{test_case['education']}' → {education_encoded} (0=Not Graduate, 1=Graduate)")
print(f"Self Employed: '{test_case['self_employed']}' → {self_employed_encoded}")
print(f"\nFull feature array:")
print(features[0])

print("\n" + "=" * 70)
print("PROFILE ANALYSIS")
print("=" * 70)

# Calculate ratios
income = test_case['income_annum']
loan_amt = test_case['loan_amount']
total_assets = (
    test_case['residential_assets_value'] +
    test_case['commercial_assets_value'] +
    test_case['luxury_assets_value'] +
    test_case['bank_asset_value']
)

loan_to_income = loan_amt / income
asset_to_loan = total_assets / loan_amt * 100

print(f"\nIncome Analysis:")
print(f"  Annual Income: ₹{income:,.0f}")
print(f"  Monthly Income: ₹{income/12:,.0f}")
print(f"  Loan Amount: ₹{loan_amt:,.0f}")
print(f"  Loan-to-Income Ratio: {loan_to_income:.2f}x")

print(f"\nAsset Analysis:")
print(f"  Residential: ₹{test_case['residential_assets_value']:,.0f}")
print(f"  Commercial: ₹{test_case['commercial_assets_value']:,.0f}")
print(f"  Luxury: ₹{test_case['luxury_assets_value']:,.0f}")
print(f"  Bank: ₹{test_case['bank_asset_value']:,.0f}")
print(f"  Total Assets: ₹{total_assets:,.0f}")
print(f"  Asset-to-Loan Ratio: {asset_to_loan:.1f}%")

print(f"\nOther Factors:")
print(f"  CIBIL Score: {test_case['cibil_score']} (Excellent!)")
print(f"  Dependents: {test_case['no_of_dependents']}")
print(f"  Loan Term: {test_case['loan_term']} months")

print("\n" + "=" * 70)
print("WHY THIS SHOULD BE APPROVED")
print("=" * 70)
print("\n✅ Strong Points:")
print("  • Excellent CIBIL (800)")
print("  • Strong assets (₹21.6L covers 144% of loan)")
print("  • Reasonable loan amount (₹15L)")
print("  • Loan is only 3.75x annual income")
print("  • Self-employed (business owner)")

print("\n⚠️ Weak Points:")
print("  • Education: 'No' → encoded as 0 (Not Graduate)")
print("  • 3 dependents (slightly high)")
print("  • Moderate income (₹4L/year)")

print("\n" + "=" * 70)
print("SOLUTION")
print("=" * 70)
print("\n❌ PROBLEM: User typed 'No' for education")
print("✅ FIX: Add validation to only accept 'Graduate' or 'Not Graduate'")

print("\n" + "=" * 70)
print("CORRECTED TEST CASES")
print("=" * 70)

# Test with corrected education
corrected_case_1 = test_case.copy()
corrected_case_1['education'] = 'Not Graduate'

corrected_case_2 = test_case.copy()
corrected_case_2['education'] = 'Graduate'

print("\nCase 1: Education = 'Not Graduate'")
print(corrected_case_1)

print("\nCase 2: Education = 'Graduate'")
print(corrected_case_2)

print("\n" + "=" * 70)
print("TRY LOADING THE MODEL")
print("=" * 70)

# Try to load and test the model
try:
    model_path = Path("models/loan_eligibility/loan_eligibility_model.pkl")
    
    if model_path.exists():
        model = joblib.load(model_path)
        print(f"\n✅ Model loaded successfully")
        print(f"✅ Model expects {model.n_features_in_} features")
        
        # Test prediction
        print("\n" + "=" * 70)
        print("TESTING PREDICTIONS")
        print("=" * 70)
        
        # Original case (education = "No")
        features_original, _, _ = prepare_features(test_case)
        pred_original = model.predict(features_original)[0]
        prob_original = model.predict_proba(features_original)[0]
        
        print(f"\nOriginal (Education='No'):")
        print(f"  Prediction: {'APPROVED' if pred_original == 1 else 'REJECTED'}")
        print(f"  Probability: Reject={prob_original[0]:.2%}, Approve={prob_original[1]:.2%}")
        
        # Corrected case 1 (Not Graduate)
        features_corrected1, _, _ = prepare_features(corrected_case_1)
        pred_corrected1 = model.predict(features_corrected1)[0]
        prob_corrected1 = model.predict_proba(features_corrected1)[0]
        
        print(f"\nCorrected (Education='Not Graduate'):")
        print(f"  Prediction: {'APPROVED ✅' if pred_corrected1 == 1 else 'REJECTED ❌'}")
        print(f"  Probability: Reject={prob_corrected1[0]:.2%}, Approve={prob_corrected1[1]:.2%}")
        
        # Corrected case 2 (Graduate)
        features_corrected2, _, _ = prepare_features(corrected_case_2)
        pred_corrected2 = model.predict(features_corrected2)[0]
        prob_corrected2 = model.predict_proba(features_corrected2)[0]
        
        print(f"\nCorrected (Education='Graduate'):")
        print(f"  Prediction: {'APPROVED ✅' if pred_corrected2 == 1 else 'REJECTED ❌'}")
        print(f"  Probability: Reject={prob_corrected2[0]:.2%}, Approve={prob_corrected2[1]:.2%}")
        
    else:
        print(f"\n❌ Model not found at: {model_path}")
        print("Please provide the correct model path")
        
except Exception as e:
    print(f"\n❌ Error loading model: {e}")
    print("\nPlease ensure:")
    print("  1. Model file exists")
    print("  2. Model was trained with same feature order")
    print("  3. All dependencies are installed")

print("\n" + "=" * 70)