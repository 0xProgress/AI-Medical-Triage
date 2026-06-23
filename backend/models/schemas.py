from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    conversation_history: Optional[List[Message]] = []

class ChatResponse(BaseModel):
    session_id: str
    message: str
    conditions: Optional[List[Dict[str, Any]]] = []
    follow_up_question: Optional[str] = None
    red_flags: Optional[List[str]] = []
    is_complete: bool = False
    turn: int = 0
    max_turns_reached: bool = False

class ReportRequest(BaseModel):
    session_id: str
    conversation_history: Optional[List[Message]] = []

class ReportResponse(BaseModel):
    report_url: str
    download_url: str
    generated_at: datetime

class ConditionMatch(BaseModel):
    name: str
    description: str
    match_score: float
    symptom_count: int
    match_percentage: float
    urgency: str
    precautions: List[str]
    medications: List[str]
    diet: List[str]
    workouts: List[str]
    red_flags: List[str]

class TriageResult(BaseModel):
    conditions: List[ConditionMatch]
    follow_up_question: Optional[str] = None
    red_flags: List[str] = []
    is_complete: bool = False
    need_immediate_care: bool = False

class SessionData(BaseModel):
    session_id: str
    created_at: datetime
    updated_at: datetime
    conversation: List[Message]
    extracted_symptoms: List[str]
    turn_count: int
    is_complete: bool