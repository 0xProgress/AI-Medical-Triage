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
    
    async def generate(self, messages: List[Dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
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
        messages = [
            {"role": "system", "content": "You are a medical symptom extractor. Extract symptoms from user messages. Return only a comma-separated list of symptoms."},
            {"role": "user", "content": f"Extract medical symptoms from this text: {user_message}"}
        ]
        
        response = await self.generate(messages)
        symptoms = [s.strip().lower() for s in response.split(",") if s.strip()]
        return symptoms
    
    async def generate_follow_up(self, symptoms: List[str], current_conditions: List[Dict]) -> str:
        conditions_text = "\n".join([
            f"- {c.get('name', 'Unknown')}: {c.get('match_percentage', 0)}% match"
            for c in current_conditions[:5]
        ])
        
        prompt = f"""Based on the following symptoms and potential conditions, ask ONE clarifying question to help differentiate between the conditions.

    Symptoms: {', '.join(symptoms)}

    Potential Conditions:
    {conditions_text}

    Ask a specific yes/no question that would help distinguish between these conditions. For example, if Strep throat and Esophagitis are both possible, ask about fever, white patches, or acid reflux.

    Clarifying Question:"""
        
        messages = [
            {"role": "system", "content": "You are a medical triage assistant. Ask clarifying questions to narrow down conditions and differentiate between similar diagnoses."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.generate(messages)
        return response.strip()
    
    async def rank_conditions(self, symptoms: List[str], matches: List[Dict]) -> List[Dict]:
        if not matches:
            return []
        
        matches_text = "\n".join([
            f"- {m.get('name', 'Unknown')}: {m.get('match_percentage', 0)}% match"
            for m in matches[:10]
        ])
        
        messages = [
            {"role": "system", "content": "You are a medical triage assistant. Rank conditions by likelihood."},
            {"role": "user", "content": f"""Rank the following potential conditions by likelihood based on the reported symptoms.

Symptoms: {', '.join(symptoms)}

Potential Conditions:
{matches_text}

Return only the condition names in order of likelihood, separated by commas.

Ranking:"""}
        ]
        
        response = await self.generate(messages)
        ranked_names = [name.strip() for name in response.split(",") if name.strip()]
        
        ranked_matches = []
        for name in ranked_names:
            for match in matches:
                if match.get('name', '').lower() == name.lower():
                    ranked_matches.append(match)
                    break
        
        for match in matches:
            if match not in ranked_matches:
                ranked_matches.append(match)
        
        return ranked_matches
    
    async def check_red_flags(self, symptoms: List[str]) -> List[str]:
        red_flag_symptoms = [
            "chest pain",
            "difficulty breathing",
            "shortness of breath",
            "severe bleeding",
            "loss of consciousness",
            "seizure",
            "stroke",
            "severe allergic reaction",
            "suicidal",
            "head injury",
            "severe headache",
            "confusion",
            "fainting"
        ]
        
        detected = []
        for symptom in symptoms:
            for flag in red_flag_symptoms:
                if flag in symptom or symptom in flag:
                    detected.append(flag)
        
        return list(set(detected))
    
    async def generate_summary(self, conversation: List[Dict], conditions: List[Dict]) -> str:
        conditions_text = "\n".join([
            f"- {c.get('name', 'Unknown')}: {c.get('description', 'No description available')[:100]}..."
            for c in conditions[:3]
        ])
        
        messages = [
            {"role": "system", "content": "You are a medical triage assistant. Generate patient summaries."},
            {"role": "user", "content": f"""Generate a concise medical summary based on the conversation and top conditions.

Top Conditions:
{conditions_text}

Provide a brief summary that includes:
1. The main symptoms reported
2. The most likely condition(s)
3. Recommended next steps

Summary:"""}
        ]
        
        response = await self.generate(messages)
        return response.strip()

qwen_client = QwenClient()