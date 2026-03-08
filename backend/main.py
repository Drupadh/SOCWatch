from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import asyncio
from datetime import datetime
from backend.database import get_db, init_db
from backend.models import AlertResponse, DashboardStatsResponse
from backend.agents.orchestrator import SOCOrchestrator
from backend.log_monitor import monitor_logs
from backend.report_generator import generate_json_report, generate_csv_report, generate_text_report
from backend.reporting.pdf_generator import generate_pdf_report, generate_single_alert_pdf
from backend.config import CONFIG
import generate_logs

app = FastAPI(title="SOC Monitoring Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("logs", exist_ok=True)
os.makedirs("reports", exist_ok=True)

# Global task reference
monitor_task = None

@app.on_event("startup")
async def startup_event():
    init_db()
    
    # Start the continuous log monitor in the background
    global monitor_task
    monitor_task = asyncio.create_task(monitor_logs())
    print("[System] Background log monitor started.")

@app.on_event("shutdown")
async def shutdown_event():
    if monitor_task:
        monitor_task.cancel()
        print("[System] Background log monitor stopped.")

# Keep old upload endpoint for legacy tests
@app.post("/api/upload")
async def upload_log_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".log") and not file.filename.endswith(".txt"):
         pass

    file_location = f"logs/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    with open(file_location, "r", encoding="utf-8", errors="ignore") as log_file:
        content = log_file.read()

    orchestrator = SOCOrchestrator()
    result = orchestrator.process_log_file(content)

    if result["status"] == "error":
         raise HTTPException(status_code=500, detail="Agent Orchestration Failed to parse logs.")

    return {"message": "File processed successfully", "events_parsed": result["events_parsed"], "alerts_generated": result["alerts_generated"]}

@app.get("/api/generate-logs")
def generate_mock_logs_endpoint():
    filename = CONFIG.get("log_file", "logs/auth.log")
    # Append the logs directly to the live file monitored by the background task
    generate_logs.generate_mock_logs(filename, num_lines=500)
    
    return {"message": f"500 lines generated and appended to {filename}. The dashboard should update shortly."}

@app.get("/api/dashboard", response_model=dict)
def get_dashboard_data():
    conn = get_db()
    cursor = conn.cursor()
    
    # Severity Stats
    cursor.execute("SELECT severity, count(*) as count FROM alerts GROUP BY severity")
    severity_counts = {row['severity']: row['count'] for row in cursor.fetchall()}
    
    stats = {
        "total_alerts": sum(severity_counts.values()),
        "critical_alerts": severity_counts.get("Critical", 0),
        "high_alerts": severity_counts.get("High", 0),
        "medium_alerts": severity_counts.get("Medium", 0)
    }

    # Recent Alerts (now with enriched data)
    cursor.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT 50")
    recent_alerts = [dict(row) for row in cursor.fetchall()]
    
    # Top IPs
    cursor.execute("SELECT source_ip, max(attempt_count) as count FROM alerts GROUP BY source_ip ORDER BY count DESC LIMIT 5")
    top_ips = [{"ip": row["source_ip"], "count": row["count"]} for row in cursor.fetchall()]

    # Time series data (alerts per day/hour - simplified for demo based on created_at string)
    # Ex: '2026-03-08T12:30:45'
    cursor.execute("SELECT substr(created_at, 1, 13) as hour_bucket, count(*) as count FROM alerts GROUP BY hour_bucket ORDER BY hour_bucket DESC LIMIT 10")
    timeline_stats = [{"time": row["hour_bucket"] + ":00", "count": row["count"]} for row in cursor.fetchall()]
    # reverse to show chronological order left-to-right
    timeline_stats.reverse()

    conn.close()
    
    return {
        "stats": stats,
        "recent_alerts": recent_alerts,
        "top_ips": top_ips,
        "timeline_stats": timeline_stats
    }

@app.get("/api/alerts/{ip}/timeline")
def get_ip_timeline(ip: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parsed_logs WHERE ip_address = ? ORDER BY id ASC LIMIT 100", (ip,))
    logs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"ip": ip, "timeline": logs}

# Exports
def get_all_alerts():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts ORDER BY severity DESC, attempt_count DESC")
    alerts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return alerts

@app.get("/api/export/json")
def export_json():
    alerts = get_all_alerts()
    json_str = generate_json_report(alerts)
    return PlainTextResponse(content=json_str, media_type="application/json", headers={"Content-Disposition": "attachment; filename=soc_alerts.json"})

@app.get("/api/export/csv")
def export_csv():
    alerts = get_all_alerts()
    csv_str = generate_csv_report(alerts)
    return PlainTextResponse(content=csv_str, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=soc_alerts.csv"})

@app.get("/api/export/txt")
def export_txt():
    alerts = get_all_alerts()
    txt_str = generate_text_report(alerts)
    # Using the existing report system style as requested
    report_path = f"reports/incident_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    with open(report_path, "w") as f:
        f.write(txt_str)
    return FileResponse(path=report_path, filename="soc_incident_report.txt", media_type="text/plain")

@app.get("/api/export/pdf")
def export_pdf():
    alerts = get_all_alerts()
    report_path = generate_pdf_report(alerts)
    return FileResponse(path=report_path, filename="soc_incident_report.pdf", media_type="application/pdf")

@app.get("/api/export/pdf/{ip}")
def export_single_pdf(ip: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts WHERE source_ip = ? ORDER BY id DESC LIMIT 1", (ip,))
    alert_row = cursor.fetchone()
    if not alert_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Alert not found for this IP")
        
    alert = dict(alert_row)
    
    cursor.execute("SELECT * FROM parsed_logs WHERE ip_address = ? ORDER BY id ASC LIMIT 100", (ip,))
    timeline = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    report_path = generate_single_alert_pdf(alert, timeline)
    return FileResponse(path=report_path, filename=f"investigation_{ip}.pdf", media_type="application/pdf")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
