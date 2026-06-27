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
    get_urgency_level,
    find_related_symptoms,
    get_all_symptoms
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
    
    def _should_conclude(self, session: SessionData, matches: List, current_top: Optional[str]) -> tuple[bool, str]:
        """
        Determine if the triage should conclude based on multiple factors.
        Returns (should_conclude, reason_string).
        """
        if not matches:
            return False, ""
        
        top_name, top_count, top_percentage = matches[0]
        
        if not hasattr(session, '_top_condition_history'):
            session._top_condition_history = []
        
        session._top_condition_history.append(top_name)
        
        if len(session._top_condition_history) > 3:
            session._top_condition_history.pop(0)
        
        symptom_count = len(session.extracted_symptoms)
        threshold = max(35, 55 - (session.turn_count * 3))
        
        if top_percentage >= threshold and symptom_count >= 3:
            return True, f"strong_match_{top_percentage:.0f}pct"
        
        if len(session._top_condition_history) >= 2:
            last_two = session._top_condition_history[-2:]
            if last_two[0] == last_two[1] and top_percentage >= 25:
                return True, "stable_diagnosis"
        
        if top_percentage >= 55:
            return True, f"high_confidence_{top_percentage:.0f}pct"
        
        if session.turn_count >= self.max_turns - 2:
            return True, "nearing_max_turns"
        
        if symptom_count >= 6 and session.turn_count >= 5:
            return True, "sufficient_data"
        
        return False, ""
    
    def _build_condition_matches(self, matches: List) -> List[ConditionMatch]:
        """Build ConditionMatch objects from database query results."""
        if not matches:
            return []
        
        disease_names = [m[0] for m in matches[:5]]
        disease_details = get_diseases_batch(disease_names)
        
        condition_matches = []
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
        
        return condition_matches
    
    def _generate_smart_follow_up(self, symptoms: List[str], matches: List) -> str:
        """
        Generate a follow-up question using database-driven symptom differentiation
        instead of always calling the LLM. Falls back to LLM only when needed.
        """
        if not symptoms or not matches:
            return "Could you describe your symptoms in more detail? Please mention any pain, discomfort, or changes you're experiencing."
        
        top_disease_names = [m[0] for m in matches[:3]]
        all_symptoms_db = set(get_all_symptoms())
        current_symptoms = set(symptoms)
        
        differentiating_symptoms = []
        
        for disease_name in top_disease_names:
            try:
                disease_symptoms = get_disease_details(disease_name)
                if disease_symptoms and disease_symptoms.get('symptoms'):
                    for ds in disease_symptoms['symptoms']:
                        ds_lower = ds.strip().lower()
                        if ds_lower and ds_lower not in current_symptoms and ds_lower in all_symptoms_db:
                            differentiating_symptoms.append(ds_lower)
            except Exception:
                continue
        
        for symptom in symptoms[:3]:
            try:
                related = find_related_symptoms(symptom, limit=5)
                for item in related:
                    if isinstance(item, (tuple, list)) and len(item) >= 1:
                        rel_name = str(item[0]).strip().lower()
                        if rel_name and rel_name not in current_symptoms and rel_name not in differentiating_symptoms:
                            differentiating_symptoms.append(rel_name)
            except Exception:
                continue
        
        seen = set()
        unique_diff = []
        for s in differentiating_symptoms:
            if s not in seen:
                seen.add(s)
                unique_diff.append(s)
        unique_diff = unique_diff[:5]
        
        if unique_diff and len(unique_diff) >= 2:
            symptom_options = unique_diff[:3]
            return f"To help narrow things down, are you also experiencing any of these: {', '.join(symptom_options)}?"
        
        if unique_diff:
            return f"One more thing — are you experiencing {unique_diff[0]}?"
        
        try:
            condition_dicts = []
            disease_details_batch = get_diseases_batch(top_disease_names)
            for match in matches[:3]:
                name, count, pct = match
                detail = next((d for d in disease_details_batch if d['name'] == name), None)
                condition_dicts.append({
                    'name': name,
                    'match_percentage': float(pct)
                })
            
            llm_question = qwen_client.generate_follow_up_sync(symptoms, condition_dicts)
            if llm_question and len(llm_question.strip()) > 10:
                return llm_question.strip()
        except Exception:
            pass
        
        return "Could you tell me more about your symptoms? Any other changes you've noticed?"
    
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
            return self._build_conclusion_response(session_id, session, force=True)
        
        session.conversation.append(Message(role="user", content=message))
        session.turn_count += 1
        
        extracted_symptoms = await qwen_client.extract_symptoms(message)
        
        if extracted_symptoms:
            session.extracted_symptoms.extend(extracted_symptoms)
            session.extracted_symptoms = list(set(session.extracted_symptoms))
        
        all_symptoms = session.extracted_symptoms
        
        matches = find_diseases_by_symptoms(all_symptoms, limit=10)
        
        red_flags = check_red_flags(all_symptoms)
        
        condition_matches = self._build_condition_matches(matches)
        
        if red_flags:
            flags_text = ", ".join(red_flags)
            warning_message = (
                f"⚠️ **Medical Advisory:** I noticed you mentioned {flags_text}. "
                "These symptoms should be discussed with a doctor. If you're experiencing "
                "severe pain, difficulty breathing, or confusion, please seek emergency care immediately."
            )
            
            condition_dicts = [c.dict() for c in condition_matches[:5]]
            
            if condition_matches:
                top_list = "\n".join([f"- {c.name} ({c.match_percentage}% match)" for c in condition_matches[:3]])
                
                should_conclude, reason = self._should_conclude(session, matches, condition_matches[0].name if condition_matches else None)
                
                if should_conclude:
                    session.is_complete = True
                    self.update_session(session_id, is_complete=True)
                    return {
                        "session_id": session_id,
                        "message": f"{warning_message}\n\nBased on your symptoms, I'm considering these conditions:\n{top_list}\n\nI recommend consulting a healthcare provider for proper evaluation. Would you like to generate a report?",
                        "conditions": condition_dicts,
                        "follow_up_question": None,
                        "red_flags": red_flags,
                        "is_complete": True,
                        "turn": session.turn_count,
                        "max_turns_reached": False
                    }
                else:
                    follow_up = self._generate_smart_follow_up(all_symptoms, matches)
                    return {
                        "session_id": session_id,
                        "message": f"{warning_message}\n\nBased on your symptoms, I'm considering:\n{top_list}\n\n{follow_up}",
                        "conditions": condition_dicts,
                        "follow_up_question": follow_up,
                        "red_flags": red_flags,
                        "is_complete": False,
                        "turn": session.turn_count,
                        "max_turns_reached": False
                    }
            else:
                return {
                    "session_id": session_id,
                    "message": f"{warning_message}\n\nCould you describe your symptoms in more detail?",
                    "conditions": [],
                    "follow_up_question": "Could you describe your symptoms in more detail?",
                    "red_flags": red_flags,
                    "is_complete": False,
                    "turn": session.turn_count,
                    "max_turns_reached": False
                }
        

        should_conclude, reason = self._should_conclude(session, matches, condition_matches[0].name if condition_matches else None)
        
        if should_conclude and condition_matches:
            return self._build_conclusion_response(session_id, session)
        
        if condition_matches:
            top_list = "\n".join([f"- {c.name} ({c.match_percentage}% match)" for c in condition_matches[:3]])
            follow_up = self._generate_smart_follow_up(all_symptoms, matches)
            message_text = f"Based on your symptoms, I'm considering these conditions:\n{top_list}\n\n{follow_up}"
        else:
            follow_up = "Could you describe your symptoms in more detail? Please mention any pain, discomfort, or changes you're experiencing."
            message_text = follow_up
        
        self.update_session(session_id, is_complete=False)
        
        return {
            "session_id": session_id,
            "message": message_text,
            "conditions": [c.dict() for c in condition_matches[:5]],
            "follow_up_question": follow_up,
            "red_flags": red_flags,
            "is_complete": False,
            "turn": session.turn_count,
            "max_turns_reached": False
        }
    
    def _build_conclusion_response(self, session_id: str, session: SessionData, force: bool = False) -> Dict[str, Any]:
        """Build the final conclusion response."""
        all_symptoms = session.extracted_symptoms
        matches = find_diseases_by_symptoms(all_symptoms, limit=5)
        condition_matches = self._build_condition_matches(matches)
        red_flags = check_red_flags(all_symptoms)
        
        session.is_complete = True
        self.update_session(session_id, is_complete=True)
        
        if condition_matches:
            top = condition_matches[0]
            if force:
                prefix = "I've gathered enough information. "
            else:
                prefix = ""
            
            return {
                "session_id": session_id,
                "message": f"{prefix}Based on your symptoms, the most likely condition is **{top.name}** with {top.match_percentage}% confidence. Would you like to generate a report?",
                "conditions": [c.dict() for c in condition_matches[:5]],
                "follow_up_question": None,
                "red_flags": red_flags,
                "is_complete": True,
                "turn": session.turn_count,
                "max_turns_reached": force
            }
        else:
            return {
                "session_id": session_id,
                "message": "I wasn't able to identify a specific condition based on the symptoms provided. I recommend consulting a healthcare provider for a proper evaluation. Would you like to generate a report with what we've discussed?",
                "conditions": [],
                "follow_up_question": None,
                "red_flags": red_flags,
                "is_complete": True,
                "turn": session.turn_count,
                "max_turns_reached": force
            }
    
    async def get_report_data(self, session_id: str) -> Optional[Dict]:
        session = self.get_session(session_id)
        if not session:
            return None
        
        all_symptoms = session.extracted_symptoms
        matches = find_diseases_by_symptoms(all_symptoms, limit=5)
        
        condition_matches = self._build_condition_matches(matches)
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