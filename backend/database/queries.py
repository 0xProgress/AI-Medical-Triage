import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from backend.config import config
import re
import asyncio

DB_PATH = config.SQLITE_DB_PATH

SYMPTOM_WEIGHTS = {
    "chest pain": 2.0,
    "difficulty breathing": 2.0,
    "loss of consciousness": 3.0,
    "severe headache": 1.5,
    "fever": 1.2,
    "cough": 1.0,
    "fatigue": 0.8,
}

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
    "sore throat": [
        "throat pain", "painful throat", "pharyngeal pain", 
        "scratchy throat", "raw throat", "throat irritation"
    ],
    "headache": [
        "head pain", "migraine", "head pressure", 
        "tension headache", "throbbing head"
    ],
    "fever": [
        "high temperature", "pyrexia", "high fever", 
        "low grade fever", "temperature", "feeling hot", "chills"
    ],
    "cough": [
        "coughing", "dry cough", "wet cough", "persistent cough", 
        "barking cough", "hacking cough"
    ],
    "chest pain": [
        "chest tightness", "chest pressure", "chest discomfort",
        "chest ache", "chest heaviness"
    ],
    "difficulty in swallowing": [
        "difficulty swallowing", "pain on swallowing", "painful swallowing",
        "trouble swallowing", "pain when swallowing", "hurts to swallow",
        "swallowing pain", "painful to swallow", "hard to swallow",
        "can't swallow", "cannot swallow", "struggling to swallow"
    ],
    "shortness of breath": [
        "difficulty breathing", "breathing difficulty", "trouble breathing",
        "hard to breathe", "can't breathe", "breathlessness",
        "breathless", "out of breath", "gasping"
    ],
    "nausea": [
        "feeling sick", "queasy", "want to vomit", "vomiting",
        "sick to stomach", "stomach upset", "nauseous"
    ],
    "fatigue": [
        "tired", "exhausted", "low energy", "lack of energy",
        "feeling tired", "worn out", "drained", "sleepy"
    ],
    "abdominal pain": [
        "stomach pain", "belly pain", "stomach ache", "tummy pain",
        "gut pain", "abdominal cramps", "cramping"
    ],
    "dizziness": [
        "lightheaded", "vertigo", "feeling faint", "woozy",
        "unsteady", "loss of balance", "spinning"
    ],
    "nasal congestion": [
        "stuffy nose", "blocked nose", "runny nose", "sinus congestion",
        "stuffed up", "nose blocked", "sniffles"
    ],
}

def get_connection():
    return sqlite3.connect(str(DB_PATH))

def normalize_symptom(symptom: str) -> str:
    """
    Normalize a symptom string to match database symptom names.
    Handles exact matches, synonyms, partial matches, and fuzzy matching.
    """
    symptom = symptom.strip().lower()
    
    stop_words = ["the", "a", "an", "my", "me", "i", "have", "has", "and", "or", "but", "for", "on", "at", "to", "with"]
    words = [w for w in symptom.split() if w not in stop_words]
    
    for main, synonyms in SYMPTOM_SYNONYMS.items():
        if symptom == main:
            return main
        if symptom in synonyms:
            return main
    
    for main, synonyms in SYMPTOM_SYNONYMS.items():
        main_words = main.split()
        for syn in synonyms:
            syn_words = syn.split()
            for word in words:
                if word in main_words or word in syn_words:
                    return main
                for sw in syn_words:
                    if sw in symptom or symptom in sw:
                        return main
    
    for main, synonyms in SYMPTOM_SYNONYMS.items():
        if main in symptom or symptom in main:
            return main
        for syn in synonyms:
            if syn in symptom or symptom in syn:
                return main
    
    suffixes = ["ing", "ed", "s", "es", "ly", "ness", "tion", "ment", "ive", "ative", "ible", "able"]
    for suffix in suffixes:
        if symptom.endswith(suffix):
            stem = symptom[:-len(suffix)]
            for main, synonyms in SYMPTOM_SYNONYMS.items():
                if stem == main or stem in synonyms:
                    return main
                for syn in synonyms:
                    if syn.startswith(stem) or stem in syn:
                        return main
    
    return symptom

def find_diseases_by_symptoms(
    symptoms: List[str], 
    limit: int = 10,
    exclude_symptoms: List[str] = None
) -> List[Tuple[str, int, float]]:
    """
    Find diseases matching given symptoms using the single table structure.
    """
    if not symptoms:
        return []
    
    exclude_symptoms = exclude_symptoms or []
    conn = get_connection()
    cursor = conn.cursor()
    
    normalized_symptoms = []
    for s in symptoms:
        if s and s.strip():
            normalized = normalize_symptom(s)
            normalized_symptoms.append(normalized)
    
    normalized_symptoms = list(set([s for s in normalized_symptoms if s]))
    
    if not normalized_symptoms:
        conn.close()
        return []
    
    # Build dynamic query to search in symptoms JSON
    like_conditions = []
    params = []
    
    for symptom in normalized_symptoms:
        # Search for symptom in the symptoms JSON field
        like_conditions.append("d.symptoms LIKE ?")
        params.append(f'%{symptom}%')
    
    where_clause = " OR ".join(like_conditions)
    
    query = f"""
    SELECT 
        d.name,
        d.symptoms,
        d.symptom_count
    FROM diseases d
    WHERE {where_clause}
    ORDER BY d.symptom_count DESC
    LIMIT ?
    """
    
    params.append(limit * 2)  # Get more results for accurate scoring
    cursor.execute(query, params)
    results = cursor.fetchall()
    
    # Calculate match scores
    scored_results = []
    for name, symptoms_json, total_symptoms in results:
        try:
            disease_symptoms = json.loads(symptoms_json) if symptoms_json else []
        except:
            disease_symptoms = []
        
        # Count matching symptoms
        matches = 0
        for symptom in normalized_symptoms:
            if any(symptom in ds.lower() or ds.lower() in symptom 
                   for ds in disease_symptoms):
                matches += 1
        
        if matches > 0:
            match_percentage = round(matches * 100.0 / total_symptoms, 2) if total_symptoms > 0 else 0
            scored_results.append((name, matches, match_percentage))
    
    # Sort by matches desc, then by percentage desc
    scored_results.sort(key=lambda x: (x[1], x[2]), reverse=True)
    
    conn.close()
    return scored_results[:limit]

def check_red_flags(symptoms: List[str]) -> List[str]:
    """Uses AI to determine if symptoms are TRUE medical red flags."""
    if not symptoms:
        return []
    
    from backend.models.qwen_client import qwen_client
    
    symptom_text = ", ".join(symptoms)
    
    prompt = f"""Analyze these symptoms and determine if any are TRUE medical red flags requiring immediate emergency care. BE CONSERVATIVE. Only flag truly life-threatening symptoms.

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

DO NOT flag these as red flags:
- Regular headache
- Mild dizziness
- Feeling tired or cold
- Cold or flu symptoms
- Sore throat
- Mild fever (under 101°F)
- Normal cough
- Minor aches

Return ONLY the symptoms that are TRUE red flags, separated by commas.
If none are red flags, return "NONE".

Red flags detected:"""
    
    messages = [
        {"role": "system", "content": "You are a conservative medical triage assistant. Only flag truly life-threatening emergencies. Never flag common symptoms as red flags."},
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
        
        flags = [f.strip().lower() for f in response.split(",") if f.strip()]
        return flags
        
    except Exception as e:
        print(f"AI red flag check failed: {e}")
        return _fallback_red_flag_check(symptoms)


def _fallback_red_flag_check(symptoms: List[str]) -> List[str]:
    """Fallback: only flag symptoms with severity modifiers."""
    serious_symptoms = ["chest pain", "difficulty breathing", "shortness of breath"]
    detected = []
    
    for symptom in symptoms:
        symptom_lower = symptom.lower()
        
        if "severe" in symptom_lower or "sharp" in symptom_lower:
            for flag in serious_symptoms:
                if flag in symptom_lower:
                    detected.append(flag)
        elif "shortness of breath" in symptom_lower or "difficulty breathing" in symptom_lower:
            detected.append("difficulty breathing")
        elif "chest pain" in symptom_lower:
            detected.append("chest pain")
    
    return list(set(detected))

def get_disease_details(disease_name: str) -> Optional[Dict]:
    """
    Get complete disease details from single table.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT 
        name,
        description,
        symptoms,
        precautions,
        medications,
        diet,
        workouts,
        symptom_count
    FROM diseases
    WHERE name = ?
    """, (disease_name,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    name, description, symptoms_str, precautions_str, medications_str, diet_str, workouts_str, symptom_count = row
    
    return {
        'name': name,
        'description': description or '',
        'symptoms': json.loads(symptoms_str) if symptoms_str else [],
        'precautions': json.loads(precautions_str) if precautions_str else [],
        'medications': json.loads(medications_str) if medications_str else [],
        'diet': json.loads(diet_str) if diet_str else [],
        'workouts': json.loads(workouts_str) if workouts_str else [],
        'symptom_count': symptom_count
    }

def get_diseases_batch(disease_names: List[str]) -> List[Dict]:
    """
    Get details for multiple diseases at once from single table.
    """
    if not disease_names:
        return []
    
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholders = ','.join('?' * len(disease_names))
    
    cursor.execute(f"""
    SELECT 
        name,
        description,
        symptoms,
        precautions,
        medications,
        diet,
        workouts,
        symptom_count
    FROM diseases
    WHERE name IN ({placeholders})
    """, disease_names)
    
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        name, description, symptoms_str, precautions_str, medications_str, diet_str, workouts_str, symptom_count = row
        results.append({
            'name': name,
            'description': description or '',
            'symptoms': json.loads(symptoms_str) if symptoms_str else [],
            'precautions': json.loads(precautions_str) if precautions_str else [],
            'medications': json.loads(medications_str) if medications_str else [],
            'diet': json.loads(diet_str) if diet_str else [],
            'workouts': json.loads(workouts_str) if workouts_str else [],
            'symptom_count': symptom_count
        })
    
    return results

def search_diseases(query: str, limit: int = 10) -> List[Dict]:
    """
    Search diseases by name or description in single table.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    search_term = f'%{query}%'
    cursor.execute("""
    SELECT name, description, symptom_count
    FROM diseases
    WHERE name LIKE ? OR description LIKE ?
    ORDER BY name
    LIMIT ?
    """, (search_term, search_term, limit))
    
    results = [
        {'name': row[0], 'description': row[1], 'symptom_count': row[2]}
        for row in cursor.fetchall()
    ]
    conn.close()
    
    return results

def get_all_symptoms() -> List[str]:
    """
    Extract all unique symptoms from the diseases table.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT symptoms FROM diseases")
    rows = cursor.fetchall()
    
    all_symptoms = set()
    for (symptoms_json,) in rows:
        try:
            symptoms_list = json.loads(symptoms_json) if symptoms_json else []
            all_symptoms.update(symptoms_list)
        except:
            pass
    
    conn.close()
    return sorted(list(all_symptoms))

def get_disease_count() -> int:
    """
    Get total number of diseases in single table.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM diseases")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_symptoms_for_disease(disease_name: str) -> List[str]:
    """
    Get symptoms for a specific disease from single table.
    """
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
    """
    Find symptoms that commonly co-occur with the given symptom.
    Modified for single table structure.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    symptom = normalize_symptom(symptom)
    
    # Get all diseases that have this symptom
    cursor.execute("""
    SELECT symptoms FROM diseases WHERE symptoms LIKE ?
    """, (f'%{symptom}%',))
    
    rows = cursor.fetchall()
    
    # Count co-occurrences
    co_occurrence_count = {}
    total_diseases_with_symptom = len(rows)
    
    for (symptoms_json,) in rows:
        try:
            disease_symptoms = json.loads(symptoms_json) if symptoms_json else []
            for ds in disease_symptoms:
                if ds.lower() != symptom.lower():
                    co_occurrence_count[ds] = co_occurrence_count.get(ds, 0) + 1
        except:
            pass
    
    # Calculate percentages and sort
    results = []
    for sym, count in co_occurrence_count.items():
        if total_diseases_with_symptom > 0:
            percentage = round(count * 100.0 / total_diseases_with_symptom, 2)
            results.append((sym, percentage))
    
    results.sort(key=lambda x: x[1], reverse=True)
    
    conn.close()
    return results[:limit]

def get_urgency_level(disease_name: str) -> str:
    """
    Determine urgency level based on disease details.
    """
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
    """
    Get diseases filtered by symptom count.
    New helper function for single table structure.
    """
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
    results = [
        {'name': row[0], 'description': row[1], 'symptom_count': row[2]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return results