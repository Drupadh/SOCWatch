import asyncio
import os
from backend.config import CONFIG
from backend.parser import parse_auth_logs
from backend.detection_engine import detect_threats
from backend.enrichment import enrich_alert
from backend.database import get_db
from datetime import datetime

async def monitor_logs():
    """
    Background task that continuously monitors the configured log file for new entries.
    Parses them, detects threats, enriches them, and saves to the database.
    """
    log_file = CONFIG.get("log_file", "logs/auth.log")
    
    print(f"[Monitor] Starting real-time monitor on {log_file}...")
    
    if not os.path.exists(log_file):
        print(f"[Monitor] Waiting for log file {log_file} to be created...")
        while not os.path.exists(log_file):
            await asyncio.sleep(1)
            
    print(f"[Monitor] Log file found. Tailing...")
    
    # Open file and seek to end so it only reads *new* lines during runtime
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, os.SEEK_END)
        
        while True:
            line = f.readline()
            if not line:
                await asyncio.sleep(0.5)
                continue
                
            # Parse line (reuse old parsing logic which expects full content but handles single lines)
            events = parse_auth_logs(line)
            if not events:
                continue
                
            # Log raw event
            try:
                conn = get_db()
                cursor = conn.cursor()
                for evt in events:
                    cursor.execute(
                        "INSERT INTO parsed_logs (ip_address, status, timestamp, username, raw_log) VALUES (?, ?, ?, ?, ?)",
                        (evt.get("ip_address"), evt.get("status"), evt.get("timestamp"), evt.get("username"), evt.get("raw_log"))
                    )
                conn.commit()
            except Exception as e:
                print(f"[Monitor] DB Error on parse: {e}")
            finally:
                conn.close()

            # For real-time threat detection, we need to gather all recent failed attempts for this IP
            # The original logic grouped by file batch. For continuous monitoring, we query the DB 
            # for recent failures for the parsed IP.
            if events[0]["status"] == "Failed":
                ip = events[0]["ip_address"]
                conn = get_db()
                cursor = conn.cursor()
                # Get total failures for this IP. In a real system you'd use a time window (e.g., last 1 hr)
                cursor.execute("SELECT COUNT(*) as count FROM parsed_logs WHERE ip_address = ? AND status = 'Failed'", (ip,))
                row = cursor.fetchone()
                fail_count = row['count'] if row else 1
                conn.close()
                
                # Check against config
                min_threshold = CONFIG.get("threat_thresholds", {}).get("medium", 3)
                
                # Wait until we strictly hit the threshold to fire *one* initial alert
                # Or fire escalating alerts depending on design. Let's fire a new alert if it crosses a threshold boundary.
                # To keep it simple, let's just create an alert for it if we hit a threshold milestone exactly to avoid spam.
                thresholds = [
                    CONFIG.get("threat_thresholds", {}).get("medium", 3),
                    CONFIG.get("threat_thresholds", {}).get("high", 6),
                    CONFIG.get("threat_thresholds", {}).get("critical", 10)
                ]
                
                # Check if this exact line put us ON a threshold, Or if it's the very first time we surpassed it
                # For a mock generation, jumping from 0 to 500 quickly means exact matching is best to prevent 500 alerts.
                # To simulate an ongoing continuous attack, we also alert every 10 attempts after the max threshold.
                if fail_count in thresholds or fail_count == min(thresholds) or (fail_count > max(thresholds) and fail_count % 10 == 0):
                    # Trigger Detection
                    # We pass a synthetic batch object just to leverage existing logic nicely,
                    # or better, just create the alert payload directly since we know the fail_count
                    
                    from backend.detection_engine import determine_severity
                    severity = determine_severity(fail_count)
                    
                    raw_alert = {
                        "source_ip": ip,
                        "username": events[0].get("username", "Unknown"),
                        "attack_type": "Brute-Force",
                        "attempt_count": fail_count,
                        "severity": severity
                    }
                    
                    # Enrich 
                    enriched_alert = enrich_alert(raw_alert)
                    
                    # Save to DB
                    conn = get_db()
                    cursor = conn.cursor()
                    now = datetime.now().isoformat()
                    cursor.execute(
                        """INSERT INTO alerts 
                           (source_ip, username, attack_type, attempt_count, severity, country, city, reputation, abuse_reports, created_at) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (enriched_alert["source_ip"], enriched_alert["username"], enriched_alert["attack_type"], 
                         enriched_alert["attempt_count"], enriched_alert["severity"], enriched_alert["country"], 
                         enriched_alert["city"], enriched_alert["reputation"], enriched_alert["abuse_reports"], now)
                    )
                    conn.commit()
                    conn.close()
                    print(f"[Monitor] ⚠️ ALARM: {severity} Threat Detected from {ip} ({enriched_alert['reputation']}) - {fail_count} attempts.")
