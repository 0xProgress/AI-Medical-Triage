import httpx
import json
from typing import List, Dict, Any, Optional
from backend.config import config

class QwenClient:
    def __init__(self):
        self.api_url = config.HF_API_URL
        self.api_token = config.HF_API_TOKEN
        self.max_tokens = config.MAX_TOKENS
        self.temperature = config.TEMPERATURE
        self.model = config.HF_MODEL
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    async def generate(self, messages: List[Dict[str, str]], temperature: float = None) -> str:
        """Generate response with optional temperature override"""
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code != 200:
                print(f"Error Response: {response.text}")
                response.raise_for_status()
            
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                print(f"Unexpected response: {result}")
                return ""
    
    async def extract_symptoms(self, user_message: str) -> List[str]:
        """
        Extract symptoms with STRICT anti-hallucination measures.
        Only extracts symptoms EXPLICITLY mentioned by the user.
        """
        prompt = f"""EXTRACT SYMPTOMS - STRICT RULES:

ONLY extract symptoms that are EXPLICITLY stated in the user's message.
DO NOT add, infer, or assume ANY symptoms.
DO NOT include body parts unless mentioned as problematic.
DO NOT infer "head injury" from "I fell" or "I tripped".
DO NOT infer "concussion" from any context.
DO NOT add common related symptoms.

User message: "{user_message}"

List ONLY the symptoms explicitly mentioned. If none, say "NONE".

Symptoms (comma-separated):"""

        messages = [
            {
                "role": "system", 
                "content": "You are a STRICT medical symptom extractor. NEVER infer or assume symptoms. ONLY extract what is explicitly stated. Be extremely conservative."
            },
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.generate(messages, temperature=0.1)  # Lower temperature for more precise extraction
            
            if "NONE" in response.upper():
                return []
            
            symptoms = [s.strip().lower() for s in response.split(",") if s.strip()]
            
            # Validate symptoms against the original message
            validated = self._validate_symptoms(symptoms, user_message)
            
            if len(validated) < len(symptoms):
                rejected = set(symptoms) - set(validated)
                print(f"HALLUCINATION DETECTED: Rejected symptoms: {rejected}")
            
            return validated
            
        except Exception as e:
            print(f"Symptom extraction failed: {e}")
            return []
    
    def _validate_symptoms(self, extracted: List[str], original_message: str) -> List[str]:
        """
        Validate that extracted symptoms appear in the original message.
        Prevents AI hallucination of symptoms.
        """
        validated = []
        message_lower = original_message.lower()
        message_words = set(message_lower.split())
        
        # Symptoms that should NEVER be inferred
        NEVER_INFER = [
            "head injury", "concussion", "brain damage", "skull fracture",
            "loss of consciousness", "seizure", "stroke", "heart attack",
            "internal bleeding", "organ failure", "paralysis"
        ]
        
        for symptom in extracted:
            symptom_lower = symptom.lower()
            
            # Skip symptoms that should never be inferred
            if symptom_lower in NEVER_INFER and symptom_lower not in message_lower:
                continue
            
            # Check if symptom is directly in message
            if symptom_lower in message_lower:
                validated.append(symptom)
                continue
            
            # Check if key words of symptom appear in message
            symptom_words = symptom_lower.split()
            significant_words = [w for w in symptom_words if len(w) > 3]
            
            if significant_words:
                # If all significant words appear in message, accept it
                if all(word in message_words for word in significant_words):
                    validated.append(symptom)
                    continue
                
                # If at least half the significant words appear, accept it
                matching_words = sum(1 for w in significant_words if w in message_words)
                if matching_words >= len(significant_words) / 2:
                    validated.append(symptom)
                    continue
        
        return validated
    
    async def generate_follow_up(self, symptoms: List[str], current_conditions: List[Dict]) -> str:
        """
        Generate a follow-up question that doesn't lead or hallucinate symptoms.
        """
        if not current_conditions:
            return "Could you describe your symptoms in more detail?"
        
        conditions_text = "\n".join([
            f"- {c.get('name', 'Unknown')}: {c.get('match_percentage', 0)}% match"
            for c in current_conditions[:3]
        ])
        
        prompt = f"""GENERATE ONE FOLLOW-UP QUESTION:

Reported symptoms: {', '.join(symptoms) if symptoms else 'none'}

Potential conditions being considered:
{conditions_text}

RULES FOR THE QUESTION:
- Ask about symptom CHARACTERISTICS (onset, severity, duration, triggers)
- Ask about TIMING (when did it start, how long does it last)
- Ask about RELIEVING/AGGRAVATING factors
- NEVER suggest symptoms the user hasn't mentioned
- NEVER ask "Do you also have X?" where X is a new symptom
- NEVER assume injuries (e.g., don't ask about head injury if user just said they fell)

GOOD examples:
- "When did your symptoms start?"
- "On a scale of 1-10, how severe is your pain?"
- "Does anything make your symptoms better or worse?"

BAD examples (DO NOT USE):
- "Did you hit your head when you fell?"
- "Are you also experiencing dizziness?"
- "Do you have a fever as well?"

Question:"""

        messages = [
            {
                "role": "system", 
                "content": "You are a medical triage assistant. Ask NEUTRAL, NON-LEADING questions about symptom characteristics. NEVER suggest new symptoms."
            },
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.generate(messages, temperature=0.3)
            response = response.strip()
            
            # Filter out obviously bad questions
            bad_patterns = [
                "did you hit", "have you hit", "did you fall on",
                "did you also", "are you also", "do you also have",
                "are you experiencing", "have you been experiencing"
            ]
            
            for pattern in bad_patterns:
                if pattern in response.lower():
                    # Replace with neutral question
                    return "Could you describe when your symptoms started and what makes them better or worse?"
            
            return response
            
        except Exception as e:
            print(f"Follow-up generation failed: {e}")
            return "Could you tell me more about your symptoms?"
    
    def generate_follow_up_sync(self, symptoms: List[str], condition_dicts: List[Dict]) -> str:
        """Synchronous version of generate_follow_up"""
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, 
                        self.generate_follow_up(symptoms, condition_dicts)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.generate_follow_up(symptoms, condition_dicts)
                )
        except Exception as e:
            print(f"Sync follow-up failed: {e}")
            return "Could you describe your symptoms in more detail?"
    
    async def rank_conditions(self, symptoms: List[str], matches: List[Dict]) -> List[Dict]:
        """Rank conditions by likelihood based on reported symptoms"""
        if not matches:
            return []
        
        matches_text = "\n".join([
            f"- {m.get('name', 'Unknown')}: {m.get('match_percentage', 0)}% match"
            for m in matches[:10]
        ])
        
        prompt = f"""RANK CONDITIONS BY LIKELIHOOD:

Reported symptoms: {', '.join(symptoms)}

Conditions to rank:
{matches_text}

Rank based ONLY on the reported symptoms. Return condition names in order of likelihood, comma-separated.

Ranking:"""
        
        messages = [
            {"role": "system", "content": "Rank medical conditions based on symptom matches. Be objective and evidence-based."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.generate(messages, temperature=0.1)
            ranked_names = [name.strip() for name in response.split(",") if name.strip()]
            
            # Reorder matches based on ranking
            ranked_matches = []
            for name in ranked_names:
                for match in matches:
                    if match.get('name', '').lower() == name.lower():
                        ranked_matches.append(match)
                        break
            
            # Add any remaining matches
            for match in matches:
                if match not in ranked_matches:
                    ranked_matches.append(match)
            
            return ranked_matches
            
        except Exception as e:
            print(f"Ranking failed: {e}")
            return matches
    
    async def check_red_flags(self, symptoms: List[str]) -> List[str]:
        """
        Check for red flag symptoms in the extracted symptoms list.
        Only flags symptoms actually present in the list.
        """
        red_flag_symptoms = [
            "chest pain",
            "difficulty breathing",
            "shortness of breath",
            "severe bleeding",
            "loss of consciousness",
            "seizure",
            "stroke symptoms",
            "severe allergic reaction",
            "suicidal thoughts",
            "severe headache",
            "confusion",
            "fainting",
            "blood in vomit",
            "blood in stool",
            "severe abdominal pain"
        ]
        
        detected = []
        for symptom in symptoms:
            symptom_lower = symptom.lower()
            for flag in red_flag_symptoms:
                if flag in symptom_lower or symptom_lower in flag:
                    detected.append(flag)
        
        return list(set(detected))
    
    async def generate_summary(self, conversation: List[Dict], conditions: List[Dict]) -> str:
        """
        Generate a summary that ONLY references actually reported symptoms.
        """
        # Extract only user messages and their symptoms
        user_messages = [msg.get('content', '') for msg in conversation if msg.get('role') == 'user']
        reported_content = ' '.join(user_messages)
        
        conditions_text = "\n".join([
            f"- {c.get('name', 'Unknown')} ({c.get('match_percentage', 0)}% match): {c.get('description', '')[:150]}"
            for c in conditions[:3]
        ]) if conditions else "No conditions identified"
        
        prompt = f"""GENERATE A MEDICAL TRIAGE SUMMARY:

STRICT RULES:
1. ONLY reference symptoms EXPLICITLY mentioned by the user
2. DO NOT add, infer, or assume any symptoms not stated
3. If the user said "I fell and hurt my knee", DO NOT mention "head injury"
4. Base your summary ONLY on the reported information below

User's reported information:
{reported_content}

Top matching conditions:
{conditions_text}

Generate a concise summary (3-4 sentences) that includes:
1. What symptoms the user ACTUALLY reported
2. The most likely condition(s)
3. General recommendation to consult a healthcare provider

Summary:"""

        messages = [
            {
                "role": "system", 
                "content": "You are a conservative medical summarizer. ONLY use information explicitly provided. NEVER add or assume symptoms. Be factual and cautious."
            },
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.generate(messages, temperature=0.2)
            
            # Validate summary doesn't contain hallucinated symptoms
            summary_lower = response.lower()
            
            # Check for common hallucinations
            hallucination_checks = [
                ("head injury", ["fell", "fall", "slipped", "tripped"]),
                ("concussion", ["fell", "fall", "hit"]),
                ("unconscious", ["fell", "fall"]),
            ]
            
            for term, triggers in hallucination_checks:
                if term in summary_lower:
                    # Check if any trigger words are in the original message
                    trigger_found = any(t in reported_content.lower() for t in triggers)
                    term_mentioned = term in reported_content.lower()
                    
                    if trigger_found and not term_mentioned:
                        print(f"HALLUCINATION IN SUMMARY: '{term}' was not in original message")
                        # Replace the summary with a safe version
                        return self._generate_safe_summary(conditions, reported_content)
            
            return response.strip()
            
        except Exception as e:
            print(f"Summary generation failed: {e}")
            return self._generate_safe_summary(conditions, reported_content)
    
    def _generate_safe_summary(self, conditions: List[Dict], reported_content: str) -> str:
        """Generate a safe summary without AI to prevent hallucination"""
        if not conditions:
            return "Based on the symptoms you reported, no specific condition could be identified. Please consult a healthcare provider for a proper evaluation."
        
        top_condition = conditions[0]
        condition_name = top_condition.get('name', 'Unknown')
        
        return (
            f"Based on the symptoms you reported, the most likely condition is {condition_name}. "
            "Please consult a healthcare provider for a proper diagnosis and treatment plan. "
            "This is not a medical diagnosis and should not replace professional medical advice."
        )

qwen_client = QwenClient()