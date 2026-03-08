import json
from backend.agents.llm_client import call_llm
from typing import List, Dict

class ParserAgent:
    """
    Agent responsible for ingesting messy raw log lines and extracting structured JSON data.
    """
    def __init__(self):
        self.system_prompt = (
            "You are the Parser Agent in a SIEM architecture. "
            "Your job is to read an unordered set of system log lines and return a structured JSON array. "
            "Extract the following for EACH log line if present: 'timestamp', 'ip_address', 'status' (Failed/Success), 'username', and 'raw_log'.\n\n"
            "Return ONLY a JSON object with a single key 'events' containing the array. Do not include markdown block formatting."
        )

    def parse(self, raw_logs: str) -> List[Dict]:
        lines = [line for line in raw_logs.strip().splitlines() if line.strip()]
        
        if len(lines) > 50:
            print(f"[Parser Agent] Log file is large ({len(lines)} lines). Processing a recent 50-line sample to prevent LLM token limits...")
            lines = lines[-50:] # Grab the last 50 lines
            
        sampled_logs = "\n".join(lines)
            
        print(f"[Parser Agent] Analyzing {len(lines)} lines of raw logs...")
        
        prompt = f"Please map these logs into structured JSON:\n\n{sampled_logs}"
        
        result = call_llm(prompt, system_message=self.system_prompt, response_format="json_object")
        
        if not result:
            return []

        try:
            parsed_data = json.loads(result)
            events = parsed_data.get("events", [])
            print(f"[Parser Agent] Successfully extracted {len(events)} structured events.")
            return events
        except json.JSONDecodeError as e:
            print(f"[Parser Agent] Error decoding JSON from LLM: {e}")
            return []
