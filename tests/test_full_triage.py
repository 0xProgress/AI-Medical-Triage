# test_full_triage.py
import asyncio
from backend.ai.triage import triage_engine

async def test_full_triage():
    print("=" * 60)
    print("Testing Full Triage Flow (AI + Database)")
    print("=" * 60)
    
    session_id = None
    
    # Turn 1: User describes symptoms
    print("\n📝 Turn 1: User describes symptoms")
    user_input = "I have a severe sore throat and it hurts to swallow. I think I have a fever too."
    print(f"   User: {user_input}")
    
    result = await triage_engine.process_message(session_id, user_input)
    session_id = result["session_id"]
    
    print(f"\n🤖 AI Response:")
    print(f"   Message: {result['message'][:150]}...")
    print(f"   Conditions: {len(result.get('conditions', []))}")
    print(f"   Red Flags: {result.get('red_flags', [])}")
    print(f"   Is Complete: {result.get('is_complete', False)}")
    
    if result.get('conditions'):
        print("\n   Top Conditions:")
        for i, cond in enumerate(result['conditions'][:3], 1):
            print(f"   {i}. {cond['name']} - {cond['match_percentage']}% match")
            print(f"      Description: {cond['description'][:80]}...")
            print(f"      Urgency: {cond['urgency']}")
    
    # Turn 2: User answers follow-up
    if result.get('follow_up_question'):
        print(f"\n📝 Turn 2: User answers follow-up")
        print(f"   AI: {result['follow_up_question']}")
        print(f"   User: Yes, I have white patches on my tonsils")
        
        result2 = await triage_engine.process_message(
            session_id, 
            "Yes, I have white patches on my tonsils"
        )
        
        print(f"\n🤖 AI Response:")
        print(f"   Message: {result2['message'][:150]}...")
        print(f"   Conditions: {len(result2.get('conditions', []))}")
        print(f"   Is Complete: {result2.get('is_complete', False)}")
        
        if result2.get('conditions'):
            print("\n   Top Conditions:")
            for i, cond in enumerate(result2['conditions'][:3], 1):
                print(f"   {i}. {cond['name']} - {cond['match_percentage']}% match")
                print(f"      Description: {cond['description'][:80]}...")
    
    print("\n" + "=" * 60)
    print("✅ Triage Flow Test Complete!")
    print("=" * 60)

asyncio.run(test_full_triage())