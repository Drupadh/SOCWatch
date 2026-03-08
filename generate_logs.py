import random
from datetime import datetime, timedelta
import os

def generate_mock_logs(filename="generated_auth.log", num_lines=5000):
    ips = [
        "185.234.217.44",
        "103.145.32.17",
        "45.156.128.33",
        "91.189.91.12",
        "172.104.11.56",
        "8.8.8.8",
        "203.0.113.1"
    ]

    users = ["root", "admin", "oracle", "test", "ubuntu", "www-data", "postgres"]

    # Start time a few hours ago
    current_time = datetime.now() - timedelta(hours=2)

    with open(filename, "a") as f:
        for _ in range(num_lines):
            ip = random.choice(ips)
            user = random.choice(users)
            
            # Format: Mar  8 12:34:56
            time_str = current_time.strftime("%b %d %H:%M:%S")

            if random.random() < 0.7:
                # 70% chance of a failed password
                line = f"{time_str} server sshd[{random.randint(2000,4000)}]: Failed password for {user} from {ip} port {random.randint(20000,60000)} ssh2"
            else:
                # 30% chance of accepted password, coming from an internal IP
                internal_ip = f"10.0.0.{random.randint(10,50)}"
                line = f"{time_str} server sshd[{random.randint(2000,4000)}]: Accepted password for {user} from {internal_ip} port {random.randint(20000,60000)} ssh2"

            f.write(line + "\n")

            # Increment time slightly between logs (1 to 5 seconds)
            current_time += timedelta(seconds=random.randint(1, 5))

    print(f"Generated {num_lines} mock log lines in {filename}")

if __name__ == "__main__":
    generate_mock_logs()
