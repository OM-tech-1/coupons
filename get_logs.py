
import paramiko
import sys

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
    if out: print(f"STDOUT:\n{out}")
    err = stderr.read().decode().strip()
    if err: print(f"STDERR:\n{err}")

def main():
    try:
        client = connect()
        run_command(client, "docker logs coupon-api-container --tail 100")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
