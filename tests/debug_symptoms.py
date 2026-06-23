# debug_symptoms_full.py
from backend.database.queries import get_connection

conn = get_connection()
cursor = conn.cursor()

# Get ALL symptoms
cursor.execute("SELECT name FROM symptoms ORDER BY name")
all_symptoms = cursor.fetchall()

print(f"Total symptoms: {len(all_symptoms)}")
print("\nFirst 50 symptoms:")
for i, row in enumerate(all_symptoms[:50]):
    print(f"  {i+1}. {row[0]}")

# Check if "difficulty swallowing" exists
cursor.execute("SELECT name FROM symptoms WHERE name LIKE '%swallow%'")
results = cursor.fetchall()
print(f"\nSymptoms containing 'swallow': {len(results)}")
for row in results:
    print(f"  - {row[0]}")

# Check Strep throat's symptoms
cursor.execute("""
SELECT s.name
FROM diseases d
JOIN disease_symptoms ds ON d.id = ds.disease_id
JOIN symptoms s ON ds.symptom_id = s.id
WHERE d.name = 'strep throat'
""")
strep = cursor.fetchall()
print(f"\nStrep throat symptoms ({len(strep)}):")
for row in strep[:20]:
    print(f"  - {row[0]}")

conn.close()