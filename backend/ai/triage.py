import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from backend.models.schemas import (
    Message, 
    TriageResult, 
    ConditionMatch, 
    SessionData
)
from backend.models.qwen_client import qwen_client
from backend.database.queries import (
    find_diseases_by_symptoms,
    get_disease_details,
    get_diseases_batch,
    check_red_flags,
    get_urgency_level
)
from backend.config import config

class TriageEngine:
    def __init__(self):
        self.sessions: Dict[str, SessionData] = {}
        self.max_turns = config.MAX_TURNS
    
    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = SessionData(
            session_id=session_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            conversation=[],
            extracted_symptoms=[],
            turn_count=0,
            is_complete=False
        )
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, **kwargs):
        if session_id in self.sessions:
            for key, value in kwargs.items():
                setattr(self.sessions[session_id], key, value)
            self.sessions[session_id].updated_at = datetime.now()
    
    def delete_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    async def process_message(
        self, 
        session_id: Optional[str], 
        message: str,
        conversation_history: List[Message] = []
    ) -> Dict[str, Any]:
        if not session_id:
            session_id = self.create_session()
        
        session = self.get_session(session_id)
        
        if not session and conversation_history:
            session = SessionData(
                session_id=session_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                conversation=conversation_history.copy(),
                extracted_symptoms=[],
                turn_count=len(conversation_history),
                is_complete=False
            )
            self.sessions[session_id] = session
            
            all_symptoms = []
            for msg in conversation_history:
                if msg.role == "user":
                    extracted = await qwen_client.extract_symptoms(msg.content)
                    all_symptoms.extend(extracted)
            
            if all_symptoms:
                session.extracted_symptoms = list(set(all_symptoms))
        
        if not session:
            session_id = self.create_session()
            session = self.get_session(session_id)
        
        if session.turn_count >= self.max_turns:
            return {
                "session_id": session_id,
                "message": "You have reached the maximum number of questions. Please generate your report.",
                "conditions": [],
                "follow_up_question": None,
                "red_flags": [],
                "is_complete": True,
                "turn": session.turn_count,
                "max_turns_reached": True
            }
        
        session.conversation.append(Message(role="user", content=message))
        session.turn_count += 1
        
        extracted_symptoms = await qwen_client.extract_symptoms(message)
        
        if extracted_symptoms:
            session.extracted_symptoms.extend(extracted_symptoms)
            session.extracted_symptoms = list(set(session.extracted_symptoms))
        
        all_symptoms = session.extracted_symptoms
        
        matches = find_diseases_by_symptoms(all_symptoms, limit=10)
        
        red_flags = check_red_flags(all_symptoms)
        if red_flags:
            flags_text = ", ".join(red_flags)
            
            warning_message = f"⚠️ **Medical Advisory:** I noticed you mentioned {flags_text}. These symptoms should be discussed with a doctor. If you're experiencing severe pain, difficulty breathing, or confusion, please seek emergency care immediately."
            
            self.update_session(session_id, is_complete=False)
            
            condition_matches = []
            if matches:
                disease_names = [m[0] for m in matches[:5]]
                disease_details = get_diseases_batch(disease_names)
                
                for match in matches[:5]:
                    name, match_count, match_percentage = match
                    detail = next((d for d in disease_details if d['name'] == name), None)
                    
                    if detail:
                        urgency = get_urgency_level(name)
                        condition_matches.append(ConditionMatch(
                            name=name,
                            description=detail.get('description', ''),
                            match_score=float(match_count) * 2.0,
                            symptom_count=match_count,
                            match_percentage=float(match_percentage),
                            urgency=urgency,
                            precautions=detail.get('precautions', []),
                            medications=detail.get('medications', []),
                            diet=detail.get('diet', []),
                            workouts=detail.get('workouts', []),
                            red_flags=detail.get('red_flags', [])
                        ))
            
            if condition_matches:
                top_list = "\n".join([f"- {c.name} ({c.match_percentage}% match)" for c in condition_matches[:3]])
                follow_up = f"{warning_message}\n\nBased on your symptoms, I'm considering these conditions:\n{top_list}\n\n{await qwen_client.generate_follow_up(all_symptoms, [c.dict() for c in condition_matches[:5]])}"
            else:
                follow_up = f"{warning_message}\n\nCould you describe your symptoms in more detail? Please mention any pain, discomfort, or changes you're experiencing."
            
            return {
                "session_id": session_id,
                "message": follow_up,
                "conditions": [c.dict() for c in condition_matches[:5]],
                "follow_up_question": follow_up,
                "red_flags": red_flags,
                "is_complete": False,
                "turn": session.turn_count,
                "max_turns_reached": False
            }
        
        condition_matches = []
        if matches:
            disease_names = [m[0] for m in matches[:5]]
            disease_details = get_diseases_batch(disease_names)
            
            for match in matches[:5]:
                name, match_count, match_percentage = match
                detail = next((d for d in disease_details if d['name'] == name), None)
                
                if detail:
                    urgency = get_urgency_level(name)
                    condition_matches.append(ConditionMatch(
                        name=name,
                        description=detail.get('description', ''),
                        match_score=float(match_count) * 2.0,
                        symptom_count=match_count,
                        match_percentage=float(match_percentage),
                        urgency=urgency,
                        precautions=detail.get('precautions', []),
                        medications=detail.get('medications', []),
                        diet=detail.get('diet', []),
                        workouts=detail.get('workouts', []),
                        red_flags=detail.get('red_flags', [])
                    ))
        
        if condition_matches and condition_matches[0].match_percentage >= 50:
            session.is_complete = True
            self.update_session(session_id, is_complete=True)
            
            top_condition = condition_matches[0]
            
            return {
                "session_id": session_id,
                "message": f"Based on your symptoms, the most likely condition is {top_condition.name} with {top_condition.match_percentage}% confidence. Would you like to generate a report?",
                "conditions": [c.dict() for c in condition_matches[:5]],
                "follow_up_question": None,
                "red_flags": red_flags,
                "is_complete": True,
                "turn": session.turn_count,
                "max_turns_reached": False
            }
        
        if condition_matches:
            top_list = "\n".join([f"- {c.name} ({c.match_percentage}% match)" for c in condition_matches[:3]])
            follow_up = f"Based on your symptoms, I'm considering these conditions:\n{top_list}\n\n{await qwen_client.generate_follow_up(all_symptoms, [c.dict() for c in condition_matches[:5]])}"
        else:
            follow_up = "Could you describe your symptoms in more detail? Please mention any pain, discomfort, or changes you're experiencing."
        
        self.update_session(session_id, is_complete=False)
        
        return {
            "session_id": session_id,
            "message": follow_up,
            "conditions": [c.dict() for c in condition_matches[:5]],
            "follow_up_question": follow_up,
            "red_flags": red_flags,
            "is_complete": False,
            "turn": session.turn_count,
            "max_turns_reached": False
        }
    
    async def get_report_data(self, session_id: str) -> Optional[Dict]:
        session = self.get_session(session_id)
        if not session:
            return None
        
        all_symptoms = session.extracted_symptoms
        matches = find_diseases_by_symptoms(all_symptoms, limit=5)
        
        condition_matches = []
        if matches:
            disease_names = [m[0] for m in matches[:5]]
            disease_details = get_diseases_batch(disease_names)
            
            for i, match in enumerate(matches[:5]):
                name, match_count, match_percentage = match
                detail = next((d for d in disease_details if d['name'] == name), None)
                
                if detail:
                    urgency = get_urgency_level(name)
                    condition_matches.append(ConditionMatch(
                        name=name,
                        description=detail.get('description', ''),
                        match_score=float(match_count) * 2.0,
                        symptom_count=match_count,
                        match_percentage=float(match_percentage),
                        urgency=urgency,
                        precautions=detail.get('precautions', []),
                        medications=detail.get('medications', []),
                        diet=detail.get('diet', []),
                        workouts=detail.get('workouts', []),
                        red_flags=detail.get('red_flags', [])
                    ))
        
        red_flags = check_red_flags(all_symptoms)
        
        try:
            summary = await qwen_client.generate_summary(
                [m.dict() for m in session.conversation],
                [c.dict() for c in condition_matches[:3]]
            )
        except Exception as e:
            print(f"Summary generation failed: {e}")
            summary = "No summary available. Please consult a healthcare provider."
        
        return {
            "session_id": session_id,
            "conversation": [m.dict() for m in session.conversation],
            "symptoms": all_symptoms,
            "conditions": [c.dict() for c in condition_matches],
            "red_flags": red_flags,
            "summary": summary,
            "turn_count": session.turn_count,
            "is_complete": session.is_complete
        }
    
    def cleanup_sessions(self):
        now = datetime.now()
        timeout = config.SESSION_TIMEOUT
        expired = []
        
        for session_id, session in self.sessions.items():
            if (now - session.updated_at).seconds > timeout:
                expired.append(session_id)
        
        for session_id in expired:
            del self.sessions[session_id]
        
        return len(expired)

triage_engine = TriageEngine()