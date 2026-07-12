# test.py
import sqlite3
import json
from backend.config import config

conn = sqlite3.connect(str(config.SQLITE_DB_PATH))
cursor = conn.cursor()

# Check if "cold" exists as a symptom
cursor.execute("SELECT COUNT(*) FROM diseases WHERE symptoms LIKE '%cold%'")
cold_count = cursor.fetchone()[0]
print(f"Diseases with 'cold': {cold_count}")

# Check if "loss of appetite" exists
cursor.execute("SELECT COUNT(*) FROM diseases WHERE symptoms LIKE '%loss of appetite%'")
appetite_count = cursor.fetchone()[0]
print(f"Diseases with 'loss of appetite': {appetite_count}")

# Check if "appetite" exists
cursor.execute("SELECT COUNT(*) FROM diseases WHERE symptoms LIKE '%appetite%'")
any_appetite = cursor.fetchone()[0]
print(f"Diseases with 'appetite': {any_appetite}")

# Show some actual symptom names from the DB
cursor.execute("SELECT symptoms FROM diseases LIMIT 3")
for row in cursor.fetchall():
    symptoms = json.loads(row[0])[:10]
    print(f"Sample symptoms: {symptoms}")

conn.close()