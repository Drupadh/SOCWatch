from backend.agents.parser_agent import ParserAgent
from backend.agents.analyzer_agent import ThreatIntelAgent
from backend.agents.reporter_agent import ReporterAgent
from backend.database import get_db
from datetime import datetime

class SOCOrchestrator:
    """
    Coordinates the log analysis workflow across the A2A system.
    """
    def __init__(self):
        self.parser = ParserAgent()
        self.analyzer = ThreatIntelAgent()
        self.reporter = ReporterAgent()

    def process_log_file(self, file_content: str):
        print("\n" + "="*50)
        print("[Orchestrator] Starting A2A Log Analysis Workflow...")
        
        # 1. Parse
        parsed_events = self.parser.parse(file_content)
        if not parsed_events:
            print("[Orchestrator] Parser failed to extract events. Aborting.")
            return {"status": "error", "message": "No events parsed"}
            
        # Store raw events to DB
        conn = get_db()
        cursor = conn.cursor()
        
        for evt in parsed_events:
            cursor.execute(
                "INSERT INTO parsed_logs (ip_address, status, timestamp, username, raw_log) VALUES (?, ?, ?, ?, ?)",
                (evt.get("ip_address"), evt.get("status"), evt.get("timestamp"), evt.get("username"), evt.get("raw_log"))
            )
            
        # 2. Analyze
        alerts = self.analyzer.analyze(parsed_events)
        
        # Store alerts to DB
        now = datetime.now().isoformat()
        for alert in alerts:
            cursor.execute(
                "INSERT INTO alerts (source_ip, attack_type, attempt_count, severity, created_at) VALUES (?, ?, ?, ?, ?)",
                (alert.get("source_ip"), alert.get("attack_type"), alert.get("attempt_count"), alert.get("severity"), now)
            )
            
        conn.commit()
        conn.close()
            
        # 3. Report
        incident_report = self.reporter.generate_report(alerts)
        
        print("[Orchestrator] Workflow Complete.")
        print("="*50 + "\n")
        
        return {
            "status": "success",
            "events_parsed": len(parsed_events),
            "alerts_generated": len(alerts),
            "report_preview": incident_report[:200] + "..." if incident_report else ""
        }
