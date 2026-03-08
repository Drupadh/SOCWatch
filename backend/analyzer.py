from typing import List, Dict

def determine_severity(attempt_count: int) -> str:
    if attempt_count >= 10:
        return "Critical"
    elif attempt_count >= 6:
        return "High"
    elif attempt_count >= 3:
        return "Medium"
    else:
        return "Low"

def detect_threats(parsed_events: List[Dict]) -> List[Dict]:
    """
    Groups failed login attempts by IP and generates alerts for brute-force patterns.
    """
    failed_attempts_by_ip = {}
    
    for event in parsed_events:
        if event["status"] == "Failed":
            ip = event["ip_address"]
            failed_attempts_by_ip[ip] = failed_attempts_by_ip.get(ip, 0) + 1

    alerts = []
    for ip, count in failed_attempts_by_ip.items():
        if count >= 3: # Minimum threshold for alert
            severity = determine_severity(count)
            alerts.append({
                "source_ip": ip,
                "attack_type": "Brute-Force",
                "attempt_count": count,
                "severity": severity
            })
            
    return alerts
