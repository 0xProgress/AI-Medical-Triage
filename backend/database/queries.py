import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from backend.config import config
import asyncio

DB_PATH = config.SQLITE_DB_PATH

RED_FLAG_SYMPTOMS = [
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
    "fainting",
    "blood in vomit",
    "blood in stool",
    "severe abdominal pain",
]

SYMPTOM_SYNONYMS = {
    "sore throat": ["throat pain", "painful throat", "pharyngeal pain", "scratchy throat", "raw throat", "throat irritation"],
    "headache": ["head pain", "migraine", "head pressure", "tension headache", "throbbing head"],
    "fever": ["high temperature", "pyrexia", "high fever", "low grade fever", "temperature", "feeling hot", "chills"],
    "cough": ["coughing", "dry cough", "wet cough", "persistent cough", "barking cough", "hacking cough"],
    "chest pain": ["chest tightness", "chest pressure", "chest discomfort", "chest ache", "chest heaviness"],
    "difficulty in swallowing": ["difficulty swallowing", "pain on swallowing", "painful swallowing", "trouble swallowing", "pain when swallowing", "hurts to swallow", "swallowing pain", "painful to swallow", "hard to swallow", "can't swallow", "cannot swallow", "struggling to swallow"],
    "shortness of breath": ["difficulty breathing", "breathing difficulty", "trouble breathing", "hard to breathe", "can't breathe", "breathlessness", "breathless", "out of breath", "gasping"],
    "nausea": ["feeling sick", "queasy", "want to vomit", "vomiting", "sick to stomach", "stomach upset", "nauseous"],
    "fatigue": ["tired", "exhausted", "low energy", "lack of energy", "feeling tired", "worn out", "drained", "sleepy"],
    "abdominal pain": ["stomach pain", "belly pain", "stomach ache", "tummy pain", "gut pain", "abdominal cramps", "cramping"],
    "dizziness": ["lightheaded", "vertigo", "feeling faint", "woozy", "unsteady", "loss of balance", "spinning"],
    "nasal congestion": ["stuffy nose", "blocked nose", "runny nose", "sinus congestion", "stuffed up", "nose blocked", "sniffles"],
}

def get_connection():
    return sqlite3.connect(str(DB_PATH))

def normalize_symptom(symptom: str) -> str:
    """Normalize using synonym map first, then AI for unknown symptoms."""
    symptom = symptom.strip().lower()
    
    for main, synonyms in SYMPTOM_SYNONYMS.items():
        if symptom == main or symptom in synonyms:
            return main
        if main in symptom or symptom in main:
            return main
        for syn in synonyms:
            if syn in symptom or symptom in syn:
                return main
    
    try:
        from backend.models.qwen_client import qwen_client
        
        prompt = f'''Map this user-described symptom to the closest standard medical symptom name.

User symptom: "{symptom}"

Return ONLY the standardized name, nothing else. If unsure, return original.'''
        
        messages = [
            {"role": "system", "content": "Map user symptoms to standard medical terms. Return ONLY the term."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, qwen_client.generate(messages, temperature=0.1))
                response = future.result(timeout=3)
        else:
            response = loop.run_until_complete(asyncio.wait_for(qwen_client.generate(messages, temperature=0.1), timeout=3))
        
        if response and response.strip():
            return response.strip().lower()
    except Exception:
        pass
    
    return symptom

def find_diseases_by_symptoms(
    symptoms: List[str], 
    limit: int = 10,
    exclude_symptoms: List[str] = None
) -> List[Tuple[str, int, float]]:
    """Find diseases matching given symptoms with accurate scoring."""
    if not symptoms:
        return []
    
    exclude_symptoms = exclude_symptoms or []
    conn = get_connection()
    cursor = conn.cursor()
    
    normalized_symptoms = []
    for s in symptoms:
        if s and s.strip():
            normalized = normalize_symptom(s)
            normalized_symptoms.append(normalized.lower().strip())
    
    normalized_symptoms = list(set([s for s in normalized_symptoms if s]))
    
    if not normalized_symptoms:
        conn.close()
        return []
    
    cursor.execute("SELECT name, symptoms, symptom_count FROM diseases")
    all_diseases = cursor.fetchall()
    
    scored_results = []
    
    for disease_name, symptoms_json, total_symptoms in all_diseases:
        try:
            disease_symptoms = json.loads(symptoms_json) if symptoms_json else []
        except:
            disease_symptoms = []
        
        if not disease_symptoms:
            continue
        
        disease_symptoms_lower = [ds.lower().strip() for ds in disease_symptoms]
        total_score = 0.0
        
        for user_symptom in normalized_symptoms:
            if user_symptom in disease_symptoms_lower:
                total_score += 1.0
                continue
            
            matched = False
            for ds in disease_symptoms_lower:
                if user_symptom in ds or ds in user_symptom:
                    total_score += 0.8
                    matched = True
                    break
            
            if matched:
                continue
            
            user_words = set(user_symptom.split())
            for ds in disease_symptoms_lower:
                ds_words = set(ds.split())
                common = user_words & ds_words
                if len(common) >= 1 and len(common) / max(len(user_words), len(ds_words)) >= 0.5:
                    total_score += 0.6
                    break
        
        if total_score > 0:
            match_pct = round((total_score / len(normalized_symptoms)) * 100, 2)
            scored_results.append((disease_name, total_score, match_pct))
    
    scored_results.sort(key=lambda x: (x[1], x[2]), reverse=True)
    conn.close()
    return [(name, round(score, 1), pct) for name, score, pct in scored_results[:limit]]

def check_red_flags(symptoms: List[str]) -> List[str]:
    """Check for red flag symptoms in the extracted symptoms list."""
    if not symptoms:
        return []
    
    from backend.models.qwen_client import qwen_client
    
    symptom_text = ", ".join(symptoms)
    
    prompt = f"""Analyze these symptoms and determine if any are TRUE medical red flags requiring immediate emergency care. BE CONSERVATIVE.

Symptoms: {symptom_text}

A symptom is a red flag ONLY if it is:
- Chest pain or pressure (not mild discomfort)
- Difficulty breathing or severe shortness of breath
- Sudden severe headache (not regular headache)
- Loss of consciousness or fainting
- Seizures
- Severe bleeding
- Sudden numbness or weakness on one side
- Confusion or difficulty speaking
- Severe allergic reaction with swelling

DO NOT flag: regular headache, mild dizziness, tiredness, cold/flu symptoms, sore throat, mild fever, normal cough, minor aches.

Return ONLY the symptoms that are TRUE red flags, separated by commas. If none, return "NONE".

Red flags detected:"""
    
    messages = [
        {"role": "system", "content": "You are a conservative medical triage assistant. Only flag truly life-threatening emergencies."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, qwen_client.generate(messages))
                response = future.result()
        else:
            response = loop.run_until_complete(qwen_client.generate(messages))
            loop.close()
        
        if "NONE" in response.upper():
            return []
        
        return [f.strip().lower() for f in response.split(",") if f.strip()]
        
    except Exception as e:
        print(f"AI red flag check failed: {e}")
        return _fallback_red_flag_check(symptoms)

def _fallback_red_flag_check(symptoms: List[str]) -> List[str]:
    """Fallback red flag check."""
    serious = ["chest pain", "difficulty breathing", "shortness of breath"]
    detected = []
    for symptom in symptoms:
        symptom_lower = symptom.lower()
        if "severe" in symptom_lower or "sharp" in symptom_lower:
            for flag in serious:
                if flag in symptom_lower:
                    detected.append(flag)
        elif "shortness of breath" in symptom_lower or "difficulty breathing" in symptom_lower:
            detected.append("difficulty breathing")
        elif "chest pain" in symptom_lower:
            detected.append("chest pain")
    return list(set(detected))

def get_disease_details(disease_name: str) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, description, symptoms, precautions, medications, diet, workouts, symptom_count FROM diseases WHERE name = ?", (disease_name,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        'name': row[0], 'description': row[1] or '',
        'symptoms': json.loads(row[2]) if row[2] else [],
        'precautions': json.loads(row[3]) if row[3] else [],
        'medications': json.loads(row[4]) if row[4] else [],
        'diet': json.loads(row[5]) if row[5] else [],
        'workouts': json.loads(row[6]) if row[6] else [],
        'symptom_count': row[7]
    }

def get_diseases_batch(disease_names: List[str]) -> List[Dict]:
    if not disease_names:
        return []
    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ','.join('?' * len(disease_names))
    cursor.execute(f"SELECT name, description, symptoms, precautions, medications, diet, workouts, symptom_count FROM diseases WHERE name IN ({placeholders})", disease_names)
    rows = cursor.fetchall()
    conn.close()
    return [{
        'name': r[0], 'description': r[1] or '',
        'symptoms': json.loads(r[2]) if r[2] else [],
        'precautions': json.loads(r[3]) if r[3] else [],
        'medications': json.loads(r[4]) if r[4] else [],
        'diet': json.loads(r[5]) if r[5] else [],
        'workouts': json.loads(r[6]) if r[6] else [],
        'symptom_count': r[7]
    } for r in rows]

def search_diseases(query: str, limit: int = 10) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, description, symptom_count FROM diseases WHERE name LIKE ? OR description LIKE ? ORDER BY name LIMIT ?", (f'%{query}%', f'%{query}%', limit))
    results = [{'name': r[0], 'description': r[1], 'symptom_count': r[2]} for r in cursor.fetchall()]
    conn.close()
    return results

def get_all_symptoms() -> List[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT symptoms FROM diseases")
    all_symptoms = set()
    for (symptoms_json,) in cursor.fetchall():
        try:
            all_symptoms.update(json.loads(symptoms_json) if symptoms_json else [])
        except:
            pass
    conn.close()
    return sorted(list(all_symptoms))

def get_disease_count() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM diseases")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_symptoms_for_disease(disease_name: str) -> List[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT symptoms FROM diseases WHERE name = ?", (disease_name,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        try:
            return json.loads(row[0])
        except:
            return []
    return []

def find_related_symptoms(symptom: str, limit: int = 10) -> List[Tuple[str, float]]:
    conn = get_connection()
    cursor = conn.cursor()
    symptom = normalize_symptom(symptom)
    cursor.execute("SELECT symptoms FROM diseases WHERE symptoms LIKE ?", (f'%{symptom}%',))
    rows = cursor.fetchall()
    co_occurrence_count = {}
    total = len(rows)
    for (symptoms_json,) in rows:
        try:
            for ds in json.loads(symptoms_json) if symptoms_json else []:
                if ds.lower() != symptom.lower():
                    co_occurrence_count[ds] = co_occurrence_count.get(ds, 0) + 1
        except:
            pass
    results = [(sym, round(count * 100.0 / total, 2)) for sym, count in co_occurrence_count.items() if total > 0]
    results.sort(key=lambda x: x[1], reverse=True)
    conn.close()
    return results[:limit]

def get_urgency_level(disease_name: str) -> str:
    urgency_keywords = {
        "high": ["emergency", "acute", "severe", "life-threatening", "critical", "urgent", "immediate"],
        "medium": ["moderate", "requires", "treatment", "medical", "consult"],
        "low": ["mild", "benign", "self-limiting", "minor"]
    }
    details = get_disease_details(disease_name)
    if not details:
        return "medium"
    text = (details.get('description', '') + ' ' + ' '.join(details.get('precautions', []))).lower()
    for level, keywords in urgency_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return level
    return "medium"

def get_disease_by_symptom_count(min_symptoms: int = None, max_symptoms: int = None) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT name, description, symptom_count FROM diseases WHERE 1=1"
    params = []
    if min_symptoms is not None:
        query += " AND symptom_count >= ?"
        params.append(min_symptoms)
    if max_symptoms is not None:
        query += " AND symptom_count <= ?"
        params.append(max_symptoms)
    query += " ORDER BY symptom_count DESC"
    cursor.execute(query, params)
    results = [{'name': r[0], 'description': r[1], 'symptom_count': r[2]} for r in cursor.fetchall()]
    conn.close()
    return results