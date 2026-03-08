from backend.agents.llm_client import call_llm
from typing import List, Dict
from datetime import datetime

class ReporterAgent:
    """
    Agent responsible for creating human-readable incident reports based on Intel Agent alerts.
    """
    def __init__(self):
        self.system_prompt = (
            "You are the Reporter Agent for a SOC. You will receive a summary of identified threat alerts. "
            "Your job is to generate a professional, markdown-formatted Incident Summary Report. "
            "Include an Executive Summary, The Attack Details, and Custom Mitigation Recommendations specific to the attacks seen."
        )

    def generate_report(self, alerts: List[Dict]) -> str:
        print(f"[Reporter Agent] Drafting executive Incident Report for {len(alerts)} alerts...")
        
        if not alerts:
            return "No threats detected in the supplied logs. System secure."
            
        alerts_text = ""
        for i, a in enumerate(alerts):
            alerts_text += f"{i+1}. IP {a.get('source_ip')} performed a {a.get('severity')} severity {a.get('attack_type')} (freq: {a.get('attempt_count')}). Reason: {a.get('reasoning')}\n"

        prompt = f"Generate the report based on these findings:\n\n{alerts_text}"
        
        report = call_llm(prompt, system_message=self.system_prompt)
        print(f"[Reporter Agent] Report finalized.")
        return report or "Failed to generate report."
