import paramiko
import sys
import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("VPS_HOST")
USER = os.getenv("VPS_USER")
PASS = os.getenv("VPS_PASSWORD")

def check_docker():
    print(f"📡 Connecting to {HOST}...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, username=USER, password=PASS)
        
        print("🐳 Checking running containers...")
        stdin, stdout, stderr = client.exec_command("docker ps")
        print(stdout.read().decode('utf-8'))
        
        print("📁 Checking current working directory files...")
        stdin, stdout, stderr = client.exec_command("ls -la")
        print(stdout.read().decode('utf-8'))
        
        client.close()
        
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    check_docker()
