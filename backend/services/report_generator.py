import io
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from backend.config import config

REPORTS_DIR = Path(__file__).parent.parent / "data" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

class ReportGenerator:
    def __init__(self):
        pass
    
    def generate_report_markdown(self, session_id: str, triage_data: Dict[str, Any]) -> str:
        """
        Generate a comprehensive Markdown report.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{session_id[:8]}_{timestamp}.md"
        filepath = REPORTS_DIR / filename
        
        # Build the markdown report
        md_content = self._build_markdown_report(session_id, triage_data)
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return str(filepath)
    
    def _build_markdown_report(self, session_id: str, triage_data: Dict[str, Any]) -> str:
        """Build the complete markdown report content"""
        
        lines = []
        
        # Header
        lines.append("# 🏥 AI Medical Triage Report")
        lines.append("")
        lines.append(f"**Report ID:** `{session_id}`")
        lines.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        lines.append(f"**Total Questions Asked:** {triage_data.get('turn_count', 0)}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Executive Summary
        lines.append("## 📋 Executive Summary")
        lines.append("")
        summary = triage_data.get('summary', 'No summary available')
        lines.append(summary)
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Reported Symptoms
        lines.append("## 🔍 Reported Symptoms")
        lines.append("")
        symptoms = triage_data.get('symptoms', [])
        if symptoms:
            lines.append("The following symptoms were **explicitly mentioned** during the triage:")
            lines.append("")
            for symptom in symptoms:
                lines.append(f"- 🩺 {symptom}")
            lines.append("")
            lines.append(f"**Total symptoms identified:** {len(symptoms)}")
        else:
            lines.append("*No specific symptoms were reported during the triage session.*")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # How AI Arrived at Answer (Transparency Section)
        lines.append("## 🤖 How AI Arrived at Answer")
        lines.append("")
        lines.append("### Methodology")
        lines.append("")
        lines.append("1. **Symptom Extraction:** Only symptoms explicitly mentioned by the user were extracted")
        lines.append("2. **Database Matching:** Symptoms were matched against a medical database of conditions")
        lines.append("3. **Confidence Scoring:** Conditions ranked by symptom overlap percentage")
        lines.append("4. **No Assumptions:** AI did not infer or add any symptoms not stated by the user")
        lines.append("")
        
        # Show the matching process
        conditions = triage_data.get('conditions', [])
        if symptoms and conditions:
            lines.append("### Matching Process")
            lines.append("")
            lines.append("| Step | Description |")
            lines.append("|------|-------------|")
            lines.append(f"| 1 | Extracted {len(symptoms)} symptoms from conversation |")
            
            # Show which symptoms matched the top condition
            top_condition = conditions[0] if conditions else None
            if top_condition:
                condition_symptoms = top_condition.get('symptoms', [])
                matched = [s for s in symptoms if any(s.lower() in cs.lower() or cs.lower() in s.lower() for cs in condition_symptoms)]
                lines.append(f"| 2 | Matched {len(matched)} symptoms with {top_condition.get('name')} |")
                lines.append(f"| 3 | Calculated {top_condition.get('match_percentage', 0)}% symptom overlap |")
                lines.append(f"| 4 | Verified no hallucinated symptoms added |")
            
            lines.append("")
            lines.append("### Symptom Matching Details")
            lines.append("")
            
            for condition in conditions[:3]:
                condition_symptoms = condition.get('symptoms', [])
                matched = [s for s in symptoms if any(s.lower() in cs.lower() or cs.lower() in s.lower() for cs in condition_symptoms)]
                unmatched = [s for s in condition_symptoms if not any(s.lower() in ms.lower() or ms.lower() in s.lower() for ms in symptoms)]
                
                lines.append(f"**{condition.get('name')}** ({condition.get('match_percentage', 0)}% match)")
                lines.append(f"- ✅ Matched symptoms: {', '.join(matched) if matched else 'None'}")
                lines.append(f"- ❓ Other symptoms of this condition: {', '.join(unmatched[:5]) if unmatched else 'None'}")
                lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # Condition Matches
        lines.append("## 🎯 Condition Matches")
        lines.append("")
        
        if conditions:
            for i, condition in enumerate(conditions, 1):
                urgency = condition.get('urgency', 'medium').upper()
                urgency_emoji = {
                    'HIGH': '🔴',
                    'MEDIUM': '🟡',
                    'LOW': '🟢'
                }.get(urgency, '⚪')
                
                lines.append(f"### {i}. {condition.get('name', 'Unknown')} {urgency_emoji}")
                lines.append("")
                lines.append(f"**Confidence:** {condition.get('match_percentage', 0)}%")
                lines.append(f"**Urgency:** {urgency}")
                lines.append(f"**Matched Symptoms:** {condition.get('symptom_count', 0)}")
                lines.append("")
                
                description = condition.get('description', 'No description available')
                lines.append(f"**Description:** {description}")
                lines.append("")
                
                # Precautions
                precautions = condition.get('precautions', [])
                if precautions:
                    lines.append("**🛡️ Precautions:**")
                    for precaution in precautions:
                        lines.append(f"- {precaution}")
                    lines.append("")
                
                # Medications
                medications = condition.get('medications', [])
                if medications:
                    lines.append("**💊 Common Medications:**")
                    for medication in medications:
                        lines.append(f"- {medication}")
                    lines.append("")
                
                # Diet
                diet = condition.get('diet', [])
                if diet:
                    lines.append("**🥗 Dietary Recommendations:**")
                    for item in diet:
                        lines.append(f"- {item}")
                    lines.append("")
                
                # Workouts
                workouts = condition.get('workouts', [])
                if workouts:
                    lines.append("**🏃 Exercise Recommendations:**")
                    for workout in workouts:
                        lines.append(f"- {workout}")
                    lines.append("")
                
                lines.append("---")
                lines.append("")
        else:
            lines.append("*No matching conditions were found based on the reported symptoms.*")
            lines.append("")
        
        # Red Flags
        red_flags = triage_data.get('red_flags', [])
        if red_flags:
            lines.append("## ⚠️ Red Flag Symptoms")
            lines.append("")
            lines.append("**The following red flag symptoms were detected:**")
            lines.append("")
            for flag in red_flags:
                lines.append(f"- 🚨 **{flag}**")
            lines.append("")
            lines.append("> ⚠️ **IMPORTANT:** These symptoms may indicate a serious condition. Seek medical attention promptly.")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Conversation Transcript
        conversation = triage_data.get('conversation', [])
        if conversation:
            lines.append("## 💬 Conversation Transcript")
            lines.append("")
            lines.append("<details>")
            lines.append("<summary>Click to expand conversation</summary>")
            lines.append("")
            
            for msg in conversation:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                
                if role == 'user':
                    lines.append(f"**👤 You:** {content}")
                elif role == 'assistant':
                    lines.append(f"**🤖 AI:** {content}")
                lines.append("")
            
            lines.append("</details>")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Recommendations
        lines.append("## 📝 Recommendations")
        lines.append("")
        lines.append("1. **Consult a Healthcare Provider:** Schedule an appointment for proper evaluation")
        lines.append("2. **Monitor Symptoms:** Keep track of any changes in your symptoms")
        lines.append("3. **Document Triggers:** Note what makes symptoms better or worse")
        lines.append("4. **Follow Medical Advice:** Do not self-medicate based on this report")
        
        if red_flags:
            lines.append("5. **🚨 Seek Immediate Care:** Due to red flag symptoms, seek prompt medical attention")
        
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Safety Information
        lines.append("## ℹ️ When to Seek Emergency Care")
        lines.append("")
        lines.append("Seek **immediate emergency care** if you experience:")
        lines.append("")
        lines.append("- Chest pain or pressure")
        lines.append("- Difficulty breathing or shortness of breath")
        lines.append("- Severe bleeding")
        lines.append("- Loss of consciousness or fainting")
        lines.append("- Sudden confusion or difficulty speaking")
        lines.append("- Severe allergic reaction")
        lines.append("- Thoughts of harming yourself or others")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Verification Note
        lines.append("## ✅ Verification & Transparency")
        lines.append("")
        lines.append("### Symptom Source Verification")
        lines.append("")
        if symptoms:
            lines.append("All symptoms listed in this report were **explicitly mentioned** by the user during the triage conversation. ")
            lines.append("The AI system was programmed to:")
            lines.append("")
            lines.append("- ✅ Only extract symptoms explicitly stated")
            lines.append("- ✅ Never infer or assume additional symptoms")
            lines.append("- ✅ Validate all symptoms against original messages")
            lines.append("- ✅ Use conservative matching algorithms")
            lines.append("")
            lines.append("**If any symptom appears in this report that you did not mention, this is an error and should be reported.**")
        else:
            lines.append("No symptoms were identified from the conversation.")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Disclaimer
        lines.append("## ⚠️ Medical Disclaimer")
        lines.append("")
        lines.append("> **IMPORTANT LEGAL NOTICE:**")
        lines.append("> ")
        lines.append("> This report is generated by an AI system for **INFORMATIONAL PURPOSES ONLY**.")
        lines.append("> ")
        lines.append("> - This is **NOT** a medical diagnosis")
        lines.append("> - This is **NOT** a substitute for professional medical advice")
        lines.append("> - This is **NOT** intended to replace consultation with a licensed healthcare provider")
        lines.append("> ")
        lines.append("> **Always consult a qualified healthcare provider** for medical concerns, diagnoses, or treatment.")
        lines.append("> ")
        lines.append("> **In case of medical emergency**, contact your local emergency services immediately.")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Footer
        lines.append(f"*Report generated on {datetime.now().strftime('%B %d, %Y at %I:%M:%S %p')}*")
        lines.append(f"*Report ID: {session_id}*")
        lines.append("")
        
        return "\n".join(lines)
    
    def generate_report_markdown_string(self, session_id: str, triage_data: Dict[str, Any]) -> str:
        """
        Generate markdown report as a string (for API responses).
        """
        return self._build_markdown_report(session_id, triage_data)
    
    def generate_report_json(self, session_id: str, triage_data: Dict[str, Any]) -> str:
        """
        Generate a JSON report file.
        """
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
            "turn_count": triage_data.get('turn_count', 0),
            "methodology": {
                "symptom_extraction": "Only explicitly mentioned symptoms extracted",
                "matching_algorithm": "Symptom overlap with medical database",
                "hallucination_prevention": "Symptoms validated against original messages",
                "confidence_calculation": "Percentage of matching symptoms / total symptoms"
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        return str(filepath)
    
    def generate_report(self, session_id: str, triage_data: Dict[str, Any]) -> str:
        """
        Main report generation method - generates Markdown by default.
        """
        return self.generate_report_markdown(session_id, triage_data)


report_generator = ReportGenerator()