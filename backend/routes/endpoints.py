from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from pathlib import Path
from backend.models.schemas import ChatRequest, ChatResponse, ReportRequest, ReportResponse, Message
from backend.ai.triage import triage_engine
from backend.services.report_generator import report_generator
from backend.config import config
from datetime import datetime
import traceback
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
            triage_data['summary'] = "No clinical summary available."
        
        # Generate Markdown report
        report_path = report_generator.generate_report(request.session_id, triage_data)
        
        # Read the markdown file
        with open(report_path, "r") as f:
            markdown_content = f.read()
        
        # Schedule cleanup
        def cleanup():
            import os
            try:
                if os.path.exists(report_path):
                    os.remove(report_path)
            except:
                pass
        
        background_tasks.add_task(cleanup)
        
        return JSONResponse({
            "report_markdown": markdown_content,
            "format": "markdown",
            "generated_at": datetime.now().isoformat()
        })
    except HTTPException:
        raise
    except Exception as e:
        print(f"Report error: {traceback.format_exc()}")
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