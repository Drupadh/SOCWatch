import requests
import json

print("1. Uploading log file...")
with open("sample_auth.log", "rb") as f:
    files = {"file": ("sample_auth.log", f, "text/plain")}
    res = requests.post("http://localhost:8080/api/upload", files=files)
    print("Upload Response:", res.status_code, res.json())

print("\n2. Fetching dashboard data...")
res2 = requests.get("http://localhost:8080/api/dashboard")
data = res2.json()

print(json.dumps(data, indent=2))
