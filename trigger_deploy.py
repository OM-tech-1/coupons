
import paramiko
import sys
import time

import os
from dotenv import load_dotenv

load_dotenv()

HOSTNAME = os.getenv("VPS_HOST")
USERNAME = os.getenv("VPS_USER")
PASSWORD = os.getenv("VPS_PASSWORD")

def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {HOSTNAME}...")
    client.connect(HOSTNAME, username=USERNAME, password=PASSWORD)
    return client

def run_command(client, command):
    print(f"Running: {command}")
    stdin, stdout, stderr = client.exec_command(command)
    # Stream output
    while True:
        line = stdout.readline()
        if not line:
            break
        print(line.strip())
    
    err = stderr.read().decode().strip()
    if err:
        print(f"STDERR: {err}")

def main():
    try:
        client = connect()
        # Verify directory exists
        run_command(client, "ls -la /root/coupons")
        
        # Run deploy script
        print("\n--- Triggering Deployment ---")
        # Ensure execute permission
        run_command(client, "chmod +x /root/coupons/deploy.sh")
        run_command(client, "cd /root/coupons && ./deploy.sh")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
