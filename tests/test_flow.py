# test_flow.py
import requests
import json

BASE = "http://localhost:8000/api/v1"

# Start
r = requests.post(f"{BASE}/chat", json={
    "message": "I have a severe sore throat, it hurts to swallow, and I have a fever"
})
data = r.json()
session_id = data["session_id"]
print(f"Session: {session_id}")
print(f"Message: {data['message'][:150]}...")
print(f"Conditions: {len(data.get('conditions', []))}")

# Answer follow-up
if data.get("follow_up_question"):
    print("\n" + "="*50)
    print("Follow-up asked. Responding...")
    r = requests.post(f"{BASE}/chat", json={
        "session_id": session_id,
        "message": "Yes, I have white patches on my tonsils"
    })
    data = r.json()
    print(f"Message: {data['message'][:150]}...")

# Generate report
print("\n" + "="*50)
print("Generating report...")
r = requests.post(f"{BASE}/report", json={"session_id": session_id})
print(f"Report: {r.json().get('download_url', 'N/A')}")