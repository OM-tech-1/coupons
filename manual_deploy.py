
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
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(f"STDOUT: {out}")
    if err: print(f"STDERR: {err}")
    return out

def main():
    try:
        client = connect()
        
        print("\n--- Cleaning up ---")
        run_command(client, "docker stop coupon-api-container")
        run_command(client, "docker rm coupon-api-container")
        
        print("\n--- Running Manual Docker Command ---")
        cmd = "docker run -d --name coupon-api-container --restart unless-stopped --network host --env-file /root/coupons/.env coupon-api"
        run_command(client, cmd)
        
        print("\n--- Waiting for startup ---")
        time.sleep(5)
        
        print("\n--- Logs ---")
        run_command(client, "docker logs --tail 20 coupon-api-container")
        
        print("\n--- Health Check ---")
        run_command(client, "curl localhost:8000/health")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
