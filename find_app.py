import paramiko
import sys

import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("VPS_HOST")
USER = os.getenv("VPS_USER")
PASS = os.getenv("VPS_PASSWORD")

def find_directory():
    print(f"📡 Connecting to {HOST}...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, username=USER, password=PASS)
        
        # Try to find the directory with a file we know exists (Dockerfile or main.py)
        cmd = "find / -name Dockerfile -type f 2>/dev/null | grep coupons || find / -name main.py -type f 2>/dev/null | grep coupons"
        print(f"🔍 Searching for app directory...")
        
        stdin, stdout, stderr = client.exec_command(cmd)
        result = stdout.read().decode('utf-8').strip()
        
        if result:
            print(f"✅ Found paths:\n{result}")
        else:
            print("❌ Could not find app directory. Listing home directory:")
            stdin, stdout, stderr = client.exec_command("ls -la ~")
            print(stdout.read().decode('utf-8'))
            
        client.close()
        
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    find_directory()
