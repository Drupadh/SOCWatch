import json
import csv
import io
from datetime import datetime

def generate_json_report(alerts: list) -> str:
    """Returns alerts formatted as JSON string."""
    return json.dumps(alerts, indent=4)

def generate_csv_report(alerts: list) -> str:
    """Returns alerts formatted as CSV string."""
    if not alerts:
        return ""
        
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=alerts[0].keys())
    writer.writeheader()
    for alert in alerts:
        writer.writerow(alert)
        
    return output.getvalue()

def generate_text_report(alerts: list) -> str:
    """Generates a professional SOC incident report in Plain Text."""
    output = []
    output.append("="*60)
    output.append("SOC INCIDENT REPORT - CONTINUOUS MONITORING PLATFORM")
    output.append(f"Generated: {datetime.now().isoformat()}")
    output.append("="*60 + "\n")
    
    output.append("EXECUTIVE SUMMARY")
    output.append("-" * 60)
    if not alerts:
         output.append("No active alerts detected in the system.\n")
         return "\n".join(output)

    total = len(alerts)
    critical = sum(1 for a in alerts if a['severity'] == 'Critical')
    
    output.append(f"Total Threats Monitored: {total}")
    output.append(f"Critical Severity Incidents: {critical}")
    output.append("-" * 60 + "\n")
    
    output.append("DETAILED ALERT LOG")
    output.append("-" * 60)
    for a in alerts:
        output.append(f"[{a['created_at']}] {a['severity'].upper()} ALERT")
        output.append(f"  Source IP : {a['source_ip']} ({a['country']}, {a['city']})")
        output.append(f"  Intel     : {a['reputation']} Reputation | {a['abuse_reports']} Abuse Reports")
        output.append(f"  Vector    : {a['attack_type']} against user '{a['username']}'")
        output.append(f"  Attempts  : {a['attempt_count']}")
        output.append("-" * 60)
        
    output.append("\nRECOMMENDED MITIGATIONS:")
    output.append("1. Block identified Critical IPs at the network perimeter (firewall/WAF).")
    output.append("2. Invalidate passwords for severely targeted accounts.")
    output.append("3. Verify geolocation of source IPs against known employee geofences.")
    output.append("\n" + "="*60)
    
    return "\n".join(output)
