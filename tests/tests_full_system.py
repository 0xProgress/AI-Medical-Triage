# test_full_system.py
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test():
    print("Testing Qwen Client...")
    
    from backend.models.qwen_client import qwen_client
    
    # Test symptom extraction
    print("\n1. Testing symptom extraction...")
    try:
        symptoms = await qwen_client.extract_symptoms(
            "I have a terrible sore throat and it hurts to swallow"
        )
        print(f"   ✅ Symptoms: {symptoms}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test follow-up
    print("\n2. Testing follow-up question...")
    try:
        follow_up = await qwen_client.generate_follow_up(
            ["sore throat", "painful swallowing"],
            [{"name": "Strep throat", "match_percentage": 85}]
        )
        print(f"   ✅ Follow-up: {follow_up}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

asyncio.run(test())