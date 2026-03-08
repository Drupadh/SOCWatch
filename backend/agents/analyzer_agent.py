import json
from backend.agents.llm_client import call_llm
from typing import List, Dict

class ThreatIntelAgent:
    """
    Agent responsible for reading structured events and heuristically or intelligently identifying anomalies.
    """
    def __init__(self):
        self.system_prompt = (
            "You are the Threat Intel Agent. You will receive a JSON list of authentication events. "
            "Analyze the events to identify threats like Brute Force attacks, Password Spraying, or impossible travel. "
            "Return a JSON object with a single key 'alerts'. "
            "Each alert in the array must have: 'source_ip', 'attack_type', 'attempt_count', 'severity' (Low|Medium|High|Critical), "
            "and a 'reasoning' block explaining *why* you classified this as a threat."
        )

    def analyze(self, parsed_events: List[Dict]) -> List[Dict]:
        print(f"[Threat Agent] analyzing {len(parsed_events)} events for malicious patterns...")
        
        events_json = json.dumps(parsed_events)
        
        prompt = f"Identify any attacks in this dataset:\n\n{events_json}"
        
        result = call_llm(prompt, system_message=self.system_prompt, response_format="json_object")
        
        if not result:
            return []

        try:
            alerts_data = json.loads(result)
            alerts = alerts_data.get("alerts", [])
            print(f"[Threat Agent] Detected {len(alerts)} alerts based on behavioral analysis.")
            return alerts
        except json.JSONDecodeError as e:
            print(f"[Threat Agent] Error decoding JSON from LLM: {e}")
            return []
