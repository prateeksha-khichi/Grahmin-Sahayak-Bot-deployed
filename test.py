from services.loan_service import LoanService

loan_service = LoanService()

print("=" * 60)
print("LOAN MODEL TEST SUITE")
print("=" * 60)

# NOTE: loan_term must match how you pass it from Telegram bot.
# The Telegram bot asks users for months (e.g. 120, 180, 240).
# loan_service._prepare_features() automatically converts months → years for the model.
# EMI is always calculated back in months for the user.

# ✅ Test 1: Should be APPROVED — high CIBIL, good income, strong assets
approved_case = {
    "no_of_dependents": 1,
    "education": "Graduate",
    "self_employed": "No",
    "income_annum": 1200000,
    "loan_amount": 3000000,
    "loan_term": 120,               # 10 years in months (bot sends months)
    "cibil_score": 780,
    "residential_assets_value": 8000000,
    "commercial_assets_value": 2000000,
    "luxury_assets_value": 500000,
    "bank_asset_value": 300000,
}

# ❌ Test 2: Should be REJECTED — low CIBIL, low income, weak assets
rejected_case = {
    "no_of_dependents": 4,
    "education": "Not Graduate",
    "self_employed": "Yes",
    "income_annum": 200000,
    "loan_amount": 5000000,
    "loan_term": 60,                # 5 years in months
    "cibil_score": 450,
    "residential_assets_value": 500000,
    "commercial_assets_value": 0,
    "luxury_assets_value": 0,
    "bank_asset_value": 20000,
}

# 🔁 Test 3: Your original case
original_case = {
    "no_of_dependents": 3,
    "education": "Not Graduate",
    "self_employed": "Yes",
    "income_annum": 400000,
    "loan_amount": 1500000,
    "loan_term": 144,               # 12 years in months (training script used 12 = years, so 12*12=144)
    "cibil_score": 800,
    "residential_assets_value": 2000000,
    "commercial_assets_value": 0,
    "luxury_assets_value": 100000,
    "bank_asset_value": 60000,
}

test_cases = [
    ("Test 1 - Strong Profile     ", approved_case, "APPROVED"),
    ("Test 2 - Weak Profile       ", rejected_case, "REJECTED"),
    ("Test 3 - Your Original Case ", original_case, "CHECK"),
]

all_passed = True

for label, data, expected in test_cases:
    result = loan_service.predict_eligibility(data)
    eligible = result["eligible"]

    if expected == "APPROVED":
        passed = eligible is True
        expected_label = "APPROVED ✅"
    elif expected == "REJECTED":
        passed = eligible is False
        expected_label = "REJECTED ❌"
    else:
        passed = None
        expected_label = "CHECK    🔁"

    status = "✅ PASS" if passed is True else ("❌ FAIL" if passed is False else "🔁 RESULT")
    if passed is False:
        all_passed = False

    print(f"\n{label} → Expected: {expected_label}")
    print(f"  Eligible   : {eligible}  {status}")
    print(f"  Confidence : {result['confidence']:.0%}")
    print(f"  Amount     : ₹{result['recommended_amount']:,.0f}")
    print(f"  EMI        : ₹{result['emi']:,.0f}")
    print(f"  Interest   : {result['interest_rate']}%")
    print(f"  Tenure     : {result['tenure_months']} months")

print("\n" + "=" * 60)
if all_passed:
    print("🎉 ALL TESTS PASSED — Model is responding correctly!")
else:
    print("⚠️  SOME TESTS FAILED — Check output above.")
print("=" * 60)