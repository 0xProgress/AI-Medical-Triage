# test_qwen_with_db.py
import asyncio
from backend.database.queries import find_diseases_by_symptoms, get_disease_details
from backend.models.qwen_client import qwen_client

async def test_qwen_with_db():
    print("=" * 60)
    print("Testing Qwen with Database Integration")
    print("=" * 60)
    
    # Step 1: Simulate user input
    user_message = "I have a sore throat and it hurts to swallow"
    print(f"\n📝 User: {user_message}")
    
    # Step 2: Extract symptoms using Qwen
    print("\n🔍 Step 1: Extracting symptoms with Qwen...")
    symptoms = await qwen_client.extract_symptoms(user_message)
    print(f"   Symptoms: {symptoms}")
    
    # Step 3: Query database for matching diseases
    print("\n🗄️ Step 2: Querying database...")
    matches = find_diseases_by_symptoms(symptoms, limit=5)
    
    if matches:
        print(f"   Found {len(matches)} matching diseases:")
        for name, count, percentage in matches[:3]:
            print(f"   - {name}: {count} symptoms matched ({percentage}%)")
        
        # Step 4: Get full details for top match
        top_disease = matches[0][0]
        details = get_disease_details(top_disease)
        
        print(f"\n📋 Step 3: Details for top match ({top_disease})")
        if details:
            print(f"   Description: {details['description'][:100]}...")
            print(f"   Precautions: {details['precautions'][:2]}")
            print(f"   Medications: {details['medications'][:2]}")
            print(f"   Diet: {details['diet'][:2]}")
            print(f"   Workouts: {details['workouts'][:2]}")
            print(f"   Total Symptoms: {len(details['symptoms'])}")
        
        # Step 5: Generate follow-up question using Qwen
        print("\n🤖 Step 4: Generating follow-up question...")
        follow_up = await qwen_client.generate_follow_up(
            symptoms, 
            [{"name": m[0], "match_percentage": m[2]} for m in matches[:3]]
        )
        print(f"   Qwen: {follow_up}")
        
    else:
        print("   No matching diseases found in database.")
    
    print("\n" + "=" * 60)
    print("✅ Test Complete!")
    print("=" * 60)

asyncio.run(test_qwen_with_db())