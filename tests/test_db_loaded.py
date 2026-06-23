# test_db_loaded.py
from backend.database.queries import get_all_symptoms, get_disease_count, get_disease_details

print("=" * 50)
print("Checking Database Contents")
print("=" * 50)

# Check total diseases
count = get_disease_count()
print(f"✅ Total diseases: {count}")

# Check symptoms
symptoms = get_all_symptoms()
print(f"✅ Total symptoms: {len(symptoms)}")
print(f"   First 10: {symptoms[:10]}")

# Check a specific disease
details = get_disease_details("strep throat")
if details:
    print(f"\n✅ Strep throat found!")
    print(f"   Description: {details['description'][:80]}...")
    print(f"   Symptoms: {len(details['symptoms'])}")
    print(f"   Precautions: {details['precautions']}")
else:
    print("\n⚠️ Strep throat not found")

# Check another disease
details = get_disease_details("panic disorder")
if details:
    print(f"\n✅ Panic disorder found!")
    print(f"   Symptoms: {len(details['symptoms'])}")
    print(f"   Medications: {details['medications'][:2]}")