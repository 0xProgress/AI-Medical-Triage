import sqlite3
import json
import csv
import ast
from pathlib import Path
from typing import Dict, List, Set
import pandas as pd
from tqdm import tqdm
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config

DATA_DIR = config.DATA_DIR
RAW_DATA_DIR = DATA_DIR / "raw"
DB_PATH = config.SQLITE_DB_PATH
JSON_PATH = config.JSON_DB_PATH

class DatabaseBuilder:
    def __init__(self):
        self.disease_symptoms_map = {}
        self.symptom_set = set()
        self.disease_info = {}
        self.raw_data_dir = RAW_DATA_DIR
        self.db_path = DB_PATH
        self.json_path = JSON_PATH
        
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def build(self):
        print("🔄 Building Medical Database...")
        self._parse_chunk_file()
        self._load_disease_info()
        self._create_sqlite_db()
        self._generate_json()
        print("✅ Database build complete!")
        print(f"   📊 Diseases: {len(self.disease_symptoms_map)}")
        print(f"   🩺 Symptoms: {len(self.symptom_set)}")
    
    def _parse_chunk_file(self):
        chunk_path = self.raw_data_dir / "Diseases.csv"
        
        if not chunk_path.exists():
            raise FileNotFoundError(f"Diseases.csv not found in {self.raw_data_dir}")
        
        df = pd.read_csv(chunk_path)
        
        symptom_columns = df.columns[1:]
        self.symptom_set = set(symptom_columns)
        
        print(f"Processing {len(df)} rows for {df['diseases'].nunique()} diseases...")
        
        for disease_name, group in tqdm(df.groupby('diseases'), desc="Processing diseases"):
            disease_name = str(disease_name).strip().lower()
            
            all_symptoms = set()
            for _, row in group.iterrows():
                for i, value in enumerate(row.iloc[1:], start=1):
                    if value == 1 or value == '1' or value is True:
                        symptom_name = symptom_columns[i-1]
                        if symptom_name and not pd.isna(symptom_name):
                            all_symptoms.add(str(symptom_name).strip())
            
            if all_symptoms:
                self.disease_symptoms_map[disease_name] = list(all_symptoms)
        
        print(f"Found {len(self.disease_symptoms_map)} unique diseases with {len(self.symptom_set)} symptoms")
    
    def _load_disease_info(self):
        desc_path = self.raw_data_dir / "description.csv"
        if desc_path.exists():
            with open(desc_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if len(row) >= 2:
                        disease = row[0].strip().lower()
                        description = row[1].strip()
                        if disease not in self.disease_info:
                            self.disease_info[disease] = {}
                        self.disease_info[disease]['description'] = description
        
        prec_path = self.raw_data_dir / "precautions.csv"
        if prec_path.exists():
            with open(prec_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if len(row) >= 5:
                        disease = row[0].strip().lower()
                        precautions = [p.strip() for p in row[1:5] if p.strip()]
                        if disease not in self.disease_info:
                            self.disease_info[disease] = {}
                        self.disease_info[disease]['precautions'] = precautions
        
        med_path = self.raw_data_dir / "medications.csv"
        if med_path.exists():
            with open(med_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if len(row) >= 2:
                        disease = row[0].strip().lower()
                        medications = self._parse_list_column(row[1])
                        if disease not in self.disease_info:
                            self.disease_info[disease] = {}
                        self.disease_info[disease]['medications'] = medications
        
        diet_path = self.raw_data_dir / "diets.csv"
        if diet_path.exists():
            with open(diet_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if len(row) >= 2:
                        disease = row[0].strip().lower()
                        diet = self._parse_list_column(row[1])
                        if disease not in self.disease_info:
                            self.disease_info[disease] = {}
                        self.disease_info[disease]['diet'] = diet
        
        workout_path = self.raw_data_dir / "workout.csv"
        if workout_path.exists():
            with open(workout_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if len(row) >= 2:
                        disease = row[0].strip().lower()
                        workouts = self._parse_list_column(row[1])
                        if disease not in self.disease_info:
                            self.disease_info[disease] = {}
                        self.disease_info[disease]['workouts'] = workouts
    
    def _parse_list_column(self, value: str) -> List[str]:
        if not value:
            return []
        
        try:
            value = value.replace("'", '"')
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if item]
        except:
            pass
        
        return [item.strip() for item in value.split(',') if item.strip()]
    
    def _create_sqlite_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA foreign_keys = ON")
        
        cursor.execute("DROP TABLE IF EXISTS disease_symptoms")
        cursor.execute("DROP TABLE IF EXISTS diseases")
        cursor.execute("DROP TABLE IF EXISTS symptoms")
        
        cursor.execute("""
        CREATE TABLE diseases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            precautions TEXT,
            medications TEXT,
            diet TEXT,
            workouts TEXT,
            symptom_count INTEGER DEFAULT 0
        )
        """)
        
        cursor.execute("""
        CREATE TABLE symptoms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """)
        
        cursor.execute("""
        CREATE TABLE disease_symptoms (
            disease_id INTEGER,
            symptom_id INTEGER,
            PRIMARY KEY (disease_id, symptom_id),
            FOREIGN KEY (disease_id) REFERENCES diseases(id) ON DELETE CASCADE,
            FOREIGN KEY (symptom_id) REFERENCES symptoms(id) ON DELETE CASCADE
        )
        """)
        
        cursor.execute("CREATE INDEX idx_disease_symptoms_disease ON disease_symptoms(disease_id)")
        cursor.execute("CREATE INDEX idx_disease_symptoms_symptom ON disease_symptoms(symptom_id)")
        cursor.execute("CREATE INDEX idx_diseases_name ON diseases(name)")
        cursor.execute("CREATE INDEX idx_symptoms_name ON symptoms(name)")
        
        symptom_id_map = {}
        for symptom in tqdm(sorted(self.symptom_set), desc="Inserting symptoms"):
            cursor.execute("INSERT INTO symptoms (name) VALUES (?)", (symptom,))
            symptom_id_map[symptom] = cursor.lastrowid
        
        disease_id_map = {}
        for disease, symptoms in tqdm(
            self.disease_symptoms_map.items(),
            desc="Inserting diseases"
        ):
            info = self.disease_info.get(disease, {})
            
            precautions_json = json.dumps(info.get('precautions', []))
            medications_json = json.dumps(info.get('medications', []))
            diet_json = json.dumps(info.get('diet', []))
            workouts_json = json.dumps(info.get('workouts', []))
            
            cursor.execute("""
            INSERT INTO diseases (name, description, precautions, medications, diet, workouts, symptom_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                disease,
                info.get('description', ''),
                precautions_json,
                medications_json,
                diet_json,
                workouts_json,
                len(symptoms)
            ))
            disease_id_map[disease] = cursor.lastrowid
        
        batch = []
        batch_size = 10000
        for disease, symptoms in tqdm(
            self.disease_symptoms_map.items(),
            desc="Building relationships"
        ):
            disease_id = disease_id_map.get(disease)
            if not disease_id:
                continue
            
            for symptom in symptoms:
                symptom_id = symptom_id_map.get(symptom)
                if symptom_id:
                    batch.append((disease_id, symptom_id))
                    
                    if len(batch) >= batch_size:
                        cursor.executemany(
                            "INSERT OR IGNORE INTO disease_symptoms (disease_id, symptom_id) VALUES (?, ?)",
                            batch
                        )
                        batch = []
        
        if batch:
            cursor.executemany(
                "INSERT OR IGNORE INTO disease_symptoms (disease_id, symptom_id) VALUES (?, ?)",
                batch
            )
        
        conn.commit()
        conn.close()
        
        print(f"   💾 Database created: {self.db_path}")
    
    def _generate_json(self):
        conn = sqlite3.connect(self.db_path)
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
        GROUP BY d.id
        ORDER BY d.name
        """)
        
        diseases = {}
        for row in cursor.fetchall():
            name, description, precautions, medications, diet, workouts, symptom_count, symptoms_str = row
            
            try:
                precautions_list = json.loads(precautions) if precautions else []
            except:
                precautions_list = []
            
            try:
                medications_list = json.loads(medications) if medications else []
            except:
                medications_list = []
            
            try:
                diet_list = json.loads(diet) if diet else []
            except:
                diet_list = []
            
            try:
                workouts_list = json.loads(workouts) if workouts else []
            except:
                workouts_list = []
            
            symptoms_list = symptoms_str.split(',') if symptoms_str else []
            
            diseases[name] = {
                'description': description or '',
                'precautions': precautions_list,
                'medications': medications_list,
                'diet': diet_list,
                'workouts': workouts_list,
                'symptom_count': symptom_count,
                'symptoms': symptoms_list
            }
        
        conn.close()
        
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(diseases, f, indent=2, ensure_ascii=False)
        
        print(f"   📄 JSON generated: {self.json_path}")

if __name__ == "__main__":
    builder = DatabaseBuilder()
    builder.build()