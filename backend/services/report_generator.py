import io
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from backend.config import config

REPORTS_DIR = Path(__file__).parent.parent / "data" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        if 'Title' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Title',
                parent=self.styles['Heading1'],
                fontSize=24,
                alignment=TA_CENTER,
                spaceAfter=20
            ))
        
        if 'Subtitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Subtitle',
                parent=self.styles['Heading2'],
                fontSize=14,
                alignment=TA_CENTER,
                spaceAfter=30
            ))
        
        if 'SectionHeader' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='SectionHeader',
                parent=self.styles['Heading3'],
                fontSize=14,
                spaceBefore=12,
                spaceAfter=6
            ))
        
        if 'BodyText' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='BodyText',
                parent=self.styles['Normal'],
                fontSize=10,
                spaceAfter=6
            ))
        
        if 'Disclaimer' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Disclaimer',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.red,
                alignment=TA_CENTER,
                spaceBefore=20
            ))
        
        if 'ConditionName' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='ConditionName',
                parent=self.styles['Heading4'],
                fontSize=12,
                spaceBefore=10,
                spaceAfter=4
            ))
    
    def generate_report(self, session_id: str, triage_data: Dict[str, Any]) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{session_id[:8]}_{timestamp}.pdf"
        filepath = REPORTS_DIR / filename
        
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        elements = []
        
        elements.append(Paragraph("AI Medical Triage Report", self.styles['Title']))
        elements.append(Paragraph(f"Report ID: {session_id}", self.styles['Subtitle']))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", self.styles['Subtitle']))
        elements.append(Spacer(1, 20))
        
        elements.append(Paragraph("Clinical Note", self.styles['SectionHeader']))
        elements.append(Paragraph(triage_data.get('summary', 'No summary available'), self.styles['BodyText']))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("Reported Symptoms", self.styles['SectionHeader']))
        symptoms = triage_data.get('symptoms', [])
        if symptoms:
            symptoms_text = ", ".join(symptoms)
        else:
            symptoms_text = "No specific symptoms recorded."
        elements.append(Paragraph(symptoms_text, self.styles['BodyText']))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("How AI Arrived at Answer", self.styles['SectionHeader']))
        elements.append(Paragraph(
            "Symptoms were matched against the Symcat medical database. "
            "Conditions were ranked by symptom overlap and clinical relevance.",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("Evidence & Condition Matches", self.styles['SectionHeader']))
        
        conditions = triage_data.get('conditions', [])
        if conditions:
            for i, condition in enumerate(conditions, 1):
                elements.append(Paragraph(f"{i}. {condition.get('name', 'Unknown')}", self.styles['ConditionName']))
                elements.append(Paragraph(f"   Confidence: {condition.get('match_percentage', 0)}%", self.styles['BodyText']))
                elements.append(Paragraph(f"   Urgency: {condition.get('urgency', 'Unknown').upper()}", self.styles['BodyText']))
                elements.append(Paragraph(f"   Description: {condition.get('description', 'N/A')}", self.styles['BodyText']))
                
                precautions = condition.get('precautions', [])
                if precautions:
                    precautions_text = "   Precautions: " + "; ".join(precautions)
                    elements.append(Paragraph(precautions_text, self.styles['BodyText']))
                
                elements.append(Spacer(1, 6))
        else:
            elements.append(Paragraph("No matching conditions found.", self.styles['BodyText']))
        
        elements.append(Spacer(1, 12))
        
        red_flags = triage_data.get('red_flags', [])
        if red_flags:
            elements.append(Paragraph("⚠️ Red Flags", self.styles['SectionHeader']))
            for flag in red_flags:
                elements.append(Paragraph(f"• {flag}", self.styles['BodyText']))
            elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("Recommendations", self.styles['SectionHeader']))
        elements.append(Paragraph(
            "• Schedule a consultation with a healthcare provider for evaluation.",
            self.styles['BodyText']
        ))
        elements.append(Paragraph(
            "• Monitor your symptoms closely for any changes.",
            self.styles['BodyText']
        ))
        if red_flags:
            elements.append(Paragraph(
                "• SEEK IMMEDIATE MEDICAL ATTENTION due to red flag symptoms.",
                self.styles['BodyText']
            ))
        elements.append(Paragraph(
            "• Do not delay seeking professional medical advice.",
            self.styles['BodyText']
        ))
        elements.append(Spacer(1, 20))
        
        elements.append(Paragraph("=" * 80, self.styles['BodyText']))
        elements.append(Paragraph(
            "DISCLAIMER: This report is for INFORMATIONAL PURPOSES ONLY. "
            "It is NOT a substitute for professional medical advice, diagnosis, or treatment. "
            "Always consult a licensed healthcare provider for medical concerns. "
            "In case of emergency, contact your local emergency services immediately.",
            self.styles['Disclaimer']
        ))
        
        doc.build(elements)
        
        return str(filepath)
    
    def generate_report_json(self, session_id: str, triage_data: Dict[str, Any]) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{session_id[:8]}_{timestamp}.json"
        filepath = REPORTS_DIR / filename
        
        report_data = {
            "report_id": session_id,
            "generated_at": datetime.now().isoformat(),
            "summary": triage_data.get('summary', ''),
            "symptoms": triage_data.get('symptoms', []),
            "conditions": triage_data.get('conditions', []),
            "red_flags": triage_data.get('red_flags', []),
            "conversation": triage_data.get('conversation', []),
            "turn_count": triage_data.get('turn_count', 0)
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        return str(filepath)

report_generator = ReportGenerator()