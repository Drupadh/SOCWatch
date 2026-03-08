import os
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

def generate_pdf_report(alerts, filename=None):
    """
    Generates a full SOC Incident Report PDF containing all provided alerts.
    """
    if filename is None:
        filename = f"reports/incident_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        
    os.makedirs(os.path.dirname(filename), exist_ok=True)
        
    doc = SimpleDocTemplate(filename, pagesize=landscape(letter))
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Title
    elements.append(Paragraph("SOC Security Incident Report", title_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    elements.append(Spacer(1, 0.5 * inch))
    
    # Executive Summary
    elements.append(Paragraph("Attack Summary", heading_style))
    total_alerts = len(alerts)
    critical_alerts = sum(1 for a in alerts if a.get('severity') == 'Critical')
    high_alerts = sum(1 for a in alerts if a.get('severity') == 'High')
    medium_alerts = sum(1 for a in alerts if a.get('severity') == 'Medium')
    
    summary_text = (f"This report details {total_alerts} security incidents detected by the SOC Platform. "
                    f"Among these, {critical_alerts} are classified as Critical, {high_alerts} as High, "
                    f"and {medium_alerts} as Medium severity.")
    elements.append(Paragraph(summary_text, normal_style))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Table of Alerts
    elements.append(Paragraph("Detected Threats", heading_style))
    
    # Table headers
    data = [["Time", "Source IP", "Attack Type", "Attempts", "Severity", "Location", "Intel"]]
    
    for alert in alerts:
        time_str = alert.get('created_at', 'Unknown')
        if 'T' in time_str:
            time_str = time_str.split('T')[0] + " " + time_str.split('T')[1][:8]
            
        location = f"{alert.get('city', 'Unknown')}, {alert.get('country', 'Unknown')}"
        intel = f"{alert.get('reputation', 'Unknown')} ({alert.get('abuse_reports', 0)} reports)"
        
        data.append([
            time_str,
            alert.get('source_ip', 'Unknown'),
            alert.get('attack_type', 'Unknown'),
            str(alert.get('attempt_count', 0)),
            alert.get('severity', 'Unknown'),
            location,
            intel
        ])
        
    # Create Table
    col_widths = [1.5*inch, 1.2*inch, 1.2*inch, 0.8*inch, 0.8*inch, 2.0*inch, 1.5*inch]
    t = Table(data, colWidths=col_widths)
    
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(t)
    
    # Mitigation Steps
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("Recommended Mitigation Steps", heading_style))
    mitigation_text = """
    1. Block the critical and high severity Source IPs at the firewall level.<br/>
    2. Audit the affected user accounts for potential compromise.<br/>
    3. Implement or enforce Multi-Factor Authentication (MFA) on all external facing portals.<br/>
    4. Review Geo-blocking policies to restrict access from high-risk countries.<br/>
    5. Search for indicators of compromise (IOCs) across internal network logs based on these IPs.
    """
    elements.append(Paragraph(mitigation_text, normal_style))
    
    # Build the PDF
    doc.build(elements)
    
    return filename

def generate_single_alert_pdf(alert, timeline_logs, filename=None):
    """
    Generates a detailed investigation report for a single alert and its timeline.
    """
    ip = alert.get("source_ip", "Unknown")
    if filename is None:
        filename = f"reports/investigation_{ip.replace('.', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        
    os.makedirs(os.path.dirname(filename), exist_ok=True)
        
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    mono_style = ParagraphStyle('Mono', parent=styles['Normal'], fontName='Courier', fontSize=8, leading=10)
    
    # Title
    elements.append(Paragraph("SOC Security Investigation Report", title_style))
    elements.append(Paragraph(f"Target IP: {ip}", styles['Heading3']))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Alert Details Table
    elements.append(Paragraph("Incident Details", heading_style))
    
    time_str = alert.get('created_at', 'Unknown')
    if 'T' in time_str:
        time_str = time_str.split('T')[0] + " " + time_str.split('T')[1][:8]
        
    details_data = [
        ["Attack Type:", alert.get('attack_type', 'Unknown')],
        ["Severity:", alert.get('severity', 'Unknown')],
        ["Total Attempts:", str(alert.get('attempt_count', 0))],
        ["Target Username:", alert.get('username', 'Unknown')],
        ["First Detected:", time_str],
        ["Geolocation:", f"{alert.get('city', 'Unknown')}, {alert.get('country', 'Unknown')}"],
        ["Threat Intel:", f"{alert.get('reputation', 'Unknown')} ({alert.get('abuse_reports', 0)} abuse reports)"]
    ]
    
    t_details = Table(details_data, colWidths=[2.0*inch, 4.0*inch])
    t_details.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(t_details)
    elements.append(Spacer(1, 0.3 * inch))
    
    # Timeline
    elements.append(Paragraph("Attack Timeline", heading_style))
    
    if not timeline_logs:
        elements.append(Paragraph("No raw timeline logs found for this IP.", normal_style))
    else:
        timeline_data = [["Timestamp", "Status", "Raw Log"]]
        for log in timeline_logs:
            # Wrap long raw log lines
            raw_log_para = Paragraph(log.get('raw_log', ''), mono_style)
            timeline_data.append([
                log.get('timestamp', ''),
                log.get('status', ''),
                raw_log_para
            ])
            
        t_timeline = Table(timeline_data, colWidths=[1.5*inch, 0.8*inch, 4.5*inch])
        t_timeline.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        
        elements.append(t_timeline)
        
    # Mitigation
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("Action Plan", heading_style))
    elements.append(Paragraph(f"1. Immediately block IP {ip} at the edge firewall.", normal_style))
    elements.append(Paragraph(f"2. Check if the user account '{alert.get('username', 'Unknown')}' has had successful logins from this IP or others recently.", normal_style))
    elements.append(Paragraph("3. Rotate credentials if the account has been compromised.", normal_style))
        
    doc.build(elements)
    return filename
