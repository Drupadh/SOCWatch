from typing import List, Dict
from backend.config import CONFIG

def determine_severity(attempt_count: int) -> str:
    thresholds = CONFIG.get("threat_thresholds", {"critical": 10, "high": 6, "medium": 3})
    
    if attempt_count >= thresholds.get("critical", 10):
        return "Critical"
    elif attempt_count >= thresholds.get("high", 6):
        return "High"
    elif attempt_count >= thresholds.get("medium", 3):
        return "Medium"
    else:
        return "Low"

def detect_threats(parsed_events: List[Dict]) -> List[Dict]:
    """
    Groups failed login attempts by IP and generates alerts for brute-force patterns.
    Takes logic from old analyzer but applies dynamic thresholds.
    """
    failed_attempts_by_ip = {}
    usernames_by_ip = {}
    
    for event in parsed_events:
        if event["status"] == "Failed":
            ip = event["ip_address"]
            username = event.get("username", "Unknown")
            
            failed_attempts_by_ip[ip] = failed_attempts_by_ip.get(ip, 0) + 1
            if ip not in usernames_by_ip or username != "Unknown":
               usernames_by_ip[ip] = username

    alerts = []
    min_threshold = CONFIG.get("threat_thresholds", {}).get("medium", 3)
    
    for ip, count in failed_attempts_by_ip.items():
        if count >= min_threshold: 
            severity = determine_severity(count)
            alerts.append({
                "source_ip": ip,
                "username": usernames_by_ip.get(ip, "Unknown"),
                "attack_type": "Brute-Force",
                "attempt_count": count,
                "severity": severity
            })
            
    return alerts
