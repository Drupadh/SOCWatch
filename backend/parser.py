import re
from typing import List, Dict

# Sample Regex for parsing standard Linux Auth Logs (sshd)
# Example: "Mar  8 12:34:56 hostname sshd[1234]: Failed password for invalid user admin from 192.168.1.100 port 22 ssh2"
# Example: "Mar  8 12:35:01 hostname sshd[1235]: Accepted password for admin from 192.168.1.100 port 22 ssh2"

LOG_REGEX = re.compile(
    r'^(?P<timestamp>[A-Z][a-z]{2}\s+\d+\s\d{2}:\d{2}:\d{2})\s+'
    r'(?P<hostname>\S+)\s+(?P<service>[^:]+):\s+'
    r'(?P<message>.*)$'
)

def parse_auth_logs(file_content: str) -> List[Dict]:
    parsed_events = []
    lines = file_content.splitlines()

    for line in lines:
        match = LOG_REGEX.match(line)
        if not match:
            continue
            
        groups = match.groupdict()
        timestamp = groups['timestamp']
        message = groups['message']
        
        status = "Unknown"
        ip_address = None
        username = "Unknown"

        if "Failed password" in message:
            status = "Failed"
            # Extract IP
            ip_match = re.search(r'from (\d+\.\d+\.\d+\.\d+)', message)
            if ip_match:
                ip_address = ip_match.group(1)
            
            # Extract Username
            user_match = re.search(r'for (?:invalid user )?(\w+)', message)
            if user_match:
                username = user_match.group(1)
                
        elif "Accepted password" in message:
            status = "Success"
            # Extract IP
            ip_match = re.search(r'from (\d+\.\d+\.\d+\.\d+)', message)
            if ip_match:
                ip_address = ip_match.group(1)
            
            # Extract Username
            user_match = re.search(r'for (\w+)', message)
            if user_match:
                username = user_match.group(1)

        if ip_address: # Only care about events with IPs for our brute force detection
            parsed_events.append({
                "ip_address": ip_address,
                "status": status,
                "timestamp": timestamp,
                "username": username,
                "raw_log": line
            })

    return parsed_events
