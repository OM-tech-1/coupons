import paramiko
import sys
import time

import os
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("VPS_HOST")
USER = os.getenv("VPS_USER")
PASS = os.getenv("VPS_PASSWORD")
REPO_URL = "https://github.com/OM-tech-1/coupons.git"

def run_deployment():
    print(f"📡 Connecting to {HOST}...")
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOST, username=USER, password=PASS)
        print("✅ Connected!")

        # Commands to run
        # 1. Check if directory exists, if not clone it
        # 2. Copy .env from root if it exists in root
        # 3. Pull latest changes
        # 4. Run deploy script
        
        setup_cmds = [
            "if [ ! -d '/root/coupons' ]; then git clone https://github.com/OM-tech-1/coupons.git /root/coupons; fi",
            "cd /root/coupons",
            "if [ -f '/root/.env' ]; then cp /root/.env .env; fi",
            "git pull origin main",
            "chmod +x deploy.sh",
            "./deploy.sh"
        ]
        
        full_cmd = " && ".join(setup_cmds)
        print(f"\n🚀 Executing deployment sequence:\n{full_cmd}\n")
        
        stdin, stdout, stderr = client.exec_command(full_cmd)
        
        # Stream output
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                print(stdout.channel.recv(1024).decode('utf-8'), end='', flush=True)
            time.sleep(0.1)
            
        print(stdout.read().decode('utf-8'), end='')
        err = stderr.read().decode('utf-8')
        
        if err:
            print(f"\n⚠️ STDERR:\n{err}")
            
        exit_status = stdout.channel.recv_exit_status()
        if exit_status == 0:
            print("\n✅ Deployment Command Completed Successfully!")
        else:
            print(f"\n❌ Deployment Failed with exit code {exit_status}")
            
        client.close()
        
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")

if __name__ == "__main__":
    run_deployment()
