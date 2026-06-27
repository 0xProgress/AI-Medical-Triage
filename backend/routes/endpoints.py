from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from pathlib import Path
from backend.models.schemas import ChatRequest, ChatResponse, ReportRequest, ReportResponse, Message
from backend.ai.triage import triage_engine
from backend.services.report_generator import report_generator
from backend.config import config
from datetime import datetime
import traceback
import base64
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if not request.message or len(request.message.strip()) < 3:
            raise HTTPException(status_code=400, detail="Message too short. Please describe your symptoms.")
        
        result = await triage_engine.process_message(
            session_id=request.session_id,
            message=request.message,
            conversation_history=request.conversation_history
        )
        
        return ChatResponse(
            session_id=result["session_id"],
            message=result["message"],
            conditions=result.get("conditions", []),
            follow_up_question=result.get("follow_up_question"),
            red_flags=result.get("red_flags", []),
            is_complete=result.get("is_complete", False),
            turn=result.get("turn", 0),
            max_turns_reached=result.get("max_turns_reached", False)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/report")
async def generate_report(request: ReportRequest, background_tasks: BackgroundTasks):
    try:
        triage_data = await triage_engine.get_report_data(request.session_id)
        
        if not triage_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not triage_data.get('summary'):
            triage_data['summary'] = "No clinical summary available. Please consult a healthcare provider."
        
        pdf_path = report_generator.generate_report(request.session_id, triage_data)
        
        # Read PDF into memory
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        
        # Schedule cleanup
        def cleanup():
            import os
            try:
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
            except:
                pass
        
        background_tasks.add_task(cleanup)
        
        return JSONResponse({
            "report_url": f"data:application/pdf;base64,{pdf_b64}",
            "download_url": f"data:application/pdf;base64,{pdf_b64}",
            "generated_at": datetime.now().isoformat()
        })
    except HTTPException:
        raise
    except Exception as e:
        print(f"Report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}")
async def get_session(session_id: str):
    session = triage_engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "turn_count": session.turn_count,
        "is_complete": session.is_complete,
        "symptoms": session.extracted_symptoms,
        "conversation": [msg.dict() for msg in session.conversation]
    }

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    triage_engine.delete_session(session_id)
    return {"status": "deleted"}

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": config.APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }


async def rebuild_from_history(session_id: str, conversation_history: List[Message]):
    """Rebuild triage data from conversation history when session is missing."""
    from backend.models.schemas import SessionData
    from backend.database.queries import find_diseases_by_symptoms, check_red_flags, get_urgency_level
    
    temp_session = SessionData(
        session_id=session_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        conversation=conversation_history,
        extracted_symptoms=[],
        turn_count=len(conversation_history),
        is_complete=False
    )
    
    all_symptoms = []
    for msg in conversation_history:
        if msg.role == "user":
            extracted = await qwen_client.extract_symptoms(msg.content)
            all_symptoms.extend(extracted)

    temp_session.extracted_symptoms = list(set(all_symptoms))
    
    matches = find_diseases_by_symptoms(temp_session.extracted_symptoms, limit=5)
    
    condition_matches = []
    if matches:
        from backend.database.queries import get_diseases_batch
        disease_names = [m[0] for m in matches[:5]]
        disease_details = get_diseases_batch(disease_names)
        
        for match in matches[:5]:
            name, match_count, match_percentage = match
            detail = next((d for d in disease_details if d['name'] == name), None)
            if detail:
                urgency = get_urgency_level(name)
                condition_matches.append({
                    'name': name,
                    'description': detail.get('description', ''),
                    'match_score': float(match_count) * 2.0,
                    'symptom_count': match_count,
                    'match_percentage': float(match_percentage),
                    'urgency': urgency,
                    'precautions': detail.get('precautions', []),
                    'medications': detail.get('medications', []),
                    'diet': detail.get('diet', []),
                    'workouts': detail.get('workouts', []),
                    'red_flags': detail.get('red_flags', [])
                })
    
    red_flags = check_red_flags(temp_session.extracted_symptoms)
    
    from backend.models.qwen_client import qwen_client
    summary = await qwen_client.generate_summary(
        [msg.dict() for msg in conversation_history],
        condition_matches[:3]
    )
    
    return {
        "session_id": session_id,
        "conversation": [msg.dict() for msg in conversation_history],
        "symptoms": temp_session.extracted_symptoms,
        "conditions": condition_matches,
        "red_flags": red_flags,
        "summary": summary,
        "turn_count": len(conversation_history)
    }