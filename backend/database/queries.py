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
    
    symptom_placeholders = ','.join('?' * len(normalized_symptoms))
    
    query = f"""
    SELECT 
        d.name,
        COUNT(ds.symptom_id) as matches,
        ROUND(COUNT(ds.symptom_id) * 100.0 / d.symptom_count, 2) as match_percentage
    FROM diseases d
    JOIN disease_symptoms ds ON d.id = ds.disease_id
    JOIN symptoms s ON ds.symptom_id = s.id
    WHERE s.name IN ({symptom_placeholders})
    GROUP BY d.id, d.name, d.symptom_count
    HAVING matches > 0
    ORDER BY matches DESC, match_percentage DESC
    LIMIT ?
    """
    
    params = normalized_symptoms + [limit]
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    
    return results

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
            # No running loop, create one
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
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT 
        d.name,
        d.description,
        d.precautions,
        d.medications,
        d.diet,
        d.workouts,
        d.symptom_count,
        GROUP_CONCAT(s.name) as symptoms
    FROM diseases d
    LEFT JOIN disease_symptoms ds ON d.id = ds.disease_id
    LEFT JOIN symptoms s ON ds.symptom_id = s.id
    WHERE d.name = ?
    GROUP BY d.id
    """, (disease_name,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    name, description, precautions, medications, diet, workouts, symptom_count, symptoms_str = row
    
    return {
        'name': name,
        'description': description or '',
        'precautions': json.loads(precautions) if precautions else [],
        'medications': json.loads(medications) if medications else [],
        'diet': json.loads(diet) if diet else [],
        'workouts': json.loads(workouts) if workouts else [],
        'symptom_count': symptom_count,
        'symptoms': symptoms_str.split(',') if symptoms_str else []
    }

def get_diseases_batch(disease_names: List[str]) -> List[Dict]:
    if not disease_names:
        return []
    
    conn = get_connection()
    cursor = conn.cursor()
    
    placeholders = ','.join('?' * len(disease_names))
    
    cursor.execute(f"""
    SELECT 
        d.name,
        d.description,
        d.precautions,
        d.medications,
        d.diet,
        d.workouts,
        d.symptom_count,
        GROUP_CONCAT(s.name) as symptoms
    FROM diseases d
    LEFT JOIN disease_symptoms ds ON d.id = ds.disease_id
    LEFT JOIN symptoms s ON ds.symptom_id = s.id
    WHERE d.name IN ({placeholders})
    GROUP BY d.id
    """, disease_names)
    
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        name, description, precautions, medications, diet, workouts, symptom_count, symptoms_str = row
        results.append({
            'name': name,
            'description': description or '',
            'precautions': json.loads(precautions) if precautions else [],
            'medications': json.loads(medications) if medications else [],
            'diet': json.loads(diet) if diet else [],
            'workouts': json.loads(workouts) if workouts else [],
            'symptom_count': symptom_count,
            'symptoms': symptoms_str.split(',') if symptoms_str else []
        })
    
    return results

def search_diseases(query: str, limit: int = 10) -> List[Dict]:
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM symptoms ORDER BY name")
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results

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
    cursor.execute("""
    SELECT s.name
    FROM symptoms s
    JOIN disease_symptoms ds ON s.id = ds.symptom_id
    JOIN diseases d ON ds.disease_id = d.id
    WHERE d.name = ?
    """, (disease_name,))
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results

def find_related_symptoms(symptom: str, limit: int = 10) -> List[Tuple[str, float]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    symptom = normalize_symptom(symptom)
    
    cursor.execute("""
    SELECT 
        s2.name,
        COUNT(DISTINCT d.id) as co_occurrence,
        ROUND(COUNT(DISTINCT d.id) * 100.0 / (
            SELECT COUNT(DISTINCT d3.id)
            FROM diseases d3
            JOIN disease_symptoms ds3 ON d3.id = ds3.disease_id
            JOIN symptoms s3 ON ds3.symptom_id = s3.id
            WHERE s3.name = ?
        ), 2) as co_occurrence_percentage
    FROM symptoms s1
    JOIN disease_symptoms ds1 ON s1.id = ds1.symptom_id
    JOIN diseases d ON ds1.disease_id = d.id
    JOIN disease_symptoms ds2 ON d.id = ds2.disease_id
    JOIN symptoms s2 ON ds2.symptom_id = s2.id
    WHERE s1.name = ? AND s2.name != ?
    GROUP BY s2.id, s2.name
    ORDER BY co_occurrence DESC
    LIMIT ?
    """, (symptom, symptom, symptom, limit))
    
    results = cursor.fetchall()
    conn.close()
    return results

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