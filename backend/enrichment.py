import requests
from backend.config import CONFIG

def enrich_alert(alert: dict) -> dict:
    """
    Takes an alert dict and enriches it with GeoLocation and Threat Intel.
    Returns the enriched dictionary.
    """
    ip = alert.get("source_ip")
    
    # Defaults
    alert["country"] = "Unknown"
    alert["city"] = "Unknown"
    alert["reputation"] = "Unknown"
    alert["abuse_reports"] = 0
    
    if not ip:
        return alert

    # 1. Geolocation lookup
    if CONFIG.get("enable_geolocation", True):
        try:
            # Note: For production use bulk endpoints or caching,
            # but for a mini-SOC, a per-alert call to ip-api.com works perfectly.
            # We use an http endpoint to avoid SSL cert issues locally occasionally seen with free tiers.
            resp = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    alert["country"] = data.get("country", "Unknown")
                    alert["city"] = data.get("city", "Unknown")
        except Exception as e:
            print(f"[Enrichment] Failed to geolocate {ip}: {e}")

    # 2. Mock Threat Intel
    if CONFIG.get("enable_threat_intel", True):
        # We'll use a deterministic mock based on the last octet of the IP for demo purposes
        # In the real world, this would call AbuseIPDB or VirusTotal.
        try:
            last_octet = int(ip.split(".")[-1])
            if last_octet % 5 == 0:
                alert["reputation"] = "Malicious"
                alert["abuse_reports"] = (last_octet % 20) + 5
            elif last_octet % 3 == 0:
                alert["reputation"] = "Suspicious"
                alert["abuse_reports"] = (last_octet % 5) + 1
            else:
                alert["reputation"] = "Neutral"
                alert["abuse_reports"] = 0
        except:
             pass

    return alert
