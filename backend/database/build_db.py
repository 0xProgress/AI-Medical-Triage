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
        self._create_single_table_db()
        self._generate_json()
        print("✅ Database build complete!")
        print(f"   📊 Diseases: {len(self.disease_symptoms_map)}")
        print(f"   🩺 Unique Symptoms: {len(self.symptom_set)}")
    
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
    
    def _create_single_table_db(self):
        """Create a single table database with all disease information in one table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS diseases")
        
        cursor.execute("""
        CREATE TABLE diseases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            symptoms TEXT,
            precautions TEXT,
            medications TEXT,
            diet TEXT,
            workouts TEXT,
            symptom_count INTEGER DEFAULT 0
        )
        """)
        
        cursor.execute("CREATE INDEX idx_diseases_name ON diseases(name)")
        
        for disease, symptoms in tqdm(
            self.disease_symptoms_map.items(),
            desc="Inserting diseases into single table"
        ):
            info = self.disease_info.get(disease, {})
            
            symptoms_json = json.dumps(symptoms)
            precautions_json = json.dumps(info.get('precautions', []))
            medications_json = json.dumps(info.get('medications', []))
            diet_json = json.dumps(info.get('diet', []))
            workouts_json = json.dumps(info.get('workouts', []))
            
            cursor.execute("""
            INSERT OR REPLACE INTO diseases 
            (name, description, symptoms, precautions, medications, diet, workouts, symptom_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                disease,
                info.get('description', ''),
                symptoms_json,
                precautions_json,
                medications_json,
                diet_json,
                workouts_json,
                len(symptoms)
            ))
        
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM diseases")
        disease_count = cursor.fetchone()[0]
        
        print(f"   💾 Single table database created: {self.db_path}")
        print(f"   📊 Total diseases stored: {disease_count}")
        
        cursor.execute("SELECT name, symptom_count FROM diseases LIMIT 3")
        samples = cursor.fetchall()
        print("   📋 Sample diseases:")
        for sample in samples:
            print(f"      - {sample[0]} ({sample[1]} symptoms)")
        
        conn.close()
    
    def _generate_json(self):
        """Generate JSON file from the single table database"""
        conn = sqlite3.connect(self.db_path)
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
        ORDER BY name
        """)
        
        diseases = {}
        for row in cursor.fetchall():
            name, description, symptoms_str, precautions_str, medications_str, diet_str, workouts_str, symptom_count = row
            
            try:
                symptoms_list = json.loads(symptoms_str) if symptoms_str else []
            except:
                symptoms_list = []
            
            try:
                precautions_list = json.loads(precautions_str) if precautions_str else []
            except:
                precautions_list = []
            
            try:
                medications_list = json.loads(medications_str) if medications_str else []
            except:
                medications_list = []
            
            try:
                diet_list = json.loads(diet_str) if diet_str else []
            except:
                diet_list = []
            
            try:
                workouts_list = json.loads(workouts_str) if workouts_str else []
            except:
                workouts_list = []
            
            diseases[name] = {
                'description': description or '',
                'symptoms': symptoms_list,
                'precautions': precautions_list,
                'medications': medications_list,
                'diet': diet_list,
                'workouts': workouts_list,
                'symptom_count': symptom_count
            }
        
        conn.close()
        
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(diseases, f, indent=2, ensure_ascii=False)
        
        print(f"   📄 JSON generated: {self.json_path}")

def query_examples(db_path):
    """Example queries for the single table database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📊 Query Examples:")
    
    print("\n1. Get 'common cold' disease info:")
    cursor.execute("SELECT * FROM diseases WHERE name LIKE '%cold%'")
    row = cursor.fetchone()
    if row:
        disease_data = {
            'name': row[1],
            'description': row[2],
            'symptoms': json.loads(row[3]),
            'precautions': json.loads(row[4]),
            'medications': json.loads(row[5]),
            'diet': json.loads(row[6]),
            'workouts': json.loads(row[7])
        }
        print(json.dumps(disease_data, indent=2))
    
    print("\n2. Diseases with 'fever' symptom:")
    cursor.execute("SELECT name FROM diseases WHERE symptoms LIKE '%fever%'")
    fever_diseases = cursor.fetchall()
    for disease in fever_diseases[:5]:  
        print(f"   - {disease[0]}")
    
    print("\n3. Top 3 diseases with most symptoms:")
    cursor.execute("SELECT name, symptom_count FROM diseases ORDER BY symptom_count DESC LIMIT 3")
    top_diseases = cursor.fetchall()
    for disease in top_diseases:
        print(f"   - {disease[0]} ({disease[1]} symptoms)")
    
    conn.close()

if __name__ == "__main__":
    builder = DatabaseBuilder()
    builder.build()
    
    query_examples(DB_PATH)